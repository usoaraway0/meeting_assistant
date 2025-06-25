# 声明我们将从外部接收构建参数
ARG HF_ENDPOINT

# Step 1: builder阶段
FROM python:3.12-slim AS builder

# 将接收到的参数，设置为这个构建阶段的环境变量
ENV HF_ENDPOINT=${HF_ENDPOINT:-https://huggingface.co}

WORKDIR /app

RUN pip install uv
COPY requirements.txt .

# 先从PyTorch官方的CPU版本专用源，安装torch和torchaudio
# 确保我们下载的是不含任何NVDIA依赖的、轻量的CPU版本，避免uv下载超时。
RUN uv pip install --system --no-cache torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt

COPY download_model.py .
# 这个脚本现在会在设置了HF_ENDPOINT的环境变量下运行
RUN python download_model.py

# Step 2: 最终运行镜像阶段
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache /root/.cache

COPY ./app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]