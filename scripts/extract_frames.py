import argparse
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_size(value: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", value)
    if not match:
        return None
    width = int(match.group(1))
    height = int(match.group(2))
    if width <= 0 or height <= 0:
        return None
    return width, height


def detect_screen_size() -> tuple[int, int] | None:
    # Finder returns desktop bounds as: left, top, right, bottom.
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", 'tell application "Finder" to get bounds of window of desktop'],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    numbers = [int(value) for value in re.findall(r"-?\d+", result.stdout)]
    if len(numbers) < 4:
        return None

    width = numbers[2] - numbers[0]
    height = numbers[3] - numbers[1]
    if width <= 0 or height <= 0:
        return None
    return width, height


def mirror_fill_frame(frame: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    target_width, target_height = target_size
    source_width, source_height = frame.size
    scale = min(target_width / source_width, target_height / source_height)
    resized_width = max(1, int(round(source_width * scale)))
    resized_height = max(1, int(round(source_height * scale)))

    resized = frame.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target_width, target_height))

    x_offset = (target_width - resized_width) // 2
    y_offset = (target_height - resized_height) // 2
    canvas.paste(resized, (x_offset, y_offset))

    left_gap = x_offset
    right_gap = target_width - (x_offset + resized_width)
    top_gap = y_offset
    bottom_gap = target_height - (y_offset + resized_height)

    if left_gap > 0:
        sample_width = min(resized_width, max(1, min(left_gap * 2, resized_width)))
        left_strip = resized.crop((0, 0, sample_width, resized_height)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        left_fill = left_strip.resize((left_gap, resized_height), Image.Resampling.BICUBIC)
        canvas.paste(left_fill, (0, y_offset))

    if right_gap > 0:
        sample_width = min(resized_width, max(1, min(right_gap * 2, resized_width)))
        right_strip = resized.crop((resized_width - sample_width, 0, resized_width, resized_height))
        right_strip = right_strip.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        right_fill = right_strip.resize((right_gap, resized_height), Image.Resampling.BICUBIC)
        canvas.paste(right_fill, (x_offset + resized_width, y_offset))

    if top_gap > 0:
        sample_height = min(resized_height, max(1, min(top_gap * 2, resized_height)))
        top_strip = canvas.crop((0, y_offset, target_width, y_offset + sample_height))
        top_strip = top_strip.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        top_fill = top_strip.resize((target_width, top_gap), Image.Resampling.BICUBIC)
        canvas.paste(top_fill, (0, 0))

    if bottom_gap > 0:
        sample_height = min(resized_height, max(1, min(bottom_gap * 2, resized_height)))
        bottom_strip = canvas.crop(
            (0, y_offset + resized_height - sample_height, target_width, y_offset + resized_height)
        )
        bottom_strip = bottom_strip.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        bottom_fill = bottom_strip.resize((target_width, bottom_gap), Image.Resampling.BICUBIC)
        canvas.paste(bottom_fill, (0, y_offset + resized_height))

    return canvas


def normalize_frame(
    frame: Image.Image,
    target_size: tuple[int, int] | None,
    placement: str,
) -> Image.Image:
    rgba_frame = frame.convert("RGBA")
    if target_size is None:
        return rgba_frame
    if placement == "mirror-fill":
        return mirror_fill_frame(rgba_frame, target_size)
    return rgba_frame.resize(target_size, Image.Resampling.LANCZOS)


def gif_to_png(
    input_gif: Path,
    output_folder: Path,
    target_size: tuple[int, int] | None,
    placement: str,
) -> int:
    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        im = Image.open(input_gif)
    except OSError:
        print(f"Can't load {input_gif}")
        return 0

    frame_index = 0
    try:
        while True:
            frame = normalize_frame(im, target_size, placement)
            output_file = output_folder / f"frame_{frame_index:05d}.png"
            # PNG is lossless; this keeps frame quality intact.
            frame.save(output_file, "PNG", optimize=False, compress_level=0)
            frame_index += 1
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    return frame_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract GIF frames as lossless PNG files.")
    parser.add_argument("input", nargs="?", help="Path to input GIF.")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "video"),
        help="Output folder for extracted frames.",
    )
    parser.add_argument(
        "--size",
        default="auto",
        help="Target size as WIDTHxHEIGHT (example: 5120x1440). Use 'auto' for current screen.",
    )
    parser.add_argument(
        "--placement",
        choices=["mirror-fill", "stretch"],
        default="mirror-fill",
        help="How frames are adapted to --size. 'mirror-fill' keeps aspect ratio and mirrors borders.",
    )
    args = parser.parse_args()

    input_value = args.input or input("Enter Path To GIF: ").strip()
    input_gif = Path(input_value).expanduser()
    output_folder = Path(args.output).expanduser()

    if not input_gif.exists():
        print(f"Input GIF does not exist: {input_gif}")
        return

    target_size: tuple[int, int] | None
    if args.size.lower() == "auto":
        target_size = detect_screen_size()
        if target_size is None:
            print("Could not detect screen size automatically. Exporting original frame sizes.")
        else:
            print(f"Detected screen size: {target_size[0]}x{target_size[1]}")
    else:
        target_size = parse_size(args.size)
        if target_size is None:
            print(f"Invalid --size value: {args.size}. Use format WIDTHxHEIGHT, e.g. 5120x1440.")
            return

    frame_count = gif_to_png(input_gif, output_folder, target_size=target_size, placement=args.placement)
    if frame_count:
        print(f"Exported {frame_count} frames to {output_folder}")


if __name__ == "__main__":
    main()
