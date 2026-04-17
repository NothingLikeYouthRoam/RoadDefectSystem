"""
图表生成工具模块
"""
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Optional


class ChartCanvas(FigureCanvasQTAgg):
    """图表画布基类"""
    
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout()


class Visualizer:
    """可视化工具类"""
    
    @staticmethod
    def create_pie_chart(data: Dict[str, int], title: str = "类别分布") -> ChartCanvas:
        """创建饼图"""
        canvas = ChartCanvas(width=5, height=4)
        
        if not data:
            canvas.axes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            labels = list(data.keys())
            values = list(data.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            canvas.axes.pie(values, labels=labels, autopct='%1.1f%%',
                           colors=colors, startangle=90,
                           textprops={'fontsize': 9})
        
        canvas.fig.tight_layout()
        return canvas
    
    @staticmethod
    def create_bar_chart(data: Dict[str, int], title: str = "类别统计") -> ChartCanvas:
        """创建柱状图"""
        canvas = ChartCanvas(width=6, height=4)
        
        if not data:
            canvas.axes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            labels = list(data.keys())
            values = list(data.values())
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
            
            bars = canvas.axes.bar(labels, values, color=colors)
            canvas.axes.set_xlabel('类别')
            canvas.axes.set_ylabel('数量')
            canvas.axes.set_title(title)
            
            for bar in bars:
                height = bar.get_height()
                canvas.axes.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}', ha='center', va='bottom')
            
            canvas.fig.autofmt_xdate(rotation=45)
        
        canvas.fig.tight_layout()
        return canvas
    
    @staticmethod
    def create_histogram(data: List[float], title: str = "置信度分布", bins: int = 10) -> ChartCanvas:
        """创建直方图"""
        canvas = ChartCanvas(width=6, height=4)
        
        if not data:
            canvas.axes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            canvas.axes.hist(data, bins=bins, color='steelblue', edgecolor='white', alpha=0.8)
            canvas.axes.set_xlabel('置信度')
            canvas.axes.set_ylabel('数量')
            canvas.axes.set_title(title)
            canvas.axes.set_xlim(0, 1)
        
        canvas.fig.tight_layout()
        return canvas
    
    @staticmethod
    def create_metrics_chart(epochs: List[int], 
                            metrics: Dict[str, List[float]], 
                            title: str = "训练指标") -> ChartCanvas:
        """创建训练指标曲线图"""
        canvas = ChartCanvas(width=8, height=5)
        
        if not epochs or not metrics:
            canvas.axes.text(0.5, 0.5, '暂无训练数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            color_idx = 0
            
            for metric_name, values in metrics.items():
                if len(values) == len(epochs):
                    canvas.axes.plot(epochs, values, 'o-', 
                                   label=metric_name, 
                                   color=colors[color_idx % len(colors)],
                                   linewidth=2,
                                   markersize=4)
                    color_idx += 1
            
            canvas.axes.set_xlabel('Epoch')
            canvas.axes.set_ylabel('Value')
            canvas.axes.set_title(title)
            canvas.axes.legend(loc='best')
            canvas.axes.grid(True, alpha=0.3)
        
        canvas.fig.tight_layout()
        return canvas
    
    @staticmethod
    def create_loss_chart(epochs: List[int], 
                         losses: Dict[str, List[float]], 
                         title: str = "训练损失") -> ChartCanvas:
        """创建损失曲线图"""
        canvas = ChartCanvas(width=8, height=5)
        
        if not epochs or not losses:
            canvas.axes.text(0.5, 0.5, '暂无损失数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']
            color_idx = 0
            
            for loss_name, values in losses.items():
                if len(values) == len(epochs):
                    canvas.axes.plot(epochs, values, 'o-', 
                                   label=loss_name, 
                                   color=colors[color_idx % len(colors)],
                                   linewidth=2,
                                   markersize=4)
                    color_idx += 1
            
            canvas.axes.set_xlabel('Epoch')
            canvas.axes.set_ylabel('Loss')
            canvas.axes.set_title(title)
            canvas.axes.legend(loc='best')
            canvas.axes.grid(True, alpha=0.3)
        
        canvas.fig.tight_layout()
        return canvas
    
    @staticmethod
    def create_confusion_matrix(data: np.ndarray, labels: List[str], title: str = "混淆矩阵") -> ChartCanvas:
        """创建混淆矩阵热力图"""
        canvas = ChartCanvas(width=8, height=6)
        
        if data is None or len(data) == 0:
            canvas.axes.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=12)
            canvas.axes.axis('off')
        else:
            im = canvas.axes.imshow(data, cmap='Blues')
            canvas.axes.set_xticks(np.arange(len(labels)))
            canvas.axes.set_yticks(np.arange(len(labels)))
            canvas.axes.set_xticklabels(labels, rotation=45, ha='right')
            canvas.axes.set_yticklabels(labels)
            canvas.axes.set_title(title)
            
            for i in range(len(labels)):
                for j in range(len(labels)):
                    text = canvas.axes.text(j, i, f'{data[i, j]:.2f}',
                                           ha="center", va="center", 
                                           color="white" if data[i, j] > data.max()/2 else "black")
            
            canvas.fig.colorbar(im, ax=canvas.axes)
        
        canvas.fig.tight_layout()
        return canvas