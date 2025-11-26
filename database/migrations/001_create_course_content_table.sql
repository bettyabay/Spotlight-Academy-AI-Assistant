-- Create course_content table for vector storage
-- This migration should be run in your Supabase SQL editor

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create course_content table
CREATE TABLE IF NOT EXISTS course_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(768),  -- Google embedding-001 dimension
    metadata JSONB DEFAULT '{}',
    module TEXT,
    chapter TEXT,
    lesson TEXT,
    concept TEXT,
    source_file TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on embedding for vector similarity search
CREATE INDEX IF NOT EXISTS course_content_embedding_idx 
ON course_content 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS course_content_module_idx ON course_content(module);
CREATE INDEX IF NOT EXISTS course_content_chapter_idx ON course_content(chapter);
CREATE INDEX IF NOT EXISTS course_content_lesson_idx ON course_content(lesson);
CREATE INDEX IF NOT EXISTS course_content_source_file_idx ON course_content(source_file);
CREATE INDEX IF NOT EXISTS course_content_version_idx ON course_content(version);

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_course_content(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 8,
    filter_module text DEFAULT NULL,
    filter_chapter text DEFAULT NULL,
    filter_lesson text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    module text,
    chapter text,
    lesson text,
    concept text,
    source_file text,
    version integer,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        course_content.id,
        course_content.content,
        course_content.metadata,
        course_content.module,
        course_content.chapter,
        course_content.lesson,
        course_content.concept,
        course_content.source_file,
        course_content.version,
        1 - (course_content.embedding <=> query_embedding) as similarity
    FROM course_content
    WHERE 
        course_content.embedding IS NOT NULL
        AND (filter_module IS NULL OR course_content.module = filter_module)
        AND (filter_chapter IS NULL OR course_content.chapter = filter_chapter)
        AND (filter_lesson IS NULL OR course_content.lesson = filter_lesson)
        AND (1 - (course_content.embedding <=> query_embedding)) >= match_threshold
    ORDER BY course_content.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_course_content_updated_at 
    BEFORE UPDATE ON course_content 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

