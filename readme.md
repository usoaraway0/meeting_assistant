# 终极AI会议助手 (Ultimate AI Meeting Assistant)

![Demo GIF of the App](https://user-images.githubusercontent.com/your-id/your-repo/demo.gif) 
这是一个全栈AI应用，旨在将会议音频自动化地处理成结构化的、可查询的知识。用户可以上传会议录音，系统会自动完成语音转文字、生成会议摘要、提取待办事项，并允许用户就本次会议内容进行对话式问答。

## 🚀 核心功能 (Key Features)

- **本地语音转录**: 使用`faster-whisper`在本地进行高性能语音识别，保障数据隐私。
- **智能工作流**: 基于`LangGraph`构建的多步AI工作流，稳定地完成摘要、任务提取等任务。
- **高级RAG问答**: 采用`ParentDocumentRetriever`策略，提供上下文更丰富、更精准的问答体验。
- **异步处理**: 后端采用FastAPI后台任务处理耗时操作，前端UI不卡顿。
- **前后端分离**: 清晰的Web服务架构，前端(Streamlit)与后端(FastAPI)分离，易于维护和扩展。
- **一键启动**: 整个应用（前后端）已完全Docker化，通过`docker compose`实现一键部署和运行。

## 🛠️ 技术栈 (Tech Stack)

- **后端**: `FastAPI`, `Uvicorn`, `LangChain`, `LangGraph`, `Google Gemini`, `faster-whisper`
- **前端**: `Streamlit`
- **向量存储**: `FAISS`
- **部署**: `Docker`, `Docker Compose`
- **开发环境**: `Python 3.12`, `uv`

## 🏗️ 项目架构 (Architecture)

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'background': '#ffffff', 'primaryColor': '#f8f9fa', 'primaryTextColor': '#333', 'lineColor': '#6c757d', 'fontSize': '14px'}}}%%
graph TD
    subgraph 用户端
        A[用户浏览器<br>User Browser]
    end

    subgraph 前端服务器
        B[Streamlit应用<br>streamlit_app.py]
    end

    subgraph 后端服务器
        C[FastAPI入口<br>main.py]
        D{API路由<br>/api/v1/meetings.py}
        E[后台任务管理器<br>BackgroundTasks]
        F[LangGraph工作流<br>workflow.py]
        G[本地转录服务<br>faster-whisper]
        H[RAG问答链<br>ParentDocumentRetriever]
        I[外部LLM API<br>Google Gemini]
        J[(任务状态存储<br>Jobs Dictionary)]
        K[uploads 文件夹]
        L[knowledge_base_storage 文件夹]
    end
    
    A -- 1.上传音频 --> B;
    B -- 2.POST /upload --> D;
    D -- 3.启动后台任务 --> E;
    E -- 触发工作流 --> F;
    F -- 执行步骤 --> G & I & L;
    D -- 返回 Job ID --> B;
    B -- 轮询状态 --> D;
    D -- 查询状态 --> J;
    J -- 返回状态 --> D;
    B -- 任务完成后 --> A;
    A -- 提问 --> B;
    B -- POST /ask --> D;
    D -- 调用RAG --> H;
    H -- 检索/生成 --> L & I;
    D -- 返回答案 --> B;
    B -- 显示答案 --> A;
```

## ⚙️ 如何运行 (Getting Started)

### 1. 环境准备
- 已安装 [Docker](https://www.docker.com/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。
- 一个 Google Gemini API Key。

### 2. 设置
```bash
# 1. 克隆本仓库
git clone [https://github.com/your-username/ultimate-meeting-assistant.git](https://github.com/your-username/ultimate-meeting-assistant.git)
cd ultimate-meeting-assistant

# 2. 创建并配置 .env 文件
# 进入后端目录，复制示例文件
cd backend
cp .env.example .env

# 然后用你的编辑器打开 .env 文件，填入你的API Key
# GOOGLE_API_KEY="your-google-api-key-here"
```

### 3. 一键启动
在项目**根目录** (`ultimate_meeting_assistant/`)下，运行以下命令：
```bash
docker compose up --build
```
等待所有镜像构建完成和服务启动后，在你的浏览器中访问 `http://localhost:8501` 即可开始使用。