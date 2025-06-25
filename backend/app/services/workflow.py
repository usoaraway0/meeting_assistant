# backend/app/services/workflow.py (完整新版)

from typing import TypedDict, List
import os
from pydantic import BaseModel, Field
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from .transcription import transcribe_audio_file

# --- 1. 定义状态 (State) ---
# 【核心修正】在状态中增加 google_api_key 字段
class WorkflowState(TypedDict):
    audio_path: str
    transcript: str
    summary: str
    action_items: List[str]
    error: str
    google_api_key: str # <--- 新增字段

# --- 2. 定义结构化输出模型 ---
class ActionItems(BaseModel):
    items: List[str] = Field(description="A list of action items from the meeting.")

# --- 3. 定义工作流节点 (Nodes) ---
def node_transcribe(state: WorkflowState):
    print("--- Node: Transcribing Audio ---")
    try:
        text = transcribe_audio_file(state["audio_path"])
        return {"transcript": text}
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}

def node_summarize(state: WorkflowState):
    print("--- Node: Summarizing Transcript ---")
    # 【核心修正】从 state 中获取 API Key，而不是从环境变量
    api_key = state["google_api_key"]
    llm = GoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=api_key)
    
    prompt = PromptTemplate.from_template("Please provide a concise summary of the following meeting transcript:\n\n{transcript}")
    chain = LLMChain(llm=llm, prompt=prompt)
    summary = chain.invoke({"transcript": state["transcript"]})
    return {"summary": summary['text']}

def node_extract_action_items(state: WorkflowState):
    print("--- Node: Extracting Action Items ---")
    # 【核心修正】从 state 中获取 API Key
    api_key = state["google_api_key"]
    llm = GoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=api_key)

    parser = PydanticOutputParser(pydantic_object=ActionItems)
    prompt = PromptTemplate(
        template="Extract all action items from the meeting transcript. {format_instructions}\n\n{transcript}",
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    action_items_obj = chain.invoke({"transcript": state["transcript"]})
    return {"action_items": action_items_obj.items}
    
# --- 4. 构建图 (Graph) ---
def build_graph():
    # 这部分无需修改
    workflow = StateGraph(WorkflowState)
    workflow.add_node("transcribe", node_transcribe)
    workflow.add_node("summarize", node_summarize)
    workflow.add_node("extract_action_items", node_extract_action_items)
    workflow.set_entry_point("transcribe")
    workflow.add_edge("transcribe", "summarize")
    workflow.add_edge("summarize", "extract_action_items")
    workflow.add_edge("extract_action_items", END)
    return workflow.compile()

langgraph_app = build_graph()