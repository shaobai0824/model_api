#!/usr/bin/env python3
"""
音檔轉換工具 - 將 M4A 轉換為 WAV 格式
"""

import os
import subprocess
import tempfile
from pathlib import Path


def install_ffmpeg():
    """嘗試安裝 ffmpeg"""
    print("🔧 嘗試安裝 ffmpeg...")

    try:
        # 檢查是否已安裝
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("✅ ffmpeg 已安裝")
            return True
    except:
        pass

    # 嘗試使用 pip 安裝 ffmpeg-python
    try:
        subprocess.run(["pip", "install", "ffmpeg-python"], check=True)
        print("✅ 安裝 ffmpeg-python 成功")
    except:
        print("⚠️ 無法自動安裝 ffmpeg")

    return False


def convert_m4a_to_wav_python(input_path: str, output_path: str) -> bool:
    """使用 Python 庫轉換音檔"""
    try:
        import librosa
        import soundfile as sf

        # 使用 librosa 載入（會自動處理格式）
        audio_data, sample_rate = librosa.load(input_path, sr=None)

        # 保存為 WAV
        sf.write(output_path, audio_data, sample_rate)

        print(f"✅ 使用 librosa 轉換成功: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Python 庫轉換失敗: {str(e)}")
        return False


def convert_m4a_to_wav_ffmpeg(input_path: str, output_path: str) -> bool:
    """使用 ffmpeg 轉換音檔"""
    try:
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-acodec",
            "pcm_s16le",  # 16-bit PCM
            "-ar",
            "16000",  # 16kHz 取樣率
            "-ac",
            "1",  # 單聲道
            "-y",  # 覆蓋輸出檔
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ 使用 ffmpeg 轉換成功: {output_path}")
            return True
        else:
            print(f"❌ ffmpeg 轉換失敗: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ ffmpeg 轉換失敗: {str(e)}")
        return False


def convert_audio_robust(input_path: str, output_path: str) -> bool:
    """強化的音檔轉換方法"""
    print(f"🔄 轉換音檔: {input_path} -> {output_path}")

    # 方法1: 使用 ffmpeg
    if convert_m4a_to_wav_ffmpeg(input_path, output_path):
        return True

    # 方法2: 使用 Python 庫
    if convert_m4a_to_wav_python(input_path, output_path):
        return True

    print("❌ 所有轉換方法都失敗了")
    return False


def main():
    """主函數"""
    print("🎯 音檔轉換工具")
    print("=" * 40)

    # 檢查並安裝 ffmpeg
    install_ffmpeg()

    # 尋找需要轉換的音檔
    debug_dir = Path("debug_audio")
    if not debug_dir.exists():
        print("❌ 找不到 debug_audio 目錄")
        return

    audio_files = list(debug_dir.glob("audio_*.m4a"))
    if not audio_files:
        print("❌ 找不到需要轉換的音檔")
        return

    # 轉換所有音檔
    for audio_file in audio_files:
        wav_file = audio_file.with_suffix(".wav")

        if wav_file.exists():
            print(f"⏭️ 跳過已存在的檔案: {wav_file}")
            continue

        if convert_audio_robust(str(audio_file), str(wav_file)):
            print(f"✅ 轉換完成: {wav_file}")

            # 驗證轉換結果
            try:
                import librosa

                audio_data, sample_rate = librosa.load(str(wav_file))
                print(
                    f"📊 轉換後音檔: {sample_rate}Hz, {len(audio_data)/sample_rate:.2f}秒"
                )
            except:
                print("⚠️ 無法驗證轉換結果，但檔案已生成")
        else:
            print(f"❌ 轉換失敗: {audio_file}")


if __name__ == "__main__":
    main()
