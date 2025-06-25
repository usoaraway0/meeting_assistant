# 使用与后端一致的Python基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装uv
RUN pip install uv

# 复制前端的依赖文件
COPY requirements.txt .

# 安装依赖
RUN uv pip install --system --no-cache -r requirements.txt

# 复制前端应用代码
COPY streamlit_app.py .

# 暴露Streamlit默认的8501端口
EXPOSE 8501

# 容器启动时运行Streamlit应用
# --server.address=0.0.0.0 是关键，让容器外的请求可以访问
# --server.enableCORS=false 是一个Streamlit在容器内运行时的常用设置，解决跨域问题
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port", "8501", "--server.enableCORS=false"]