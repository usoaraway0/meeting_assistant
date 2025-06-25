# backend/app/api/meetings.py (完整新版)

from fastapi import APIRouter, File, UploadFile, BackgroundTasks, HTTPException
from ..schemas.meeting import JobResponse, StatusResponse, AskRequest, AskResponse
import uuid
import os
import shutil
from ..services.workflow import langgraph_app
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

router = APIRouter()
jobs = {}

def get_rag_chain_for_job(job_id: str, api_key: str): # <--- 修正点：接收api_key
    transcript_path = os.path.join("knowledge_base_storage", job_id, "transcript.txt")
    if not os.path.exists(transcript_path):
        return None

    # --- 修正点：使用传入的api_key ---
    llm = GoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    
    loader = TextLoader(transcript_path)
    docs = loader.load()
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
    vectorstore = FAISS.from_documents(docs, embeddings)
    store = InMemoryStore()
    retriever = ParentDocumentRetriever(vectorstore=vectorstore, docstore=store, child_splitter=child_splitter, parent_splitter=parent_splitter)
    retriever.add_documents(docs)
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# 【核心修正】run_workflow现在接收api_key作为参数
def run_workflow(job_id: str, audio_path: str, transcript_dir: str, api_key: str):
    """The background task function."""
    jobs[job_id] = {"status": "processing", "summary": None, "action_items": None}
    
    config = {"recursion_limit": 5}
    # 【核心修正】将api_key放入工作流的初始状态
    initial_state = {"audio_path": audio_path, "google_api_key": api_key}
    
    final_state = langgraph_app.invoke(initial_state, config=config)

    transcript_path = os.path.join(transcript_dir, "transcript.txt")
    with open(transcript_path, "w") as f:
        f.write(final_state['transcript'])

    jobs[job_id] = {
        "status": "complete", 
        "summary": final_state.get("summary"), 
        "action_items": final_state.get("action_items"), 
        "transcript": final_state.get("transcript")
        }

@router.post("/upload", response_model=JobResponse)
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    upload_dir = "uploads"
    job_storage_dir = os.path.join("knowledge_base_storage", job_id)
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(job_storage_dir, exist_ok=True)
    audio_path = os.path.join(upload_dir, f"{job_id}_{file.filename}")
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 【核心修正】在启动后台任务前，先在主进程中获取API Key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=500, detail="Google API Key not configured on the server.")

    # 【核心修正】将获取到的API Key作为参数传给后台任务
    background_tasks.add_task(run_workflow, job_id, audio_path, job_storage_dir, google_api_key)

    jobs[job_id] = {"status": "queued"}
    return {"job_id": job_id, "message": "File uploaded, processing started."}

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}

@router.post("/ask/{job_id}", response_model=AskResponse)
async def ask_question(job_id: str, request: AskRequest):
    job = jobs.get(job_id)
    if not job or job["status"] != "complete":
        raise HTTPException(status_code=400, detail="Job not complete or not found")
    
    # 【核心修正】将API Key也传递给RAG链的创建函数
    google_api_key = os.getenv("GOOGLE_API_KEY")
    qa_chain = get_rag_chain_for_job(job_id, google_api_key)
    if not qa_chain:
        raise HTTPException(status_code=500, detail="Could not create RAG chain.")
    result = qa_chain.invoke(request.question)
    return {"answer": result["result"]}