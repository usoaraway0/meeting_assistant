# backend/app/services/workflow.py

from typing import TypedDict, List
import os
from pydantic import BaseModel, Field
from langchain_google_genai import GoogleGenerativeAI
# from langchain.chains import LLMChain  <- 不再使用被弃用的LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END
from .transcription import transcribe_audio_file

# --- 1. State 和 Pydantic 模型 ---
class WorkflowState(TypedDict):
    audio_path: str
    transcript: str
    summary: str
    action_items: List[str]
    error: str
    google_api_key: str

class ActionItems(BaseModel):
    items: List[str] = Field(description="A list of action items from the meeting.")

# --- 2. 节点定义 ---
def node_transcribe(state: WorkflowState):
    print("--- Node: Transcribing Audio ---")
    try:
        text = transcribe_audio_file(state["audio_path"])
        return {"transcript": text, "error": None}
    except Exception as e:
        error_message = f"Transcription failed: {e}"
        print(f"🔴 {error_message}")
        # 失败时只返回错误信息，不再返回空的transcript
        return {"error": error_message}

def node_summarize(state: WorkflowState):
    print("--- Node: Summarizing Transcript ---")
    api_key = state["google_api_key"]
    
    # 使用LCEL构建链
    prompt = PromptTemplate.from_template(
        "Please provide a concise summary of the following meeting transcript:\n\n{transcript}"
    )
    llm = GoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.4, google_api_key=api_key)
    # StrOutputParser确保我们得到的是一个字符串
    chain = prompt | llm | StrOutputParser()
    
    summary = chain.invoke({"transcript": state["transcript"]})
    return {"summary": summary}

def node_extract_action_items(state: WorkflowState):
    print("--- Node: Extracting Action Items ---")
    api_key = state["google_api_key"]

    # 使用LCEL构建链，并采纳Copilot的健壮性检查思想
    parser = PydanticOutputParser(pydantic_object=ActionItems)
    prompt = PromptTemplate(
        template="Extract all action items from the meeting transcript.\n{format_instructions}\n\n{transcript}",
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=api_key)
    chain = prompt | llm | parser

    try:
        action_items_obj = chain.invoke({"transcript": state["transcript"]})
        items = action_items_obj.items if isinstance(action_items_obj, ActionItems) else []
        return {"action_items": items}
    except Exception as e:
        # 如果Pydantic解析失败，我们也优雅地处理
        print(f"⚠️ Action items parsing failed: {e}")
        return {"action_items": []}

# --- 3. 决策函数 ---
def decide_after_transcription(state: WorkflowState):
    print("--- Node: Deciding next step ---")
    if state.get("error"):
        print("-> Transcription failed. Ending workflow.")
        return "end_with_failure"
    else:
        print("-> Transcription succeeded. Continuing to summary.")
        return "continue_to_summary"

# --- 4. 构建图 (Graph) ---
def build_graph():
    workflow = StateGraph(WorkflowState)
    workflow.add_node("transcribe", node_transcribe)
    workflow.add_node("summarize", node_summarize)
    workflow.add_node("extract_action_items", node_extract_action_items)
    workflow.set_entry_point("transcribe")
    workflow.add_conditional_edges(
        "transcribe",
        decide_after_transcription,
        {
            "continue_to_summary": "summarize",
            "end_with_failure": END,
        },
    )
    workflow.add_edge("summarize", "extract_action_items")
    workflow.add_edge("extract_action_items", END)
    return workflow.compile()

langgraph_app = build_graph()