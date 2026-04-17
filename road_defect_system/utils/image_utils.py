"""
图像处理工具模块
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


def extract_gps(image_path: str) -> Optional[Tuple[float, float]]:
    """从图片 EXIF 中提取 GPS 坐标，返回 (latitude, longitude) 或 None"""
    try:
        from PIL import Image
        from PIL.ExifTags import Base as ExifBase, GPSTAGS
        img = Image.open(image_path)
        exif = img.getexif()
        if not exif:
            return None

        gps_ifd = None
        for tag_id, value in exif.items():
            if tag_id == ExifBase.GPSInfo:
                gps_ifd = value
                break
        if not gps_ifd:
            return None

        # gps_ifd 可能是 dict 或 int (offset)
        if isinstance(gps_ifd, int):
            return None

        def _dms_to_dd(dms, ref):
            d, m, s = [float(v) if isinstance(v, (int, float)) else float(v.num) / float(v.den) for v in dms]
            dd = d + m / 60.0 + s / 3600.0
            if ref in ('S', 'W'):
                dd = -dd
            return dd

        lat_dms = gps_ifd.get(2)
        lat_ref = gps_ifd.get(1)
        lon_dms = gps_ifd.get(4)
        lon_ref = gps_ifd.get(3)

        if lat_dms and lat_ref and lon_dms and lon_ref:
            lat = _dms_to_dd(lat_dms, lat_ref)
            lon = _dms_to_dd(lon_dms, lon_ref)
            return (lat, lon)
    except Exception:
        pass
    return None


def numpy_to_qimage(image: np.ndarray) -> QImage:
    """将numpy数组转换为QImage"""
    if image is None:
        return QImage()

    if len(image.shape) == 2:
        height, width = image.shape
        bytes_per_line = width
        data = np.ascontiguousarray(image)
        qimg = QImage(data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        qimg._numpy_ref = data
        return qimg

    height, width, channel = image.shape
    bytes_per_line = channel * width

    if channel == 3:
        rgb_image = np.ascontiguousarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        qimg = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        qimg._numpy_ref = rgb_image
        return qimg
    elif channel == 4:
        rgba_image = np.ascontiguousarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA))
        qimg = QImage(rgba_image.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888)
        qimg._numpy_ref = rgba_image
        return qimg

    return QImage()


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    """将numpy数组转换为QPixmap"""
    qimage = numpy_to_qimage(image)
    return QPixmap.fromImage(qimage)


def qimage_to_numpy(qimage: QImage) -> Optional[np.ndarray]:
    """将QImage转换为numpy数组"""
    if qimage is None or qimage.isNull():
        return None
    
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
    width = qimage.width()
    height = qimage.height()
    
    ptr = qimage.bits()
    ptr.setsize(height * width * 4)
    arr = np.array(ptr).reshape(height, width, 4)
    
    return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)


def resize_image(image: np.ndarray, max_size: int = 1920) -> np.ndarray:
    """调整图像大小，保持宽高比"""
    if image is None:
        return None
    
    height, width = image.shape[:2]
    if max(height, width) <= max_size:
        return image
    
    scale = max_size / max(height, width)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)


def draw_detections(image: np.ndarray, detections: List[dict], 
                    font_scale: float = 0.5, thickness: int = 2) -> np.ndarray:
    """在图像上绘制检测框"""
    if image is None or not detections:
        return image
    
    result = image.copy()
    
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (128, 0, 0), (0, 128, 0), (0, 0, 128)
    ]
    
    for i, det in enumerate(detections):
        bbox = det.get('bbox', [])
        if len(bbox) != 4:
            continue
        
        x1, y1, x2, y2 = map(int, bbox)
        class_name = det.get('class_name', 'Unknown')
        confidence = det.get('confidence', 0)
        
        color = colors[det.get('class_id', 0) % len(colors)]
        
        cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
        
        label = f"{class_name} {confidence:.2f}"
        
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        
        cv2.rectangle(result, (x1, y1 - label_height - baseline - 5),
                     (x1 + label_width, y1), color, -1)
        
        cv2.putText(result, label, (x1, y1 - baseline - 2),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    return result


def create_result_image_with_stats(image: np.ndarray, detections: List[dict],
                                   class_names: List[str]) -> np.ndarray:
    """创建带有统计信息的检测结果图"""
    if image is None:
        return None
    
    h, w = image.shape[:2]
    panel_width = 300
    result = np.zeros((h, w + panel_width, 3), dtype=np.uint8)
    result[:h, :w] = image
    
    class_counts = {}
    confidences = []
    
    for det in detections:
        class_name = det.get('class_name', 'Unknown')
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(det.get('confidence', 0))
    
    y_offset = 30
    cv2.putText(result, f"检测结果: {len(detections)} 个目标", (w + 10, y_offset),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    y_offset += 30
    
    for cls, count in class_counts.items():
        cv2.putText(result, f"{cls}: {count}", (w + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 20
    
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        max_conf = max(confidences)
        y_offset += 20
        cv2.putText(result, f"平均置信度: {avg_conf:.2f}", (w + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 20
        cv2.putText(result, "最高置信度: {:.2f}".format(max_conf), (w + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return result


def capture_frame(video_capture) -> Optional[np.ndarray]:
    """从视频捕获中读取帧"""
    if video_capture is None or not video_capture.isOpened():
        return None
    
    ret, frame = video_capture.read()
    return frame if ret else None


def get_video_info(video_path: str) -> dict:
    """获取视频信息"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    
    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    }
    
    cap.release()
    return info


def get_severity(total_objects: int) -> tuple:
    """返回 (等级文字, 颜色hex)

    根据检测到的目标总数判定缺陷严重程度:
      - 总数 <= 2 : ('轻微', '#10B981')
      - 总数 <= 5 : ('中等', '#F59E0B')
      - 总数 >  5 : ('严重', '#EF4444')
    """
    if total_objects <= 2:
        return ('轻微', '#10B981')
    elif total_objects <= 5:
        return ('中等', '#F59E0B')
    else:
        return ('严重', '#EF4444')


def get_severity_color(severity: str) -> str:
    """返回严重程度对应的颜色代码"""
    severity_colors = {
        '轻微': '#10B981',
        '中等': '#F59E0B',
        '严重': '#EF4444',
    }
    return severity_colors.get(severity, '#8B9AB5')


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """计算两个框的IoU"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)
    
    inter_width = max(0, inter_x_max - inter_x_min)
    inter_height = max(0, inter_y_max - inter_y_min)
    inter_area = inter_width * inter_height
    
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0