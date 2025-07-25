#!/usr/bin/env python3
"""
Windows 系統 ffmpeg 安裝和配置腳本
"""

import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


def download_ffmpeg_windows():
    """下載並安裝 ffmpeg for Windows"""
    print("🔧 正在為 Windows 安裝 ffmpeg...")

    # ffmpeg Windows 下載連結
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    download_path = "ffmpeg.zip"
    extract_path = "ffmpeg"

    try:
        print("📥 下載 ffmpeg...")
        urllib.request.urlretrieve(ffmpeg_url, download_path)
        print("✅ 下載完成")

        print("📦 解壓縮...")
        with zipfile.ZipFile(download_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 尋找 ffmpeg.exe
        ffmpeg_dirs = list(Path(extract_path).glob("ffmpeg-*"))
        if ffmpeg_dirs:
            ffmpeg_bin = ffmpeg_dirs[0] / "bin"
            ffmpeg_exe = ffmpeg_bin / "ffmpeg.exe"

            if ffmpeg_exe.exists():
                print(f"✅ ffmpeg 安裝到: {ffmpeg_exe}")

                # 添加到系統路徑
                add_to_path(str(ffmpeg_bin))

                # 清理下載檔案
                os.remove(download_path)

                return True

        print("❌ 找不到 ffmpeg.exe")
        return False

    except Exception as e:
        print(f"❌ 安裝失敗: {str(e)}")
        return False


def add_to_path(ffmpeg_bin_path):
    """將 ffmpeg 添加到系統 PATH"""
    try:
        # 檢查是否已在 PATH 中
        current_path = os.environ.get("PATH", "")
        if ffmpeg_bin_path not in current_path:
            print("🔧 添加 ffmpeg 到 PATH...")

            # 暫時添加到當前會話
            os.environ["PATH"] = ffmpeg_bin_path + os.pathsep + current_path

            print("✅ ffmpeg 已添加到當前會話的 PATH")
            print("💡 如需永久添加，請手動將以下路徑添加到系統 PATH:")
            print(f"   {ffmpeg_bin_path}")
        else:
            print("✅ ffmpeg 已在 PATH 中")

    except Exception as e:
        print(f"⚠️ 添加到 PATH 失敗: {str(e)}")


def test_ffmpeg():
    """測試 ffmpeg 是否可用"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ ffmpeg 測試成功")
            return True
        else:
            print("❌ ffmpeg 測試失敗")
            return False
    except Exception as e:
        print(f"❌ ffmpeg 測試失敗: {str(e)}")
        return False


def main():
    """主安裝流程"""
    print("🎯 ffmpeg 安裝工具")
    print("=" * 40)

    # 檢查是否已安裝
    if test_ffmpeg():
        print("🎉 ffmpeg 已可用，無需安裝")
        return

    print("⚠️ 未檢測到 ffmpeg，開始安裝...")

    if sys.platform == "win32":
        if download_ffmpeg_windows():
            print("\n🎉 ffmpeg 安裝完成！")
            print("💡 現在可以重新測試 ASR 服務")
        else:
            print("\n❌ 自動安裝失敗")
            print("💡 請手動安裝 ffmpeg:")
            print("   1. 到 https://ffmpeg.org/download.html")
            print("   2. 下載 Windows 版本")
            print("   3. 解壓並添加到 PATH")
    else:
        print("💡 請手動安裝 ffmpeg:")
        print("   Ubuntu/Debian: sudo apt install ffmpeg")
        print("   macOS: brew install ffmpeg")


if __name__ == "__main__":
    main()
