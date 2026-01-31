"""
Main Controller for Lingo-Live - Optimized
"""

import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keyboard
from services.ocr_service import OCRService
from services.translation_service import TranslationService
from ui.overlay import OverlayWindow
from ui.screen_selector import ScreenSelector
from config import DEFAULT_TARGET_LANGUAGE

HOTKEY = 'ctrl+alt+t'


class LingoLiveController:
    """Optimized controller."""

    def __init__(self):
        self.ocr = OCRService()
        self.translator = TranslationService()
        self.overlay = None
        self._selecting = False

    def _on_lang_change(self, code):
        self.translator.set_target_language(code)

    def _start_new(self):
        """Start new translation - hide overlay first."""
        if self._selecting:
            return
        self._selecting = True
        
        # Hide overlay
        if self.overlay:
            self.overlay.schedule_action(self.overlay.hide)
        
        # Start selection after small delay
        threading.Thread(target=self._select, daemon=True).start()

    def _select(self):
        """Run selection."""
        import time
        time.sleep(0.1)  # Wait for overlay to hide
        
        try:
            selector = ScreenSelector(on_selection_complete=self._on_selected)
            selector.start_selection()
        except Exception as e:
            print(f"[Error] {e}")
        finally:
            self._selecting = False

    def _on_selected(self, image, pos):
        """Process selection."""
        threading.Thread(target=self._translate, args=(image, pos), daemon=True).start()

    def _translate(self, image, pos):
        """Do OCR and translation."""
        try:
            if self.overlay:
                self.overlay.schedule_action(self.overlay.show_loading)
            
            # OCR
            text = self.ocr.extract_text(image)
            if not text:
                if self.overlay:
                    self.overlay.schedule_action(self.overlay.show_text, "", "No text found", pos)
                return
            
            print(f"[OCR] {text[:50]}...")
            
            # Translate
            lang = self.overlay.get_current_language() if self.overlay else DEFAULT_TARGET_LANGUAGE
            result = self.translator.translate(text, lang)
            
            print(f"[Trans] {result[:50]}...")
            
            if self.overlay:
                self.overlay.schedule_action(self.overlay.show_text, text, result, pos)
                
        except Exception as e:
            print(f"[Error] {e}")
            if self.overlay:
                self.overlay.schedule_action(self.overlay.show_error, str(e))

    def _exit_app(self):
        """Exit the application."""
        print("\n[Exiting...]")
        if self.overlay:
            self.overlay.schedule_action(self.overlay.quit)

    def start(self):
        """Start app."""
        print("=" * 45)
        print("  🌐 Lingo-Live")
        print("=" * 45)
        print("  Ctrl+Alt+T or 📷 New → Drag → Release")
        print("  ESC during selection to cancel")
        print("  ESC in overlay to exit app")
        print("=" * 45)
        
        if self.ocr.is_available():
            print("  ✅ OCR Ready")
        else:
            print("  ⚠️ Tesseract not found")
        
        keyboard.add_hotkey(HOTKEY, self._start_new, suppress=False)
        keyboard.add_hotkey('escape', self._exit_app, suppress=False)
        
        self.overlay = OverlayWindow(
            on_language_change=self._on_lang_change,
            on_new_translation=self._start_new
        )
        
        try:
            self.overlay.run()
        except:
            pass
        finally:
            keyboard.unhook_all()
            print("[Done]")


def main():
    LingoLiveController().start()


if __name__ == "__main__":
    main()
