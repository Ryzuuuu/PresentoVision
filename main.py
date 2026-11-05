#!/usr/bin/env python3
"""
PresentoVision — Hand Gesture Presentation Controller
YOLOv8n (scene context) + MediaPipe (21-landmark hand tracking)

Works with PowerPoint · Canva · Google Slides · Keynote
         LibreOffice Impress · PDF viewers (Acrobat, Evince, Okular)
"""

import os
import sys

# Ensure project root is on the path (allows `python main.py` from any cwd)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.engine import PresentoVision  # noqa: E402


BANNER = """
╔══════════════════════════════════════════════════╗
║   PresentoVision — Hand Gesture Slide Controller ║
║       YOLOv8n  +  MediaPipe  |  any presenter    ║
╚══════════════════════════════════════════════════╝

  GESTURE MAP
  ───────────────────────────────────────────────
  Open Palm  (Right hand)  →  Next Slide
  Open Palm  (Left hand)   →  Prev Slide
  Fist                     →  Pause / Autoplay
  One Finger               →  Screenshot
  Two Fingers              →  Fullscreen toggle
  Three Fingers            →  Quit App
  ───────────────────────────────────────────────
  Works with: PowerPoint · Canva · Google Slides
              Keynote · LibreOffice · PDF viewers
"""


def main() -> int:
    # Windows consoles redirected to a file/pipe default to a legacy code page
    # that cannot encode the banner; never crash on printing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    print(BANNER)
    try:
        app = PresentoVision()
        app.run()
    except KeyboardInterrupt:
        print("\n[PresentoVision] Interrupted.")
    except RuntimeError as exc:
        print(f"[PresentoVision] Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
