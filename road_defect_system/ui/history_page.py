import json
import os
import re
import tempfile
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QTextBrowser,
    QMessageBox, QHeaderView, QScrollArea, QFrame, QSizePolicy,
    QFileDialog, QAbstractItemView, QDialog, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, QSizeF, QMarginsF
from PyQt6.QtGui import QFont, QPageSize, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument
from styles import AppStyles
from database.db_manager import DatabaseManager
from database.models import DetectionRecord

TYPE_MAP = {'all': '全部', 'image': '图片', 'video': '视频'}
TYPE_REVERSE = {'全部': 'all', '图片': 'image', '视频': 'video'}
TYPE_DISPLAY = {'image': '图片', 'video': '视频'}


def _md_to_html(text):
    """轻量 markdown → HTML，仅处理内联格式"""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code style="background:rgba(255,255,255,0.08);padding:1px 4px;border-radius:3px">\1</code>', text)
    text = text.replace('\n', '<br>')
    return text


class HistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager()
        self._records = []
        self._ai_lock = threading.Lock()
        self._ai_result = None
        self._ai_poll_timer = QTimer(self)
        self._ai_poll_timer.timeout.connect(self._poll_ai_result)
        self._chat_history = []
        self._chat_record = None
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._on_refresh()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._create_left_panel(), 3)
        layout.addWidget(self._create_right_panel(), 2)

    # ── 左侧 ──

    def _create_left_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        ll = QVBoxLayout(widget)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(12)

        toolbar = QWidget()
        toolbar.setStyleSheet('background: transparent;')
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(12)

        tl.addWidget(self._make_label('类型:'))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部', '图片', '视频'])
        self.type_combo.setFixedWidth(100)
        self.type_combo.setFont(QFont('Microsoft YaHei', 9))
        self.type_combo.setStyleSheet(AppStyles.get_combobox_style())
        self.type_combo.currentTextChanged.connect(self._on_search)
        tl.addWidget(self.type_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('关键词搜索...')
        self.search_input.setFixedWidth(150)
        self.search_input.setFont(QFont('Microsoft YaHei', 9))
        self.search_input.setStyleSheet(AppStyles.get_input_style())
        self.search_input.textChanged.connect(self._on_search)
        tl.addWidget(self.search_input)

        tl.addStretch()

        for text, variant, func in [
            ('刷新', 'primary', self._on_refresh),
            ('导出CSV', 'outline', self._on_export_csv),
            ('生成报告', 'success', self._on_export_pdf),
            ('对比', 'outline', self._on_compare),
            ('清空历史', 'danger', self._on_clear_all),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont('Microsoft YaHei', 9))
            btn.setStyleSheet(AppStyles.get_button_style(variant, 'small'))
            btn.clicked.connect(func)
            tl.addWidget(btn)

        ll.addWidget(toolbar)

        tg = QGroupBox('检测记录')
        tg.setStyleSheet(AppStyles.get_groupbox_style())
        tbl = QVBoxLayout(tg)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(
            ['ID', '时间', '类型', '来源', '模型', '目标数', '类别分布'])
        self.history_table.setRowCount(0)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setFont(QFont('Microsoft YaHei', 9))
        self.history_table.setStyleSheet(AppStyles.get_table_style())
        self.history_table.horizontalHeader().setStretchLastSection(True)
        for col in [0, 1, 2, 5]:
            self.history_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.clicked.connect(self._on_row_clicked)
        tbl.addWidget(self.history_table)
        ll.addWidget(tg, 1)
        return widget

    # ── 右侧（详情 + AI 助手聊天）──

    def _create_right_panel(self):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        rl = QVBoxLayout(widget)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        # 记录详情
        dg = QGroupBox('记录详情')
        dg.setStyleSheet(AppStyles.get_groupbox_style())
        dl = QVBoxLayout(dg)
        self.detail_text = QTextBrowser()
        self.detail_text.setFont(QFont('Microsoft YaHei', 9))
        self.detail_text.setHtml(f'''
            <div style='color: {c["text_secondary"]}; font-size: 9pt; text-align: center; padding: 40px;'>
                点击左侧记录查看详情
            </div>''')
        self.detail_text.setStyleSheet(f'''
            QTextBrowser {{
                background-color: {c["background_elevated"]};
                border: 1px solid {c["border"]};
                border-radius: {AppStyles.BORDER_RADIUS["small"]}px;
                color: {c["text_secondary"]};
            }}''')
        dl.addWidget(self.detail_text)
        btn_del = QPushButton('删除此记录')
        btn_del.setFixedHeight(28)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setFont(QFont('Microsoft YaHei', 8))
        btn_del.setStyleSheet(AppStyles.get_button_style('danger', 'small'))
        btn_del.clicked.connect(self._on_delete_record)
        dl.addWidget(btn_del)
        rl.addWidget(dg, 3)

        # ── AI 助手聊天面板 ──
        ag = QGroupBox('AI 助手')
        ag.setStyleSheet(f'''
            QGroupBox {{
                font-family: "Microsoft YaHei";
                font-size: 10pt; font-weight: bold;
                color: {c["gradient_start"]};
                border: 1px solid {c["border_focus"]};
                border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
                margin-top: 10px; padding: 10px; padding-top: 22px;
                background-color: {c["background_card"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }}''')
        al = QVBoxLayout(ag)
        al.setSpacing(6)
        al.setContentsMargins(8, 8, 8, 8)

        # 顶部行：模型 + 设置
        top = QHBoxLayout()
        self.ai_model_label = QLabel('模型: --')
        self.ai_model_label.setFont(QFont('Microsoft YaHei', 8))
        self.ai_model_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        top.addWidget(self.ai_model_label)
        top.addStretch()
        sbtn = QPushButton('设置')
        sbtn.setFixedHeight(28)
        sbtn.setMinimumWidth(48)
        sbtn.setFont(QFont('Microsoft YaHei', 8))
        sbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        sbtn.setStyleSheet(AppStyles.get_button_style('ghost', 'small'))
        sbtn.clicked.connect(self._on_ai_settings)
        top.addWidget(sbtn)
        al.addLayout(top)

        # 消息区
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setMinimumHeight(160)
        self.chat_scroll.setStyleSheet(f'''
            QScrollArea {{
                background-color: {c["background_main"]};
                border: 1px solid {c["border"]};
                border-radius: 6px;
            }}''')
        self.chat_scroll.verticalScrollBar().setStyleSheet('''
            QScrollBar:vertical {
                background: transparent; width: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.4); border-radius: 3px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.65);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }''')
        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(6, 6, 6, 6)
        self._chat_layout.setSpacing(4)
        self._chat_layout.addStretch()
        self.chat_scroll.setWidget(self._chat_container)
        al.addWidget(self.chat_scroll)

        # 分析按钮（独立行，主要 CTA）
        self.analyze_btn = QPushButton('分析记录')
        self.analyze_btn.setFont(QFont('Microsoft YaHei', 9))
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setStyleSheet(AppStyles.get_button_style('primary'))
        self.analyze_btn.clicked.connect(self._on_ai_analyze)
        al.addWidget(self.analyze_btn)

        # 输入行
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText('输入追问，回车发送...')
        self.chat_input.setFont(QFont('Microsoft YaHei', 9))
        self.chat_input.setStyleSheet(AppStyles.get_input_style())
        self.chat_input.returnPressed.connect(self._on_send_chat)
        input_row.addWidget(self.chat_input)

        self.send_btn = QPushButton('发送')
        self.send_btn.setMinimumWidth(56)
        self.send_btn.setFont(QFont('Microsoft YaHei', 9))
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(AppStyles.get_button_style('success'))
        self.send_btn.clicked.connect(self._on_send_chat)
        input_row.addWidget(self.send_btn)

        al.addLayout(input_row)
        rl.addWidget(ag, 2)

        self._refresh_model_label()
        return widget

    # ── 辅助 ──

    def _make_label(self, text):
        c = AppStyles.COLORS
        lbl = QLabel(text)
        lbl.setFont(QFont('Microsoft YaHei', 9))
        lbl.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        return lbl

    def _refresh_model_label(self):
        from core.ai_analyzer import load_config
        cfg = load_config()
        m = cfg.get('model', '未配置')
        if '/' in m:
            m = m.split('/')[-1]
        self.ai_model_label.setText(f'模型: {m}')

    # ── 聊天气泡 ──

    def _add_chat_bubble(self, text, role='assistant'):
        """添加聊天气泡，role='assistant' 或 'user'"""
        c = AppStyles.COLORS
        # 移除末尾的 stretch
        item = self._chat_layout.takeAt(self._chat_layout.count() - 1)

        bubble = QLabel(_md_to_html(text))
        bubble.setWordWrap(True)
        bubble.setTextFormat(Qt.TextFormat.RichText)
        bubble.setFont(QFont('Microsoft YaHei', 9))
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if role == 'assistant':
            bubble.setStyleSheet(f'''
                background-color: {c["background_elevated"]};
                color: {c["text_primary"]};
                border: none; border-radius: 8px;
                padding: 6px 10px;
            ''')
            row = QHBoxLayout()
            lbl = QLabel('AI')
            lbl.setFixedSize(24, 24)
            lbl.setFont(QFont('Microsoft YaHei', 7, QFont.Weight.Bold))
            lbl.setStyleSheet(f'''
                background-color: {c["gradient_start"]}; color: white;
                border-radius: 12px; border: none;
            ''')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(lbl)
            row.addWidget(bubble, 1)
            self._chat_layout.addLayout(row)
        else:
            bubble.setAlignment(Qt.AlignmentFlag.AlignRight)
            bubble.setStyleSheet(f'''
                background-color: {c["gradient_start"]};
                color: white;
                border: none; border-radius: 8px;
                padding: 6px 10px;
            ''')
            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(bubble)
            self._chat_layout.addLayout(row)

        self._chat_layout.addStretch()

        # 滚动到底部
        sb = self.chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── 表格数据 ──

    def _load_records(self, records):
        self._records = records
        self.history_table.setRowCount(len(records))
        for row, r in enumerate(records):
            for col, val in enumerate([
                str(r.id), r.timestamp or '--',
                TYPE_DISPLAY.get(r.type, r.type),
                r.source or '--', r.model_name or '--',
                str(r.total_objects), r.class_distribution or '--',
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.history_table.setItem(row, col, item)

    def _on_search(self):
        kw = self.search_input.text().strip()
        tt = self.type_combo.currentText()
        self._load_records(self._db.search_records(keyword=kw, record_type=TYPE_REVERSE.get(tt, 'all')))

    def _on_refresh(self):
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self._load_records(self._db.get_all_records())
        self._refresh_model_label()

    def _on_row_clicked(self, index):
        row = index.row()
        if row >= len(self._records):
            return
        r = self._records[row]
        c = AppStyles.COLORS
        td = TYPE_DISPLAY.get(r.type, r.type)

        dh = ''
        dl = r.get_details_list()
        if dl:
            dh = '<table style="width:100%;border-collapse:collapse;">'
            dh += f'<tr style="border-bottom:1px solid {c["border"]};"><th style="text-align:left;padding:4px;color:{c["text_secondary"]};">类别</th><th style="text-align:left;padding:4px;color:{c["text_secondary"]};">置信度</th><th style="text-align:left;padding:4px;color:{c["text_secondary"]};">坐标</th></tr>'
            for d in dl:
                bb = d.get('bbox', [])
                bs = f'({bb[0]:.0f},{bb[1]:.0f},{bb[2]:.0f},{bb[3]:.0f})' if len(bb) == 4 else '--'
                dh += f'<tr style="border-bottom:1px solid {c["border"]};"><td style="padding:3px;color:{c["text_primary"]};">{d.get("class","--")}</td><td style="padding:3px;color:{c["success"]};">{d.get("confidence",0):.3f}</td><td style="padding:3px;color:{c["text_primary"]};font-size:8pt;">{bs}</td></tr>'
            dh += '</table>'

        gps_html = ''
        if r.latitude is not None and r.longitude is not None:
            gps_html = f'<p><b style="color:{c["text_primary"]};">GPS:</b> <span style="color:{c["accent_cyan"]};">{r.latitude:.6f}, {r.longitude:.6f}</span></p>'

        # 严重程度
        from utils.image_utils import get_severity
        sev_text, sev_color = get_severity(r.total_objects)
        severity_html = f'<p><b style="color:{c["text_primary"]};">严重程度:</b> <span style="color:{sev_color};font-weight:bold;">{sev_text}</span></p>'

        # 标注图片
        import os
        img_html = ''
        if r.image_path and os.path.isfile(r.image_path):
            img_w = max(self.detail_text.viewport().width() - 30, 200)
            src = 'file:///' + r.image_path.replace('\\', '/')
            img_html = (f'<div style="text-align:center;margin:8px 0;">'
                        f'<p><b style="color:{c["text_primary"]};">标注图像</b></p>'
                        f'<img src="{src}" width="{img_w}" '
                        f'style="border:1px solid {c["border"]};border-radius:4px;" />'
                        f'</div>')
        else:
            img_html = f'<p style="color:{c["text_disabled"]};font-style:italic;">无标注图像</p>'

        self.detail_text.setHtml(f'''<div style="color:{c["text_secondary"]};font-size:9pt;padding:8px;">
            <p><b style="color:{c["text_primary"]};">ID:</b> {r.id}</p>
            <p><b style="color:{c["text_primary"]};">时间:</b> {r.timestamp or "--"}</p>
            <p><b style="color:{c["text_primary"]};">类型:</b> <span style="color:#8B5CF6;">{td}检测</span></p>
            <p><b style="color:{c["text_primary"]};">来源:</b> {r.source or "--"}</p>
            <p><b style="color:{c["text_primary"]};">模型:</b> {r.model_name or "--"}</p>
            <p><b style="color:{c["text_primary"]};">检测数:</b> <span style="color:{c["success"]};font-weight:bold;">{r.total_objects}</span></p>
            {severity_html}
            <p><b style="color:{c["text_primary"]};">类别分布:</b> {r.class_distribution or "--"}</p>
            {gps_html}
            {img_html}
            <hr style="border:1px solid {c["border"]};">{dh}</div>''')

    def _on_delete_record(self):
        sel = self.history_table.selectedItems()
        if not sel:
            QMessageBox.information(self, '提示', '请先选择一条记录')
            return
        row = sel[0].row()
        if row >= len(self._records):
            return
        rec = self._records[row]
        if QMessageBox.question(self, '确认删除', f'确定要删除记录 #{rec.id} 吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            # 清理标注图片
            if rec.image_path:
                import os
                try:
                    if os.path.isfile(rec.image_path):
                        os.remove(rec.image_path)
                except OSError:
                    pass
            self._db.delete_record(rec.id)
            self._on_refresh()

    def _on_export_csv(self):
        if not self._records:
            QMessageBox.information(self, '提示', '没有可导出的记录')
            return
        from utils.file_utils import save_file_dialog
        p = save_file_dialog(self, '导出CSV', 'detection_history.csv', 'CSV文件 (*.csv)')
        if not p:
            return
        try:
            self._db.export_to_csv(self._records, p)
            QMessageBox.information(self, '成功', f'已导出到:\n{p}')
        except Exception as e:
            QMessageBox.warning(self, '失败', f'导出失败: {e}')


    def _on_clear_all(self):
        cnt = self._db.get_records_count()
        if cnt == 0:
            QMessageBox.information(self, '提示', '暂无记录')
            return
        if QMessageBox.question(self, '确认清空', f'确定要清空所有 {cnt} 条记录吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            self._db.clear_all_records()
            self._on_refresh()

    def _on_export_pdf(self):
        """将选中记录导出为 PDF 巡检报告"""
        sel = self.history_table.selectedItems()
        if not sel:
            QMessageBox.information(self, '提示', '请先选择一条检测记录')
            return
        row = sel[0].row()
        if row >= len(self._records):
            return
        r = self._records[row]

        from utils.file_utils import save_file_dialog
        default_name = f'巡检报告_#{r.id}.pdf'
        pdf_path = save_file_dialog(self, '保存PDF报告', default_name, 'PDF文件 (*.pdf)')
        if not pdf_path:
            return

        from utils.image_utils import get_severity
        td = TYPE_DISPLAY.get(r.type, r.type)
        sev_text, sev_color = get_severity(r.total_objects)

        # 构建 HTML 报告
        img_html = ''
        if r.image_path and os.path.isfile(r.image_path):
            src = 'file:///' + r.image_path.replace('\\', '/')
            img_html = (f'<div style="text-align:center;margin:12px 0;">'
                        f'<img src="{src}" width="520" '
                        f'style="border:1px solid #ccc;border-radius:4px;" />'
                        f'<p style="color:#666;font-size:9pt;">标注图像</p></div>')

        gps_html = ''
        if r.latitude is not None and r.longitude is not None:
            gps_html = (f'<tr><td style="padding:6px 12px;color:#666;">GPS 坐标</td>'
                        f'<td style="padding:6px 12px;">{r.latitude:.6f}, {r.longitude:.6f}</td></tr>')

        # 检测详情表
        detail_rows = ''
        for d in r.get_details_list():
            bb = d.get('bbox', [])
            bs = f'({bb[0]:.0f},{bb[1]:.0f},{bb[2]:.0f},{bb[3]:.0f})' if len(bb) == 4 else '--'
            detail_rows += (f'<tr><td style="padding:4px 10px;border-bottom:1px solid #eee;">'
                            f'{d.get("class","--")}</td>'
                            f'<td style="padding:4px 10px;border-bottom:1px solid #eee;">'
                            f'{d.get("confidence",0):.3f}</td>'
                            f'<td style="padding:4px 10px;border-bottom:1px solid #eee;">'
                            f'{bs}</td></tr>')

        detail_table = ''
        if detail_rows:
            detail_table = (f'<table style="width:100%;border-collapse:collapse;margin-top:10px;">'
                            f'<tr style="background:#f0f0f0;"><th style="padding:6px 10px;text-align:left;">缺陷类型</th>'
                            f'<th style="padding:6px 10px;text-align:left;">置信度</th>'
                            f'<th style="padding:6px 10px;text-align:left;">坐标</th></tr>'
                            f'{detail_rows}</table>')

        report_html = f'''
        <html><head><style>
            body {{ font-family: "Microsoft YaHei", "SimHei", sans-serif; color: #333; margin: 40px; }}
            h1 {{ color: #1a56db; font-size: 20pt; border-bottom: 3px solid #1a56db; padding-bottom: 8px; }}
            h2 {{ color: #333; font-size: 13pt; margin-top: 24px; }}
            .meta {{ background: #f8f9fa; border-radius: 6px; padding: 12px 16px; margin: 12px 0; }}
            .sev {{ display: inline-block; padding: 3px 12px; border-radius: 12px; color: white; font-weight: bold; font-size: 10pt; }}
        </style></head><body>
        <h1>道路缺陷巡检报告</h1>
        <div class="meta">
            <table style="width:100%;">
                <tr><td style="padding:6px 12px;color:#666;width:120px;">报告编号</td>
                    <td style="padding:6px 12px;">RPT-{r.id:04d}</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">检测时间</td>
                    <td style="padding:6px 12px;">{r.timestamp or "--"}</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">检测类型</td>
                    <td style="padding:6px 12px;">{td}检测</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">来源</td>
                    <td style="padding:6px 12px;">{r.source or "--"}</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">检测模型</td>
                    <td style="padding:6px 12px;">{r.model_name or "--"}</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">缺陷数量</td>
                    <td style="padding:6px 12px;"><b>{r.total_objects}</b> 个</td></tr>
                <tr><td style="padding:6px 12px;color:#666;">严重程度</td>
                    <td style="padding:6px 12px;"><span class="sev" style="background:{sev_color};">{sev_text}</span></td></tr>
                <tr><td style="padding:6px 12px;color:#666;">类别分布</td>
                    <td style="padding:6px 12px;">{r.class_distribution or "--"}</td></tr>
                {gps_html}
            </table>
        </div>
        {img_html}
        <h2>检测详情</h2>
        {detail_table}
        <div style="margin-top:40px;padding-top:12px;border-top:1px solid #ddd;color:#999;font-size:8pt;text-align:center;">
            本报告由「路巡者」道路缺陷智能检测系统自动生成 &mdash; {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        </body></html>'''

        try:
            doc = QTextDocument()
            doc.setHtml(report_html)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(pdf_path)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)
            doc.print(printer)
            QMessageBox.information(self, '成功', f'报告已保存到:\n{pdf_path}')
        except Exception as e:
            QMessageBox.warning(self, '失败', f'生成PDF失败: {e}')

    def _on_compare(self):
        """对比两条检测记录"""
        rows = self.history_table.selectionModel().selectedRows()
        if len(rows) != 2:
            QMessageBox.information(
                self, '提示',
                '请在表格中选择两条记录进行对比（按住Ctrl多选）')
            return
        row_indices = sorted([r.row() for r in rows])
        if any(ri >= len(self._records) for ri in row_indices):
            return
        r1 = self._records[row_indices[0]]
        r2 = self._records[row_indices[1]]
        dlg = _CompareDialog(r1, r2, self)
        dlg.exec()

    # ── AI 聊天 ──

    def _on_ai_settings(self):
        from ui.ai_config_dialog import AIConfigDialog
        dlg = AIConfigDialog(self)
        dlg.exec()
        self._refresh_model_label()

    def _on_ai_analyze(self):
        sel = self.history_table.selectedItems()
        if not sel:
            QMessageBox.information(self, '提示', '请先选择一条检测记录')
            return
        row = sel[0].row()
        if row >= len(self._records):
            return

        from core.ai_analyzer import load_config
        cfg = load_config()
        if not cfg.get('api_key'):
            if QMessageBox.question(self, '未配置', '需要配置 API Key，是否现在设置？',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    ) == QMessageBox.StandardButton.Yes:
                self._on_ai_settings()
            return

        self._chat_record = self._records[row]
        self._chat_history = []
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText('分析中...')
        self._ai_result = None

        # 显示用户消息
        self._add_chat_bubble('请分析这条检测记录', 'user')

        # 显示加载中
        self._add_chat_bubble('正在分析...', 'assistant')

        def run():
            from core.ai_analyzer import analyze
            try:
                r = analyze(self._chat_record)
                with self._ai_lock:
                    self._ai_result = r
            except Exception as e:
                with self._ai_lock:
                    self._ai_result = {'error': str(e)}

        threading.Thread(target=run, daemon=True).start()
        self._ai_poll_timer.start(500)

    def _on_send_chat(self):
        text = self.chat_input.text().strip()
        if not text:
            return
        if self._chat_record is None:
            QMessageBox.information(self, '提示', '请先分析一条记录')
            return

        self._add_chat_bubble(text, 'user')
        self._chat_history.append({'role': 'user', 'content': text})
        self.chat_input.clear()
        self.send_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self._ai_result = None

        self._add_chat_bubble('思考中...', 'assistant')

        def run():
            from core.ai_analyzer import chat
            try:
                r = chat(self._chat_record, list(self._chat_history))
                with self._ai_lock:
                    self._ai_result = r
            except Exception as e:
                with self._ai_lock:
                    self._ai_result = {'error': str(e)}

        threading.Thread(target=run, daemon=True).start()
        self._ai_poll_timer.start(500)

    def _poll_ai_result(self):
        with self._ai_lock:
            if self._ai_result is None:
                return
            result = self._ai_result
            self._ai_result = None
        self._ai_poll_timer.stop()
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText('分析记录')
        self.send_btn.setEnabled(True)

        # 移除最后的 "正在分析..." / "思考中..." 占位气泡
        self._remove_last_assistant_bubble()

        if 'error' in result:
            self._add_chat_bubble(f'[错误] {result["error"]}', 'assistant')
            return

        # 首次分析（结构化结果）
        if 'rating' in result:
            rating = result.get('rating', '--')
            urgency = result.get('urgency', '--')
            analysis = result.get('analysis', '--')
            suggestions = result.get('suggestions', [])
            sug_text = '\n'.join(f'{i}. {s}' for i, s in enumerate(suggestions, 1))
            reply = f'评级: {rating}  |  紧急: {urgency}\n\n{analysis}\n\n修复建议:\n{sug_text}'
            self._chat_history.append({'role': 'assistant', 'content': reply})
            self._add_chat_bubble(reply, 'assistant')
        else:
            # 追问回复（纯文本）
            content = result.get('content', '--')
            self._chat_history.append({'role': 'assistant', 'content': content})
            self._add_chat_bubble(content, 'assistant')

    def _remove_last_assistant_bubble(self):
        """移除最后一条 AI 气泡（加载占位）"""
        count = self._chat_layout.count()
        if count < 2:
            return
        # 最后一个是 stretch, 倒数第二个是 AI 气泡的 layout
        stretch_item = self._chat_layout.takeAt(count - 1)
        bubble_layout = self._chat_layout.takeAt(count - 2)
        # 清理 widgets
        if bubble_layout.layout():
            while bubble_layout.layout().count():
                item = bubble_layout.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        si = item.layout().takeAt(0)
                        if si.widget():
                            si.widget().deleteLater()
        # 重新添加 stretch
        self._chat_layout.addStretch()


# ── 对比对话框 ──────────────────────────────────────────────────────

class _CompareDialog(QDialog):
    """两条检测记录的对比窗口"""

    def __init__(self, r1: DetectionRecord, r2: DetectionRecord, parent=None):
        super().__init__(parent)
        self.setWindowTitle('检测结果对比')
        self.setMinimumSize(700, 500)
        self._init_ui(r1, r2)

    def _init_ui(self, r1, r2):
        c = AppStyles.COLORS
        self.setStyleSheet(f'''
            QDialog {{
                background-color: {c['background_main']};
            }}
            QLabel {{
                color: {c['text_primary']};
                border: none;
            }}
        ''')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel('检测结果对比')
        title.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        title.setStyleSheet(
            f'color: {c["gradient_start"]}; border: none;')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 对比表格
        from utils.image_utils import get_severity
        sev1_text, sev1_color = get_severity(r1.total_objects)
        sev2_text, sev2_color = get_severity(r2.total_objects)

        dist1 = r1.get_class_distribution_dict()
        dist2 = r2.get_class_distribution_dict()
        dist1_str = ', '.join(f'{k}:{v}' for k, v in dist1.items()) if dist1 else '--'
        dist2_str = ', '.join(f'{k}:{v}' for k, v in dist2.items()) if dist2 else '--'

        type_display = {'image': '图片', 'video': '视频'}

        compare_items = [
            ('时间', r1.timestamp or '--', r2.timestamp or '--', None),
            ('类型', type_display.get(r1.type, r1.type), type_display.get(r2.type, r2.type), None),
            ('来源', r1.source or '--', r2.source or '--', None),
            ('缺陷数量', str(r1.total_objects), str(r2.total_objects), 'total_objects'),
            ('严重程度', sev1_text, sev2_text, 'severity'),
            ('类别分布', dist1_str, dist2_str, None),
        ]

        # 使用 QGridLayout 构建对比表
        grid = QGridLayout()
        grid.setSpacing(0)

        # 表头
        header_style = f'''
            background-color: {c['background_secondary']};
            color: {c['text_secondary']};
            padding: 10px; font-weight: bold; border: none;
            border-bottom: 1px solid {c['border_light']};
        '''
        for col, text in enumerate(['对比项', '记录 A', '记录 B']):
            lbl = QLabel(text)
            lbl.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
            lbl.setStyleSheet(header_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, 0, col)

        # 数据行
        cell_style = f'''
            background-color: {c['background_elevated']};
            color: {c['text_primary']};
            padding: 10px; border: none;
            border-bottom: 1px solid {c['border']};
        '''
        label_style = f'''
            background-color: {c['background_card']};
            color: {c['text_secondary']};
            padding: 10px; border: none;
            border-bottom: 1px solid {c['border']};
        '''

        for row, (label, val1, val2, diff_key) in enumerate(compare_items, 1):
            # 对比项名称
            lbl = QLabel(label)
            lbl.setFont(QFont('Microsoft YaHei', 9))
            lbl.setStyleSheet(label_style)
            grid.addWidget(lbl, row, 0)

            # 记录 A 值
            v1_lbl = QLabel(str(val1))
            v1_lbl.setFont(QFont('Microsoft YaHei', 9))
            v1_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v1_cell_style = cell_style
            if diff_key == 'severity':
                v1_cell_style = cell_style + f'color: {sev1_color}; font-weight: bold;'
            v1_lbl.setStyleSheet(v1_cell_style)
            grid.addWidget(v1_lbl, row, 1)

            # 记录 B 值
            v2_lbl = QLabel(str(val2))
            v2_lbl.setFont(QFont('Microsoft YaHei', 9))
            v2_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v2_cell_style = cell_style
            if diff_key == 'severity':
                v2_cell_style = cell_style + f'color: {sev2_color}; font-weight: bold;'
            v2_lbl.setStyleSheet(v2_cell_style)
            grid.addWidget(v2_lbl, row, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)

        layout.addLayout(grid)

        # 变化趋势区域
        trend_group = QGroupBox('变化趋势')
        trend_group.setStyleSheet(AppStyles.get_groupbox_style())
        trend_layout = QVBoxLayout(trend_group)
        trend_layout.setSpacing(6)

        diff = r2.total_objects - r1.total_objects
        if diff > 0:
            trend_text = f'缺陷数量: +{diff} (增多)'
            trend_color = '#EF4444'
            arrow = '(+)'
        elif diff < 0:
            trend_text = f'缺陷数量: {diff} (减少)'
            trend_color = '#10B981'
            arrow = '(-)'
        else:
            trend_text = '缺陷数量: 无变化'
            trend_color = '#8B9AB5'
            arrow = '(=)'

        trend_label = QLabel(trend_text)
        trend_label.setFont(QFont('Microsoft YaHei', 11, QFont.Weight.Bold))
        trend_label.setStyleSheet(f'color: {trend_color}; border: none;')
        trend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_layout.addWidget(trend_label)

        # 严重程度变化
        sev_levels = {'轻微': 1, '中等': 2, '严重': 3}
        sev_diff = sev_levels.get(sev2_text, 0) - sev_levels.get(sev1_text, 0)
        if sev_diff > 0:
            sev_trend = f'严重程度: 加重 ({sev1_text} -> {sev2_text})'
            sev_trend_color = '#EF4444'
        elif sev_diff < 0:
            sev_trend = f'严重程度: 减轻 ({sev1_text} -> {sev2_text})'
            sev_trend_color = '#10B981'
        else:
            sev_trend = f'严重程度: 不变 ({sev1_text})'
            sev_trend_color = '#8B9AB5'

        sev_label = QLabel(sev_trend)
        sev_label.setFont(QFont('Microsoft YaHei', 10))
        sev_label.setStyleSheet(f'color: {sev_trend_color}; border: none;')
        sev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_layout.addWidget(sev_label)

        layout.addWidget(trend_group)

        # 关闭按钮
        close_btn = QPushButton('关闭')
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFont(QFont('Microsoft YaHei', 10))
        close_btn.setStyleSheet(AppStyles.get_button_style('outline'))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
