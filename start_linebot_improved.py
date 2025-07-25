#!/usr/bin/env python3
"""
改進的 LINE Bot 啟動腳本
包含語音下載診斷和監控功能
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


def check_prerequisites():
    """檢查前置條件"""
    print("🔍 檢查前置條件...")

    # 檢查環境變數
    required_vars = [
        "LINE_CHANNEL_ACCESS_TOKEN",
        "LINE_CHANNEL_SECRET",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ 缺少必要的環境變數: {', '.join(missing_vars)}")
        return False

    # 檢查虛擬環境
    if not os.path.exists("venv"):
        print("❌ 找不到虛擬環境目錄 'venv'")
        return False

    print("✅ 前置條件檢查通過")
    return True


def start_services():
    """啟動相關服務"""
    print("🚀 啟動服務...")

    services = []

    try:
        # 啟動 ASR 服務（如果需要）
        print("📡 檢查 ASR 服務...")
        asr_check = subprocess.run(
            [
                "python",
                "-c",
                "import requests; requests.get('http://localhost:8001/health', timeout=2)",
            ],
            capture_output=True,
            cwd=".",
            timeout=5,
        )

        if asr_check.returncode != 0:
            print("🔄 啟動 ASR 服務...")
            asr_process = subprocess.Popen(
                ["python", "asr_service/asr_server.py"],
                cwd=".",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            services.append(("ASR", asr_process))
            time.sleep(3)  # 等待服務啟動
        else:
            print("✅ ASR 服務已運行")

        # 啟動 TTS 服務（如果需要）
        print("📡 檢查 TTS 服務...")
        tts_check = subprocess.run(
            [
                "python",
                "-c",
                "import requests; requests.get('http://localhost:8003/health', timeout=2)",
            ],
            capture_output=True,
            cwd=".",
            timeout=5,
        )

        if tts_check.returncode != 0:
            print("🔄 啟動 TTS 服務...")
            tts_process = subprocess.Popen(
                ["python", "tts_service/tts_server.py"],
                cwd=".",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            services.append(("TTS", tts_process))
            time.sleep(3)  # 等待服務啟動
        else:
            print("✅ TTS 服務已運行")

        # 啟動 LINE Bot 服務
        print("🤖 啟動 LINE Bot 服務...")
        linebot_process = subprocess.Popen(
            ["python", "linebot_service/linebot_server.py"],
            cwd=".",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        services.append(("LINE Bot", linebot_process))

        return services

    except Exception as e:
        print(f"❌ 啟動服務時發生錯誤: {str(e)}")
        return []


def monitor_services(services):
    """監控服務狀態"""
    print("👀 開始監控服務...")
    print("按 Ctrl+C 停止所有服務")

    try:
        while True:
            for service_name, process in services:
                if process.poll() is not None:
                    print(f"⚠️ {service_name} 服務意外停止")
                    return

            # 顯示 LINE Bot 的即時日誌
            if services and services[-1][0] == "LINE Bot":
                linebot_process = services[-1][1]
                try:
                    line = linebot_process.stdout.readline()
                    if line:
                        print(f"[LINE Bot] {line.strip()}")
                except:
                    pass

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 收到停止信號...")

    finally:
        # 停止所有服務
        for service_name, process in services:
            print(f"🔄 停止 {service_name} 服務...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"⚠️ 強制終止 {service_name} 服務...")
                process.kill()
            except:
                pass


def show_status():
    """顯示系統狀態"""
    print("\n📊 系統狀態:")
    print("=" * 40)

    # 檢查端口使用情況
    ports = [8000, 8001, 8002, 8003]
    for port in ports:
        try:
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=5
            )

            if f":{port}" in result.stdout:
                print(f"✅ 端口 {port}: 使用中")
            else:
                print(f"❌ 端口 {port}: 空閒")

        except:
            print(f"❓ 端口 {port}: 無法檢查")

    print("\n🔗 服務地址:")
    print("- LINE Bot: http://localhost:8000")
    print("- ASR 服務: http://localhost:8001")
    print("- LLM 服務: http://localhost:8002")
    print("- TTS 服務: http://localhost:8003")


def main():
    """主執行函數"""
    print("🎯 LINE Bot 改進版啟動器")
    print("=" * 40)

    # 檢查前置條件
    if not check_prerequisites():
        print("❌ 前置條件檢查失敗，請修正後重試")
        return 1

    # 顯示當前狀態
    show_status()

    # 啟動服務
    services = start_services()
    if not services:
        print("❌ 服務啟動失敗")
        return 1

    print("✅ 所有服務已啟動")
    print("\n🎉 LINE Bot 已準備就緒！")
    print("💡 現在可以透過 LINE 發送語音或文字訊息進行測試")

    # 監控服務
    monitor_services(services)

    print("👋 所有服務已停止")
    return 0


if __name__ == "__main__":
    sys.exit(main())
