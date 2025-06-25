import streamlit as st
import requests
import time
import os

# 后端API的地址
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")
st.title("🤖 终极AI会议助手")

# --- 1. 文件上传 ---
st.header("1. 上传会议录音")
uploaded_file = st.file_uploader(
    "选择一个音频文件 (MP3, WAV, M4A)...", 
    type=["mp3", "wav", "m4a", "mp4"]
)

if uploaded_file is not None:
    if "job_id" not in st.session_state or st.session_state.get("uploaded_filename") != uploaded_file.name:
        with st.spinner("Uploading and starting analysis..."):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            try:
                response = requests.post(f"{BACKEND_URL}/api/v1/meetings/upload", files=files)
                if response.status_code == 200:
                    st.session_state.job_id = response.json()["job_id"]
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.success(f"文件上传成功！任务ID: {st.session_state.job_id}")
                else:
                    st.error(f"上传失败: {response.text}")
                    st.stop()
            except requests.exceptions.ConnectionError:
                st.error("无法连接到后端服务。请确保后端正在运行。")
                st.stop()
    
    job_id = st.session_state.job_id

    # --- 2. 状态轮询和结果展示 ---
    st.header("2. 分析结果")
    
    status_placeholder = st.empty()
    transcript_placeholder = st.empty()
    summary_placeholder = st.empty()
    actions_placeholder = st.empty()
    
    # 轮询任务状态
    while True:
        try:
            status_response = requests.get(f"{BACKEND_URL}/api/v1/meetings/status/{job_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                with status_placeholder.container():
                    st.info(f"任务状态: **{status}**")

                if status == "complete":
                    with transcript_placeholder.container():
                        st.subheader("完整文字稿")
                        with st.expander("点击展开/收起完整文字稿", expanded=True):
                            st.text_area("文字稿内容", status_data.get("transcript", "无文字稿"), height=300)
                    with summary_placeholder.container():
                        st.subheader("会议摘要")
                        st.markdown(status_data.get("summary", "无摘要"))
                    with actions_placeholder.container():
                        st.subheader("待办事项")
                        action_items = status_data.get("action_items", [])
                        if action_items:
                            for item in action_items:
                                st.checkbox(item)
                        else:
                            st.write("无待办事项")
                    st.session_state.job_complete = True
                    break
                elif status == "failed":
                    st.error("任务处理失败。")
                    break
            else:
                st.error("获取状态失败。")
                break
            
            time.sleep(5) # 每5秒轮询一次
        except requests.exceptions.ConnectionError:
            st.error("无法连接到后端服务。")
            st.stop()
            
    # --- 3. 对话问答 ---
    if st.session_state.get("job_complete"):
        st.header("3. 与会议纪要对话")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("就这次会议提问..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("思考中..."):
                    try:
                        ask_response = requests.post(
                            f"{BACKEND_URL}/api/v1/meetings/ask/{job_id}",
                            json={"question": prompt}
                        )
                        if ask_response.status_code == 200:
                            full_response = ask_response.json()["answer"]
                            message_placeholder.markdown(full_response)
                        else:
                            message_placeholder.error(f"回答失败: {ask_response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("无法连接到后端服务。")
            st.session_state.messages.append({"role": "assistant", "content": full_response})