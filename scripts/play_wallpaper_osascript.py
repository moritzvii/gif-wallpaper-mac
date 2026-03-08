import argparse
import re
import subprocess
import time
from pathlib import Path

FRAME_FILE_PATTERN = re.compile(r"^frame_(\d+)\.(png|jpe?g)$", re.IGNORECASE)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OSA_SCRIPT_PREFIX = [
    "/usr/bin/osascript",
    "-e",
    "on run argv",
    "-e",
    'tell application "Finder" to set desktop picture to POSIX file (item 1 of argv)',
    "-e",
    "end run",
]


def set_desktop_background(filename: Path) -> None:
    subprocess.run(OSA_SCRIPT_PREFIX + [str(filename)], check=True)


def list_frames(folder: Path) -> list[Path]:
    indexed_frames = []
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        match = FRAME_FILE_PATTERN.match(file_path.name)
        if not match:
            continue

        indexed_frames.append((int(match.group(1)), file_path))

    indexed_frames.sort(key=lambda item: item[0])
    return [frame for _, frame in indexed_frames]


def is_screen_saver_active() -> bool:
    result = subprocess.run(
        ["/usr/bin/pgrep", "-qx", "ScreenSaverEngine"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Wallpaper playback using osascript directly.")
    parser.add_argument(
        "--folder",
        default=str(PROJECT_ROOT / "video"),
        help="Folder containing frame_XXXXX.png/.jpg files.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=2.0,
        help="Frames per second for wallpaper playback.",
    )
    parser.add_argument(
        "--pause-when-locked",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pause updates while screen saver / lock screen is active.",
    )
    args = parser.parse_args()

    if args.fps <= 0:
        print("FPS must be greater than 0.")
        return

    folder = Path(args.folder).expanduser()
    if not folder.exists():
        print(f"Frame folder does not exist: {folder}")
        return

    frames = list_frames(folder)
    if not frames:
        print(f"No frame files found in {folder}.")
        return

    frame_delay = 1.0 / args.fps
    print(f"Playing {len(frames)} frames from {folder} at {args.fps} FPS. Press Ctrl+C to stop.")

    try:
        while True:
            if args.pause_when_locked and is_screen_saver_active():
                time.sleep(1.0)
                continue
            for frame in frames:
                if args.pause_when_locked and is_screen_saver_active():
                    break
                set_desktop_background(frame)
                time.sleep(frame_delay)
    except KeyboardInterrupt:
        print("\nStopped wallpaper playback.")


if __name__ == "__main__":
    main()
