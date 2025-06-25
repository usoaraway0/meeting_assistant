import os
from faster_whisper import WhisperModel

# --- 全局模型缓存 ---
# 这是一个简单的字典，用于在内存中缓存已加载的模型。
# 避免每次调用都重新加载模型，这对于Web服务至关重要，因为模型加载很耗时。
model_cache = {}
MODEL_SIZE = "base" # 你可以选择: "tiny", "base", "small", "medium", "large-v3"

def transcribe_audio_file(audio_path: str) -> str:
    """
    Transcribes an audio file using the locally run faster-whisper model.
    """
    global model_cache
    
    # 设定设备和计算类型。对于CPU，int8是很好的选择，速度快且精度损失小。
    device = "cpu"
    compute_type = "int8"
    
    print(f"🎤 Starting local transcription for {audio_path} using faster-whisper...")
    
    # --- 模型加载与缓存 ---
    # 检查模型是否已经在缓存中，如果不在，则加载并存入缓存
    if MODEL_SIZE not in model_cache:
        print(f"第一次加载模型 '{MODEL_SIZE}'，这可能需要一些时间来下载和初始化...")
        try:
            model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
            model_cache[MODEL_SIZE] = model
        except Exception as e:
            print(f"🔴 加载 faster-whisper 模型失败: {e}")
            raise
    else:
        print(f"从缓存中加载模型 '{MODEL_SIZE}'。")
        model = model_cache[MODEL_SIZE]

    # --- 执行转录 ---
    # beam_size=5 是一个常用的解码参数
    try:
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        print(f"检测到语言: {info.language}，置信度: {info.language_probability:.2f}")
        
        # 将所有识别出的文本片段拼接成一个完整的字符串
        full_transcript = "".join(segment.text for segment in segments)
        
        print("✅ Local transcription complete.")
        return full_transcript

    except Exception as e:
        print(f"🔴 本地转录过程中发生错误: {e}")
        # 在实际应用中，这里应该有更健壮的错误处理
        raise