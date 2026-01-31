import cv2
import numpy as np
from typing import Optional
from functools import lru_cache

class VideoLoader:
    def __init__(self, cache_size=100):
        self.cap = None
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
        if self.cap:
            self.cap.release()
        
        self.file_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        
        if not self.cap.isOpened():
            return False
        
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_pos = -1
        self.cache.clear()
        self.cache_order.clear()
        return True

    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        if not self.cap or not self.cap.isOpened():
            return None
        
        if frame_index < 0 or frame_index >= self.frame_count:
            return None

        # 1. Check Cache
        if frame_index in self.cache:
            # Move to end of order (most recently used)
            self.cache_order.remove(frame_index)
            self.cache_order.append(frame_index)
            return self.cache[frame_index]

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
        self.cache.clear()
        self.cache_order.clear()
