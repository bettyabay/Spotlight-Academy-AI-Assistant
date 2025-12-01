"""
FastAPI app exposing the RAG chat endpoint for Spotlight Academy (Sprint 2).

This complements the Streamlit ingestion admin panel by providing:
- /api/chat endpoint for student-facing chat
- Basic guardrails to prevent full assignment/project solutions
"""

from typing import List, Optional, Dict

from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai

from config import Config
from src.rag.rag_service import RAGService
from src.guardrails.intent_classifier import (
    classify_intent,
    build_solution_guardrail_instructions,
    build_solution_seeking_response,
)


class ChatRequest(BaseModel):
    message: str
    student_id: Optional[str] = None
    module: Optional[str] = None
    chapter: Optional[str] = None
    lesson: Optional[str] = None
    # Quick action hint: "explain", "hint", "source"
    mode: Optional[str] = None


class SourceChunk(BaseModel):
    content: str
    source_file: Optional[str] = None
    module: Optional[str] = None
    chapter: Optional[str] = None
    lesson: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: List[SourceChunk]


app = FastAPI(title="Spotlight Academy RAG API", version="0.1.0")


@app.on_event("startup")
def _configure_genai():
    Config.validate()
    genai.configure(api_key=Config.GOOGLE_API_KEY)


rag_service = RAGService()


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    Main RAG chat endpoint used by the student-facing UI.

    - Classifies intent (concept_question, hint_request, solution_seeking)
    - Applies guardrails for solution-seeking queries
    - Retrieves relevant course content and calls Gemini for an answer
    - Returns answer plus structured citations
    """
    # 1) Classify intent & apply guardrails
    intent = classify_intent(payload.message)

    if intent == "solution_seeking":
        # Hard guardrail: do not call LLM, just return guided response
        guided_answer = build_solution_seeking_response()
        return ChatResponse(answer=guided_answer, intent=intent, sources=[])

    # 2) Retrieve context from RAG service
    filters: Dict = {}
    if payload.module:
        filters["module"] = payload.module
    if payload.chapter:
        filters["chapter"] = payload.chapter
    if payload.lesson:
        filters["lesson"] = payload.lesson

    retrieved = rag_service.retrieve_context(payload.message, filters or None)
    context_text, _ = rag_service.build_context_prompt(retrieved)

    # 3) Build system/user prompts for Gemini
    guardrail_instructions = build_solution_guardrail_instructions()

    # Adjust style based on quick action mode
    mode_instruction = ""
    if payload.mode == "explain":
        mode_instruction = "Focus on giving a clear, step-by-step explanation of the underlying concepts.\n"
    elif payload.mode == "hint":
        mode_instruction = (
            "Do NOT provide the full solution. Instead, give 1–3 progressively stronger hints "
            "that help the student move forward.\n"
        )
    elif payload.mode == "source":
        mode_instruction = (
            "Focus on summarizing what the retrieved sources say that is relevant to the question. "
            "Do not invent content beyond the provided context.\n"
        )

    system_prompt = (
        f"{guardrail_instructions}\n\n"
        "You MUST answer using ONLY the course content provided in the CONTEXT.\n"
        "If the context is not sufficient, say you don't have enough information from Spotlight Academy materials.\n"
        "Cite specific sources at the end of your answer under a 'Sources' section.\n"
    )

    user_prompt = (
        f"CONTEXT:\n{context_text or '[No context retrieved]'}\n\n"
        f"{mode_instruction}"
        f"STUDENT QUESTION:\n{payload.message}"
    )

    model_name = getattr(Config, "GENERATION_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    result = model.generate_content(
        [
            {"role": "system", "parts": [system_prompt]},
            {"role": "user", "parts": [user_prompt]},
        ]
    )

    answer_text = result.text or ""

    # 4) Build structured sources list for UI citations
    sources: List[SourceChunk] = []
    for item in retrieved:
        metadata = item.get("metadata", {}) or {}
        sources.append(
            SourceChunk(
                content=item.get("content") or item.get("chunk") or "",
                source_file=metadata.get("source_file") or item.get("source_file"),
                module=metadata.get("module") or item.get("module"),
                chapter=metadata.get("chapter") or item.get("chapter"),
                lesson=metadata.get("lesson") or item.get("lesson"),
            )
        )

    return ChatResponse(
        answer=answer_text,
        intent=intent,
        sources=sources,
    )


