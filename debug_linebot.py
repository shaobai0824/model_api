#!/usr/bin/env python3
"""
LINE Bot 除錯腳本
確認 ApiClient 異步問題的確切位置
"""

import asyncio
import os

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def test_line_api_sync():
    """測試同步 LINE API 調用"""
    print("🔍 測試同步 LINE API 調用...")

    try:
        from linebot.v3.messaging import (
            ApiClient,
            Configuration,
            MessagingApi,
            ReplyMessageRequest,
            TextMessage,
        )

        # 設定
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        if not channel_access_token:
            print("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")
            return False

        configuration = Configuration(access_token=channel_access_token)

        # 測試同步調用
        print("📞 嘗試同步 ApiClient...")
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            print("✅ 同步 ApiClient 創建成功")

        return True

    except Exception as e:
        print(f"❌ 同步 API 測試失敗: {e}")
        return False


async def test_line_api_async():
    """測試異步 LINE API 調用（應該會失敗）"""
    print("\n🔍 測試異步 LINE API 調用（預期失敗）...")

    try:
        from linebot.v3.messaging import ApiClient, Configuration, MessagingApi

        # 設定
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        configuration = Configuration(access_token=channel_access_token)

        # 測試異步調用（這應該會失敗）
        print("📞 嘗試異步 ApiClient...")
        async with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            print("❌ 異步 ApiClient 不應該成功")

        return True

    except Exception as e:
        print(f"✅ 異步 API 測試如預期失敗: {e}")
        return False


def test_openai_api():
    """測試 OpenAI API"""
    print("\n🔍 測試 OpenAI API...")

    try:
        import aiohttp

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY 未設定")
            return False

        print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")
        print("✅ OpenAI API Key 已設定")
        return True

    except Exception as e:
        print(f"❌ OpenAI API 測試失敗: {e}")
        return False


async def main():
    """主測試流程"""
    print("🎯 LINE Bot API 除錯測試")
    print("=" * 40)

    # 1. 測試同步 LINE API
    sync_ok = test_line_api_sync()

    # 2. 測試異步 LINE API（應該失敗）
    async_ok = await test_line_api_async()

    # 3. 測試 OpenAI API
    openai_ok = test_openai_api()

    print("\n" + "=" * 40)
    print("📋 除錯結果:")
    print(
        f"   {'✅' if sync_ok else '❌'} 同步 LINE API: {'正常' if sync_ok else '異常'}"
    )
    print(
        f"   {'✅' if not async_ok else '❌'} 異步 LINE API: {'如預期失敗' if not async_ok else '異常成功'}"
    )
    print(
        f"   {'✅' if openai_ok else '❌'} OpenAI API: {'正常' if openai_ok else '異常'}"
    )

    if sync_ok and not async_ok:
        print("\n💡 確認:")
        print("   - 同步 LINE API 正常工作")
        print("   - 異步 LINE API 如預期失敗")
        print("   - 我們的修正方向是正確的")
    else:
        print("\n⚠️  發現問題:")
        if not sync_ok:
            print("   - 同步 LINE API 也有問題")
        if async_ok:
            print("   - 異步 LINE API 意外成功")


if __name__ == "__main__":
    asyncio.run(main())
