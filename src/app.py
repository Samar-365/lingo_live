"""
Lingo-Live - Persistent Background Application
X button and ESC hide the window; Quit button exits.
"""

import customtkinter as ctk
import tkinter as tk
from PIL import ImageGrab
import threading
import keyboard
import sys
import os
import time
import tempfile
import atexit

LOCK_FILE = os.path.join(tempfile.gettempdir(), "lingo_live.lock")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_OPACITY,
    OVERLAY_BG_COLOR, OVERLAY_TEXT_COLOR, OVERLAY_ACCENT_COLOR,
    OVERLAY_FONT_FAMILY, OVERLAY_FONT_SIZE,
    SUPPORTED_LANGUAGES, DEFAULT_TARGET_LANGUAGE
)

HOTKEY = 'ctrl+alt+t'


def acquire_lock():
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                return False
            except (OSError, ProcessLookupError):
                pass
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except:
        return True


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


class LingoLiveApp:
    """Persistent translator app - runs in background."""
    
    def __init__(self):
        from services.ocr_service import OCRService
        from services.translation_service import TranslationService
        
        self.ocr = OCRService()
        self.translator = TranslationService()
        self.current_language = DEFAULT_TARGET_LANGUAGE
        
        self.running = True
        self.in_selection = False
        self.selection_window = None
        
        atexit.register(self._cleanup)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self._build_main_window()
        
    def _build_main_window(self):
        """Build persistent main window."""
        self.root = ctk.CTk()
        self.root.title("Lingo-Live")
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+100+100")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', OVERLAY_OPACITY)
        self.root.overrideredirect(True)
        self.root.configure(fg_color=OVERLAY_BG_COLOR)
        
        # Frame
        frame = ctk.CTkFrame(self.root, fg_color=OVERLAY_BG_COLOR,
                             corner_radius=15, border_width=2,
                             border_color=OVERLAY_ACCENT_COLOR)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        title = ctk.CTkLabel(header, text="🌐 Lingo-Live",
                             font=(OVERLAY_FONT_FAMILY, 14, "bold"),
                             text_color=OVERLAY_ACCENT_COLOR)
        title.pack(side="left")
        
        # Language
        self.lang_var = ctk.StringVar(value=SUPPORTED_LANGUAGES.get(self.current_language, "English"))
        ctk.CTkComboBox(header, values=list(SUPPORTED_LANGUAGES.values()),
                        variable=self.lang_var, width=100, height=28,
                        command=self._on_lang).pack(side="left", padx=(15, 0))
        
        # Quit button (Explicit exit)
        ctk.CTkButton(header, text="Quit", width=50, height=30,
                      fg_color="transparent", hover_color="#ff4444", border_width=1, border_color="#ff4444",
                      text_color="#ff4444",
                      command=self._exit_app).pack(side="right")
        
        # Hide button (X)
        ctk.CTkButton(header, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color="#6ab0f9",
                      command=self._hide_window).pack(side="right", padx=(5, 5))
        
        # New button
        self.new_btn = ctk.CTkButton(header, text="📷 New", width=70, height=30,
                                      fg_color=OVERLAY_ACCENT_COLOR,
                                      command=self._new_selection)
        self.new_btn.pack(side="right", padx=(0, 5))
        
        # Text
        self.textbox = ctk.CTkTextbox(frame, fg_color="#2a2a4a",
                                       text_color=OVERLAY_TEXT_COLOR,
                                       font=(OVERLAY_FONT_FAMILY, OVERLAY_FONT_SIZE),
                                       wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self._set_text("Press Ctrl+Alt+T or click '📷 New' to select text.\n\nClick ✕ to hide window (app keeps running).")
        
        # Status
        self.status = ctk.CTkLabel(frame, text="Ctrl+Alt+T = New | ✕ = Hide | Quit = Exit",
                                    font=(OVERLAY_FONT_FAMILY, 10), text_color="#888")
        self.status.pack(pady=(0, 5))
        
        # ESC hides window
        self.root.bind("<Escape>", lambda e: self._hide_window())
        
        # Drag
        self._dx, self._dy = 0, 0
        header.bind("<Button-1>", lambda e: setattr(self, '_dx', e.x) or setattr(self, '_dy', e.y))
        header.bind("<B1-Motion>", self._drag)
        title.bind("<Button-1>", lambda e: setattr(self, '_dx', e.x) or setattr(self, '_dy', e.y))
        title.bind("<B1-Motion>", self._drag)
        
    def _drag(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")
        
    def _on_lang(self, choice):
        for code, name in SUPPORTED_LANGUAGES.items():
            if name == choice:
                self.current_language = code
                break
                
    def _set_text(self, txt):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", txt)
        self.textbox.configure(state="disabled")
        
    def _on_hotkey(self):
        """Hotkey - always start fresh selection."""
        if self.running:
            self.root.after(10, self._new_selection)
            
    def _new_selection(self):
        """Start fresh selection."""
        if not self.running:
            return
            
        self._close_selection_window()
        if self.in_selection:
            return
            
        self.in_selection = True
        self._set_text("Starting new selection...")
        self.root.withdraw()
        self.root.after(100, self._show_selector)
        
    def _close_selection_window(self):
        if self.selection_window:
            try:
                self.selection_window.grab_release()
                self.selection_window.destroy()
            except:
                pass
            self.selection_window = None
            
    def _show_selector(self):
        try:
            self.selection_window = tk.Toplevel()
            win = self.selection_window
            
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            
            win.geometry(f"{sw}x{sh}+0+0")
            win.overrideredirect(True)
            win.attributes('-topmost', True)
            win.attributes('-alpha', 0.35)
            win.configure(bg='#1a1a2e')
            win.config(cursor='cross')
            
            canvas = tk.Canvas(win, width=sw, height=sh, highlightthickness=0, bg='#1a1a2e')
            canvas.pack()
            
            canvas.create_text(sw//2, 50, text="🖱️ DRAG to select text | ESC to cancel",
                               font=("Segoe UI", 18, "bold"), fill="#00ff88")
            
            state = {"x1": 0, "y1": 0, "rect": None}
            
            def press(e):
                state["x1"], state["y1"] = e.x, e.y
                if state["rect"]:
                    canvas.delete(state["rect"])
                state["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline='#00ff88', width=3)
                
            def drag(e):
                if state["rect"]:
                    canvas.coords(state["rect"], state["x1"], state["y1"], e.x, e.y)
                    
            def release(e):
                x1, y1 = min(state["x1"], e.x), min(state["y1"], e.y)
                x2, y2 = max(state["x1"], e.x), max(state["y1"], e.y)
                
                self._close_selection_window()
                self.in_selection = False
                
                if x2 - x1 > 10 and y2 - y1 > 10:
                    self.root.after(50, lambda: self._translate(x1, y1, x2, y2))
                else:
                    self.root.after(0, self._show_main)
                    
            def cancel(e):
                self._close_selection_window()
                self.in_selection = False
                self.root.after(0, self._show_main)
                
            canvas.bind("<Button-1>", press)
            canvas.bind("<B1-Motion>", drag)
            canvas.bind("<ButtonRelease-1>", release)
            win.bind("<Escape>", cancel)
            
            win.focus_force()
            win.grab_set()
            
        except Exception as e:
            print(f"[Selection Error] {e}")
            self.in_selection = False
            self._show_main()
            
    def _show_main(self):
        self.root.deiconify()
        self.root.lift()
        self._set_text("Press Ctrl+Alt+T or click '📷 New' to select text")
        self.status.configure(text="Ctrl+Alt+T = New | ✕ = Hide | Quit = Exit")
        
    def _translate(self, x1, y1, x2, y2):
        self.root.deiconify()
        self.root.lift()
        self._set_text("⏳ Processing...")
        self.status.configure(text="Translating...")
        
        def work():
            try:
                img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                text = self.ocr.extract_text(img)
                if not text:
                    self.root.after(0, lambda: self._show_result("", "No text detected"))
                    return
                print(f"[OCR] {text[:50]}...")
                result = self.translator.translate(text, self.current_language)
                print(f"[Trans] {result[:50]}...")
                self.root.after(0, lambda: self._show_result(text, result))
            except Exception as e:
                print(f"[Error] {e}")
                self.root.after(0, lambda: self._show_result("", f"Error: {e}"))
                
        threading.Thread(target=work, daemon=True).start()
        
    def _show_result(self, original, translated):
        if original and original != translated:
            out = f"📝 Original:\n{original}\n\n🌐 Translation:\n{translated}"
        else:
            out = translated or "No text"
        self._set_text(out)
        self.status.configure(text="Ctrl+Alt+T = New | ✕ = Hide | Quit = Exit")
        
    def _hide_window(self):
        """Hide window but keep app running."""
        print("[Hiding window]")
        self.root.withdraw()
        
    def _cleanup(self):
        self.running = False
        try:
            keyboard.unhook_all()
        except:
            pass
        self._close_selection_window()
        release_lock()
        
    def _exit_app(self):
        """Real exit."""
        print("[Exiting Application]")
        self._cleanup()
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        os._exit(0)
        
    def run(self):
        print("=" * 40)
        print("  🌐 Lingo-Live")
        print("=" * 40)
        print(f"  Hotkey: {HOTKEY}")
        print("  📷 New to select")
        print("  ✕ to Hide | Quit to Exit")
        print("=" * 40)
        
        if self.ocr.is_available():
            print("  ✅ OCR Ready")
            
        keyboard.add_hotkey(HOTKEY, self._on_hotkey, suppress=False)
        print("  ✅ Hotkey active")
        print("[Ready - App runs in background]")
        
        try:
            self.root.mainloop()
        except:
            pass
        finally:
            self._cleanup()


def main():
    if not acquire_lock():
        print("[!] Killing old instance...")
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 9)
            time.sleep(0.5)
        except:
            pass
        acquire_lock()
    
    app = LingoLiveApp()
    app.run()


if __name__ == "__main__":
    main()
