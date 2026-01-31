from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QLabel, QFileDialog, QFrame, QSlider,
    QSpinBox, QGroupBox, QFormLayout, QCheckBox, QComboBox,
    QProgressBar, QLineEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
import numpy as np

class PreviewLabel(QLabel):
    margins_selected = pyqtSignal(int, int, int, int)
    color_picked = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        self.setMinimumSize(400, 300)
        self.selection_start = None
        self.is_selecting = False
        self.is_picking_color = False
        self.full_pixmap = None
        self.processed_pixmap = None
        self.scaled_pixmap_rect = QRect()
        self.image_size = (0, 0)
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.show_cropped_only = False
        self.checker_pixmap = QPixmap(20, 20)
        p = QPainter(self.checker_pixmap)
        p.fillRect(0, 0, 10, 10, QColor(80, 80, 80))
        p.fillRect(10, 10, 10, 10, QColor(80, 80, 80))
        p.fillRect(10, 0, 10, 10, QColor(50, 50, 50))
        p.fillRect(0, 10, 10, 10, QColor(50, 50, 50))
        p.end()

    def set_frame(self, full_pixmap, processed_pixmap, original_size, margins, show_cropped_only=False):
        self.full_pixmap = full_pixmap
        self.processed_pixmap = processed_pixmap
        self.image_size = original_size
        self.margin_left, self.margin_top, self.margin_right, self.margin_bottom = margins
        self.show_cropped_only = show_cropped_only
        self._update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def _update_display(self):
        pix = self.processed_pixmap if (self.show_cropped_only and self.processed_pixmap) else self.full_pixmap
        if not pix: return
        scaled = pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)
        pw, ph = scaled.width(), scaled.height()
        lx, ly = self.width(), self.height()
        self.scaled_pixmap_rect = QRect((lx - pw) // 2, (ly - ph) // 2, pw, ph)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.scaled_pixmap_rect.contains(event.pos()):
            if self.is_picking_color: self._pick_color(event.pos())
            elif not self.show_cropped_only:
                self.selection_start = event.pos()
                self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting: self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self._finalize_selection(event.pos())
            self.update()

    def _pick_color(self, pos):
        sx, sy = self.image_size[0] / self.scaled_pixmap_rect.width(), self.image_size[1] / self.scaled_pixmap_rect.height()
        ix, iy = int((pos.x() - self.scaled_pixmap_rect.left()) * sx), int((pos.y() - self.scaled_pixmap_rect.top()) * sy)
        img = self.full_pixmap.toImage()
        if 0 <= ix < img.width() and 0 <= iy < img.height():
            c = QColor(img.pixel(ix, iy))
            self.color_picked.emit(c.red(), c.green(), c.blue())

    def _finalize_selection(self, end):
        if not self.selection_start: return
        rect = QRect(self.selection_start, end).normalized().intersected(self.scaled_pixmap_rect)
        if rect.width() < 5 or rect.height() < 5: return
        sx, sy = self.image_size[0] / self.scaled_pixmap_rect.width(), self.image_size[1] / self.scaled_pixmap_rect.height()
        x1, y1 = int((rect.left() - self.scaled_pixmap_rect.left()) * sx), int((rect.top() - self.scaled_pixmap_rect.top()) * sy)
        x2, y2 = int((rect.right() - self.scaled_pixmap_rect.left() + 1) * sx), int((rect.bottom() - self.scaled_pixmap_rect.top() + 1) * sy)
        self.margins_selected.emit(x1, y1, max(0, self.image_size[0] - x2), max(0, self.image_size[1] - y2))
        self.selection_start = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.scaled_pixmap_rect.isEmpty(): painter.drawTiledPixmap(self.scaled_pixmap_rect, self.checker_pixmap)
        painter.end()
        super().paintEvent(event)
        if not self.full_pixmap or self.show_cropped_only: return
        painter = QPainter(self)
        if self.is_selecting and self.selection_start:
            rect = QRect(self.selection_start, self.mapFromGlobal(self.cursor().pos())).normalized()
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawRect(rect)
        else:
            sx, sy = self.scaled_pixmap_rect.width() / self.image_size[0], self.scaled_pixmap_rect.height() / self.image_size[1]
            x, y = self.scaled_pixmap_rect.left() + int(self.margin_left * sx), self.scaled_pixmap_rect.top() + int(self.margin_top * sy)
            w, h = int((self.image_size[0] - self.margin_left - self.margin_right) * sx), int((self.image_size[1] - self.margin_top - self.margin_bottom) * sy)
            cr = QRect(x, y, w, h)
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.scaled_pixmap_rect.left(), self.scaled_pixmap_rect.top(), x - self.scaled_pixmap_rect.left(), self.scaled_pixmap_rect.height())
            painter.drawRect(cr.right() + 1, self.scaled_pixmap_rect.top(), self.scaled_pixmap_rect.right() - cr.right(), self.scaled_pixmap_rect.height())
            painter.drawRect(x, self.scaled_pixmap_rect.top(), w, y - self.scaled_pixmap_rect.top())
            painter.drawRect(x, cr.bottom() + 1, w, self.scaled_pixmap_rect.bottom() - cr.bottom())
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawRect(cr)
        painter.end()

class MainWindow(QMainWindow):
    frame_changed = pyqtSignal(int)
    range_changed = pyqtSignal(int, int)
    crop_changed = pyqtSignal(int, int, int, int)
    chroma_changed = pyqtSignal(bool, tuple, int, int)
    export_requested = pyqtSignal(str, int)
    add_current_frame_requested = pyqtSignal()

    def __init__(self, on_open_file_callback):
        super().__init__()
        self.setWindowTitle("SpriteSpite")
        self.resize(1200, 900)
        self.on_open_file_callback = on_open_file_callback
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left Panel
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(340)
        left_layout = QVBoxLayout(self.left_panel)
        
        self.open_button = QPushButton("Open Video/GIF")
        self.open_button.clicked.connect(self._handle_open_file)
        left_layout.addWidget(self.open_button)
        
        info_group = QGroupBox("File Info")
        info_layout = QVBoxLayout()
        self.info_label = QLabel("No file loaded")
        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)

        # Selection Group
        sel_group = QGroupBox("Frame Selection")
        sel_layout = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        self.range_radio = QRadioButton("Range")
        self.range_radio.setChecked(True)
        self.individual_radio = QRadioButton("Individual")
        mode_layout.addWidget(self.range_radio)
        mode_layout.addWidget(self.individual_radio)
        sel_layout.addLayout(mode_layout)
        
        # Range sub-panel
        self.range_widget = QWidget()
        range_fl = QFormLayout(self.range_widget)
        self.start_frame_spin = QSpinBox()
        self.end_frame_spin = QSpinBox()
        range_fl.addRow("Start:", self.start_frame_spin)
        range_fl.addRow("End:", self.end_frame_spin)
        sel_layout.addWidget(self.range_widget)
        
        # Individual sub-panel
        self.individual_widget = QWidget()
        self.individual_widget.setVisible(False)
        indiv_layout = QVBoxLayout(self.individual_widget)
        self.frames_input = QLineEdit()
        self.frames_input.setPlaceholderText("e.g. 0, 5, 10-15")
        indiv_layout.addWidget(QLabel("Frame List:"))
        indiv_layout.addWidget(self.frames_input)
        self.add_frame_btn = QPushButton("Add Current Frame")
        self.add_frame_btn.clicked.connect(lambda: self.add_current_frame_requested.emit())
        indiv_layout.addWidget(self.add_frame_btn)
        sel_layout.addWidget(self.individual_widget)
        
        self.range_radio.toggled.connect(lambda b: self.range_widget.setVisible(b))
        self.individual_radio.toggled.connect(lambda b: self.individual_widget.setVisible(b))
        
        sel_group.setLayout(sel_layout)
        left_layout.addWidget(sel_group)

        # Cropping/Chroma Group
        crop_group = QGroupBox("Cropping (Margins)")
        crop_layout = QFormLayout()
        self.crop_left_spin = QSpinBox()
        self.crop_top_spin = QSpinBox()
        self.crop_right_spin = QSpinBox()
        self.crop_bottom_spin = QSpinBox()
        for s in [self.crop_left_spin, self.crop_top_spin, self.crop_right_spin, self.crop_bottom_spin]:
            s.setRange(0, 9999)
            s.valueChanged.connect(self._handle_crop_change)
        crop_layout.addRow("Left:", self.crop_left_spin)
        crop_layout.addRow("Top:", self.crop_top_spin)
        crop_layout.addRow("Right:", self.crop_right_spin)
        crop_layout.addRow("Bottom:", self.crop_bottom_spin)
        self.reset_crop_button = QPushButton("Reset Crop")
        self.reset_crop_button.clicked.connect(self.reset_crop)
        crop_layout.addRow(self.reset_crop_button)
        crop_group.setLayout(crop_layout)
        left_layout.addWidget(crop_group)

        chroma_group = QGroupBox("Chroma Key")
        chroma_layout = QVBoxLayout()
        self.chroma_enable_check = QCheckBox("Enable Chroma Key")
        self.chroma_enable_check.stateChanged.connect(self._handle_chroma_change)
        chroma_layout.addWidget(self.chroma_enable_check)
        color_row = QHBoxLayout()
        self.pick_color_button = QPushButton("Pick Color")
        self.pick_color_button.setCheckable(True)
        self.pick_color_button.toggled.connect(self._handle_pick_mode)
        color_row.addWidget(self.pick_color_button)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: green; border: 1px solid white;")
        color_row.addWidget(self.color_preview)
        chroma_layout.addLayout(color_row)
        self.chroma_color = (0, 255, 0)
        chroma_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.tolerance_slider.setRange(0, 100)
        self.tolerance_slider.setValue(30)
        self.tolerance_slider.valueChanged.connect(self._handle_chroma_change)
        chroma_layout.addWidget(self.tolerance_slider)
        chroma_layout.addWidget(QLabel("Edge Trim:"))
        self.edge_trim_slider = QSlider(Qt.Orientation.Horizontal)
        self.edge_trim_slider.setRange(0, 10)
        self.edge_trim_slider.setValue(0)
        self.edge_trim_slider.valueChanged.connect(self._handle_chroma_change)
        chroma_layout.addWidget(self.edge_trim_slider)
        chroma_group.setLayout(chroma_layout)
        left_layout.addWidget(chroma_group)
        
        self.show_cropped_check = QCheckBox("Show Cropped Result")
        self.show_cropped_check.stateChanged.connect(lambda: self.frame_changed.emit(self.scrub_slider.value()))
        left_layout.addWidget(self.show_cropped_check)

        # Export Group
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(["Sprite Sheet (PNG)", "Animated GIF", "MP4 Video"])
        export_layout.addWidget(QLabel("Format:"))
        export_layout.addWidget(self.export_type_combo)
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(0, 100)
        self.cols_spin.setSpecialValueText("Auto")
        export_layout.addWidget(QLabel("Columns:"))
        export_layout.addWidget(self.cols_spin)
        self.export_button = QPushButton("Process & Export")
        self.export_button.setStyleSheet("background-color: #2c5a2c; font-weight: bold;")
        self.export_button.clicked.connect(self._handle_export)
        export_layout.addWidget(self.export_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        export_layout.addWidget(self.progress_bar)
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        left_layout.addStretch()
        
        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.preview_label = PreviewLabel()
        self.preview_label.margins_selected.connect(self._handle_mouse_crop)
        self.preview_label.color_picked.connect(self._handle_color_picked)
        right_layout.addWidget(self.preview_label, stretch=1)
        nav_layout = QVBoxLayout()
        self.scrub_slider = QSlider(Qt.Orientation.Horizontal)
        self.scrub_slider.valueChanged.connect(self._handle_slider_change)
        nav_layout.addWidget(self.scrub_slider)
        bottom_nav = QHBoxLayout()
        self.current_frame_label = QLabel("Frame: 0/0")
        bottom_nav.addWidget(self.current_frame_label)
        bottom_nav.addStretch()
        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        bottom_nav.addWidget(self.play_button)
        nav_layout.addLayout(bottom_nav)
        right_layout.addLayout(nav_layout)
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(right_panel)

    def _handle_open_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video (*.mp4 *.gif *.mkv *.webm);;All (*)")
        if p: self.on_open_file_callback(p)

    def _handle_mouse_crop(self, l, t, r, b):
        for s, v in zip([self.crop_left_spin, self.crop_top_spin, self.crop_right_spin, self.crop_bottom_spin], [l, t, r, b]):
            s.blockSignals(True); s.setValue(v); s.blockSignals(False)
        self._handle_crop_change()

    def _handle_pick_mode(self, a):
        self.preview_label.is_picking_color = a
        self.preview_label.setCursor(Qt.CursorShape.CrossCursor if a else Qt.CursorShape.ArrowCursor)
        self.pick_color_button.setText("Click Frame..." if a else "Pick Color")

    def _handle_color_picked(self, r, g, b):
        self.chroma_color = (r, g, b)
        self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid white;")
        self.pick_color_button.setChecked(False); self._handle_chroma_change()

    def _handle_chroma_change(self):
        self.chroma_changed.emit(self.chroma_enable_check.isChecked(), self.chroma_color, self.tolerance_slider.value(), self.edge_trim_slider.value())

    def setup_video_controls(self, c, w, h):
        self.scrub_slider.setRange(0, c - 1); self.start_frame_spin.setRange(0, c - 1)
        self.end_frame_spin.setRange(0, c - 1); self.end_frame_spin.setValue(c - 1)
        for s, m in zip([self.crop_left_spin, self.crop_top_spin, self.crop_right_spin, self.crop_bottom_spin], [w, h, w, h]): s.setRange(0, m - 1)
        self.reset_crop()

    def reset_crop(self):
        for s in [self.crop_left_spin, self.crop_top_spin, self.crop_right_spin, self.crop_bottom_spin]: s.setValue(0)
        self._handle_crop_change()

    def _handle_crop_change(self):
        self.crop_changed.emit(self.crop_left_spin.value(), self.crop_top_spin.value(), self.crop_right_spin.value(), self.crop_bottom_spin.value())

    def _handle_slider_change(self, v): self.frame_changed.emit(v)

    def _handle_export(self): self.export_requested.emit(self.export_type_combo.currentText(), self.cols_spin.value())

    def update_preview(self, full, proc, cur, tot):
        self.current_frame_label.setText(f"Frame: {cur}/{tot-1}")
        self.scrub_slider.blockSignals(True); self.scrub_slider.setValue(cur); self.scrub_slider.blockSignals(False)
        def to_pix(a):
            h, w = a.shape[:2]; f = QImage.Format.Format_RGB888 if a.shape[2] == 3 else QImage.Format.Format_RGBA8888
            return QPixmap.fromImage(QImage(a.data, w, h, a.strides[0], f).copy())
        m = (self.crop_left_spin.value(), self.crop_top_spin.value(), self.crop_right_spin.value(), self.crop_bottom_spin.value())
        self.preview_label.set_frame(to_pix(full), to_pix(proc), (full.shape[1], full.shape[0]), m, self.show_cropped_check.isChecked())

    def set_progress(self, v):
        self.progress_bar.setVisible(0 < v < 100); self.progress_bar.setValue(v)

    def set_info(self, t): self.info_label.setText(t)
