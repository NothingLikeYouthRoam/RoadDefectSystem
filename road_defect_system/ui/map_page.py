import folium
import io
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import AppStyles

TYPE_DISPLAY = {'image': '图片', 'video': '视频', 'camera': '摄像头'}


class MapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_map()

    def _init_ui(self):
        c = AppStyles.COLORS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet(AppStyles.get_panel_style())
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(16, 10, 16, 10)

        self.count_label = QLabel('标注数: 0')
        self.count_label.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        self.count_label.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        tl.addWidget(self.count_label)

        self.stats_label = QLabel('')
        self.stats_label.setFont(QFont('Microsoft YaHei', 9))
        self.stats_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        tl.addWidget(self.stats_label)
        tl.addStretch()

        btn_refresh = QPushButton('刷新地图')
        btn_refresh.setFixedHeight(32)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setFont(QFont('Microsoft YaHei', 9))
        btn_refresh.setStyleSheet(AppStyles.get_button_style('primary'))
        btn_refresh.clicked.connect(self._refresh_map)
        tl.addWidget(btn_refresh)

        layout.addWidget(toolbar)

        # 直接创建 QWebEngineView，预设深色背景避免白闪
        self._web = QWebEngineView()
        self._web.setStyleSheet(f'''
            QWebEngineView {{
                background-color: {c["background_main"]};
                border: 1px solid {c["border"]};
                border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
            }}
        ''')
        self._show_empty_html()
        layout.addWidget(self._web, 1)

    def _refresh_map(self):
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        records = db.get_records_with_gps()

        self.count_label.setText(f'标注数: {len(records)}')

        if not records:
            self._show_empty_html()
            self.stats_label.setText('暂无带位置信息的检测记录')
            return

        # 统计
        type_counts = {}
        for r in records:
            t = TYPE_DISPLAY.get(r.type, r.type)
            type_counts[t] = type_counts.get(t, 0) + 1
        stats = '  |  '.join(f'{k}: {v}' for k, v in type_counts.items())
        self.stats_label.setText(stats)

        # 计算中心点
        lats = [r.latitude for r in records]
        lons = [r.longitude for r in records]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        for r in records:
            td = TYPE_DISPLAY.get(r.type, r.type)
            popup_html = (
                f'<b style="font-size:13px">#{r.id} {td}检测</b><br>'
                f'时间: {r.timestamp or "--"}<br>'
                f'来源: {r.source or "--"}<br>'
                f'检测数: <b>{r.total_objects}</b><br>'
                f'类别: {r.class_distribution or "--"}'
            )
            folium.Marker(
                location=[r.latitude, r.longitude],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f'#{r.id} ({r.total_objects}个缺陷)',
                icon=folium.Icon(color='blue', icon='info-sign'),
            ).add_to(m)

        buf = io.BytesIO()
        m.save(buf, close_file=False)
        html = buf.getvalue().decode('utf-8')
        self._web.setHtml(html)

    def _show_empty_html(self):
        c = AppStyles.COLORS
        html = f'''<html><body style="
            display:flex;align-items:center;justify-content:center;
            height:100vh;margin:0;
            background-color:{c['background_main']};
            color:{c['text_secondary']};
            font-family:'Microsoft YaHei',sans-serif;font-size:14px;
        ">
            <div style="text-align:center">
                <p style="font-size:18px;color:{c['text_secondary']}">暂无带位置信息的检测记录</p>
                <p style="font-size:12px;color:{c['text_disabled']}">
                    检测含有 GPS 信息的照片后，缺陷位置将自动标注在地图上
                </p>
            </div>
        </body></html>'''
        self._web.setHtml(html)
