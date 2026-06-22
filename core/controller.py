"""
GesturePPT – platform-aware slide controller.

Keyboard shortcuts work universally across:
  PowerPoint · Canva · Google Slides · Keynote
  LibreOffice Impress · PDF viewers (Acrobat, Evince, Okular)
"""

import os
import time
import pyautogui
from datetime import datetime

from config.settings import SYSTEM, SCREENSHOTS_DIR


class SlideController:

    @staticmethod
    def next_slide():
        pyautogui.press("right")

    @staticmethod
    def prev_slide():
        pyautogui.press("left")

    @staticmethod
    def pause_play():
        """Space bar toggles autoplay / pause in every major presentation app."""
        pyautogui.press("space")

    @staticmethod
    def screenshot() -> str:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOTS_DIR, f"slide_{ts}.png")
        pyautogui.screenshot(path)
        return path

    @staticmethod
    def enter_fullscreen():
        if SYSTEM == "Windows":
            pyautogui.press("f5")
        elif SYSTEM == "Darwin":
            pyautogui.hotkey("ctrl", "shift", "f")
        else:
            pyautogui.press("f5")
        time.sleep(0.05)

    @staticmethod
    def exit_fullscreen():
        pyautogui.press("escape")
        time.sleep(0.05)
        if SYSTEM == "Darwin":
            pyautogui.hotkey("ctrl", "shift", "f")
