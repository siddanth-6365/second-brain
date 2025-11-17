"""Utilities for loading content from links and uploaded files."""

from __future__ import annotations

import asyncio
import io
import logging
import os
from typing import Dict, Tuple

import httpx
from bs4 import BeautifulSoup
from fastapi import UploadFile
from PyPDF2 import PdfReader
import docx


logger = logging.getLogger(__name__)


class ContentLoader:
    """Fetches and normalizes content from external sources."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/16.5 Safari/605.1.15"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def fetch_link(self, url: str) -> Tuple[str, Dict[str, str]]:
        """Download a URL and convert HTML to plaintext."""
        if not url:
            raise ValueError("URL is required for link ingestion")

        logger.info("Fetching link content: %s", url)
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.default_headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Failed to fetch URL %s (status=%s): %s", url, status, exc)

            if status in (401, 403):
                warning = "Access denied by the destination site"
            else:
                warning = f"HTTP {status}"

            metadata = {
                "source_url": url,
                "content_type": "link",
                "link_fetch_warning": warning,
            }
            return "", metadata

        fetch_warning = ""
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles to reduce noise
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = (soup.title.string.strip() if soup.title and soup.title.string else None)
        meta_description = ""
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag and description_tag.get("content"):
            meta_description = description_tag["content"].strip()

        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        metadata = {
            "source_url": url,
            "link_title": title or "",
            "link_description": meta_description,
            "content_type": "link",
            "link_fetch_warning": fetch_warning,
        }
        return text, metadata

    async def extract_file(self, upload_file: UploadFile) -> Tuple[str, Dict[str, str]]:
        """Read and normalize content from an uploaded file."""
        if upload_file is None:
            raise ValueError("File upload is required for file ingestion")

        filename = upload_file.filename or "uploaded_file"
        _, ext = os.path.splitext(filename.lower())

        raw_bytes = await upload_file.read()
        if not raw_bytes:
            raise ValueError("Uploaded file is empty")

        text = ""
        if ext == ".pdf":
            text = self._extract_pdf(raw_bytes)
        elif ext in [".docx"]:
            text = self._extract_docx(raw_bytes)
        elif ext in [".txt", ".md"]:
            text = raw_bytes.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file type: {ext or 'unknown'}")

        text = text.strip()
        if not text:
            raise ValueError("Could not extract textual content from the uploaded file")

        metadata = {
            "file_name": filename,
            "content_type": "file",
            "file_extension": ext or "",
        }
        return text, metadata

    def _extract_pdf(self, raw_bytes: bytes) -> str:
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception as exc:
                logger.warning("Failed to extract PDF page text: %s", exc)
        return "\n".join(pages)

    def _extract_docx(self, raw_bytes: bytes) -> str:
        document = docx.Document(io.BytesIO(raw_bytes))
        paragraphs = [para.text for para in document.paragraphs if para.text]
        return "\n".join(paragraphs)


_content_loader: ContentLoader | None = None


def get_content_loader() -> ContentLoader:
    global _content_loader
    if _content_loader is None:
        _content_loader = ContentLoader()
    return _content_loader

