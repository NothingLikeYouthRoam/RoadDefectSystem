# 道路缺陷检测系统打包配置
# 安装依赖: pip install pyinstaller
# 打包命令: pyinstaller road_defect.spec --clean

# 或者直接用命令行:
# pyinstaller main.py 
#   --name RoadDefectSystem
#   --windowed 
#   --onedir
#   --add-data "models;models"
#   --hidden-import PyQt6.QtWebEngineWidgets
#   --hidden-import folium
#   --hidden-import branca
#   --collect-all folium
#   --collect-all branca
