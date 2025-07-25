@echo off
chcp 65001 >nul
echo 🔍 語音助理服務狀態檢查
echo ================================

echo.
echo 📡 檢查端口監聽狀態...
echo --------------------------------
netstat -ano | findstr ":800" 2>nul
if %errorlevel% == 1 (
    echo ❌ 沒有服務在運行
) else (
    echo ✅ 發現運行中的服務
)

echo.
echo 🏥 檢查服務健康狀態...
echo --------------------------------

REM 檢查 ASR 服務 (端口 8001)
echo [ASR 服務 - 端口 8001]
curl -s http://localhost:8001/health 2>nul
if %errorlevel% == 0 (
    echo ✅ ASR 服務正常
) else (
    echo ❌ ASR 服務無回應
)

echo.
REM 檢查 LINE Bot 服務 (端口 8000)  
echo [LINE Bot 服務 - 端口 8000]
curl -s http://localhost:8000/ 2>nul
if %errorlevel% == 0 (
    echo ✅ LINE Bot 服務正常
) else (
    echo ❌ LINE Bot 服務無回應
)

echo.
REM 檢查 TTS 服務 (端口 8003)
echo [TTS 服務 - 端口 8003]
curl -s http://localhost:8003/health 2>nul
if %errorlevel% == 0 (
    echo ✅ TTS 服務正常
) else (
    echo ❌ TTS 服務無回應
)

echo.
echo 🔧 服務管理指令...
echo --------------------------------
echo 啟動所有服務: .\start_venv.bat
echo 停止所有服務: .\stop_services.bat
echo 檢查服務狀態: .\check_services.bat
echo.
pause 