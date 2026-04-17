from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QLineEdit,
    QDoubleSpinBox, QSpinBox, QFormLayout, QFileDialog, QMessageBox, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import AppStyles


class ModelManagePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._info_labels = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.addWidget(self._create_model_file_group())
        layout.addWidget(self._create_param_group())

    def _create_model_file_group(self):
        c = AppStyles.COLORS
        group = QGroupBox('模型文件设置')
        group.setStyleSheet(AppStyles.get_groupbox_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(16)

        path_layout = QHBoxLayout()
        path_label = QLabel('模型路径:')
        path_label.setFont(QFont('Microsoft YaHei', 9))
        path_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        self.model_path_input = QLineEdit()
        self.model_path_input.setText('model/best.pt')
        self.model_path_input.setFixedHeight(36)
        self.model_path_input.setFont(QFont('Microsoft YaHei', 9))
        self.model_path_input.setStyleSheet(AppStyles.get_input_style())

        btn_browse = QPushButton('浏览')
        btn_browse.setFixedWidth(80)
        btn_browse.setFixedHeight(36)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.setFont(QFont('Microsoft YaHei', 9))
        btn_browse.setStyleSheet(AppStyles.get_button_style('outline', 'small'))
        btn_browse.clicked.connect(self._on_browse_model)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.model_path_input, 1)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        # 模型信息面板
        info_group = QWidget()
        info_group.setStyleSheet(f'background-color: {c["background_elevated"]}; border: 1px solid {c["border"]}; border-top: 1px solid {c["border_light"]}; border-radius: {AppStyles.BORDER_RADIUS["group"]}px; padding: 12px;')
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(12)

        info_configs = [
            ('file_path', '文件路径:', '未加载'),
            ('file_size', '文件大小:', '--'),
            ('model_type', '模型类型:', '--'),
            ('classes', '类别列表:', '--'),
            ('input_size', '输入尺寸:', '--'),
            ('status', '加载状态:', '未加载'),
        ]

        for idx, (key, title, default) in enumerate(info_configs):
            title_label = QLabel(title)
            title_label.setFont(QFont('Microsoft YaHei', 9))
            title_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            value_label = QLabel(default)
            value_label.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
            value_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
            info_layout.addWidget(title_label, idx, 0)
            info_layout.addWidget(value_label, idx, 1)
            self._info_labels[key] = value_label
        info_layout.setColumnStretch(0, 0)
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnMinimumWidth(0, 80)

        layout.addWidget(info_group)

        btn_layout = QHBoxLayout()
        btn_verify = QPushButton('验证并加载模型')
        btn_verify.setFixedHeight(40)
        btn_verify.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_verify.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        btn_verify.setStyleSheet(AppStyles.get_button_style('success'))
        btn_verify.clicked.connect(self._on_verify_model)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_verify)
        layout.addLayout(btn_layout)
        return group

    def _create_param_group(self):
        c = AppStyles.COLORS
        group = QGroupBox('检测参数设置')
        group.setStyleSheet(AppStyles.get_groupbox_style())
        form_layout = QFormLayout(group)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.conf_spin = QDoubleSpinBox()
        self.iou_spin = QDoubleSpinBox()
        self.max_det_spin = QSpinBox()

        spin_style = AppStyles.get_spinbox_style()

        param_configs = [
            ('置信度阈值:', self.conf_spin, (0.0, 1.0, 0.25, 0.05, 140)),
            ('IoU 阈值:', self.iou_spin, (0.0, 1.0, 0.45, 0.05, 140)),
            ('最大检测数:', self.max_det_spin, (1, 1000, 300, 1, 140))
        ]

        for label_text, spin, (r_min, r_max, r_val, r_step, width) in param_configs:
            label = QLabel(label_text)
            label.setFont(QFont('Microsoft YaHei', 9))
            label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            spin.setRange(r_min, r_max)
            spin.setValue(r_val)
            if hasattr(spin, 'setSingleStep'):
                spin.setSingleStep(r_step)
            if isinstance(spin, QDoubleSpinBox):
                spin.setDecimals(2)
            spin.setFixedWidth(width)
            spin.setFixedHeight(36)
            spin.setFont(QFont('Microsoft YaHei', 9))
            spin.setStyleSheet(spin_style)
            form_layout.setWidget(form_layout.rowCount(), QFormLayout.ItemRole.LabelRole, label)
            form_layout.setWidget(form_layout.rowCount() - 1, QFormLayout.ItemRole.FieldRole, spin)

        device_label = QLabel('推理设备:')
        device_label.setFont(QFont('Microsoft YaHei', 9))
        device_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        self.device_combo = QComboBox()
        self.device_combo.addItems(['CPU', 'CUDA (GPU)'])
        self.device_combo.setFixedWidth(140)
        self.device_combo.setFixedHeight(36)
        self.device_combo.setFont(QFont('Microsoft YaHei', 9))
        self.device_combo.setStyleSheet(AppStyles.get_combobox_style())

        row = form_layout.rowCount()
        form_layout.setWidget(row, QFormLayout.ItemRole.LabelRole, device_label)
        form_layout.setWidget(row, QFormLayout.ItemRole.FieldRole, self.device_combo)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton('保存设置')
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        btn_save.setStyleSheet(AppStyles.get_button_style('primary'))
        btn_save.clicked.connect(self._on_save_params)

        btn_reset = QPushButton('重置')
        btn_reset.setFixedHeight(40)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        btn_reset.setStyleSheet(AppStyles.get_button_style('ghost'))
        btn_reset.clicked.connect(self._on_reset_params)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_reset)

        form_layout.addRow('', btn_layout)

        return group

    # ── 功能实现 ──

    def _on_browse_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择模型文件', '', '模型文件 (*.pt *.pth);;所有文件 (*)')
        if file_path:
            self.model_path_input.setText(file_path)

    def _on_verify_model(self):
        import os
        model_path = self.model_path_input.text().strip()
        if not model_path:
            QMessageBox.warning(self, '提示', '请输入模型文件路径')
            return
        if not os.path.exists(model_path):
            QMessageBox.warning(self, '错误', f'文件不存在: {model_path}')
            return

        try:
            from core.detector import RoadDefectDetector
            from utils.file_utils import format_file_size

            detector = RoadDefectDetector.get_instance()
            success = detector.load_model(model_path)

            if not success:
                QMessageBox.critical(self, '错误', '模型加载失败')
                self._info_labels['status'].setText('加载失败')
                self._info_labels['status'].setStyleSheet(
                    f'color: {AppStyles.COLORS["error"]}; border: none;')
                return

            # 更新模型信息
            info = detector.get_model_info()
            self._info_labels['file_path'].setText(model_path)
            self._info_labels['file_size'].setText(format_file_size(os.path.getsize(model_path)))
            self._info_labels['model_type'].setText('YOLOv8')
            self._info_labels['classes'].setText(', '.join(info['class_names'][:8])
                                                 + ('...' if len(info['class_names']) > 8 else ''))
            self._info_labels['input_size'].setText('640 x 640')
            self._info_labels['status'].setText('已加载')
            self._info_labels['status'].setStyleSheet(
                f'color: {AppStyles.COLORS["success"]}; border: none;')

            # 同步参数到控件
            self.conf_spin.setValue(info['conf_thres'])
            self.iou_spin.setValue(info['iou_thres'])
            self.max_det_spin.setValue(info['max_det'])

            QMessageBox.information(self, '成功',
                                    f'模型加载成功\n类别数: {len(info["class_names"])}\n'
                                    f'类别: {", ".join(info["class_names"])}')

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'模型加载失败: {e}')
            self._info_labels['status'].setText('加载失败')
            self._info_labels['status'].setStyleSheet(
                f'color: {AppStyles.COLORS["error"]}; border: none;')

    def _on_save_params(self):
        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()
        detector.set_conf_thres(self.conf_spin.value())
        detector.set_iou_thres(self.iou_spin.value())
        detector.set_max_det(self.max_det_spin.value())
        QMessageBox.information(self, '成功', '参数已保存并应用')

    def _on_reset_params(self):
        self.conf_spin.setValue(0.25)
        self.iou_spin.setValue(0.45)
        self.max_det_spin.setValue(300)
        self.device_combo.setCurrentIndex(0)
