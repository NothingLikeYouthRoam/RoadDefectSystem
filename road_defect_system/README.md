# 道路缺陷检测系统 - YOLOv8

基于 YOLOv8 和 PyQt6 实现的道路缺陷检测桌面应用程序。

## 项目简介

本系统是一个功能完善的道路缺陷检测桌面应用，支持图片、视频和摄像头实时检测，采用 YOLOv8 进行缺陷识别，可检测 9 种道路缺陷类型：

- **Crack** - 裂缝
- **Manhole** - 井盖
- **Net** - 网状裂缝
- **Pothole** - 坑洞
- **Patch-Crack** - 修补裂缝
- **Patch-Net** - 修补网裂
- **Patch-Pothole** - 修补坑洞
- **other** - 其他
- **Other** - 其他（备用）

## 技术栈

- **UI框架**: PyQt6
- **模型推理**: Ultralytics YOLOv8 (PyTorch)
- **图像处理**: OpenCV (cv2)
- **可视化图表**: Matplotlib (FigureCanvasQTAgg)
- **数据处理**: Pandas (CSV 导出/导入)
- **数据库**: SQLite (检测历史记录存储)

## 项目结构

```
road_defect_system/
├── main.py                     # 程序入口
├── ui/
│   ├── main_window.py          # 主窗口
│   ├── login_dialog.py         # 登录对话框
│   ├── detect_image_page.py    # 图片检测页面
│   ├── detect_video_page.py    # 视频检测页面
│   ├── detect_camera_page.py   # 摄像头实时检测页面
│   ├── history_page.py         # 检测历史记录页面
│   ├── model_manage_page.py    # 模型管理页面
│   ├── metrics_page.py         # 训练指标展示页面
│   └── styles.qss              # QSS 样式文件
├── core/
│   ├── detector.py             # YOLOv8 检测器封装类
│   └── visualizer.py          # 图表生成工具
├── database/
│   ├── db_manager.py          # SQLite 数据库管理
│   └── models.py              # 数据模型定义
├── utils/
│   ├── file_utils.py          # 文件操作工具
│   └── image_utils.py         # 图像处理工具
├── models/
│   └── best.pt                # YOLOv8 模型文件（需自行放置）
├── output/                    # 检测结果导出目录
├── training_logs/             # 训练日志目录（可选）
└── requirements.txt           # 项目依赖列表
```

## 功能特性

### 1. 登录模块
- 用户名/密码认证
- 默认账号：`admin` / `admin123`
- 支持用户注册（本地模拟）

### 2. 图片检测
- 支持多种图片格式（PNG、JPG、BMP、WebP）
- 实时显示检测结果
- 导出标注图片和CSV数据
- 统计信息展示（总数、类别数、置信度）

### 3. 视频检测
- 支持常见视频格式（MP4、AVI、MOV、MKV）
- 可调节检测间隔
- 实时截图功能
- 播放控制（开始/暂停/停止）

### 4. 摄像头实时检测
- 本地摄像头实时检测
- 实时显示检测结果
- 截图和清空记录功能

### 5. 检测历史
- SQLite 数据库存储
- 支持类型筛选和关键词搜索
- 导出 CSV 文件
- 记录详情查看

### 6. 模型管理
- 加载/切换 YOLOv8 模型
- 调节检测参数（置信度阈值、IoU阈值、最大检测数）
- 显示模型信息和类别列表

### 7. 指标展示
- 训练损失曲线（Box Loss、Cls Loss、DFL Loss）
- mAP 指标曲线（mAP50、mAP50-95）
- Precision/Recall 曲线

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python main.py
```

## 使用说明

1. **首次运行**：使用默认账号 `admin` / `admin123` 登录
2. **模型加载**：将训练好的 `best.pt` 模型文件放置在 `models/` 目录，或在模型管理页面选择
3. **开始检测**：根据需要选择图片/视频/摄像头检测模式
4. **查看历史**：检测历史自动保存，可在历史记录页面查看

## 界面预览

系统采用深色科技风格设计：
- 主色调：深蓝/紫色
- 左侧导航栏 + 右侧内容区
- 卡片式布局，圆角按钮

## 注意事项

- 确保已安装 CUDA（如果使用 GPU 加速）
- 模型文件较大，首次加载可能需要一些时间
- 视频/摄像头检测建议在性能较好的设备上运行

## 许可证

MIT License