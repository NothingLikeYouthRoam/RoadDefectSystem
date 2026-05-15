; Inno Setup Script for RoadDefectSystem
; 安装前请确保已安装 Inno Setup: https://jrsoftware.org/isinfo.php

[Setup]
AppName=道路缺陷检测系统
AppVersion=1.0.0
AppPublisher=RoadDefectSystem
DefaultDirName={autopf}\RoadDefectSystem
DefaultGroupName=道路缺陷检测系统
OutputDir=..\installer
OutputBaseFilename=RoadDefectSystem_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\RoadDefectSystem\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\道路缺陷检测系统"; Filename: "{app}\RoadDefectSystem.exe"

[Run]
Filename: "{app}\RoadDefectSystem.exe"; Description: "启动程序"; Flags: postinstall nowait
