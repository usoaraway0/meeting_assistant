# 该脚本的唯一目的，就是在构建Docker镜像时，
# 提前下载并缓存好faster-whisper模型。
from faster_whisper import WhisperModel

# 你可以在这里指定你最终想要使用的模型尺寸
MODEL_SIZE = "base"

print(f"Downloading faster-whisper model: {MODEL_SIZE}...")

try:
    # 仅初始化模型就会触发下载
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print(f"Model {MODEL_SIZE} downloaded successfully.")
except Exception as e:
    print(f"Failed to download model {MODEL_SIZE}. Error: {e}")
    # 抛出异常以使Docker构建失败，这能让我们及早发现网络问题
    raise e