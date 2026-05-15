@echo off
cd /d "%~dp0"
echo 正在创建压缩包...
powershell -Command "Compress-Archive -Path 'dist\RoadDefectSystem' -DestinationPath 'RoadDefectSystem_v1.0.0.zip' -Force"
echo 完成！
pause