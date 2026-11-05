"""Unit tests for finger decoding and gesture classification (no camera needed)."""

from types import SimpleNamespace

import pytest

from core.gesture import FingerState, Gesture


def _hand(thumb_extended_right=False, fingers=(False, False, False, False)):
    """Build a fake 21-landmark hand. `fingers` = (index, middle, ring, pinky) extended."""
    lm = [SimpleNamespace(x=0.5, y=0.5) for _ in range(21)]
    # Thumb (right-hand convention): tip left of the IP joint means extended.
    lm[3].x = 0.5
    lm[4].x = 0.4 if thumb_extended_right else 0.6
    # Finger tip above its PIP joint (smaller y) means extended.
    for tip, extended in zip((8, 12, 16, 20), fingers):
        lm[tip - 2].y = 0.5
        lm[tip].y = 0.3 if extended else 0.7
    return SimpleNamespace(landmark=lm)


@pytest.mark.parametrize(
    "states, expected",
    [
        ([False, False, False, False, False], Gesture.FIST),
        ([True, True, True, True, True], Gesture.OPEN_PALM),
        ([False, True, False, False, False], Gesture.ONE_FINGER),
        ([True, True, False, False, False], Gesture.ONE_FINGER),   # thumb ignored
        ([False, True, True, False, False], Gesture.PEACE),
        ([True, True, True, False, False], Gesture.PEACE),
        ([False, True, True, True, False], Gesture.THREE_FINGERS),
        ([False, False, True, False, False], Gesture.NONE),
        ([False, True, False, True, False], Gesture.NONE),
        ([False, True, True, True, True], Gesture.NONE),           # four fingers, no thumb
    ],
)
def test_classify(states, expected):
    assert Gesture.classify(states) == expected


def test_finger_state_right_hand():
    hand = _hand(thumb_extended_right=True, fingers=(True, False, True, False))
    assert FingerState.get(hand, "Right") == [True, True, False, True, False]


def test_finger_state_left_hand_mirrors_thumb():
    hand = _hand(thumb_extended_right=True, fingers=(False, False, False, False))
    # The same thumb geometry is "folded" for a left hand.
    assert FingerState.get(hand, "Left")[0] is False
    assert FingerState.get(hand, "Right")[0] is True


def test_open_palm_end_to_end():
    hand = _hand(thumb_extended_right=True, fingers=(True, True, True, True))
    assert Gesture.classify(FingerState.get(hand, "Right")) == Gesture.OPEN_PALM
