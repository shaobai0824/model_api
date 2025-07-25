# =============================================
# 語音助理 LINE Bot 服務啟動腳本 (Windows)
# =============================================

Write-Host "=== 語音助理 LINE Bot 服務啟動腳本 ===" -ForegroundColor Green

# 檢查 Python 環境
Write-Host "檢查 Python 環境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤：找不到 Python，請確保 Python 已安裝並加入 PATH" -ForegroundColor Red
    exit 1
}

# 載入環境變數
if (Test-Path ".env") {
    Write-Host "載入環境變數檔案..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}
else {
    Write-Host "警告：找不到 .env 檔案，請參考 env.example 建立環境變數檔案" -ForegroundColor Yellow
}

# 檢查必要的環境變數
$requiredVars = @("ASR_MODEL_NAME")
foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        Write-Host "錯誤：環境變數 $var 未設定" -ForegroundColor Red
        Write-Host "請參考 env.example 設定環境變數" -ForegroundColor Yellow
        exit 1
    }
}

# 建立必要的目錄
Write-Host "建立必要的目錄..." -ForegroundColor Yellow
$directories = @("logs", "temp_files")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "已建立目錄: $dir" -ForegroundColor Green
    }
}

# 啟動服務函數
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$ScriptPath,
        [int]$Port,
        [string]$Color = "Cyan"
    )
    
    Write-Host "啟動 $ServiceName (Port: $Port)..." -ForegroundColor $Color
    
    # 檢查連接埠是否被占用
    $portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "警告：Port $Port 已被占用，$ServiceName 可能無法啟動" -ForegroundColor Yellow
    }
    
    # 在新的 PowerShell 視窗中啟動服務
    $arguments = "-NoExit", "-Command", "cd '$PWD'; python $ScriptPath"
    Start-Process powershell -ArgumentList $arguments -WindowStyle Normal -PassThru
    
    Write-Host "$ServiceName 啟動指令已執行" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# 依序啟動服務
Write-Host ""
Write-Host "開始啟動各項服務..." -ForegroundColor Green

# 1. 啟動 ASR 服務
Start-Service -ServiceName "ASR 語音辨識服務" -ScriptPath "asr_service/asr_server.py" -Port 8001 -Color "Blue"

# 2. 啟動 TTS 服務  
Start-Service -ServiceName "TTS 語音合成服務" -ScriptPath "tts_service/tts_server.py" -Port 8003 -Color "Magenta"

# 3. 啟動 LINE Bot 服務
Start-Service -ServiceName "LINE Bot 主服務" -ScriptPath "linebot_service/linebot_server.py" -Port 8000 -Color "Green"

Write-Host ""
Write-Host "=== 服務啟動完成 ===" -ForegroundColor Green
Write-Host "各服務應該會在新的 PowerShell 視窗中啟動" -ForegroundColor Yellow
Write-Host ""
Write-Host "服務端點：" -ForegroundColor Cyan
Write-Host "  • LINE Bot 主服務:    http://localhost:8000" -ForegroundColor White
Write-Host "  • ASR 語音辨識服務:   http://localhost:8001" -ForegroundColor White  
Write-Host "  • TTS 語音合成服務:   http://localhost:8003" -ForegroundColor White
Write-Host ""
Write-Host "LINE Bot Webhook URL: http://your-domain:8000/webhook" -ForegroundColor Yellow
Write-Host ""
Write-Host "如需停止服務，請關閉對應的 PowerShell 視窗或按 Ctrl+C" -ForegroundColor Gray
Write-Host ""

# 等待用戶輸入
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null 