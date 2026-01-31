import numpy as np
import cv2

class ImageProcessor:
    def __init__(self):
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.use_crop = False
        
        # Chroma Key settings
        self.use_chroma = False
        self.target_color_rgb = (0, 255, 0)
        self.tolerance = 30
        self.edge_trim = 0

    def set_crop_margins(self, left, top, right, bottom):
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom
        self.use_crop = (left > 0 or top > 0 or right > 0 or bottom > 0)

    def set_chroma_settings(self, enabled, color_rgb, tolerance, edge_trim):
        self.use_chroma = enabled
        self.target_color_rgb = color_rgb
        self.tolerance = tolerance
        self.edge_trim = edge_trim

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        result = frame
        
        # 1. Apply Crop
        if self.use_crop:
            img_h, img_w = frame.shape[:2]
            x1 = max(0, min(self.margin_left, img_w - 1))
            y1 = max(0, min(self.margin_top, img_h - 1))
            x2 = max(x1 + 1, min(img_w - self.margin_right, img_w))
            y2 = max(y1 + 1, min(img_h - self.margin_bottom, img_h))
            result = result[y1:y2, x1:x2].copy()

        # 2. Apply Chroma Key (convert to RGBA)
        if self.use_chroma:
            hsv = cv2.cvtColor(result, cv2.COLOR_RGB2HSV)
            target_np = np.uint8([[self.target_color_rgb]])
            target_hsv = cv2.cvtColor(target_np, cv2.COLOR_RGB2HSV)[0][0]
            
            # Create the raw color mask
            lower = np.array([
                max(0, int(target_hsv[0]) - self.tolerance),
                max(0, int(target_hsv[1]) - self.tolerance * 2),
                max(20, int(target_hsv[2]) - self.tolerance * 3)
            ], dtype=np.uint8)
            upper = np.array([min(180, int(target_hsv[0]) + self.tolerance), 255, 255], dtype=np.uint8)
            
            mask = cv2.inRange(hsv, lower, upper)
            
            # --- "Inside/Outside" Logic ---
            # We want to identify the subject (foreground).
            # The mask currently contains the background (1s) and subject (0s).
            foreground_mask = cv2.bitwise_not(mask)
            
            # Fill holes inside the subject so that inner green-ish pixels are ignored
            # We find contours of the foreground and fill them.
            contours, _ = cv2.findContours(foreground_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            solid_foreground = np.zeros_like(foreground_mask)
            cv2.drawContours(solid_foreground, contours, -1, 255, thickness=cv2.FILLED)
            
            # Now solid_foreground is a clean "blob" of the subject.
            # Edge Trim should only affect the boundary of this solid blob.
            if self.edge_trim > 0:
                kernel = np.ones((3, 3), np.uint8)
                solid_foreground = cv2.erode(solid_foreground, kernel, iterations=self.edge_trim)
            
            # Create RGBA image using the solid filled mask
            rgba = cv2.cvtColor(result, cv2.COLOR_RGB2RGBA)
            rgba[:, :, 3] = solid_foreground
            return rgba
        
        return result