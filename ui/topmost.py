"""
GesturePPT – keep the overlay window always on top.
Re-called every ~1.5 s because some window managers steal focus back.
"""

import subprocess
from typing import Optional
import cv2

from config.settings import WIN_NAME, SYSTEM


class TopMost:
    _hwnd: Optional[int] = None

    @classmethod
    def enforce(cls, use_cv2: bool = True):
        # Cross-platform OpenCV property (cheapest)
        if use_cv2:
            try:
                cv2.setWindowProperty(WIN_NAME, cv2.WND_PROP_TOPMOST, 1)
            except Exception:
                pass

        if SYSTEM == "Windows":
            cls._enforce_windows()
        elif SYSTEM == "Linux":
            cls._enforce_linux()
        # macOS: cv2 flag is sufficient

    @classmethod
    def _enforce_windows(cls):
        try:
            import win32gui, win32con
            if cls._hwnd is None:
                cls._hwnd = win32gui.FindWindow(None, WIN_NAME)
            if cls._hwnd:
                win32gui.SetWindowPos(
                    cls._hwnd,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
        except ImportError:
            pass

    @classmethod
    def _enforce_linux(cls):
        try:
            subprocess.Popen(
                ["wmctrl", "-r", WIN_NAME, "-b", "add,above"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass
