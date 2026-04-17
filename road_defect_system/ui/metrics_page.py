from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QTabWidget, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import AppStyles


class MetricsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._create_top_bar())

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f'''
            QTabWidget::pane {{
                border: 1px solid {AppStyles.COLORS["border"]};
                background-color: {AppStyles.COLORS["background_card"]};
                border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {AppStyles.COLORS["background_elevated"]};
                color: {AppStyles.COLORS["text_secondary"]};
                padding: 10px 28px;
                border: none;
                border-top-left-radius: {AppStyles.BORDER_RADIUS["small"]}px;
                border-top-right-radius: {AppStyles.BORDER_RADIUS["small"]}px;
                margin-right: 4px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {AppStyles.COLORS["gradient_start"]}, stop:1 {AppStyles.COLORS["gradient_end"]});
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {AppStyles.COLORS["background_hover"]};
                color: {AppStyles.COLORS["text_primary"]};
            }}
        ''')
        self.tabs.addTab(self._create_loss_tab(), '损失曲线')
        self.tabs.addTab(self._create_eval_tab(), '评估指标')
        layout.addWidget(self.tabs, 1)

    def _create_top_bar(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet('background: transparent;')
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        record_label = QLabel('训练记录:')
        record_label.setFont(QFont('Microsoft YaHei', 9))
        record_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        self.record_combo = QComboBox()
        self.record_combo.addItems(['run_2024-01-15_14-30-25', 'run_2024-01-14_10-15-30', 'run_2024-01-13_16-45-00'])
        self.record_combo.setFixedWidth(220)
        self.record_combo.setFont(QFont('Microsoft YaHei', 9))
        self.record_combo.setStyleSheet(AppStyles.get_combobox_style())

        btn_reload = QPushButton('重新加载')
        btn_reload.setFixedHeight(32)
        btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reload.setFont(QFont('Microsoft YaHei', 9))
        btn_reload.setStyleSheet(AppStyles.get_button_style('outline', 'small'))

        layout.addWidget(record_label)
        layout.addWidget(self.record_combo)
        layout.addStretch()
        layout.addWidget(btn_reload)
        return widget

    def _create_loss_tab(self):
        c = AppStyles.COLORS
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        chart_group = QGroupBox('训练损失曲线')
        chart_group.setStyleSheet(AppStyles.get_groupbox_style())
        chart_layout = QVBoxLayout(chart_group)
        loss_chart = AppStyles.create_empty_state('暂无损失数据', 'chart_placeholder')
        loss_chart.setMinimumHeight(280)
        chart_layout.addWidget(loss_chart)
        layout.addWidget(chart_group, 1)

        legend_group = QGroupBox('曲线说明')
        legend_group.setStyleSheet(AppStyles.get_groupbox_style())
        legend_layout = QHBoxLayout(legend_group)
        legend_layout.setSpacing(30)

        legend_configs = [
            ('定位损失 (Box)', '#FF6B6B'),
            ('分类损失 (Cls)', c['gradient_start']),
            ('DFL损失', c['success']),
        ]

        for name, color in legend_configs:
            item = QWidget()
            item_layout = QHBoxLayout(item)
            item_layout.setSpacing(8)
            item_layout.setContentsMargins(0, 0, 0, 0)

            color_box = QLabel()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f'background-color: {color}; border-radius: 3px; border: none;')

            label = QLabel(name)
            label.setFont(QFont('Microsoft YaHei', 9))
            label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

            item_layout.addWidget(color_box)
            item_layout.addWidget(label)
            legend_layout.addWidget(item)

        layout.addWidget(legend_group)
        return widget

    def _create_eval_tab(self):
        c = AppStyles.COLORS
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        metrics_group = QGroupBox('最终评估指标')
        metrics_group.setStyleSheet(AppStyles.get_groupbox_style())
        metrics_layout = QGridLayout(metrics_group)
        metrics_layout.setSpacing(12)

        metric_configs = [
            ('mAP50', '0.856', c['gradient_start']),
            ('mAP50-95', '0.742', c['gradient_end']),
            ('Precision', '0.891', c['success']),
            ('Recall', '0.834', c['warning']),
        ]

        for idx, (name, value, color) in enumerate(metric_configs):
            card = AppStyles.create_stat_card(name, value, color)
            metrics_layout.addWidget(card['widget'], idx // 2, idx % 2)
        layout.addWidget(metrics_group)

        curves_group = QGroupBox('详细曲线')
        curves_group.setStyleSheet(AppStyles.get_groupbox_style())
        curves_layout = QHBoxLayout(curves_group)
        curves_layout.setSpacing(16)

        curve_configs = [
            ('P-R 曲线', c['gradient_start']),
            ('F1-置信度曲线', c['gradient_end']),
        ]

        for text, color in curve_configs:
            curve = AppStyles.create_empty_state(text, 'chart_placeholder')
            curve.setMinimumHeight(160)
            curves_layout.addWidget(curve, 1)

        layout.addWidget(curves_group, 1)
        return widget
