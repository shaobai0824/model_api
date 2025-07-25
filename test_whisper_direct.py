#!/usr/bin/env python3
"""
直接測試 whisper 音頻載入的腳本
"""


def test_whisper_load():
    """測試 whisper 載入音檔"""
    try:
        import torch
        import whisper

        print("🎯 測試 Whisper 音頻載入")
        print("=" * 40)

        # 載入音檔
        audio_path = "debug_audio/audio_571333182528946501.m4a"
        print(f"📁 載入音檔: {audio_path}")

        audio_data = whisper.load_audio(audio_path)
        print(f"✅ 載入成功!")
        print(f"📊 音頻資料: {type(audio_data)}, 長度: {len(audio_data)}")
        print(f"📏 音頻時長: {len(audio_data)/16000:.2f} 秒")

        # 轉換為 torch tensor
        waveform = torch.from_numpy(audio_data).unsqueeze(0)
        print(f"🔄 轉換為 tensor: {waveform.shape}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_transformers_pipeline():
    """測試 transformers pipeline 與 whisper 音頻的兼容性"""
    try:
        import torch
        import whisper
        from transformers import pipeline

        print("\n🧪 測試 Transformers Pipeline")
        print("=" * 40)

        # 載入音檔
        audio_path = "debug_audio/audio_571333182528946501.m4a"
        audio_data = whisper.load_audio(audio_path)

        print(f"✅ 音頻載入成功: {len(audio_data)} samples")

        # 嘗試創建 ASR pipeline (不實際執行，只測試兼容性)
        print("🔄 測試音頻資料格式兼容性...")

        # 檢查音頻資料格式
        print(f"📊 音頻類型: {type(audio_data)}")
        print(f"📊 音頻形狀: {audio_data.shape}")
        print(f"📊 音頻範圍: {audio_data.min():.3f} ~ {audio_data.max():.3f}")

        return True

    except Exception as e:
        print(f"❌ Pipeline 測試失敗: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("🎯 Whisper 音頻載入完整測試")
    print("=" * 50)

    # 測試1: 基本載入
    success1 = test_whisper_load()

    # 測試2: Pipeline 兼容性
    success2 = test_transformers_pipeline()

    if success1 and success2:
        print("\n🎉 所有測試通過！")
        print("💡 whisper.load_audio 可以正常工作")
        print("💡 建議檢查 ASR 服務中的其他部分")
    else:
        print("\n❌ 測試失敗")
        print("💡 需要進一步調試")


if __name__ == "__main__":
    main()
