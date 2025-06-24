@echo off
chcp 65001 > nul
title QQ Scraper - Master Launcher
cls
echo =================================================================
echo.
echo              欢迎使用 QQ 智能聊天记录抓取工具
echo.
echo =================================================================
echo.
echo 系统将全自动为您完成所有启动步骤，请稍候...
echo.
echo [1/3] 正在启动后台 OCR 识别服务器...
start "OnnxOCR Server" /min cmd /c "cd OnnxOCR-main && py app-service.py"
echo      > OCR 服务器已在后台启动 (最小化至任务栏)。

echo [2/3] 正在等待 OCR 服务器完成初始化 (约15秒)...
timeout /t 15 /nobreak > nul
echo      > 服务器预热完成。

echo [3/3] 正在启动主程序并打开浏览器...
start "QQ Scraper App" /min py app.py
timeout /t 2 /nobreak > nul
start http://127.0.0.1:5000
echo      > 操作界面已在浏览器中弹出！

echo.
echo --- 所有服务均已启动，您可以开始使用了！ ---
echo.
echo   重要提示: 在使用过程中，请不要关闭任何由本脚本
echo   自动打开的黑色命令行窗口，它们是程序的核心。
echo.
pause