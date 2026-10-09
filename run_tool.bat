@echo off
chcp 65001 >nul
title AI Video Transcriber & Auto Renamer
echo ===================================================
echo     DANG KHOI DONG CONG CU LAY KICH BAN VIDEO
echo ===================================================
python main.py
if errorlevel 1 (
    echo.
    echo [LOI] Chuong trinh gap loi hoac da ket thuc.
    pause
)
