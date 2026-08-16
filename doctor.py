"""
doctor.py
---------
Self-check and repair for AI Virtual Mouse Pro v3.0.

Run this before app.py. It verifies every layer the application
depends on and repairs what it safely can:

    python doctor.py

Each check prints PASS, WARN or FAIL together with the exact command
needed to fix a failure. The exit code is 0 when the application is
expected to start, and 1 otherwise.
"""

from __future__ import annotations
 
import os
import platform
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

RESULTS = []


# ==============================================================
# REPORTING
# ==============================================================

def report(
    status: str,
    name: str,
    detail: str = "",
    fix: str = "",
) -> None:

    RESULTS.append(
        (status, name, detail, fix)
    )

    symbol = {
        "PASS": "  [ OK ]",
        "WARN": "  [WARN]",
        "FAIL": "  [FAIL]",
    }.get(status, "  [ ?? ]")

    line = f"{symbol}  {name}"

    if detail:
        line += f"  --  {detail}"

    print(line)

    if fix:
        print(f"          fix: {fix}")


def section(title: str) -> None:

    print()
    print(title)
    print("-" * len(title))


# ==============================================================
# 1. INTERPRETER
# ==============================================================

def check_python() -> None:

    section("1. Interpreter")

    version = sys.version_info

    text = (
        f"Python {version.major}.{version.minor}.{version.micro}"
        f" ({platform.machine()})"
    )

    if version[:2] == (3, 11):

        report(
            "PASS",
            "Python version",
            text,
        )

    elif version[:2] in ((3, 9), (3, 10)):

        report(
            "WARN",
            "Python version",
            f"{text} -- 3.11 is the tested target",
        )

    else:

        report(
            "FAIL",
            "Python version",
            f"{text} -- MediaPipe is known to break here",
            "py -3.11 -m venv .venv  &&  .venv\\Scripts\\activate"
            "  &&  pip install -r requirements.txt",
        )

    if platform.system() != "Windows":

        report(
            "WARN",
            "Operating system",
            f"{platform.system()} -- camera uses cv2.CAP_DSHOW "
            f"(Windows only) and media keys assume Windows",
        )

    else:

        report(
            "PASS",
            "Operating system",
            "Windows",
        )


# ==============================================================
# 2. DEPENDENCIES
# ==============================================================

def check_dependencies() -> None:

    section("2. Dependencies")

    packages = [
        ("cv2", "opencv-python", None),
        ("numpy", "numpy", "1."),
        ("mediapipe", "mediapipe", "0.10."),
        ("PyQt6", "PyQt6", None),
        ("pynput", "pynput", None),
        ("pyautogui", "pyautogui", None),
    ]

    for module_name, package, expected_prefix in packages:

        try:

            # Some packages (pyautogui via mouseinfo) call sys.exit()
            # on a failed import, which raises SystemExit rather than
            # a normal Exception. Catch everything.

            module = __import__(module_name)

            version = str(
                getattr(
                    module,
                    "__version__",
                    "installed",
                )
            )

            if (
                expected_prefix is not None
                and version != "installed"
                and not version.startswith(expected_prefix)
            ):

                report(
                    "WARN",
                    package,
                    f"{version} installed, {expected_prefix}x expected",
                    f"pip install -r requirements.txt",
                )

            else:

                report(
                    "PASS",
                    package,
                    version,
                )

        except BaseException as e:

            report(
                "FAIL",
                package,
                f"{type(e).__name__}: {str(e)[:70]}",
                f"pip install {package}",
            )

    # numpy 2.x silently breaks mediapipe 0.10.x

    try:

        import numpy

        if int(numpy.__version__.split(".")[0]) >= 2:

            report(
                "FAIL",
                "numpy ABI",
                f"numpy {numpy.__version__} is incompatible "
                f"with mediapipe 0.10.x",
                'pip install "numpy<2.0"',
            )

    except Exception:
        pass


# ==============================================================
# 3. DATA DIRECTORIES
# ==============================================================

def check_data_dirs() -> None:

    section("3. Output directories")

    for name in (
        "screenshots",
        "recordings",
        "logs",
    ):

        path = PROJECT_ROOT / "data" / name

        # A stray zero-byte file can occupy the directory path.

        if path.exists() and not path.is_dir():

            try:

                path.unlink()

                path.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                (path / ".gitkeep").touch()

                report(
                    "PASS",
                    f"data/{name}",
                    "was a stray file, replaced with a directory",
                )

                continue

            except Exception as e:

                report(
                    "FAIL",
                    f"data/{name}",
                    f"occupied by a file: {e}",
                    f"Remove-Item data\\{name}  ;  "
                    f"New-Item -ItemType Directory data\\{name}",
                )

                continue

        try:

            path.mkdir(
                parents=True,
                exist_ok=True,
            )

            probe = path / ".write_test"

            probe.write_text("ok")
            probe.unlink()

            report(
                "PASS",
                f"data/{name}",
                "writable",
            )

        except Exception as e:

            report(
                "FAIL",
                f"data/{name}",
                str(e)[:70],
                f"check folder permissions on {path}",
            )


# ==============================================================
# 4. MODEL ASSET
# ==============================================================

def check_model() -> None:

    section("4. MediaPipe model")

    path = (
        PROJECT_ROOT
        / "models"
        / "hand_landmarker.task"
    )

    if not path.exists():

        report(
            "FAIL",
            "hand_landmarker.task",
            "missing",
            "download from "
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/latest/"
            "hand_landmarker.task  into models/",
        )

        return

    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb < 1.0:

        report(
            "FAIL",
            "hand_landmarker.task",
            f"only {size_mb:.2f} MB -- file looks truncated",
            "re-download the model asset",
        )

        return

    report(
        "PASS",
        "hand_landmarker.task",
        f"{size_mb:.1f} MB",
    )


# ==============================================================
# 5. CAMERA
# ==============================================================

def check_camera() -> None:

    section("5. Camera")

    try:

        import cv2

    except Exception:

        report(
            "FAIL",
            "camera probe",
            "opencv not installed, skipped",
        )

        return

    backend = (
        cv2.CAP_DSHOW
        if platform.system() == "Windows"
        else 0
    )

    capture = None

    try:

        capture = cv2.VideoCapture(
            0,
            backend,
        )

        if not capture.isOpened():

            report(
                "FAIL",
                "camera index 0",
                "could not open",
                "close Teams/Zoom/Camera app, check Windows "
                "Settings > Privacy > Camera, or try index 1",
            )

            return

        ok, frame = capture.read()

        if not ok or frame is None:

            report(
                "FAIL",
                "camera index 0",
                "opened but returned no frame",
                "unplug and replug the webcam, or try index 1",
            )

            return

        height, width = frame.shape[:2]

        report(
            "PASS",
            "camera index 0",
            f"{width}x{height} frame captured",
        )

    except Exception as e:

        report(
            "FAIL",
            "camera probe",
            f"{type(e).__name__}: {str(e)[:60]}",
        )

    finally:

        if capture is not None:

            try:
                capture.release()
            except Exception:
                pass


# ==============================================================
# 6. HAND TRACKING
# ==============================================================

def check_hand_tracking() -> None:

    section("6. Hand tracking")

    try:

        import numpy as np

        from core.hand_tracker import HandTracker

    except BaseException as e:

        report(
            "FAIL",
            "HandTracker import",
            f"{type(e).__name__}: {str(e)[:70]}",
        )

        return

    tracker = None

    try:

        tracker = HandTracker(
            max_hands=2,
            detection_confidence=0.7,
            tracking_confidence=0.7,
        )

        report(
            "PASS",
            "HandLandmarker created",
            "model loaded",
        )

        blank = np.zeros(
            (720, 1280, 3),
            dtype=np.uint8,
        )

        result = tracker.detect(blank)

        if isinstance(result, dict):

            report(
                "PASS",
                "inference on blank frame",
                f"hand_detected={result.get('hand_detected')}",
            )

        else:

            report(
                "FAIL",
                "inference on blank frame",
                f"unexpected result type {type(result).__name__}",
            )

    except Exception as e:

        report(
            "FAIL",
            "HandLandmarker",
            f"{type(e).__name__}: {str(e)[:70]}",
            "usually a Python/MediaPipe version mismatch -- "
            "use Python 3.11 with mediapipe==0.10.21",
        )

    finally:

        if tracker is not None:

            try:
                tracker.close()
            except Exception:
                pass


# ==============================================================
# 7. OPERATING SYSTEM INPUT
# ==============================================================

def check_os_input() -> None:

    section("7. Operating system input")

    try:

        from controllers.mouse_controller import MouseController

        mouse = MouseController()

        width, height = mouse.get_screen_size()

        report(
            "PASS",
            "MouseController",
            f"screen {width}x{height}",
        )

        centre = mouse.map_to_screen(
            640,
            360,
            1280,
            720,
        )

        expected_x = width // 2
        expected_y = height // 2

        close_enough = (
            abs(centre[0] - expected_x) < width * 0.1
            and abs(centre[1] - expected_y) < height * 0.1
        )

        report(
            "PASS" if close_enough else "FAIL",
            "coordinate mapping",
            f"frame centre -> {centre} "
            f"(expected near {expected_x},{expected_y})",
        )

        mouse.close()

    except BaseException as e:

        report(
            "FAIL",
            "MouseController",
            f"{type(e).__name__}: {str(e)[:70]}",
        )

    for label, module_path, class_name in (
        ("MediaController",
         "controllers.media_controller",
         "MediaController"),
        ("PresentationController",
         "controllers.presentation_controller",
         "PresentationController"),
        ("ScreenshotController",
         "controllers.screenshot_controller",
         "ScreenshotController"),
    ):

        try:

            module = __import__(
                module_path,
                fromlist=[class_name],
            )

            instance = getattr(
                module,
                class_name,
            )()

            report(
                "PASS",
                label,
                "constructed",
            )

            try:
                instance.close()
            except Exception:
                pass

        except BaseException as e:

            report(
                "FAIL",
                label,
                f"{type(e).__name__}: {str(e)[:70]}",
            )


# ==============================================================
# 8. APPLICATION WIRING
# ==============================================================

def check_wiring() -> None:

    section("8. Application wiring")

    try:

        from core.input_pipeline import InputPipeline

        report(
            "PASS",
            "InputPipeline import",
            "",
        )

    except BaseException as e:

        report(
            "FAIL",
            "InputPipeline import",
            f"{type(e).__name__}: {str(e)[:70]}",
        )

        return

    try:

        from ui.main_window import MainWindow

        required = [
            "build_ui",
            "setup_pipeline",
            "setup_camera",
            "update_camera_frame",
            "update_dashboard",
            "toggle_control",
            "closeEvent",
        ]

        missing = [
            name
            for name in required
            if not hasattr(MainWindow, name)
        ]

        if missing:

            report(
                "FAIL",
                "MainWindow methods",
                f"missing {missing}",
                "indentation problem in ui/main_window.py",
            )

        else:

            report(
                "PASS",
                "MainWindow methods",
                f"all {len(required)} present",
            )

    except BaseException as e:

        report(
            "FAIL",
            "MainWindow import",
            f"{type(e).__name__}: {str(e)[:70]}",
        )


# ==============================================================
# MAIN
# ==============================================================

def main() -> int:

    print()
    print("=" * 62)
    print("  AI Virtual Mouse Pro v3.0  --  environment check")
    print("=" * 62)

    for check in (
        check_python,
        check_dependencies,
        check_data_dirs,
        check_model,
        check_camera,
        check_hand_tracking,
        check_os_input,
        check_wiring,
    ):

        try:

            check()

        except BaseException:

            section(
                f"{check.__name__} crashed"
            )

            traceback.print_exc()

            report(
                "FAIL",
                check.__name__,
                "check itself crashed",
            )

    failures = [
        r for r in RESULTS
        if r[0] == "FAIL"
    ]

    warnings = [
        r for r in RESULTS
        if r[0] == "WARN"
    ]

    print()
    print("=" * 62)

    print(
        f"  {len(RESULTS) - len(failures) - len(warnings)} passed, "
        f"{len(warnings)} warnings, "
        f"{len(failures)} failures"
    )

    print("=" * 62)

    if failures:

        print()
        print("  Must fix before the app will work:")

        for _, name, detail, fix in failures:

            print(f"    - {name}: {detail}")

            if fix:
                print(f"        {fix}")

        print()

        return 1

    print()
    print("  Environment looks good. Start the app with:")
    print()
    print("      python app.py")
    print()
    print("  Control starts PAUSED. Press 'Start Control' in the")
    print("  sidebar to enable gestures, and Esc to stop.")
    print()

    return 0


if __name__ == "__main__":

    sys.exit(
        main()
    )
