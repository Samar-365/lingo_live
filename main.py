"""
Lingo-Live - Real-Time Screen Translation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from app import main

if __name__ == "__main__":
    main()
