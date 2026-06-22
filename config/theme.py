"""
GesturePPT – HUD color palette and font handles.
All BGR tuples; import after cv2 is available.
"""

import cv2

# ── BGR palette ───────────────────────────────────────────────────────────────
C_PANEL   = (20,  20,  35)
C_GREEN   = (50,  230, 130)
C_RED     = (60,  80,  240)
C_BLUE    = (230, 140, 50)
C_GOLD    = (30,  200, 255)
C_CYAN    = (230, 215, 0)
C_MAGENTA = (210, 60,  200)
C_WHITE   = (240, 240, 240)
C_GRAY    = (100, 100, 115)
C_DARK    = (35,  35,  50)
C_ORANGE  = (30,  160, 255)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT      = cv2.FONT_HERSHEY_SIMPLEX
FONT_MONO = cv2.FONT_HERSHEY_DUPLEX

# ── Gesture guide rows: (symbol, description, color) ─────────────────────────
GESTURE_GUIDE = [
    ("🖐  Palm  (Right)",  "Next Slide  →",    C_GREEN),
    ("🖐  Palm  (Left)",   "Prev Slide  ←",    C_BLUE),
    ("✊  Fist",           "Pause / Auto",      C_RED),
    ("☝  One Finger",     "Screenshot  📸",    C_GOLD),
    ("✌  Two Fingers",    "Fullscreen  ⇄",     C_CYAN),
    ("🤟  Three Fingers",  "Quit App",          C_MAGENTA),
]
