"""
文件操作工具模块
"""
import os
import shutil
from datetime import datetime
from typing import Optional, List
from PyQt6.QtWidgets import QFileDialog, QMessageBox


def get_timestamp_filename(prefix: str = "result", extension: str = "jpg") -> str:
    """获取带时间戳的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def ensure_directory(path: str) -> bool:
    """确保目录存在，不存在则创建"""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def select_image_file(parent, title: str = "选择图片") -> Optional[str]:
    """选择图片文件"""
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        "",
        "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
    )
    return file_path if file_path else None


def select_video_file(parent, title: str = "选择视频") -> Optional[str]:
    """选择视频文件"""
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        "",
        "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
    )
    return file_path if file_path else None


def select_model_file(parent, title: str = "选择模型") -> Optional[str]:
    """选择模型文件"""
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        "",
        "模型文件 (*.pt);;所有文件 (*.*)"
    )
    return file_path if file_path else None


def save_file_dialog(parent, title: str = "保存文件", 
                     default_name: str = "result.jpg",
                     file_filter: str = "图片文件 (*.jpg *.png)") -> Optional[str]:
    """保存文件对话框"""
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        default_name,
        file_filter
    )
    return file_path if file_path else None


def copy_file(src: str, dst: str) -> bool:
    """复制文件"""
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"复制文件失败: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def list_files(directory: str, extensions: List[str] = None) -> List[str]:
    """列出目录下的文件"""
    try:
        if not os.path.exists(directory):
            return []
        
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                if extensions is None:
                    files.append(item_path)
                else:
                    ext = os.path.splitext(item)[1].lower()
                    if ext in [e.lower() for e in extensions]:
                        files.append(item_path)
        return files
    except Exception as e:
        print(f"列出文件失败: {e}")
        return []