import cv2
import numpy as np
import os
from PIL import Image
from pathlib import Path

class SpriteExporter:
    def __init__(self, video_loader, processor):
        self.video_loader = video_loader
        self.processor = processor

    def _get_processed_frames(self, frame_indices, progress_callback=None):
        frames = []
        total = len(frame_indices)
        for i, frame_idx in enumerate(frame_indices):
            raw_frame = self.video_loader.get_frame(frame_idx)
            if raw_frame is not None:
                processed = self.processor.process_frame(raw_frame)
                frames.append(processed)
            if progress_callback:
                progress_callback(int((i / total) * 100))
        return frames

    def export_gif(self, path, frame_indices, fps, progress_callback=None):
        frames = self._get_processed_frames(frame_indices, progress_callback)
        if not frames: return False
        
        pil_frames = [Image.fromarray(f) for f in frames]
        duration = int(1000 / max(1, fps))
        
        pil_frames[0].save(
            path,
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration,
            loop=0,
            disposal=2
        )
        return True

    def export_mp4(self, path, frame_indices, fps, progress_callback=None):
        frames = self._get_processed_frames(frame_indices, progress_callback)
        if not frames: return False
        
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))
        
        for f in frames:
            if f.shape[2] == 4:
                # Create a white background
                white_bg = np.full((h, w, 3), 255, dtype=np.uint8)
                
                # Separate color and alpha channels
                alpha = f[:, :, 3] / 255.0
                alpha = np.stack([alpha, alpha, alpha], axis=-1)
                color = f[:, :, :3]
                
                # Composite: (Foreground * Alpha) + (Background * (1 - Alpha))
                composited = (color * alpha + white_bg * (1 - alpha)).astype(np.uint8)
                bgr = cv2.cvtColor(composited, cv2.COLOR_RGB2BGR)
            else:
                bgr = cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
            out.write(bgr)
            
        out.release()
        return True

    def export_spritesheet(self, path, frame_indices, columns, progress_callback=None):
        frames = self._get_processed_frames(frame_indices, progress_callback)
        if not frames: return False
        
        num_frames = len(frames)
        f_h, f_w = frames[0].shape[:2]
        
        cols = columns if columns > 0 else int(np.ceil(np.sqrt(num_frames)))
        rows = int(np.ceil(num_frames / cols))
        
        sheet_w = cols * f_w
        sheet_h = rows * f_h
        sheet = np.zeros((sheet_h, sheet_w, 4), dtype=np.uint8)
        
        for i, frame in enumerate(frames):
            r = i // cols
            c = i % cols
            y = r * f_h
            x = c * f_w
            
            if frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
            
            sheet[y:y+f_h, x:x+f_w] = frame
            
        Image.fromarray(sheet).save(path)
        self._write_godot_meta(path, f_w, f_h, cols, rows, num_frames)
        return True

    def _write_godot_meta(self, sheet_path, f_w, f_h, cols, rows, count):
        meta_path = str(Path(sheet_path).with_suffix('.txt'))
        with open(meta_path, 'w') as f:
            f.write("--- SpriteSpite Export Metadata ---\n")
            f.write(f"Sprite Sheet: {os.path.basename(sheet_path)}\n")
            f.write(f"Frame Size: {f_w}x{f_h}\n")
            f.write(f"Grid: {cols} columns, {rows} rows\n")
            f.write(f"Total Frames: {count}\n\n")
            f.write("--- Godot 4 Import Instructions ---\n")
            f.write("1. In Godot, add an 'AnimatedSprite2D' node to your scene.\n")
            f.write("2. In the Inspector, click 'Sprite Frames' -> 'New SpriteFrames'.\n")
            f.write("3. Click the 'SpriteFrames' at the bottom of the editor to open the panel.\n")
            f.write("4. Click the 'Add frames from a Sprite Sheet' icon (grid icon).\n")
            f.write(f"5. Select '{os.path.basename(sheet_path)}'.\n")
            f.write(f"6. Set Horizontal to {cols} and Vertical to {rows}.\n")
            f.write(f"7. Select the frames (usually all {count}) and click 'Add Frames'.\n")
            f.write("8. Set 'Animation Speed' to match your source FPS.\n")
