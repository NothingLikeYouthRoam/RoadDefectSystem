from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QIcon, QPen, QCloseEvent

from ui.detect_image_page import DetectImagePage
from ui.detect_video_page import DetectVideoPage
from ui.map_page import MapPage
from ui.history_page import HistoryPage
from ui.model_manage_page import ModelManagePage
from ui.metrics_page import MetricsPage
from styles import AppStyles


class MainWindow(QMainWindow):
    def __init__(self, username='admin'):
        super().__init__()
        self.username = username
        self.setWindowTitle('道路缺陷检测系统 - YOLOv8')

        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(icon_pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(59, 130, 246)))
        p.drawRoundedRect(2, 2, 28, 28, 6, 6)
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawEllipse(8, 8, 16, 10)
        p.drawRect(8, 18, 16, 6)
        p.end()
        self.setWindowIcon(QIcon(icon_pixmap))

        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.showMaximized()
        self._init_ui()

    def _init_ui(self):
        c = AppStyles.COLORS
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.left_nav = QWidget()
        self.left_nav.setFixedWidth(220)
        self.left_nav.setStyleSheet(f'background-color: {c["background_secondary"]};')
        self._setup_left_nav()
        main_layout.addWidget(self.left_nav)

        self.right_widget = QWidget()
        self.right_widget.setStyleSheet(f'background-color: {c["background_main"]};')
        self._setup_right_widget()
        main_layout.addWidget(self.right_widget, 1)

        # Status bar
        self.statusBar().setStyleSheet(f'''
            QStatusBar {{
                background-color: {c["background_secondary"]};
                color: {c["text_disabled"]};
                border-top: 1px solid {c["border"]};
                padding: 0 12px;
            }}
        ''')
        status_dot = QLabel()
        dot_pix = QPixmap(8, 8)
        dot_pix.fill(Qt.GlobalColor.transparent)
        dp = QPainter(dot_pix)
        dp.setRenderHint(QPainter.RenderHint.Antialiasing)
        dp.setBrush(QBrush(QColor(16, 185, 129)))
        dp.setPen(Qt.PenStyle.NoPen)
        dp.drawEllipse(0, 0, 8, 8)
        dp.end()
        status_dot.setPixmap(dot_pix)
        status_dot.setStyleSheet('border: none;')
        self.statusBar().addWidget(status_dot)
        self.statusBar().showMessage('  就绪')

    def _setup_left_nav(self):
        c = AppStyles.COLORS
        left_layout = QVBoxLayout(self.left_nav)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Brand header
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(f'''
            background-color: {c['background_secondary']};
            border-bottom: 1px solid {c['border']};
        ''')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(10)

        logo_bg = QWidget()
        logo_bg.setFixedSize(34, 34)
        logo_bg.setStyleSheet('''
            background-color: rgba(59, 130, 246, 0.12);
            border-radius: 8px;
        ''')
        logo_inner_layout = QVBoxLayout(logo_bg)
        logo_inner_layout.setContentsMargins(5, 5, 5, 5)
        logo_label = QLabel()
        logo_label.setPixmap(AppStyles.create_icon('road', 24, QColor(59, 130, 246)))
        logo_label.setStyleSheet('border: none;')
        logo_inner_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignCenter)

        brand = QWidget()
        brand.setStyleSheet('background: transparent;')
        brand_l = QVBoxLayout(brand)
        brand_l.setSpacing(0)
        brand_l.setContentsMargins(0, 0, 0, 0)
        t = QLabel('道路缺陷检测')
        t.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.Bold))
        t.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        brand_l.addWidget(t)
        s = QLabel('YOLOv8')
        s.setFont(QFont('Microsoft YaHei', 8))
        s.setStyleSheet(f'color: {c["text_disabled"]}; border: none;')
        brand_l.addWidget(s)

        header_layout.addWidget(logo_bg)
        header_layout.addWidget(brand, 1)
        left_layout.addWidget(header)

        # Nav items
        nav_container = QWidget()
        nav_container.setStyleSheet('background: transparent;')
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 12, 8, 8)
        nav_layout.setSpacing(2)

        self.nav_items = []
        nav_data = [
            ('section', '检测'),
            ('image', '图片识别'),
            ('video', '视频识别'),
            ('section', '管理'),
            ('history', '检测历史'),
            ('model', '模型管理'),
            ('metrics', '指标展示'),
            ('map', '缺陷地图'),
        ]

        for entry in nav_data:
            if entry[0] == 'section':
                lbl = QLabel(entry[1])
                lbl.setFont(QFont('Microsoft YaHei', 8))
                lbl.setStyleSheet(f'color: {c["text_disabled"]}; border: none; padding: 10px 14px 2px 14px;')
                nav_layout.addWidget(lbl)
            else:
                nav_item = self._create_nav_item(entry[0], entry[1])
                self.nav_items.append(nav_item)
                nav_layout.addWidget(nav_item['widget'])

        nav_layout.addStretch()
        left_layout.addWidget(nav_container, 1)

        # User area
        user_widget = QWidget()
        user_widget.setFixedHeight(52)
        user_widget.setStyleSheet(f'''
            background-color: {c["background_secondary"]};
            border-top: 1px solid {c["border"]};
        ''')
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(14, 6, 14, 6)
        user_layout.setSpacing(8)

        avatar = QLabel()
        avatar.setFixedSize(30, 30)
        avatar_pixmap = QPixmap(30, 30)
        avatar_pixmap.fill(Qt.GlobalColor.transparent)
        ap = QPainter(avatar_pixmap)
        ap.setRenderHint(QPainter.RenderHint.Antialiasing)
        ap.setPen(QPen(QColor(59, 130, 246), 1.5))
        ap.setBrush(QBrush(QColor(59, 130, 246, 30)))
        ap.drawEllipse(1, 1, 28, 28)
        ap.setPen(Qt.PenStyle.NoPen)
        ap.setBrush(QBrush(QColor(148, 163, 184)))
        ap.drawEllipse(9, 6, 12, 10)
        ap.drawRoundedRect(7, 17, 16, 7, 3, 3)
        ap.end()
        avatar.setPixmap(avatar_pixmap)
        avatar.setStyleSheet('border: none;')

        user_name = QLabel(self.username)
        user_name.setFont(QFont('Microsoft YaHei', 9))
        user_name.setStyleSheet(f'color: {c["text_primary"]}; border: none;')

        role = QLabel('管理员')
        role.setFont(QFont('Microsoft YaHei', 8))
        role.setStyleSheet(f'color: {c["gradient_start"]}; background-color: rgba(59,130,246,0.10); border-radius: 3px; padding: 1px 5px; border: none;')

        user_layout.addWidget(avatar)
        user_layout.addWidget(user_name)
        user_layout.addWidget(role)
        user_layout.addStretch()
        left_layout.addWidget(user_widget)

    def _create_nav_item(self, icon_type, text):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setFixedHeight(36)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setToolTip(text)
        widget.setStyleSheet(f'''
            QWidget {{ background: transparent; border-radius: 6px; }}
            QWidget:hover {{ background-color: {c['background_hover']}; }}
        ''')

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        indicator = QLabel()
        indicator.setFixedWidth(3)
        indicator.setFixedHeight(18)
        indicator.setStyleSheet(f'background-color: {c["gradient_start"]}; border-radius: 1px;')
        indicator.hide()

        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setPixmap(AppStyles.create_icon(icon_type, 16, QColor(c['text_secondary'])))
        icon_label.setStyleSheet('border: none;')

        text_label = QLabel(text)
        text_label.setFont(QFont('Microsoft YaHei', 9))
        text_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        layout.addWidget(indicator)
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

        item_data = {
            'widget': widget, 'indicator': indicator,
            'icon_label': icon_label, 'icon_type': icon_type,
            'text_label': text_label, 'key': text, 'selected': False
        }
        item_data['key'] = {'图片识别': 'image', '视频识别': 'video',
                            '检测历史': 'history', '模型管理': 'model', '指标展示': 'metrics',
                            '缺陷地图': 'map'}[text]
        widget.mousePressEvent = lambda e, d=item_data: self._on_nav_click(d)
        return item_data

    def _on_nav_click(self, item_data):
        c = AppStyles.COLORS
        for item in self.nav_items:
            item['selected'] = False
            item['indicator'].hide()
            item['text_label'].setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            item['icon_label'].setPixmap(AppStyles.create_icon(item['icon_type'], 16, QColor(c['text_secondary'])))
            item['widget'].setStyleSheet(f'''
                QWidget {{ background: transparent; border-radius: 6px; }}
                QWidget:hover {{ background-color: {c['background_hover']}; }}
            ''')

        item_data['selected'] = True
        item_data['indicator'].show()
        item_data['text_label'].setStyleSheet(f'color: {c["gradient_start"]}; font-weight: bold; border: none;')
        item_data['icon_label'].setPixmap(AppStyles.create_icon(item_data['icon_type'], 16, QColor(c['gradient_start'])))
        item_data['widget'].setStyleSheet(f'''
            QWidget {{
                background-color: rgba(59, 130, 246, 0.08);
                border-radius: 6px;
            }}
        ''')

        target_index = self.page_keys.index(item_data['key'])
        self._animate_page_switch(target_index)

        titles = {'image': '图片识别', 'video': '视频识别',
                  'history': '检测历史', 'model': '模型管理', 'metrics': '指标展示',
                  'map': '缺陷地图'}
        self.page_title_label.setText(titles.get(item_data['key'], ''))

    def _animate_page_switch(self, target_index):
        current_index = self.stack.currentIndex()
        if current_index == target_index:
            return
        target_page = self.pages[self.page_keys[target_index]]
        # QWebEngineView 不兼容 QGraphicsOpacityEffect，直接切换
        from ui.map_page import MapPage
        if isinstance(target_page, MapPage):
            self.stack.setCurrentIndex(target_index)
            return
        if not hasattr(target_page, '_opacity_effect') or target_page._opacity_effect is None:
            effect = QGraphicsOpacityEffect(target_page)
            target_page.setGraphicsEffect(effect)
            target_page._opacity_effect = effect
        else:
            effect = target_page._opacity_effect
        self.stack.setCurrentIndex(target_index)
        effect.setOpacity(0.0)
        self._page_anim = QPropertyAnimation(effect, b'opacity')
        self._page_anim.setDuration(150)
        self._page_anim.setStartValue(0.0)
        self._page_anim.setEndValue(1.0)
        self._page_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._page_anim.start()

    def _setup_right_widget(self):
        c = AppStyles.COLORS
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet(f'''
            background-color: {c['background_secondary']};
            border-bottom: 1px solid {c['border']};
        ''')
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        accent = QWidget()
        accent.setFixedSize(3, 18)
        accent.setStyleSheet(f'background-color: {c["gradient_start"]}; border-radius: 1px;')

        page_title = QLabel('图片识别')
        page_title.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        page_title.setStyleSheet(f'color: {c["text_primary"]}; border: none;')
        self.page_title_label = page_title

        top_layout.addWidget(accent)
        top_layout.addSpacing(8)
        top_layout.addWidget(page_title)
        top_layout.addStretch()

        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont('Microsoft YaHei', 9))
        self.datetime_label.setStyleSheet(f'color: {c["text_disabled"]}; border: none;')
        top_layout.addWidget(self.datetime_label)
        top_layout.addSpacing(16)

        user_label = QLabel(self.username)
        user_label.setFont(QFont('Microsoft YaHei', 9))
        user_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        top_layout.addWidget(user_label)

        right_layout.addWidget(top_bar)

        # Content
        content_widget = QWidget()
        content_widget.setStyleSheet(f'background-color: {c["background_main"]};')
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.stack = QStackedWidget()
        self.pages = {
            'image': DetectImagePage(), 'video': DetectVideoPage(),
            'history': HistoryPage(), 'model': ModelManagePage(), 'metrics': MetricsPage(),
            'map': MapPage(),
        }
        self.page_keys = ['image', 'video', 'history', 'model', 'metrics', 'map']
        for key in self.page_keys:
            self.stack.addWidget(self.pages[key])
        content_layout.addWidget(self.stack)
        right_layout.addWidget(content_widget, 1)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        for item in self.nav_items:
            if item['key'] == 'image':
                self._on_nav_click(item)
                break

    def _update_clock(self):
        self.datetime_label.setText(QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss'))

    def closeEvent(self, event: QCloseEvent):
        """关闭窗口时清理所有资源，确保程序退出"""
        # 停止时钟定时器
        if hasattr(self, '_clock_timer'):
            self._clock_timer.stop()

        # 停止各子页面的定时器、后台线程并释放资源
        if hasattr(self, 'pages'):
            for page in self.pages.values():
                # 标记停止，阻止后台线程再往主线程注入回调
                page._detect_busy = False
                timer = getattr(page, '_timer', None)
                if timer is not None:
                    timer.stop()
                cap = getattr(page, '_cap', None)
                if cap is not None:
                    cap.release()

        event.accept()
        QApplication.quit()
