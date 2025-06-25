from typing import TypedDict, List
import os
from pydantic import BaseModel, Field
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from .transcription import transcribe_audio_file

class WorkflowState(TypedDict):
    audio_path: str
    transcript: str
    summary: str
    action_items: List[str]
    error: str
    google_api_key: str

class ActionItems(BaseModel):
    items: List[str] = Field(description="A list of action items from the meeting.")

# --- 节点定义 ---
def node_transcribe(state: WorkflowState):
    print("--- Node: Transcribing Audio ---")
    try:
        text = transcribe_audio_file(state["audio_path"])
        # 【修正】返回转录结果的同时，也清空error字段
        return {"transcript": text, "error": None}
    except Exception as e:
        error_message = f"Transcription failed: {e}"
        print(f"🔴 {error_message}")
        # 【修正】当失败时，返回错误信息
        return {"error": error_message}

# ... node_summarize 和 node_extract_action_items 保持不变 ...
def node_summarize(state: WorkflowState):
    print("--- Node: Summarizing Transcript ---")
    api_key = state["google_api_key"]
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=api_key)
    prompt = PromptTemplate.from_template("Please provide a concise summary of the following meeting transcript:\n\n{transcript}")
    chain = LLMChain(llm=llm, prompt=prompt)
    summary = chain.invoke({"transcript": state["transcript"]})
    return {"summary": summary['text']}

def node_extract_action_items(state: WorkflowState):
    print("--- Node: Extracting Action Items ---")
    api_key = state["google_api_key"]
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=api_key)
    parser = PydanticOutputParser(pydantic_object=ActionItems)
    prompt = PromptTemplate(
        template="Extract all action items from the meeting transcript. {format_instructions}\n\n{transcript}",
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    action_items_obj = chain.invoke({"transcript": state["transcript"]})
    return {"action_items": action_items_obj.items}


# --- 【核心修正】决策节点 ---
def decide_after_transcription(state: WorkflowState):
    """决策节点：在转录后，根据是否存在错误来决定下一步走向。"""
    print("--- Node: Deciding next step ---")
    if state.get("error"):
        print("-> Transcription failed. Ending workflow.")
        return "end_with_failure"
    else:
        print("-> Transcription succeeded. Continuing to summary.")
        return "continue_to_summary"

# --- 构建图 (Graph) ---
def build_graph():
    workflow = StateGraph(WorkflowState)
    workflow.add_node("transcribe", node_transcribe)
    workflow.add_node("summarize", node_summarize)
    workflow.add_node("extract_action_items", node_extract_action_items)

    # 【核心修正】添加决策节点
    workflow.add_node("transcription_decision", decide_after_transcription)

    # 【核心修正】定义新的流程逻辑
    workflow.set_entry_point("transcribe")
    workflow.add_edge("transcribe", "transcription_decision")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "transcription_decision",
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