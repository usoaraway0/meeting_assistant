# 声明我们将从外部接收构建参数
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG HF_ENDPOINT # <-- 新增

# Step 1: builder阶段
FROM python:3.12-slim AS builder

# 将接收到的参数，设置为这个构建阶段的环境变量
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV HF_ENDPOINT=${HF_ENDPOINT} # <-- 新增

WORKDIR /app

RUN pip install uv
COPY requirements.txt .
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