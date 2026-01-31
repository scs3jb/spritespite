import sys
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer
from app.ui import MainWindow
from app.video_io import VideoLoader
from app.processing import ImageProcessor
from app.exporters import SpriteExporter

class SpriteSpiteApp:
    def __init__(self):
        self.video_loader = VideoLoader()
        self.processor = ImageProcessor()
        self.exporter = SpriteExporter(self.video_loader, self.processor)
        self.ui = MainWindow(self.handle_open_file)
        
        # Internal state
        self.current_frame_index = 0
        self.start_frame = 0
        self.end_frame = 0
        
        # Timer for playback
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.next_frame)
        
        # Timer for scrubbing debounce (improves performance during fast drags)
        self.scrub_timer = QTimer()
        self.scrub_timer.setSingleShot(True)
        self.scrub_timer.timeout.connect(self.perform_scrub)
        self.pending_scrub_index = 0
        
        # Connect UI signals
        self.ui.frame_changed.connect(self.on_scrub_slider_moved)
        self.ui.range_changed.connect(self.update_range)
        self.ui.crop_changed.connect(self.update_crop)
        self.ui.chroma_changed.connect(self.update_chroma)
        self.ui.export_requested.connect(self.handle_export)
        self.ui.add_current_frame_requested.connect(self.add_current_frame_to_list)
        self.ui.play_button.toggled.connect(self.toggle_playback)

    def add_current_frame_to_list(self):
        current = str(self.current_frame_index)
        existing = self.ui.frames_input.text().strip()
        if existing:
            self.ui.frames_input.setText(f"{existing}, {current}")
        else:
            self.ui.frames_input.setText(current)

    def _parse_frame_selection(self, selection_str, max_frames):
        """Parses strings like '5, 0, 10-12' into a list of indices preserving order."""
        indices = []
        parts = selection_str.replace(' ', '').split(',')
        for part in parts:
            if not part: continue
            try:
                if '-' in part:
                    start_str, end_str = part.split('-')
                    s, e = int(start_str), int(end_str)
                    # For ranges like 10-12, we add 10, 11, 12 in order
                    step = 1 if s <= e else -1
                    for i in range(s, e + step, step):
                        if 0 <= i < max_frames:
                            indices.append(i)
                else:
                    idx = int(part)
                    if 0 <= idx < max_frames:
                        indices.append(idx)
            except ValueError:
                continue
        return indices

    def handle_export(self, fmt_str, cols):
        # Determine which frames to export
        if self.ui.individual_radio.isChecked():
            selection = self.ui.frames_input.text()
            frame_indices = self._parse_frame_selection(selection, self.video_loader.frame_count)
            if not frame_indices:
                print("Error: No valid frames selected for export.")
                return
        else:
            # Range mode
            frame_indices = list(range(self.ui.start_frame_spin.value(), self.ui.end_frame_spin.value() + 1))

        # Choose file path
        ext = ".png" if "Sprite" in fmt_str else (".gif" if "GIF" in fmt_str else ".mp4")
        filter_str = f"File (*{ext})"
        
        path, _ = QFileDialog.getSaveFileName(self.ui, "Export File", "output" + ext, filter_str)
        if not path: return
        
        self.ui.export_button.setEnabled(False)
        self.ui.set_progress(1)
        
        success = False
        fps = self.video_loader.fps
        
        if "Sprite" in fmt_str:
            success = self.exporter.export_spritesheet(path, frame_indices, cols, self.ui.set_progress)
        elif "GIF" in fmt_str:
            success = self.exporter.export_gif(path, frame_indices, fps, self.ui.set_progress)
        elif "MP4" in fmt_str:
            success = self.exporter.export_mp4(path, frame_indices, fps, self.ui.set_progress)
            
        self.ui.set_progress(100)
        self.ui.export_button.setEnabled(True)
        
        if success:
            print(f"Export successful: {path}")

    def handle_open_file(self, file_path: str):
        if self.video_loader.open_file(file_path):
            count = self.video_loader.frame_count
            w, h = self.video_loader.width, self.video_loader.height
            info = (
                f"File: {file_path}\n"
                f"Resolution: {w}x{h}\n"
                f"Frames: {count}\n"
                f"FPS: {self.video_loader.fps:.2f}"
            )
            self.ui.set_info(info)
            self.ui.setup_video_controls(count, w, h)
            
            self.current_frame_index = 0
            self.start_frame = 0
            self.end_frame = count - 1
            
            self.seek_to_frame(0)
            
            interval = max(16, int(1000 / max(1, self.video_loader.fps)))
            self.playback_timer.setInterval(interval)
        else:
            self.ui.set_info("Failed to open file.")

    def on_scrub_slider_moved(self, index: int):
        # If playing, seek immediately (don't debounce playback)
        if self.playback_timer.isActive():
            self.seek_to_frame(index)
        else:
            # During manual scrubbing, debounce the decode request
            self.pending_scrub_index = index
            self.scrub_timer.start(15) # 15ms debounce

    def perform_scrub(self):
        self.seek_to_frame(self.pending_scrub_index)

    def seek_to_frame(self, index: int):
        self.current_frame_index = index
        frame = self.video_loader.get_frame(index)
        if frame is not None:
            # We provide both the raw frame and the processed (cropped/chroma'd) frame
            processed = self.processor.process_frame(frame)
            self.ui.update_preview(frame, processed, index, self.video_loader.frame_count)

    def update_crop(self, left, top, right, bottom):
        self.processor.set_crop_margins(left, top, right, bottom)
        self.seek_to_frame(self.current_frame_index)

    def update_chroma(self, enabled, color, tolerance, edge_trim):
        self.processor.set_chroma_settings(enabled, color, tolerance, edge_trim)
        self.seek_to_frame(self.current_frame_index)

    def update_range(self, start: int, end: int):
        self.start_frame = start
        self.end_frame = end
        # If current frame is out of range, seek to start
        if self.current_frame_index < start or self.current_frame_index > end:
            self.seek_to_frame(start)

    def toggle_playback(self, playing: bool):
        if playing:
            self.ui.play_button.setText("Pause")
            self.playback_timer.start()
        else:
            self.ui.play_button.setText("Play")
            self.playback_timer.stop()

    def next_frame(self):
        next_idx = self.current_frame_index + 1
        if next_idx > self.end_frame:
            next_idx = self.start_frame
        
        self.seek_to_frame(next_idx)

    def run(self):
        self.ui.show()

def main():
    app = QApplication(sys.argv)
    spritespite = SpriteSpiteApp()
    spritespite.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()