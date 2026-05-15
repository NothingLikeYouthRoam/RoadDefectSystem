import os
import json
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QMessageBox, QDoubleSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
from styles import AppStyles
from utils.image_utils import numpy_to_qpixmap, get_video_info
from core.tracker import SimpleTracker


class DetectVideoPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path = None
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_frame)
        self._is_paused = False
        self._is_detecting = False
        self._frame_count = 0
        self._last_screenshot = None
        self._video_label_ready = False
        self._max_detections = 0
        self._frames_with_detections = 0
        self._tracker = SimpleTracker()

        self._init_ui()

    # ── UI ──

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._create_main_panel(), 3)
        layout.addWidget(self._create_side_panel(), 1)

    def _create_main_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.video_label = AppStyles.create_placeholder('点击下方按钮打开视频文件', 'video')
        self.video_label.setMinimumHeight(500)
        layout.addWidget(self.video_label, 1)

        control_group = QGroupBox('控制面板')
        control_group.setStyleSheet(AppStyles.get_groupbox_style())
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(10)

        for text, variant, func in [
            ('打开视频', 'outline', self._on_open_video),
            ('开始检测', 'primary', self._on_start_detect),
            ('暂停', 'ghost', self._on_pause),
            ('停止', 'ghost', self._on_stop),
            ('截图', 'outline', self._on_screenshot),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont('Microsoft YaHei', 9))
            btn.setStyleSheet(AppStyles.get_button_style(variant))
            btn.clicked.connect(func)
            control_layout.addWidget(btn)

        control_layout.addStretch()

        interval_label = QLabel('检测间隔:')
        interval_label.setFont(QFont('Microsoft YaHei', 9))
        interval_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.05, 2.0)
        self.interval_spin.setValue(0.1)
        self.interval_spin.setSuffix('s')
        self.interval_spin.setFixedWidth(80)
        self.interval_spin.setFont(QFont('Microsoft YaHei', 9))
        self.interval_spin.setStyleSheet(AppStyles.get_spinbox_style())

        control_layout.addWidget(interval_label)
        control_layout.addWidget(self.interval_spin)
        layout.addWidget(control_group)
        return widget

    def _create_side_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info_group = QGroupBox('检测信息')
        info_group.setStyleSheet(AppStyles.get_groupbox_style())
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)

        self.info_labels = {}
        for key, title, value in [
            ('file', '文件:', '未加载'),
            ('duration', '时长:', '--'),
            ('fps', '帧率:', '--'),
            ('resolution', '分辨率:', '--'),
            ('current_frame', '当前帧:', '0'),
            ('total_detections', '检测数:', '0'),
        ]:
            row = QHBoxLayout()
            t = QLabel(title)
            t.setFont(QFont('Microsoft YaHei', 9))
            t.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            v = QLabel(value)
            v.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
            v.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
            self.info_labels[key] = v
            row.addWidget(t)
            row.addWidget(v, 1)
            info_layout.addLayout(row)
        layout.addWidget(info_group)

        stats_group = QGroupBox('实时统计')
        stats_group.setStyleSheet(AppStyles.get_groupbox_style())
        sl = QVBoxLayout(stats_group)
        sl.setSpacing(8)

        self.total_count_label = QLabel('0')
        self.total_count_label.setFont(QFont('Microsoft YaHei', 32, QFont.Weight.Bold))
        self.total_count_label.setStyleSheet(f'color: {c["gradient_start"]}; border: none;')
        self.total_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        total_cl = QLabel('累计检测目标数')
        total_cl.setFont(QFont('Microsoft YaHei', 9))
        total_cl.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        total_cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sl.addWidget(self.total_count_label)
        sl.addWidget(total_cl)
        sl.addSpacing(4)

        rate_row = QHBoxLayout()
        rate_title = QLabel('检出率:')
        rate_title.setFont(QFont('Microsoft YaHei', 9))
        rate_title.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.rate_label = QLabel('0.0%')
        self.rate_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        self.rate_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        rate_row.addWidget(rate_title)
        rate_row.addWidget(self.rate_label, 1)
        sl.addLayout(rate_row)

        max_row = QHBoxLayout()
        max_title = QLabel('最大单帧:')
        max_title.setFont(QFont('Microsoft YaHei', 9))
        max_title.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.max_label = QLabel('0')
        self.max_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        self.max_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        max_row.addWidget(max_title)
        max_row.addWidget(self.max_label, 1)
        sl.addLayout(max_row)
        layout.addWidget(stats_group, 1)
        return widget

    # ── 显示 ──

    def _ensure_video_label(self):
        if self._video_label_ready:
            return
        self._video_label_ready = True
        old = self.video_label
        parent_layout = old.parent().layout()
        idx = parent_layout.indexOf(old)
        parent_layout.removeWidget(old)
        old.deleteLater()

        c = AppStyles.COLORS
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(500)
        label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        label.setStyleSheet(f'''
            background-color: {c["background_main"]};
            border: 2px solid {c["border_focus"]};
            border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
        ''')
        parent_layout.insertWidget(idx, label, 1)
        self.video_label = label

    def _update_display(self, frame_bgr):
        self._ensure_video_label()
        pixmap = numpy_to_qpixmap(frame_bgr)
        cr = self.video_label.contentsRect()
        if cr.width() < 10 or cr.height() < 10:
            return
        scaled = pixmap.scaled(
            cr.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.video_label.setPixmap(scaled)

    # ── 操作 ──

    def _on_open_video(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择视频', '', '视频文件 (*.mp4 *.avi *.mov *.mkv)'
        )
        if not file_path:
            return

        self._on_stop()
        self._video_path = file_path

        info = get_video_info(file_path)
        if not info:
            QMessageBox.warning(self, '错误', '无法读取视频文件')
            return

        self.info_labels['file'].setText(os.path.basename(file_path))
        d = info.get('duration', 0)
        m, s = divmod(int(d), 60)
        self.info_labels['duration'].setText(f'{m:02d}:{s:02d}')
        self.info_labels['fps'].setText(f'{info["fps"]:.1f}')
        self.info_labels['resolution'].setText(f'{info["width"]}x{info["height"]}')
        self.info_labels['current_frame'].setText('0')
        self.info_labels['total_detections'].setText('0')
        self._frame_count = 0
        self._max_detections = 0
        self._frames_with_detections = 0
        self._tracker.reset()
        self.total_count_label.setText('0')
        self.rate_label.setText('0.0%')
        self.max_label.setText('0')

        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            self._update_display(frame)

    def _on_start_detect(self):
        if not self._video_path:
            QMessageBox.information(self, '提示', '请先选择视频文件')
            return

        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()
        if not detector._model:
            from core.detector import DEFAULT_MODEL_PATH
            model_path = DEFAULT_MODEL_PATH
            if not os.path.exists(model_path):
                QMessageBox.warning(self, '错误',
                    f'模型文件不存在: {model_path}\n请先在模型管理中加载模型')
                return
            try:
                detector.load_model(model_path)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'模型加载失败: {e}')
                return

        if self._cap is not None:
            self._cap.release()

        self._cap = cv2.VideoCapture(self._video_path)
        if not self._cap.isOpened():
            QMessageBox.warning(self, '错误', '无法打开视频文件')
            return

        self._is_detecting = True
        self._is_paused = False
        self._frame_count = 0
        self._max_detections = 0
        self._frames_with_detections = 0
        self._tracker.reset()
        self.info_labels['total_detections'].setText('0')
        self.total_count_label.setText('0')
        self.rate_label.setText('0.0%')
        self.max_label.setText('0')

        # 根据检测间隔计算 timer 间隔（ms）
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        interval_sec = self.interval_spin.value()
        self._skip_frames = max(1, int(fps * interval_sec)) - 1
        self._frame_idx = 0

        self._timer.start(1)

    # ── 核心：逐帧检测 ──

    def _process_frame(self):
        if self._cap is None or not self._cap.isOpened() or self._is_paused:
            return

        ret, frame = self._cap.read()
        if not ret:
            self._timer.stop()
            self._is_detecting = False
            self._cap.release()
            self._cap = None
            self._save_record()
            QMessageBox.information(self, '完成', '视频检测完成')
            return

        self._frame_count += 1
        self.info_labels['current_frame'].setText(str(self._frame_count))

        # 按间隔跳帧：只在目标帧执行检测
        self._frame_idx += 1
        should_detect = self._frame_idx > self._skip_frames
        if should_detect:
            self._frame_idx = 0

        if should_detect:
            from core.detector import RoadDefectDetector
            detector = RoadDefectDetector.get_instance()
            result = detector.detect(frame)

            if result is not None:
                detections, annotated = detector.parse_results(result)

                raw_count = len(detections)
                if raw_count > 0:
                    self._frames_with_detections += 1
                if raw_count > self._max_detections:
                    self._max_detections = raw_count

                new_count, _ = self._tracker.update(detections)
                unique = self._tracker.total_unique
                self.info_labels['total_detections'].setText(str(unique))
                self.total_count_label.setText(str(unique))
                rate = self._frames_with_detections / self._frame_count * 100
                self.rate_label.setText(f'{rate:.1f}%')
                self.max_label.setText(str(self._max_detections))
        else:
            self._tracker.miss_all()

        display_frame = frame
        active_tracks = self._tracker.active_tracks
        if active_tracks:
            display_frame = self._draw_trackingResults(frame, active_tracks)

        self._last_screenshot = display_frame
        self._update_display(display_frame)

    def _on_pause(self):
        if not self._is_detecting:
            return
        self._is_paused = not self._is_paused

    def _on_stop(self):
        should_save = self._is_detecting and self._frame_count > 0
        self._timer.stop()
        self._is_detecting = False
        self._is_paused = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if should_save:
            self._save_record()

    def _save_record(self):
        unique_dets = self._tracker.all_unique_detections
        if not unique_dets:
            return
        try:
            from database.db_manager import DatabaseManager
            from database.models import DetectionRecord

            class_count = {}
            for d in unique_dets:
                class_count[d['class_name']] = class_count.get(d['class_name'], 0) + 1
            class_dist = ', '.join(f"{k}:{v}" for k, v in sorted(class_count.items()))

            details = json.dumps([
                {'class': d['class_name'],
                 'confidence': round(d['confidence'], 3),
                 'bbox': list(map(int, d['bbox']))}
                for d in unique_dets
            ], ensure_ascii=False)

            record = DetectionRecord(
                type='video',
                source=os.path.basename(self._video_path) if self._video_path else 'unknown',
                model_name='best.pt',
                total_objects=len(unique_dets),
                class_distribution=class_dist,
                details=details,
            )
            db = DatabaseManager()
            db.add_record(record)
        except Exception as e:
            print(f"[视频检测] 保存记录失败: {e}")

    def _draw_trackingResults(self, frame, tracks):
        display = frame.copy()
        colors = {
            0: (255, 0, 0),
            1: (0, 255, 0),
            2: (0, 0, 255),
            3: (255, 255, 0),
            4: (255, 0, 255),
            5: (0, 255, 255),
        }
        for track in tracks:
            bbox = list(map(int, track['bbox']))
            track_id = track['id']
            class_name = track['class_name']
            confidence = track['confidence']
            color = colors[track_id % len(colors)]
            cv2.rectangle(display, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            label = f'#{track_id} {class_name} {confidence:.2f}'
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(display, (bbox[0], bbox[1] - h - 6),
                        (bbox[0] + w, bbox[1]), color, -1)
            cv2.putText(display, label, (bbox[0], bbox[1] - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return display

    def _on_screenshot(self):
        if self._last_screenshot is None:
            QMessageBox.information(self, '提示', '请先开始检测')
            return

        from utils.file_utils import save_file_dialog
        save_path = save_file_dialog(self, '保存截图', 'screenshot.png',
                                     '图片 (*.png *.jpg)')
        if not save_path:
            return

        success = cv2.imwrite(save_path, self._last_screenshot)
        if success:
            QMessageBox.information(self, '成功', f'已保存到:\n{save_path}')
        else:
            QMessageBox.warning(self, '失败', '保存失败')
