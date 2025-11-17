"""Summarization helpers for link/file ingestion."""

from __future__ import annotations

import logging
from typing import Optional

from groq import Groq

from backend.config import settings

logger = logging.getLogger(__name__)


SUMMARIZE_PROMPT = """You are summarizing external web content for a personal knowledge base.
Given the raw text below, create a concise bullet summary (max 6 bullets) highlighting the key info.
If the text is mostly boilerplate or navigation, note that it could not be summarized usefully.

Return plain text with bullet points.

CONTENT:
{content}
"""


class SummarizationError(RuntimeError):
    """Raised when summarization cannot be completed."""


class SummarizationService:
    """Wraps Groq LLM calls for content summarization."""

    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required for summarization.")
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.summary_model or "llama-3.1-8b-instant"

    async def summarize(self, text: str) -> Optional[str]:
        if not text or len(text) < 120:
            return None

        prompt = SUMMARIZE_PROMPT.format(content=text[:8000])
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You summarize content for personal notes."},
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=400,
            )
            summary = completion.choices[0].message.content.strip()
            if not summary:
                return None
            return summary
        except Exception as exc:
            logger.error("Failed to summarize content: %s", exc)
            raise SummarizationError(
                "LLM summarization failed; falling back to original content."
            ) from exc


_summarizer: Optional[SummarizationService] = None


def get_summarization_service() -> Optional[SummarizationService]:
    global _summarizer
    if _summarizer is None:
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY missing; summarization disabled.")
            return None
        _summarizer = SummarizationService()
    return _summarizer

