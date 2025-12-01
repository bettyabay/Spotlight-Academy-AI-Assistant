"""
Basic intent classifier and guardrail helpers (Sprint 2).

Categories:
- concept_question: asking about a concept/explanation
- hint_request: explicitly asking for hints
- solution_seeking: asking for direct answers/solutions to assignments/projects
"""

from typing import Literal
import re

IntentLabel = Literal["concept_question", "hint_request", "solution_seeking"]


def classify_intent(user_message: str) -> IntentLabel:
    """
    Very lightweight rule-based classifier.
    This can later be replaced by a dedicated ML model.
    """
    text = (user_message or "").lower()

    # Explicit hint-style requests
    hint_patterns = [
        r"\bgive me a hint\b",
        r"\bany hints?\b",
        r"\bclue\b",
        r"\bhelp me get started\b",
    ]
    if any(re.search(p, text) for p in hint_patterns):
        return "hint_request"

    # Obvious solution-seeking patterns
    solution_patterns = [
        r"\bgive me the answer\b",
        r"\bwhat is the answer\b",
        r"\bcomplete solution\b",
        r"\bfull solution\b",
        r"\bsolve this for me\b",
        r"\bwrite the code\b",
        r"\bdo my homework\b",
        r"\bproject code\b",
        r"\bsubmit this\b",
    ]
    if any(re.search(p, text) for p in solution_patterns):
        return "solution_seeking"

    # Requests that look like they're asking to implement/finish assignments
    if "assignment" in text or "homework" in text or "project" in text:
        if "explain" in text or "understand" in text or "concept" in text:
            return "concept_question"
        return "solution_seeking"

    # Default assumption: concept question
    return "concept_question"


def build_solution_guardrail_instructions() -> str:
    """
    System-level instructions to enforce 'no full solutions' behavior
    when interacting with the LLM.
    """
    return (
        "You are a Spotlight Academy learning assistant. "
        "You must NEVER provide full assignment or project solutions or complete code that directly solves tasks. "
        "You are allowed to explain concepts, break down problems, and give high-level hints. "
        "Always encourage the student to think and attempt the solution themselves. "
        "If the question is asking for a direct solution, respond with structured guidance only."
    )


def build_solution_seeking_response() -> str:
    """
    Predefined response for blocked solution-seeking requests.
    """
    return (
        "It looks like you're asking for a full solution or direct answer to an assignment or project.\n\n"
        "I can't provide completed solutions, but I can definitely help you learn how to solve it:\n"
        "1. First, restate the problem in your own words.\n"
        "2. Identify the key concepts from the course materials that apply here.\n"
        "3. Break the task into 2–4 smaller steps you could implement.\n\n"
        "If you share where you're stuck (e.g., understanding a concept or a specific step), "
        "I can explain that part and give you a hint to move forward."
    )


