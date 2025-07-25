import asyncio
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
    description="整合語音辨識、大語言模型和語音合成的 LINE Bot",
    version="1.0.0",
)


class LineBotService:
    def __init__(self):
        """初始化 LINE Bot 服務"""
        # LINE Bot 設定
        self.channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.channel_secret = os.getenv("LINE_CHANNEL_SECRET")

        # 開發模式：允許在沒有 LINE Token 的情況下啟動服務
        self.dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"

        if not self.channel_access_token or not self.channel_secret:
            if not self.dev_mode:
                raise ValueError(
                    "請設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數"
                )
            else:
                logger.warning("⚠️  開發模式：LINE Bot Token 未設定，部分功能將無法使用")
                self.channel_access_token = "dev_token"
                self.channel_secret = "dev_secret"

        # LINE Bot API 設定
        if not self.dev_mode:
            self.configuration = Configuration(access_token=self.channel_access_token)
            self.handler = WebhookHandler(self.channel_secret)
        else:
            # 開發模式：創建虛擬配置
            self.configuration = None
            self.handler = None
            logger.info("🔧 開發模式：跳過 LINE Bot API 初始化")

        # 服務端點設定
        self.asr_service_url = os.getenv("ASR_SERVICE_URL", "http://localhost:8001")
        self.llm_service_url = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")
        self.tts_service_url = os.getenv("TTS_SERVICE_URL", "http://localhost:8003")

        # OpenAI API 設定 (作為 LLM 的替代選項)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"

        logger.info("LINE Bot 服務初始化完成")
        logger.info(f"ASR 服務: {self.asr_service_url}")
        logger.info(f"LLM 服務: {self.llm_service_url}")
        logger.info(f"TTS 服務: {self.tts_service_url}")
        logger.info(f"使用 OpenAI: {self.use_openai}")

        # 註冊事件處理器 (開發模式也需要處理訊息)
        if not self.dev_mode:
            self._register_handlers()
        else:
            logger.info("🔧 開發模式：註冊簡化事件處理器")
            self._register_dev_handlers()

    def _register_handlers(self):
        """註冊 LINE Bot 事件處理器"""

        @self.handler.add(MessageEvent, message=AudioMessageContent)
        def handle_audio_message(event):
            """處理語音訊息"""
            logger.info(f"收到語音訊息: {event.message.id}")

            # 在背景處理語音訊息
            asyncio.create_task(self.process_audio_message(event))

        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event):
            """處理文字訊息"""
            logger.info(f"收到文字訊息: {event.message.text}")

            # 在背景處理文字訊息
            asyncio.create_task(self.process_text_message(event))

    def _register_dev_handlers(self):
        """註冊開發模式事件處理器（無需 LINE SDK）"""
        # 在開發模式下，我們無法使用 LINE SDK 的事件處理器
        # 但我們可以提供 webhook 端點來接收和處理訊息
        logger.info("🔧 開發模式：事件處理將通過 webhook 端點進行")

    async def handle_webhook_manually(self, webhook_body: str):
        """開發模式：手動處理 LINE Webhook 訊息"""
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
                        # 處理語音訊息
                        logger.info("🎤 處理語音訊息")
                        await self.handle_audio_message_dev(message, reply_token)

                    elif message_type == "text":
                        # 處理文字訊息
                        text_content = message.get("text", "")
                        logger.info(f"💬 處理文字訊息: {text_content}")
                        await self.handle_text_message_dev(text_content, reply_token)

        except Exception as e:
            logger.error(f"手動處理 Webhook 時發生錯誤: {str(e)}")
            raise

    async def handle_audio_message_dev(self, message, reply_token):
        """開發模式：處理語音訊息"""
        try:
            message_id = message.get("id")
            logger.info(f"🎙️ 開始處理語音訊息: {message_id}")

            # 1. 下載語音檔（開發模式可能無法下載，使用測試音檔）
            logger.info("📥 開發模式：無法直接下載 LINE 語音，使用 ASR 測試流程")

            # 2. 使用預設回應（因為無法取得實際語音內容）
            recognized_text = "抱歉，開發模式下無法處理實際語音內容"
            logger.info(f"📝 辨識結果: {recognized_text}")

            # 3. LLM 回應
            llm_response = await self.get_llm_response(recognized_text)
            if not llm_response:
                llm_response = "我是您的語音助理，目前在開發模式下運行。請設定正確的 LINE Token 以使用完整功能。"

            logger.info(f"🤖 LLM 回應: {llm_response}")

            # 4. 回覆文字（開發模式無法回覆到 LINE）
            logger.info(f"📤 開發模式：無法直接回覆到 LINE，回應內容: {llm_response}")

        except Exception as e:
            logger.error(f"開發模式處理語音訊息時發生錯誤: {str(e)}")

    async def handle_text_message_dev(self, text_content, reply_token):
        """開發模式：處理文字訊息"""
        try:
            logger.info(f"💭 開發模式處理文字: {text_content}")

            # 特殊指令處理
            if text_content.lower() in ["/help", "幫助", "說明"]:
                response = "🤖 開發模式說明：\n目前在開發模式下運行，部分功能受限。\n請設定 LINE Token 以使用完整功能。"
            elif text_content.lower() in ["/status", "狀態"]:
                response = await self.check_services_status()
            else:
                # LLM 回應
                response = await self.get_llm_response(text_content)
                if not response:
                    response = (
                        f"我收到您的訊息：「{text_content}」\n目前在開發模式下運行。"
                    )

            logger.info(f"📤 開發模式回應: {response}")

        except Exception as e:
            logger.error(f"開發模式處理文字訊息時發生錯誤: {str(e)}")

    async def process_audio_message(self, event):
        """處理語音訊息的完整流程"""
        try:
            # 1. 下載語音檔
            audio_content = await self.download_audio_content(event.message.id)
            if not audio_content:
                await self.reply_text(event.reply_token, "抱歉，無法下載語音檔案")
                return

            # 2. 語音辨識
            recognized_text = await self.transcribe_audio(audio_content)
            if not recognized_text:
                await self.reply_text(event.reply_token, "抱歉，無法辨識您的語音內容")
                return

            logger.info(f"語音辨識結果: {recognized_text}")

            # 3. 大語言模型處理
            llm_response = await self.get_llm_response(recognized_text)
            if not llm_response:
                await self.reply_text(event.reply_token, "抱歉，無法生成回應")
                return

            logger.info(f"LLM 回應: {llm_response}")

            # 4. 語音合成
            audio_file_path = await self.synthesize_speech(llm_response)
            if not audio_file_path:
                # 如果語音合成失敗，回傳文字
                await self.reply_text(event.reply_token, llm_response)
                return

            # 5. 回傳語音訊息
            await self.reply_audio(event.reply_token, audio_file_path)

            # 清理臨時檔案
            if audio_file_path and Path(audio_file_path).exists():
                Path(audio_file_path).unlink()

        except Exception as e:
            logger.error(f"處理語音訊息時發生錯誤: {str(e)}")
            await self.reply_text(event.reply_token, "抱歉，處理您的語音時發生錯誤")

    async def process_text_message(self, event):
        """處理文字訊息"""
        try:
            text = event.message.text

            # 特殊指令處理
            if text.lower() in ["/help", "幫助", "說明"]:
                help_text = """
🤖 語音助理功能說明：

📢 語音訊息：傳送語音給我，我會：
1. 辨識您的語音內容
2. 透過 AI 生成回應
3. 將回應轉換為語音回傳

💬 文字訊息：直接傳送文字也可以對話

🔧 指令：
/help - 顯示此說明
/status - 檢查服務狀態
                """
                await self.reply_text(event.reply_token, help_text)
                return

            elif text.lower() in ["/status", "狀態"]:
                status = await self.check_services_status()
                await self.reply_text(event.reply_token, status)
                return

            # 一般文字對話
            llm_response = await self.get_llm_response(text)
            if llm_response:
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
                await self.reply_text(event.reply_token, "抱歉，無法生成回應")

        except Exception as e:
            logger.error(f"處理文字訊息時發生錯誤: {str(e)}")
            await self.reply_text(event.reply_token, "抱歉，處理您的訊息時發生錯誤")

    async def download_audio_content(self, message_id: str) -> Optional[bytes]:
        """改進的語音內容下載方法"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"🔄 嘗試下載語音內容 (第 {attempt + 1}/{max_retries} 次): {message_id}"
                )

                # 檢查憑證
                if not self.configuration.access_token:
                    logger.error("❌ LINE Channel Access Token 未設定")
                    return None

                    # 使用同步 API（LINE Bot SDK 不支援異步）
                with ApiClient(self.configuration) as api_client:
                    line_bot_blob_api = MessagingApiBlob(api_client)

                    # 下載語音內容
                    audio_content = line_bot_blob_api.get_message_content(
                        message_id=message_id
                    )

                    if audio_content and len(audio_content) > 0:
                        logger.info(
                            f"✅ 成功下載語音內容，大小: {len(audio_content)} 字節"
                        )

                        # 驗證音檔格式
                        if self.validate_audio_content(audio_content):
                            # 保存調試音檔（可選）
                            await self.save_audio_for_debug(audio_content, message_id)
                            return audio_content
                        else:
                            logger.warning("⚠️ 音檔格式驗證失敗，但仍嘗試處理")
                            return audio_content  # 仍然返回，讓 ASR 服務處理
                    else:
                        logger.warning(f"⚠️ 下載的語音內容為空")

            except Exception as e:
                logger.error(f"❌ 第 {attempt + 1} 次下載嘗試失敗: {str(e)}")

                if attempt < max_retries - 1:
                    logger.info(f"⏳ {retry_delay} 秒後重試...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避
                else:
                    logger.error("❌ 所有下載嘗試都失敗了")

        return None

    def validate_audio_content(self, audio_content: bytes) -> bool:
        """驗證音檔內容"""
        try:
            # 檢查檔案大小
            if len(audio_content) < 100:  # 太小可能不是有效音檔
                logger.warning(f"⚠️ 音檔太小: {len(audio_content)} 字節")
                return False

            # 檢查檔案頭（M4A 格式）
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

            logger.warning("⚠️ 未知的音檔格式，但繼續處理")
            return False

        except Exception as e:
            logger.error(f"❌ 音檔驗證失敗: {str(e)}")
            return False

    async def save_audio_for_debug(self, audio_content: bytes, message_id: str) -> str:
        """保存音檔用於調試"""
        try:
            debug_dir = "debug_audio"
            os.makedirs(debug_dir, exist_ok=True)

            file_path = os.path.join(debug_dir, f"audio_{message_id}.m4a")

            with open(file_path, "wb") as f:
                f.write(audio_content)

            logger.info(f"🔍 調試音檔已保存: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"❌ 保存調試音檔失敗: {str(e)}")
            return ""

    async def transcribe_audio(self, audio_content: bytes) -> Optional[str]:
        """呼叫 ASR 服務進行語音辨識"""
        logger.info(f"🎙️ 開始語音辨識，音檔大小: {len(audio_content)} 字節")
        try:
            async with aiohttp.ClientSession() as session:
                # 建立臨時檔案
                with tempfile.NamedTemporaryFile(
                    suffix=".m4a", delete=False
                ) as temp_file:
                    temp_file.write(audio_content)
                    temp_file_path = temp_file.name

                # 準備檔案上傳
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
                            # ASR 服務回傳的是 transcription 欄位，不是 text
                            transcription = result.get("transcription", "")
                            logger.info(f"🎙️ ASR 辨識成功: {transcription}")
                            return transcription
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"ASR 服務回應錯誤: {response.status}, 詳細: {error_text}"
                            )
                            return None

        except Exception as e:
            logger.error(f"❌ 語音辨識失敗: {str(e)}", exc_info=True)
            return None
        finally:
            # 清理臨時檔案
            if "temp_file_path" in locals() and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()

    async def get_llm_response(self, text: str) -> Optional[str]:
        """獲取大語言模型回應"""
        if self.use_openai and self.openai_api_key:
            return await self.get_openai_response(text)
        else:
            return await self.get_local_llm_response(text)

    async def get_openai_response(self, text: str) -> Optional[str]:
        """使用 OpenAI API 獲取回應"""
        import asyncio

        # 如果 OpenAI API 有問題，提供智能預設回應
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
                            "content": "你是一個友善的AI助理，請用繁體中文回應，回應要簡潔明瞭。",
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
                        logger.warning("OpenAI API 請求限制，使用預設回應")
                        return fallback_response
                    else:
                        logger.error(f"OpenAI API 錯誤: {response.status}")
                        return fallback_response

        except asyncio.TimeoutError:
            logger.warning("OpenAI API 超時，使用預設回應")
            return fallback_response
        except Exception as e:
            logger.error(f"OpenAI API 呼叫失敗: {str(e)}")
            return fallback_response

    def generate_smart_fallback(self, text: str) -> str:
        """生成智能預設回應"""
        text_lower = text.lower()

        # 問候語
        if any(word in text_lower for word in ["你好", "哈囉", "hello", "hi", "嗨"]):
            return "你好！我是您的語音助理，很高興為您服務！有什麼可以幫助您的嗎？"

        # 料理相關
        elif any(
            word in text
            for word in ["料理", "食譜", "煮", "做菜", "烹飪", "雞胸肉", "牛肉", "豬肉"]
        ):
            return f"關於「{text}」的料理問題，我建議您可以：\n1. 搜尋相關食譜網站\n2. 參考料理書籍\n3. 詢問有經驗的廚師\n\n我目前正在學習中，希望很快能提供更詳細的料理建議！"

        # 天氣相關
        elif any(word in text for word in ["天氣", "溫度", "下雨", "晴天", "陰天"]):
            return "關於天氣資訊，建議您可以：\n1. 查看天氣預報APP\n2. 關注氣象局資訊\n3. 觀察窗外實際狀況\n\n我正在努力學習提供即時天氣資訊！"

        # 時間相關
        elif any(word in text for word in ["時間", "幾點", "現在"]):
            from datetime import datetime

            now = datetime.now()
            return f"現在是 {now.strftime('%Y年%m月%d日 %H:%M')}。\n\n有什麼其他可以幫助您的嗎？"

        # 感謝
        elif any(word in text for word in ["謝謝", "感謝", "thanks", "thank you"]):
            return "不客氣！很高興能幫助您。如果還有其他問題，隨時都可以問我喔！"

        # 詢問功能
        elif any(word in text for word in ["功能", "能做什麼", "怎麼用", "幫助"]):
            return """我是您的語音助理，目前可以：

🎤 **語音辨識**：發送語音訊息給我，我會轉換成文字
💬 **文字對話**：與我進行文字對話
🤖 **智能回應**：回答各種問題（正在學習中）

📱 **使用方式**：
- 直接發送文字或語音訊息
- 我會盡力回答您的問題
- 目前正在持續學習和改進中

有什麼想聊的嗎？"""

        # 一般問題
        else:
            return f"""我收到您的訊息：「{text}」

雖然我目前的 AI 功能正在升級中，但我很樂意與您對話！

💡 **我可以幫您：**
- 回答一般問題
- 進行語音辨識
- 提供基本資訊

🔧 **正在改進：**
- 更智能的對話能力
- 更準確的回答
- 更多實用功能

請繼續與我對話，我會持續學習！"""

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
        """呼叫 TTS 服務進行語音合成"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": text}

                async with session.post(
                    f"{self.tts_service_url}/synthesize",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        # 儲存音檔到臨時檔案
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
        """回傳文字訊息"""
        try:
            # LINE Bot API 不支援異步，使用同步調用
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token, messages=[TextMessage(text=text)]
                    )
                )
                logger.info(f"✅ 成功回覆文字訊息: {text[:50]}...")
        except Exception as e:
            logger.error(f"回傳文字訊息失敗: {str(e)}")
            # 如果回覆失敗，至少記錄訊息內容
            logger.info(f"📝 原本要回覆的內容: {text}")

    async def reply_audio(self, reply_token: str, audio_file_path: str):
        """回傳語音訊息"""
        try:
            # 這裡需要將音檔上傳到可公開訪問的 URL
            # 簡化實作：回傳文字說明
            await self.reply_text(reply_token, "語音回應已生成（需要設定音檔上傳服務）")
        except Exception as e:
            logger.error(f"回傳語音訊息失敗: {str(e)}")

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
                        status_info.append("🟢 ASR 服務：正常")
                    else:
                        status_info.append("🔴 ASR 服務：異常")
        except:
            status_info.append("🔴 ASR 服務：無法連接")

        # 檢查 LLM 服務
        if self.use_openai:
            status_info.append("🟢 LLM 服務：OpenAI API")
        else:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.llm_service_url}/health", timeout=5
                    ) as response:
                        if response.status == 200:
                            status_info.append("🟢 LLM 服務：正常")
                        else:
                            status_info.append("🔴 LLM 服務：異常")
            except:
                status_info.append("🔴 LLM 服務：無法連接")

        # 檢查 TTS 服務
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.tts_service_url}/health", timeout=5
                ) as response:
                    if response.status == 200:
                        status_info.append("🟢 TTS 服務：正常")
                    else:
                        status_info.append("🔴 TTS 服務：異常")
        except:
            status_info.append("🔴 TTS 服務：無法連接")

        return "📊 服務狀態檢查：\n\n" + "\n".join(status_info)


# 全域服務實例
linebot_service = None


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化服務"""
    global linebot_service

    # 載入環境變數
    from dotenv import load_dotenv

    load_dotenv()

    logger.info("正在初始化 LINE Bot 服務...")
    linebot_service = LineBotService()
    logger.info("LINE Bot 服務初始化完成！")


@app.get("/")
def read_root():
    """健康檢查端點"""
    if not linebot_service:
        return {
            "message": "LINE Bot 服務初始化中...",
            "status": "initializing",
        }

    return {
        "message": "LINE Bot 服務已啟動",
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
        raise HTTPException(status_code=503, detail="服務尚未初始化")

    if not linebot_service.dev_mode:
        raise HTTPException(status_code=403, detail="此功能僅在開發模式下可用")

    try:
        logger.info("🧪 開發模式：開始測試語音處理流程")

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
                "message": "語音處理流程測試成功",
            }
        )

    except Exception as e:
        logger.error(f"測試語音處理時發生錯誤: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)})


@app.post("/webhook")
async def webhook(request: Request):
    """LINE Bot Webhook 端點"""
    if not linebot_service:
        raise HTTPException(status_code=503, detail="服務尚未初始化")

    # 取得請求內容
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 開發模式：跳過簽名驗證，直接處理訊息
    if linebot_service.dev_mode:
        logger.info("🔧 開發模式：接收到 Webhook 請求，跳過簽名驗證")
        try:
            # 解析 LINE 訊息
            webhook_body = body.decode("utf-8")
            logger.info(f"📥 Webhook 內容: {webhook_body}")

            # 手動處理 LINE 訊息
            await linebot_service.handle_webhook_manually(webhook_body)

            return JSONResponse(content={"status": "ok"})
        except Exception as e:
            logger.error(f"開發模式處理 Webhook 時發生錯誤: {str(e)}")
            return JSONResponse(content={"status": "error", "message": str(e)})

    # 正常模式：使用 LINE SDK 處理
    try:
        linebot_service.handler.handle(body.decode("utf-8"), signature)
        return JSONResponse(content={"status": "ok"})
    except InvalidSignatureError:
        logger.error("LINE Webhook 簽名驗證失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"處理 Webhook 時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    # 從環境變數取得設定
    host = os.getenv("LINEBOT_HOST", "0.0.0.0")
    port = int(os.getenv("LINEBOT_PORT", "8000"))

    uvicorn.run(app, host=host, port=port, log_level="debug")
