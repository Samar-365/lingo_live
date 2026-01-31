"""
Overlay UI Module for Lingo-Live
Optimized overlay that hides during selection.
"""

import customtkinter as ctk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_OPACITY,
    OVERLAY_BG_COLOR, OVERLAY_TEXT_COLOR, OVERLAY_ACCENT_COLOR,
    OVERLAY_FONT_FAMILY, OVERLAY_FONT_SIZE,
    SUPPORTED_LANGUAGES, DEFAULT_TARGET_LANGUAGE
)


class OverlayWindow:
    """Optimized overlay window."""

    def __init__(self, on_language_change=None, on_new_translation=None):
        self.on_language_change = on_language_change
        self.on_new_translation = on_new_translation
        self.current_language = DEFAULT_TARGET_LANGUAGE
        self._root = None
        self._is_visible = False
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _create_window(self):
        """Create the overlay."""
        self._root = ctk.CTk()
        self._root.title("Lingo-Live")
        self._root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+100+100")
        self._root.attributes('-topmost', True)
        self._root.attributes('-alpha', OVERLAY_OPACITY)
        self._root.overrideredirect(True)
        self._root.configure(fg_color=OVERLAY_BG_COLOR)
        
        # Main frame
        self.main_frame = ctk.CTkFrame(self._root, fg_color=OVERLAY_BG_COLOR,
                                        corner_radius=15, border_width=2,
                                        border_color=OVERLAY_ACCENT_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        self.header = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=40)
        self.header.pack(fill="x", padx=10, pady=(10, 5))
        
        # Title
        self.title = ctk.CTkLabel(self.header, text="🌐 Lingo-Live",
                                   font=(OVERLAY_FONT_FAMILY, 14, "bold"),
                                   text_color=OVERLAY_ACCENT_COLOR)
        self.title.pack(side="left")
        
        # Language dropdown (first, after title)
        self.lang_var = ctk.StringVar(value=SUPPORTED_LANGUAGES.get(self.current_language, "English"))
        self.lang_menu = ctk.CTkComboBox(self.header, values=list(SUPPORTED_LANGUAGES.values()),
                                          variable=self.lang_var, width=100, height=28,
                                          fg_color="#2a2a4a", border_color=OVERLAY_ACCENT_COLOR,
                                          button_color=OVERLAY_ACCENT_COLOR,
                                          command=self._lang_changed)
        self.lang_menu.pack(side="left", padx=(15, 0))
        
        # Close button
        self.close_btn = ctk.CTkButton(self.header, text="✕", width=30, height=30,
                                        fg_color="transparent", hover_color="#ff4444",
                                        text_color=OVERLAY_TEXT_COLOR, command=self.hide)
        self.close_btn.pack(side="right")
        
        # New button
        self.new_btn = ctk.CTkButton(self.header, text="📷 New", width=70, height=30,
                                      fg_color=OVERLAY_ACCENT_COLOR, hover_color="#6ab0f9",
                                      text_color="white", font=(OVERLAY_FONT_FAMILY, 12, "bold"),
                                      command=self._new_click)
        self.new_btn.pack(side="right", padx=(0, 10))
        
        # Text area
        self.text = ctk.CTkTextbox(self.main_frame, fg_color="#2a2a4a",
                                    text_color=OVERLAY_TEXT_COLOR,
                                    font=(OVERLAY_FONT_FAMILY, OVERLAY_FONT_SIZE),
                                    corner_radius=10, wrap="word")
        self.text.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.text.insert("1.0", "Press Ctrl+Alt+T or click 📷 New")
        self.text.configure(state="disabled")
        
        # Status
        self.status = ctk.CTkLabel(self.main_frame, text="Ready | Press ESC to exit",
                                    font=(OVERLAY_FONT_FAMILY, 10), text_color="#888")
        self.status.pack(pady=(0, 5))
        
        # ESC to exit binding
        self._root.bind("<Escape>", lambda e: self._exit_app())
        
        # Dragging
        self._drag = {"x": 0, "y": 0}
        for w in [self.header, self.title]:
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)
        
        self._is_visible = True

    def _start_drag(self, e):
        self._drag["x"], self._drag["y"] = e.x, e.y

    def _do_drag(self, e):
        x = self._root.winfo_x() + e.x - self._drag["x"]
        y = self._root.winfo_y() + e.y - self._drag["y"]
        self._root.geometry(f"+{x}+{y}")

    def _lang_changed(self, choice):
        for code, name in SUPPORTED_LANGUAGES.items():
            if name == choice:
                self.current_language = code
                if self.on_language_change:
                    self.on_language_change(code)
                break

    def _new_click(self):
        """Hide overlay and start new translation."""
        self.hide()
        if self.on_new_translation:
            # Small delay to ensure window is hidden
            self._root.after(50, self.on_new_translation)

    def show_text(self, original: str, translated: str, pos: tuple = None):
        """Show translation result."""
        if not self._root:
            return
        
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        
        if original and original != translated:
            content = f"📝 Original:\n{original}\n\n🌐 Translation:\n{translated}"
        else:
            content = translated or "No text detected"
        
        self.text.insert("1.0", content)
        self.text.configure(state="disabled")
        
        if pos:
            self._root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+{pos[0]}+{pos[1]+20}")
        
        self._root.deiconify()
        self._root.lift()
        self._is_visible = True
        self.status.configure(text="Drag header to move")

    def show_loading(self):
        """Show loading."""
        if not self._root:
            return
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "⏳ Processing...")
        self.text.configure(state="disabled")
        self.status.configure(text="Please wait...")
        self._root.deiconify()
        self._root.lift()
        self._is_visible = True

    def show_error(self, msg: str):
        """Show error."""
        if not self._root:
            return
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", f"❌ Error\n{msg}")
        self.text.configure(state="disabled")
        self._root.deiconify()
        self._is_visible = True

    def _exit_app(self):
        """Exit the app when ESC is pressed."""
        print("[ESC pressed - Exiting]")
        self.quit()

    def hide(self):
        """Hide overlay."""
        if self._root:
            self._root.withdraw()
            self._is_visible = False

    def is_visible(self):
        return self._is_visible

    def get_current_language(self):
        return self.current_language

    def run(self):
        """Start overlay."""
        self._create_window()
        print("[Overlay] Ready")
        self._root.mainloop()

    def schedule_action(self, func, *args):
        """Schedule on main thread."""
        if self._root:
            self._root.after(0, lambda: func(*args))

    def quit(self):
        """Quit."""
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except:
                pass
