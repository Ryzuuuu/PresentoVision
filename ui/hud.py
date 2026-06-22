"""
GesturePPT – HUD renderer.
All OpenCV drawing lives here; no business logic.
"""

import time
import cv2
import numpy as np

from config.settings import COOLDOWN_SEC
from config.theme import (
    C_PANEL, C_GREEN, C_RED, C_BLUE, C_GOLD, C_CYAN,
    C_MAGENTA, C_WHITE, C_GRAY, C_DARK, C_ORANGE,
    FONT, FONT_MONO, GESTURE_GUIDE,
)

PANEL_W = 300


def _blend_rect(img: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                color: tuple, alpha: float = 0.65):
    """Semi-transparent filled rectangle via alpha blend."""
    sub     = img[y1:y2, x1:x2]
    overlay = np.full_like(sub, color)
    cv2.addWeighted(overlay, 1 - alpha, sub, alpha, 0, sub)


def _label(img, text, x, y, font=FONT, scale=0.44, color=C_WHITE, thick=1):
    cv2.putText(img, text, (x, y), font, scale, color, thick, cv2.LINE_AA)


def draw(
    frame: np.ndarray,
    state: dict,
    mp_hands,
    mp_draw,
    mp_style,
    hand_lm,
    yolo_boxes: list,
) -> np.ndarray:
    h, w = frame.shape[:2]
    now  = time.time()

    # ── Side-panel background ─────────────────────────────────────────────────
    _blend_rect(frame, 0, 0, PANEL_W, h, C_PANEL, alpha=0.22)
    cv2.rectangle(frame, (PANEL_W, 0), (PANEL_W + 1, h), C_DARK, -1)

    y = 38

    # Title block
    cv2.putText(frame, "GesturePPT", (14, y), FONT_MONO, 0.95, C_CYAN, 2, cv2.LINE_AA)
    y += 22
    _label(frame, "YOLOv8n  +  MediaPipe", 14, y, scale=0.37, color=C_GRAY)
    y += 18
    cv2.line(frame, (14, y), (PANEL_W - 14, y), C_DARK, 1)
    y += 16

    # FPS + hand label
    fps       = state.get("fps", 0.0)
    hand_lbl  = state.get("hand_label", "")
    _label(frame, f"FPS {fps:4.1f}", 14, y, color=C_GREEN)
    if hand_lbl:
        _label(frame, f"{hand_lbl} hand", 150, y, color=C_BLUE)
    y += 24

    # Raw / confirmed gesture
    raw_g  = state.get("raw_gesture",  "—")
    conf_g = state.get("conf_gesture", "—")
    _label(frame, "RAW :", 14, y, color=C_GRAY)
    _label(frame, raw_g,   70, y, color=C_WHITE)
    y += 20

    flash = (now - state.get("last_action_ts", 0)) < 1.8
    conf_col = C_GOLD if flash else C_GREEN
    _label(frame, "CONFIRMED :", 14, y, color=C_GRAY)
    cv2.putText(frame, conf_g, (120, y), FONT, 0.54, conf_col, 2, cv2.LINE_AA)
    y += 26
    cv2.line(frame, (14, y), (PANEL_W - 14, y), C_DARK, 1)
    y += 14

    # Last action (wrapped)
    action_txt = state.get("last_action", "Ready — show a hand gesture")
    act_col    = C_GOLD if flash else C_WHITE
    _label(frame, "ACTION", 14, y, color=C_GRAY, scale=0.39)
    y += 17
    words = action_txt.split()
    line, lines = "", []
    for wd in words:
        if len(line) + len(wd) + 1 <= 25:
            line += (" " if line else "") + wd
        else:
            lines.append(line); line = wd
    lines.append(line)
    for ln in lines[:2]:
        cv2.putText(frame, ln, (14, y), FONT, 0.54, act_col, 1, cv2.LINE_AA)
        y += 20
    y += 4
    cv2.line(frame, (14, y), (PANEL_W - 14, y), C_DARK, 1)
    y += 14

    # Stats row
    slides  = state.get("slides", 0)
    paused  = state.get("paused", False)
    fs_on   = state.get("fullscreen", False)
    _label(frame, f"Slides : {slides}", 14, y, color=C_WHITE)
    y += 19
    st_col = C_RED if paused else C_GREEN
    st_txt = "PAUSED" if paused else "RUNNING"
    _label(frame, f"Status : {st_txt}", 14, y, color=st_col)
    y += 19
    fs_col = C_CYAN if fs_on else C_GRAY
    _label(frame, f"Fullscr: {'ON' if fs_on else 'OFF'}", 14, y, color=fs_col)
    y += 22
    cv2.line(frame, (14, y), (PANEL_W - 14, y), C_DARK, 1)
    y += 12

    # Gesture guide
    _label(frame, "GESTURE GUIDE", 14, y, color=C_CYAN, scale=0.40)
    y += 17
    for sym, desc, col in GESTURE_GUIDE:
        _label(frame, sym,  14,  y, color=col,   scale=0.37)
        _label(frame, desc, 155, y, color=C_WHITE, scale=0.37)
        y += 17

    # Cooldown bar (bottom of panel)
    elapsed = now - state.get("last_gesture_ts", 0)
    pct     = min(elapsed / COOLDOWN_SEC, 1.0)
    bx1, bx2 = 14, PANEL_W - 14
    by1 = h - 26
    cv2.rectangle(frame, (bx1, by1), (bx2, by1 + 9), C_DARK, -1)
    bar_col = C_GREEN if pct >= 1.0 else C_GRAY
    cv2.rectangle(frame, (bx1, by1), (bx1 + int((bx2 - bx1) * pct), by1 + 9), bar_col, -1)
    _label(frame, "COOLDOWN", 14, by1 - 5, color=C_GRAY, scale=0.35)

    # ── Hand landmarks (camera region) ───────────────────────────────────────
    if hand_lm is not None:
        mp_draw.draw_landmarks(
            frame, hand_lm,
            mp_hands.HAND_CONNECTIONS,
            mp_style.get_default_hand_landmarks_style(),
            mp_style.get_default_hand_connections_style(),
        )

    # ── YOLO person boxes ─────────────────────────────────────────────────────
    for box in yolo_boxes:
        x1, y1_, x2, y2_ = map(int, box)
        cv2.rectangle(frame, (x1, y1_), (x2, y2_), C_GRAY, 1)
        _label(frame, "person", x1 + 4, y1_ - 4, color=C_GRAY, scale=0.37)

    # ── Flash border (action feedback) ───────────────────────────────────────
    if flash:
        t_norm    = (now - state.get("last_action_ts", 0)) / 1.8
        alpha_f   = max(0.0, 1.0 - t_norm)
        gcolor    = state.get("flash_color", C_GOLD)
        thickness = max(2, int(8 * alpha_f))
        cv2.rectangle(frame, (PANEL_W + 2, 2), (w - 2, h - 2), gcolor, thickness)

    return frame
