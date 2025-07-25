# 簡化版語音助理 LINE Bot 啟動腳本

Write-Host "啟動語音助理 LINE Bot 服務..." -ForegroundColor Green

# 檢查 Python
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤：找不到 Python" -ForegroundColor Red
    pause
    exit 1
}

# 建立目錄
if (!(Test-Path "logs")) { mkdir logs }
if (!(Test-Path "temp_files")) { mkdir temp_files }

Write-Host "正在啟動服務..." -ForegroundColor Yellow

# 啟動 ASR 服務
Write-Host "啟動 ASR 服務 (Port 8001)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python asr_service/asr_server.py"

Start-Sleep 3

# 啟動 TTS 服務
Write-Host "啟動 TTS 服務 (Port 8003)..." -ForegroundColor Magenta  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python tts_service/tts_server.py"

Start-Sleep 3

# 啟動 LINE Bot 服務
Write-Host "啟動 LINE Bot 服務 (Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python linebot_service/linebot_server.py"

Write-Host ""
Write-Host "服務啟動完成！" -ForegroundColor Green
Write-Host "各服務會在新的視窗中運行" -ForegroundColor Yellow
Write-Host ""
Write-Host "服務端點："
Write-Host "  LINE Bot: http://localhost:8000"
Write-Host "  ASR:      http://localhost:8001" 
Write-Host "  TTS:      http://localhost:8003"
Write-Host ""

pause 