"""
Screen Capture Service for Lingo-Live
Uses MSS for fast, cross-platform screen capture.
"""

import mss
import mss.tools
from PIL import Image
from pynput import mouse


class ScreenCaptureService:
    """
    Handles screen capture operations around the mouse cursor.
    """

    def __init__(self):
        # Don't create MSS instance here - create per-thread when needed
        pass

    def get_mouse_position(self) -> tuple[int, int]:
        """
        Get the current mouse cursor position.
        
        Returns:
            Tuple of (x, y) coordinates.
        """
        return mouse.Controller().position

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """
        Capture a region of the screen.
        
        Args:
            x: X coordinate of the top-left corner.
            y: Y coordinate of the top-left corner.
            width: Width of the capture region.
            height: Height of the capture region.
            
        Returns:
            PIL Image of the captured region.
        """
        monitor = {
            "top": y,
            "left": x,
            "width": width,
            "height": height
        }
        
        # Create MSS instance in the current thread
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes(
                "RGB",
                (screenshot.width, screenshot.height),
                screenshot.rgb
            )
        
        return img

    def capture_around_mouse(self, width: int, height: int) -> tuple[Image.Image, tuple[int, int]]:
        """
        Capture a region centered around the current mouse position.
        
        Args:
            width: Width of the capture region.
            height: Height of the capture region.
            
        Returns:
            Tuple of (PIL Image, (x, y) top-left position of capture).
        """
        mouse_x, mouse_y = self.get_mouse_position()
        
        # Calculate top-left corner (centered around mouse)
        x = max(0, mouse_x - width // 2)
        y = max(0, mouse_y - height // 2)
        
        img = self.capture_region(x, y, width, height)
        
        return img, (x, y)

    def close(self):
        """Close the screen capture resources."""
        pass  # Nothing to close since we create MSS per-capture

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
