import numpy as np
import cv2
from PIL import Image

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
        self.exclusion_points = [] # List of (x, y) in original image coordinates
        
        # Resizing
        self.resize_w = 0
        self.resize_h = 0
        self.use_resize = False
        
        # Compression (Color Quantization)
        self.max_colors = 256

    def set_crop_margins(self, left, top, right, bottom):
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom
        self.use_crop = (left > 0 or top > 0 or right > 0 or bottom > 0)

    def set_chroma_settings(self, enabled, color_rgb, tolerance, edge_trim, exclusion_points=None):
        self.use_chroma = enabled
        self.target_color_rgb = color_rgb
        self.tolerance = tolerance
        self.edge_trim = edge_trim
        if exclusion_points is not None:
            self.exclusion_points = exclusion_points

    def set_resize(self, enabled, w, h):
        self.use_resize = enabled
        self.resize_w = w
        self.resize_h = h

    def set_compression(self, max_colors):
        self.max_colors = max_colors

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        result = frame
        
        # 1. Apply Crop
        img_h, img_w = frame.shape[:2]
        x1, y1, x2, y2 = 0, 0, img_w, img_h
        if self.use_crop:
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
            
            lower = np.array([
                max(0, int(target_hsv[0]) - self.tolerance),
                max(0, int(target_hsv[1]) - self.tolerance * 2),
                max(20, int(target_hsv[2]) - self.tolerance * 3)
            ], dtype=np.uint8)
            upper = np.array([min(180, int(target_hsv[0]) + self.tolerance), 255, 255], dtype=np.uint8)
            
            mask = cv2.inRange(hsv, lower, upper)
            foreground_mask = cv2.bitwise_not(mask)
            contours, _ = cv2.findContours(foreground_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            solid_foreground = np.zeros_like(foreground_mask)
            cv2.drawContours(solid_foreground, contours, -1, 255, thickness=cv2.FILLED)
            
            # Apply manual exclusions
            if self.exclusion_points:
                for px, py in self.exclusion_points:
                    # Map original coordinates to cropped coordinates
                    cx, cy = px - x1, py - y1
                    # Ensure coordinates are within the current cropped frame
                    if 0 <= cx < result.shape[1] and 0 <= cy < result.shape[0]:
                        # If the clicked point was originally background, remove that connected component from the solid foreground
                        if mask[cy, cx] == 255:
                            # Find all connected background pixels from this point
                            flood_mask = np.zeros((mask.shape[0] + 2, mask.shape[1] + 2), np.uint8)
                            cv2.floodFill(mask, flood_mask, (cx, cy), 255, flags=cv2.FLOODFILL_MASK_ONLY | (1 << 8))
                            comp_mask = (flood_mask[1:-1, 1:-1] == 1)
                            solid_foreground[comp_mask] = 0
                        else:
                            # If it wasn't background, try a color-based flood fill on the original image
                            # to remove the specific color component
                            flood_mask = np.zeros((result.shape[0] + 2, result.shape[1] + 2), np.uint8)
                            cv2.floodFill(result, flood_mask, (cx, cy), (0, 0, 0, 0), 
                                          loDiff=(10, 10, 10), upDiff=(10, 10, 10),
                                          flags=cv2.FLOODFILL_MASK_ONLY | (1 << 8))
                            comp_mask = (flood_mask[1:-1, 1:-1] == 1)
                            solid_foreground[comp_mask] = 0

            if self.edge_trim > 0:
                kernel = np.ones((3, 3), np.uint8)
                solid_foreground = cv2.erode(solid_foreground, kernel, iterations=self.edge_trim)
            
            rgba = cv2.cvtColor(result, cv2.COLOR_RGB2RGBA)
            rgba[:, :, 3] = solid_foreground
            result = rgba

        # 3. Apply Resize
        if self.use_resize and self.resize_w > 0 and self.resize_h > 0:
            # We use INTER_AREA for downscaling as it's less prone to moiré
            result = cv2.resize(result, (self.resize_w, self.resize_h), interpolation=cv2.INTER_AREA)
        
        # 4. Apply Compression (Color Quantization)
        if self.max_colors < 256:
            if result.shape[2] == 4:
                pil_img = Image.fromarray(result, 'RGBA')
                alpha = pil_img.getchannel('A')
                quantized = pil_img.convert('RGB').quantize(colors=self.max_colors)
                result_pil = quantized.convert('RGBA')
                result_pil.putalpha(alpha)
                result = np.array(result_pil)
            else:
                pil_img = Image.fromarray(result, 'RGB')
                result = np.array(pil_img.quantize(colors=self.max_colors).convert('RGB'))
                
        return result