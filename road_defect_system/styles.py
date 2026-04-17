from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QPixmap, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect


class AppStyles:
    """应用程序样式定义 - 深色科技风格"""

    COLORS = {
        # ── Backgrounds (dark → light) ──
        'background_main': '#0C1017',
        'background_secondary': '#121820',
        'background_card': '#171E28',
        'background_elevated': '#1C2433',
        'background_hover': '#232D3F',
        # ── Borders ──
        'border': '#262F3D',
        'border_light': '#313D50',
        'border_focus': '#3B82F6',
        # ── Primary: Blue ──
        'gradient_start': '#3B82F6',
        'gradient_end': '#2563EB',
        'gradient_hover_start': '#60A5FA',
        'gradient_hover_end': '#3B82F6',
        'gradient_pressed_start': '#2563EB',
        'gradient_pressed_end': '#1D4ED8',
        # ── Accent palette ──
        'accent_cyan': '#06B6D4',
        'accent_purple': '#8B5CF6',
        'accent_amber': '#F59E0B',
        # ── Semantic ──
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444',
        'info': '#06B6D4',
        # ── Text ──
        'text_primary': '#F1F5F9',
        'text_secondary': '#8B9AB5',
        'text_disabled': '#5A6A80',
        # ── Misc ──
        'glow_blue': 'rgba(59, 130, 246, 0.30)',
        'surface_gradient_top': '#1A2230',
        'surface_gradient_bottom': '#141B24',
    }

    BORDER_RADIUS = {
        'panel': 12,
        'card': 12,
        'group': 8,
        'button': 6,
        'button_large': 10,
        'input': 6,
        'small': 4,
        'badge': 4,
        'pill': 14,
    }

    SPACING = {
        'page_margin': 20,
        'card_padding': 16,
        'group_padding': 14,
        'widget_gap': 12,
        'tight': 8,
        'section': 20,
    }

    # ── Icon drawing ──────────────────────────────────────────────

    @staticmethod
    def create_icon(icon_type, size=20, color=None):
        if color is None:
            color = QColor(139, 154, 181)
        elif isinstance(color, str):
            color = QColor(color)

        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, max(1.5, size / 12), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        s = size
        m = s * 0.15

        if icon_type == 'image':
            p.drawRoundedRect(int(m), int(m), int(s - 2*m), int(s - 2*m), 2, 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            pts = [int(m + s*0.1), int(s - m - s*0.05), int(s*0.45), int(m + s*0.35), int(s*0.55), int(m + s*0.35)]
            p.drawPolygon(QPolygonF([QPointF(pts[0], pts[1]), QPointF(pts[2], pts[3]), QPointF(pts[4], pts[5])]))
            pts2 = [int(s*0.45), int(s - m - s*0.05), int(s*0.7), int(m + s*0.45), int(s - m - s*0.1), int(s - m - s*0.05)]
            p.drawPolygon(QPolygonF([QPointF(pts2[0], pts2[1]), QPointF(pts2[2], pts2[3]), QPointF(pts2[4], pts2[5])]))
            p.drawEllipse(int(s*0.62), int(m + s*0.12), int(s*0.16), int(s*0.16))

        elif icon_type == 'video':
            p.drawRoundedRect(int(m), int(m), int(s - 2*m), int(s - 2*m), 2, 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            cx, cy = s/2, s/2
            r = s * 0.18
            tri = QPolygonF([QPointF(cx - r*0.6, cy - r), QPointF(cx - r*0.6, cy + r), QPointF(cx + r, cy)])
            p.drawPolygon(tri)

        elif icon_type == 'camera':
            bw, bh, by = s - 2*m, s * 0.5, s * 0.38
            p.drawRoundedRect(int(m), int(by), int(bw), int(bh), 3, 3)
            p.drawRect(int(s*0.35), int(by - s*0.08), int(s*0.3), int(s*0.1))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(int(s*0.35), int(by + bh*0.15), int(s*0.3), int(s*0.3))
            inner = QColor(color); inner.setAlpha(60)
            p.setBrush(QBrush(inner))
            p.drawEllipse(int(s*0.4), int(by + bh*0.22), int(s*0.2), int(s*0.2))

        elif icon_type == 'history':
            cx, cy, r = s/2, s/2, (s - 2*m)/2
            p.drawEllipse(int(cx - r), int(cy - r), int(2*r), int(2*r))
            p.drawLine(int(cx), int(cy), int(cx), int(cy - r*0.55))
            p.drawLine(int(cx), int(cy), int(cx + r*0.45), int(cy - r*0.1))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(int(cx - 1.5), int(cy - 1.5), 3, 3)

        elif icon_type == 'model':
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(color))
            cols = [s*0.25, s*0.5, s*0.75]
            rows = [[s*0.3, s*0.5, s*0.7], [s*0.35, s*0.65], [s*0.3, s*0.5, s*0.7]]
            dot_r = max(2, s * 0.07)
            p.setPen(QPen(color, max(1, s/20)))
            for ci, (col, row_list) in enumerate(zip(cols, rows)):
                for ry in row_list:
                    if ci < 2:
                        for ry2 in rows[ci + 1]:
                            p.drawLine(int(col), int(ry), int(cols[ci+1]), int(ry2))
            p.setPen(Qt.PenStyle.NoPen)
            for ci, (col, row_list) in enumerate(zip(cols, rows)):
                for ry in row_list:
                    p.drawEllipse(int(col - dot_r), int(ry - dot_r), int(2*dot_r), int(2*dot_r))

        elif icon_type == 'metrics':
            bar_w = (s - 2*m - 2*3) / 3
            heights = [0.5, 0.8, 0.35]
            base_y = s - m
            p.setPen(Qt.PenStyle.NoPen)
            for i, h in enumerate(heights):
                bx = m + i * (bar_w + 3)
                bh = (s - 2*m) * h
                p.setBrush(QBrush(color))
                p.drawRoundedRect(int(bx), int(base_y - bh), int(bar_w), int(bh), 2, 2)

        elif icon_type == 'road':
            p.setPen(QPen(color, max(1.5, s/12)))
            p.drawLine(int(s*0.5), int(m), int(s*0.2), int(s - m))
            p.drawLine(int(s*0.5), int(m), int(s*0.8), int(s - m))
            pen2 = QPen(color, max(1, s/16), Qt.PenStyle.DashLine)
            p.setPen(pen2)
            p.drawLine(int(s*0.5), int(s*0.35), int(s*0.5), int(s*0.8))

        elif icon_type == 'chart_placeholder':
            p.drawRoundedRect(int(m), int(m), int(s - 2*m), int(s - 2*m), 4, 4)
            p.setPen(QPen(color, max(1.5, s/14)))
            path = QPainterPath()
            path.moveTo(int(s*0.2), int(s*0.7)); path.lineTo(int(s*0.4), int(s*0.35))
            path.lineTo(int(s*0.6), int(s*0.55)); path.lineTo(int(s*0.8), int(s*0.3))
            p.drawPath(path)

        p.end()
        return pix

    # ── Component style helpers ───────────────────────────────────

    @staticmethod
    def get_groupbox_style(variant='default'):
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QGroupBox {{
                background: {c['background_elevated']};
                border: 1px solid {c['border']};
                border-radius: {r['group']}px;
                padding: 14px;
                padding-top: 22px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                color: {c['text_primary']};
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                font-size: 13px;
            }}
        """

    @staticmethod
    def get_button_style(variant='primary', size='default'):
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        h = '32px' if size == 'small' else ('42px' if size == 'large' else '36px')
        if variant == 'primary':
            return f"""
                QPushButton {{
                    background: {c['gradient_start']};
                    color: white; border: 1.5px solid transparent; border-radius: {r['button']}px;
                    padding: 0 18px; font-weight: 600; min-height: {h};
                }}
                QPushButton:hover {{
                    background: {c['gradient_hover_start']};
                }}
                QPushButton:pressed {{
                    background: {c['gradient_pressed_start']};
                }}
                QPushButton:disabled {{ background: {c['background_hover']}; color: {c['text_disabled']}; }}
            """
        elif variant == 'success':
            return f"""
                QPushButton {{
                    background-color: {c['success']}; color: white; border: 1.5px solid transparent;
                    border-radius: {r['button']}px; padding: 0 18px; font-weight: 600; min-height: {h};
                }}
                QPushButton:hover {{ background-color: #34D399; }}
                QPushButton:pressed {{ background-color: #059669; }}
            """
        elif variant == 'danger':
            return f"""
                QPushButton {{
                    background-color: {c['error']}; color: white; border: 1.5px solid transparent;
                    border-radius: {r['button']}px; padding: 0 18px; font-weight: 600; min-height: {h};
                }}
                QPushButton:hover {{ background-color: #F87171; }}
                QPushButton:pressed {{ background-color: #DC2626; }}
            """
        elif variant == 'outline':
            return f"""
                QPushButton {{
                    background-color: transparent; color: {c['gradient_start']};
                    border: 1.5px solid {c['gradient_start']}; border-radius: {r['button']}px;
                    padding: 0 18px; font-weight: 500; min-height: {h};
                }}
                QPushButton:hover {{
                    background-color: rgba(59, 130, 246, 0.08);
                }}
                QPushButton:pressed {{
                    background-color: rgba(59, 130, 246, 0.16);
                }}
            """
        elif variant == 'ghost':
            return f"""
                QPushButton {{
                    background-color: transparent; color: {c['text_secondary']};
                    border: 1.5px solid transparent; border-radius: {r['button']}px;
                    padding: 0 18px; font-weight: 500; min-height: {h};
                }}
                QPushButton:hover {{
                    background-color: {c['background_hover']}; color: {c['text_primary']};
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.08);
                }}
            """
        return ''

    @staticmethod
    def get_input_style():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QLineEdit {{
                background-color: {c['background_secondary']};
                border: 1.5px solid {c['border']}; border-radius: {r['input']}px;
                padding: 8px 12px; color: {c['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {c['gradient_start']}; background-color: {c['background_card']}; }}
            QLineEdit:disabled {{ background-color: {c['background_main']}; color: {c['text_disabled']}; }}
            QLineEdit::placeholder {{ color: {c['text_disabled']}; }}
        """

    @staticmethod
    def get_combobox_style():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QComboBox {{
                background-color: {c['background_secondary']};
                border: 1.5px solid {c['border']}; border-radius: {r['input']}px;
                padding: 6px 12px; color: {c['text_primary']};
            }}
            QComboBox:hover {{ border-color: {c['border_light']}; }}
            QComboBox:focus {{ border-color: {c['gradient_start']}; }}
            QComboBox QAbstractItemView {{
                background-color: {c['background_card']}; border: 1px solid {c['border']};
                selection-background-color: rgba(59, 130, 246, 0.25);
                selection-color: {c['text_primary']}; border-radius: {r['input']}px; padding: 4px;
            }}
        """

    @staticmethod
    def get_spinbox_style():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QDoubleSpinBox, QSpinBox {{
                background-color: {c['background_secondary']};
                border: 1.5px solid {c['border']}; border-radius: {r['input']}px;
                color: {c['text_primary']}; padding: 6px 8px;
            }}
            QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {c['gradient_start']}; }}
        """

    @staticmethod
    def get_panel_style():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            background: {c['background_card']};
            border: 1px solid {c['border']};
            border-radius: {r['panel']}px;
        """

    @staticmethod
    def get_table_style():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QTableWidget {{
                background-color: {c['background_card']};
                border: 1px solid {c['border']}; border-radius: {r['small']}px;
                gridline-color: {c['border']};
                alternate-background-color: {c['background_elevated']};
            }}
            QTableWidget::item {{
                color: {c['text_primary']}; padding: 8px 10px;
                border-bottom: 1px solid {c['border']};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(59, 130, 246, 0.15); color: white;
            }}
            QHeaderView::section {{
                background-color: {c['background_secondary']};
                color: {c['text_secondary']}; padding: 10px 8px;
                border: none; border-bottom: 1px solid {c['border_light']}; font-weight: 600;
            }}
        """

    @staticmethod
    def get_stat_card_style(accent_color):
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
            QWidget {{
                background: {c['background_elevated']};
                border: 1px solid {c['border']};
                border-left: 3px solid {accent_color};
                border-radius: {r['small']}px;
                padding: 14px 16px;
            }}
        """

    # ── Shadow helpers ────────────────────────────────────────────

    @staticmethod
    def apply_shadow(widget, blur=20, offset=3, color=None, opacity=50):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, offset)
        if color is None:
            color = QColor(0, 0, 0); color.setAlpha(opacity)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)
        return shadow

    @staticmethod
    def apply_blue_glow(widget, blur=25, opacity=40):
        color = QColor(59, 130, 246); color.setAlpha(opacity)
        return AppStyles.apply_shadow(widget, blur, 2, color)

    # ── Stat card ─────────────────────────────────────────────────

    @staticmethod
    def create_stat_card(title, value, accent_color):
        c = AppStyles.COLORS
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_stat_card_style(accent_color))
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        value_label = QLabel(value)
        value_label.setFont(QFont('Microsoft YaHei', 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f'color: {accent_color}; border: none;')

        title_label = QLabel(title)
        title_label.setFont(QFont('Microsoft YaHei', 9))
        title_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')

        layout.addWidget(value_label)
        layout.addStretch()
        layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignBottom)

        return {'widget': widget, 'value': value_label}

    # ── Empty state ───────────────────────────────────────────────

    @staticmethod
    def create_empty_state(text='暂无数据', icon_type='chart_placeholder'):
        c = AppStyles.COLORS
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_pix = AppStyles.create_icon(icon_type, 48, QColor(c['text_secondary']))
        icon_label.setPixmap(icon_pix)
        icon_label.setStyleSheet('border: none;')

        text_label = QLabel(text)
        text_label.setFont(QFont('Microsoft YaHei', 10))
        text_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label, 0, Qt.AlignmentFlag.AlignCenter)
        return widget

    # ── Placeholder ───────────────────────────────────────────────

    @staticmethod
    def create_placeholder(text='点击下方按钮开始', icon_type='image'):
        c = AppStyles.COLORS
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_pix = AppStyles.create_icon(icon_type, 44, QColor(c['text_secondary']))
        icon_label.setPixmap(icon_pix)
        icon_label.setStyleSheet('border: none;')

        text_label = QLabel(text)
        text_label.setFont(QFont('Microsoft YaHei', 11))
        text_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        widget.setStyleSheet(f'''
            background-color: {c["background_card"]};
            border: 1.5px dashed {c["border_light"]}; border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
        ''')
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label, 0, Qt.AlignmentFlag.AlignCenter)
        widget.setMinimumHeight(120)
        return widget

    # ── Global stylesheet ─────────────────────────────────────────

    @staticmethod
    def get_global_stylesheet():
        c = AppStyles.COLORS
        r = AppStyles.BORDER_RADIUS
        return f"""
        QMainWindow {{ background-color: {c['background_main']}; }}

        QWidget {{ color: {c['text_primary']}; }}

        QLabel {{ color: {c['text_primary']}; font-size: 13px; }}

        QToolTip {{
            background-color: {c['background_elevated']};
            color: {c['text_primary']}; border: 1px solid {c['border_light']};
            border-radius: {r['small']}px; padding: 6px 10px; font-size: 12px;
        }}

        QPushButton {{
            background-color: {c['background_elevated']};
            color: {c['text_secondary']}; border: 1px solid {c['border']};
            border-radius: {r['button']}px; padding: 0 16px; font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {c['background_hover']}; color: {c['text_primary']}; }}
        QPushButton:pressed {{ background-color: rgba(255,255,255,0.05); }}
        QPushButton:disabled {{ background-color: {c['background_secondary']}; color: {c['text_disabled']}; }}

        QLineEdit {{
            background-color: {c['background_secondary']}; color: {c['text_primary']};
            border: 1.5px solid {c['border']}; border-radius: {r['input']}px;
            padding: 10px 14px; font-size: 13px;
        }}
        QLineEdit:focus {{ border-color: {c['gradient_start']}; background-color: {c['background_card']}; }}
        QLineEdit::placeholder {{ color: {c['text_disabled']}; }}

        QCheckBox {{ color: {c['text_primary']}; spacing: 8px; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px; border: 1.5px solid {c['border_light']};
            border-radius: 4px; background-color: {c['background_secondary']};
        }}
        QCheckBox::indicator:hover {{ border-color: {c['gradient_start']}; }}
        QCheckBox::indicator:checked {{
            background-color: {c['gradient_start']}; border-color: {c['gradient_start']};
        }}

        QRadioButton {{ color: {c['text_primary']}; spacing: 8px; }}
        QRadioButton::indicator {{
            width: 18px; height: 18px; border: 1.5px solid {c['border_light']};
            border-radius: 9px; background-color: {c['background_secondary']};
        }}
        QRadioButton::indicator:hover {{ border-color: {c['gradient_start']}; }}
        QRadioButton::indicator:checked {{
            background-color: {c['gradient_start']}; border: 3px solid {c['background_elevated']};
        }}

        QTableWidget {{
            background-color: {c['background_card']}; border: 1px solid {c['border']};
            border-radius: {r['small']}px; gridline-color: {c['border']};
            alternate-background-color: {c['background_elevated']}; outline: none;
        }}
        QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {c['border']}; }}
        QTableWidget::item:selected {{ background-color: rgba(59,130,246,0.15); }}
        QHeaderView::section {{
            background-color: {c['background_secondary']}; color: {c['text_secondary']};
            padding: 10px; border: none; border-bottom: 1px solid {c['border_light']}; font-weight: 600;
        }}
        QTableWidget::verticalHeader {{ background-color: {c['background_secondary']}; color: {c['text_disabled']}; }}

        QTabWidget::pane {{
            border: 1px solid {c['border']}; border-radius: {r['panel']}px;
            background-color: {c['background_card']}; top: -1px;
        }}
        QTabBar::tab {{
            background-color: {c['background_elevated']}; color: {c['text_secondary']};
            padding: 10px 24px; border: none;
            border-top-left-radius: {r['small']}px; border-top-right-radius: {r['small']}px;
            margin-right: 2px; font-weight: 500;
        }}
        QTabBar::tab:selected {{
            background-color: {c['gradient_start']}; color: white;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {c['background_hover']}; color: {c['text_primary']};
        }}

        QGroupBox {{
            background-color: {c['background_elevated']}; border: 1px solid {c['border']};
            border-radius: {r['group']}px; margin-top: 22px; padding-top: 18px;
            color: {c['text_primary']}; font-weight: 600;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}

        QProgressBar {{
            background-color: {c['background_secondary']}; border: none;
            border-radius: 4px; height: 6px;
        }}
        QProgressBar::chunk {{
            background-color: {c['gradient_start']}; border-radius: 4px;
        }}

        QComboBox {{
            background-color: {c['background_secondary']}; color: {c['text_primary']};
            border: 1.5px solid {c['border']}; border-radius: {r['input']}px; padding: 8px 12px;
        }}
        QComboBox:hover {{ border-color: {c['border_light']}; }}
        QComboBox:focus {{ border-color: {c['gradient_start']}; }}
        QComboBox QAbstractItemView {{
            background-color: {c['background_card']}; border: 1px solid {c['border']};
            selection-background-color: rgba(59,130,246,0.25);
        }}

        QScrollBar:vertical {{
            background: transparent; width: 6px; border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background-color: rgba(42,49,66,0.6); border-radius: 3px; min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{ background-color: {c['gradient_start']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

        QScrollBar:horizontal {{
            background: transparent; height: 6px; border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: rgba(42,49,66,0.6); border-radius: 3px; min-width: 30px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

        QStatusBar {{
            background-color: {c['background_secondary']}; color: {c['text_disabled']};
            border-top: 1px solid {c['border']}; font-size: 12px;
        }}

        QMessageBox {{ background-color: {c['background_card']}; }}
        QMessageBox QLabel {{ color: {c['text_primary']}; }}

        QDialog {{
            background-color: {c['background_main']};
        }}

        QDoubleSpinBox, QSpinBox {{
            background-color: {c['background_secondary']}; color: {c['text_primary']};
            border: 1.5px solid {c['border']}; border-radius: {r['input']}px; padding: 6px;
        }}
        QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {c['gradient_start']}; }}

        QTextBrowser {{
            background-color: {c['background_elevated']}; border: 1px solid {c['border']};
            border-radius: {r['small']}px; color: {c['text_secondary']};
        }}

        QScrollArea {{ border: none; background: transparent; }}
        """

    @staticmethod
    def setup_matplotlib_style():
        import matplotlib.pyplot as plt
        plt.rcParams.update({
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
            'axes.prop_cycle': plt.cycler('color', ['#3B82F6', '#10B981', '#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444'])
        })
