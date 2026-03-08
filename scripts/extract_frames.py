import argparse
import shutil
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def gif_to_png(input_gif: Path, output_folder: Path) -> int:
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
            frame = im.convert("RGBA")
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
    args = parser.parse_args()

    input_value = args.input or input("Enter Path To GIF: ").strip()
    input_gif = Path(input_value).expanduser()
    output_folder = Path(args.output).expanduser()

    if not input_gif.exists():
        print(f"Input GIF does not exist: {input_gif}")
        return

    frame_count = gif_to_png(input_gif, output_folder)
    if frame_count:
        print(f"Exported {frame_count} frames to {output_folder}")


if __name__ == "__main__":
    main()
