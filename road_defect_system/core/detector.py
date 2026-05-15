"""
YOLOv8 道路缺陷检测器封装类
"""
import os
from typing import Optional, List, Tuple
import numpy as np
from ultralytics import YOLO

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "best.pt")


class RoadDefectDetector:
    """道路缺陷检测器"""

    _instance = None
    _model = None
    _model_path = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH,
                 conf_thres: float = 0.25,
                 iou_thres: float = 0.45,
                 max_det: int = 300):
        # 延迟加载模型，避免初始化阶段阻塞 UI
        self.model_path = model_path
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.max_det = max_det
        self.class_names = []
        self._model = None
        self._model_path = model_path
    
    def load_model(self, model_path: str) -> bool:
        """加载YOLO模型"""
        try:
            if not os.path.exists(model_path):
                return False
            
            self._model = YOLO(model_path)
            self._model_path = model_path
            
            if hasattr(self._model, 'model') and hasattr(self._model.model, 'names'):
                self.class_names = list(self._model.model.names.values())
            else:
                self.class_names = ["Crack", "Manhole", "Net", "Pothole", 
                                   "Patch-Crack", "Patch-Net", "Patch-Pothole", 
                                   "other", "Other"]
            
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False
    
    def detect(self, image: np.ndarray) -> Optional[object]:
        """
        对图像进行检测
        
        Args:
            image: numpy数组 (BGR格式)
            
        Returns:
            ultralytics Results 对象
        """
        if self._model is None:
            # 尝试按预设路径加载模型（懒加载）
            if self._model_path is None:
                self._model_path = self.model_path
            loaded = self.load_model(self._model_path)
            if not loaded:
                return None
        
        try:
            results = self._model.predict(
                image,
                conf=self.conf_thres,
                iou=self.iou_thres,
                max_det=self.max_det,
                device=self.device,
                verbose=False
            )
            return results[0] if results else None
        except Exception as e:
            print(f"检测失败: {e}")
            return None
    
    def detect_batch(self, images: List[np.ndarray]) -> List[object]:
        """批量检测"""
        if self._model is None:
            return []
        
        try:
            results = self._model.predict(
                images,
                conf=self.conf_thres,
                iou=self.iou_thres,
                max_det=self.max_det,
                device=self.device,
                verbose=False
            )
            return results
        except Exception as e:
            print(f"批量检测失败: {e}")
            return []
    
    def set_conf_thres(self, conf: float):
        """设置置信度阈值"""
        self.conf_thres = max(0.0, min(1.0, conf))
    
    def set_iou_thres(self, iou: float):
        """设置IoU阈值"""
        self.iou_thres = max(0.0, min(1.0, iou))
    
    def set_max_det(self, max_det: int):
        """设置最大检测数"""
        self.max_det = max(1, max_det)

    def set_device(self, device: str):
        """设置推理设备: 'cpu' or 'cuda'"""
        self._device = device

    @property
    def device(self):
        return getattr(self, '_device', 'cpu')
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_path": self._model_path,
            "class_names": self.class_names,
            "conf_thres": self.conf_thres,
            "iou_thres": self.iou_thres,
            "max_det": self.max_det,
            "loaded": self._model is not None
        }
    
    def parse_results(self, results) -> Tuple[List[dict], np.ndarray]:
        """
        解析检测结果
        
        Returns:
            检测结果列表, 标注后的图像
        """
        if results is None:
            return [], None
        
        detections = []
        
        if results.boxes is not None:
            boxes = results.boxes.xyxy.cpu().numpy()
            confidences = results.boxes.conf.cpu().numpy()
            class_ids = results.boxes.cls.cpu().numpy().astype(int)
            
            for i in range(len(boxes)):
                detection = {
                    "class_id": int(class_ids[i]),
                    "class_name": self.class_names[int(class_ids[i])] if int(class_ids[i]) < len(self.class_names) else "Unknown",
                    "confidence": float(confidences[i]),
                    "bbox": boxes[i].tolist()
                }
                detections.append(detection)
        
        annotated_image = None
        if hasattr(results, 'plot'):
            try:
                annotated_image = results.plot()
            except Exception:
                annotated_image = None
        
        return detections, annotated_image
    
    @classmethod
    def get_instance(cls) -> 'RoadDefectDetector':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例"""
        cls._instance = None
        cls._model = None
        cls._model_path = None
