"""
PresentoVision – runtime config.
Tweak these values without touching any other file.
"""

import os
import platform

# ── Window ────────────────────────────────────────────────────────────────────
WIN_NAME     = "PresentoVision"
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

# ── YOLO (person overlay) ─────────────────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"   # downloaded automatically on first run
YOLO_CONF  = 0.45

# ── MediaPipe confidence ──────────────────────────────────────────────────────
MP_DETECT_CONF  = 0.80
MP_TRACK_CONF   = 0.80

# ── Screenshots ───────────────────────────────────────────────────────────────
# Created lazily on the first screenshot. Override with PRESENTOVISION_SHOTS_DIR.
SCREENSHOTS_DIR = os.environ.get("PRESENTOVISION_SHOTS_DIR") or os.path.join(
    os.path.expanduser("~"), "Desktop", "PresentoVision_Shots"
)

# ── Platform ─────────────────────────────────────────────────────────────────
SYSTEM = platform.system()   # "Windows" | "Darwin" | "Linux"
