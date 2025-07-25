﻿import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import aiohttp
import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

# LINE Bot SDK
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    AudioMessage,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import AudioMessageContent, MessageEvent, TextMessageContent

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="LINE Bot Service",
    description="具備語音辨識和記憶功能的智能 LINE Bot",
    version="1.0.0",
)


class LineBotService:
    def __init__(self):
        """初始化 LINE Bot 服務"""
        # LINE Bot 設定
        self.channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.channel_secret = os.getenv("LINE_CHANNEL_SECRET")

        # 開發模式，允許在沒有 LINE Token 的情況下測試
        self.dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"

        if not self.channel_access_token or not self.channel_secret:
            if not self.dev_mode:
                raise ValueError(
                    "請設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數"
                )
            else:
                logger.warning("⚠️ 開發模式：LINE Bot Token 未設定，僅供測試使用")
                self.channel_access_token = "dev_token"
                self.channel_secret = "dev_secret"

        # LINE Bot API 設定
        if not self.dev_mode:
            self.configuration = Configuration(access_token=self.channel_access_token)
            self.handler = WebhookHandler(self.channel_secret)
        else:
            # 開發模式不需要真實配置
            self.configuration = None
            self.handler = None
            logger.info("🔧 開發模式：跳過 LINE Bot API 初始化")

        # 服務端點設定
        self.asr_service_url = os.getenv("ASR_SERVICE_URL", "http://localhost:8001")
        self.llm_service_url = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")
        self.tts_service_url = os.getenv("TTS_SERVICE_URL", "http://localhost:8003")
        # 新增：記憶服務端點
        self.memory_service_url = os.getenv(
            "MEMORY_SERVICE_URL", "http://localhost:8004"
        )

        # OpenAI API 設定 (作為 LLM 的選項)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"

        logger.info("✅ LINE Bot 服務初始化完成")
        logger.info(f"ASR 服務: {self.asr_service_url}")
        logger.info(f"LLM 服務: {self.llm_service_url}")
        logger.info(f"TTS 服務: {self.tts_service_url}")
        logger.info(f"記憶 服務: {self.memory_service_url}")
        logger.info(f"使用 OpenAI: {self.use_openai}")

        # 註冊事件處理器（非開發模式才註冊）
        if not self.dev_mode:
            self._register_handlers()
        else:
            logger.info("🔧 開發模式：跳過事件處理器註冊")
            self._register_dev_handlers()

    def _register_handlers(self):
        """註冊 LINE Bot 事件處理器"""

        @self.handler.add(MessageEvent, message=AudioMessageContent)
        def handle_audio_message(event):
            """處理語音訊息"""
            logger.info(f"收到語音訊息: {event.message.id}")

            # 使用異步任務處理語音
            asyncio.create_task(self.process_audio_message(event))

        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event):
            """處理文字訊息"""
            logger.info(f"收到文字訊息: {event.message.text}")

            # 使用異步任務處理文字
            asyncio.create_task(self.process_text_message(event))

    def _register_dev_handlers(self):
        """註冊開發模式事件處理器（不依賴 LINE SDK）"""
        # 在開發模式下，我們手動解析 webhook 請求
        # 而不是使用 LINE SDK 的事件處理器
        logger.info("🔧 開發模式：事件處理器使用 webhook 請求手動解析")

    async def handle_webhook_manually(self, webhook_body: str):
        """開發模式：手動處理 LINE Webhook 請求"""
        try:
            import json

            # 解析 JSON
            webhook_data = json.loads(webhook_body)
            events = webhook_data.get("events", [])

            for event in events:
                event_type = event.get("type")
                message = event.get("message", {})
                reply_token = event.get("replyToken")

                logger.info(
                    f"📨 處理事件: {event_type}, 訊息類型: {message.get('type')}"
                )

                if event_type == "message":
                    message_type = message.get("type")

                    if message_type == "audio":
                        # 語音訊息
                        logger.info("🎵 處理語音訊息")
                        await self.handle_audio_message_dev(message, reply_token)

                    elif message_type == "text":
                        # 文字訊息
                        text_content = message.get("text", "")
                        logger.info(f"💬 處理文字訊息: {text_content}")
                        await self.handle_text_message_dev(text_content, reply_token)

        except Exception as e:
            logger.error(f"手動處理 Webhook 失敗: {str(e)}")
            raise

    async def handle_audio_message_dev(self, message, reply_token):
        """開發模式：處理語音訊息"""
        try:
            message_id = message.get("id")
            logger.info(f"📱 開發模式處理語音訊息: {message_id}")

            # 1. 下載語音（開發模式下跳過，因為需要真實的 LINE Token）
            logger.info("🔧 開發模式：跳過實際 LINE 語音下載，使用 ASR 測試音檔")

            # 2. 使用預設文字（實際應該是語音辨識結果）
            recognized_text = "抱歉，開發模式下無法處理真實語音內容"
            logger.info(f"🎯 語音辨識結果: {recognized_text}")

            # 3. LLM 回應
            llm_response = await self.get_llm_response(recognized_text)
            if not llm_response:
                llm_response = "抱歉，語音處理功能在開發模式下無法完整運作。請設定正確的 LINE Token 後重新測試。"

            logger.info(f"🤖 LLM 回應: {llm_response}")

            # 4. 回覆（開發模式下只能記錄到 LINE）
            logger.info(f"📤 開發模式：應回覆到 LINE：{llm_response}")

        except Exception as e:
            logger.error(f"開發模式處理語音訊息失敗: {str(e)}")

    async def handle_text_message_dev(self, text_content, reply_token):
        """開發模式：處理文字訊息"""
        try:
            logger.info(f"📝 開發模式處理: {text_content}")

            # 特殊指令處理
            if text_content.lower() in ["/help", "幫助", "說明"]:
                response = "🤖 開發模式說明：\n目前在開發模式下運行，無法真正回覆到 LINE。\n請設定 LINE Token 後重新測試。"
            elif text_content.lower() in ["/status", "狀態"]:
                response = await self.check_services_status()
            else:
                # LLM 回應
                response = await self.get_llm_response(text_content)
                if not response:
                    response = f"收到您的訊息：{text_content}\n目前在開發模式下運行。"

            logger.info(f"📤 開發模式回應: {response}")

        except Exception as e:
            logger.error(f"開發模式處理文字訊息失敗: {str(e)}")

    async def process_audio_message(self, event):
        """處理語音訊息的完整流程（正式模式）"""
        user_id = (
            event.source.user_id if hasattr(event.source, "user_id") else "unknown"
        )

        try:
            # 1. 下載語音
            audio_content = await self.download_audio_content(event.message.id)
            if not audio_content:
                await self.reply_text(event.reply_token, "抱歉，無法下載語音檔案。")
                return

            # 2. 語音辨識
            recognized_text = await self.transcribe_audio(audio_content)
            if not recognized_text:
                await self.reply_text(event.reply_token, "抱歉，無法辨識您的語音內容。")
                return

            logger.info(f"語音辨識結果: {recognized_text}")

            # 新增 3. 將用戶語音訊息加入記憶
            await self.add_message_to_memory(user_id, "user", recognized_text, "voice")

            # 4. 獲取智能回應 (使用記憶上下文)
            llm_response = await self.get_llm_response_with_memory(
                user_id, recognized_text
            )
            if not llm_response:
                await self.reply_text(event.reply_token, "抱歉，無法產生回應。")
                return

            logger.info(f"LLM 回應: {llm_response}")

            # 新增 5. 將助手回應加入記憶
            await self.add_message_to_memory(
                user_id, "assistant", llm_response, "voice"
            )

            # 6. 語音合成
            audio_file_path = await self.synthesize_speech(llm_response)
            if not audio_file_path:
                # 如果語音合成失敗，回傳文字
                await self.reply_text(event.reply_token, llm_response)
                return

            # 7. 回覆語音訊息
            await self.reply_audio(event.reply_token, audio_file_path)

            # 清理臨時檔案
            if audio_file_path and Path(audio_file_path).exists():
                Path(audio_file_path).unlink()

        except Exception as e:
            logger.error(f"處理語音訊息失敗: {str(e)}")
            await self.reply_text(event.reply_token, "抱歉，語音處理過程中發生錯誤。")

    async def process_text_message(self, event):
        """處理文字訊息 (正式模式)"""
        user_id = (
            event.source.user_id if hasattr(event.source, "user_id") else "unknown"
        )

        try:
            text = event.message.text

            # 特殊指令處理
            if text.lower() in ["/help", "幫助", "說明"]:
                help_text = """
🤖 語音助手使用說明：

🎵 語音訊息：傳送語音後，我會：
1. 辨識您的語音內容
2. 透過 AI 產生回應
3. 轉換成語音回覆

💬 文字訊息：直接文字對話

🧠 記憶功能：我會記住我們的對話

📊 指令：
/help - 顯示此幫助訊息
/status - 檢查服務狀態
/stats - 查看對話統計
/clear - 清除對話記憶
/formal - 設定正式語調
/casual - 設定輕鬆語調
                """
                await self.reply_text(event.reply_token, help_text)
                return

            elif text.lower() in ["/status", "狀態"]:
                status = await self.check_services_status()
                await self.reply_text(event.reply_token, status)
                return

            elif text.lower() in ["/stats", "統計"]:
                stats = await self.get_user_stats(user_id)
                await self.reply_text(event.reply_token, stats)
                return

            elif text.lower() in ["/clear", "清除記憶"]:
                success = await self.clear_user_memory(user_id)
                if success:
                    await self.reply_text(event.reply_token, "✅ 已清除所有對話記憶！")
                else:
                    await self.reply_text(event.reply_token, "❌ 清除記憶失敗")
                return

            elif text.lower() in ["/formal", "正式"]:
                await self.set_user_preference(user_id, "language", "formal")
                await self.reply_text(event.reply_token, "✅ 已設定為正式語調")
                return

            elif text.lower() in ["/casual", "輕鬆"]:
                await self.set_user_preference(user_id, "language", "casual")
                await self.reply_text(event.reply_token, "✅ 已設定為輕鬆語調")
                return

            # 新增 將用戶文字訊息加入記憶
            await self.add_message_to_memory(user_id, "user", text, "text")

            # 一般文字對話(使用記憶上下文)
            llm_response = await self.get_llm_response_with_memory(user_id, text)
            if llm_response:
                # 新增 將助手回應加入記憶
                await self.add_message_to_memory(
                    user_id, "assistant", llm_response, "text"
                )

                # 嘗試語音合成
                audio_file_path = await self.synthesize_speech(llm_response)
                if audio_file_path:
                    await self.reply_audio(event.reply_token, audio_file_path)
                    # 清理臨時檔案
                    if Path(audio_file_path).exists():
                        Path(audio_file_path).unlink()
                else:
                    await self.reply_text(event.reply_token, llm_response)
            else:
                await self.reply_text(event.reply_token, "抱歉，無法產生回應。")

        except Exception as e:
            logger.error(f"處理文字訊息失敗: {str(e)}")
            await self.reply_text(event.reply_token, "抱歉，文字處理過程中發生錯誤。")

    async def download_audio_content(self, message_id: str) -> Optional[bytes]:
        """下載語音內容並進行驗證"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"🔽 嘗試下載語音內容 (第 {attempt + 1}/{max_retries} 次): {message_id}"
                )

                # 檢查配置
                if not self.configuration.access_token:
                    logger.error("❌ LINE Channel Access Token 未設定")
                    return None

                    # 使用同步 API，LINE Bot SDK 不支援異步
                with ApiClient(self.configuration) as api_client:
                    line_bot_blob_api = MessagingApiBlob(api_client)

                    # 下載語音內容
                    audio_content = line_bot_blob_api.get_message_content(
                        message_id=message_id
                    )

                    if audio_content and len(audio_content) > 0:
                        logger.info(
                            f"✅ 成功下載語音內容，大小: {len(audio_content)} 位元組"
                        )

                        # 驗證音檔格式
                        if self.validate_audio_content(audio_content):
                            # 保存音檔供調試用
                            await self.save_audio_for_debug(audio_content, message_id)
                            return audio_content
                        else:
                            logger.warning("⚠️ 音檔格式驗證失敗，但仍嘗試處理")
                            return audio_content  # 仍然返回，讓 ASR 嘗試處理
                    else:
                        logger.warning(f"⚠️ 下載的音檔內容為空")

            except Exception as e:
                logger.error(f"❌ 第 {attempt + 1} 次下載失敗: {str(e)}")

                if attempt < max_retries - 1:
                    logger.info(f"⏳ 等待 {retry_delay} 秒後重試...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避
                else:
                    logger.error("❌ 所有下載嘗試均失敗")

        return None

    def validate_audio_content(self, audio_content: bytes) -> bool:
        """驗證音檔內容"""
        try:
            # 檢查檔案大小
            if len(audio_content) < 100:  # 太小的音檔可能無效
                logger.warning(f"⚠️ 音檔太小: {len(audio_content)} 位元組")
                return False

            # 檢查檔案簽名 (M4A 格式)
            if (
                audio_content[:4] == b"\x00\x00\x00\x20"
                or audio_content[4:8] == b"ftyp"
            ):
                logger.info("✅ 檢測到 M4A 格式")
                return True

            # 檢查其他常見音檔格式
            if audio_content[:3] == b"ID3" or audio_content[:2] == b"\xff\xfb":
                logger.info("✅ 檢測到 MP3 格式")
                return True

            if audio_content[:4] == b"RIFF":
                logger.info("✅ 檢測到 WAV 格式")
                return True

            logger.warning("⚠️ 未知音檔格式")
            return False

        except Exception as e:
            logger.error(f"音檔驗證失敗: {str(e)}")
            return False

    async def save_audio_for_debug(self, audio_content: bytes, message_id: str) -> str:
        """保存音檔供調試用"""
        try:
            debug_dir = "debug_audio"
            os.makedirs(debug_dir, exist_ok=True)

            file_path = os.path.join(debug_dir, f"audio_{message_id}.m4a")

            with open(file_path, "wb") as f:
                f.write(audio_content)

            logger.info(f"💾 調試音檔已保存至: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"保存調試音檔失敗: {str(e)}")
            return ""

    async def transcribe_audio(self, audio_content: bytes) -> Optional[str]:
        """透過 ASR 服務進行語音辨識"""
        logger.info(f"🎯 開始語音辨識，檔案大小: {len(audio_content)} 位元組")
        try:
            async with aiohttp.ClientSession() as session:
                # 建立臨時檔案
                with tempfile.NamedTemporaryFile(
                    suffix=".m4a", delete=False
                ) as temp_file:
                    temp_file.write(audio_content)
                    temp_file_path = temp_file.name

                # 讀取檔案並上傳
                with open(temp_file_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "audio_file",
                        f,
                        filename="audio.m4a",
                        content_type="audio/x-m4a",
                    )

                    async with session.post(
                        f"{self.asr_service_url}/recognize",
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=120),  # 2 分鐘超時
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            # ASR 服務返回 transcription 欄位，不是 text
                            transcription = result.get("transcription", "")
                            logger.info(f"🎯 ASR 辨識結果: {transcription}")
                            return transcription
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"ASR 服務回應錯誤: {response.status}, 詳細: {error_text}"
                            )
                            return None

        except Exception as e:
            logger.error(f"語音辨識失敗: {str(e)}", exc_info=True)
            return None
        finally:
            # 清理臨時檔案
            if "temp_file_path" in locals() and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()

    async def get_llm_response(self, text: str) -> Optional[str]:
        """獲取智能回應"""
        if self.use_openai and self.openai_api_key:
            return await self.get_openai_response(text)
        else:
            return await self.get_local_llm_response(text)

    async def get_openai_response(self, text: str) -> Optional[str]:
        """使用 OpenAI API 獲取回應"""
        import asyncio

        # 如果 OpenAI API 不可用，使用智能後備回應
        fallback_response = self.generate_smart_fallback(text)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一個親切的AI助手，請用繁體中文簡潔地回答問題。",
                        },
                        {"role": "user", "content": text},
                    ],
                    "max_tokens": 150,
                    "temperature": 0.7,
                }

                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    elif response.status == 429:
                        logger.warning("OpenAI API 額度不足，使用後備回應")
                        return fallback_response
                    else:
                        logger.error(f"OpenAI API 錯誤: {response.status}")
                        return fallback_response

        except asyncio.TimeoutError:
            logger.warning("OpenAI API 超時，使用後備回應")
            return fallback_response
        except Exception as e:
            logger.error(f"OpenAI API 呼叫失敗: {str(e)}")
            return fallback_response

    def generate_smart_fallback(self, text: str) -> str:
        """智能後備回應"""
        text_lower = text.lower()

        # 問候
        if any(word in text_lower for word in ["你好", "哈囉", "hello", "hi", "嗨"]):
            return "你好！我是語音智能助手，很高興為您服務！有什麼我可以幫助您的嗎？"

        # 問題類
        elif any(
            word in text
            for word in ["什麼", "怎麼", "如何", "為什麼", "哪裡", "誰", "何時", "多少"]
        ):
            return f"關於「{text}」這個問題，我建議您可以：\n1. 查詢相關資料\n2. 諮詢專家\n3. 網路搜尋\n\n如果有其他具體問題，歡迎繼續詢問我！"

        # 健康類問題
        elif any(word in text for word in ["健康", "醫療", "生病", "症狀", "藥物"]):
            return "關於健康問題，我建議：\n1. 諮詢專業醫師\n2. 定期健康檢查\n3. 維持良好生活習慣\n\n如果有緊急狀況，請立即就醫！"

        # 時間
        elif any(word in text for word in ["時間", "現在", "幾點"]):
            from datetime import datetime

            now = datetime.now()
            return f"現在時間是 {now.strftime('%Y年%m月%d日 %H:%M')}。\n\n很高興為您提供時間資訊！"

        # 感謝
        elif any(word in text for word in ["謝謝", "感謝", "thanks", "thank you"]):
            return "不客氣！很高興能幫助您。如果還有其他問題，隨時歡迎詢問！"

        # 幫助
        elif any(word in text for word in ["幫助", "協助", "說明", "幫忙"]):
            return """我是語音智能助手，可以為您：

🎵 **語音辨識**：處理您的語音並轉為文字
🧠 **記憶對話**：記住我們的對話內容
💬 **智能回應**：提供有用的資訊和建議

📝 **使用方式**：
- 直接傳送語音訊息
- 或輸入文字與我對話
- 輸入指令獲得更多功能

有什麼需要幫忙的嗎？"""

        # 一般不認識的內容
        else:
            return f"""收到您的訊息「{text}」。

我是 AI 智能助手，目前正在學習中。

🤖 **我可以協助您：**
- 回答一般問題
- 進行語音辨識
- 提供資訊查詢

💡 **建議嘗試：**
- 詢問具體問題
- 描述您的需求
- 使用語音功能

需要其他協助嗎？"""

    async def get_local_llm_response(self, text: str) -> Optional[str]:
        """使用本地 LLM 服務獲取回應"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": text}

                async with session.post(
                    f"{self.llm_service_url}/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"本地 LLM 服務錯誤: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"本地 LLM 服務呼叫失敗: {str(e)}")
            return None

    async def synthesize_speech(self, text: str) -> Optional[str]:
        """透過 TTS 服務進行語音合成"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": text}

                async with session.post(
                    f"{self.tts_service_url}/synthesize",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        # 獲取音檔資料並儲存
                        audio_data = await response.read()
                        temp_file = tempfile.NamedTemporaryFile(
                            suffix=".mp3", delete=False
                        )
                        temp_file.write(audio_data)
                        temp_file.close()
                        return temp_file.name
                    else:
                        logger.error(f"TTS 服務錯誤: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"語音合成失敗: {str(e)}")
            return None

    async def reply_text(self, reply_token: str, text: str):
        """回覆文字訊息"""
        try:
            # LINE Bot API 不支援異步，使用同步模式
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token, messages=[TextMessage(text=text)]
                    )
                )
                logger.info(f"✅ 成功回覆文字訊息: {text[:50]}...")
        except Exception as e:
            logger.error(f"回覆文字訊息失敗: {str(e)}")
            # 如果回覆失敗，至少記錄內容
            logger.info(f"📝 原本要回覆的內容: {text}")

    async def reply_audio(self, reply_token: str, audio_file_path: str):
        """回覆語音訊息"""
        try:
            # 暫時改為回覆音檔下載連結，因為需要建立公開的URL
            # 實際部署時，需要音檔託管服務
            await self.reply_text(
                reply_token, "語音合成已完成，但需要設定音檔託管服務。"
            )
        except Exception as e:
            logger.error(f"回覆語音訊息失敗: {str(e)}")

    async def check_services_status(self) -> str:
        """檢查各服務狀態"""
        status_info = []

        # 檢查 ASR 服務
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.asr_service_url}/health", timeout=5
                ) as response:
                    if response.status == 200:
                        status_info.append("✅ ASR 服務：正常")
                    else:
                        status_info.append("❌ ASR 服務：異常")
        except:
            status_info.append("❌ ASR 服務：無法連接")

        # 檢查 LLM 服務
        if self.use_openai:
            status_info.append("✅ LLM 服務：OpenAI API")
        else:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.llm_service_url}/health", timeout=5
                    ) as response:
                        if response.status == 200:
                            status_info.append("✅ LLM 服務：正常")
                        else:
                            status_info.append("❌ LLM 服務：異常")
            except:
                status_info.append("❌ LLM 服務：無法連接")

        # 檢查 TTS 服務
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.tts_service_url}/health", timeout=5
                ) as response:
                    if response.status == 200:
                        status_info.append("✅ TTS 服務：正常")
                    else:
                        status_info.append("❌ TTS 服務：異常")
        except:
            status_info.append("❌ TTS 服務：無法連接")

        return "🔍 服務狀態檢查結果：\n\n" + "\n".join(status_info)

    # 新增 ========== 記憶功能相關方法 ==========

    async def add_message_to_memory(
        self, user_id: str, role: str, content: str, message_type: str = "text"
    ) -> bool:
        """添加訊息到記憶服務"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "message_type": message_type,
                }

                async with session.post(
                    f"{self.memory_service_url}/add_message",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.debug(f"🧠 已為用戶 {user_id} 添加 {role} 訊息到記憶")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"🧠 添加訊息到記憶失敗: {response.status}, {error_text}"
                        )
                        return False

        except Exception as e:
            logger.error(f"🧠 記憶服務錯誤: {e}")
            return False

    async def get_conversation_context(self, user_id: str) -> list:
        """獲取用戶對話上下文"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.memory_service_url}/conversation_context/{user_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        context = result.get("context", [])
                        logger.debug(
                            f"🧠 為用戶 {user_id} 獲取了 {len(context)} 條上下文"
                        )
                        return context
                    else:
                        logger.error(f"🧠 獲取對話上下文失敗: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"🧠 獲取對話上下文失敗: {e}")
            return []

    async def get_llm_response_with_memory(
        self, user_id: str, current_message: str
    ) -> Optional[str]:
        """使用記憶上下文獲取 LLM 回應"""
        try:
            # 獲取對話上下文
            context_messages = await self.get_conversation_context(user_id)

            if self.use_openai and self.openai_api_key:
                # 使用 OpenAI API 處理帶上下文的對話
                return await self.get_openai_response_with_context(
                    context_messages, current_message
                )
            else:
                # 使用本地 LLM 服務，暫時只傳遞當前訊息
                return await self.get_llm_response(current_message)

        except Exception as e:
            logger.error(f"🧠 使用記憶獲取 LLM 回應失敗: {e}")
            # 降級到無記憶模式
            return await self.get_llm_response(current_message)

    async def get_openai_response_with_context(
        self, context_messages: list, current_message: str
    ) -> Optional[str]:
        """使用 OpenAI API 與上下文生成回應"""
        try:
            # 準備訊息列表
            messages = context_messages.copy()

            # 如果沒有系統訊息，添加一個
            if not messages or messages[0]["role"] != "system":
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": "你是一個友善且有用的 AI 助手。你能夠記住我們之前的對話內容，並提供連貫的回應。",
                    },
                )

            # 添加當前用戶訊息
            messages.append({"role": "user", "content": current_message})

            # 呼叫 OpenAI API (使用新版 API)
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )

            assistant_message = response.choices[0].message.content.strip()
            logger.info(f"🤖 OpenAI 回應 (含記憶): {assistant_message[:50]}...")
            return assistant_message

        except Exception as e:
            logger.error(f"🤖 OpenAI API 錯誤 (含記憶): {e}")
            return self.generate_smart_fallback(current_message)

    async def get_user_stats(self, user_id: str) -> str:
        """獲取用戶統計資訊"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.memory_service_url}/user_stats/{user_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        stats = result.get("stats", {})

                        stats_text = f"""
📊 您的對話統計資訊：

💬 總訊息數量：{stats.get('total_messages', 0)}
🔄 本次會話訊息：{stats.get('current_session_messages', 0)}
🎵 語音訊息：{stats.get('voice_messages', 0)}
💬 文字訊息：{stats.get('text_messages', 0)}
🤖 AI 回應：{stats.get('assistant_messages', 0)}
⏰ 最後互動：{stats.get('last_interaction', 'N/A')}

設定偏好：{stats.get('preferences', {})}
                        """
                        return stats_text.strip()
                    else:
                        return "❌ 無法獲取統計資訊"

        except Exception as e:
            logger.error(f"🧠 獲取用戶統計失敗: {e}")
            return "❌ 獲取統計資訊時發生錯誤"

    async def clear_user_memory(self, user_id: str) -> bool:
        """清除用戶記憶"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {"user_id": user_id}

                async with session.post(
                    f"{self.memory_service_url}/clear_memory",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info(f"🧠 已清除用戶 {user_id} 的記憶")
                        return True
                    else:
                        logger.error(f"🧠 清除記憶失敗: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"🧠 清除記憶失敗: {e}")
            return False

    async def set_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """設定用戶偏好"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {"user_id": user_id, "key": key, "value": value}

                async with session.post(
                    f"{self.memory_service_url}/set_preference",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info(f"🧠 已為用戶 {user_id} 設定偏好 {key}={value}")
                        return True
                    else:
                        logger.error(f"🧠 設定偏好失敗: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"🧠 設定偏好失敗: {e}")
            return False


# 全域服務實例
linebot_service = None


@app.on_event("startup")
async def startup_event():
    """應用程式啟動事件"""
    global linebot_service

    # 載入環境變數
    from dotenv import load_dotenv

    load_dotenv()

    logger.info("正在初始化 LINE Bot 服務...")
    linebot_service = LineBotService()
    logger.info("LINE Bot 服務初始化完成")


@app.get("/")
def read_root():
    """根路徑檢查端點"""
    if not linebot_service:
        return {
            "message": "LINE Bot 服務初始化中...",
            "status": "initializing",
        }

    return {
        "message": "LINE Bot 服務運行中",
        "status": "healthy",
        "dev_mode": linebot_service.dev_mode,
        "services": {
            "asr": linebot_service.asr_service_url,
            "llm": linebot_service.llm_service_url,
            "tts": linebot_service.tts_service_url,
        },
    }


@app.post("/test_voice")
async def test_voice_processing(audio_file: UploadFile = File(...)):
    """開發模式：測試語音處理流程"""
    if not linebot_service:
        raise HTTPException(status_code=503, detail="服務未就緒")

    if not linebot_service.dev_mode:
        raise HTTPException(status_code=403, detail="此功能僅在開發模式下可用")

    try:
        logger.info("🧪 開發模式：測試語音處理流程")

        # 讀取上傳的音檔
        audio_content = await audio_file.read()

        # 語音辨識
        recognized_text = await linebot_service.transcribe_audio(audio_content)
        if not recognized_text:
            return JSONResponse(content={"success": False, "error": "語音辨識失敗"})

        # LLM 回應
        llm_response = await linebot_service.get_llm_response(recognized_text)
        if not llm_response:
            return JSONResponse(content={"success": False, "error": "LLM 回應生成失敗"})

        return JSONResponse(
            content={
                "success": True,
                "recognized_text": recognized_text,
                "llm_response": llm_response,
                "message": "語音處理測試完成",
            }
        )

    except Exception as e:
        logger.error(f"測試語音處理失敗: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@app.post("/webhook")
async def webhook(request: Request):
    """LINE Bot Webhook 端點"""
    if not linebot_service:
        raise HTTPException(status_code=503, detail="服務未就緒")

    # 取得請求內容
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 開發模式：跳過簽名驗證並手動解析請求
    if linebot_service.dev_mode:
        logger.info("🔧 開發模式：收到 Webhook 請求，跳過簽名驗證")
        try:
            # 解析 LINE 請求
            webhook_body = body.decode("utf-8")
            logger.info(f"📨 Webhook 內容: {webhook_body}")

            # 手動處理 LINE 請求
            await linebot_service.handle_webhook_manually(webhook_body)

            return JSONResponse(content={"status": "ok"})
        except Exception as e:
            logger.error(f"開發模式處理 Webhook 失敗: {str(e)}")
            return JSONResponse(content={"status": "error", "message": str(e)})

    # 正式模式：使用 LINE SDK 處理
    try:
        linebot_service.handler.handle(body.decode("utf-8"), signature)
        return JSONResponse(content={"status": "ok"})
    except InvalidSignatureError:
        logger.error("LINE Webhook 簽名驗證失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"處理 Webhook 失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    # 從環境變數讀取主機和埠號
    host = os.getenv("LINEBOT_HOST", "0.0.0.0")
    port = int(os.getenv("LINEBOT_PORT", "8000"))

    uvicorn.run(app, host=host, port=port, log_level="debug")
