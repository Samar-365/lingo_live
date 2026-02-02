"""
Gemini Service for Lingo-Live
Wraps the google-generativeai library for text summarization.
"""

import google.generativeai as genai

# Hardcoded API key as requested
# In production, use os.environ.get("GEMINI_API_KEY")
API_KEY = "AIzaSyA55TexTd-omj93VJJAfHMn_nBIZJeCSCg"

class GeminiService:
    """Service to interact with Google Gemini models."""
    
    def __init__(self):
        try:
            genai.configure(api_key=API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self._available = True
        except Exception as e:
            print(f"[Gemini] Init Error: {e}")
            self._available = False

    def is_available(self):
        return self._available

    def summarize(self, text: str, target_language: str = None) -> str:
        """
        Summarize the given text using Gemini.
        Args:
            text: Text to summarize
            target_language: Optional language to summarize in (e.g. "Spanish")
        Returns the summary.
        """
        if not self._available:
            return "Gemini service is not available."

        if not text or not text.strip():
             return "No text to summarize."

        try:
            lang_instruction = f" in {target_language}" if target_language else " in the same language as the text"
            prompt = f"Please summarize the following text concisely{lang_instruction}:\n\n{text}"
            
            response = self.model.generate_content(prompt)
            if response.text:
                 return response.text
            return "No summary generated."
        except Exception as e:
            return f"Summarization failed: {str(e)}"
