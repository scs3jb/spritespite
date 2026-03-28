import cv2
import numpy as np
import os
from PIL import Image, ImageSequence
from typing import Optional
from functools import lru_cache

class VideoLoader:
    def __init__(self, cache_size=100):
        self.cap = None
        self.pil_img = None
        self.file_path = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        self.current_pos = -1 # Track internal head position
        
        # Simple manual cache for decoded frames
        self.cache = {}
        self.cache_order = []
        self.cache_size = cache_size

    def open_file(self, file_path: str) -> bool:
        self.close()
        self.file_path = file_path
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'):
            try:
                self.pil_img = Image.open(file_path)
                self.frame_count = getattr(self.pil_img, "n_frames", 1)
                self.width, self.height = self.pil_img.size
                self.fps = 10.0 # Default for GIFs if not found
                if "duration" in self.pil_img.info:
                    dur = self.pil_img.info["duration"]
                    if dur > 0:
                        self.fps = 1000.0 / dur
                return True
            except Exception as e:
                print(f"PIL failed to open {file_path}: {e}")
                # Fallback to OpenCV
                pass

        self.cap = cv2.VideoCapture(file_path)
        
        if not self.cap.isOpened():
            return False
        
        raw_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.frame_count = int(raw_count) if raw_count > 0 else 0
        
        # If count is nonsensical (OpenCV often returns negative or 0 for certain formats/images), 
        # try to read one frame to confirm it's at least valid
        if self.frame_count <= 0:
            ret, _ = self.cap.read()
            if ret:
                self.frame_count = 1
                # Reset position after probe read
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_pos = -1
            else:
                return False

        # Limit frame count to 32-bit signed int max (actually lower for safety)
        # to prevent overflows in UI sliders and spinboxes.
        self.frame_count = min(self.frame_count, 1_000_000_000)

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Handle 0 or NaN FPS
        if self.fps <= 0 or np.isnan(self.fps):
            self.fps = 24.0 # Default fallback
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_pos = -1 # Always reset head position
        self.cache.clear()
        self.cache_order.clear()
        return True

    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        if frame_index < 0 or frame_index >= self.frame_count:
            return None

        # 1. Check Cache
        if frame_index in self.cache:
            # Move to end of order (most recently used)
            self.cache_order.remove(frame_index)
            self.cache_order.append(frame_index)
            return self.cache[frame_index]

        rgb_frame = None

        if self.pil_img:
            try:
                self.pil_img.seek(frame_index)
                # Convert to RGB or RGBA depending on mode
                if self.pil_img.mode in ("RGBA", "LA") or (self.pil_img.mode == "P" and "transparency" in self.pil_img.info):
                    frame = self.pil_img.convert("RGBA")
                else:
                    frame = self.pil_img.convert("RGB")
                rgb_frame = np.array(frame)
            except Exception as e:
                print(f"PIL get_frame failed: {e}")
                return None
        elif self.cap and self.cap.isOpened():
            # 2. Optimized Seek
            # If we are already at the previous frame, we don't need to 'set' (which is slow)
            # We can just 'read' (which is fast)
            if frame_index != self.current_pos + 1:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            
            ret, frame = self.cap.read()
            
            if ret:
                # Update position
                self.current_pos = frame_index
                # Convert and store in cache
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                return None
        else:
            return None
        
        if rgb_frame is not None:
            self.cache[frame_index] = rgb_frame
            self.cache_order.append(frame_index)
            
            # Evict oldest if cache full
            if len(self.cache_order) > self.cache_size:
                oldest = self.cache_order.pop(0)
                del self.cache[oldest]
                
            return rgb_frame
            
        return None

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.pil_img:
            self.pil_img.close()
            self.pil_img = None
        self.cache.clear()
        self.cache_order.clear()
