from __future__ import annotations
"""Document post-processing pipeline.

Handles smart chunking of Markdown content by heading hierarchy,
token estimation, and format-specific adaptation.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of a document after processing."""

    content: str
    index: int
    total: int
    section_path: list[str]
    source_format: str
    token_count: int


class DocumentProcessor:
    """Post-processing pipeline for parsed documents.

    Splits large Markdown documents into chunks suitable for LLM processing,
    using heading hierarchy for natural break points.
    """

    def __init__(self, chunk_token_limit: int = 6000) -> None:
        self.chunk_token_limit = chunk_token_limit

    def process(
        self,
        content: str,
        source_format: str,
        title: str = "",
    ) -> list[DocumentChunk]:
        content = content.strip()
        if not content:
            return []

        if source_format == "pptx":
            return self._split_pptx(content, source_format, title)

        token_count = self._estimate_tokens(content)
        if token_count <= self.chunk_token_limit:
            return [DocumentChunk(
                content=content,
                index=0,
                total=1,
                section_path=[title] if title else [],
                source_format=source_format,
                token_count=token_count,
            )]

        return self._split_by_headings(content, source_format, title)

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _split_by_headings(
        self,
        content: str,
        source_format: str,
        title: str,
    ) -> list[DocumentChunk]:
        sections = re.split(r"(?=^# [^#])", content, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]

        chunks: list[DocumentChunk] = []
        for section in sections:
            token_count = self._estimate_tokens(section)
            if token_count <= self.chunk_token_limit:
                heading = self._extract_heading(section)
                chunks.append(DocumentChunk(
                    content=section,
                    index=0,
                    total=0,
                    section_path=[title, heading] if title else [heading],
                    source_format=source_format,
                    token_count=token_count,
                ))
            else:
                sub_chunks = self._split_by_h2(section, source_format, title)
                chunks.extend(sub_chunks)

        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.index = i
            chunk.total = total

        return chunks

    def _split_by_h2(
        self,
        section: str,
        source_format: str,
        title: str,
    ) -> list[DocumentChunk]:
        parts = re.split(r"(?=^## [^#])", section, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]

        chunks: list[DocumentChunk] = []
        for part in parts:
            heading = self._extract_heading(part)
            chunks.append(DocumentChunk(
                content=part,
                index=0,
                total=0,
                section_path=[title, heading] if title else [heading],
                source_format=source_format,
                token_count=self._estimate_tokens(part),
            ))

        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.index = i
            chunk.total = total

        return chunks

    def _split_pptx(
        self,
        content: str,
        source_format: str,
        title: str,
    ) -> list[DocumentChunk]:
        slides = re.split(r"\n---\n", content)
        slides = [s.strip() for s in slides if s.strip()]

        if not slides:
            return []

        total = len(slides)
        chunks: list[DocumentChunk] = []
        for i, slide in enumerate(slides):
            chunks.append(DocumentChunk(
                content=slide,
                index=i,
                total=total,
                section_path=[title, f"Slide {i + 1}"] if title else [f"Slide {i + 1}"],
                source_format=source_format,
                token_count=self._estimate_tokens(slide),
            ))

        return chunks

    def _extract_heading(self, markdown: str) -> str:
        match = re.match(r"^#{1,3}\s+(.+)$", markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"
