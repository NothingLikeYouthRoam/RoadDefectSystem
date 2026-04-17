"""
AI 分析配置对话框 — 配置 API Key、Base URL、模型名
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import AppStyles
from core.ai_analyzer import load_config, save_config, test_connection

# 预设平台配置
PRESETS = [
    ('自定义', '', ''),
    ('硅基流动 - Qwen3-8B (免费)', 'https://api.siliconflow.cn', 'Qwen/Qwen3-8B'),
    ('硅基流动 - DeepSeek-V3', 'https://api.siliconflow.cn', 'deepseek-ai/DeepSeek-V3'),
    ('硅基流动 - Qwen2.5-7B (免费)', 'https://api.siliconflow.cn', 'Qwen/Qwen2.5-7B-Instruct'),
    ('DeepSeek 官方', 'https://api.deepseek.com', 'deepseek-chat'),
]


class AIConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 分析设置')
        self.setFixedSize(480, 420)
        self._init_ui()
        self._load()

    def _init_ui(self):
        c = AppStyles.COLORS
        self.setStyleSheet(f'''
            QDialog {{
                background-color: {c["background_elevated"]};
            }}
        ''')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel('AI 分析接口配置')
        title.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        title.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        layout.addWidget(title)

        desc = QLabel('配置 OpenAI 兼容的 LLM API，选择预设或自定义填写')
        desc.setFont(QFont('Microsoft YaHei', 9))
        desc.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 预设选择
        preset_row = QHBoxLayout()
        preset_label = QLabel('快速选择:')
        preset_label.setFont(QFont('Microsoft YaHei', 9))
        preset_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        preset_row.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([p[0] for p in PRESETS])
        self.preset_combo.setFont(QFont('Microsoft YaHei', 9))
        self.preset_combo.setStyleSheet(AppStyles.get_combobox_style())
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        # 表单
        form_group = QGroupBox('接口参数')
        form_group.setStyleSheet(AppStyles.get_groupbox_style())
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(12)

        # API Key
        key_row = QVBoxLayout()
        key_label = QLabel('API Key:')
        key_label.setFont(QFont('Microsoft YaHei', 9))
        key_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        key_row.addWidget(key_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText('sk-...')
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setFont(QFont('Microsoft YaHei', 9))
        self.key_input.setStyleSheet(AppStyles.get_input_style())
        key_row.addWidget(self.key_input)
        form_layout.addLayout(key_row)

        # Base URL
        url_row = QVBoxLayout()
        url_label = QLabel('Base URL:')
        url_label.setFont(QFont('Microsoft YaHei', 9))
        url_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        url_row.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('https://api.siliconflow.cn')
        self.url_input.setFont(QFont('Microsoft YaHei', 9))
        self.url_input.setStyleSheet(AppStyles.get_input_style())
        url_row.addWidget(self.url_input)
        form_layout.addLayout(url_row)

        # Model
        model_row = QVBoxLayout()
        model_label = QLabel('模型名称:')
        model_label.setFont(QFont('Microsoft YaHei', 9))
        model_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        model_row.addWidget(model_label)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText('Qwen/Qwen3-8B')
        self.model_input.setFont(QFont('Microsoft YaHei', 9))
        self.model_input.setStyleSheet(AppStyles.get_input_style())
        model_row.addWidget(self.model_input)
        form_layout.addLayout(model_row)

        layout.addWidget(form_group)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        test_btn = QPushButton('测试连接')
        test_btn.setFixedHeight(34)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setFont(QFont('Microsoft YaHei', 9))
        test_btn.setStyleSheet(AppStyles.get_button_style('outline'))
        test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton('取消')
        cancel_btn.setFixedHeight(34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFont(QFont('Microsoft YaHei', 9))
        cancel_btn.setStyleSheet(AppStyles.get_button_style('ghost'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton('保存')
        save_btn.setFixedHeight(34)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFont(QFont('Microsoft YaHei', 9))
        save_btn.setStyleSheet(AppStyles.get_button_style('primary'))
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load(self):
        cfg = load_config()
        self.key_input.setText(cfg.get('api_key', ''))
        self.url_input.setText(cfg.get('base_url', 'https://api.siliconflow.cn'))
        self.model_input.setText(cfg.get('model', 'Qwen/Qwen3-8B'))
        # 尝试匹配预设
        base = cfg.get('base_url', '').rstrip('/')
        model = cfg.get('model', '')
        for i, (_, url, m) in enumerate(PRESETS):
            if url and url.rstrip('/') == base and m == model:
                self.preset_combo.setCurrentIndex(i)
                break

    def _on_preset_changed(self, index):
        if index <= 0:
            return
        _, url, model = PRESETS[index]
        if url:
            self.url_input.setText(url)
        if model:
            self.model_input.setText(model)

    def _on_save(self):
        key = self.key_input.text().strip()
        url = self.url_input.text().strip()
        model = self.model_input.text().strip()

        if not key:
            QMessageBox.warning(self, '提示', '请输入 API Key')
            return
        if not url:
            QMessageBox.warning(self, '提示', '请输入 Base URL')
            return
        if not model:
            QMessageBox.warning(self, '提示', '请输入模型名称')
            return

        save_config(key, url, model)
        QMessageBox.information(self, '成功', '配置已保存')
        self.accept()

    def _on_test(self):
        key = self.key_input.text().strip()
        url = self.url_input.text().strip()
        model = self.model_input.text().strip()

        if not key or not url or not model:
            QMessageBox.warning(self, '提示', '请填写所有配置项')
            return

        ok, msg = test_connection(key, url, model)
        if ok:
            QMessageBox.information(self, '成功', msg)
        else:
            QMessageBox.warning(self, '失败', msg)
