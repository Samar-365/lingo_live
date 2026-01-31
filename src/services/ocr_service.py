"""
OCR Service for Lingo-Live - Multi-language Support
"""

import pytesseract
from PIL import Image, ImageEnhance
import os


class OCRService:
    """Multi-language OCR using Tesseract."""

    def __init__(self, tesseract_cmd: str = None):
        from config import TESSERACT_CMD
        
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        
        if not self._check_tesseract():
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

    def _check_tesseract(self):
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess for better OCR."""
        gray = image.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        return enhancer.enhance(1.5)

    def extract_text(self, image: Image.Image, preprocess: bool = True) -> str:
        """
        Extract text from image - supports multiple languages.
        Uses multiple language packs for better recognition.
        """
        if preprocess:
            image = self.preprocess_image(image)
        
        try:
            # Use multiple languages: English + common languages
            # Format: eng+hin+jpn+chi_sim+kor+fra+deu+spa+rus+ara
            # Only use installed language packs
            langs = self._get_available_langs()
            lang_str = '+'.join(langs) if langs else 'eng'
            
            # OCR config for better accuracy
            config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, lang=lang_str, config=config)
            return ' '.join(text.strip().split())
        except Exception as e:
            print(f"[OCR Error] {e}")
            # Fallback to English only
            try:
                text = pytesseract.image_to_string(image, lang='eng', config='--oem 3 --psm 6')
                return ' '.join(text.strip().split())
            except:
                return ""

    def _get_available_langs(self):
        """Get list of available Tesseract language packs."""
        try:
            available = pytesseract.get_languages()
            # Prioritize common languages
            priority = ['eng', 'hin', 'jpn', 'chi_sim', 'chi_tra', 'kor', 
                       'fra', 'deu', 'spa', 'rus', 'ara', 'por', 'ita']
            result = []
            for lang in priority:
                if lang in available:
                    result.append(lang)
            # Add eng as fallback if not present
            if 'eng' not in result and 'eng' in available:
                result.insert(0, 'eng')
            return result if result else ['eng']
        except:
            return ['eng']

    def is_available(self):
        return self._check_tesseract()
