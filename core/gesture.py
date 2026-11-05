"""
PresentoVision – gesture recognition layer.

Gesture map:
  OPEN_PALM  + Right hand  ->  Next Slide
  OPEN_PALM  + Left hand   ->  Prev Slide
  FIST                     ->  Pause / Autoplay toggle
  ONE_FINGER (index only)  ->  Screenshot
  PEACE      (index+mid)   ->  Fullscreen toggle
  THREE_FINGERS            ->  Quit App
"""


class FingerState:
    """
    Decode 21-landmark hand output from MediaPipe into a 5-bool list.
    Returns [thumb, index, middle, ring, pinky] — True = extended.
    """

    @staticmethod
    def get(landmarks, hand_label: str) -> list:
        lm = landmarks.landmark

        # Thumb: use horizontal displacement (mirrored for left hand)
        if hand_label == "Right":
            thumb = lm[4].x < lm[3].x
        else:
            thumb = lm[4].x > lm[3].x

        # Index / Middle / Ring / Pinky: tip.y < PIP.y (y grows downward)
        fingers = [lm[tip].y < lm[tip - 2].y for tip in (8, 12, 16, 20)]

        return [thumb, *fingers]   # [thumb, index, middle, ring, pinky]


class Gesture:
    """Gesture label constants + classifier."""

    NONE          = "NONE"
    ONE_FINGER    = "ONE_FINGER"     # index only
    PEACE         = "PEACE"          # index + middle
    THREE_FINGERS = "THREE_FINGERS"  # index + middle + ring
    FIST          = "FIST"           # all folded
    OPEN_PALM     = "OPEN_PALM"      # all extended

    @staticmethod
    def classify(states: list) -> str:
        _thumb, index, middle, ring, pinky = states

        # Order matters: check most-constrained patterns first
        if not any(states):
            return Gesture.FIST

        if all(states):
            return Gesture.OPEN_PALM

        if index and not middle and not ring and not pinky:
            return Gesture.ONE_FINGER        # thumb state irrelevant

        if index and middle and not ring and not pinky:
            return Gesture.PEACE

        if index and middle and ring and not pinky:
            return Gesture.THREE_FINGERS

        return Gesture.NONE
