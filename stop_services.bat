@echo off
echo 🛑 正在停止所有語音助理服務...

echo.
echo 📍 檢查端口使用情況...
netstat -ano | findstr ":800"

echo.
echo 🔍 尋找並終止 Python 服務程序...

REM 終止佔用端口 8000 的程序 (LINE Bot 服務)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8000 "') do (
    if not "%%i"=="0" (
        echo 終止 LINE Bot 服務 (PID: %%i)
        taskkill /PID %%i /F >nul 2>&1
    )
)

REM 終止佔用端口 8001 的程序 (ASR 服務)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8001 "') do (
    if not "%%i"=="0" (
        echo 終止 ASR 服務 (PID: %%i)
        taskkill /PID %%i /F >nul 2>&1
    )
)

REM 終止佔用端口 8003 的程序 (TTS 服務)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8003 "') do (
    if not "%%i"=="0" (
        echo 終止 TTS 服務 (PID: %%i)
        taskkill /PID %%i /F >nul 2>&1
    )
)

REM 額外安全措施：終止所有相關的 Python 程序
echo.
echo 🧹 清理相關 Python 程序...
tasklist | findstr python.exe >nul
if %errorlevel% == 0 (
    echo 發現 Python 程序，正在安全終止...
    REM 只終止在我們專案目錄中運行的 Python 程序
    wmic process where "name='python.exe' and commandline like '%%asr_server.py%%'" delete >nul 2>&1
    wmic process where "name='python.exe' and commandline like '%%tts_server.py%%'" delete >nul 2>&1
    wmic process where "name='python.exe' and commandline like '%%linebot_server.py%%'" delete >nul 2>&1
)

timeout /t 2 >nul

echo.
echo ✅ 服務清理完成！
echo.
echo 📍 當前端口狀態：
netstat -ano | findstr ":800"
if %errorlevel% == 1 (
    echo    ✅ 所有端口已釋放
)

echo.
echo 💡 現在您可以重新啟動服務：
echo    .\start_venv.bat
echo.
pause 