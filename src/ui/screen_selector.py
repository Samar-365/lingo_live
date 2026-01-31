"""
Screen Selection Module for Lingo-Live
Optimized for smooth, flicker-free selection.
"""

import tkinter as tk
from PIL import Image, ImageGrab


class ScreenSelector:
    """Smooth fullscreen drag-to-select."""

    def __init__(self, on_selection_complete=None):
        self.on_selection_complete = on_selection_complete
        self.start_x = 0
        self.start_y = 0
        self.root = None
        self.rect = None

    def start_selection(self):
        """Show selection overlay."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Get screen size
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        # Configure fullscreen overlay
        self.root.geometry(f"{w}x{h}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.2)
        self.root.configure(bg='#000000')
        self.root.config(cursor="cross")
        
        # Canvas
        self.canvas = tk.Canvas(self.root, width=w, height=h, highlightthickness=0, bg='#000000')
        self.canvas.pack()
        
        # Instructions
        self.canvas.create_text(w//2, 40, text="Drag to select • ESC to cancel", 
                                font=("Segoe UI", 14), fill="#00ff00")
        
        # Events
        self.canvas.bind("<Button-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.root.bind("<Escape>", self._cancel)
        
        # Show
        self.root.deiconify()
        self.root.focus_force()
        self.root.mainloop()

    def _press(self, e):
        self.start_x, self.start_y = e.x, e.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, 
                                                   outline='#00ff00', width=2)

    def _drag(self, e):
        self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def _release(self, e):
        x1, y1 = min(self.start_x, e.x), min(self.start_y, e.y)
        x2, y2 = max(self.start_x, e.x), max(self.start_y, e.y)
        
        # Close overlay first
        self._close()
        
        # Capture if valid area
        if x2 - x1 > 5 and y2 - y1 > 5:
            # Small delay to let overlay close
            import time
            time.sleep(0.05)
            
            # Capture screen
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            if self.on_selection_complete:
                self.on_selection_complete(img, (x1, y1))

    def _cancel(self, e=None):
        self._close()

    def _close(self):
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
            self.root = None
