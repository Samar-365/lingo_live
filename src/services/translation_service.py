"""
Translation Service for Lingo-Live - Optimized for Speed
Uses Google Translate for fast response, with Lingo.dev as option.
"""

import os
from typing import Optional

from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound, RequestError, TooManyRequests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_TARGET_LANGUAGE, SUPPORTED_LANGUAGES, LINGODOTDEV_API_KEY


class TranslationService:
    """Fast translation service - Google Translate primary for speed."""

    def __init__(self, target_language: str = None):
        self.target_language = target_language or DEFAULT_TARGET_LANGUAGE
        self._translator = GoogleTranslator(source='auto', target=self.target_language)
        print("[Translation] ✅ Using Google Translate (fast mode)")

    def set_target_language(self, language_code: str):
        if language_code in SUPPORTED_LANGUAGES:
            self.target_language = language_code
            self._translator = GoogleTranslator(source='auto', target=language_code)

    def translate(self, text: str, target_lang: str = None) -> str:
        """Translate text quickly."""
        if not text or not text.strip():
            return ""

        target = target_lang or self.target_language
        
        try:
            if target != self.target_language:
                translator = GoogleTranslator(source='auto', target=target)
            else:
                translator = self._translator
            
            result = translator.translate(text)
            return result if result else text
        except Exception as e:
            return f"[Translation error: {e}]"

    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES.copy()
