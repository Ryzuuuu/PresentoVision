# PresentoVision

[![CI](https://github.com/Ryzuuuu/PresentoVision/actions/workflows/ci.yml/badge.svg)](https://github.com/Ryzuuuu/PresentoVision/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.9--3.12-blue.svg)

Control a slide deck with your hand. PresentoVision reads your webcam, tracks a hand with **MediaPipe** (21 landmarks, in real time), and turns simple gestures into keyboard shortcuts for whatever presentation app is in focus: PowerPoint, Google Slides, Canva, Keynote, LibreOffice Impress or a PDF viewer. A small always-on-top overlay shows what the system sees, and **YOLOv8n** adds person detection as scene context.

<!-- TODO: add a demo GIF here, e.g. docs/demo.gif
![PresentoVision demo](docs/demo.gif)
-->

## Features

- **Hands-free slide control**: next / previous slide, pause, fullscreen and screenshot from one hand.
- **Works with any app**: it sends standard key presses (`Right`, `Left`, `Space`, `F5`, `Esc`), so there are no plugins or per-app integrations.
- **Reliable triggering**: a majority-vote buffer removes single-frame noise and a cooldown stops one gesture firing twice.
- **Live HUD**: raw vs. confirmed gesture, FPS, last action, slide counter, status and a cooldown bar, on a window that stays above your slides.
- **Easy to tune**: every threshold lives in [`config/settings.py`](config/settings.py).

## Gesture map

| Gesture | Hand | Action |
|---|---|---|
| Open palm | **Right** | Next slide |
| Open palm | **Left** | Previous slide |
| Fist | Either | Pause / resume autoplay (`Space`) |
| One finger (index) | Either | Save a screenshot |
| Two fingers (index + middle) | Either | Fullscreen on / off (alternates) |
| Three fingers (index + middle + ring) | Either | Quit the app |

The camera image is mirrored, so "Left" and "Right" refer to your own hands.

## How it works

```
 webcam frame ──► mirror
                    │
        ┌───────────┴─────────────┐
        ▼                         ▼
  YOLOv8n (every 4th frame)   MediaPipe Hands
  person boxes (overlay)      21 landmarks
        │                         ▼
        │                     FingerState  [thumb, index, middle, ring, pinky]
        │                         ▼
        │                     Gesture.classify
        │                         ▼
        │                     GestureBuffer (majority vote)
        │                         ▼
        │                     cooldown ──► SlideController ──► key press (pyautogui)
        │                         │
        └──────────► HUD renderer ◄┘
```

1. **Capture**: OpenCV grabs a frame and mirrors it.
2. **Hand tracking**: MediaPipe returns 21 landmarks and which hand it is. `FingerState` marks each finger as extended or folded (fingertip above its PIP joint; the thumb uses horizontal displacement).
3. **Classification**: the five booleans map to a gesture. The thumb is ignored for "one finger" and "two fingers" so they are easy to make.
4. **Smoothing**: a gesture only counts once it wins the majority (4 of the last 6 frames).
5. **Dispatch**: after a 1 second cooldown, `SlideController` sends the matching key press with `pyautogui`.
6. **Feedback**: the HUD draws the landmarks, person boxes, state and a flash border on each action.

YOLOv8n is a visual aid; gesture recognition does not depend on it.

## Tech stack

| Area | Tools |
|---|---|
| Hand tracking | [MediaPipe](https://developers.google.com/mediapipe) Hands (legacy `mp.solutions` API) |
| Object detection | [Ultralytics](https://github.com/ultralytics/ultralytics) YOLOv8n |
| Video + HUD | OpenCV, NumPy |
| Input automation | PyAutoGUI |
| Always-on-top | OpenCV window property, `pywin32` (Windows), `wmctrl` (Linux) |
| Quality | pytest, Ruff, GitHub Actions |

## Project structure

```
PresentoVision/
├── main.py               ← entry point
├── requirements.txt      ← runtime dependencies
├── requirements-dev.txt  ← adds pytest and ruff
├── pyproject.toml        ← pytest + ruff config
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
├── app/
│   └── engine.py         ← PresentoVision main loop + GestureEngine dispatcher
│
└── tests/                ← unit tests for gesture logic and smoothing
```

## Setup

Requirements: Python **3.9 – 3.12** and a webcam.

```bash
git clone https://github.com/Ryzuuuu/PresentoVision.git
cd PresentoVision

python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

pip install -r requirements.txt
```

- The first run downloads the YOLOv8n weights (`yolov8n.pt`, about 6 MB) into the current directory.
- **Windows:** `pywin32` is installed automatically for stronger always-on-top behaviour.
- **Linux:** optionally install `wmctrl` (`sudo apt install wmctrl`) for the same effect.
- **macOS:** allow your terminal under *Privacy & Security* for **Camera** and **Accessibility** (needed to send key presses).

MediaPipe is pinned below 0.10.30 because later releases removed the `mp.solutions` API this project uses.

## Usage

```bash
python main.py
```

1. Open your presentation and put it in focus.
2. The PresentoVision overlay opens in the top-right corner, always on top.
3. Show your hand to the camera and use the gestures above.
4. Press **Q** or **Esc** in the overlay window, or show three fingers, to quit.

Screenshots are saved to `~/Desktop/PresentoVision_Shots/` by default. Set the `PRESENTOVISION_SHOTS_DIR` environment variable (or edit `SCREENSHOTS_DIR`) to change the folder.

## Tuning

All knobs live in [`config/settings.py`](config/settings.py):

| Variable | Default | Effect |
|---|---|---|
| `COOLDOWN_SEC` | `1.0` | Min seconds between triggers |
| `CONFIRM_FRAMES` | `6` | Size of the majority-vote window (a gesture needs more than half of it) |
| `YOLO_SKIP` | `4` | Run YOLO every N frames |
| `MP_DETECT_CONF` / `MP_TRACK_CONF` | `0.80` | MediaPipe detection / tracking thresholds |
| `CAM_INDEX` | `0` | Which camera to use |
| `CAM_FPS` | `60` | Camera target FPS |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not open camera 0` | Close other apps using the webcam, or set `CAM_INDEX` to another device. |
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | You have MediaPipe 0.10.30 or newer. Run `pip install -r requirements.txt` to get the pinned version. |
| Gestures fire twice or not at all | Raise `CONFIRM_FRAMES` / `COOLDOWN_SEC`, or improve lighting and keep your hand fully in frame. |
| Low FPS | Raise `YOLO_SKIP`, or lower `CAM_W` / `CAM_H`. |
| Key presses go to the wrong window | Click your presentation first so it has focus, then use gestures. |

## Development

```bash
pip install -r requirements-dev.txt
pytest          # gesture classification + smoothing tests
ruff check .    # lint
```

CI runs both on every push and pull request.

## License

Released under the [MIT License](LICENSE).
