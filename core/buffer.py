"""
GesturePPT – gesture smoothing.
Majority-vote over a sliding window to suppress single-frame noise.
"""

from collections import deque
from config.settings import CONFIRM_FRAMES
from core.gesture import Gesture


class GestureBuffer:
    """
    Push raw gesture labels each frame; returns a confirmed label only
    when one gesture wins the majority over the last `window` frames.
    """

    def __init__(self, window: int = CONFIRM_FRAMES):
        self._buf    = deque(maxlen=window)
        self._window = window

    def push(self, gesture: str) -> str:
        self._buf.append(gesture)
        if len(self._buf) < self._window:
            return Gesture.NONE

        counts: dict = {}
        for g in self._buf:
            counts[g] = counts.get(g, 0) + 1

        winner, count = max(counts.items(), key=lambda x: x[1])
        threshold = self._window // 2 + 1
        return winner if count >= threshold else Gesture.NONE

    def clear(self):
        self._buf.clear()
