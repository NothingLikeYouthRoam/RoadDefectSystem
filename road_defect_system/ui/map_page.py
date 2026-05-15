"""缺陷地图页面 — Folium + QWebEngineView（按文档方案实现）"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QEvent, QUrl, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from styles import AppStyles
from utils.image_utils import get_severity

import folium
import io
import os
import tempfile
from folium.plugins import MarkerCluster, HeatMap

TYPE_DISPLAY = {'image': '图片', 'video': '视频'}

# 地图 HTML 临时文件路径（固定，避免重复生成）
_MAP_HTML = os.path.join(tempfile.gettempdir(), 'road_defect_map.html')


# ── 统计卡片 ──────────────────────────────────────────

class _StatCard(QFrame):
    def __init__(self, title, value, accent, parent=None):
        super().__init__(parent)
        c = AppStyles.COLORS
        self.setFixedHeight(68)
        self.setStyleSheet(f"""
            QFrame {{
                background: {c['background_card']};
                border: 1px solid {c['border']};
                border-left: 3px solid {accent};
                border-radius: {AppStyles.BORDER_RADIUS['card']}px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        t = QLabel(title)
        t.setFont(QFont('Microsoft YaHei', 8))
        t.setStyleSheet(
            f"color:{c['text_secondary']};border:none;background:transparent;")
        lay.addWidget(t)
        self._v = QLabel(value)
        self._v.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        self._v.setStyleSheet(
            f"color:{accent};border:none;background:transparent;")
        lay.addWidget(self._v)

    def set_value(self, text):
        self._v.setText(text)


# ── 地图页面 ──────────────────────────────────────────

class MapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._records = []
        self._show_route = True
        self._show_heatmap = False
        self._first_load = True
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        # 延迟刷新，等布局完成后再设置 overlay 几何和加载地图
        QTimer.singleShot(0, self._refresh_map)

    def eventFilter(self, obj, event):
        if obj is self._web and event.type() == QEvent.Type.Resize:
            self._overlay.setGeometry(self._web.rect())
        return super().eventFilter(obj, event)

    def _on_map_loaded(self, ok):
        if self._first_load:
            self._first_load = False
            self._overlay.hide()

    # ── UI ──────────────────────────────────────────────

    def _init_ui(self):
        c = AppStyles.COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet(AppStyles.get_panel_style())
        toolbar.setFixedHeight(48)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(16, 6, 16, 6)

        title = QLabel('缺陷地图')
        title.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{c['text_primary']};border:none;")
        tl.addWidget(title)

        self.count_label = QLabel('标注数: 0')
        self.count_label.setFont(QFont('Microsoft YaHei', 9))
        self.count_label.setStyleSheet(
            f"color:{c['text_secondary']};border:none;")
        tl.addWidget(self.count_label)

        self.stats_label = QLabel('')
        self.stats_label.setFont(QFont('Microsoft YaHei', 9))
        self.stats_label.setStyleSheet(
            f"color:{c['text_secondary']};border:none;")
        tl.addWidget(self.stats_label)
        tl.addStretch()

        self.btn_route = QPushButton('巡检路线')
        self.btn_route.setCheckable(True)
        self.btn_route.setChecked(True)
        self.btn_route.setFixedHeight(30)
        self.btn_route.setFont(QFont('Microsoft YaHei', 8))
        self.btn_route.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_route.setStyleSheet(self._toggle_style(c['accent_cyan']))
        self.btn_route.clicked.connect(self._on_toggle_route)
        tl.addWidget(self.btn_route)

        self.btn_heat = QPushButton('热力图')
        self.btn_heat.setCheckable(True)
        self.btn_heat.setChecked(False)
        self.btn_heat.setFixedHeight(30)
        self.btn_heat.setFont(QFont('Microsoft YaHei', 8))
        self.btn_heat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_heat.setStyleSheet(self._toggle_style(c['accent_purple']))
        self.btn_heat.clicked.connect(self._on_toggle_heat)
        tl.addWidget(self.btn_heat)

        btn_refresh = QPushButton('刷新地图')
        btn_refresh.setFixedHeight(30)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFont(QFont('Microsoft YaHei', 8))
        btn_refresh.setStyleSheet(
            AppStyles.get_button_style('primary', 'small'))
        btn_refresh.clicked.connect(self._refresh_map)
        tl.addWidget(btn_refresh)

        layout.addWidget(toolbar)

        # 主体：左面板 + 地图 + 右面板
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._left_panel = self._build_left_panel()
        self._left_panel.setFixedWidth(200)
        body.addWidget(self._left_panel)

        # QWebEngineView 地图
        self._web = QWebEngineView()
        self._web.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._web.setStyleSheet(f"""
            QWebEngineView {{
                background-color: {c['background_main']};
                border: none;
            }}
        """)
        # 深色遮罩：盖住白闪
        self._overlay = QLabel(self._web)
        self._overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay.setStyleSheet(f"""
            background-color: {c['background_main']};
            color: {c['text_secondary']};
            font-family: 'Microsoft YaHei', sans-serif;
            font-size: 14px;
        """)
        self._overlay.setText('地图加载中...')
        self._web.installEventFilter(self)
        self._web.loadFinished.connect(self._on_map_loaded)
        # 设置 WebView 页面底色为深色，避免白闪
        self._web.page().setBackgroundColor(QColor(12, 16, 23))
        # 预加载深色页面，提前初始化 Chromium 渲染管线，避免首次显示白闪
        self._web.setHtml(
            '<html><body style="background:#0C1017;margin:0"></body></html>')
        body.addWidget(self._web, 1)

        self._right_panel = self._build_right_panel()
        self._right_panel.setFixedWidth(200)
        body.addWidget(self._right_panel)

        layout.addLayout(body, 1)

    def _build_left_panel(self):
        c = AppStyles.COLORS
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background: {c['background_secondary']};
                border-right: 1px solid {c['border']};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(8)

        hdr = QLabel('检测统计')
        hdr.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        hdr.setStyleSheet(
            f"color:{c['text_primary']};border:none;background:transparent;")
        lay.addWidget(hdr)

        self.card_total = _StatCard('总检测数', '0', c['info'])
        lay.addWidget(self.card_total)
        self.card_severe = _StatCard('严重缺陷', '0', c['error'])
        lay.addWidget(self.card_severe)
        self.card_moderate = _StatCard('中等缺陷', '0', c['warning'])
        lay.addWidget(self.card_moderate)
        self.card_minor = _StatCard('轻微缺陷', '0', c['success'])
        lay.addWidget(self.card_minor)
        self.card_gps = _StatCard('GPS 标注', '0', c['accent_cyan'])
        lay.addWidget(self.card_gps)

        lay.addStretch()
        return panel

    def _build_right_panel(self):
        c = AppStyles.COLORS
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background: {c['background_secondary']};
                border-left: 1px solid {c['border']};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(6)

        hdr = QLabel('缺陷类型分布')
        hdr.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        hdr.setStyleSheet(
            f"color:{c['text_primary']};border:none;background:transparent;")
        lay.addWidget(hdr)

        self._type_layout = QVBoxLayout()
        self._type_layout.setSpacing(4)
        lay.addLayout(self._type_layout)

        lay.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{c['border']};border:none;")
        lay.addWidget(sep)

        src_hdr = QLabel('来源分布')
        src_hdr.setFont(QFont('Microsoft YaHei', 9, QFont.Weight.Bold))
        src_hdr.setStyleSheet(
            f"color:{c['text_secondary']};border:none;background:transparent;")
        lay.addWidget(src_hdr)

        self._source_layout = QVBoxLayout()
        self._source_layout.setSpacing(4)
        lay.addLayout(self._source_layout)

        lay.addStretch()
        return panel

    # ── 辅助 ──

    @staticmethod
    def _toggle_style(accent):
        c = AppStyles.COLORS
        return f"""
            QPushButton {{
                background: {c['background_card']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: {AppStyles.BORDER_RADIUS['button']}px;
                padding: 4px 12px;
            }}
            QPushButton:checked {{
                background: {c['background_elevated']};
                color: {accent};
                border: 1px solid {accent};
            }}
            QPushButton:hover {{
                background: {c['background_hover']};
            }}
        """

    @staticmethod
    def _bar_html(label, count, total, color):
        c = AppStyles.COLORS
        pct = (count / total * 100) if total > 0 else 0
        return (
            f'<div style="margin-bottom:4px">'
            f'<span style="color:{c["text_secondary"]};font-size:11px">'
            f'{label}</span>'
            f'<span style="color:{c["text_primary"]};font-size:11px;'
            f'float:right">{count}</span>'
            f'<div style="background:{c["background_hover"]};'
            f'border-radius:3px;height:5px;margin-top:2px">'
            f'<div style="background:{color};border-radius:3px;'
            f'height:5px;width:{pct:.1f}%"></div>'
            f'</div></div>'
        )

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # ── 切换 ──

    def _on_toggle_route(self):
        self._show_route = self.btn_route.isChecked()
        self._render_map()

    def _on_toggle_heat(self):
        self._show_heatmap = self.btn_heat.isChecked()
        self._render_map()

    # ── 数据刷新 ──

    def _refresh_map(self):
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        self._records = db.get_records_with_gps()
        self._update_panels()
        if not self._records:
            self._show_empty()
            return
        self._render_map()

    def _update_panels(self):
        records = self._records
        c = AppStyles.COLORS

        self.count_label.setText(f'标注数: {len(records)}')

        severe = moderate = minor = 0
        for r in records:
            sev, _ = get_severity(r.total_objects)
            if sev == '严重':
                severe += 1
            elif sev == '中等':
                moderate += 1
            else:
                minor += 1

        self.card_total.set_value(str(len(records)))
        self.card_severe.set_value(str(severe))
        self.card_moderate.set_value(str(moderate))
        self.card_minor.set_value(str(minor))
        self.card_gps.set_value(str(len(records)))
        self.stats_label.setText(
            f'严重:{severe}  中等:{moderate}  轻微:{minor}')

        # 右侧：缺陷类型分布
        self._clear_layout(self._type_layout)
        class_counts = {}
        for r in records:
            for cls, cnt in r.get_class_distribution_dict().items():
                class_counts[cls] = class_counts.get(cls, 0) + cnt
        total_cls = sum(class_counts.values()) or 1
        palette = ['#3B82F6', '#06B6D4', '#8B5CF6', '#F59E0B',
                    '#10B981', '#EF4444', '#EC4899', '#6366F1', '#14B8A6']
        for i, (cls, cnt) in enumerate(
                sorted(class_counts.items(), key=lambda x: -x[1])):
            lbl = QLabel(
                self._bar_html(cls, cnt, total_cls, palette[i % len(palette)]))
            lbl.setStyleSheet("border:none;background:transparent;")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            self._type_layout.addWidget(lbl)

        # 右侧：来源分布
        self._clear_layout(self._source_layout)
        type_counts = {}
        for r in records:
            td = TYPE_DISPLAY.get(r.type, r.type)
            type_counts[td] = type_counts.get(td, 0) + 1
        total_src = sum(type_counts.values()) or 1
        src_colors = {'图片': '#3B82F6', '视频': '#8B5CF6'}
        for tp, cnt in type_counts.items():
            lbl = QLabel(
                self._bar_html(
                    tp, cnt, total_src, src_colors.get(tp, '#3B82F6')))
            lbl.setStyleSheet("border:none;background:transparent;")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            self._source_layout.addWidget(lbl)

    # ── 地图渲染（Folium）──────────────────────────────

    @staticmethod
    def _fix_cdn(html_path):
        """修复 HTML 中被墙的 CDN 资源"""
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # jQuery (code.jquery.com 被墙) → 换 jsdelivr
        html = html.replace(
            'https://code.jquery.com/jquery-3.7.1.min.js',
            'https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _render_map(self):
        records = self._records
        if not records:
            self._show_empty()
            return

        lats = [r.latitude for r in records]
        lons = [r.longitude for r in records]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=16,
            tiles=None,
            control_scale=True,
        )

        # 使用固定子域 b 的显式 URL，避免 {s} 子域变量在 Chromium 中加载失败
        folium.TileLayer(
            tiles='https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
            attr='&copy; <a href="https://carto.com/">CARTO</a>',
            name='深色底图', control=False).add_to(m)

        # 标注点聚类
        cluster = MarkerCluster(
            name='缺陷标注', overlay=True, control=False,
            options={'maxClusterRadius': 50,
                     'spiderfyOnMaxZoom': True,
                     'showCoverageOnHover': False})

        for r in records:
            sev, sev_color = get_severity(r.total_objects)
            td = TYPE_DISPLAY.get(r.type, r.type)
            fcolor = {'严重': 'red', '中等': 'orange',
                      '轻微': 'green'}.get(sev, 'blue')

            cls_dist = r.get_class_distribution_dict()
            cls_rows = ''.join(
                f'<tr><td style="color:#8B9AB5;padding:2px 8px">{k}</td>'
                f'<td style="color:#F1F5F9;text-align:right;'
                f'padding:2px 8px">{v}</td></tr>'
                for k, v in cls_dist.items())

            popup = f"""
            <div style="background:#171E28;color:#F1F5F9;
                font-family:'Microsoft YaHei',sans-serif;
                padding:12px;border-radius:8px;min-width:220px;font-size:12px;">
                <div style="display:flex;justify-content:space-between;
                    align-items:center;margin-bottom:8px">
                    <b style="font-size:14px">#{r.id} {td}检测</b>
                    <span style="background:{sev_color};color:#fff;
                        padding:2px 8px;border-radius:10px;
                        font-size:11px;font-weight:bold;">{sev}</span>
                </div>
                <div style="color:#8B9AB5;font-size:11px;margin-bottom:6px">
                    {r.timestamp or '--'}<br>来源: {r.source or '--'}
                </div>
                <div style="color:#06B6D4;font-size:12px;margin-bottom:4px">
                    检出 <b style="color:#F1F5F9">{r.total_objects}</b> 个缺陷
                </div>
                <table style="width:100%;border-collapse:collapse;margin-top:4px">
                    <tr style="border-bottom:1px solid #262F3D">
                        <th style="color:#5A6A80;text-align:left;
                            padding:2px 8px;font-size:11px">类型</th>
                        <th style="color:#5A6A80;text-align:right;
                            padding:2px 8px;font-size:11px">数量</th>
                    </tr>
                    {cls_rows}
                </table>
            </div>"""

            folium.Marker(
                [r.latitude, r.longitude],
                popup=folium.Popup(popup, max_width=300, min_width=250),
                tooltip=f'#{r.id} ({r.total_objects}个缺陷) [{sev}]',
                icon=folium.Icon(color=fcolor, icon='exclamation-triangle',
                                 prefix='fa'),
            ).add_to(cluster)

        cluster.add_to(m)

        # 巡检路线
        if self._show_route and len(records) > 1:
            sorted_recs = sorted(records, key=lambda r: r.timestamp or '')
            coords = [[r.latitude, r.longitude] for r in sorted_recs]
            folium.PolyLine(
                coords, color='#3B82F6', weight=3, opacity=0.7,
                dash_array='10, 6', tooltip='巡检路线').add_to(m)
            folium.Marker(
                coords[0], tooltip='起点',
                icon=folium.Icon(color='green', icon='play',
                                 prefix='fa')).add_to(m)
            folium.Marker(
                coords[-1], tooltip='终点',
                icon=folium.Icon(color='red', icon='flag-checkered',
                                 prefix='fa')).add_to(m)

        # 热力图
        if self._show_heatmap and len(records) > 1:
            HeatMap(
                [[r.latitude, r.longitude, r.total_objects]
                 for r in records],
                name='缺陷密度', min_opacity=0.3, max_zoom=16,
                radius=20, blur=15,
                gradient={0.2: '#10B981', 0.5: '#F59E0B',
                          0.8: '#EF4444', 1.0: '#DC2626'},
            ).add_to(m)

        folium.LayerControl(hideSingleBase=True).add_to(m)

        # 保存 HTML 并修复被墙的 CDN
        m.save(_MAP_HTML)
        self._fix_cdn(_MAP_HTML)

        self._first_load = True
        self._overlay.show()
        self._overlay.setGeometry(self._web.rect())
        self._web.setUrl(QUrl.fromLocalFile(_MAP_HTML))

    def _show_empty(self):
        c = AppStyles.COLORS
        html = f'''<html><head><style>
            html,body{{margin:0;padding:0;height:100vh;
            display:flex;align-items:center;justify-content:center;
            background-color:{c['background_main']};
            color:{c['text_secondary']};
            font-family:'Microsoft YaHei',sans-serif;}}
        </style></head><body>
            <div style="text-align:center">
                <p style="font-size:18px;color:{c['text_secondary']}">
                    暂无带位置信息的检测记录</p>
                <p style="font-size:12px;color:{c['text_disabled']}">
                    检测含有 GPS 信息的照片后，缺陷位置将自动标注在地图上
                </p>
            </div>
        </body></html>'''
        self._overlay.hide()
        self._web.setHtml(html)
