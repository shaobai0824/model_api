import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

# TTS 相關套件
try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="TTS Service",
    description="文字轉語音服務 - 支援多種 TTS 引擎",
    version="1.0.0",
)


class TTSService:
    def __init__(self):
        """初始化 TTS 服務"""
        self.tts_engine = os.getenv("TTS_ENGINE", "edge").lower()
        self.voice_name = os.getenv(
            "TTS_VOICE", "zh-TW-HsiaoChenNeural"
        )  # Edge TTS 預設語音
        self.speech_rate = os.getenv("TTS_SPEECH_RATE", "0%")  # 語速調整
        self.speech_pitch = os.getenv("TTS_SPEECH_PITCH", "0%")  # 音調調整

        logger.info(f"TTS 引擎: {self.tts_engine}")
        logger.info(f"語音: {self.voice_name}")

        # 檢查可用的 TTS 引擎
        self._check_available_engines()

        # 初始化選定的引擎
        self._initialize_engine()

    def _check_available_engines(self):
        """檢查可用的 TTS 引擎"""
        available_engines = []

        if EDGE_TTS_AVAILABLE:
            available_engines.append("edge")
        if GTTS_AVAILABLE:
            available_engines.append("gtts")
        if PYTTSX3_AVAILABLE:
            available_engines.append("pyttsx3")

        logger.info(f"可用的 TTS 引擎: {available_engines}")

        if not available_engines:
            raise RuntimeError("沒有可用的 TTS 引擎，請安裝至少一個 TTS 套件")

        if self.tts_engine not in available_engines:
            logger.warning(
                f"指定的引擎 {self.tts_engine} 不可用，使用第一個可用引擎: {available_engines[0]}"
            )
            self.tts_engine = available_engines[0]

    def _initialize_engine(self):
        """初始化選定的 TTS 引擎"""
        if self.tts_engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            self.pyttsx3_engine = pyttsx3.init()
            # 設定語音屬性
            voices = self.pyttsx3_engine.getProperty("voices")
            # 嘗試找到中文語音
            for voice in voices:
                if "chinese" in voice.name.lower() or "zh" in voice.id.lower():
                    self.pyttsx3_engine.setProperty("voice", voice.id)
                    break

            # 設定語速 (預設約 200)
            rate = self.pyttsx3_engine.getProperty("rate")
            self.pyttsx3_engine.setProperty("rate", max(100, min(300, rate)))

        logger.info(f"TTS 引擎 {self.tts_engine} 初始化完成")

    async def synthesize_edge_tts(self, text: str) -> bytes:
        """使用 Edge TTS 進行語音合成"""
        try:
            # 建立 Edge TTS 通訊物件
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_name,
                rate=self.speech_rate,
                pitch=self.speech_pitch,
            )

            # 收集音檔資料
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            return audio_data

        except Exception as e:
            logger.error(f"Edge TTS 合成失敗: {str(e)}")
            raise e

    def synthesize_gtts(self, text: str) -> bytes:
        """使用 Google TTS 進行語音合成"""
        try:
            # 建立 gTTS 物件
            tts = gTTS(text=text, lang="zh-tw", slow=False)

            # 儲存到記憶體
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            return audio_buffer.read()

        except Exception as e:
            logger.error(f"Google TTS 合成失敗: {str(e)}")
            raise e

    def synthesize_pyttsx3(self, text: str) -> bytes:
        """使用 pyttsx3 進行語音合成"""
        try:
            # 建立臨時檔案
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file_path = temp_file.name

            # 儲存到檔案
            self.pyttsx3_engine.save_to_file(text, temp_file_path)
            self.pyttsx3_engine.runAndWait()

            # 讀取檔案內容
            with open(temp_file_path, "rb") as f:
                audio_data = f.read()

            # 清理臨時檔案
            Path(temp_file_path).unlink()

            return audio_data

        except Exception as e:
            logger.error(f"pyttsx3 合成失敗: {str(e)}")
            raise e

    async def synthesize(self, text: str) -> bytes:
        """根據設定的引擎進行語音合成"""
        if not text or not text.strip():
            raise ValueError("文字內容不能為空")

        # 限制文字長度
        max_length = int(os.getenv("TTS_MAX_LENGTH", "500"))
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.warning(f"文字過長，已截斷至 {max_length} 字元")

        logger.info(f"開始合成語音: {text[:50]}...")

        try:
            if self.tts_engine == "edge" and EDGE_TTS_AVAILABLE:
                return await self.synthesize_edge_tts(text)
            elif self.tts_engine == "gtts" and GTTS_AVAILABLE:
                # gTTS 是同步的，在執行緒池中執行
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.synthesize_gtts, text)
            elif self.tts_engine == "pyttsx3" and PYTTSX3_AVAILABLE:
                # pyttsx3 是同步的，在執行緒池中執行
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.synthesize_pyttsx3, text)
            else:
                raise RuntimeError(f"TTS 引擎 {self.tts_engine} 不可用")

        except Exception as e:
            logger.error(f"語音合成失敗: {str(e)}")
            raise e

    def get_supported_voices(self) -> list:
        """取得支援的語音清單"""
        if self.tts_engine == "edge":
            # Edge TTS 支援的中文語音
            return [
                "zh-TW-HsiaoChenNeural",  # 台灣中文 (女)
                "zh-TW-YunJheNeural",  # 台灣中文 (男)
                "zh-TW-HsiaoYuNeural",  # 台灣中文 (女)
                "zh-CN-XiaoxiaoNeural",  # 大陸中文 (女)
                "zh-CN-YunxiNeural",  # 大陸中文 (男)
                "zh-HK-HiuMaanNeural",  # 香港中文 (女)
            ]
        elif self.tts_engine == "gtts":
            return ["zh-tw", "zh-cn"]
        elif self.tts_engine == "pyttsx3":
            if hasattr(self, "pyttsx3_engine"):
                voices = self.pyttsx3_engine.getProperty("voices")
                return [voice.id for voice in voices]
            return []

        return []


# 全域 TTS 服務實例
tts_service = None


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化服務"""
    global tts_service

    # 載入環境變數
    from dotenv import load_dotenv

    load_dotenv()

    logger.info("正在初始化 TTS 服務...")
    tts_service = TTSService()
    logger.info("TTS 服務初始化完成！")


@app.get("/")
def read_root():
    """健康檢查端點"""
    return {
        "message": "TTS 服務已啟動",
        "engine": tts_service.tts_engine if tts_service else "未初始化",
        "voice": tts_service.voice_name if tts_service else "未設定",
    }


@app.get("/health")
def health_check():
    """詳細的健康檢查"""
    if tts_service is None:
        return {"status": "error", "message": "TTS 服務尚未初始化"}

    return {
        "status": "healthy",
        "engine": tts_service.tts_engine,
        "voice": tts_service.voice_name,
        "available_engines": [
            "edge" if EDGE_TTS_AVAILABLE else None,
            "gtts" if GTTS_AVAILABLE else None,
            "pyttsx3" if PYTTSX3_AVAILABLE else None,
        ],
    }


@app.get("/voices")
def get_voices():
    """取得支援的語音清單"""
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS 服務尚未初始化")

    return {
        "engine": tts_service.tts_engine,
        "current_voice": tts_service.voice_name,
        "supported_voices": tts_service.get_supported_voices(),
    }


@app.post("/synthesize")
async def synthesize_speech(request: dict):
    """
    語音合成端點

    Args:
        request: 包含 text 欄位的 JSON 請求

    Returns:
        音檔資料 (MP3 格式)
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS 服務尚未初始化")

    text = request.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="文字內容不能為空")

    try:
        logger.info(f"收到語音合成請求: {text[:50]}...")

        # 進行語音合成
        audio_data = await tts_service.synthesize(text)

        if not audio_data:
            raise HTTPException(status_code=500, detail="語音合成失敗，未產生音檔資料")

        logger.info(f"語音合成完成，音檔大小: {len(audio_data)} bytes")

        # 根據引擎決定 MIME 類型
        if tts_service.tts_engine == "edge":
            media_type = "audio/mpeg"
        elif tts_service.tts_engine == "gtts":
            media_type = "audio/mpeg"
        elif tts_service.tts_engine == "pyttsx3":
            media_type = "audio/wav"
        else:
            media_type = "audio/mpeg"

        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "Content-Disposition": "attachment; filename=synthesized_speech.mp3"
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"語音合成時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")


@app.post("/synthesize_with_voice")
async def synthesize_with_voice(request: dict):
    """
    使用指定語音進行語音合成

    Args:
        request: 包含 text 和 voice 欄位的 JSON 請求
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS 服務尚未初始化")

    text = request.get("text", "").strip()
    voice = request.get("voice", "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="文字內容不能為空")

    try:
        # 暫時更改語音設定
        original_voice = tts_service.voice_name
        if voice and voice in tts_service.get_supported_voices():
            tts_service.voice_name = voice

        # 進行語音合成
        audio_data = await tts_service.synthesize(text)

        # 還原語音設定
        tts_service.voice_name = original_voice

        # 根據引擎決定 MIME 類型
        if tts_service.tts_engine == "edge":
            media_type = "audio/mpeg"
        elif tts_service.tts_engine == "gtts":
            media_type = "audio/mpeg"
        elif tts_service.tts_engine == "pyttsx3":
            media_type = "audio/wav"
        else:
            media_type = "audio/mpeg"

        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=synthesized_speech_{voice}.mp3"
            },
        )

    except Exception as e:
        logger.error(f"指定語音合成時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")


if __name__ == "__main__":
    # 從環境變數取得設定
    host = os.getenv("TTS_HOST", "0.0.0.0")
    port = int(os.getenv("TTS_PORT", "8003"))

    uvicorn.run(app, host=host, port=port, log_level="info")
