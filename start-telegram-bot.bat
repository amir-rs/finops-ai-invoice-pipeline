@echo off
title n8n Telegram Bot Bridge (@tets_manager111_bot)
echo ==============================================================
echo    Starting Telegram Bot Bridge for n8n Invoice Pipeline
echo    Bot Username: @tets_manager111_bot
echo ==============================================================
python "%~dp0scripts\telegram_bridge.py"
pause
