"""基于 IoU 的简易目标跟踪器，用于跨帧去重。"""

from utils.image_utils import calculate_iou


class SimpleTracker:
    def __init__(self, iou_threshold=0.2, max_misses=10):
        self._tracks = []
        self._next_id = 0
        self._iou_threshold = iou_threshold
        self._max_misses = max_misses
        self._all_unique = []  # 所有出现过的唯一目标（去重后）

    def update(self, detections):
        """
        用当前帧的检测结果更新跟踪器。
        detections: list of dict, 每个 dict 包含 bbox, class_id, class_name, confidence
        返回: (new_count, matched_count) — 本帧新增的独立目标数 和 匹配到已有轨迹的数量
        """
        matched_track_idx = set()
        matched_det_idx = set()
        new_count = 0

        for i, det in enumerate(detections):
            best_iou = 0.0
            best_j = -1
            for j, track in enumerate(self._tracks):
                if j in matched_track_idx:
                    continue
                if det['class_id'] != track['class_id']:
                    continue
                iou = calculate_iou(det['bbox'], track['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_j = j

            if best_iou >= self._iou_threshold and best_j >= 0:
                self._tracks[best_j]['bbox'] = det['bbox']
                self._tracks[best_j]['confidence'] = max(
                    det['confidence'], self._tracks[best_j]['confidence']
                )
                self._tracks[best_j]['miss_count'] = 0
                matched_track_idx.add(best_j)
                matched_det_idx.add(i)
            else:
                track = {
                    'id': self._next_id,
                    'bbox': det['bbox'],
                    'class_id': det['class_id'],
                    'class_name': det['class_name'],
                    'confidence': det['confidence'],
                    'miss_count': 0,
                }
                self._next_id += 1
                self._tracks.append(track)
                self._all_unique.append(track)
                new_count += 1
                matched_det_idx.add(i)

        for j, track in enumerate(self._tracks):
            if j not in matched_track_idx:
                track['miss_count'] += 1

        self._tracks = [
            t for t in self._tracks if t['miss_count'] <= self._max_misses
        ]

        return new_count, len(matched_track_idx)

    @property
    def total_unique(self):
        return self._next_id

    @property
    def all_unique_detections(self):
        return list(self._all_unique)

    def reset(self):
        self._tracks.clear()
        self._all_unique.clear()
        self._next_id = 0
