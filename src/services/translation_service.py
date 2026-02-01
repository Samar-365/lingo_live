"""
Translation Service for Lingo-Live
Uses Lingo.dev API as primary translation service.
Falls back to Google Translate if Lingo.dev fails.
"""

import asyncio
import os
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_TARGET_LANGUAGE, SUPPORTED_LANGUAGES, LINGODOTDEV_API_KEY


class TranslationService:
    """Translation service using Lingo.dev API primarily."""

    def __init__(self, target_language: str = None):
        self.target_language = target_language or DEFAULT_TARGET_LANGUAGE
        self.api_key = LINGODOTDEV_API_KEY
        self._use_lingodotdev = True
        
        # Check if lingodotdev is available
        try:
            from lingodotdev.engine import LingoDotDevEngine
            self._lingo_engine_class = LingoDotDevEngine
            print("[Translation] ✅ Using Lingo.dev API (primary)")
        except ImportError:
            print("[Translation] ⚠️ lingodotdev not installed, falling back to Google")
            self._use_lingodotdev = False
            self._init_fallback()
            
    def _init_fallback(self):
        """Initialize Google Translate as fallback."""
        try:
            from deep_translator import GoogleTranslator
            self._google = GoogleTranslator(source='auto', target=self.target_language)
            print("[Translation] ✅ Google Translate fallback ready")
        except:
            self._google = None

    def set_target_language(self, language_code: str):
        if language_code in SUPPORTED_LANGUAGES:
            self.target_language = language_code
            if not self._use_lingodotdev and hasattr(self, '_google') and self._google:
                from deep_translator import GoogleTranslator
                self._google = GoogleTranslator(source='auto', target=language_code)

    def translate(self, text: str, target_lang: str = None) -> str:
        """Translate text using Lingo.dev API primarily."""
        if not text or not text.strip():
            return ""

        target = target_lang or self.target_language
        
        # Try Lingo.dev first
        if self._use_lingodotdev and self.api_key:
            try:
                result = self._translate_with_lingodotdev(text, target)
                if result:
                    return result
            except Exception as e:
                print(f"[Lingo.dev Error] {e}")
        
        # Fallback to Google Translate
        return self._translate_with_google(text, target)
    
    def _translate_with_lingodotdev(self, text: str, target_lang: str) -> str:
        """Translate using Lingo.dev API."""
        try:
            from lingodotdev.engine import LingoDotDevEngine
            
            # Run async translation in sync context
            async def do_translate():
                result = await LingoDotDevEngine.quick_translate(
                    text,
                    api_key=self.api_key,
                    source_locale="auto",  # Auto-detect source
                    target_locale=target_lang
                )
                return result
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(do_translate())
            finally:
                loop.close()
            
            return result if result else text
            
        except Exception as e:
            print(f"[Lingo.dev Translation Error] {e}")
            raise
    
    def _translate_with_google(self, text: str, target_lang: str) -> str:
        """Fallback translation using Google Translate."""
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target=target_lang)
            result = translator.translate(text)
            return result if result else text
        except Exception as e:
            print(f"[Google Translation Error] {e}")
            return f"[Translation failed: {e}]"

    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES.copy()
