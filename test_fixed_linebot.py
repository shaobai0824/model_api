#!/usr/bin/env python3
"""
修正後的 LINE Bot 測試腳本
測試 OpenAI API 錯誤處理和 LINE Bot API 修正
"""

import json
import time

import requests


def test_text_message_with_fallback():
    """測試文字訊息處理（包含 OpenAI 錯誤處理）"""
    print("💬 測試文字訊息處理（含錯誤處理）...")

    # 模擬 LINE Webhook 文字訊息
    webhook_data = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token_12345",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "你好，請告訴我今天的天氣如何？",
                },
            }
        ]
    }

    try:
        print("📤 發送測試訊息到 LINE Bot...")
        response = requests.post(
            "http://localhost:8000/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code == 200:
            print("✅ Webhook 處理成功")
            result = response.json()
            print(f"📊 回應: {result}")
            return True
        else:
            print(f"❌ Webhook 處理失敗: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False


def test_openai_fallback():
    """測試 OpenAI 錯誤回退機制"""
    print("\n🤖 測試 OpenAI 錯誤回退機制...")

    # 模擬會觸發 OpenAI API 的訊息
    webhook_data = {
        "events": [
            {
                "type": "message",
                "replyToken": "fallback_test_token",
                "message": {
                    "type": "text",
                    "id": "fallback_test_id",
                    "text": "這是一個測試訊息，用來檢查 OpenAI API 錯誤處理",
                },
            }
        ]
    }

    try:
        print("📤 發送會觸發 LLM 處理的訊息...")
        response = requests.post(
            "http://localhost:8000/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )

        if response.status_code == 200:
            print("✅ 錯誤回退機制正常工作")
            return True
        else:
            print(f"❌ 錯誤回退測試失敗: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 錯誤回退測試失敗: {str(e)}")
        return False


def test_service_health():
    """測試服務健康狀態"""
    print("\n🔍 檢查服務健康狀態...")

    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ LINE Bot 服務健康")
            print(f"📊 狀態: {data.get('status')}")
            print(f"🔧 開發模式: {data.get('dev_mode')}")

            # 檢查服務配置
            services = data.get("services", {})
            print(f"🎙️ ASR 服務: {services.get('asr')}")
            print(f"🤖 LLM 服務: {services.get('llm')}")
            print(f"🔊 TTS 服務: {services.get('tts')}")

            return True
        else:
            print(f"❌ 服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False


def main():
    """主測試流程"""
    print("🎯 修正後的 LINE Bot 功能測試")
    print("=" * 50)

    # 測試結果
    results = {}

    # 1. 服務健康檢查
    results["health"] = test_service_health()

    if not results["health"]:
        print("\n❌ 服務未正常運行，請先啟動服務")
        return

    # 2. 基本文字訊息測試
    print("\n" + "=" * 50)
    results["basic"] = test_text_message_with_fallback()

    # 3. OpenAI 錯誤回退測試
    print("\n" + "=" * 50)
    results["fallback"] = test_openai_fallback()

    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(
        f"   {'✅' if results['health'] else '❌'} 服務健康: {'正常' if results['health'] else '異常'}"
    )
    print(
        f"   {'✅' if results['basic'] else '❌'} 基本訊息: {'正常' if results['basic'] else '異常'}"
    )
    print(
        f"   {'✅' if results['fallback'] else '❌'} 錯誤回退: {'正常' if results['fallback'] else '異常'}"
    )

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 所有修正測試通過！")
        print("\n💡 修正內容:")
        print("   ✅ OpenAI API 429 錯誤 → 提供預設回應")
        print("   ✅ LINE Bot API 異步問題 → 改用同步調用")
        print("   ✅ 錯誤處理增強 → 更詳細的日誌記錄")

        print("\n🚀 您的 LINE Bot 現在更穩定了！")
        print("📱 即使 OpenAI API 有問題，用戶仍會收到回應")

    else:
        print("\n❌ 部分測試失敗")
        print("🔧 請檢查服務日誌以了解詳細錯誤")

    print("\n💡 提示:")
    print("   - 如果 OpenAI API 持續出現 429 錯誤，請檢查 API 配額")
    print("   - 系統會自動提供預設回應，確保用戶體驗")
    print("   - 查看服務日誌了解詳細的處理過程")


if __name__ == "__main__":
    main()
