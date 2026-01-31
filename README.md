# SpriteSpite

A Linux desktop application to convert videos and GIFs into sprite sheets, MP4s, and GIFs for use in Godot and other game engines.

## Features (Current)
- Load video files (MP4, MKV, WebM) and GIFs.
- Preview the first frame of the loaded file.

## Prerequisites
- Python 3.10+
- `ffmpeg` installed on your system.
- `uv` for dependency management.

### Installing `uv`
If you don't have `uv` installed, you can install it via curl:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Or via pip:
```bash
pip install uv
```

## Installation
Clone the repository and run `uv sync` to install dependencies:
```bash
uv sync
```

## Running the App
Launch the application using `uv run`:
```bash
uv run app/main.py
```

## How to Test This Step
1. Launch the app: `uv run app/main.py`.
2. Click the **"Open Video/GIF"** button.
3. Select a video file (e.g., `test.mp4` or `test2.mp4` if they are in the project root).
4. Verify that:
   - The left panel displays the file metadata (resolution, frame count, FPS).
   - The right panel displays the first frame of the video.