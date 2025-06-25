# backend/app/main.py (完整新版)
from fastapi import FastAPI
from app.api import router as meetings_router
import os
from dotenv import load_dotenv

# 在应用启动时加载环境变量
load_dotenv()

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("knowledge_base_storage", exist_ok=True)

app = FastAPI(title="AI Meeting Assistant API")

app.include_router(meetings_router, prefix="/api/v1/meetings", tags=["meetings"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Meeting Assistant API"}