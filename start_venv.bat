@echo off
chcp 65001 >nul
echo ====================================
echo   語音助理 LINE Bot 服務啟動 (虛擬環境)
echo ====================================

echo.
echo 啟動虛擬環境並檢查 Python...
call venv\Scripts\activate.bat
python --version
if %errorlevel% neq 0 (
    echo 錯誤：虛擬環境中找不到 Python
    pause
    exit /b 1
)

echo.
echo 建立必要目錄...
if not exist "logs" mkdir logs
if not exist "temp_files" mkdir temp_files

echo.
echo 正在啟動各項服務 (虛擬環境中)...
echo.

echo 啟動 ASR 語音辨識服務 (Port 8001)...
start "ASR Service (venv)" cmd /k "call venv\Scripts\activate.bat && python asr_service/asr_server.py"
timeout /t 3 /nobreak >nul

echo 啟動 TTS 語音合成服務 (Port 8003)...
start "TTS Service (venv)" cmd /k "call venv\Scripts\activate.bat && python tts_service/tts_server.py"
timeout /t 3 /nobreak >nul

echo 🧠 啟動記憶服務 (Port 8004)...
start "Memory Service (venv)" cmd /k "call venv\Scripts\activate.bat && python memory_service/memory_server.py"
timeout /t 3 /nobreak >nul

echo 啟動 LINE Bot 主服務 (Port 8000)...
start "LINE Bot Service (venv)" cmd /k "call venv\Scripts\activate.bat && python linebot_service/linebot_server.py"

echo.
echo ====================================
echo   服務啟動完成！(虛擬環境)
echo ====================================
echo.
echo 各服務已在新視窗中啟動：
echo   • LINE Bot 主服務:    http://localhost:8000
echo   • ASR 語音辨識服務:   http://localhost:8001
echo   • TTS 語音合成服務:   http://localhost:8003
echo   • 🧠 記憶服務:        http://localhost:8004
echo.
echo LINE Bot Webhook URL: http://your-domain:8000/webhook
echo.
echo 要停止服務，請關閉對應的命令提示字元視窗
echo.

pause 