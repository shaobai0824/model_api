"""
共用設定檔
管理所有服務的環境變數和設定
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """基礎設定類別"""

    # 專案根目錄
    PROJECT_ROOT = Path(__file__).parent.parent

    # 日誌設定
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 臨時檔案目錄
    TEMP_DIR = PROJECT_ROOT / "temp_files"
    LOGS_DIR = PROJECT_ROOT / "logs"

    @classmethod
    def ensure_directories(cls):
        """確保必要的目錄存在"""
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)


class ASRConfig(Config):
    """ASR 服務設定"""

    # 服務設定
    HOST = os.getenv("ASR_HOST", "0.0.0.0")
    PORT = int(os.getenv("ASR_PORT", "8001"))

    # 模型設定
    MODEL_NAME = os.getenv("ASR_MODEL_NAME", "your-username/breeze-asr-finetuned")

    # 硬體設定
    DEVICE = os.getenv("ASR_DEVICE", "auto")  # auto, cpu, cuda:0
    USE_GPU = os.getenv("ASR_USE_GPU", "true").lower() == "true"

    # 音訊處理設定
    SAMPLE_RATE = int(os.getenv("ASR_SAMPLE_RATE", "16000"))
    MAX_AUDIO_LENGTH = int(os.getenv("ASR_MAX_AUDIO_LENGTH", "300"))  # 秒

    # 效能設定
    BATCH_SIZE = int(os.getenv("ASR_BATCH_SIZE", "16"))
    MAX_NEW_TOKENS = int(os.getenv("ASR_MAX_NEW_TOKENS", "128"))
    CHUNK_LENGTH_S = int(os.getenv("ASR_CHUNK_LENGTH_S", "30"))


class LineBotConfig(Config):
    """LINE Bot 服務設定"""

    # 服務設定
    HOST = os.getenv("LINEBOT_HOST", "0.0.0.0")
    PORT = int(os.getenv("LINEBOT_PORT", "8000"))

    # LINE Bot API 設定
    CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

    # 服務端點設定
    ASR_SERVICE_URL = os.getenv("ASR_SERVICE_URL", "http://localhost:8001")
    LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")
    TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8003")

    # OpenAI 設定 (替代 LLM)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "150"))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # 超時設定
    ASR_TIMEOUT = int(os.getenv("ASR_TIMEOUT", "120"))  # 秒
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))  # 秒
    TTS_TIMEOUT = int(os.getenv("TTS_TIMEOUT", "60"))  # 秒

    @classmethod
    def validate(cls):
        """驗證必要的設定"""
        if not cls.CHANNEL_ACCESS_TOKEN:
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定")
        if not cls.CHANNEL_SECRET:
            raise ValueError("LINE_CHANNEL_SECRET 環境變數未設定")


class TTSConfig(Config):
    """TTS 服務設定"""

    # 服務設定
    HOST = os.getenv("TTS_HOST", "0.0.0.0")
    PORT = int(os.getenv("TTS_PORT", "8003"))

    # TTS 引擎設定
    ENGINE = os.getenv("TTS_ENGINE", "edge").lower()
    VOICE = os.getenv("TTS_VOICE", "zh-TW-HsiaoChenNeural")
    SPEECH_RATE = os.getenv("TTS_SPEECH_RATE", "0%")
    SPEECH_PITCH = os.getenv("TTS_SPEECH_PITCH", "0%")

    # 文字處理設定
    MAX_LENGTH = int(os.getenv("TTS_MAX_LENGTH", "500"))

    # Edge TTS 特定設定
    EDGE_VOICES = {
        "zh-TW-HsiaoChenNeural": "台灣中文 (女)",
        "zh-TW-YunJheNeural": "台灣中文 (男)",
        "zh-TW-HsiaoYuNeural": "台灣中文 (女)",
        "zh-CN-XiaoxiaoNeural": "大陸中文 (女)",
        "zh-CN-YunxiNeural": "大陸中文 (男)",
        "zh-HK-HiuMaanNeural": "香港中文 (女)",
    }


class LLMConfig(Config):
    """本地 LLM 服務設定 (如果使用)"""

    # 服務設定
    HOST = os.getenv("LLM_HOST", "0.0.0.0")
    PORT = int(os.getenv("LLM_PORT", "8002"))

    # 模型設定
    MODEL_NAME = os.getenv("LLM_MODEL_NAME", "microsoft/DialoGPT-medium")
    MODEL_PATH = os.getenv("LLM_MODEL_PATH", "")

    # 硬體設定
    DEVICE = os.getenv("LLM_DEVICE", "auto")
    USE_GPU = os.getenv("LLM_USE_GPU", "true").lower() == "true"

    # 生成設定
    MAX_LENGTH = int(os.getenv("LLM_MAX_LENGTH", "150"))
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
    TOP_K = int(os.getenv("LLM_TOP_K", "50"))


# 全域設定實例
asr_config = ASRConfig()
linebot_config = LineBotConfig()
tts_config = TTSConfig()
llm_config = LLMConfig()


def load_env_file(env_file: str = ".env"):
    """載入環境變數檔案"""
    env_path = Path(env_file)
    if env_path.exists():
        from dotenv import load_dotenv

        load_dotenv(env_path)
        print(f"已載入環境變數檔案: {env_path.absolute()}")
    else:
        print(f"環境變數檔案不存在: {env_path.absolute()}")


def get_service_info():
    """取得所有服務的資訊"""
    return {
        "asr_service": {
            "url": f"http://{asr_config.HOST}:{asr_config.PORT}",
            "model": asr_config.MODEL_NAME,
            "device": asr_config.DEVICE,
        },
        "linebot_service": {
            "url": f"http://{linebot_config.HOST}:{linebot_config.PORT}",
            "webhook_url": f"http://{linebot_config.HOST}:{linebot_config.PORT}/webhook",
            "use_openai": linebot_config.USE_OPENAI,
        },
        "tts_service": {
            "url": f"http://{tts_config.HOST}:{tts_config.PORT}",
            "engine": tts_config.ENGINE,
            "voice": tts_config.VOICE,
        },
    }


if __name__ == "__main__":
    # 測試設定載入
    load_env_file()

    print("=== 服務設定資訊 ===")
    import json

    print(json.dumps(get_service_info(), indent=2, ensure_ascii=False))
