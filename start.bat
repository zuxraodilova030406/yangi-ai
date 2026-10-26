@echo off
chcp 65001 >nul
title Telegram AI Yordamchi (24/7)
echo ============================================================
echo   TELEGRAM SHAXSIY AI YORDAMCHI ISHGA TUSHIRILMOQDA...
echo ============================================================

if not exist "venv" (
    echo [1/3] Virtual muhit yaratilmoqda...
    python -m venv venv
)

echo [2/3] Kerakli kutubxonalar tekshirilmoqda...
call venv\Scripts\activate
pip install -r requirements.txt --quiet

echo [3/3] Dastur ishga tushirilmoqda...
python main.py
pause
