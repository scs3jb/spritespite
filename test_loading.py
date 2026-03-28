import cv2
import numpy as np
from app.video_io import VideoLoader

def test_png_loading():
    loader = VideoLoader()
    path = '/home/jbriggs/downloads/Gemini_Generated_Image_kqdb5xkqdb5xkqdb.png'
    success = loader.open_file(path)
    print(f"Success: {success}")
    if success:
        print(f"Frame Count: {loader.frame_count}")
        print(f"Width: {loader.width}, Height: {loader.height}")
        print(f"FPS: {loader.fps}")
        
        # Check if it fits in 32-bit int
        try:
            val = int(loader.frame_count)
            if -(2**31) <= val - 1 <= (2**31 - 1):
                print("Frame count is within 32-bit signed integer range.")
            else:
                print("Frame count is STILL outside range!")
        except Exception as e:
            print(f"Range check failed: {e}")

if __name__ == "__main__":
    test_png_loading()
