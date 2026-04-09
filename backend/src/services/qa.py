from __future__ import annotations
"""QA service for answering questions using retrieved documents."""

import logging
import re
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from src.llm.client import LLMClient
from src.llm.prompts import PromptTemplates
from src.repositories.document_repo import DocumentRepo

logger = logging.getLogger(__name__)


@dataclass
class QAResult:
    """Result of a question-answering operation.

    Attributes:
        answer: The generated answer text.
        sources: List of source documents used to generate the answer.
        related_concepts: List of related concepts mentioned in the answer.
    """

    answer: str
    sources: list[dict] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "related_concepts": self.related_concepts,
        }


class QAService:
    """Service for answering questions using retrieved documents.

    Searches for relevant documents, builds a prompt with context,
    and uses an LLM to generate comprehensive answers.
    """

    def __init__(
        self,
        doc_repo: DocumentRepo,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        """Initialize the QA service.

        Args:
            doc_repo: Document repository for searching documents.
            llm_client: LLM client for generating answers. Creates a new
                instance if not provided.
        """
        self.doc_repo = doc_repo
        self.llm_client = llm_client or LLMClient()

    async def ask(
        self,
        question: str,
        top_k: int = 5,
        output_language: str = "中文",
    ) -> QAResult:
        """Answer a question using relevant documents.

        Searches for relevant documents, builds a prompt with context,
        and generates an answer using the LLM.

        Args:
            question: The user's question.
            top_k: Maximum number of documents to retrieve.
            output_language: Language for the generated answer.

        Returns:
            QAResult containing the answer, sources, and related concepts.
        """
        # 1. Search for relevant documents
        search_results = await self.doc_repo.search_documents(
            query=question,
            limit=top_k,
        )

        # 2. Build sources text for prompt
        sources_text = self._build_sources_text(search_results)

        # 3. Extract source IDs and titles for prompt
        source_ids = [doc["id"] for doc in search_results]
        titles = [doc.get("title", "Untitled") for doc in search_results]

        # 4. Build QA prompt using PromptTemplates
        prompt = PromptTemplates.qa_answer(
            question=question,
            sources=sources_text,
            source_ids=source_ids,
            titles=titles,
        )

        # 5. Call LLM to generate answer
        try:
            answer = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000,
            )
        except Exception as e:
            logger.error(f"LLM generation failed for question: {e}")
            raise

        # 6. Extract related concepts from answer
        related_concepts = self._extract_wiki_links(answer)

        # 7. Build source info for response
        sources = [
            {
                "id": doc["id"],
                "title": doc.get("title", "Untitled"),
                "relevance": abs(doc.get("rank", 0)),
            }
            for doc in search_results
        ]

        logger.info(f"Generated answer for question with {len(sources)} sources")

        return QAResult(
            answer=answer,
            sources=sources,
            related_concepts=related_concepts,
        )

    async def stream_ask(
        self,
        question: str,
        top_k: int = 5,
        output_language: str = "中文",
    ) -> AsyncGenerator[str, None]:
        """Stream answer generation for a question.

        Searches for relevant documents and streams the LLM response
        token by token.

        Args:
            question: The user's question.
            top_k: Maximum number of documents to retrieve.
            output_language: Language for the generated answer.

        Yields:
            Text chunks from the LLM response.
        """
        # 1. Search for relevant documents
        search_results = await self.doc_repo.search_documents(
            query=question,
            limit=top_k,
        )

        # 2. Build sources text for prompt
        sources_text = self._build_sources_text(search_results)

        # 3. Extract source IDs and titles for prompt
        source_ids = [doc["id"] for doc in search_results]
        titles = [doc.get("title", "Untitled") for doc in search_results]

        # 4. Build QA prompt using PromptTemplates
        prompt = PromptTemplates.qa_answer(
            question=question,
            sources=sources_text,
            source_ids=source_ids,
            titles=titles,
        )

        # 5. Stream LLM response
        try:
            async for chunk in self.llm_client.stream(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"LLM streaming failed for question: {e}")
            raise

    def _build_sources_text(self, documents: list[dict]) -> str:
        """Build formatted text from source documents.

        Args:
            documents: List of document dictionaries.

        Returns:
            Formatted text string with document contents.
        """
        if not documents:
            return "No relevant documents found."

        parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled")
            doc_id = doc["id"]
            # Get content from document or indicate not available
            content = doc.get("content", "Content not available in search results.")
            parts.append(
                f"### Document {i}: {title} (ID: {doc_id})\n\n{content}\n"
            )

        return "\n".join(parts)

    def _extract_wiki_links(self, text: str) -> list[str]:
        """Extract wiki-link concepts from text.

        Finds all [[concept]] style links in the text.

        Args:
            text: Text containing wiki-links.

        Returns:
            List of unique concept names.
        """
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, text)
        # Return unique concepts preserving order
        seen = set()
        concepts = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                concepts.append(match)
        return concepts
