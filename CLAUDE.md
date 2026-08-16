# CLAUDE.md — AI Virtual Mouse Pro v3.0

Context file for future sessions. Generated 2026-08-16 from a full read of the tree.

## What this is

Desktop app (Windows-oriented) that turns webcam hand gestures into OS mouse/system control.
PyQt6 dashboard UI + OpenCV capture + MediaPipe hand landmarks + pynput/pyautogui output.

Entry point: `app.py` → `ui/main_window.MainWindow`.

## Stack

- Python **3.11** is the target. `__pycache__` contains both `cpython-311` and `cpython-314` artifacts; 3.14 broke MediaPipe previously.
- `mediapipe` **Tasks API** (`mediapipe.tasks.python.vision.HandLandmarker`), model at `models/hand_landmarker.task`.
  ⚠️ `PROJECT_STATUS.md` says "Do not use MediaPipe Tasks API / use solutions API" — that decision was **reversed** in code. `PROJECT_STATUS.md` is stale (dated 03 Aug 2026).
- `opencv-python`, `PyQt6`, `pynput` (actual mouse events), `pyautogui` (screen size only), `numpy`.
- No `requirements.txt`. `requirements.py` exists but is **empty**.

## Layout

```
app.py                      entry point (20 lines)
config.py                   EMPTY
requirements.py             EMPTY
models/hand_landmarker.task MediaPipe model asset
PROJECT_STATUS.md           stale roadmap/status doc

core/
  camera_thread.py      QThread webcam capture; signals frame_ready/fps_updated/camera_status; CAP_DSHOW, buffersize 1, cv2.flip
  hand_tracker.py       MediaPipe Tasks wrapper -> {results, hands[], landmarks, handedness, hand_detected, confidence}
  gesture_detector.py   1100-line pose classifier (angle + wrist-distance based finger extension, normalized pinch)
  gesture_manager.py    stability window, cooldowns, gesture -> one-shot event
  input_pipeline.py     ACTIVE pipeline: tracker -> detector -> manager -> MouseController
  frame_processor.py    LEGACY/dead alternate pipeline (incompatible API, see Known issues)
  hand_data.py, hand_utils.py   small helpers
  gestures/             ALTERNATE modular recognizers: finger_state.py, pinch.py, mouse.py, media.py, presentation.py
                        (click.py, scroll.py, __init__.py are EMPTY)
  __init__.py, fps_counter.py, mode_manager.py   EMPTY

controllers/
  mouse_controller.py   ONLY implemented controller (pynput; smoothing, margin mapping, drag, scroll, release_all)
  media_/presentation_/screenshot_/system_controller.py   EMPTY
  "__init__,py"         typo — comma not dot

ui/
  main_window.py  QMainWindow: sidebar + topbar + dashboard, owns CameraThread
  dashboard.py    camera feed + virtual-desktop panes + 8 info cards
  sidebar.py, topbar.py, widgets.py (CardWidget/ProgressCard/StatusCard), styles.py (GLOBAL_STYLE)
  icons.py, cards.py, __init__.py, dialogs/*, pages/*   ALL EMPTY

utils/, analytics/, tests/   ALL EMPTY (helpers, constants, logger, animation, theme,
                             performance_monitor, gesture_logger, session_stats, test_camera/gestures/ui)
data/logs, data/screenshots, data/recordings   empty dirs
test_hand_tracker.py, test_live_hand.py        manual scripts, not pytest

AI Virtual Mouse Pro v3.0/   ← nested duplicate dir holding .git, README.md, LICENSE,
                               .gitignore, profiles/*.json (all profile JSONs EMPTY)
```

## Runtime data flow (intended)

```
CameraThread.frame_ready
  → InputPipeline.process(frame)
      HandTracker.detect        -> hand dict
      HandTracker.draw_landmarks (manual cv2 skeleton, 21 pts, hardcoded connections)
      GestureDetector.detect    -> {gesture, fingers, pinch, position, ...}
      GestureManager.update     -> {gesture, stable, event}
      InputPipeline._execute    -> MouseController action
  → MainWindow updates dashboard cards
```

## Known issues / live bugs

1. **`ui/main_window.py` indentation is broken.** Only `__init__` is indented into the class (1 space);
   `build_ui`, `setup_camera`, `update_camera_frame`, `update_fps`, `update_camera_status`, `closeEvent`
   sit at module level. `app.py` will raise `AttributeError: 'MainWindow' object has no attribute 'build_ui'`.
   This is the first thing to fix before anything runs.

2. **Gesture vocabulary mismatch.** `GestureDetector` emits
   `NONE / OPEN_PALM / FIST / INDEX / TWO_FINGER / THUMB_UP / PINCH / OK`.
   `GestureManager._generate_event` switches on
   `MOVE / SCROLL / LEFT_CLICK / RIGHT_CLICK / FIST / OPEN_PALM / SWIPE_LEFT / SWIPE_RIGHT / THUMBS_UP / THUMBS_DOWN`.
   Only `FIST` and `OPEN_PALM` overlap → no click/move/scroll can ever fire. Note `THUMB_UP` vs `THUMBS_UP`.
   A translation layer (or renaming one side) is required. `core/gestures/mouse.py` already emits the
   action-style names and is the natural source of truth.

3. **`InputPipeline` is not wired into the UI.** `MainWindow` only displays the raw camera frame.
   Nothing calls `InputPipeline.process`.

4. **Two competing pipelines.** `frame_processor.py` calls `hand_tracker.detect(...)["frame"]`,
   `gesture_detector.detect(hands, mode)` and `gesture_manager.execute(...)` — none of which exist
   on the current classes. Treat it as dead code; `input_pipeline.py` is authoritative.

5. **Two competing gesture engines.** Monolithic `core/gesture_detector.py` vs modular `core/gestures/*`.
   Pick one before adding gestures.

6. **`InputPipeline._execute` never emits `DOUBLE_CLICK`** — `GestureManager.register_click()` exists
   but is never called.

7. **Scroll direction is hardcoded** to `scroll(1)` (up only) in `InputPipeline._execute`.

8. **Git repo root is the nested `AI Virtual Mouse Pro v3.0/` folder**, so none of the source code is
   tracked. Only README/LICENSE/.gitignore/empty profiles are in the repo.

9. **`CAP_DSHOW` is Windows-only** — camera init will fail on macOS/Linux.

## Conventions to preserve

- `from __future__ import annotations` at top of core modules; full type hints.
- Heavy vertical whitespace, one argument per line, `# ===` banner comments separating sections.
- Strict separation: **detectors classify, controllers act.** Never call pyautogui/pynput from
  `core/gestures/*` or `gesture_detector.py`.
- Defensive style: wrap in try/except, log `[ClassName] message`, return a well-formed empty dict
  (`_empty_result` / `_empty_data` / `_empty_state`) rather than raising.
- Clamp/normalize all numeric config in `__init__` (`max(...)`, `min(...)`).
- Landmark access goes through `_xyz()` so both dict and MediaPipe-object landmarks work.

## Working agreements (from project rules)

- Read only files explicitly provided; don't scan the repo unless asked.
- Deliver patches/diffs, not full rewrites. Root cause → exact change → patch.
- Preserve existing architecture and formatting style.
- Keep responses token-efficient; no unrequested explanations.

## Suggested next steps

1. Fix `ui/main_window.py` indentation.
2. Reconcile gesture names (detector ↔ manager).
3. Wire `InputPipeline` into `MainWindow.update_camera_frame` and feed the dashboard cards.
4. Delete or rewrite `core/frame_processor.py`.
5. Add a real `requirements.txt`; pin `mediapipe==0.10.21` under Python 3.11.
6. Move `.git` to the actual project root so the code is version-controlled.
