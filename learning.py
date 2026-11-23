import streamlit as st
from openai import OpenAI
import json
import os

st.set_page_config(
    page_title="AI Chat",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded",
    menu_items={}
)

SESSION_FILE = "chat_session.json"

# 读取会话文件
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 保存会话文件
def save_sessions(data):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if "session_list" not in st.session_state:
    st.session_state.session_list = load_sessions()
if "active_session_idx" not in st.session_state:
    st.session_state.active_session_idx = -1

#创建会话
def create_new_chat_session():
    new_session = {
        "title": f"会话{len(st.session_state.session_list)+1}",
        "messages": [],
        "ai_name": "AI",
        "ai_personality": "温柔"
    }
    st.session_state.session_list.append(new_session)
    save_sessions(st.session_state.session_list)
    st.session_state.active_session_idx = len(st.session_state.session_list) - 1


def delete_session(index):
    st.session_state.session_list.pop(index)
    save_sessions(st.session_state.session_list)
    if st.session_state.active_session_idx >= len(st.session_state.session_list):
        st.session_state.active_session_idx = max(0, len(st.session_state.session_list) - 1)
    elif st.session_state.active_session_idx == index:
        if st.session_state.session_list:
            st.session_state.active_session_idx = max(0, index - 1)
        else:
            st.session_state.active_session_idx = -1
    st.rerun()

if len(st.session_state.session_list) == 0:
    create_new_chat_session()

#侧边框
with st.sidebar:
    st.title("⚙ AI助手设置")
    # 获取当前激活会话
    if st.session_state.active_session_idx >= 0:
        current_session_sidebar = st.session_state.session_list[st.session_state.active_session_idx]
        current_session_sidebar["ai_name"] = st.text_input("填写AI名称", value=current_session_sidebar["ai_name"])
        current_session_sidebar["ai_personality"] = st.text_area("设定AI性格、说话语气", value=current_session_sidebar["ai_personality"])
        # 修改配置立刻保存至本地文件
        save_sessions(st.session_state.session_list)

    st.divider()
    if st.button("➕ 新建会话", use_container_width=True):
        create_new_chat_session()
        st.rerun()

    st.subheader("📜 会话列表")
    for index, item in enumerate(st.session_state.session_list):
        with st.container():
            col1, col2 = st.columns([4, 1])
            btn_title = item["title"]
            with col1:
                is_active = index == st.session_state.active_session_idx
                if st.button(btn_title, key=f"sid_{index}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_session_idx = index
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{index}"):
                    delete_session(index)


client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com"
)


if st.session_state.active_session_idx == -1 or len(st.session_state.session_list) == 0:
    st.markdown("# 欢迎使用AI聊天助手")
    st.markdown("左侧侧边栏点击【新建会话】开启对话。")
else:
    current_session = st.session_state.session_list[st.session_state.active_session_idx]
    st.header(f"{current_session['ai_name']}")

    for msg in current_session["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("请输入你的问题……")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        current_session["messages"].append({"role": "user", "content": user_input})

        system_prompt = f"你的名字叫做{current_session['ai_name']}。你的性格：{current_session['ai_personality']}。全程严格按照设定的性格进行回答。"
        request_msg = [{"role": "system", "content": system_prompt}]
        request_msg.extend(current_session["messages"])

        with st.chat_message("assistant"):
            response_placeholder = st.empty()

            stream_result = client.chat.completions.create(
                model="deepseek-chat",
                messages=request_msg,
                stream=True
            )

            full_answer = ""
            for chunk in stream_result:
                if chunk.choices[0].delta.content is not None:
                    full_answer += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_answer)

        current_session["messages"].append({"role": "assistant", "content": full_answer})

        if len(current_session["messages"]) == 2:
            current_session["title"] = user_input[:12]
        save_sessions(st.session_state.session_list)
        st.rerun()
