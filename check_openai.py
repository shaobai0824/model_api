#!/usr/bin/env python3
"""
OpenAI API 檢查和測試腳本
"""

import json
import os

import requests
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def check_openai_api():
    """檢查 OpenAI API 狀態和配額"""
    print("🔍 檢查 OpenAI API 設定...")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 未設定")
        return False

    print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")

    # 檢查 API 狀態
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 測試簡單請求
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "你好"}],
            "max_tokens": 50,
            "temperature": 0.7,
        }

        print("📞 測試 OpenAI API 連接...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        print(f"📊 回應狀態碼: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ OpenAI API 正常運作")
            print(f"📝 測試回應: {content}")
            return True

        elif response.status_code == 429:
            print("❌ OpenAI API 請求限制 (429)")
            try:
                error_info = response.json()
                print(f"🔍 錯誤詳情: {error_info}")
            except:
                print(f"🔍 錯誤內容: {response.text}")

            print("\n💡 可能的解決方案:")
            print("   1. 檢查 API 配額是否用完")
            print("   2. 等待一段時間後再試")
            print("   3. 升級 OpenAI 方案")
            print("   4. 檢查帳單狀態")
            return False

        elif response.status_code == 401:
            print("❌ OpenAI API Key 無效 (401)")
            print("💡 請檢查 API Key 是否正確")
            return False

        else:
            print(f"❌ OpenAI API 錯誤: {response.status_code}")
            print(f"🔍 錯誤內容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 連接 OpenAI API 失敗: {str(e)}")
        return False


def suggest_solutions():
    """提供解決方案建議"""
    print("\n🔧 OpenAI API 429 錯誤解決方案:")
    print("=" * 50)

    print("1️⃣ **檢查帳戶狀態**")
    print("   - 到 https://platform.openai.com/account/billing")
    print("   - 檢查是否有可用額度")
    print("   - 確認付款方式是否有效")

    print("\n2️⃣ **調整請求頻率**")
    print("   - 減少同時請求數量")
    print("   - 增加請求間隔時間")
    print("   - 使用更小的 max_tokens")

    print("\n3️⃣ **升級方案**")
    print("   - 考慮升級到付費方案")
    print("   - 增加每分鐘請求限制")

    print("\n4️⃣ **使用替代方案**")
    print("   - 暫時使用預設回應")
    print("   - 設定本地 LLM 服務")
    print("   - 使用其他 AI 服務")


def main():
    """主檢查流程"""
    print("🎯 OpenAI API 診斷工具")
    print("=" * 40)

    if check_openai_api():
        print("\n🎉 OpenAI API 運作正常！")
        print("💡 如果 LINE Bot 仍出現 429 錯誤，可能是請求頻率太高")
    else:
        suggest_solutions()


if __name__ == "__main__":
    main()
