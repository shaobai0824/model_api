# 🤖 語音助理 LINE Bot

這是一個整合語音辨識 (ASR)、大型語言模型 (LLM) 和語音合成 (TTS) 的 LINE Bot 專案，能夠接收使用者的語音訊息，進行智能對話，並以語音形式回應。

## ✨ 功能特色

- 🎤 **語音辨識**：使用微調後的 Breeze ASR 模型，支援繁體中文語音辨識
- 🧠 **智能對話**：整合 OpenAI GPT 或本地 LLM 模型，提供智能回應
- 🔊 **語音合成**：支援多種 TTS 引擎 (Edge TTS、Google TTS、pyttsx3)
- 📱 **LINE Bot**：完整的 LINE Bot 整合，支援語音和文字訊息
- 🧠 **記憶功能**：記住每個用戶的對話歷史，提供連貫的個人化體驗
- 🚀 **微服務架構**：模組化設計，各服務可獨立部署和擴展
- 🖥️ **Windows 優化**：針對 Windows 環境進行優化，支援 PowerShell

## 🏗️ 系統架構

```
使用者 (LINE App)
    ↓ 語音/文字訊息
LINE Platform
    ↓ Webhook
LINE Bot 服務 (Port 8000)
    ↓ 呼叫各服務
┌──────────────────────────────────────────────────────┐
│  ASR 服務     │  記憶服務     │  LLM 服務     │  TTS 服務  │
│  (Port 8001)  │  (Port 8004)  │  (OpenAI API) │ (Port 8003)│
│  語音 → 文字   │  對話歷史存取  │  文字 → 回應   │ 文字 → 語音 │
└──────────────────────────────────────────────────────┘
    ↓ 回傳語音/文字
LINE Platform → 使用者
```

## 📁 專案結構

```
model_api/
├── asr_service/                 # ASR 語音辨識服務
│   ├── asr_server.py           # ASR 服務主程式
│   └── requirements.txt        # ASR 服務套件
├── linebot_service/            # LINE Bot 主服務
│   ├── linebot_server.py       # LINE Bot 主程式
│   ├── handlers/               # 事件處理器
│   └── requirements.txt        # LINE Bot 套件
├── tts_service/                # TTS 語音合成服務
│   ├── tts_server.py           # TTS 服務主程式
│   └── requirements.txt        # TTS 服務套件
├── 🧠 memory_service/           # 記憶服務 (新增)
│   ├── memory_server.py        # 記憶服務主程式
│   ├── memory_manager.py       # 記憶管理器
│   └── __init__.py             # 模組初始化
├── shared/                     # 共用模組
│   ├── config.py               # 設定管理
│   └── utils/                  # 工具函數
├── logs/                       # 日誌檔案
├── temp_files/                 # 臨時檔案
├── memory_data/                # 記憶資料存儲 (自動創建)
├── requirements.txt            # 主要套件清單
├── env.example                 # 環境變數範例
├── start_services.ps1          # Windows 啟動腳本
└── README.md                   # 專案說明
```

## 🚀 快速開始

### 1. 環境需求

- **作業系統**：Windows 10/11 (已針對 Windows 優化)
- **Python**：3.8 或更新版本
- **硬體**：建議使用 NVIDIA GPU (支援 CUDA) 以加速 ASR 模型推論
- **記憶體**：建議 8GB 以上 RAM

### 2. 安裝步驟

#### 步驟 1：複製專案
```powershell
git clone <your-repo-url>
cd model_api
```

#### 步驟 2：建立虛擬環境 (建議)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 步驟 3：安裝套件
```powershell
# 如果有 GPU，先安裝 PyTorch GPU 版本
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安裝所有套件
pip install -r requirements.txt
```

#### 步驟 4：設定環境變數
```powershell
# 複製環境變數範例檔案
Copy-Item env.example .env

# 編輯 .env 檔案，設定以下必要變數：
# - LINE_CHANNEL_ACCESS_TOKEN: LINE Bot 存取權杖
# - LINE_CHANNEL_SECRET: LINE Bot 頻道密鑰
# - ASR_MODEL_NAME: 您在 Hugging Face 上的微調模型名稱
# - OPENAI_API_KEY: OpenAI API 金鑰 (如果使用 OpenAI)
```

### 3. 設定 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Messaging API Channel
3. 取得 **Channel Access Token** 和 **Channel Secret**
4. 設定 Webhook URL：`https://your-domain.com:8000/webhook`
5. 啟用 **Use webhook** 選項

### 4. 啟動服務

#### 方法 1：使用啟動腳本 (推薦)
```powershell
# 執行啟動腳本
.\start_services.ps1
```

#### 方法 2：手動啟動各服務
```powershell
# 開啟 3 個 PowerShell 視窗，分別執行：

# 視窗 1：ASR 服務
python asr_service/asr_server.py

# 視窗 2：TTS 服務  
python tts_service/tts_server.py

# 視窗 3：LINE Bot 主服務
python linebot_service/linebot_server.py
```

### 5. 測試服務

訪問以下端點檢查服務狀態：
- LINE Bot 主服務：http://localhost:8000
- ASR 服務：http://localhost:8001/health
- TTS 服務：http://localhost:8003/health

## 🔧 設定說明

### ASR 模型設定

在 `.env` 檔案中設定您的 Hugging Face 微調模型：

```env
# 將 'your-username/breeze-asr-finetuned' 替換為您的實際模型名稱
ASR_MODEL_NAME=your-username/breeze-asr-finetuned
```

### LLM 設定選項

#### 選項 1：使用 OpenAI API (推薦)
```env
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

#### 選項 2：使用本地 LLM (進階)
```env
USE_OPENAI=false
LLM_MODEL_NAME=microsoft/DialoGPT-medium
```

### TTS 引擎選擇

支援三種 TTS 引擎：

1. **Edge TTS** (推薦)：Microsoft 的免費 TTS 服務，音質最佳
2. **Google TTS**：需要網路連線，音質良好
3. **pyttsx3**：本地 TTS，無需網路但音質較差

```env
TTS_ENGINE=edge  # edge, gtts, pyttsx3
TTS_VOICE=zh-TW-HsiaoChenNeural  # Edge TTS 語音
```

## 📊 效能優化

### GPU 加速

確保您的系統已安裝 CUDA 並正確設定：

```powershell
# 檢查 CUDA 是否可用
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 模型載入優化

ASR 服務會在啟動時載入模型到記憶體，首次載入可能需要較長時間。模型載入後，推論速度會顯著提升。

### 預期效能

- **CPU 模式**：語音辨識約 30-60 秒
- **GPU 模式**：語音辨識約 5-15 秒 (取決於 GPU 效能)
- **TTS 合成**：通常 1-3 秒

## 🧠 記憶功能詳細說明

### 記憶系統特色
- **個人化對話**：為每個用戶維護獨立的對話歷史
- **上下文感知**：LLM 能夠參考先前的對話內容
- **用戶偏好**：記住用戶的語調偏好和其他設定
- **統計資訊**：提供詳細的對話統計和使用分析

### 記憶指令
在 LINE Bot 中可以使用以下指令：

- `/stats` - 查看對話統計
- `/clear` - 清除對話記憶
- `/formal` - 設定正式語調
- `/casual` - 設定輕鬆語調

### 記憶設定選項
在 `.env` 檔案中可以調整以下記憶相關設定：

```env
# 記憶服務設定
MEMORY_SERVICE_URL=http://localhost:8004
MAX_MESSAGES_PER_USER=50          # 每個用戶最多保存的訊息數
MAX_CONTEXT_MESSAGES=10           # 傳送給 LLM 的上下文訊息數
MEMORY_EXPIRE_DAYS=30             # 記憶過期天數
```

### 記憶資料存儲
- **存儲方式**：預設使用 JSON 檔案存儲 (可升級到 Redis)
- **資料位置**：`memory_data/` 目錄
- **資料格式**：每個用戶一個 JSON 檔案
- **自動清理**：系統會自動清理過期的記憶資料

### 測試記憶功能
使用測試腳本驗證記憶功能：

```powershell
python test_memory_service.py
```

## 🐛 常見問題

### Q1：ASR 服務啟動失敗
**A1**：檢查以下項目：
- 確認 `ASR_MODEL_NAME` 設定正確
- 檢查網路連線，確保能訪問 Hugging Face
- 確認 GPU 驅動程式已正確安裝

### Q2：LINE Bot 無法接收訊息
**A2**：檢查以下項目：
- 確認 LINE Bot 設定中的 Webhook URL 正確
- 檢查防火牆設定，確保 8000 port 可被外部訪問
- 確認 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 設定正確

### Q3：語音辨識速度太慢
**A3**：建議解決方案：
- 使用 GPU 加速 (安裝 CUDA 版本的 PyTorch)
- 調整 `ASR_BATCH_SIZE` 和 `ASR_CHUNK_LENGTH_S` 參數
- 考慮使用更小的模型或量化版本

### Q4：TTS 服務無法合成語音
**A4**：檢查以下項目：
- 確認選擇的 TTS 引擎已正確安裝
- 檢查網路連線 (Edge TTS 和 Google TTS 需要網路)
- 嘗試切換不同的語音或引擎

## 🔒 安全性考量

- 不要將 `.env` 檔案提交到版本控制系統
- 定期更新 API 金鑰
- 在生產環境中使用 HTTPS
- 考慮實作請求限制和身份驗證

## 📝 開發指南

### 新增功能

1. 在對應的服務資料夾中新增功能
2. 更新相關的 `requirements.txt`
3. 在 `shared/config.py` 中新增設定選項
4. 更新 `env.example` 和文件

### 除錯模式

設定環境變數啟用除錯模式：
```env
LOG_LEVEL=DEBUG
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝

- [Breeze ASR](https://github.com/MediaTek-Research/Breeze-7B) - 語音辨識模型
- [LINE Bot SDK](https://github.com/line/line-bot-sdk-python) - LINE Bot 開發套件
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Edge TTS](https://github.com/rany2/edge-tts) - 語音合成引擎

---

如有任何問題或建議，請隨時聯絡！ 🚀 