"""
数据统计大屏 — 基于实际检测数据的统计可视化
"""
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'sans-serif'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#171E28',
    'axes.facecolor': '#171E28',
    'axes.edgecolor': '#262F3D',
    'axes.labelcolor': '#F1F5F9',
    'xtick.color': '#8B9AB5',
    'ytick.color': '#8B9AB5',
    'text.color': '#F1F5F9',
    'grid.color': '#262F3D',
    'legend.facecolor': '#121820',
    'legend.edgecolor': '#262F3D',
    'axes.prop_cycle': plt.cycler('color', [
        '#3B82F6', '#10B981', '#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444',
    ]),
})

from collections import Counter, defaultdict
from datetime import datetime
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTabWidget, QGridLayout, QScrollArea, QSizePolicy, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from styles import AppStyles
from database.db_manager import DatabaseManager
from core.visualizer import ChartCanvas


# ── helpers ──────────────────────────────────────────────────────────

def _severity_of(count: int) -> str:
    if count <= 2:
        return '轻微'
    elif count <= 5:
        return '中等'
    return '严重'


# ── MetricsPage ──────────────────────────────────────────────────────

class MetricsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager()
        self._init_ui()

    # ── lifecycle ──

    def showEvent(self, event):
        """每次切换到该页时刷新数据"""
        super().showEvent(event)
        self._refresh()

    # ── UI skeleton ──

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 顶部刷新栏
        top_bar = QWidget()
        top_bar.setStyleSheet('background: transparent;')
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel('数据统计大屏')
        title.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        title.setStyleSheet(
            f'color: {AppStyles.COLORS["text_primary"]}; border: none;')
        top_layout.addWidget(title)
        top_layout.addStretch()

        btn_refresh = QPushButton('刷新数据')
        btn_refresh.setFixedHeight(32)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFont(QFont('Microsoft YaHei', 9))
        btn_refresh.setStyleSheet(AppStyles.get_button_style('outline', 'small'))
        btn_refresh.clicked.connect(self._refresh)
        top_layout.addWidget(btn_refresh)
        layout.addWidget(top_bar)

        # Tab 页
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppStyles.COLORS["gradient_start"]},
                    stop:1 {AppStyles.COLORS["gradient_end"]});
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {AppStyles.COLORS["background_hover"]};
                color: {AppStyles.COLORS["text_primary"]};
            }}
        ''')

        self._overview_tab = QWidget()
        self._defect_tab = QWidget()
        self._trend_tab = QWidget()
        self._train_tab = QWidget()
        self.tabs.addTab(self._overview_tab, '总览')
        self.tabs.addTab(self._defect_tab, '缺陷分析')
        self.tabs.addTab(self._trend_tab, '趋势分析')
        self.tabs.addTab(self._train_tab, '训练指标')
        layout.addWidget(self.tabs, 1)

    # ── data loading ──

    def _refresh(self):
        records = self._db.get_all_records(limit=10000)
        self._build_overview(records)
        self._build_defect(records)
        self._build_trend(records)
        self._build_train_tab()

    # ── Tab 1: 总览 ──

    def _clear_tab(self, tab_widget):
        """安全清理 tab 内容"""
        old = tab_widget.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            QWidget().setLayout(old)

    def _build_overview(self, records):
        self._clear_tab(self._overview_tab)

        c = AppStyles.COLORS
        root = QVBoxLayout(self._overview_tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # ── 统计卡片 ──
        total_detections = len(records)
        total_defects = sum(r.total_objects for r in records)

        # 计算平均置信度
        all_confs = []
        for r in records:
            for d in r.get_details_list():
                conf = d.get('confidence')
                if conf is not None:
                    all_confs.append(float(conf))
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0.0

        gps_count = sum(
            1 for r in records
            if r.latitude is not None and r.longitude is not None
        )

        card_group = QGroupBox('核心指标')
        card_group.setStyleSheet(AppStyles.get_groupbox_style())
        card_grid = QGridLayout(card_group)
        card_grid.setSpacing(12)
        card_grid.setContentsMargins(8, 8, 8, 8)

        stat_configs = [
            ('总检测次数', str(total_detections), c['gradient_start']),
            ('总缺陷数', str(total_defects), c['error']),
            ('平均置信度', f'{avg_conf:.2f}', c['success']),
            ('有GPS记录数', str(gps_count), c['accent_cyan']),
        ]
        for idx, (title, value, color) in enumerate(stat_configs):
            card = AppStyles.create_stat_card(title, value, color)
            card_grid.addWidget(card['widget'], idx // 2, idx % 2)
        root.addWidget(card_group)

        # ── 检测类型分布饼图 ──
        type_counts = Counter(r.type for r in records)
        type_display_map = {'image': '图片', 'video': '视频'}
        pie_data = {type_display_map.get(k, k): v for k, v in type_counts.items()}

        pie_group = QGroupBox('检测类型分布')
        pie_group.setStyleSheet(AppStyles.get_groupbox_style())
        pie_layout = QVBoxLayout(pie_group)
        pie_layout.setContentsMargins(4, 4, 4, 4)

        if pie_data:
            canvas = ChartCanvas(width=5, height=3.5)
            labels = list(pie_data.keys())
            values = list(pie_data.values())
            colors_list = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444']
            canvas.axes.pie(
                values, labels=labels, autopct='%1.1f%%',
                colors=colors_list[:len(labels)],
                startangle=90,
                textprops={'fontsize': 10, 'color': '#F1F5F9'},
            )
            canvas.fig.tight_layout()
            pie_layout.addWidget(canvas)
        else:
            pie_layout.addWidget(
                AppStyles.create_empty_state('暂无数据', 'chart_placeholder'))
        root.addWidget(pie_group, 1)

    # ── Tab 2: 缺陷分析 ──

    def _build_defect(self, records):
        self._clear_tab(self._defect_tab)

        c = AppStyles.COLORS

        root = QVBoxLayout(self._defect_tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # ── 缺陷类别分布柱状图 ──
        class_counter = Counter()
        for r in records:
            class_counter.update(r.get_class_distribution_dict())

        bar_group = QGroupBox('缺陷类别分布')
        bar_group.setStyleSheet(AppStyles.get_groupbox_style())
        bar_layout = QVBoxLayout(bar_group)
        bar_layout.setContentsMargins(4, 4, 4, 4)

        if class_counter:
            canvas = ChartCanvas(width=6, height=3.5)
            labels = list(class_counter.keys())
            values = list(class_counter.values())
            colors_list = ['#3B82F6', '#10B981', '#06B6D4', '#8B5CF6',
                           '#F59E0B', '#EF4444']
            bar_colors = [colors_list[i % len(colors_list)] for i in range(len(labels))]
            bars = canvas.axes.bar(labels, values, color=bar_colors)
            canvas.axes.set_ylabel('数量')
            for bar in bars:
                h = bar.get_height()
                canvas.axes.text(bar.get_x() + bar.get_width() / 2., h,
                                 f'{int(h)}', ha='center', va='bottom',
                                 fontsize=9)
            canvas.axes.set_title('各类缺陷数量', fontsize=11)
            for label in canvas.axes.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
            canvas.fig.tight_layout()
            bar_layout.addWidget(canvas)
        else:
            bar_layout.addWidget(
                AppStyles.create_empty_state('暂无数据', 'chart_placeholder'))
        root.addWidget(bar_group, 1)

        # ── 严重程度分布饼图 ──
        sev_counter = Counter()
        for r in records:
            sev_counter[_severity_of(r.total_objects)] += 1

        sev_group = QGroupBox('严重程度分布')
        sev_group.setStyleSheet(AppStyles.get_groupbox_style())
        sev_layout = QVBoxLayout(sev_group)
        sev_layout.setContentsMargins(4, 4, 4, 4)

        if sev_counter:
            canvas = ChartCanvas(width=5, height=3.5)
            sev_order = ['轻微', '中等', '严重']
            sev_colors = {'轻微': '#10B981', '中等': '#F59E0B', '严重': '#EF4444'}
            labels = [k for k in sev_order if k in sev_counter]
            values = [sev_counter[k] for k in labels]
            colors = [sev_colors[k] for k in labels]
            canvas.axes.pie(
                values, labels=labels, autopct='%1.1f%%',
                colors=colors, startangle=90,
                textprops={'fontsize': 10, 'color': '#F1F5F9'},
            )
            canvas.fig.tight_layout()
            sev_layout.addWidget(canvas)
        else:
            sev_layout.addWidget(
                AppStyles.create_empty_state('暂无数据', 'chart_placeholder'))
        root.addWidget(sev_group, 1)

    # ── Tab 3: 趋势分析 ──

    def _build_trend(self, records):
        self._clear_tab(self._trend_tab)

        c = AppStyles.COLORS
        root = QVBoxLayout(self._trend_tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # 按日期聚合
        date_det_count = Counter()   # 检测次数
        date_def_count = Counter()   # 缺陷数量
        for r in records:
            if r.timestamp:
                try:
                    day = r.timestamp.split(' ')[0]  # "YYYY-MM-DD"
                except Exception:
                    day = 'unknown'
            else:
                day = 'unknown'
            date_det_count[day] += 1
            date_def_count[day] += r.total_objects

        sorted_dates = sorted(d for d in date_det_count if d != 'unknown')
        det_values = [date_det_count[d] for d in sorted_dates]
        def_values = [date_def_count[d] for d in sorted_dates]

        # ── 检测数量折线图 ──
        line1_group = QGroupBox('每日检测数量趋势')
        line1_group.setStyleSheet(AppStyles.get_groupbox_style())
        line1_layout = QVBoxLayout(line1_group)
        line1_layout.setContentsMargins(4, 4, 4, 4)

        if sorted_dates:
            canvas1 = ChartCanvas(width=7, height=3.5)
            canvas1.axes.plot(sorted_dates, det_values, 'o-',
                              color='#3B82F6', linewidth=2, markersize=5)
            canvas1.axes.set_ylabel('检测次数')
            canvas1.axes.set_title('每日检测数量', fontsize=11)
            canvas1.axes.grid(True, alpha=0.3)
            for label in canvas1.axes.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
            canvas1.fig.tight_layout()
            line1_layout.addWidget(canvas1)
        else:
            line1_layout.addWidget(
                AppStyles.create_empty_state('暂无数据', 'chart_placeholder'))
        root.addWidget(line1_group, 1)

        # ── 缺陷数量折线图 ──
        line2_group = QGroupBox('每日缺陷数量趋势')
        line2_group.setStyleSheet(AppStyles.get_groupbox_style())
        line2_layout = QVBoxLayout(line2_group)
        line2_layout.setContentsMargins(4, 4, 4, 4)

        if sorted_dates:
            canvas2 = ChartCanvas(width=7, height=3.5)
            canvas2.axes.plot(sorted_dates, def_values, 'o-',
                              color='#EF4444', linewidth=2, markersize=5)
            canvas2.axes.set_ylabel('缺陷数量')
            canvas2.axes.set_title('每日缺陷数量', fontsize=11)
            canvas2.axes.grid(True, alpha=0.3)
            for label in canvas2.axes.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
            canvas2.fig.tight_layout()
            line2_layout.addWidget(canvas2)
        else:
            line2_layout.addWidget(
                AppStyles.create_empty_state('暂无数据', 'chart_placeholder'))
        root.addWidget(line2_group, 1)

    # ── Tab 4: 训练指标 ──

    def _build_train_tab(self):
        self._clear_tab(self._train_tab)
        c = AppStyles.COLORS
        root = QVBoxLayout(self._train_tab)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # 导入按钮行
        btn_row = QHBoxLayout()
        btn_import = QPushButton('导入训练日志 (results.csv)')
        btn_import.setFixedHeight(34)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.setFont(QFont('Microsoft YaHei', 9))
        btn_import.setStyleSheet(AppStyles.get_button_style('primary'))
        btn_import.clicked.connect(self._on_import_training_log)
        btn_row.addWidget(btn_import)
        btn_row.addStretch()

        self._train_status = QLabel('未导入训练日志')
        self._train_status.setFont(QFont('Microsoft YaHei', 9))
        self._train_status.setStyleSheet(f'color:{c["text_secondary"]};border:none;')
        btn_row.addWidget(self._train_status)
        root.addLayout(btn_row)

        # 滚动区域包裹内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')

        self._train_content_widget = QWidget()
        self._train_content = QVBoxLayout(self._train_content_widget)
        self._train_content.setContentsMargins(0, 0, 0, 0)
        self._train_content.setSpacing(12)
        self._train_content.addWidget(AppStyles.create_empty_state(
            '导入 YOLO 训练输出目录下的 results.csv 文件\n以查看训练指标曲线', 'chart_placeholder'))

        scroll.setWidget(self._train_content_widget)
        root.addWidget(scroll, 1)

        # 自动加载项目目录下的 results.csv
        auto_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'results.csv')
        if os.path.exists(auto_csv):
            try:
                import pandas as pd
                df = pd.read_csv(auto_csv)
                df.columns = [c.strip() for c in df.columns]
                if 'epoch' in df.columns:
                    self._plot_training(df)
                    self._train_status.setText('已加载: results.csv')
            except Exception:
                pass

    def _on_import_training_log(self):
        csv_path, _ = QFileDialog.getOpenFileName(
            self, '选择训练日志', '', 'CSV 文件 (*.csv);;所有文件 (*)')
        if not csv_path:
            return
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            # 去除列名空格
            df.columns = [c.strip() for c in df.columns]

            # YOLO results.csv 标准列
            required = ['epoch']
            if not all(c in df.columns for c in required):
                QMessageBox.warning(self, '格式错误', '未找到 epoch 列，请确认是 YOLO 训练日志')
                return

            self._plot_training(df)
            self._train_status.setText(f'已加载: {csv_path.split("/")[-1].split(chr(92))[-1]}')
        except Exception as e:
            QMessageBox.warning(self, '导入失败', f'无法解析文件: {e}')

    def _plot_training(self, df):
        c = AppStyles.COLORS

        # 清理旧内容
        while self._train_content.count():
            item = self._train_content.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                while item.layout().count():
                    si = item.layout().takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        epochs = df['epoch'].values

        # ── Loss 曲线 ──
        loss_group = QGroupBox('训练损失曲线')
        loss_group.setStyleSheet(AppStyles.get_groupbox_style())
        loss_lay = QVBoxLayout(loss_group)
        loss_lay.setContentsMargins(4, 4, 4, 4)

        loss_canvas = ChartCanvas(width=7, height=3.5)
        loss_cols = [c for c in ['train/box_loss', 'train/cls_loss', 'train/dfl_loss',
                                  'val/box_loss', 'val/cls_loss', 'val/dfl_loss']
                     if c in df.columns]
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
        for i, col in enumerate(loss_cols):
            label = col.replace('train/', '训练-').replace('val/', '验证-').replace('_', ' ')
            loss_canvas.axes.plot(epochs, df[col].values, label=label,
                                  color=colors[i % len(colors)], linewidth=1.5)
        if loss_cols:
            loss_canvas.axes.set_xlabel('Epoch')
            loss_canvas.axes.set_ylabel('Loss')
            loss_canvas.axes.legend(fontsize=8, loc='upper right')
            loss_canvas.axes.grid(True, alpha=0.3)
            loss_canvas.axes.set_title('Loss 曲线', fontsize=11)
            loss_canvas.fig.tight_layout()
            loss_lay.addWidget(loss_canvas)
        self._train_content.addWidget(loss_group)

        # ── mAP / Precision / Recall ──
        metric_group = QGroupBox('精度指标')
        metric_group.setStyleSheet(AppStyles.get_groupbox_style())
        metric_lay = QVBoxLayout(metric_group)
        metric_lay.setContentsMargins(4, 4, 4, 4)

        metric_canvas = ChartCanvas(width=7, height=3.5)
        metric_cols = [c for c in ['metrics/precision(B)', 'metrics/recall(B)',
                                    'metrics/mAP50(B)', 'metrics/mAP50-95(B)']
                       if c in df.columns]
        metric_labels = ['Precision', 'Recall', 'mAP@0.5', 'mAP@0.5:0.95']
        metric_colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
        for i, col in enumerate(metric_cols):
            idx = ['metrics/precision(B)', 'metrics/recall(B)',
                   'metrics/mAP50(B)', 'metrics/mAP50-95(B)'].index(col)
            metric_canvas.axes.plot(epochs, df[col].values, label=metric_labels[idx],
                                    color=metric_colors[idx], linewidth=1.5)
        if metric_cols:
            metric_canvas.axes.set_xlabel('Epoch')
            metric_canvas.axes.set_ylabel('Value')
            metric_canvas.axes.legend(fontsize=8, loc='lower right')
            metric_canvas.axes.grid(True, alpha=0.3)
            metric_canvas.axes.set_title('Precision / Recall / mAP', fontsize=11)
            metric_canvas.axes.set_ylim(0, 1.05)
            metric_canvas.fig.tight_layout()
            metric_lay.addWidget(metric_canvas)
        self._train_content.addWidget(metric_group)

        # ── 最终指标汇总 ──
        summary_group = QGroupBox('最终训练结果')
        summary_group.setStyleSheet(AppStyles.get_groupbox_style())
        summary_lay = QHBoxLayout(summary_group)
        summary_lay.setContentsMargins(12, 10, 12, 10)

        last = df.iloc[-1]
        summary_items = []
        for col, label in [('metrics/precision(B)', 'Precision'),
                           ('metrics/recall(B)', 'Recall'),
                           ('metrics/mAP50(B)', 'mAP@0.5'),
                           ('metrics/mAP50-95(B)', 'mAP@0.5:0.95')]:
            if col in df.columns:
                summary_items.append((label, f'{last[col]:.4f}'))

        accent_colors = [c['gradient_start'], c['success'], c['accent_amber'], c['error']]
        for i, (label, value) in enumerate(summary_items):
            card = AppStyles.create_stat_card(label, value, accent_colors[i % len(accent_colors)])
            summary_lay.addWidget(card['widget'])

        self._train_content.addWidget(summary_group)
        self._train_content.addStretch()
