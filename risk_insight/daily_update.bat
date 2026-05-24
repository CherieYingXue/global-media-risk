@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在生成每日风险报告...
python report_generator.py
echo 完成: %date% %time%
