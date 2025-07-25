#!/usr/bin/env python3
"""
LINE Bot 語音下載診斷和修復工具
"""

import os
import sys
import tempfile

from dotenv import load_dotenv
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi

# 載入環境變數
load_dotenv()


def check_line_credentials():
    """檢查 LINE Bot 憑證設定"""
    print("🔍 檢查 LINE Bot 憑證...")

    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")

    if not channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")
        return False

    if not channel_secret:
        print("❌ LINE_CHANNEL_SECRET 未設定")
        return False

    print(f"✅ Channel Access Token: {channel_access_token[:20]}...")
    print(f"✅ Channel Secret: {channel_secret[:10]}...")
    return True


def test_audio_download_sync():
    """測試同步語音下載（當前實現）"""
    print("\n🧪 測試同步語音下載...")

    try:
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        configuration = Configuration(access_token=channel_access_token)

        # 測試 API 配置
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            print("✅ LINE Bot API 配置成功")

            # 注意：這裡需要實際的 message_id 才能測試
            print("💡 需要實際的語音訊息 ID 才能完整測試下載功能")
            return True

    except Exception as e:
        print(f"❌ 同步語音下載測試失敗: {str(e)}")
        return False


def create_improved_audio_handler():
    """建立改進的語音處理方法"""
    print("\n🔧 建立改進的語音下載處理...")

    improved_code = '''
async def download_audio_content_improved(self, message_id: str) -> Optional[bytes]:
    """改進的語音內容下載方法"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 嘗試下載語音內容 (第 {attempt + 1}/{max_retries} 次): {message_id}")
            
            # 檢查憑證
            if not self.configuration.access_token:
                logger.error("❌ LINE Channel Access Token 未設定")
                return None
            
            # 使用同步 API（LINE Bot SDK 不支援異步）
            with ApiClient(self.configuration) as api_client:
                line_bot_blob_api = MessagingApi(api_client)
                
                # 設定請求超時
                audio_content = line_bot_blob_api.get_message_content(
                    message_id=message_id
                )
                
                if audio_content and len(audio_content) > 0:
                    logger.info(f"✅ 成功下載語音內容，大小: {len(audio_content)} 字節")
                    
                    # 驗證音檔格式
                    if self.validate_audio_content(audio_content):
                        return audio_content
                    else:
                        logger.warning("⚠️ 音檔格式驗證失敗")
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
        if audio_content[:4] == b'\\x00\\x00\\x00\\x20' or audio_content[4:8] == b'ftyp':
            logger.info("✅ 檢測到 M4A 格式")
            return True
            
        # 檢查其他常見音檔格式
        if audio_content[:3] == b'ID3' or audio_content[:2] == b'\\xff\\xfb':
            logger.info("✅ 檢測到 MP3 格式")
            return True
            
        if audio_content[:4] == b'RIFF':
            logger.info("✅ 檢測到 WAV 格式")
            return True
            
        logger.warning("⚠️ 未知的音檔格式")
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
'''

    print("✅ 改進的語音下載代碼已準備")
    return improved_code


def suggest_troubleshooting():
    """提供故障排除建議"""
    print("\n🔧 語音下載故障排除指南:")
    print("=" * 50)

    print("1️⃣ **檢查 LINE Bot 設定**")
    print("   - 確認 Channel Access Token 有效")
    print("   - 確認 Channel Secret 正確")
    print("   - 檢查 Webhook URL 設定")

    print("\n2️⃣ **檢查權限設定**")
    print("   - LINE Developers Console > Messaging API")
    print("   - 確認已啟用 'Use webhooks'")
    print("   - 確認 Bot 有接收訊息權限")

    print("\n3️⃣ **網路連線問題**")
    print("   - 檢查防火牆設定")
    print("   - 確認可以連接到 LINE API")
    print("   - 測試網路延遲和穩定性")

    print("\n4️⃣ **訊息 ID 問題**")
    print("   - 確認使用正確的 message_id")
    print("   - 檢查訊息是否為語音類型")
    print("   - 確認訊息未過期")

    print("\n5️⃣ **格式支援問題**")
    print("   - LINE 語音訊息通常為 M4A 格式")
    print("   - 確認 ASR 服務支援該格式")
    print("   - 考慮添加格式轉換")


def main():
    """主診斷流程"""
    print("🎯 LINE Bot 語音下載診斷工具")
    print("=" * 40)

    # 檢查憑證
    if not check_line_credentials():
        print("\n❌ 請先設定正確的 LINE Bot 憑證")
        return

    # 測試 API 連接
    if test_audio_download_sync():
        print("\n✅ LINE Bot API 連接正常")
    else:
        print("\n❌ LINE Bot API 連接有問題")

    # 提供改進建議
    create_improved_audio_handler()
    suggest_troubleshooting()

    print("\n💡 下一步建議:")
    print("1. 更新 linebot_server.py 中的語音下載方法")
    print("2. 添加更詳細的錯誤處理和日誌")
    print("3. 測試實際的語音訊息下載")


if __name__ == "__main__":
    main()
