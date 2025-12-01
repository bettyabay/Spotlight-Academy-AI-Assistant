"""
Main Streamlit dashboard to choose between Student and Admin experiences.
"""

from pathlib import Path
import sys

import streamlit as st

from config import Config

# Ensure project root is on sys.path (for any future imports)
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

st.set_page_config(
    page_title="Spotlight Academy - AI Assistant",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Spotlight Academy - AI Learning Assistant")
st.markdown(
    "Choose how you want to use the assistant.\n\n"
    "- **Students**: Ask questions about concepts, get explanations and hints.\n"
    "- **Admins/Instructors**: Upload and manage course materials for the assistant."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("I'm a Student")
    st.markdown(
        "- Ask questions about course content\n"
        "- Get step-by-step explanations\n"
        "- See which course materials your answer came from"
    )
    if st.button("Go to Student Chat", type="primary"):
        # Streamlit 1.28+ supports switch_page
        st.switch_page("pages/1_Student_Chat.py")

with col2:
    st.subheader("I'm an Admin / Instructor")
    st.markdown(
        "- Upload PDFs, DOCX, PPTX, and images\n"
        "- Ingest and re-index course materials\n"
        "- View ingestion status"
    )
    if st.button("Go to Admin Panel"):
        st.switch_page("pages/admin.py")

st.markdown("---")
st.caption(f"Spotlight Academy AI Assistant {getattr(Config, 'ENV', 'local')}")
