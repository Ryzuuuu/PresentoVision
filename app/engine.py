"""
PresentoVision – application engine.
Owns the camera loop, model inference, and gesture dispatch.
"""

import os
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
from ultralytics import YOLO

from config.settings import (
    WIN_NAME, WIN_W, WIN_H, CAM_INDEX, CAM_W, CAM_H, CAM_FPS,
    COOLDOWN_SEC, CONFIRM_FRAMES, YOLO_SKIP, YOLO_MODEL, YOLO_CONF,
    MP_DETECT_CONF, MP_TRACK_CONF,
)
from config.theme import C_GREEN, C_RED, C_BLUE, C_GOLD, C_CYAN, C_MAGENTA, C_GRAY
from core.gesture import Gesture, FingerState
from core.buffer import GestureBuffer
from core.controller import SlideController
from ui.hud import draw as hud_draw
from ui.topmost import TopMost

# Consecutive failed camera reads tolerated (~5 s) before giving up.
MAX_READ_FAILURES = 100


class GestureEngine:
    """
    Gesture -> Action dispatch table.
    Hand label is forwarded so OPEN_PALM can branch on left/right.
    """

    _HANDLED = frozenset({
        Gesture.OPEN_PALM,
        Gesture.FIST,
        Gesture.ONE_FINGER,
        Gesture.PEACE,
        Gesture.THREE_FINGERS,
    })

    def __init__(self):
        self._ctrl       = SlideController()
        self._slides     = 0
        self._paused     = False
        self._fullscreen = False

    def dispatch(self, gesture: str, hand_label: str) -> tuple:
        """
        Execute the action for `gesture`.
        Returns (result_message, flash_color) or (None, None) if gesture unmapped.
        Messages are ASCII-only because they are drawn with OpenCV's Hershey fonts.
        """
        if gesture not in self._HANDLED:
            return None, None

        if gesture == Gesture.OPEN_PALM:
            if hand_label == "Right":
                self._ctrl.next_slide()
                self._slides += 1
                return f"Next Slide -> (#{self._slides})", C_GREEN
            else:
                self._ctrl.prev_slide()
                self._slides = max(0, self._slides - 1)
                return f"Prev Slide <- (#{self._slides})", C_BLUE

        if gesture == Gesture.FIST:
            self._ctrl.pause_play()
            self._paused = not self._paused
            return ("Paused" if self._paused else "Resumed"), C_RED

        if gesture == Gesture.ONE_FINGER:
            path = self._ctrl.screenshot()
            return f"Saved {os.path.basename(path)}", C_GOLD

        if gesture == Gesture.PEACE:
            if self._fullscreen:
                self._ctrl.exit_fullscreen()
                self._fullscreen = False
                return "Fullscreen OFF", C_GRAY
            else:
                self._ctrl.enter_fullscreen()
                self._fullscreen = True
                return "Fullscreen ON", C_CYAN

        # Remaining handled gesture: THREE_FINGERS (the caller stops the loop).
        return "Quitting...", C_MAGENTA

    @property
    def slides(self): return self._slides

    @property
    def paused(self): return self._paused

    @property
    def fullscreen(self): return self._fullscreen


class PresentoVision:

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
        print("[PresentoVision] Loading YOLOv8n ...")
        self._yolo = YOLO(YOLO_MODEL)
        print("[PresentoVision] YOLOv8n ready.")

        # Camera
        self._cap = cv2.VideoCapture(CAM_INDEX)
        if not self._cap.isOpened():
            self._cap.release()
            self._hands.close()
            raise RuntimeError(
                f"Could not open camera {CAM_INDEX}. Check that a webcam is connected, "
                "not in use by another app, and that camera access is allowed; "
                "or change CAM_INDEX in config/settings.py."
            )
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
        self._last_action     = "Ready - show a hand gesture"
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
        print(f"[GESTURE] {gesture:15s} [{hand_label:5s}]  ->  {msg}")

        if gesture == Gesture.THREE_FINGERS:
            self._running = False

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        try:
            self._loop()
        finally:
            self._cap.release()
            self._hands.close()
            cv2.destroyAllWindows()
            print("[PresentoVision] Closed.")

    def _loop(self):
        cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WIN_NAME, WIN_W, WIN_H)

        sw, _sh = pyautogui.size()
        cv2.moveWindow(WIN_NAME, sw - WIN_W - 12, 12)
        TopMost.enforce(use_cv2=True)

        print("[PresentoVision] Window open. Press Q or Esc to quit.")
        prev_t    = time.time()
        topmost_t = 0.0
        read_failures = 0

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                read_failures += 1
                if read_failures >= MAX_READ_FAILURES:
                    raise RuntimeError("Camera stopped delivering frames.")
                time.sleep(0.05)
                continue
            read_failures = 0

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
                results = self._yolo(frame, classes=[0], verbose=False, conf=YOLO_CONF)
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

                if conf_g != Gesture.NONE:
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
                raw_gesture     = raw_g  if raw_g  != Gesture.NONE else "-",
                conf_gesture    = conf_g if conf_g != Gesture.NONE else "-",
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
