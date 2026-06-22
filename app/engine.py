"""
GesturePPT – application engine.
Owns the camera loop, model inference, and gesture dispatch.
"""

import time
import os
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from ultralytics import YOLO

import pyautogui

from config.settings import (
    WIN_NAME, WIN_W, WIN_H, CAM_INDEX, CAM_W, CAM_H, CAM_FPS,
    COOLDOWN_SEC, CONFIRM_FRAMES, YOLO_SKIP,
    MP_DETECT_CONF, MP_TRACK_CONF,
)
from config.theme import C_GREEN, C_RED, C_BLUE, C_GOLD, C_CYAN, C_MAGENTA, C_GRAY
from core.gesture  import Gesture, FingerState
from core.buffer   import GestureBuffer
from core.controller import SlideController
from ui.hud        import draw as hud_draw
from ui.topmost    import TopMost


class GestureEngine:
    """
    Gesture → Action dispatch table.
    Hand label is forwarded so OPEN_PALM can branch on left/right.
    """

    # Maps gesture → (description, flash_color)
    META = {
        Gesture.OPEN_PALM:     ("Palm",         C_GREEN),
        Gesture.FIST:          ("Pause / Auto",  C_RED),
        Gesture.ONE_FINGER:    ("Screenshot 📸", C_GOLD),
        Gesture.PEACE:         ("Fullscreen ⇄",  C_CYAN),
        Gesture.THREE_FINGERS: ("Quit App",       C_MAGENTA),
    }

    def __init__(self):
        self._ctrl       = SlideController()
        self._slides     = 0
        self._paused     = False
        self._fullscreen = False

    def dispatch(self, gesture: str, hand_label: str) -> tuple:
        """
        Execute the action for `gesture`.
        Returns (result_message, flash_color) or (None, None) if gesture unmapped.
        """
        if gesture not in self.META:
            return None, None

        _, color = self.META[gesture]

        if gesture == Gesture.OPEN_PALM:
            if hand_label == "Right":
                self._ctrl.next_slide()
                self._slides += 1
                return f"Next Slide → (#{self._slides})", C_GREEN
            else:
                self._ctrl.prev_slide()
                self._slides = max(0, self._slides - 1)
                return f"Prev Slide ← (#{self._slides})", C_BLUE

        if gesture == Gesture.FIST:
            self._ctrl.pause_play()
            self._paused = not self._paused
            return ("⏸ Paused" if self._paused else "▶ Resumed"), C_RED

        if gesture == Gesture.ONE_FINGER:
            path = self._ctrl.screenshot()
            return f"📸 {os.path.basename(path)}", C_GOLD

        if gesture == Gesture.PEACE:
            if self._fullscreen:
                self._ctrl.exit_fullscreen()
                self._fullscreen = False
                return "🗗 Fullscreen OFF", C_GRAY
            else:
                self._ctrl.enter_fullscreen()
                self._fullscreen = True
                return "🔲 Fullscreen ON", C_CYAN

        if gesture == Gesture.THREE_FINGERS:
            return "👋 Quitting…", C_MAGENTA

        return None, None

    @property
    def slides(self): return self._slides

    @property
    def paused(self): return self._paused

    @property
    def fullscreen(self): return self._fullscreen


class GesturePPT:

    def __init__(self):
        # MediaPipe
        self._mp_hands = mp.solutions.hands
        self._mp_draw  = mp.solutions.drawing_utils
        self._mp_style = mp.solutions.drawing_styles
        self._hands    = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=MP_DETECT_CONF,
            min_tracking_confidence=MP_TRACK_CONF,
        )

        # YOLOv8n (person scene context)
        print("[GesturePPT] Loading YOLOv8n …")
        self._yolo = YOLO("yolov8n.pt")
        print("[GesturePPT] YOLOv8n ready.")

        # Camera
        self._cap = cv2.VideoCapture(CAM_INDEX)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        self._cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

        # Subsystems
        self._engine    = GestureEngine()
        self._g_buf     = GestureBuffer(CONFIRM_FRAMES)

        # Runtime state
        self._running         = True
        self._last_gesture_ts = 0.0
        self._last_action_ts  = 0.0
        self._last_action     = "Ready — show a hand gesture"
        self._flash_color     = C_GOLD

        self._fps_buf        = deque(maxlen=30)
        self._yolo_boxes: list = []
        self._yolo_skip       = 0

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE    = 0

    # ── gesture dispatch ──────────────────────────────────────────────────────
    def _trigger(self, gesture: str, hand_label: str):
        now = time.time()
        if (now - self._last_gesture_ts) < COOLDOWN_SEC:
            return

        msg, color = self._engine.dispatch(gesture, hand_label)
        if msg is None:
            return

        self._last_action     = msg
        self._flash_color     = color
        self._last_gesture_ts = now
        self._last_action_ts  = now
        print(f"[GESTURE] {gesture:15s} [{hand_label:5s}]  →  {msg}")

        if gesture == Gesture.THREE_FINGERS:
            self._running = False

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WIN_NAME, WIN_W, WIN_H)

        sw, sh = pyautogui.size()
        cv2.moveWindow(WIN_NAME, sw - WIN_W - 12, 12)
        TopMost.enforce(use_cv2=True)

        print(f"[GesturePPT] Window open. Press Q to quit.")
        prev_t    = time.time()
        topmost_t = 0.0

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            now   = time.time()

            # FPS
            dt = max(now - prev_t, 1e-6)
            self._fps_buf.append(1.0 / dt)
            prev_t = now
            fps    = float(np.mean(self._fps_buf))

            # YOLO (every N frames)
            self._yolo_skip += 1
            if self._yolo_skip >= YOLO_SKIP:
                self._yolo_skip = 0
                results = self._yolo(frame, classes=[0], verbose=False, conf=0.45)
                self._yolo_boxes = [
                    box.xyxy[0].cpu().numpy()
                    for r in results for box in r.boxes
                ]

            # MediaPipe
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self._hands.process(rgb)

            raw_g  = Gesture.NONE
            conf_g = Gesture.NONE
            hand_lm    = None
            hand_label = ""

            if result.multi_hand_landmarks and result.multi_handedness:
                hand_lm    = result.multi_hand_landmarks[0]
                hand_label = result.multi_handedness[0].classification[0].label

                states = FingerState.get(hand_lm, hand_label)
                raw_g  = Gesture.classify(states)
                conf_g = self._g_buf.push(raw_g)

                if conf_g not in (Gesture.NONE,):
                    self._trigger(conf_g, hand_label)
            else:
                self._g_buf.clear()

            # Re-enforce topmost every 1.5 s
            if now - topmost_t > 1.5:
                TopMost.enforce(use_cv2=False)
                topmost_t = now

            state = dict(
                fps             = fps,
                hand_label      = hand_label,
                raw_gesture     = raw_g  if raw_g  != Gesture.NONE else "—",
                conf_gesture    = conf_g if conf_g != Gesture.NONE else "—",
                last_action     = self._last_action,
                last_gesture_ts = self._last_gesture_ts,
                last_action_ts  = self._last_action_ts,
                flash_color     = self._flash_color,
                slides          = self._engine.slides,
                paused          = self._engine.paused,
                fullscreen      = self._engine.fullscreen,
            )

            frame = hud_draw(
                frame, state,
                self._mp_hands, self._mp_draw, self._mp_style,
                hand_lm, self._yolo_boxes,
            )

            cv2.imshow(WIN_NAME, frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                break

        self._cap.release()
        cv2.destroyAllWindows()
        print("[GesturePPT] Closed.")
