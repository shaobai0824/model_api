import io
import logging
import os
from pathlib import Path

import numpy as np
import torch
import torchaudio
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Breeze ASR Service",
    description="語音辨識服務 - 支援 Hugging Face 微調模型",
    version="1.0.0",
)


class ASRService:
    def __init__(self, model_name_or_path: str):
        """
        初始化 ASR 服務

        Args:
            model_name_or_path: Hugging Face 模型名稱或本地路徑
                               例如: "your-username/breeze-asr-finetuned"
        """
        self.model_name_or_path = model_name_or_path
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        logger.info(f"使用的裝置: {self.device}")
        logger.info(f"使用的資料型別: {self.torch_dtype}")

        self._load_model()

    def _load_model(self):
        """載入模型和處理器"""
        try:
            logger.info(f"正在載入模型: {self.model_name_or_path}")

            # 載入模型和處理器
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name_or_path,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model.to(self.device)

            self.processor = AutoProcessor.from_pretrained(self.model_name_or_path)

            # 建立 pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )

            logger.info("模型載入成功！")

        except Exception as e:
            logger.error(f"模型載入失敗: {str(e)}")
            raise e

    def transcribe(self, audio_input) -> dict:
        """
        進行語音辨識

        Args:
            audio_input: 音訊資料 (numpy array)

        Returns:
            dict: 包含辨識結果的字典
        """
        try:
            # 確保音訊是單聲道且為 numpy array
            if isinstance(audio_input, torch.Tensor):
                audio_input = audio_input.numpy()

            if audio_input.ndim > 1:
                audio_input = audio_input.mean(axis=0)  # 轉為單聲道

            # 進行語音辨識
            result = self.pipe(audio_input)

            return {
                "text": result["text"],
                "chunks": result.get("chunks", []),
                "confidence": getattr(result, "confidence", None),
            }

        except Exception as e:
            logger.error(f"語音辨識失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=f"語音辨識失敗: {str(e)}")


# 全域 ASR 服務實例
asr_service = None


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化模型"""
    global asr_service

    # 載入環境變數
    from dotenv import load_dotenv

    load_dotenv()

    # 從環境變數或預設值取得模型名稱
    model_name = os.getenv(
        "ASR_MODEL_NAME", "shaobai880824/breeze-asr-25-final-chinese"
    )

    logger.info("正在初始化 ASR 服務...")
    logger.info(f"使用模型: {model_name}")
    asr_service = ASRService(model_name)
    logger.info("ASR 服務初始化完成！")


@app.get("/")
def read_root():
    """健康檢查端點"""
    return {
        "message": "Breeze ASR 服務已啟動",
        "device": asr_service.device if asr_service else "未初始化",
        "model": asr_service.model_name_or_path if asr_service else "未載入",
    }


@app.get("/health")
def health_check():
    """詳細的健康檢查"""
    if asr_service is None:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "ASR 服務尚未初始化"},
        )

    return {
        "status": "healthy",
        "device": asr_service.device,
        "model": asr_service.model_name_or_path,
        "torch_dtype": str(asr_service.torch_dtype),
    }


async def load_audio_robust(audio_bytes: bytes, filename: str = "audio"):
    """
    強化的音檔載入方法，支援多種格式
    使用 Whisper 模型的內建音頻處理
    """
    import os
    import subprocess
    import tempfile

    # 方法1: 使用 Whisper 內建的音頻處理
    try:
        import whisper

        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # 使用 Whisper 的 load_audio 函數
            audio_data = whisper.load_audio(temp_path)
            # 轉換為 torch tensor 並添加 batch 維度
            waveform = torch.from_numpy(audio_data).unsqueeze(0)
            sample_rate = 16000  # Whisper 固定使用 16kHz
            logger.info("✅ 使用 Whisper 內建音頻處理載入成功")
            return waveform, sample_rate
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    except ImportError:
        logger.warning("⚠️ whisper 模組不可用")
    except Exception as e:
        logger.warning(f"⚠️ Whisper 音頻處理失敗: {str(e)}")

    # 方法2: 直接使用 torchaudio
    try:
        waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
        logger.info("✅ 使用 torchaudio 直接載入成功")
        return waveform, sample_rate
    except Exception as e:
        logger.warning(f"⚠️ torchaudio 直接載入失敗: {str(e)}")

    # 方法3: 儲存為臨時檔案後載入
    try:
        # 根據檔名判斷副檔名
        if filename.lower().endswith(".m4a"):
            suffix = ".m4a"
        elif filename.lower().endswith(".mp3"):
            suffix = ".mp3"
        elif filename.lower().endswith(".wav"):
            suffix = ".wav"
        else:
            suffix = ".m4a"  # 預設為 m4a

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            waveform, sample_rate = torchaudio.load(temp_path)
            logger.info(f"✅ 使用臨時檔案載入成功: {suffix}")
            return waveform, sample_rate
        finally:
            # 清理臨時檔案
            try:
                os.unlink(temp_path)
            except:
                pass

    except Exception as e:
        logger.warning(f"⚠️ 臨時檔案載入失敗: {str(e)}")

    # 方法4: 嘗試使用 librosa (如果安裝了)
    try:
        import librosa
        import numpy as np

        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # 使用 librosa 載入
            audio_data, sample_rate = librosa.load(temp_path, sr=None)
            # 轉換為 torch tensor
            waveform = torch.from_numpy(audio_data).unsqueeze(0)  # 添加 channel 維度
            logger.info("✅ 使用 librosa 載入成功")
            return waveform, sample_rate
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    except ImportError:
        logger.warning("⚠️ librosa 未安裝，跳過此方法")
    except Exception as e:
        logger.warning(f"⚠️ librosa 載入失敗: {str(e)}")

    # 所有方法都失敗
    raise Exception(
        f"無法載入音檔，已嘗試所有可用方法。檔案大小: {len(audio_bytes)} bytes"
    )


@app.post("/recognize")
async def recognize_speech(audio_file: UploadFile = File(...)):
    """
    語音辨識端點，依賴 FFmpeg 處理各種音訊格式
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR 服務尚未初始化")

    try:
        # 讀取上傳的音檔內容
        audio_bytes = await audio_file.read()
        logger.info(
            f"接收到音檔: {audio_file.filename}, 大小: {len(audio_bytes)} bytes"
        )

        # 直接將音訊 bytes 交給 pipeline 處理
        # Transformers pipeline 會在內部調用 ffmpeg (如果已安裝並在 PATH 中)
        logger.info("開始進行語音辨識...")
        result = asr_service.pipe(audio_bytes)

        transcription = result["text"]
        logger.info(f"辨識完成: {transcription[:100]}...")

        return {
            "success": True,
            "transcription": transcription,
        }

    except Exception as e:
        logger.error(f"處理音檔時發生錯誤: {str(e)}", exc_info=True)
        # 檢查常見的 ffmpeg 錯誤
        if "ffmpeg" in str(e).lower() or "format not recognised" in str(e).lower():
            detail = (
                f"處理音檔失敗: FFmpeg 可能未正確安裝或未在 PATH 中。錯誤: {str(e)}"
            )
        else:
            detail = f"處理音檔失敗: {str(e)}"

        raise HTTPException(status_code=500, detail=detail)


@app.post("/recognize_url")
async def recognize_from_url(audio_url: str):
    """
    從 URL 進行語音辨識 (用於 LINE Bot 的音檔 URL)

    Args:
        audio_url: 音檔的 URL

    Returns:
        dict: 辨識結果
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR 服務尚未初始化")

    try:
        import requests

        # 下載音檔
        response = requests.get(audio_url, timeout=30)
        response.raise_for_status()

        audio_bytes = response.content
        logger.info(f"從 URL 下載音檔，大小: {len(audio_bytes)} bytes")

        # 使用相同的處理邏輯
        waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))

        target_sample_rate = 16000
        if sample_rate != target_sample_rate:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sample_rate, new_freq=target_sample_rate
            )
            waveform = resampler(waveform)

        audio_input = waveform.squeeze().numpy()

        # 進行語音辨識
        result = asr_service.transcribe(audio_input)

        return {
            "success": True,
            "text": result["text"],
            "chunks": result.get("chunks", []),
            "audio_info": {
                "duration": len(audio_input) / target_sample_rate,
                "sample_rate": target_sample_rate,
                "channels": "mono",
            },
        }

    except Exception as e:
        logger.error(f"從 URL 處理音檔時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"從 URL 處理音檔失敗: {str(e)}")


if __name__ == "__main__":
    # 從環境變數取得設定
    host = os.getenv("ASR_HOST", "0.0.0.0")
    port = int(os.getenv("ASR_PORT", "8001"))

    uvicorn.run(app, host=host, port=port, log_level="info")
