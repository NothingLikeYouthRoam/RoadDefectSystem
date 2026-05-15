from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, QSplitter,
    QFileDialog, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication
from styles import AppStyles


class DetectImagePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_path = None
        self._gps = None  # (lat, lon) or None
        self._annotated_image = None  # numpy annotated image for export
        self._display_size = None     # 缓存展示区尺寸，固定不变
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        splitter.setHandleWidth(1)
        c = AppStyles.COLORS
        splitter.setStyleSheet(f'QSplitter::handle {{ background-color: {c["border"]}; }}')

        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)

        right_widget = self._create_right_panel()
        splitter.addWidget(right_widget)

        layout.addWidget(splitter)

    def _create_left_panel(self):
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        preview_group = QGroupBox('图片预览')
        preview_group.setStyleSheet(AppStyles.get_groupbox_style())

        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(12)

        self.image_label = AppStyles.create_placeholder('点击下方按钮选择图片', 'image')
        self.image_label.setMinimumHeight(350)
        preview_layout.addWidget(self.image_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_configs = [
            ('打开图片', 'outline', self._on_open_image),
            ('批量检测', 'success', self._on_batch_detect),
            ('开始检测', 'primary', self._on_start_detect),
            ('导出图片', 'ghost', self._on_export_image),
            ('清除', 'ghost', self._on_clear),
        ]

        for text, variant, func in btn_configs:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            btn.setMinimumWidth(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont('Microsoft YaHei', 9))
            btn.setStyleSheet(AppStyles.get_button_style(variant))
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)

        preview_layout.addLayout(btn_layout)
        layout.addWidget(preview_group, 1)
        return widget

    def _create_right_panel(self):
        widget = QWidget()
        widget.setStyleSheet(AppStyles.get_panel_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # GPS 位置信息
        gps_group = QGroupBox('位置信息')
        gps_group.setStyleSheet(AppStyles.get_groupbox_style())
        gps_layout = QVBoxLayout(gps_group)
        gps_layout.setSpacing(6)

        # 第一行：GPS显示
        self.gps_label = QLabel('无位置信息')
        self.gps_label.setFont(QFont('Microsoft YaHei', 9))
        c = AppStyles.COLORS
        self.gps_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        gps_layout.addWidget(self.gps_label)

        # 第二行：手动输入经纬度（两行布局，避免右侧面板过窄）
        from PyQt6.QtWidgets import QLineEdit

        coord_row1 = QHBoxLayout()
        coord_row1.setSpacing(6)
        lat_label = QLabel('纬度:')
        lat_label.setFont(QFont('Microsoft YaHei', 9))
        lat_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        coord_row1.addWidget(lat_label)
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText('39.9042')
        self.lat_input.setStyleSheet(AppStyles.get_input_style())
        coord_row1.addWidget(self.lat_input, 1)
        gps_layout.addLayout(coord_row1)

        coord_row2 = QHBoxLayout()
        coord_row2.setSpacing(6)
        lon_label = QLabel('经度:')
        lon_label.setFont(QFont('Microsoft YaHei', 9))
        lon_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        coord_row2.addWidget(lon_label)
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText('116.3974')
        self.lon_input.setStyleSheet(AppStyles.get_input_style())
        coord_row2.addWidget(self.lon_input, 1)
        btn_apply_gps = QPushButton('应用坐标')
        btn_apply_gps.setFixedHeight(28)
        btn_apply_gps.setFont(QFont('Microsoft YaHei', 9))
        btn_apply_gps.setStyleSheet(AppStyles.get_button_style('outline'))
        btn_apply_gps.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_apply_gps.clicked.connect(self._on_apply_manual_gps)
        coord_row2.addWidget(btn_apply_gps)
        gps_layout.addLayout(coord_row2)
        layout.addWidget(gps_group)

        # 统计卡片（紧凑2行布局）
        stats_group = QGroupBox('统计摘要')
        stats_group.setStyleSheet(AppStyles.get_groupbox_style())
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(4)
        stats_layout.setContentsMargins(6, 4, 6, 4)

        self.stat_labels = {}
        stat_configs = [
            ('total', '总检测数', '0', AppStyles.COLORS['gradient_start']),
            ('classes', '类别数', '0', AppStyles.COLORS['gradient_end']),
            ('avg_conf', '平均置信度', '0.00', AppStyles.COLORS['success']),
            ('max_conf', '最高置信度', '0.00', AppStyles.COLORS['warning']),
        ]

        for idx, (key, title, value, color) in enumerate(stat_configs):
            card = AppStyles.create_stat_card(title, value, color)
            self.stat_labels[key] = card['value']
            stats_layout.addWidget(card['widget'], idx // 2, idx % 2)

        # 严重程度卡片（占满一行）
        severity_card = AppStyles.create_stat_card('严重程度', '--', '#8B9AB5')
        self.stat_labels['severity'] = severity_card['value']
        self._severity_widget = severity_card['widget']
        stats_layout.addWidget(severity_card['widget'], 2, 0, 1, 2)

        layout.addWidget(stats_group)

        # 类别分布图表
        chart_group = QGroupBox('类别分布')
        chart_group.setStyleSheet(AppStyles.get_groupbox_style())
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(4, 4, 4, 4)
        self.chart_container = QWidget()
        self.chart_container_layout = QVBoxLayout(self.chart_container)
        self.chart_container_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_container_layout.setSpacing(0)
        chart_placeholder = AppStyles.create_empty_state('暂无图表数据', 'chart_placeholder')
        self.chart_container_layout.addWidget(chart_placeholder)
        self.chart_container.setFixedHeight(120)
        chart_layout.addWidget(self.chart_container)
        layout.addWidget(chart_group)

        # 检测结果表格
        result_group = QGroupBox('检测结果列表')
        result_group.setStyleSheet(AppStyles.get_groupbox_style())
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(['类别', '置信度', '坐标'])
        self.result_table.setRowCount(0)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFont(QFont('Microsoft YaHei', 9))
        self.result_table.setStyleSheet(AppStyles.get_table_style())
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.verticalHeader().setDefaultSectionSize(28)
        result_layout.addWidget(self.result_table)
        layout.addWidget(result_group, 1)
        return widget

    # ── 功能实现 ──

    def _set_image_widget(self, new_widget):
        """替换图片显示区域的 widget"""
        old = self.image_label
        parent_layout = old.parent().layout()
        idx = parent_layout.indexOf(old)
        parent_layout.removeWidget(old)
        old.deleteLater()
        parent_layout.insertWidget(idx, new_widget)
        self.image_label = new_widget

    def _on_open_image(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择图片', '', '图片文件 (*.png *.jpg *.jpeg *.bmp)'
        )
        if not file_path:
            return
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '错误', '无法加载图片')
            return

        self._image_path = file_path
        self._annotated_image = None
        self._gps = None

        # 提取 GPS
        from utils.image_utils import extract_gps
        gps = extract_gps(file_path)
        c = AppStyles.COLORS
        if gps:
            self._gps = gps
            self.gps_label.setText(f'{gps[0]:.6f}, {gps[1]:.6f}')
            self.gps_label.setStyleSheet(f'color: {c["success"]}; border: none;')
            self.lat_input.setText(f'{gps[0]:.6f}')
            self.lon_input.setText(f'{gps[1]:.6f}')
        else:
            self._gps = None
            self.gps_label.setText('无位置信息')
            self.gps_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
            self.lat_input.clear()
            self.lon_input.clear()

        # 首次打开：记下 placeholder 占据的区域尺寸，之后始终用这个尺寸
        if self._display_size is None:
            sz = self.image_label.size()
            if sz.width() < 10 or sz.height() < 10:
                sz = self.image_label.parent().size()
            self._display_size = sz

        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(350)
        scaled = pixmap.scaled(
            self._display_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled)
        c = AppStyles.COLORS
        label.setStyleSheet(f'''
            background-color: {c["background_main"]};
            border: 2px solid {c["border_focus"]};
            border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
        ''')
        self._set_image_widget(label)

    def _on_start_detect(self):
        from PyQt6.QtWidgets import QMessageBox

        if not self._image_path:
            QMessageBox.information(self, '提示', '请先选择一张图片')
            return

        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()

        # 确保模型已加载
        if not detector._model:
            from core.detector import DEFAULT_MODEL_PATH
            model_path = DEFAULT_MODEL_PATH
            import os
            if not os.path.exists(model_path):
                QMessageBox.warning(self, '错误', f'模型文件不存在: {model_path}\n请先在模型管理中加载模型')
                return
            try:
                detector.load_model(model_path)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'模型加载失败: {e}')
                return

        try:
            import cv2
            import numpy as np

            # 读取图片
            img = cv2.imread(self._image_path)
            if img is None:
                QMessageBox.warning(self, '错误', '无法读取图片文件')
                return

            # 运行检测 — detect() 返回单个 Result，parse_results() 返回 (detections, annotated_image)
            result = detector.detect(img)
            if result is None:
                QMessageBox.warning(self, '错误', '检测失败')
                return

            detections, annotated_bgr = detector.parse_results(result)

            if not detections:
                QMessageBox.information(self, '结果', '未检测到目标')
                self._update_stats(0, 0, 0.0, 0.0)
                self.result_table.setRowCount(0)
                return

            self._annotated_image = annotated_bgr

            # 显示标注后的图片（与预览同尺寸）
            if annotated_bgr is not None:
                from utils.image_utils import numpy_to_qpixmap
                annotated_qt = numpy_to_qpixmap(annotated_bgr)
                label = QLabel()
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setMinimumHeight(350)
                # 用缓存的固定展示区尺寸，不随图片大小变化
                target = self._display_size if self._display_size is not None else annotated_qt.size()
                scaled = annotated_qt.scaled(
                    target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled)
                c = AppStyles.COLORS
                label.setStyleSheet(f'''
                    background-color: {c["background_main"]};
                    border: 2px solid {c["success"]};
                    border-radius: {AppStyles.BORDER_RADIUS["panel"]}px;
                ''')
                self._set_image_widget(label)

            # 更新统计
            total = len(detections)
            class_set = set(d['class_name'] for d in detections)
            confidences = [d['confidence'] for d in detections]
            avg_conf = sum(confidences) / total
            max_conf = max(confidences)
            self._update_stats(total, len(class_set), avg_conf, max_conf)

            # 更新严重程度
            from utils.image_utils import get_severity
            sev_text, sev_color = get_severity(total)
            self.stat_labels['severity'].setText(sev_text)
            self.stat_labels['severity'].setStyleSheet(f'color: {sev_color}; border: none;')
            self._severity_widget.setStyleSheet(AppStyles.get_stat_card_style(sev_color))

            # 更新表格
            self.result_table.setRowCount(total)
            for row, d in enumerate(detections):
                x1, y1, x2, y2 = d['bbox']
                for col, val in enumerate([
                    d['class_name'],
                    f"{d['confidence']:.2f}",
                    f"({x1}, {y1}, {x2}, {y2})"
                ]):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.result_table.setItem(row, col, item)

            # 更新图表
            self._update_chart(detections)

            # 保存到数据库
            self._save_record(detections)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'检测失败: {e}')

    def _update_stats(self, total, classes, avg_conf, max_conf):
        self.stat_labels['total'].setText(str(total))
        self.stat_labels['classes'].setText(str(classes))
        self.stat_labels['avg_conf'].setText(f'{avg_conf:.2f}')
        self.stat_labels['max_conf'].setText(f'{max_conf:.2f}')

    def _update_chart(self, detections):
        # 清除旧图表
        while self.chart_container_layout.count():
            item = self.chart_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 统计类别分布
        class_count = {}
        for d in detections:
            name = d['class_name']
            class_count[name] = class_count.get(name, 0) + 1

        if class_count:
            from core.visualizer import Visualizer
            chart = Visualizer.create_pie_chart(class_count, '检测类别分布')
            self.chart_container_layout.addWidget(chart)

    def _save_record(self, detections):
        """保存检测记录到数据库"""
        try:
            from database.db_manager import DatabaseManager
            from database.models import DetectionRecord
            import json
            import os

            class_count = {}
            for d in detections:
                class_count[d['class_name']] = class_count.get(d['class_name'], 0) + 1
            class_dist = ', '.join(f"{k}:{v}" for k, v in sorted(class_count.items()))

            details = json.dumps([
                {
                    'class': d['class_name'],
                    'confidence': round(d['confidence'], 3),
                    'bbox': list(d['bbox'])
                }
                for d in detections
            ], ensure_ascii=False)

            record = DetectionRecord(
                type='image',
                source=os.path.basename(self._image_path),
                model_name='best.pt',
                total_objects=len(detections),
                class_distribution=class_dist,
                details=details,
                latitude=self._gps[0] if self._gps else None,
                longitude=self._gps[1] if self._gps else None,
            )

            db = DatabaseManager()
            record_id = db.add_record(record)

            # 保存标注图片
            if self._annotated_image is not None:
                from utils.image_utils import save_annotated_image
                path = save_annotated_image(
                    self._annotated_image, record_id,
                    source_name=os.path.basename(self._image_path))
                db.update_image_path(record_id, path)
        except Exception as e:
            print(f"[图片检测] 保存记录失败: {e}")
            import traceback
            traceback.print_exc()

    def _on_export_image(self):
        from PyQt6.QtWidgets import QMessageBox
        if self._annotated_image is None:
            QMessageBox.information(self, '提示', '请先进行检测')
            return

        from utils.file_utils import save_file_dialog
        save_path = save_file_dialog(self, '导出检测结果', 'result.png',
                                     '图片 (*.png *.jpg *.jpeg)')
        if not save_path:
            return

        import cv2
        success = cv2.imwrite(save_path, self._annotated_image)
        if success:
            QMessageBox.information(self, '成功', f'已导出到:\n{save_path}')
        else:
            QMessageBox.warning(self, '失败', '导出失败，请检查路径')

    def _on_batch_detect(self):
        """批量检测：选择文件夹，逐个处理所有图片"""
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if not folder:
            return

        # 扫描图片文件
        import os
        valid_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
        image_files = []
        for fname in sorted(os.listdir(folder)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in valid_exts:
                image_files.append(os.path.join(folder, fname))

        if not image_files:
            QMessageBox.information(self, '提示', '所选文件夹中没有支持的图片文件')
            return

        # 确保检测器已加载
        from core.detector import RoadDefectDetector
        detector = RoadDefectDetector.get_instance()
        if not detector._model:
            from core.detector import DEFAULT_MODEL_PATH
            model_path = DEFAULT_MODEL_PATH
            if not os.path.exists(model_path):
                QMessageBox.warning(self, '错误',
                                    f'模型文件不存在: {model_path}\n请先在模型管理中加载模型')
                return
            try:
                detector.load_model(model_path)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'模型加载失败: {e}')
                return

        # 进度对话框
        progress = QProgressDialog('正在批量检测...', '取消', 0, len(image_files), self)
        progress.setWindowTitle('批量检测')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        total_objects = 0
        class_counter = {}
        processed = 0
        cancelled = False

        for i, img_path in enumerate(image_files):
            if progress.wasCanceled():
                cancelled = True
                break

            progress.setLabelText(f'检测中 ({i + 1}/{len(image_files)}): {os.path.basename(img_path)}')
            progress.setValue(i)
            QApplication.processEvents()

            try:
                import cv2
                import json
                from utils.image_utils import extract_gps
                from database.db_manager import DatabaseManager
                from database.models import DetectionRecord

                img = cv2.imread(img_path)
                if img is None:
                    continue

                result = detector.detect(img)
                if result is None:
                    continue

                detections, annotated_bgr = detector.parse_results(result)
                if not detections:
                    # 即使没有检测结果也记录（0 个目标）
                    gps = extract_gps(img_path)
                    class_dist = ''
                    details = '[]'
                    record = DetectionRecord(
                        type='image',
                        source=os.path.basename(img_path),
                        model_name='best.pt',
                        total_objects=0,
                        class_distribution=class_dist,
                        details=details,
                        latitude=gps[0] if gps else None,
                        longitude=gps[1] if gps else None,
                    )
                    db = DatabaseManager()
                    db.add_record(record)
                    processed += 1
                    continue

                total_objects += len(detections)

                # 统计类别
                for d in detections:
                    name = d['class_name']
                    class_counter[name] = class_counter.get(name, 0) + 1

                # 生成类别分布字符串
                local_count = {}
                for d in detections:
                    local_count[d['class_name']] = local_count.get(d['class_name'], 0) + 1
                class_dist = ', '.join(f"{k}:{v}" for k, v in sorted(local_count.items()))

                details_json = json.dumps([
                    {
                        'class': d['class_name'],
                        'confidence': round(d['confidence'], 3),
                        'bbox': list(d['bbox'])
                    }
                    for d in detections
                ], ensure_ascii=False)

                # 提取 GPS
                gps = extract_gps(img_path)

                # 保存到数据库
                record = DetectionRecord(
                    type='image',
                    source=os.path.basename(img_path),
                    model_name='best.pt',
                    total_objects=len(detections),
                    class_distribution=class_dist,
                    details=details_json,
                    latitude=gps[0] if gps else None,
                    longitude=gps[1] if gps else None,
                )
                db = DatabaseManager()
                record_id = db.add_record(record)

                # 保存标注图片
                if annotated_bgr is not None:
                    from utils.image_utils import save_annotated_image
                    img_save_path = save_annotated_image(
                        annotated_bgr, record_id,
                        source_name=os.path.basename(img_path))
                    db.update_image_path(record_id, img_save_path)

                processed += 1

            except Exception:
                import traceback
                traceback.print_exc()
                continue

        progress.setValue(len(image_files))
        progress.close()

        if not cancelled:
            # 构建汇总信息
            class_lines = '\n'.join(f'  {k}: {v}' for k, v in sorted(class_counter.items()))
            if not class_lines:
                class_lines = '  (无检出)'

            summary = (
                f'批量检测完成\n\n'
                f'总图片数: {len(image_files)}\n'
                f'成功处理: {processed}\n'
                f'检出目标总数: {total_objects}\n\n'
                f'各类型分布:\n{class_lines}'
            )
            QMessageBox.information(self, '批量检测完成', summary)

    def _on_apply_manual_gps(self):
        """手动输入GPS坐标"""
        try:
            lat_text = self.lat_input.text().strip()
            lon_text = self.lon_input.text().strip()
            if not lat_text or not lon_text:
                QMessageBox.information(self, '提示', '请输入纬度和经度')
                return
            lat = float(lat_text)
            lon = float(lon_text)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                QMessageBox.warning(self, '错误', '坐标范围错误：纬度 -90~90，经度 -180~180')
                return
            self._gps = (lat, lon)
            c = AppStyles.COLORS
            self.gps_label.setText(f'{lat:.6f}, {lon:.6f}')
            self.gps_label.setStyleSheet(f'color: {c["success"]}; border: none;')
        except ValueError:
            QMessageBox.warning(self, '错误', '请输入有效的数字')

    def _on_clear(self):
        self._image_path = None
        self._annotated_image = None
        self._gps = None
        self._update_stats(0, 0, 0.0, 0.0)

        # 重置严重程度卡片
        self.stat_labels['severity'].setText('--')
        self.stat_labels['severity'].setStyleSheet('color: #8B9AB5; border: none;')
        self._severity_widget.setStyleSheet(AppStyles.get_stat_card_style('#8B9AB5'))

        c = AppStyles.COLORS
        self.gps_label.setText('无位置信息')
        self.gps_label.setStyleSheet(f'color: {c["text_secondary"]}; border: none;')
        self.lat_input.clear()
        self.lon_input.clear()
        self.result_table.setRowCount(0)

        # 恢复图表占位
        while self.chart_container_layout.count():
            item = self.chart_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        placeholder = AppStyles.create_empty_state('暂无图表数据', 'chart_placeholder')
        self.chart_container_layout.addWidget(placeholder)

        # 恢复图片占位
        self._display_size = None
        new_placeholder = AppStyles.create_placeholder('点击下方按钮选择图片', 'image')
        new_placeholder.setMinimumHeight(350)
        self._set_image_widget(new_placeholder)
