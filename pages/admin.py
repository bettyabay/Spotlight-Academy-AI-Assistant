"""
Streamlit admin panel for content ingestion (moved from root app.py).
"""

import logging
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

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

def render_ingestion_results(results):
    """Display ingestion summary and per-file details."""
    if not results:
        st.info("No supported files were found in the provided folder.")
        return

    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)
    st.success(f"✅ Processed {success_count}/{total_count} files")

    for result in results:
        status_icon = "✅" if result.get("success") else "❌"
        label = f"{result.get('file_name', 'Unknown')} - {status_icon}"
        with st.expander(label):
            st.json(result)

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
    st.header("Process Directory / Folder")
    st.markdown(
        "Process a local directory on the server or upload a zipped folder to ingest "
        "all supported files (PDF, DOCX, PPTX, PNG, JPG, JPEG). Subfolders are scanned automatically."
    )

    # Option 1: process an existing directory on the server
    st.subheader("Use a server directory path")
    directory_path = st.text_input(
        "Directory Path",
        help="Enter the full path to the directory containing course materials",
    )

    if st.button("🚀 Process Directory", type="primary", key="process_directory"):
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
                        concept=concept or None,
                        version=int(version),
                    )

                render_ingestion_results(results)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # Option 2: upload a zipped folder and ingest its contents
    st.subheader("Upload and ingest a zipped folder")
    uploaded_zip = st.file_uploader(
        "Upload a .zip file containing your course materials",
        type=["zip"],
        help="We will extract the zip to a temporary folder and ingest all supported files inside it.",
    )

    if uploaded_zip is not None:
        st.info(f"📦 Uploaded archive: {uploaded_zip.name} ({uploaded_zip.size / 1024:.2f} KB)")

    if st.button("🚀 Ingest Uploaded Folder", type="primary", key="process_zip"):
        if uploaded_zip is None:
            st.warning("Please upload a .zip file first.")
        else:
            temp_root = Path("temp_uploads")
            temp_root.mkdir(exist_ok=True)
            temp_dir = Path(tempfile.mkdtemp(prefix="folder_ingest_", dir=temp_root))
            zip_path = temp_dir / uploaded_zip.name
            extract_dir = temp_dir / "extracted"

            try:
                # Save the uploaded zip
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.getbuffer())

                # Extract contents
                extract_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                with st.spinner("Processing uploaded folder..."):
                    results = st.session_state.pipeline.ingest_directory(
                        str(extract_dir),
                        module=module or None,
                        chapter=chapter or None,
                        lesson=lesson or None,
                        concept=concept or None,
                        version=int(version),
                    )

                render_ingestion_results(results)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                # Clean up extracted files
                shutil.rmtree(temp_dir, ignore_errors=True)

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


