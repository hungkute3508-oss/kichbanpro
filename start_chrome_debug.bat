@echo off
chcp 65001 >nul
title Mo Google Chrome Che Do Debug Port 9222
echo ======================================================================
echo    DANG KHOI DONG GOOGLE CHROME CHE DO REMOTE DEBUGGING (PORT 9222)
echo ======================================================================
echo.
echo Thong bao: Trinh duyet Chrome se duoc mo voi profile rieng (khong anh huong
echo den Chrome dang su dung). Hay dang nhap tai khoan Google va mo tab Gemini!
echo.

set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME_PATH% (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
if not exist %CHROME_PATH% (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

set PROFILE_DIR="%LOCALAPPDATA%\Google\Chrome\DebugProfile"

start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=%PROFILE_DIR% "https://gemini.google.com"

echo Chrome da duoc khoi dong tai cong 9222.
echo URL: https://gemini.google.com
echo Ban co the de nguyen tab nay de tool tu dong gui file am thanh va lay kich ban!
timeout /t 5
