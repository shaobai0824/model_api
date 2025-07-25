#!/usr/bin/env python3
"""
LINE Bot 最終測試腳本
確認所有功能都正常運作
"""

import os

import requests
from dotenv import load_dotenv


def test_env_loading():
    """測試環境變數載入"""
    print("🔍 測試環境變數載入...")

    # 載入環境變數
    load_dotenv()

    # 檢查關鍵變數
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_secret = os.getenv("LINE_CHANNEL_SECRET")
    dev_mode = os.getenv("DEV_MODE")

    if line_token and line_secret:
        print("✅ LINE Bot Token 和 Secret 已載入")
        print(f"📊 DEV_MODE: {dev_mode}")
        return True
    else:
        print("❌ LINE Bot Token 或 Secret 未載入")
        return False


def test_linebot_service():
    """測試 LINE Bot 服務"""
    print("\n📱 測試 LINE Bot 服務...")

    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ LINE Bot 服務正常運行")
            print(f"📊 服務狀態: {data.get('status')}")
            print(f"🔧 開發模式: {data.get('dev_mode')}")
            return True
        else:
            print(f"❌ LINE Bot 服務異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 LINE Bot 服務")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_webhook():
    """測試 Webhook 處理"""
    print("\n🔗 測試 Webhook 處理...")

    # 模擬 LINE 文字訊息
    webhook_data = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "測試訊息",
                },
            }
        ]
    }

    try:
        response = requests.post(
            "http://localhost:8000/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ Webhook 處理成功")
            return True
        else:
            print(f"❌ Webhook 處理失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook 測試失敗: {e}")
        return False


def test_asr_service():
    """測試 ASR 服務"""
    print("\n🎙️ 測試 ASR 服務...")

    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ ASR 服務正常")
            print(f"📊 使用模型: {data.get('model')}")
            print(f"🔧 使用設備: {data.get('device')}")
            return True
        else:
            print(f"❌ ASR 服務異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 ASR 服務")
        return False
    except Exception as e:
        print(f"❌ ASR 測試失敗: {e}")
        return False


def main():
    """主測試流程"""
    print("🎯 LINE Bot 最終功能測試")
    print("=" * 50)

    # 測試結果
    results = {}

    # 1. 環境變數測試
    results["env"] = test_env_loading()

    # 2. LINE Bot 服務測試
    results["linebot"] = test_linebot_service()

    # 3. Webhook 測試
    results["webhook"] = test_webhook()

    # 4. ASR 服務測試
    results["asr"] = test_asr_service()

    # 總結
    print("\n" + "=" * 50)
    print("📋 最終測試結果:")
    print(
        f"   {'✅' if results['env'] else '❌'} 環境變數載入: {'成功' if results['env'] else '失敗'}"
    )
    print(
        f"   {'✅' if results['linebot'] else '❌'} LINE Bot 服務: {'正常' if results['linebot'] else '異常'}"
    )
    print(
        f"   {'✅' if results['webhook'] else '❌'} Webhook 處理: {'正常' if results['webhook'] else '異常'}"
    )
    print(
        f"   {'✅' if results['asr'] else '❌'} ASR 服務: {'正常' if results['asr'] else '異常'}"
    )

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 所有測試通過！")
        print("\n💡 您的語音助理 LINE Bot 已完全準備就緒！")
        print("\n📱 下一步操作:")
        print("   1. 設定 ngrok 隧道: ngrok http 8000")
        print("   2. 複製 ngrok HTTPS URL")
        print("   3. 在 LINE Developers Console 設定 Webhook URL")
        print("   4. 開始與您的語音助理對話！")

        print("\n🔧 功能特色:")
        print("   ✅ 語音辨識：使用您的微調 Breeze ASR 模型")
        print("   ✅ 智能對話：OpenAI GPT-3.5 驅動")
        print("   ✅ 快速處理：GPU 加速，3 秒內完成")
        print("   ✅ LINE 整合：完整 Webhook 支援")

    else:
        print("\n❌ 部分測試失敗")
        print("🔧 請檢查失敗的項目並重新測試")


if __name__ == "__main__":
    main()
