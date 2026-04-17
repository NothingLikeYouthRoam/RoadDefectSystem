"""
道路缺陷检测系统 - 主程序入口
基于 YOLOv8 和 PyQt6
"""
import sys
import PyQt6.QtWebEngineWidgets
from styles import AppStyles


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("道路缺陷检测系统")
    app.setApplicationVersion("1.0.0")
    app.setFont(QFont("Microsoft YaHei", 9))

    app.setStyleSheet(AppStyles.get_global_stylesheet())
    try:
        AppStyles.setup_matplotlib_style()
    except ImportError:
        pass

    from ui.login_dialog import LoginDialog
    from PyQt6.QtWidgets import QDialog

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        return
    username = getattr(login, 'username', 'admin')
    # 停掉登录页数字雨定时器，防止隐藏窗口仍占用事件循环
    rain = getattr(login, '_rain', None)
    if rain is not None:
        rain._timer.stop()
    del login

    from ui.main_window import MainWindow
    from PyQt6.QtWidgets import QMessageBox

    try:
        w = MainWindow(username)
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "错误", f"无法启动主窗口: {e}")


if __name__ == '__main__':
    main()
