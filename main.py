#!/usr/bin/env python3
"""
GesturePPT — Hand Gesture Presentation Controller
YOLOv8n (scene context) + MediaPipe (21-landmark hand tracking)

Works with PowerPoint · Canva · Google Slides · Keynote
         LibreOffice Impress · PDF viewers (Acrobat, Evince, Okular)
"""

import sys
import os

# Ensure project root is on the path (allows `python main.py` from any cwd)
sys.path.insert(0, os.path.dirname(__file__))

from app.engine import GesturePPT


BANNER = """
╔══════════════════════════════════════════════════╗
║     GesturePPT — Hand Gesture Slide Controller   ║
║       YOLOv8n  +  MediaPipe  |  any presenter    ║
╚══════════════════════════════════════════════════╝

  GESTURE MAP
  ───────────────────────────────────────────────
  🖐  Open Palm  (Right hand)  →  Next Slide
  🖐  Open Palm  (Left hand)   →  Prev Slide
  ✊  Fist                     →  Pause / Autoplay
  ☝  One Finger               →  Screenshot
  ✌  Two Fingers              →  Fullscreen toggle
  🤟  Three Fingers            →  Quit App
  ───────────────────────────────────────────────
  Works with: PowerPoint · Canva · Google Slides
              Keynote · LibreOffice · PDF viewers
"""


def main():
    print(BANNER)
    try:
        app = GesturePPT()
        app.run()
    except KeyboardInterrupt:
        print("\n[GesturePPT] Interrupted.")


if __name__ == "__main__":
    main()
