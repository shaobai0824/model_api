#!/usr/bin/env python3
"""
快速測試 ASR 服務
"""

import os
import time

import requests


def quick_test():
    """快速測試 ASR 服務"""
    audio_file_path = "test_audio.wav"

    print("🎙️  快速 ASR 測試")
    print("=" * 30)

    # 檢查檔案是否存在
    if not os.path.exists(audio_file_path):
        print(f"❌ 找不到測試音檔: {audio_file_path}")
        print("💡 請先執行: python create_test_audio.py")
        return

    print(f"🎵 測試音檔: {audio_file_path}")
    print(f"📁 檔案大小: {os.path.getsize(audio_file_path)} bytes")

    try:
        # 發送音檔到 ASR 服務
        with open(audio_file_path, "rb") as audio_file:
            files = {"audio_file": audio_file}

            print("📤 正在上傳到 ASR 服務...")
            start_time = time.time()

            response = requests.post(
                "http://localhost:8001/recognize", files=files, timeout=60
            )

            end_time = time.time()
            process_time = end_time - start_time

            print(f"\n📊 回應狀態碼: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 辨識成功！")
                print(f"📝 辨識結果: {result.get('text', '無結果')}")
                print(f"⏱️  處理時間: {process_time:.2f} 秒")
                print(f"🔧 使用模型: {result.get('model', '未知')}")
                print(f"🖥️  使用裝置: {result.get('device', '未知')}")
            else:
                print(f"❌ 辨識失敗")
                print(f"錯誤訊息: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 ASR 服務")
        print("💡 請確認 ASR 服務是否正在運行:")
        print("   .\start_venv.bat")
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")


if __name__ == "__main__":
    quick_test()
