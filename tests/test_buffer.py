"""Unit tests for the majority-vote smoothing buffer."""

from core.buffer import GestureBuffer
from core.gesture import Gesture


def test_returns_none_until_window_is_full():
    buf = GestureBuffer(window=4)
    for _ in range(3):
        assert buf.push(Gesture.FIST) == Gesture.NONE
    assert buf.push(Gesture.FIST) == Gesture.FIST


def test_majority_wins_over_single_frame_noise():
    buf = GestureBuffer(window=5)
    for g in (Gesture.OPEN_PALM, Gesture.OPEN_PALM, Gesture.NONE, Gesture.OPEN_PALM):
        buf.push(g)
    assert buf.push(Gesture.OPEN_PALM) == Gesture.OPEN_PALM


def test_no_majority_returns_none():
    buf = GestureBuffer(window=6)
    for g in (Gesture.FIST, Gesture.FIST, Gesture.PEACE, Gesture.PEACE, Gesture.NONE):
        buf.push(g)
    # 2 / 2 / 2 split: nobody reaches the threshold of 4.
    assert buf.push(Gesture.NONE) == Gesture.NONE


def test_clear_resets_the_window():
    buf = GestureBuffer(window=3)
    for _ in range(3):
        buf.push(Gesture.FIST)
    buf.clear()
    assert buf.push(Gesture.FIST) == Gesture.NONE
