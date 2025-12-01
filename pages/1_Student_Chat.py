"""
Streamlit student-facing chat interface (Sprint 2).

This UI calls the FastAPI RAG endpoint defined in chat_api.py.
"""

import logging
from typing import Dict

import requests
import streamlit as st

from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)


API_BASE_URL = getattr(Config, "CHAT_API_BASE_URL", "http://localhost:8000")


st.title(" Student Chat - Spotlight Academy AI Assistant")
st.markdown(
    "Ask questions about your Spotlight Academy course materials. "
    "**Note:** I can explain concepts and give hints, but I won't provide full assignment solutions."
)


def send_chat_request(message: str, mode: str | None = None) -> Dict:
    payload = {
        "message": message,
        "mode": mode,
    }
    try:
        resp = requests.post(f"{API_BASE_URL}/api/chat", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        st.error("There was a problem contacting the AI assistant. Please try again.")
        return {}


if "messages" not in st.session_state:
    st.session_state.messages = []

# Quick action buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🧠 Explain it"):
        st.session_state.quick_mode = "explain"
with col2:
    if st.button("💡 Give me a hint"):
        st.session_state.quick_mode = "hint"
with col3:
    if st.button("📚 Show the source"):
        st.session_state.quick_mode = "source"

quick_mode = st.session_state.get("quick_mode")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type your question about the course...")

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_request(prompt, mode=quick_mode)

        if not result:
            st.stop()

        answer = result.get("answer", "")
        intent = result.get("intent", "")
        sources = result.get("sources", [])

        # Display answer
        st.markdown(answer)

        # Display citations
        if sources:
            st.markdown("---")
            st.markdown("**Sources (Spotlight Academy course content):**")
            for idx, src in enumerate(sources, start=1):
                path_parts = [
                    p
                    for p in [
                        src.get("module"),
                        src.get("chapter"),
                        src.get("lesson"),
                    ]
                    if p
                ]
                label = src.get("source_file") or "Course material"
                if path_parts:
                    label += f" — {' > '.join(path_parts)}"
                st.markdown(f"- **Source {idx}**: {label}")

        # Append assistant message to history
        st.session_state.messages.append(
            {"role": "assistant", "content": answer or "_No answer returned._"}
        )


