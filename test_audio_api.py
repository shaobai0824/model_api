#!/usr/bin/env python3
"""
測試 LINE Bot 語音 API 的腳本
"""

import os

from dotenv import load_dotenv
from linebot.v3.messaging import ApiClient, Configuration, MessagingApiBlob

# 載入環境變數
load_dotenv()


def test_messaging_api_blob():
    """測試 MessagingApiBlob 是否可以正確初始化"""
    print("🧪 測試 MessagingApiBlob...")

    try:
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        if not channel_access_token:
            print("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")
            return False

        configuration = Configuration(access_token=channel_access_token)

        with ApiClient(configuration) as api_client:
            blob_api = MessagingApiBlob(api_client)
            print("✅ MessagingApiBlob 初始化成功")

            # 檢查是否有 get_message_content 方法
            if hasattr(blob_api, "get_message_content"):
                print("✅ get_message_content 方法存在")
                return True
            else:
                print("❌ get_message_content 方法不存在")
                return False

    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False


def show_api_methods():
    """顯示 MessagingApiBlob 的可用方法"""
    print("\n📋 MessagingApiBlob 可用方法:")

    try:
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        configuration = Configuration(access_token=channel_access_token)

        with ApiClient(configuration) as api_client:
            blob_api = MessagingApiBlob(api_client)

            methods = [method for method in dir(blob_api) if not method.startswith("_")]
            for method in methods:
                print(f"  - {method}")

    except Exception as e:
        print(f"❌ 無法顯示方法: {str(e)}")


def main():
    """主測試函數"""
    print("🎯 LINE Bot 語音 API 測試")
    print("=" * 40)

    if test_messaging_api_blob():
        print("\n🎉 API 測試通過！")
        show_api_methods()
    else:
        print("\n❌ API 測試失敗")
        return 1

    print("\n💡 現在可以嘗試發送語音訊息到您的 LINE Bot 進行測試")
    return 0


if __name__ == "__main__":
    exit(main())
