# Mac-Dynamic-Wallpapers

Dynamic wallpaper script for MacOS that turns any GIF into a useable wallpaper

## How to use

 * Clone the directory and cd into it
 * run `pip3 install -r requirements.txt`
 * run `python3 GIFtoImage.py /path/to/your.gif`
 * now run `python3 wallpaper.py` and accept any permissions it asks you

## Notes

 * Frames are exported as lossless PNG files (`video/frame_00000.png`, etc.) to keep original quality.
 * Default playback speed is 2 FPS. You can change it with `python3 wallpaper.py --fps 4`.
 * Stop playback with `Ctrl+C`.
 * `method#2.py` is an alternative playback method via `osascript`.
