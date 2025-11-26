# Setup Guide - Sprint 1

## Prerequisites

- Python 3.8 or higher
- Supabase account and project
- Google API key with Generative AI access

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Where to find these values:**
- **Supabase URL & Keys**: Go to your Supabase project → Settings → API
- **Google API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Set Up Supabase Database

1. Open your Supabase project dashboard
2. Go to SQL Editor
3. Run the migration script: `database/migrations/001_create_course_content_table.sql`
4. Verify the `course_content` table was created

**Important Notes:**
- The migration enables the `pgvector` extension
- Creates indexes for efficient vector search
- Sets up the `match_course_content` RPC function for similarity search

### 4. Verify Embedding Model Dimension

Google's `embedding-001` model may have different dimensions. Check the actual dimension:

1. Run a test embedding generation
2. Update `VECTOR_DIMENSION` in `config.py` if needed
3. Update the SQL migration if the dimension differs from 768

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Testing the Setup

### Test File Upload

1. Prepare a test PDF, DOCX, or PPTX file
2. Open the Streamlit app
3. Go to "Upload File" tab
4. Upload your test file
5. Fill in optional metadata (module, chapter, lesson)
6. Click "Ingest File"
7. Check the "Ingestion Status" tab to verify

### Verify Database

1. Go to Supabase dashboard → Table Editor
2. Check the `course_content` table
3. You should see rows with:
   - `content`: Text chunks
   - `embedding`: Vector arrays
   - `metadata`: JSON with file info
   - `source_file`: Original filename

## Troubleshooting

### Common Issues

**1. "Missing required configuration" error**
- Check that your `.env` file exists and has all required variables
- Ensure no extra spaces or quotes around values

**2. "Error generating embedding"**
- Verify your Google API key is valid
- Check that you have access to the embedding model
- Ensure your API key has the correct permissions

**3. "Table 'course_content' does not exist"**
- Run the SQL migration script in Supabase SQL Editor
- Verify the migration completed successfully

**4. "Vector dimension mismatch"**
- Check the actual dimension of your embeddings
- Update `VECTOR_DIMENSION` in `config.py`
- Re-run the migration with correct dimension

**5. Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## Next Steps

Once Sprint 1 is working:
- Test with multiple file types
- Verify chunking quality
- Test re-indexing (version control)
- Prepare for Sprint 2 (Chat interface)

