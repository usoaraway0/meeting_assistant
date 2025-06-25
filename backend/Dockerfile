# Step 1: 使用一个官方的、包含了构建工具的Python基础镜像
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装uv，我们用它来安装依赖，速度更快
RUN pip install uv

# 仅复制依赖文件，以便利用Docker的层缓存机制
COPY requirements.txt .

# 使用uv安装所有依赖
# --system 表示安装到系统全局，因为我们在一个干净的容器里
RUN uv pip install --system --no-cache -r requirements.txt

# Step 2: 创建最终的、轻量的运行镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 从上一个"builder"阶段，复制已安装好的依赖库
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制下载模型的脚本到容器中
# 这个脚本会在容器启动时运行，确保模型已经下载好
COPY download_model.py .
RUN python download_model.py

# 复制你的应用代码到容器中
COPY ./app /app/app

# 暴露8000端口，让外界可以访问
EXPOSE 8000

# 容器启动时要执行的命令
# 这里的 --host 0.0.0.0 和我们之前在streamlit里用的是一个道理，让容器内的服务能被外部访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
