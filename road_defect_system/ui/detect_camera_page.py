import os
import json
import time
import threading
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QMessageBox, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPixmap
from styles import AppStyles
from utils.image_utils import numpy_to_qpixmap
from core.tracker import SimpleTracker


class StatusDot(QWidget):
    """状态指示点"""
    def __init__(self, size=24, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = QColor(107, 114, 128)
        self.setFixedSize(size, size)

    def set_status(self, status):
        colors = {
            'connected': QColor(16, 185, 129),
            'disconnected': QColor(107, 114, 128),
            'error': QColor(239, 68, 68),
        }
        self._color = colors.get(status, QColor(107, 114, 128))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, self._size - 4, self._size - 4)
        p.end()


class DetectCameraPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_frame)
        self._is_detecting = False
        self._is_paused = False
        self._detect_busy = False
        self._video_source = None  # 视频文件路径（模拟摄像头）
        self._frame_count = 0
        self._max_detections = 0
        self._frames_with_detections = 0
        self._last_screenshot = None
        self._tracker = SimpleTracker()
        self._fps_start_time = time.time()
        self._fps_frame_count = 0
        self._current_fps = 0.0
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        main_widget = self._create_main_panel()
        layout.addWidget(main_widget, 3)

        side_widget = self._create_side_panel()
        layout.addWidget(side_widget, 1)

    def _create_main_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.camera_label = AppStyles.create_placeholder('点击下方按钮开启摄像头', 'camera')
        self.camera_label.setMinimumHeight(400)
        layout.addWidget(self.camera_label, 1)

        control_group = QGroupBox('控制面板')
        control_group.setStyleSheet(AppStyles.get_groupbox_style())
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(10)

        btn_configs = [
            ('开启摄像头', 'outline', self._on_start_camera),
            ('打开视频', 'outline', self._on_open_video),
            ('开始检测', 'primary', self._on_start_detect),
            ('暂停', 'ghost', self._on_pause),
            ('停止', 'ghost', self._on_stop),
            ('截图', 'outline', self._on_screenshot),
        ]

        for text, variant, func in btn_configs:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont('Microsoft YaHei', 9))
            btn.setStyleSheet(AppStyles.get_button_style(variant))
            btn.clicked.connect(func)
            control_layout.addWidget(btn)

        control_layout.addStretch()

        camera_select_label = QLabel('摄像头:')
        camera_select_label.setFont(QFont('Microsoft YaHei', 9))
        camera_select_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        self.camera_combo = QComboBox()
        self.camera_combo.addItems(['摄像头 0', '摄像头 1', '摄像头 2'])
        self.camera_combo.setFixedWidth(120)
        self.camera_combo.setFont(QFont('Microsoft YaHei', 9))
        self.camera_combo.setStyleSheet(AppStyles.get_combobox_style())

        control_layout.addWidget(camera_select_label)
        control_layout.addWidget(self.camera_combo)

        layout.addWidget(control_group)
        return widget

    def _create_side_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 连接状态
        status_group = QGroupBox('连接状态')
        status_group.setStyleSheet(AppStyles.get_groupbox_style())
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_indicator = StatusDot(24)
        self.status_text = QLabel('未连接')
        self.status_text.setFont(QFont('Microsoft YaHei', 10))
        self.status_text.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_layout.addWidget(self.status_indicator, 0, Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_text)
        layout.addWidget(status_group)

        # 实时信息
        info_group = QGroupBox('实时信息')
        info_group.setStyleSheet(AppStyles.get_groupbox_style())
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)

        self.info_labels = {}
        info_configs = [
            ('fps', 'FPS:', '0'),
            ('resolution', '分辨率:', '--'),
            ('total_detections', '总检测数:', '0'),
        ]

        for key, title, value in info_configs:
            row_layout = QHBoxLayout()
            title_label = QLabel(title)
            title_label.setFont(QFont('Microsoft YaHei', 9))
            title_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            value_label = QLabel(value)
            value_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
            value_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
            self.info_labels[key] = value_label
            row_layout.addWidget(title_label)
            row_layout.addWidget(value_label, 1)
            info_layout.addLayout(row_layout)
        layout.addWidget(info_group)

        # 实时统计
        stats_group = QGroupBox('实时统计')
        stats_group.setStyleSheet(AppStyles.get_groupbox_style())
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)

        self.total_count_label = QLabel('0')
        self.total_count_label.setFont(QFont('Microsoft YaHei', 32, QFont.Weight.Bold))
        self.total_count_label.setStyleSheet(f'color: {c["gradient_start"]}; border: none;')
        self.total_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        total_cl = QLabel('累计检测目标数')
        total_cl.setFont(QFont('Microsoft YaHei', 9))
        total_cl.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        total_cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats_layout.addWidget(self.total_count_label)
        stats_layout.addWidget(total_cl)
        stats_layout.addSpacing(4)

        rate_row = QHBoxLayout()
        rate_title = QLabel('检出率:')
        rate_title.setFont(QFont('Microsoft YaHei', 9))
        rate_title.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.rate_label = QLabel('0.0%')
        self.rate_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        self.rate_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        rate_row.addWidget(rate_title)
        rate_row.addWidget(self.rate_label, 1)
        stats_layout.addLayout(rate_row)

        max_row = QHBoxLayout()
        max_title = QLabel('最大单帧:')
        max_title.setFont(QFont('Microsoft YaHei', 9))
        max_title.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.max_label = QLabel('0')
        self.max_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        self.max_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        max_row.addWidget(max_title)
        max_row.addWidget(self.max_label, 1)
        stats_layout.addLayout(max_row)
        layout.addWidget(stats_group, 1)
        return widget

    # ── 功能实现 ──

    def _update_display(self, pixmap):
        """更新摄像头显示（复用同一个 QLabel，仅刷新 pixmap）"""
        label = self.camera_label
        if not isinstance(label, QLabel) or label.pixmap() is None:
            # 首次：替换 placeholder 为可复用的 QLabel
            parent_layout = label.parent().layout()
            idx = parent_layout.indexOf(label)
            parent_layout.removeWidget(label)
            label.deleteLater()

            new_label = QLabel()
            new_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            new_label.setMinimumHeight(400)
            # Ignored: 布局忽略 sizeHint，防止 pixmap 驱动 label 尺寸增长
            new_label.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
            )
            c = AppStyles.COLORS
            new_label.setStyleSheet(f'''
                background-color: {c["background_main"]};
                border: 2px solid {c["border_focus"]};
                border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
            ''')
            parent_layout.insertWidget(idx, new_label)
            self.camera_label = new_label
            label = new_label

        cr = label.contentsRect()
        if cr.width() < 10 or cr.height() < 10:
            return
        scaled = pixmap.scaled(
            cr.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        label.setPixmap(scaled)

    def _on_open_video(self):
        """用视频文件模拟摄像头输入"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', '', '视频文件 (*.mp4 *.avi *.mov *.mkv)')
        if not file_path:
            return

        self._on_stop()
        self._video_source = file_path
        self._cap = cv2.VideoCapture(file_path)
        if not self._cap.isOpened():
            self.status_indicator.set_status('error')
            self.status_text.setText('打开失败')
            QMessageBox.warning(self, '错误', '无法打开视频文件')
            return

        self.status_indicator.set_status('connected')
        self.status_text.setText(os.path.basename(file_path))
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.info_labels['resolution'].setText(f'{w}x{h}')

        self._is_detecting = False
        self._is_paused = False
        self._fps_start_time = time.time()
        self._fps_frame_count = 0
        self._timer.start(33)

    def _on_start_camera(self):
        self._on_stop()

        cam_idx = self.camera_combo.currentIndex()
        self._cap = cv2.VideoCapture(cam_idx)
        if not self._cap.isOpened():
            self.status_indicator.set_status('error')
            self.status_text.setText('连接失败')
            QMessageBox.warning(self, '错误', '无法打开摄像头')
            return

        # 更新状态
        self.status_indicator.set_status('connected')
        self.status_text.setText('已连接')
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.info_labels['resolution'].setText(f'{w}x{h}')

        # 开始预览（不检测）
        self._is_detecting = False
        self._is_paused = False
        self._fps_start_time = time.time()
        self._fps_frame_count = 0
        self._timer.start(33)  # ~30fps 预览

    def _on_start_detect(self):
        if self._cap is None or not self._cap.isOpened():
            QMessageBox.information(self, '提示', '请先开启摄像头或打开视频文件')
            return

        # 确保模型已加载
        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()
        if not detector._model:
            model_path = 'model/best.pt'
            if not os.path.exists(model_path):
                QMessageBox.warning(self, '错误', f'模型文件不存在: {model_path}\n请先在模型管理中加载模型')
                return
            try:
                detector.load_model(model_path)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'模型加载失败: {e}')
                return

        self._is_detecting = True
        self._is_paused = False
        self._detect_busy = False
        self._frame_count = 0
        self._max_detections = 0
        self._frames_with_detections = 0
        self._tracker.reset()
        self.info_labels['total_detections'].setText('0')
        self.total_count_label.setText('0')
        self.rate_label.setText('0.0%')
        self.max_label.setText('0')

    def _process_frame(self):
        if self._cap is None or not self._cap.isOpened():
            return
        if self._is_paused:
            return

        ret, frame = self._cap.read()
        if not ret:
            # 视频文件播放完毕
            if self._video_source:
                self._on_stop()
                QMessageBox.information(self, '完成', '视频播放完毕')
            return

        # FPS 计算
        self._fps_frame_count += 1
        elapsed = time.time() - self._fps_start_time
        if elapsed >= 1.0:
            self._current_fps = self._fps_frame_count / elapsed
            self.info_labels['fps'].setText(f'{self._current_fps:.1f}')
            self._fps_frame_count = 0
            self._fps_start_time = time.time()

        if self._is_detecting:
            # 始终立即显示原始帧，保证流畅
            pixmap = numpy_to_qpixmap(frame)
            self._update_display(pixmap)

            # 后台线程检测（如果上一次检测已完成）
            if not self._detect_busy:
                self._detect_busy = True
                frame_copy = frame.copy()
                threading.Thread(
                    target=self._detect_in_thread,
                    args=(frame_copy,),
                    daemon=True
                ).start()
        else:
            # 未开启检测，直接显示原始帧
            pixmap = numpy_to_qpixmap(frame)
            self._update_display(pixmap)

    def _detect_in_thread(self, frame):
        """在后台线程中执行检测"""
        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()
        result = detector.detect(frame)

        detections = []
        annotated = frame
        if result is not None:
            detections, annotated_bgr = detector.parse_results(result)
            if annotated_bgr is not None:
                annotated = annotated_bgr

        # 只有未被停止时才回调主线程
        if self._is_detecting:
            QTimer.singleShot(0, lambda d=detections, a=annotated: self._on_detect_done(d, a))

    def _on_detect_done(self, detections, annotated):
        """主线程回调：更新检测结果到 UI"""
        if not self._is_detecting:
            return
        self._detect_busy = False

        raw_count = len(detections)
        self._frame_count += 1
        if raw_count > 0:
            self._frames_with_detections += 1
        if raw_count > self._max_detections:
            self._max_detections = raw_count

        self._tracker.update(detections)
        unique = self._tracker.total_unique
        self.info_labels['total_detections'].setText(str(unique))
        self.total_count_label.setText(str(unique))
        rate = self._frames_with_detections / self._frame_count * 100
        self.rate_label.setText(f'{rate:.1f}%')
        self.max_label.setText(str(self._max_detections))
        self._last_screenshot = annotated

        # 用标注帧替换显示
        pixmap = numpy_to_qpixmap(annotated)
        self._update_display(pixmap)

    def _on_pause(self):
        if self._cap is None:
            return
        self._is_paused = not self._is_paused

    def _on_stop(self):
        should_save = self._is_detecting and self._frame_count > 0
        self._timer.stop()
        self._is_detecting = False
        self._is_paused = False
        self._detect_busy = False
        self._video_source = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self.status_indicator.set_status('disconnected')
        self.status_text.setText('未连接')
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

            if self._video_source:
                source = os.path.basename(self._video_source)
            else:
                source = f'摄像头 {self.camera_combo.currentIndex()}'
            record = DetectionRecord(
                type='camera',
                source=source,
                model_name='best.pt',
                total_objects=len(unique_dets),
                class_distribution=class_dist,
                details=details,
            )
            db = DatabaseManager()
            db.add_record(record)
        except Exception as e:
            print(f"[摄像头检测] 保存记录失败: {e}")

    def _on_screenshot(self):
        if self._last_screenshot is None:
            QMessageBox.information(self, '提示', '请先开始检测')
            return

        from utils.file_utils import save_file_dialog
        save_path = save_file_dialog(self, '保存截图', 'camera_screenshot.png',
                                     '图片 (*.png *.jpg)')
        if not save_path:
            return

        success = cv2.imwrite(save_path, self._last_screenshot)
        if success:
            QMessageBox.information(self, '成功', f'已保存到:\n{save_path}')
        else:
            QMessageBox.warning(self, '失败', '保存失败')
