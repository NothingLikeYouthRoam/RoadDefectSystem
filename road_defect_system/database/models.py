"""
数据库模型定义
"""
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List


@dataclass
class DetectionRecord:
    """检测记录数据模型"""
    id: Optional[int] = None
    timestamp: str = None
    type: str = "image"  # image/video/camera
    source: str = ""
    model_name: str = ""
    total_objects: int = 0
    class_distribution: str = ""  # "Manhole:2, Patch-Crack:2"
    details: str = ""  # JSON格式存储详细检测结果

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> 'DetectionRecord':
        """从字典创建实例"""
        return cls(**data)

    def get_class_distribution_dict(self) -> Dict[str, int]:
        """获取类别分布字典"""
        if not self.class_distribution:
            return {}
        result = {}
        for item in self.class_distribution.split(","):
            if ":" in item:
                cls, count = item.split(":")
                result[cls.strip()] = int(count)
        return result

    def get_details_list(self) -> List[Dict]:
        """获取详细检测结果列表"""
        if not self.details:
            return []
        try:
            return json.loads(self.details)
        except:
            return []


@dataclass
class User:
    """用户数据模型"""
    id: Optional[int] = None
    username: str = ""
    password: str = ""
    role: str = "user"
    create_time: str = None

    def __post_init__(self):
        if self.create_time is None:
            self.create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")