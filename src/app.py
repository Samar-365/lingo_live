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
        from services.gemini_service import GeminiService
        
        self.ocr = OCRService()
        self.translator = TranslationService()
        self.gemini = GeminiService()
        self.current_language = DEFAULT_TARGET_LANGUAGE
        
        self.running = True
        self.in_selection = False
        self.selection_window = None
        self.is_maximized = False
        self.normal_geometry = None
        self.last_translated_text = ""  # Store for TTS
        self.tts_available = False
        self._init_tts()
        
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
        self.frame = ctk.CTkFrame(self.root, fg_color=OVERLAY_BG_COLOR,
                             corner_radius=15, border_width=2,
                             border_color=OVERLAY_ACCENT_COLOR)
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        self.header = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(10, 5))
        
        self.title = ctk.CTkLabel(self.header, text="🌐 Lingo-Live",
                             font=(OVERLAY_FONT_FAMILY, 14, "bold"),
                             text_color=OVERLAY_ACCENT_COLOR)
        self.title.pack(side="left")
        
        # Language
        self.lang_var = ctk.StringVar(value=SUPPORTED_LANGUAGES.get(self.current_language, "English"))
        ctk.CTkComboBox(self.header, values=list(SUPPORTED_LANGUAGES.values()),
                        variable=self.lang_var, width=100, height=28,
                        command=self._on_lang).pack(side="left", padx=(15, 0))
        
        # Quit button (Explicit exit)
        ctk.CTkButton(self.header, text="Quit", width=50, height=30,
                      fg_color="transparent", hover_color="#ff4444", border_width=1, border_color="#ff4444",
                      text_color="#ff4444",
                      command=self._exit_app).pack(side="right")
        
        # Hide button (X)
        ctk.CTkButton(self.header, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color="#6ab0f9",
                      command=self._hide_window).pack(side="right", padx=(5, 5))
        
        # Maximize button
        self.max_btn = ctk.CTkButton(self.header, text="◻", width=30, height=30,
                      fg_color="transparent", hover_color="#6ab0f9",
                      command=self._toggle_maximize)
        self.max_btn.pack(side="right", padx=(0, 2))
        
        # New button
        self.new_btn = ctk.CTkButton(self.header, text="📷 New", width=70, height=30,
                                      fg_color=OVERLAY_ACCENT_COLOR,
                                      command=self._new_selection)
        self.new_btn.pack(side="right", padx=(0, 5))

        # Summarize button
        self.summarize_btn = ctk.CTkButton(self.header, text="✨", width=35, height=30,
                                            fg_color="transparent", hover_color="#9C27B0",
                                            border_width=1, border_color="#9C27B0",
                                            command=self._summarize)
        self.summarize_btn.pack(side="right", padx=(0, 5))
        
        # Read Aloud button (optional TTS)
        self.read_btn = ctk.CTkButton(self.header, text="🔊", width=35, height=30,
                                       fg_color="transparent", hover_color="#4a90d9",
                                       border_width=1, border_color="#4a90d9",
                                       command=self._read_aloud)
        self.read_btn.pack(side="right", padx=(0, 5))
        
        # Text
        self.textbox = ctk.CTkTextbox(self.frame, fg_color="#2a2a4a",
                                       text_color=OVERLAY_TEXT_COLOR,
                                       font=(OVERLAY_FONT_FAMILY, OVERLAY_FONT_SIZE),
                                       wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self._set_text("Press Ctrl+Alt+T or click '📷 New' to select text.\n\nClick ✕ to hide window (app keeps running).")
        
        # Status
        self.status = ctk.CTkLabel(self.frame, text="Ctrl+Alt+T = New | ✕ = Hide | Quit = Exit",
                                    font=(OVERLAY_FONT_FAMILY, 10), text_color="#888")
        self.status.pack(pady=(0, 5))
        
        # ESC hides window
        self.root.bind("<Escape>", lambda e: self._hide_window())
        
        # Drag - bind to header, title, and frame for easy moving
        self._dx, self._dy = 0, 0
        self._start_drag_bind(self.header)
        self._start_drag_bind(self.title)
        self._start_drag_bind(self.frame)
        
    def _start_drag_bind(self, widget):
        """Bind drag events to a widget."""
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag)
        
    def _start_drag(self, e):
        self._dx, self._dy = e.x, e.y
        
    def _drag(self, e):
        # Don't drag when maximized
        if self.is_maximized:
            return
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")
        
    def _toggle_maximize(self):
        """Toggle between maximized and normal window size."""
        if self.is_maximized:
            # Restore to normal size
            if self.normal_geometry:
                self.root.geometry(self.normal_geometry)
            self.max_btn.configure(text="◻")
            self.is_maximized = False
        else:
            # Save current geometry and maximize
            self.normal_geometry = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self.max_btn.configure(text="❐")
            self.is_maximized = True
        
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
        
        # Stop any ongoing TTS
        self._stop_tts()
            
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
        """Show full-screen selection overlay with ESC button."""
        try:
            print("[Selection] Creating full-screen selection window...")
            
            self.selection_window = tk.Toplevel()
            win = self.selection_window
            
            # Get actual screen dimensions
            win.update_idletasks()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            print(f"[Selection] Screen: {sw}x{sh}")
            
            # Make truly full screen
            win.geometry(f"{sw}x{sh}+0+0")
            win.overrideredirect(True)
            win.attributes('-topmost', True)
            win.attributes('-alpha', 0.3)
            win.configure(bg='#1a1a2e')
            win.config(cursor='cross')
            
            # Force the window to cover entire screen
            win.wm_attributes('-topmost', 1)
            win.state('zoomed')  # Maximize on Windows
            
            # Create canvas filling entire screen
            canvas = tk.Canvas(win, highlightthickness=0, bg='#1a1a2e')
            canvas.pack(fill='both', expand=True)
            
            # Instructions at top
            canvas.create_text(sw//2, 50, text="🖱️ DRAG to select area for translation",
                               font=("Arial", 24, "bold"), fill="#00ff00")
            
            # ESC button (visible cancel button)
            esc_btn = tk.Button(win, text="✕ ESC to Cancel", font=("Arial", 14, "bold"),
                               bg="#ff4444", fg="white", bd=0, padx=20, pady=10,
                               command=lambda: on_escape(None))
            esc_btn.place(x=sw-180, y=20)  # Top right corner
            
            # Selection state
            self.sel_state = {"x1": 0, "y1": 0, "rect": None}
            
            def on_press(event):
                print(f"[Selection] Press at ({event.x}, {event.y})")
                self.sel_state["x1"] = event.x
                self.sel_state["y1"] = event.y
                if self.sel_state["rect"]:
                    canvas.delete(self.sel_state["rect"])
                self.sel_state["rect"] = canvas.create_rectangle(
                    event.x, event.y, event.x, event.y,
                    outline='#00ff00', width=3
                )
                
            def on_drag(event):
                if self.sel_state["rect"]:
                    canvas.coords(self.sel_state["rect"], 
                                  self.sel_state["x1"], self.sel_state["y1"],
                                  event.x, event.y)
                    
            def on_release(event):
                print(f"[Selection] Release at ({event.x}, {event.y})")
                x1 = min(self.sel_state["x1"], event.x)
                y1 = min(self.sel_state["y1"], event.y)
                x2 = max(self.sel_state["x1"], event.x)
                y2 = max(self.sel_state["y1"], event.y)
                
                print(f"[Selection] Area: ({x1}, {y1}) to ({x2}, {y2})")
                
                # Close window
                self._close_selection_window()
                self.in_selection = False
                
                # Translate if valid selection
                if x2 - x1 > 10 and y2 - y1 > 10:
                    self.root.after(200, lambda: self._translate(x1, y1, x2, y2))
                else:
                    print("[Selection] Too small, cancelling")
                    self.root.after(0, self._show_main)
                    
            def on_escape(event):
                print("[Selection] Cancelled")
                self._close_selection_window()
                self.in_selection = False
                self.root.after(0, self._show_main)
            
            # Bind events
            canvas.bind("<ButtonPress-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
            win.bind("<Escape>", on_escape)
            
            # Focus
            win.focus_force()
            win.lift()
            
            print("[Selection] Window ready")
            
        except Exception as e:
            print(f"[Selection Error] {e}")
            import traceback
            traceback.print_exc()
            self.in_selection = False
            self._show_main()
            
    def _show_main(self):
        self.root.deiconify()
        self.root.lift()
        self._set_text("Press Ctrl+Alt+T or click '📷 New' to select text")
        self.status.configure(text="Ctrl+Alt+T = New | ✕ = Hide | Quit = Exit")
        
    def _translate(self, x1, y1, x2, y2):
        """Capture and translate selected area."""
        print(f"[Translate] Capturing region: ({x1}, {y1}) to ({x2}, {y2})")
        
        self.root.deiconify()
        self.root.lift()
        self._set_text("⏳ Capturing...")
        self.status.configure(text="Capturing screen...")
        
        def work():
            try:
                import time
                # Extra delay to ensure selection window is completely gone
                time.sleep(0.1)
                
                print(f"[Capture] Taking screenshot...")
                img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                print(f"[Capture] Image size: {img.size}")
                
                # Update status
                self.root.after(0, lambda: self._set_text("⏳ Extracting text..."))
                self.root.after(0, lambda: self.status.configure(text="Running OCR..."))
                
                text = self.ocr.extract_text(img)
                print(f"[OCR] Extracted: '{text[:100] if text else 'EMPTY'}...'")
                
                if not text or not text.strip():
                    self.root.after(0, lambda: self._show_result("", "No text detected in selection.\n\nTry selecting a larger area with clear text."))
                    return
                
                # Update status
                self.root.after(0, lambda: self._set_text("⏳ Translating..."))
                self.root.after(0, lambda: self.status.configure(text="Translating..."))
                
                result = self.translator.translate(text, self.current_language)
                print(f"[Trans] Result: '{result[:100] if result else 'EMPTY'}...'")
                
                self.root.after(0, lambda: self._show_result(text, result))
                
            except Exception as e:
                import traceback
                print(f"[Error] {e}")
                traceback.print_exc()
                self.root.after(0, lambda: self._show_result("", f"Error: {e}"))
                
        threading.Thread(target=work, daemon=True).start()
        
    def _show_result(self, original, translated):
        # Store translated text for TTS
        self.last_translated_text = translated or ""
        print(f"[TTS Storage] Stored for TTS: '{self.last_translated_text}'")
        
        # Always show both if we have original text, even if they are the same
        if original:
            out = f"📝 Original:\n{original}\n\n🌐 Translation:\n{translated or '...'}"
        else:
            out = translated or "No text"
            
        self._set_text(out)
        self.status.configure(text="🔊 = Read Aloud | Ctrl+Alt+T = New")
    
    def _init_tts(self):
        """Check if edge-tts is available."""
        try:
            import edge_tts
            import pygame
            import asyncio
            pygame.mixer.init()
            self.tts_available = True
            print("  ✅ TTS Ready (edge-tts - high quality)")
        except Exception as e:
            print(f"  ⚠️ TTS not available: {e}")
            self.tts_available = False
            
    def _summarize(self):
        """Summarize the current translation."""
        if not self.last_translated_text:
            self._set_text("No text to summarize. Please translate something first.")
            return
            
        if not self.gemini.is_available():
            self._set_text("Gemini service is not available (check API key or connection).")
            return
            
        print("[Summarize] Requesting summary...")
        self.status.configure(text="✨ Summarizing...")
        
        # Disable button to prevent spam
        self.summarize_btn.configure(state="disabled")
        
        def work():
            try:
                # Get full language name for better prompting
                from config import SUPPORTED_LANGUAGES
                lang_name = SUPPORTED_LANGUAGES.get(self.current_language, "English")
                
                summary = self.gemini.summarize(self.last_translated_text, target_language=lang_name)
                self.root.after(0, lambda: self._show_summary(summary))
            except Exception as e:
                print(f"[Summarize Error] {e}")
                self.root.after(0, lambda: self._set_text(f"Summarization failed: {e}"))
            finally:
                self.root.after(0, lambda: self.summarize_btn.configure(state="normal"))
                
        threading.Thread(target=work, daemon=True).start()
        
    def _show_summary(self, summary):
        """Append summary to text box."""
        current_text = self.textbox.get("1.0", "end").strip()
        # Avoid duplicating if already summarized (simple check)
        if "✨ Summary:" in current_text:
             # Strip old summary if we want to replace, or just append new one?
             # Let's just append for now, or maybe split?
             pass

        new_content = f"{current_text}\n\n✨ Summary:\n{summary}"
        self._set_text(new_content)
        self.status.configure(text="Summary generated | 🔊 = Read Aloud")
    
    def _read_aloud(self):
        """Read the translated text aloud using Microsoft Edge TTS."""
        text_to_read = self.last_translated_text
        target_lang = self.current_language
        
        print(f"[TTS] Button clicked")
        print(f"[TTS] Text to read: '{text_to_read[:50] if text_to_read else 'EMPTY'}...'")
        print(f"[TTS] Target language: {target_lang}")
        
        if not text_to_read or not text_to_read.strip():
            self._set_text("No translated text to read.\n\nSelect text first using 📷 New.")
            return
        
        if not self.tts_available:
            self._set_text("TTS not available.\n\nInstall: pip install edge-tts pygame")
            return
        
        self.status.configure(text="🔊 Generating audio...")
        
        # Copy variables for thread
        text_copy = str(text_to_read)
        lang_copy = str(target_lang)
        
        # Run TTS in background thread
        def speak_text(text, lang):
            try:
                import asyncio
                import edge_tts
                import pygame
                import os
                import tempfile
                
                # Map languages to Edge TTS voices
                # Find more voices: edge-tts --list-voices
                voice_map = {
                    'hi': 'hi-IN-MadhurNeural',      # Hindi (Male)
                    'bn': 'bn-IN-BashkarNeural',     # Bengali
                    'ta': 'ta-IN-ValluvarNeural',    # Tamil
                    'te': 'te-IN-MohanNeural',       # Telugu
                    'mr': 'mr-IN-ManoharNeural',     # Marathi
                    'gu': 'gu-IN-NiranjanNeural',    # Gujarati
                    'ur': 'ur-IN-SalmanNeural',      # Urdu
                    'kn': 'kn-IN-GaganNeural',       # Kannada
                    'ml': 'ml-IN-MidhunNeural',      # Malayalam
                    
                    'en': 'en-US-ChristopherNeural', # English
                    'es': 'es-ES-AlvaroNeural',      # Spanish
                    'fr': 'fr-FR-HenriNeural',       # French
                    'de': 'de-DE-ConradNeural',      # German
                    'it': 'it-IT-DiegoNeural',       # Italian
                    'pt': 'pt-BR-AntonioNeural',     # Portuguese
                    'ru': 'ru-RU-DmitryNeural',      # Russian
                    'ja': 'ja-JP-KeitaNeural',       # Japanese
                    'ko': 'ko-KR-InJoonNeural',      # Korean
                    'zh-CN': 'zh-CN-YunxiNeural',    # Chinese (Simplified)
                    'zh-TW': 'zh-TW-YunJheNeural',   # Chinese (Traditional)
                    'ar': 'ar-SA-HamedNeural',       # Arabic
                }
                
                voice = voice_map.get(lang, 'en-US-ChristopherNeural')
                print(f"[TTS] Using voice: {voice}")
                
                self.root.after(0, lambda: self.status.configure(text=f"🔊 Generating ({lang})..."))
                
                # Create temp file
                temp_file = os.path.join(tempfile.gettempdir(), "lingo_edge_tts.mp3")
                
                # Generate audio (async)
                async def generate():
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(temp_file)
                
                asyncio.run(generate())
                
                if not os.path.exists(temp_file):
                    print("[TTS] Failed to generate audio file")
                    return

                print(f"[TTS] Playing audio...")
                self.root.after(0, lambda: self.status.configure(text="🔊 Reading aloud..."))
                
                # Play with pygame
                try:
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                        
                    pygame.mixer.music.unload()
                except Exception as e:
                    print(f"[Playback Error] {e}")
                
                print("[TTS] Finished speaking")
                self.root.after(0, lambda: self.status.configure(text="🔊 = Read Aloud | Ctrl+Alt+T = New"))
                
                # Cleanup
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
            except Exception as e:
                print(f"[TTS Error] {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.status.configure(text="TTS error"))
        
        t = threading.Thread(target=speak_text, args=(text_copy, lang_copy))
        t.start()
    
    def _stop_tts(self):
        """Stop any ongoing text-to-speech."""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
        
    def _hide_window(self):
        """Hide window but keep app running."""
        print("[Hiding window]")
        self._stop_tts()
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
