# PresentoVision

Hand-gesture presentation controller built on **YOLOv8n** (person/scene context overlay) and **MediaPipe** (21-landmark real-time hand tracking).

Controls any presentation app — PowerPoint, Canva, Google Slides, Keynote, LibreOffice Impress, PDF viewers — via system-level keyboard shortcuts.

---

## Gesture Map

| Gesture | Hand | Action |
|---|---|---|
| 🖐 Open Palm | **Right** | Next Slide → |
| 🖐 Open Palm | **Left** | Prev Slide ← |
| ✊ Fist | Either | Pause / Autoplay toggle |
| ☝ One Finger | Either | Screenshot |
| ✌ Two Fingers | Either | Fullscreen on/off (alternates) |
| 🤟 Three Fingers | Either | Quit App |

---

## Project Structure

```
PresentoVision/
├── main.py               ← entry point
├── requirements.txt
│
├── config/
│   ├── settings.py       ← runtime tuning knobs (cooldown, FPS, paths …)
│   └── theme.py          ← colors, fonts, gesture guide rows
│
├── core/
│   ├── gesture.py        ← FingerState decoder + Gesture classifier
│   ├── buffer.py         ← majority-vote smoothing buffer
│   └── controller.py     ← SlideController (platform-aware keyboard actions)
│
├── ui/
│   ├── hud.py            ← HUD renderer (side panel, landmarks, flash border)
│   └── topmost.py        ← always-on-top window enforcement
│
└── app/
    └── engine.py         ← GesturePPT main loop + GestureEngine dispatcher
```

---

## Setup

```bash
pip install -r requirements.txt
```

> **Windows only:** `pywin32` is installed automatically for stronger always-on-top enforcement.  
> **Linux:** optionally install `wmctrl` (`sudo apt install wmctrl`) for the same effect.

---

## Run

```bash
python main.py
```

The overlay window opens in the **top-right corner** of your screen, always on top, so it never blocks your slides.

---

## Tuning

All knobs live in `config/settings.py`:

| Variable | Default | Effect |
|---|---|---|
| `COOLDOWN_SEC` | `1.0` | Min seconds between triggers |
| `CONFIRM_FRAMES` | `6` | Frames a gesture must hold to fire |
| `YOLO_SKIP` | `4` | Run YOLO every N frames |
| `MP_DETECT_CONF` | `0.80` | MediaPipe detection threshold |
| `CAM_FPS` | `60` | Camera target FPS |

Screenshots save to `~/Desktop/GesturePPT_Shots/` by default (change `SCREENSHOTS_DIR`).
