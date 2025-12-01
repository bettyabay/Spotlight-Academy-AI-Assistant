"""
Streamlit admin panel for content ingestion (moved from root app.py).
"""

import logging
from pathlib import Path
import sys

import streamlit as st

# Ensure project root is on sys.path so we can import src.*
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ingestion.ingestion_pipeline import IngestionPipeline
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(Config, "LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

st.title("📚 Spotlight Academy - Content Ingestion (Admin Panel)")
st.markdown("**Sprint 1: Content Ingestion Prototype**")

# Initialize session state
if "pipeline" not in st.session_state:
    try:
        st.session_state.pipeline = IngestionPipeline()
        st.success("✅ Ingestion pipeline initialized")
    except Exception as e:
        st.error(f"❌ Error initializing pipeline: {str(e)}")
        st.info("Please check your .env file and ensure all API keys are configured.")
        st.stop()

# Sidebar for configuration
with st.sidebar:
    st.header("Ingestion Configuration")
    st.markdown("---")

    module = st.text_input("Module", help="Optional: Module name for content organization")
    chapter = st.text_input("Chapter", help="Optional: Chapter name")
    lesson = st.text_input("Lesson", help="Optional: Lesson name")
    concept = st.text_input("Concept", help="Optional: Concept name")
    version = st.number_input("Version", min_value=1, value=1, step=1)

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload File", "📁 Process Directory", "📊 Ingestion Status"])

with tab1:
    st.header("Upload and Ingest Single File")
    st.markdown("Upload a PDF, DOCX, PPTX, or image file to ingest into the vector database.")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "pptx", "png", "jpg", "jpeg"],
        help="Supported formats: PDF, DOCX, PPTX, PNG, JPG, JPEG",
    )

    if uploaded_file is not None:
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")

        if st.button("🚀 Ingest File", type="primary"):
            # Save uploaded file temporarily
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / uploaded_file.name

            try:
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner("Processing file..."):
                    result = st.session_state.pipeline.ingest_file(
                        str(temp_path),
                        module=module or None,
                        chapter=chapter or None,
                        lesson=lesson or None,
                        concept=concept or None,
                        version=int(version),
                    )

                if result.get("success"):
                    st.success(f"✅ Successfully ingested {result['file_name']}")
                    st.json(result)
                else:
                    st.error(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
                    st.json(result)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()

with tab2:
    st.header("Process Directory")
    st.markdown("Ingest all supported files from a directory.")

    directory_path = st.text_input(
        "Directory Path",
        help="Enter the full path to the directory containing course materials",
    )

    if st.button("🚀 Process Directory", type="primary"):
        if not directory_path:
            st.warning("Please enter a directory path")
        else:
            try:
                with st.spinner("Processing directory..."):
                    results = st.session_state.pipeline.ingest_directory(
                        directory_path,
                        module=module or None,
                        chapter=chapter or None,
                        lesson=lesson or None,
                    )

                # Display results
                success_count = sum(1 for r in results if r.get("success"))
                total_count = len(results)

                st.success(f"✅ Processed {success_count}/{total_count} files")

                # Show detailed results
                for result in results:
                    status_icon = "✅" if result.get("success") else "❌"
                    label = f"{result.get('file_name', 'Unknown')} - {status_icon}"
                    with st.expander(label):
                        st.json(result)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with tab3:
    st.header("Ingestion Status")
    st.markdown("View the status of ingested content.")

    source_file_filter = st.text_input(
        "Filter by Source File (optional)",
        help="Leave empty to see all ingested files",
    )

    if st.button("🔄 Refresh Status"):
        try:
            status_data = st.session_state.pipeline.get_ingestion_status(
                source_file=source_file_filter if source_file_filter else None
            )

            if status_data:
                st.dataframe(status_data)
            else:
                st.info("No ingestion records found.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("**Spotlight Academy AI Assistant - Admin Content Ingestion Panel**")


