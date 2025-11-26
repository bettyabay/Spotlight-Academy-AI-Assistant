# Spotlight Academy AI Assistant

Spotlight Academy AI Learning Assistant builds a curriculum-based AI tutor with a student chat, admin content management, and strict guardrails to prevent direct solutions. It uses Google Gemini, a vector database, and Streamlit for a secure, role-based learning experience.

## Sprint 1: Foundation (Current)

### Components Implemented

- ✅ **System Architecture**: Modular Python structure with separation of concerns
- ✅ **Vector DB Setup**: Supabase integration with pgvector extension
- ✅ **Embedding Pipeline**: Google embedding model integration
- ✅ **Content Ingestion**: Support for PDF, DOCX, PPTX, and image OCR
- ✅ **Chunking**: Semantic text chunking (200-500 tokens) with overlap
- ✅ **Streamlit Prototype**: Admin interface for content ingestion

### Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Fill in your Supabase credentials and Google API key

3. **Set Up Supabase Database**
   - Run the migration script: `database/migrations/001_create_course_content_table.sql`
   - This creates the `course_content` table with vector support

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

### Project Structure

```
├── app.py                          # Streamlit ingestion interface
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── src/
│   ├── database/
│   │   └── supabase_client.py     # Supabase vector DB operations
│   ├── embeddings/
│   │   └── embedding_service.py   # Google embedding generation
│   └── ingestion/
│       ├── chunking.py             # Text chunking utilities
│       ├── document_processor.py  # File format processors
│       └── ingestion_pipeline.py  # Main ingestion orchestrator
└── database/
    └── migrations/                 # SQL migration scripts
```

### Features

- **Multi-format Support**: PDF, DOCX, PPTX, and image OCR
- **Semantic Chunking**: Intelligent text splitting (200-500 tokens)
- **Metadata Tagging**: Module, chapter, lesson, concept organization
- **Version Control**: Support for content updates and re-indexing
- **Vector Storage**: Efficient similarity search with Supabase pgvector

### Next Steps (Sprint 2)

- Chat interface MVP
- RAG endpoint
- Basic guardrails
