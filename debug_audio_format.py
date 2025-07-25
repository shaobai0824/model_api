#!/usr/bin/env python3
"""
調試音檔格式的工具
"""

import os
from pathlib import Path


def analyze_audio_file():
    """分析下載的音檔"""
    print("🔍 分析音檔格式...")

    # 尋找最新的調試音檔
    debug_dir = Path("debug_audio")
    if not debug_dir.exists():
        print("❌ 找不到 debug_audio 目錄")
        return

    audio_files = list(debug_dir.glob("audio_*.m4a"))
    if not audio_files:
        print("❌ 找不到調試音檔")
        return

    # 使用最新的音檔
    latest_audio = max(audio_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 分析音檔: {latest_audio}")
    print(f"📏 檔案大小: {latest_audio.stat().st_size} 字節")

    # 讀取檔案頭部
    with open(latest_audio, "rb") as f:
        header = f.read(32)

    print(f"🔢 檔案頭部 (hex): {header.hex()}")
    print(f"🔤 檔案頭部 (ascii): {header}")

    # 檢查各種格式標識
    print("\n📋 格式檢查:")

    # M4A/MP4 格式檢查
    if header[4:8] == b"ftyp":
        print("✅ 檢測到 MP4/M4A 容器格式")
        ftyp_brand = header[8:12]
        print(f"   品牌: {ftyp_brand}")
    elif header[:4] == b"\x00\x00\x00\x20":
        print("✅ 可能是 M4A 格式")
    else:
        print("❓ 未檢測到標準 M4A 格式標識")

    # 其他格式檢查
    if header[:3] == b"ID3":
        print("✅ 檢測到 MP3 格式")
    elif header[:4] == b"RIFF":
        print("✅ 檢測到 WAV 格式")
    elif header[:4] == b"OggS":
        print("✅ 檢測到 OGG 格式")
    elif header[:4] == b"fLaC":
        print("✅ 檢測到 FLAC 格式")

    # 嘗試使用不同的工具載入
    test_loading_methods(latest_audio)


def test_loading_methods(audio_path):
    """測試不同的音檔載入方法"""
    print(f"\n🧪 測試載入方法:")

    # 方法1: torchaudio 直接載入
    try:
        import io

        import torchaudio

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
        print(f"✅ torchaudio (BytesIO): 成功 - {sample_rate}Hz, {waveform.shape}")
    except Exception as e:
        print(f"❌ torchaudio (BytesIO): {str(e)}")

    # 方法2: torchaudio 從檔案載入
    try:
        waveform, sample_rate = torchaudio.load(str(audio_path))
        print(f"✅ torchaudio (file): 成功 - {sample_rate}Hz, {waveform.shape}")
    except Exception as e:
        print(f"❌ torchaudio (file): {str(e)}")

    # 方法3: torchaudio 使用 ffmpeg 後端
    try:
        waveform, sample_rate = torchaudio.load(str(audio_path), backend="ffmpeg")
        print(f"✅ torchaudio (ffmpeg): 成功 - {sample_rate}Hz, {waveform.shape}")
    except Exception as e:
        print(f"❌ torchaudio (ffmpeg): {str(e)}")

    # 方法4: librosa
    try:
        import librosa

        audio_data, sample_rate = librosa.load(str(audio_path), sr=None)
        print(f"✅ librosa: 成功 - {sample_rate}Hz, {audio_data.shape}")
    except Exception as e:
        print(f"❌ librosa: {str(e)}")

    # 方法5: soundfile
    try:
        import soundfile as sf

        audio_data, sample_rate = sf.read(str(audio_path))
        print(f"✅ soundfile: 成功 - {sample_rate}Hz, {audio_data.shape}")
    except Exception as e:
        print(f"❌ soundfile: {str(e)}")


def check_dependencies():
    """檢查相關依賴"""
    print("\n📦 檢查相關依賴:")

    deps = ["torchaudio", "librosa", "soundfile", "ffmpeg-python"]

    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep}: 已安裝")
        except ImportError:
            print(f"❌ {dep}: 未安裝")


def main():
    """主函數"""
    print("🎯 音檔格式調試工具")
    print("=" * 40)

    check_dependencies()
    analyze_audio_file()

    print("\n💡 建議:")
    print("1. 如果所有載入方法都失敗，可能需要安裝 ffmpeg")
    print("2. 考慮轉換音檔格式為 WAV")
    print("3. 檢查音檔是否損壞")


if __name__ == "__main__":
    main()
