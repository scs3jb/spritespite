You are my senior Python desktop-app engineer.

Your job:
- Design and implement a **Linux** desktop application in Python that turns videos or GIFs into:
  - Animated GIF
  - MP4
  - Sprite sheet PNG + a Godot import instructions `.txt` file
- The app must provide an interactive UI for:
  - Loading an input video (mp4, mkv, webm, etc.) or GIF
  - Selecting frames or a frame range
  - Cropping
  - Chroma-key background removal (transparent PNG output)
  - Live preview of processed frames
  - Exporting to GIF / MP4 / sprite sheet

Assumptions and constraints:
- Target OS: Linux (I’m on a typical desktop distro).
- Use **Python 3.x**.
- Use **ffmpeg** for video handling and encoding (assume it’s installed and on PATH).[web:15]
- Use a widely-available GUI toolkit:
  - Prefer **PyQt6 or PySide6** (you choose one and stick with it), or **Tkinter** if you must.
  - The UI should be a single main window with panels.
- Use **OpenCV** and/or **Pillow** for:
  - Frame extraction and manipulation
  - Cropping
  - Chroma keying (creation of alpha channel).[web:14]
- For spritesheets, generate **PNG** with:
  - Transparent background (alpha channel)
  - Even grid of frames in row-major order
  - Layout and metadata compatible with Godot 4’s AnimatedSprite2D / SpriteFrames workflow.[web:13]
- The Godot instructions `.txt` must clearly describe:
  - Sprite sheet file name and pixel size of each frame
  - Columns/rows or frame order
  - How to import and configure it in Godot’s SpriteFrames / AnimatedSprite2D editor.[web:13]
- **Dependency management must use `uv`, not `pip`.**  
  - The project should be configured with a `pyproject.toml` suitable for `uv`.[web:24][web:25]
  - I should be able to run:
    - `uv sync` to create the env and install dependencies.
    - `uv run app/main.py` to launch the app.[web:24][web:29]

General behavior rules:
- Code must be **runnable end-to-end**, no “pseudo-code”.
- Use **`pyproject.toml` + uv** instead of `requirements.txt` + pip.
- Prefer small, focused modules over one giant file, but keep the structure simple enough for a non-expert.
- Always explain:
  - How to install `uv`.
  - How to install dependencies with `uv`.
  - How to run the app using `uv`.
- After each major step, include a **short “How to test this step”** section.

UI/UX requirements:
- Main window layout:
  - Left side: controls
    - File chooser for input (video/gif)
    - Playback and navigation controls (play/pause, current frame index, total frames)
    - Time-range / frame-range selectors:
      - Start and end time sliders (or numeric fields)
      - Option to specify desired number of frames and/or FPS
    - Cropping controls:
      - Either numeric (x, y, width, height) or click-and-drag selection
    - Chroma key controls:
      - A color picker (or a simple “pick color from frame” click)
      - Tolerance slider
      - Toggle chroma-key on/off
    - Output options:
      - Output type: GIF / MP4 / PNG sprite sheet
      - Output path selector
      - For sprite sheets:
        - Number of columns (or auto)
        - Optional max width / frame size
  - Right side: **live preview panel**
    - Shows the currently selected frame, after crop and chroma key
    - Allows scrubbing through frames in the chosen range

Frame selection rules:
- The user can:
  - Select specific individual frames (e.g., 0, 5, 10, 11, 12).
  - OR specify:
    - Start time and end time
    - Either FPS or total number of frames to sample between them
- Frames must be exported in correct chronological order.

Cropping rules:
- Cropping must be applied consistently to all selected frames.
- Cropping must be previewable before export.
- If the user does not crop, use the full frame.

Chroma key rules:
- Allow the user to choose a color from the current preview frame (eyedropper-style or approximated via clicking).
- Allow a tolerance value (e.g., 0–100) to control how aggressively similar colors are removed.
- Result:
  - All removed pixels become fully transparent in the PNG / sprite sheet.
  - For GIF/MP4, you can either:
    - Keep background, or
    - Approximate transparency using GIF transparency if reasonably simple.

Export behavior:
- GIF export:
  - Build an animated GIF from the selected frames.
  - Respect a user-set or inferred FPS (or per-frame duration).
- MP4 export:
  - Use ffmpeg to encode the selected frames to an MP4 file.
  - Provide reasonable default settings (H.264, 720p if resized, etc.).[web:9]
- Sprite sheet export:
  - Lay out frames in a grid in row-major order.
  - Optionally let user set number of columns; rows are then derived.
  - Save as PNG with alpha.
  - Generate a `.txt` file next to the PNG with:
    - Frame width and height
    - Number of columns and rows
    - Total frame count
    - The order frames are laid out in
    - Step-by-step Godot 4 instructions to:
      - Create a SpriteFrames (or AnimatedSprite2D) resource
      - Import the sprite sheet
      - Set up grid size and animation frames using the given metadata.[web:13][web:16]

Implementation details (you choose details but follow these constraints):
- Video handling:
  - Use ffmpeg and/or OpenCV for decoding frames.
  - Be robust to common containers: mp4, mkv, webm, mov, and GIF.[web:20]
- Chroma key implementation:
  - Convert frame to an appropriate color space (e.g., HSV).
  - Build a mask based on selected color and tolerance.
  - Apply mask to create transparent background (alpha channel).[web:14]
- Performance:
  - Avoid loading all frames into memory at once for long videos.
  - Either:
    - Stream frames as needed, or
    - Cache only the selected frames.
- Temporary files:
  - Store temporary frames and intermediates in a temp directory.
  - Clean them up on successful export and also when the app exits.

Testing instructions (must be implemented and documented in the repo):
- Provide a **“How to Test”** section in the README that uses this scenario:
  1. Use `input.mp4` as a sample file (assume user has it).
  2. Load `input.mp4` in the app.
  3. Select the first frame and last frame in the video.
  4. Choose output type: **sprite sheet**.
  5. Export.
  6. Verify:
     - The sprite sheet’s first and last frames match the original video’s first and last frames (visually).
     - The accompanying Godot instructions `.txt` can be followed to:
       - Create a minimal Godot scene.
       - Import the sprite sheet.
       - Set up an animation using those two frames.
       - Run the scene and confirm it animates between the two frames in-game.[web:13][web:19]
  7. Confirm that any temporary files created during this process are cleaned up.
- Include clear Godot 4.x-oriented text in the `.txt` so I can easily follow it.

Project structure (you can tweak, but keep it simple and well-organized):
- `app/`
  - `__init__.py`
  - `main.py` (entry point launching the GUI)
  - `ui.py` (widgets, layout)
  - `video_io.py` (ffmpeg/OpenCV integration, frame extraction)
  - `processing.py` (cropping, chroma key, frame sampling)
  - `exporters.py` (GIF, MP4, sprite sheet export + Godot txt)
  - `temp_utils.py` (temp directory management, cleanup)
- `pyproject.toml` configured for `uv` dependency management and `uv run app/main.py` as the main entry command.[web:24][web:25][web:32]
- `README.md`
- `LICENSE` (use MIT unless told otherwise)
- Example assets:
  - An example `input.mp4` reference in README (not required to be included in repo).

Coding style:
- Use clear, descriptive function and class names.
- Add minimal but helpful comments and docstrings.
- Validate user inputs where it’s easy (e.g., check that there is at least one selected frame before export).

When you respond:
1. First, propose a brief design summary (UI layout, main classes/modules, data flow).
2. Then generate the initial project structure with minimal working:
   - `app/main.py` that opens an empty window with left controls panel and right preview area.
   - A stub implementation for loading a video and showing the first frame in the preview.
3. Then iteratively add features in small steps when I ask:
   - Frame navigation and range selection
   - Cropping
   - Chroma key
   - Exporters (GIF, MP4, sprite sheet + Godot `.txt`)
   - Temp file handling and cleanup
4. After each step, include:
   - “How to run” using `uv`
   - “How to test this step”

You must treat my follow-up messages as change requests or “next feature” tasks and keep the app building forward, not rewriting from scratch unless I explicitly ask.

