import random
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import (
    QFont, QPainter, QColor, QBrush, QPen, QPixmap, QIcon,
    QPainterPath
)


# ── 数字雨背景组件 ──────────────────────────────────────────────

class DigitalRainWidget(QWidget):
    """仿 Matrix 数字雨动画背景 — 青蓝色调"""

    CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&'
    FONT_SIZE = 15
    COL_SPACING = 30  # 列间距（原 15，拉大后更清爽）
    BG_COLOR = QColor(10, 14, 26)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._columns = 0
        self._drops = []
        self._speeds = []

        self._buffer = None
        self._buffer_painter = None
        self._fade_pixmap = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(65)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._columns = max(1, self.width() // self.COL_SPACING)
        while len(self._drops) < self._columns:
            self._drops.append(random.uniform(-30, 0))
            self._speeds.append(random.uniform(0.25, 0.55))
        self._drops = self._drops[:self._columns]
        self._speeds = self._speeds[:self._columns]
        if self._buffer_painter:
            self._buffer_painter.end()
            self._buffer_painter = None
        self._buffer = QPixmap(self.size())
        self._buffer.fill(self.BG_COLOR)
        self._fade_pixmap = QPixmap(self.size())
        self._fade_pixmap.fill(QColor(10, 14, 26, 18))

    def _tick(self):
        if not self._buffer or self._columns == 0:
            return

        p = self._buffer_painter
        if p is None:
            p = QPainter(self._buffer)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            self._buffer_painter = p

        # 在离屏缓冲区上叠加半透明遮罩（产生拖尾渐隐效果）
        if self._fade_pixmap:
            p.drawPixmap(0, 0, self._fade_pixmap)

        font = QFont('Consolas', self.FONT_SIZE)
        font.setBold(True)
        p.setFont(font)

        h = self.height()
        col_w = self.COL_SPACING

        for i in range(self._columns):
            x = i * col_w
            y = self._drops[i] * col_w

            ch = random.choice(self.CHARS)
            p.setPen(QPen(QColor(180, 235, 255, 240)))
            p.drawText(int(x), int(y), ch)

            for t in range(1, 5):
                ty = y - t * col_w
                if ty < -col_w:
                    break
                tc = random.choice(self.CHARS)
                alpha = max(15, 200 - t * 50)
                blue = max(80, 230 - t * 30)
                p.setPen(QPen(QColor(0, 170, blue, alpha)))
                p.drawText(int(x), int(ty), tc)

            self._drops[i] += self._speeds[i]
            if self._drops[i] * col_w > h and random.random() > 0.975:
                self._drops[i] = random.uniform(-20, 0)
                self._speeds[i] = random.uniform(0.6, 1.4)

        self.update()

    def paintEvent(self, event):
        if self._buffer:
            p = QPainter(self)
            p.drawPixmap(0, 0, self._buffer)
            p.end()


# ── 登录对话框 ──────────────────────────────────────────────────

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.username = None
        self._drag_pos = QPoint()

        self.setWindowTitle('道路缺陷检测系统 - 登录')
        self.setModal(True)
        self.setFixedSize(900, 600)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        ip = QPainter(icon_pixmap)
        ip.setRenderHint(QPainter.RenderHint.Antialiasing)
        ip.setBrush(QBrush(QColor(0, 140, 255)))
        ip.drawRoundedRect(2, 2, 28, 28, 4, 4)
        ip.setBrush(QBrush(QColor(255, 255, 255)))
        ip.drawRect(4, 20, 24, 4)
        ip.drawEllipse(10, 12, 8, 6)
        ip.drawRect(14, 16, 4, 2)
        ip.end()
        self.setWindowIcon(QIcon(icon_pixmap))

        self._init_ui()

    # ── 构建界面 ──

    def _init_ui(self):
        self.setStyleSheet('background-color: #0a0e1a;')

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 数字雨背景
        self._rain = DigitalRainWidget(self)
        self._rain.setGeometry(0, 0, self.width(), self.height())

        # 自定义标题栏
        self._title_bar = QWidget(self)
        self._title_bar.setFixedHeight(36)
        self._title_bar.setStyleSheet('background-color: rgba(10, 14, 26, 0.9);')
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(12, 0, 0, 0)
        title_layout.setSpacing(0)

        # 标题栏图标 + 文字
        title_icon = QLabel()
        title_icon.setPixmap(self.windowIcon().pixmap(18, 18))
        title_icon.setStyleSheet('border: none;')
        title_label = QLabel(' 道路缺陷检测系统 - 登录')
        title_label.setFont(QFont('Microsoft YaHei', 9))
        title_label.setStyleSheet('color: rgba(160,185,230,0.6); border: none;')
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 最小化按钮
        btn_ss = '''
            QPushButton {{
                background: transparent; color: rgba(160,185,230,0.5);
                border: none; font-size: 14px; font-weight: bold;
                min-width: 46px; max-width: 46px;
            }}
            QPushButton:hover {{ background-color: rgba(255,255,255,0.08); color: rgba(200,220,255,0.8); }}
        '''
        self._min_btn = QPushButton('—')
        self._min_btn.setFixedHeight(36)
        self._min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._min_btn.setStyleSheet(btn_ss)
        self._min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self._min_btn)

        # 关闭按钮
        close_btn_ss = '''
            QPushButton {
                background: transparent; color: rgba(160,185,230,0.5);
                border: none; font-size: 14px; font-weight: bold;
                min-width: 46px; max-width: 46px;
            }
            QPushButton:hover { background-color: rgba(255,80,80,0.15); color: #ff6b6b; }
        '''
        self._close_btn = QPushButton('✕')
        self._close_btn.setFixedHeight(36)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet(close_btn_ss)
        self._close_btn.clicked.connect(self.reject)
        title_layout.addWidget(self._close_btn)

        # 登录卡片
        self._card = QWidget(self)
        self._card.setObjectName('loginCard')
        self._card.setStyleSheet('''
            QWidget#loginCard {
                background-color: rgba(12, 18, 36, 0.78);
                border-radius: 20px;
                border: 1px solid rgba(0, 170, 255, 0.15);
            }
        ''')
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 100, 200, 50))
        self._card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(36, 28, 36, 28)
        card_layout.setSpacing(0)

        # Logo
        logo_bg = QWidget()
        logo_bg.setFixedSize(56, 56)
        logo_bg.setStyleSheet('''
            background: qlineargradient(x1:0,y1:0,x2:1,x2:1,
                stop:0 #00b4ff, stop:1 #0055dd);
            border-radius: 16px;
        ''')
        logo_layout = QVBoxLayout(logo_bg)
        logo_layout.setContentsMargins(10, 10, 10, 10)
        logo_label = QLabel()
        logo_label.setPixmap(self._create_shield_icon(34))
        logo_label.setStyleSheet('border: none;')
        logo_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignCenter)

        logo_shadow = QGraphicsDropShadowEffect(logo_bg)
        logo_shadow.setBlurRadius(20)
        logo_shadow.setOffset(0, 4)
        logo_shadow.setColor(QColor(0, 120, 255, 60))
        logo_bg.setGraphicsEffect(logo_shadow)

        card_layout.addWidget(logo_bg, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(14)

        # 标题
        title = QLabel('系统登录')
        title.setFont(QFont('Microsoft YaHei', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: #e8f0ff; border: none;')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel('Road Defect Detection System')
        subtitle.setFont(QFont('Microsoft YaHei', 9))
        subtitle.setStyleSheet('color: rgba(160,185,230,0.5); border: none;')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(26)

        # ── 输入框区 ──

        input_ss_template = '''
            QLineEdit {{
                background-color: rgba(0, 30, 80, 0.35);
                border: 1px solid rgba(0, 120, 255, 0.18);
                border-radius: 10px;
                padding: 10px 14px 10px {padding_left}px;
                color: #c8deff; font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: rgba(0, 170, 255, 0.5);
                background-color: rgba(0, 30, 80, 0.5);
            }}
            QLineEdit::placeholder {{ color: rgba(100,150,220,0.4); }}
        '''

        # 用户名输入框（带图标）
        user_container = QWidget()
        user_container.setStyleSheet('background: transparent; border: none;')
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(0)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('请输入用户名')
        self.username_input.setFixedHeight(48)
        self.username_input.setText('admin')
        self.username_input.setFont(QFont('Microsoft YaHei', 10))
        self.username_input.setStyleSheet(input_ss_template.format(padding_left='44'))
        # 用户名图标
        user_icon = QLabel(self.username_input)
        user_icon.setPixmap(self._draw_user_icon(18))
        user_icon.setStyleSheet('background: transparent; border: none;')
        user_icon.setGeometry(14, (48 - 18) // 2, 18, 18)

        card_layout.addWidget(self.username_input)
        card_layout.addSpacing(14)

        # 密码输入框（带图标 + 显隐按钮）
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('请输入密码')
        self.password_input.setFixedHeight(48)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText('admin123')
        self.password_input.setFont(QFont('Microsoft YaHei', 10))
        self.password_input.setStyleSheet(input_ss_template.format(padding_left='44'))

        # 密码图标
        pwd_icon = QLabel(self.password_input)
        pwd_icon.setPixmap(self._draw_lock_icon(18))
        pwd_icon.setStyleSheet('background: transparent; border: none;')
        pwd_icon.setGeometry(14, (48 - 18) // 2, 18, 18)

        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(22)

        # 密码显隐按钮
        self._pwd_visible = False
        self.toggle_pwd_btn = QPushButton()
        self.toggle_pwd_btn.setParent(self.password_input)
        self.toggle_pwd_btn.setFixedSize(36, 36)
        self.toggle_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd_btn.setToolTip('显示/隐藏密码')
        self.toggle_pwd_btn.setStyleSheet('''
            QPushButton {
                background: transparent; border: none;
            }
            QPushButton:hover { background: rgba(0,170,255,0.1); border-radius: 6px; }
        ''')
        self._update_toggle_icon()
        self.toggle_pwd_btn.clicked.connect(self._toggle_password)

        # ── 登录页内容 ──
        self._login_page = QWidget()
        self._login_page.setStyleSheet('background: transparent;')
        login_layout = QVBoxLayout(self._login_page)
        login_layout.setContentsMargins(0, 0, 0, 0)
        login_layout.setSpacing(0)

        # 登录按钮
        self.login_btn = QPushButton('登 录')
        self.login_btn.setFixedHeight(48)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        self.login_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0088ff, stop:1 #0055dd);
                color: white; border: none; border-radius: 12px;
                font-size: 15px; letter-spacing: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2299ff, stop:1 #0066ee);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0066dd, stop:1 #0044bb);
            }
        ''')
        self.login_btn.clicked.connect(self._handle_login)
        login_layout.addWidget(self.login_btn)

        # 注册入口
        login_layout.addSpacing(12)
        register_row = QHBoxLayout()
        register_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        register_row.setSpacing(0)
        no_account = QLabel('还没有账号？')
        no_account.setFont(QFont('Microsoft YaHei', 9))
        no_account.setStyleSheet('color: rgba(100,150,220,0.5); border: none;')
        register_row.addWidget(no_account)
        register_btn = QLabel('立即注册')
        register_btn.setFont(QFont('Microsoft YaHei', 9))
        register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        register_btn.setStyleSheet('color: #3B82F6; border: none;')
        register_btn.mousePressEvent = lambda e: self._switch_to_register()
        register_row.addWidget(register_btn)
        login_layout.addLayout(register_row)
        login_layout.addStretch()

        # ── 注册页内容 ──
        self._register_page = QWidget()
        self._register_page.setStyleSheet('background: transparent;')
        reg_layout = QVBoxLayout(self._register_page)
        reg_layout.setContentsMargins(0, 0, 0, 0)
        reg_layout.setSpacing(0)

        # 确认密码
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText('请再次输入密码')
        self.confirm_input.setFixedHeight(48)
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setFont(QFont('Microsoft YaHei', 10))
        self.confirm_input.setStyleSheet(input_ss_template.format(padding_left='14'))
        reg_layout.addWidget(self.confirm_input)
        reg_layout.addSpacing(22)

        # 注册按钮
        self.register_btn = QPushButton('注 册')
        self.register_btn.setFixedHeight(48)
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        self.register_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0088ff, stop:1 #0055dd);
                color: white; border: none; border-radius: 12px;
                font-size: 15px; letter-spacing: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #2299ff, stop:1 #0066ee);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0066dd, stop:1 #0044bb);
            }
        ''')
        self.register_btn.clicked.connect(self._handle_register)
        reg_layout.addWidget(self.register_btn)

        # 返回登录入口
        reg_layout.addSpacing(12)
        back_row = QHBoxLayout()
        back_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        back_row.setSpacing(0)
        has_account = QLabel('已有账号？')
        has_account.setFont(QFont('Microsoft YaHei', 9))
        has_account.setStyleSheet('color: rgba(100,150,220,0.5); border: none;')
        back_row.addWidget(has_account)
        back_btn = QLabel('返回登录')
        back_btn.setFont(QFont('Microsoft YaHei', 9))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet('color: #3B82F6; border: none;')
        back_btn.mousePressEvent = lambda e: self._switch_to_login()
        back_row.addWidget(back_btn)
        reg_layout.addLayout(back_row)
        reg_layout.addStretch()

        self._register_page.hide()
        card_layout.addWidget(self._login_page)
        card_layout.addWidget(self._register_page)

        # 回车快捷键
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_login)
        self.confirm_input.returnPressed.connect(self._handle_register)

    # ── showEvent 中定位卡片和按钮 ──

    def showEvent(self, event):
        super().showEvent(event)
        # 居中显示
        screen = self.screen()
        if screen:
            geo = screen.geometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2
            )
        self._update_card_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        super().keyPressEvent(event)

    def _update_card_position(self):
        # 标题栏
        self._title_bar.setGeometry(0, 0, self.width(), 36)
        self._title_bar.raise_()
        # 数字雨
        self._rain.setGeometry(0, 0, self.width(), self.height())
        # 卡片
        is_register = hasattr(self, '_register_page') and self._register_page.isVisible()
        cw, ch = (400, 500) if is_register else (400, 470)
        self._card.setGeometry(
            (self.width() - cw) // 2,
            (self.height() - ch) // 2,
            cw, ch
        )
        pw = self.password_input.width()
        if pw > 0:
            self.toggle_pwd_btn.move(pw - 42, (48 - 36) // 2)
        self._card.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_card_position()
        self._card.raise_()

    # ── 登录/注册切换 ──

    def _switch_to_register(self):
        self._login_page.hide()
        self._register_page.show()
        self.username_input.setPlaceholderText('请输入用户名（至少3个字符）')
        self.password_input.setPlaceholderText('请输入密码（至少6个字符）')
        self.username_input.setText('')
        self.password_input.setText('')
        self.username_input.setFocus()
        self._update_card_position()

    def _switch_to_login(self):
        self._register_page.hide()
        self._login_page.show()
        self.username_input.setPlaceholderText('请输入用户名')
        self.password_input.setPlaceholderText('请输入密码')
        self.confirm_input.setText('')
        self.username_input.setFocus()
        self._update_card_position()

    # ── 图标绘制 ──

    @staticmethod
    def _draw_user_icon(size):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 170, 255, 160)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        # 头
        p.drawEllipse(int(size * 0.3), int(size * 0.05), int(size * 0.4), int(size * 0.4))
        # 身体
        path = QPainterPath()
        path.moveTo(int(size * 0.1), int(size * 0.95))
        path.quadTo(int(size * 0.1), int(size * 0.55), int(size * 0.5), int(size * 0.52))
        path.quadTo(int(size * 0.9), int(size * 0.55), int(size * 0.9), int(size * 0.95))
        p.drawPath(path)
        p.end()
        return pix

    @staticmethod
    def _draw_lock_icon(size):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 170, 255, 160)
        p.setPen(QPen(color, max(1.5, size / 10)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # 锁环
        p.drawRoundedRect(int(size * 0.25), 0, int(size * 0.5), int(size * 0.5), 3, 3)
        # 锁体
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawRoundedRect(int(size * 0.1), int(size * 0.4), int(size * 0.8), int(size * 0.55), 3, 3)
        p.end()
        return pix

    @staticmethod
    def _create_shield_icon(size):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = size
        path = QPainterPath()
        path.moveTo(s * 0.5, s * 0.08)
        path.lineTo(s * 0.88, s * 0.22)
        path.lineTo(s * 0.88, s * 0.52)
        path.cubicTo(s * 0.88, s * 0.78, s * 0.5, s * 0.92, s * 0.5, s * 0.92)
        path.cubicTo(s * 0.5, s * 0.92, s * 0.12, s * 0.78, s * 0.12, s * 0.52)
        path.lineTo(s * 0.12, s * 0.22)
        path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 220)))
        p.drawPath(path)
        p.setPen(QPen(QColor(0, 100, 220), max(2, s / 14),
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                       Qt.PenJoinStyle.RoundJoin))
        p.drawLine(int(s * 0.32), int(s * 0.52),
                   int(s * 0.45), int(s * 0.66))
        p.drawLine(int(s * 0.45), int(s * 0.66),
                   int(s * 0.7), int(s * 0.36))
        p.end()
        return pix

    # ── 拖动窗口 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    # ── 密码显隐 ──

    def _toggle_password(self):
        self._pwd_visible = not self._pwd_visible
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if self._pwd_visible
            else QLineEdit.EchoMode.Password
        )
        self._update_toggle_icon()

    def _update_toggle_icon(self):
        pix = QPixmap(18, 18)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(100, 170, 255) if self._pwd_visible else QColor(80, 120, 180)
        p.setPen(QPen(color, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(2, 5, 14, 8)
        if self._pwd_visible:
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(6, 7, 6, 4)
        else:
            p.drawLine(3, 14, 15, 4)
        p.end()
        self.toggle_pwd_btn.setIcon(QIcon(pix))

    # ── 登录逻辑 ──

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.information(self, '提示', '请输入用户名和密码')
            return
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        user = db.verify_user(username, password)
        if user:
            self.username = user.username
            self.user_role = user.role
            self.accept()
        else:
            QMessageBox.warning(self, '登录失败', '用户名或密码错误')

    # ── 注册逻辑 ──

    def _handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not username or not password or not confirm:
            QMessageBox.information(self, '提示', '请填写所有字段')
            return
        if password != confirm:
            QMessageBox.warning(self, '提示', '两次密码输入不一致')
            return

        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        success, msg = db.register_user(username, password)
        if success:
            QMessageBox.information(self, '成功', '注册成功，请登录')
            self.password_input.setText(password)
            self._switch_to_login()
        else:
            QMessageBox.warning(self, '注册失败', msg)

