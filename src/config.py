"""
Configuration settings for Lingo-Live
"""

# Lingo.dev API Key
LINGODOTDEV_API_KEY = "api_vtllh8r409171u3dfuqp4ii7"

# Hotkey combination to trigger translation (Ctrl+Alt+T)
HOTKEY_COMBINATION = {'ctrl', 'alt', 't'}

# Screen capture region size (pixels around the mouse cursor)
CAPTURE_WIDTH = 400
CAPTURE_HEIGHT = 150

# Default target language for translation
DEFAULT_TARGET_LANGUAGE = 'en'

# Supported languages (code: display name)
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
}

# Overlay display duration (seconds)
OVERLAY_DISPLAY_DURATION = 8

# Overlay appearance
OVERLAY_WIDTH = 450
OVERLAY_HEIGHT = 200
OVERLAY_OPACITY = 0.95
OVERLAY_BG_COLOR = "#1a1a2e"
OVERLAY_TEXT_COLOR = "#eaeaea"
OVERLAY_ACCENT_COLOR = "#4a90d9"
OVERLAY_FONT_FAMILY = "Segoe UI"
OVERLAY_FONT_SIZE = 14

# Tesseract path (set to None to use system PATH, or provide full path)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
