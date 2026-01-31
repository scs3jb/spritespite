import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

class VideoLoader:
    def __init__(self):
        self.cap = None
        self.file_path = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0

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
        return True

    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        if not self.cap or not self.cap.isOpened():
            return None
        
        if frame_index < 0 or frame_index >= self.frame_count:
            return None
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        if ret:
            # OpenCV uses BGR, we usually want RGB for UI
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None