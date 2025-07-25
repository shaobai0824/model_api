#!/usr/bin/env python3
"""
測試 ASR 服務的腳本，使用實際下載的語音檔案
"""

import json
import os
from pathlib import Path

import requests


def test_asr_health():
    """測試 ASR 服務健康狀態"""
    print("🏥 測試 ASR 服務健康狀態...")

    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        print(f"📊 健康檢查狀態碼: {response.status_code}")

        if response.status_code == 200:
            print("✅ ASR 服務健康狀態正常")
            try:
                health_data = response.json()
                print(
                    f"📋 健康資訊: {json.dumps(health_data, indent=2, ensure_ascii=False)}"
                )
            except:
                print(f"📋 健康回應: {response.text}")
            return True
        else:
            print(f"⚠️ ASR 服務健康狀態異常: {response.status_code}")
            print(f"📋 回應內容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 無法連接到 ASR 服務: {str(e)}")
        return False


def test_asr_with_downloaded_audio():
    """使用已下載的語音檔案測試 ASR"""
    print("\n🎤 測試 ASR 語音辨識...")

    # 尋找最新的調試音檔
    debug_dir = Path("debug_audio")
    if not debug_dir.exists():
        print("❌ 找不到 debug_audio 目錄")
        return False

    audio_files = list(debug_dir.glob("audio_*.m4a"))
    if not audio_files:
        print("❌ 找不到調試音檔")
        return False

    # 使用最新的音檔
    latest_audio = max(audio_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 使用音檔: {latest_audio}")
    print(f"📏 檔案大小: {latest_audio.stat().st_size} 字節")

    try:
        with open(latest_audio, "rb") as f:
            files = {"audio_file": (latest_audio.name, f, "audio/x-m4a")}

            print("📤 發送到 ASR 服務...")
            response = requests.post(
                "http://localhost:8001/recognize", files=files, timeout=120  # 2分鐘超時
            )

            print(f"📊 回應狀態碼: {response.status_code}")
            print(f"📋 回應內容: {response.text}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    transcription = result.get("transcription", "")
                    print(f"✅ 語音辨識成功")
                    print(f"📝 辨識結果: 「{transcription}」")
                    return True
                except Exception as e:
                    print(f"❌ 解析 JSON 回應失敗: {str(e)}")
                    return False
            else:
                print(f"❌ ASR 服務錯誤: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ 測試 ASR 失敗: {str(e)}")
        return False


def diagnose_asr_service():
    """診斷 ASR 服務問題"""
    print("\n🔍 ASR 服務診斷...")

    # 檢查服務端點
    endpoints = ["/health", "/", "/docs"]

    for endpoint in endpoints:
        try:
            url = f"http://localhost:8001{endpoint}"
            response = requests.get(url, timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")


def main():
    """主測試函數"""
    print("🎯 ASR 服務完整測試")
    print("=" * 40)

    # 1. 健康檢查
    health_ok = test_asr_health()

    # 2. 端點診斷
    diagnose_asr_service()

    # 3. 實際語音測試
    if health_ok:
        test_asr_with_downloaded_audio()
    else:
        print("\n⚠️ 由於健康檢查失敗，跳過語音測試")

    print("\n💡 檢查完成")
    print("📋 如果 ASR 服務有問題，請檢查:")
    print("   1. ASR 服務日誌")
    print("   2. 模型載入狀態")
    print("   3. GPU/CPU 記憶體使用")
    print("   4. 音檔格式支援")


if __name__ == "__main__":
    main()
