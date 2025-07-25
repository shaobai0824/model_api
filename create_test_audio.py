#!/usr/bin/env python3
"""
建立測試音檔生成器
"""

import os

import numpy as np
import soundfile as sf


def create_test_audio():
    """建立一個簡單的測試音檔"""
    # 音檔設定
    sample_rate = 16000
    duration = 3  # 3 秒
    frequency = 440  # A4 音符頻率

    # 生成正弦波
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

    # 儲存音檔
    output_path = "test_audio.wav"
    sf.write(output_path, audio_data, sample_rate)

    print(f"✅ 測試音檔已建立: {output_path}")
    print(f"📊 音檔資訊:")
    print(f"   - 長度: {duration} 秒")
    print(f"   - 採樣率: {sample_rate} Hz")
    print(f"   - 頻率: {frequency} Hz")
    print(f"   - 檔案大小: {os.path.getsize(output_path)} bytes")

    return output_path


if __name__ == "__main__":
    create_test_audio()
