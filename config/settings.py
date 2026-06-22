"""
GesturePPT – runtime config.
Tweak these values without touching any other file.
"""

import os
import platform

# ── Window ────────────────────────────────────────────────────────────────────
WIN_NAME     = "GesturePPT"
WIN_W        = 860
WIN_H        = 540

# ── Camera ────────────────────────────────────────────────────────────────────
CAM_INDEX    = 0
CAM_W        = 1280
CAM_H        = 720
CAM_FPS      = 60

# ── Gesture timing ────────────────────────────────────────────────────────────
COOLDOWN_SEC   = 1.0   # seconds between distinct triggers
CONFIRM_FRAMES = 6     # majority-vote window (anti-flicker)
YOLO_SKIP      = 4     # run YOLO every N frames (saves CPU)

# ── MediaPipe confidence ──────────────────────────────────────────────────────
MP_DETECT_CONF  = 0.80
MP_TRACK_CONF   = 0.80

# ── Screenshots ───────────────────────────────────────────────────────────────
SCREENSHOTS_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "GesturePPT_Shots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ── Platform ─────────────────────────────────────────────────────────────────
SYSTEM = platform.system()   # "Windows" | "Darwin" | "Linux"
