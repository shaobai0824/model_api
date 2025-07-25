# 🚀 語音助理 LINE Bot 設定指南

## 📋 現況確認

✅ **所有套件已安裝完成**  
✅ **GPU 支援已啟用 (NVIDIA GeForce RTX 3060 Ti)**  
✅ **TTS 服務測試成功**  
✅ **您的 ASR 模型**: `shaobai880824/breeze-asr-25-final-chinese`

## 🔧 下一步設定

### 1. 設定環境變數

您的 `.env` 檔案已建立，請編輯以下重要設定：

```bash
# 開啟 .env 檔案進行編輯
notepad .env
```

**必須設定的項目**：
```env
# LINE Bot 設定 (必須)
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# ASR 模型 (已設定)
ASR_MODEL_NAME=shaobai880824/breeze-asr-25-final-chinese

# OpenAI API (建議設定，用於 LLM)
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 取得 LINE Bot 憑證

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Messaging API Channel
3. 在 Channel 設定中取得：
   - **Channel Access Token**
   - **Channel Secret**
4. 將這些值填入 `.env` 檔案

### 3. 啟動服務

使用我們提供的啟動腳本：

```powershell
# 方法 1: 使用批次檔 (推薦)
.\start.bat

# 方法 2: 使用 PowerShell 腳本
.\start_services_fixed.ps1

# 方法 3: 手動啟動各服務
# 開啟 3 個 PowerShell 視窗分別執行：
python asr_service/asr_server.py    # Port 8001
python tts_service/tts_server.py    # Port 8003  
python linebot_service/linebot_server.py  # Port 8000
```

### 4. 設定 LINE Bot Webhook

在 LINE Developers Console 中：
1. 找到您的 Messaging API Channel
2. 在 Webhook 設定中輸入：`https://your-domain.com:8000/webhook`
3. 啟用 **Use webhook** 選項
4. 關閉 **Auto-reply messages** (自動回覆訊息)

## 🔍 服務檢查

啟動服務後，可以訪問以下端點檢查狀態：

```powershell
# 檢查各服務健康狀態
Invoke-WebRequest http://localhost:8000     # LINE Bot 主服務
Invoke-WebRequest http://localhost:8001/health  # ASR 服務
Invoke-WebRequest http://localhost:8003/health  # TTS 服務
```

## ⚡ 效能預期

根據您的硬體配置 (NVIDIA GeForce RTX 3060 Ti)：

- **語音辨識速度**: 約 5-15 秒 (GPU 加速)
- **TTS 合成速度**: 約 1-3 秒
- **整體回應時間**: 約 10-20 秒

這比您之前在終端機測試的 30-60 秒要快很多！

## 🐛 常見問題解決

### Q1: ASR 服務啟動時出現模型載入錯誤
```
解決方案：
1. 確認網路連線正常，能訪問 Hugging Face
2. 檢查模型名稱是否正確：shaobai880824/breeze-asr-25-final-chinese
3. 首次載入需要下載模型，可能需要較長時間
```

### Q2: LINE Bot 無法接收訊息
```
解決方案：
1. 確認 Webhook URL 設定正確
2. 檢查防火牆是否阻擋 8000 port
3. 確認 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 正確
4. 檢查 LINE Bot 設定中是否啟用了 Webhook
```

### Q3: TTS 服務無法合成語音
```
解決方案：
1. 檢查網路連線 (Edge TTS 需要網路)
2. 嘗試切換 TTS 引擎：
   - Edge TTS (推薦): TTS_ENGINE=edge
   - Google TTS: TTS_ENGINE=gtts  
   - 本地 TTS: TTS_ENGINE=pyttsx3
```

### Q4: GPU 無法使用
```
檢查方案：
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

如果顯示 False：
1. 確認 NVIDIA 驅動程式已安裝
2. 重新安裝 PyTorch GPU 版本：
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📱 測試 LINE Bot

設定完成後，您可以：

1. **加入您的 LINE Bot 為好友**
2. **傳送語音訊息測試**：
   - Bot 會進行語音辨識
   - 透過 OpenAI GPT 生成回應
   - 將回應轉換為語音回傳

3. **傳送文字訊息測試**：
   - 輸入 `/help` 查看說明
   - 輸入 `/status` 檢查服務狀態

## 🔧 進階設定

### 調整 ASR 效能
```env
# 在 .env 中調整這些參數
ASR_BATCH_SIZE=16        # 批次大小，可嘗試 8, 16, 32
ASR_CHUNK_LENGTH_S=30    # 音訊分段長度
ASR_MAX_NEW_TOKENS=128   # 最大生成 token 數
```

### 調整 TTS 語音
```env
# Edge TTS 語音選項
TTS_VOICE=zh-TW-HsiaoChenNeural  # 台灣中文 (女)
TTS_VOICE=zh-TW-YunJheNeural     # 台灣中文 (男)
TTS_SPEECH_RATE=+20%             # 語速調整 (-50% ~ +50%)
TTS_SPEECH_PITCH=+10%            # 音調調整 (-50% ~ +50%)
```

## 📊 監控與日誌

服務運行時會產生日誌檔案：
- `logs/` 目錄包含各服務的日誌
- 臨時檔案存放在 `temp_files/` 目錄

## 🎯 下一步

1. **完成 LINE Bot 設定**
2. **測試語音對話功能**
3. **根據需要調整參數**
4. **考慮部署到雲端服務** (如需公開使用)

---

🎉 **恭喜！您的語音助理 LINE Bot 已準備就緒！**

如有任何問題，請參考 `README.md` 或檢查各服務的日誌檔案。 