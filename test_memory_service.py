#!/usr/bin/env python3
"""
測試記憶服務功能
"""

import asyncio
import json
import sys
from pathlib import Path

import aiohttp


async def test_memory_service():
    """測試記憶服務的各項功能"""
    base_url = "http://localhost:8004"
    test_user_id = "test_user_123"

    print("🧠 開始測試記憶服務...")
    print(f"服務地址: {base_url}")
    print(f"測試用戶: {test_user_id}")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:

        # 1. 健康檢查
        print("\n1. 🔍 健康檢查...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ 記憶服務正常運行")
                    print(f"   狀態: {health_data.get('status')}")
                    print(f"   後端: {health_data.get('backend')}")
                    print(f"   最大訊息數: {health_data.get('max_messages_per_user')}")
                else:
                    print(f"❌ 健康檢查失敗: {response.status}")
                    return
        except Exception as e:
            print(f"❌ 無法連接到記憶服務: {e}")
            return

        # 2. 添加測試訊息
        print("\n2. 📝 添加測試訊息...")
        test_messages = [
            {"role": "user", "content": "你好，我是新用戶", "message_type": "text"},
            {
                "role": "assistant",
                "content": "您好！很高興認識您！",
                "message_type": "text",
            },
            {"role": "user", "content": "我喜歡聽音樂", "message_type": "voice"},
            {
                "role": "assistant",
                "content": "音樂是很棒的興趣！您喜歡什麼類型的音樂呢？",
                "message_type": "voice",
            },
            {
                "role": "user",
                "content": "我喜歡古典音樂和爵士樂",
                "message_type": "text",
            },
        ]

        for i, msg in enumerate(test_messages, 1):
            try:
                data = {"user_id": test_user_id, **msg}
                async with session.post(
                    f"{base_url}/add_message", json=data
                ) as response:
                    if response.status == 200:
                        print(
                            f"   ✅ 訊息 {i}: {msg['role']} - {msg['content'][:20]}..."
                        )
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 訊息 {i} 添加失敗: {error_text}")
            except Exception as e:
                print(f"   ❌ 添加訊息 {i} 時發生錯誤: {e}")

        # 3. 獲取對話上下文
        print("\n3. 💭 獲取對話上下文...")
        try:
            async with session.get(
                f"{base_url}/conversation_context/{test_user_id}"
            ) as response:
                if response.status == 200:
                    context_data = await response.json()
                    context = context_data.get("context", [])
                    print(f"✅ 成功獲取 {len(context)} 條上下文訊息")

                    for i, ctx in enumerate(context, 1):
                        role = ctx.get("role", "unknown")
                        content = ctx.get("content", "")[:50]
                        print(f"   {i}. [{role}] {content}...")
                else:
                    error_text = await response.text()
                    print(f"❌ 獲取上下文失敗: {error_text}")
        except Exception as e:
            print(f"❌ 獲取上下文時發生錯誤: {e}")

        # 4. 獲取用戶統計
        print("\n4. 📊 獲取用戶統計...")
        try:
            async with session.get(f"{base_url}/user_stats/{test_user_id}") as response:
                if response.status == 200:
                    stats_data = await response.json()
                    stats = stats_data.get("stats", {})
                    print("✅ 用戶統計資訊:")
                    print(f"   總訊息數: {stats.get('total_messages', 0)}")
                    print(
                        f"   當前會話訊息: {stats.get('current_session_messages', 0)}"
                    )
                    print(f"   語音訊息: {stats.get('voice_messages', 0)}")
                    print(f"   文字訊息: {stats.get('text_messages', 0)}")
                    print(f"   用戶訊息: {stats.get('user_messages', 0)}")
                    print(f"   助手訊息: {stats.get('assistant_messages', 0)}")
                    print(f"   最後互動: {stats.get('last_interaction', 'N/A')}")
                    print(f"   偏好設定: {stats.get('preferences', {})}")
                else:
                    error_text = await response.text()
                    print(f"❌ 獲取統計失敗: {error_text}")
        except Exception as e:
            print(f"❌ 獲取統計時發生錯誤: {e}")

        # 5. 設定用戶偏好
        print("\n5. ⚙️ 設定用戶偏好...")
        preferences = [
            {"key": "language", "value": "formal"},
            {"key": "music_preference", "value": "classical"},
        ]

        for pref in preferences:
            try:
                data = {"user_id": test_user_id, **pref}
                async with session.post(
                    f"{base_url}/set_preference", json=data
                ) as response:
                    if response.status == 200:
                        print(f"   ✅ 設定偏好: {pref['key']} = {pref['value']}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 設定偏好失敗: {error_text}")
            except Exception as e:
                print(f"   ❌ 設定偏好時發生錯誤: {e}")

        # 6. 再次獲取統計以確認偏好設定
        print("\n6. 🔄 確認偏好設定...")
        try:
            async with session.get(f"{base_url}/user_stats/{test_user_id}") as response:
                if response.status == 200:
                    stats_data = await response.json()
                    stats = stats_data.get("stats", {})
                    preferences = stats.get("preferences", {})
                    print(f"✅ 更新後的偏好設定: {preferences}")
                else:
                    print(f"❌ 確認偏好設定失敗")
        except Exception as e:
            print(f"❌ 確認偏好設定時發生錯誤: {e}")

        # 7. 列出所有用戶
        print("\n7. 👥 列出所有用戶...")
        try:
            async with session.get(f"{base_url}/list_users") as response:
                if response.status == 200:
                    users_data = await response.json()
                    users = users_data.get("users", [])
                    print(f"✅ 系統中共有 {len(users)} 個用戶:")
                    for user in users:
                        print(f"   - {user}")
                else:
                    error_text = await response.text()
                    print(f"❌ 列出用戶失敗: {error_text}")
        except Exception as e:
            print(f"❌ 列出用戶時發生錯誤: {e}")

        # 8. 清除測試用戶記憶 (可選)
        print("\n8. 🧹 清除測試用戶記憶...")
        while True:
            choice = input("是否要清除測試用戶的記憶？(y/n): ").lower().strip()
            if choice in ["y", "yes", "是"]:
                try:
                    data = {"user_id": test_user_id}
                    async with session.post(
                        f"{base_url}/clear_memory", json=data
                    ) as response:
                        if response.status == 200:
                            print(f"✅ 已清除用戶 {test_user_id} 的記憶")
                        else:
                            error_text = await response.text()
                            print(f"❌ 清除記憶失敗: {error_text}")
                except Exception as e:
                    print(f"❌ 清除記憶時發生錯誤: {e}")
                break
            elif choice in ["n", "no", "否"]:
                print("保留測試用戶記憶")
                break
            else:
                print("請輸入 y 或 n")

    print("\n" + "=" * 50)
    print("🎉 記憶服務測試完成！")


def main():
    """主函數"""
    print("🧠 記憶服務功能測試")
    print("請確保記憶服務正在運行 (http://localhost:8004)")
    print()

    try:
        asyncio.run(test_memory_service())
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
