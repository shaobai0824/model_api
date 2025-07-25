
        from fastapi import FastAPI, UploadFile, File
        import uvicorn
        import torch
        from transformers import pipeline
        import torchaudio
        import io

        # --- 模型初始化 ---
        # 這裡的路徑請換成您微調後模型的實際路徑
        MODEL_PATH = "./models/breeze-asr-finetuned" 
        
        # 檢查是否有可用的 GPU
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"使用的裝置: {device}")

        # 載入模型 Pipeline
        # 根據 Breeze ASR 的建議，可能需要指定 task 與 model_kwargs
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=MODEL_PATH,
            device=device,
            # 如果是繁體中文，可能需要此參數
            # task="transcribe",
            # model_kwargs={"language": "zh-TW"} 
        )
        
        # 建立 FastAPI 應用
        app = FastAPI()

        @app.get("/")
        def read_root():
            return {"message": "Breeze ASR 服務已啟動"}

        @app.post("/recognize")
        async def recognize_speech(audio_file: UploadFile = File(...)):
            """
            接收音檔，回傳辨識後的文字
            """
            # 讀取上傳的音檔內容
            audio_bytes = await audio_file.read()
            
            # 使用 torchaudio 載入音檔，並確保取樣率正確
            # Breeze ASR 需要 16kHz 的取樣率
            waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
            
            # 如果取樣率不是 16kHz，則進行重採樣
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                waveform = resampler(waveform)

            # 將 waveform 轉換為 pipeline 需要的格式 (numpy array)
            audio_input = waveform.squeeze().numpy()

            # 進行語音辨識
            result = asr_pipeline(audio_input)
            
            return {"text": result["text"]}

        if __name__ == "__main__":
            # 啟動服務，監聽在 8001 port
            uvicorn.run(app, host="0.0.0.0", port=8001)
