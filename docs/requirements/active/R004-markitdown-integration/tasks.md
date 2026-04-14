# R004 MarkItDown 集成实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PDFParser and WebParser with MarkItDown as the unified file parsing engine, add smart chunking via DocumentProcessor, and add format-specific prompt templates.

**Architecture:** MarkItDownParser wraps the markitdown library (sync→async via asyncio.to_thread). DocumentProcessor splits large Markdown outputs by headings into chunks with token estimation. PromptTemplates gains format-specific compile templates routed by source_format. IngestService routes to the correct pipeline (document/video/code).

**Tech Stack:** Python 3.11+, FastAPI, markitdown[all]>=0.1.0, asyncio, pytest

**Spec:** `docs/requirements/active/R004-markitdown-integration/design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `backend/src/parsers/markitdown.py` | MarkItDown wrapper (sync→async, ParseResult output) |
| Create | `backend/src/services/processor.py` | DocumentProcessor: smart chunking, token estimation, format adaptation |
| Create | `backend/tests/unit/test_markitdown_parser.py` | Tests for MarkItDownParser |
| Create | `backend/tests/unit/test_processor.py` | Tests for DocumentProcessor |
| Modify | `backend/src/config.py` | Add markitdown + chunk config fields |
| Modify | `backend/src/parsers/__init__.py` | Swap exports (remove PDFParser/WebParser, add MarkItDownParser) |
| Modify | `backend/src/llm/prompts.py` | Add 3 format-specific templates + compile_for_format router |
| Modify | `backend/src/services/ingest.py` | Replace parsers, add processor, update routing |
| Modify | `backend/requirements.txt` | Add markitdown[all], remove PyMuPDF and readability-lxml |
| Delete | `backend/src/parsers/pdf.py` | Replaced by markitdown |
| Delete | `backend/src/parsers/web.py` | Replaced by markitdown |
| Delete | `backend/tests/unit/test_pdf_parser.py` | Replaced by test_markitdown_parser.py |
| Delete | `backend/tests/unit/test_web_parser.py` | Replaced by test_markitdown_parser.py |

---

### Task 1: Update dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Replace the old parser dependencies with markitdown. Open `backend/requirements.txt` and change lines 13-14 from:

```
# 解析器
beautifulsoup4>=4.12.0
readability-lxml>=0.8.1
httpx>=0.26.0
PyMuPDF>=1.23.0
youtube-transcript-api>=0.6.0
GitPython>=3.1.0
```

to:

```
# 解析器
markitdown[all]>=0.1.0
beautifulsoup4>=4.12.0
httpx>=0.26.0
youtube-transcript-api>=0.6.0
GitPython>=3.1.0
```

We keep beautifulsoup4 (used by markitdown internally and possibly elsewhere), httpx (used by VideoParser), youtube-transcript-api, and GitPython. We remove readability-lxml and PyMuPDF (both replaced by markitdown).

- [ ] **Step 2: Install the new dependency**

Run: `cd backend && source venv/bin/activate && pip install 'markitdown[all]>=0.1.0'`

Expected: Successfully installed markitdown and its dependencies (pdfminer.six, pdfplumber, mammoth, python-pptx, openpyxl, etc.)

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(r004): add markitdown dependency, remove PyMuPDF and readability-lxml"
```

---

### Task 2: Add config fields

**Files:**
- Modify: `backend/src/config.py:33-38`

- [ ] **Step 1: Add new config fields to Settings class**

Open `backend/src/config.py`. After line 38 (`max_concurrent_tasks: int = 3`), add these two fields before the `# 日志配置` section:

```python
    # MarkItDown 配置
    markitdown_llm_image_description: bool = True
    chunk_token_limit: int = 6000
```

The section should now read:

```python
    # 并发配置
    max_concurrent_tasks: int = 3

    # MarkItDown 配置
    markitdown_llm_image_description: bool = True
    chunk_token_limit: int = 6000

    # 日志配置
    log_level: str = "INFO"
```

- [ ] **Step 2: Verify config loads**

Run: `cd backend && source venv/bin/activate && python -c "from src.config import Settings; s = Settings(vault_path='/tmp/test'); print(s.markitdown_llm_image_description, s.chunk_token_limit)"`

Expected: `True 6000`

- [ ] **Step 3: Commit**

```bash
git add backend/src/config.py
git commit -m "feat(r004): add markitdown and chunk config fields"
```

---

### Task 3: Create MarkItDownParser

**Files:**
- Create: `backend/src/parsers/markitdown.py`
- Create: `backend/tests/unit/test_markitdown_parser.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_markitdown_parser.py`:

```python
"""Tests for MarkItDownParser."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsers.base import ParseResult
from src.parsers.markitdown import MarkItDownParser


class TestMarkItDownParser:
    """Tests for MarkItDownParser class."""

    @pytest.fixture
    def parser(self) -> MarkItDownParser:
        """Create a MarkItDownParser instance without LLM client."""
        return MarkItDownParser()

    def test_supported_extensions(self, parser: MarkItDownParser) -> None:
        """Verify SUPPORTED_EXTENSIONS contains expected formats."""
        assert ".pdf" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".docx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".pptx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".xlsx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".html" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".epub" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".csv" in MarkItDownParser.SUPPORTED_EXTENSIONS

    async def test_parse_file_not_found(self, parser: MarkItDownParser) -> None:
        """Test handling of missing file."""
        result = await parser.parse_file(Path("/non/existent/file.pdf"))

        assert isinstance(result, ParseResult)
        assert result.success is False
        assert result.error is not None

    async def test_parse_file_returns_markdown(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        """Test that parse_file returns Markdown content, not plain text."""
        # Create a simple CSV file (no special deps needed)
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Name,Age\nAlice,30\nBob,25\n")

        result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.content  # non-empty
        # MarkItDown produces markdown tables from CSV
        assert "|" in result.content  # markdown table syntax
        assert result.metadata.get("source_format") == "csv"

    async def test_parse_file_sets_source_format(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        """Test that source_format is set from file extension."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("Col1,Col2\nA,B\n")

        result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.metadata["source_format"] == "csv"

    async def test_parse_file_unsupported_format(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        """Test handling of unsupported file format."""
        xyz_file = tmp_path / "test.xyz"
        xyz_file.write_text("some content")

        result = await parser.parse_file(xyz_file)

        assert result.success is False
        assert "unsupported" in result.error.lower()

    async def test_parse_url_returns_markdown(self, parser: MarkItDownParser) -> None:
        """Test that parse_url returns Markdown from a URL."""
        mock_result = MagicMock()
        mock_result.title = "Test Page"
        mock_result.markdown = "# Test Page\n\nSome content"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            result = await parser.parse_url("https://example.com/page.html")

        assert result.success is True
        assert result.title == "Test Page"
        assert result.content == "# Test Page\n\nSome content"
        assert result.metadata["source_format"] == "html"
        assert result.metadata["source_url"] == "https://example.com/page.html"

    async def test_parse_url_failure(self, parser: MarkItDownParser) -> None:
        """Test handling of URL conversion failure."""
        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.side_effect = Exception("Network error")

            result = await parser.parse_url("https://example.com/nonexistent")

        assert result.success is False
        assert result.error is not None

    async def test_parse_file_with_mock(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        """Test parse_file with mocked markitdown for a PDF."""
        mock_result = MagicMock()
        mock_result.title = "Mock PDF Title"
        mock_result.markdown = "# Mock PDF\n\nContent with **bold** and a table:\n\n| A | B |\n|---|---|\n| 1 | 2 |"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 dummy")

            result = await parser.parse_file(pdf_file)

        assert result.success is True
        assert result.title == "Mock PDF Title"
        assert "| A | B |" in result.content
        assert result.metadata["source_format"] == "pdf"

    async def test_parse_file_no_title(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        """Test that empty title defaults to empty string."""
        mock_result = MagicMock()
        mock_result.title = None
        mock_result.markdown = "Just content"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            csv_file = tmp_path / "test.csv"
            csv_file.write_text("A\n1\n")

            result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.title == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_markitdown_parser.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'src.parsers.markitdown'`

- [ ] **Step 3: Write MarkItDownParser implementation**

Create `backend/src/parsers/markitdown.py`:

```python
from __future__ import annotations
"""Unified file parser using Microsoft MarkItDown library."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from src.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class MarkItDownParser(BaseParser):
    """Unified parser for multiple file formats via MarkItDown.

    Converts PDF, DOCX, PPTX, XLSX, HTML, EPUB, CSV, images, and more
    to structured Markdown. Replaces the previous PDFParser and WebParser.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
        ".html", ".htm", ".epub", ".csv",
        ".jpg", ".jpeg", ".png", ".ipynb", ".zip",
    }

    def __init__(
        self,
        llm_client: Optional[object] = None,
        llm_model: Optional[str] = None,
    ) -> None:
        """Initialize the parser.

        Args:
            llm_client: Optional OpenAI-compatible client for image descriptions.
            llm_model: Model name for image descriptions (e.g. "gpt-4o").
        """
        from markitdown import MarkItDown

        kwargs = {}
        if llm_client is not None:
            kwargs["llm_client"] = llm_client
        if llm_model is not None:
            kwargs["llm_model"] = llm_model

        self._md = MarkItDown(**kwargs)

    async def parse_file(self, path: Path) -> ParseResult:
        """Parse a local file to Markdown.

        Args:
            path: Path to the file.

        Returns:
            ParseResult with Markdown content and source_format metadata.
        """
        if not path.exists():
            return ParseResult(
                success=False,
                error=f"File not found: {path}",
            )

        if not path.is_file():
            return ParseResult(
                success=False,
                error=f"Path is not a file: {path}",
            )

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            return ParseResult(
                success=False,
                error=f"Unsupported file format: {suffix}. Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}",
            )

        try:
            result = await asyncio.to_thread(self._md.convert, str(path))
            return ParseResult(
                success=True,
                title=result.title or "",
                content=result.markdown,
                metadata={
                    "source_format": suffix.lstrip("."),
                },
            )
        except Exception as e:
            logger.error("MarkItDown failed to parse %s: %s", path, e)
            return ParseResult(
                success=False,
                error=f"Failed to parse {path}: {str(e)}",
            )

    async def parse_url(self, url: str) -> ParseResult:
        """Parse a URL to Markdown.

        Args:
            url: The URL to fetch and convert.

        Returns:
            ParseResult with Markdown content.
        """
        try:
            result = await asyncio.to_thread(self._md.convert, url)
            return ParseResult(
                success=True,
                title=result.title or "",
                content=result.markdown,
                metadata={
                    "source_format": "html",
                    "source_url": url,
                },
            )
        except Exception as e:
            logger.error("MarkItDown failed to parse URL %s: %s", url, e)
            return ParseResult(
                success=False,
                error=f"Failed to parse URL: {str(e)}",
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_markitdown_parser.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/parsers/markitdown.py backend/tests/unit/test_markitdown_parser.py
git commit -m "feat(r004): add MarkItDownParser with tests"
```

---

### Task 4: Create DocumentProcessor

**Files:**
- Create: `backend/src/services/processor.py`
- Create: `backend/tests/unit/test_processor.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_processor.py`:

```python
"""Tests for DocumentProcessor."""

import pytest

from src.services.processor import DocumentChunk, DocumentProcessor


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_chunk_fields(self) -> None:
        """Verify chunk has expected fields."""
        chunk = DocumentChunk(
            content="# Hello",
            index=0,
            total=1,
            section_path=["Title"],
            source_format="pdf",
            token_count=100,
        )
        assert chunk.content == "# Hello"
        assert chunk.index == 0
        assert chunk.total == 1
        assert chunk.section_path == ["Title"]
        assert chunk.source_format == "pdf"
        assert chunk.token_count == 100


class TestDocumentProcessor:
    """Tests for DocumentProcessor."""

    @pytest.fixture
    def processor(self) -> DocumentProcessor:
        """Create a processor with low token limit for testing."""
        return DocumentProcessor(chunk_token_limit=100)

    def test_small_document_no_chunking(self) -> None:
        """Documents under the token limit are not split."""
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "# Short Doc\n\nSome content here."
        chunks = proc.process(content, source_format="pdf", title="Short Doc")

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].total == 1
        assert chunks[0].index == 0
        assert chunks[0].source_format == "pdf"

    def test_splits_by_h1(self, processor: DocumentProcessor) -> None:
        """Large documents are split at # headings."""
        # Each line is ~40 chars = ~10 tokens. We need > 100 tokens total.
        section_a = "# Chapter A\n\n" + "Word " * 200  # ~1000 chars = ~250 tokens
        section_b = "# Chapter B\n\n" + "Word " * 200
        content = section_a + "\n\n" + section_b

        chunks = processor.process(content, source_format="pdf", title="Big Doc")

        assert len(chunks) == 2
        assert "# Chapter A" in chunks[0].content
        assert "# Chapter B" in chunks[1].content
        assert all(c.source_format == "pdf" for c in chunks)
        assert all(c.total == 2 for c in chunks)

    def test_splits_by_h2_when_h1_too_large(self, processor: DocumentProcessor) -> None:
        """If a single # section exceeds limit, split by ## instead."""
        big_section = "# Big Chapter\n\n## Part A\n\n" + "Word " * 200 + "\n\n## Part B\n\n" + "Word " * 200
        content = big_section

        chunks = processor.process(content, source_format="docx", title="Big")

        assert len(chunks) >= 2
        # Each chunk should contain a heading
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_section_path_carries_title(self) -> None:
        """Each chunk's section_path includes the document title."""
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "# My Doc\n\nContent."
        chunks = proc.process(content, source_format="html", title="My Doc")

        assert chunks[0].section_path == ["My Doc"]

    def test_section_path_includes_heading(self, processor: DocumentProcessor) -> None:
        """Chunks from headings include heading names in section_path."""
        section_a = "# Alpha\n\n" + "Word " * 200
        section_b = "# Beta\n\n" + "Word " * 200
        content = section_a + "\n\n" + section_b

        chunks = processor.process(content, source_format="pdf", title="Doc")

        # Section path should include doc title + heading
        assert "Alpha" in chunks[0].section_path[-1] or "Alpha" in chunks[0].content
        assert "Beta" in chunks[1].section_path[-1] or "Beta" in chunks[1].content

    def test_token_estimation(self, processor: DocumentProcessor) -> None:
        """Token estimation is reasonable (len/4 heuristic)."""
        tokens = processor._estimate_tokens("Hello world, this is a test.")
        # 30 chars / 4 = 7.5 → 8
        assert tokens > 0
        assert tokens < 100

    def test_empty_content(self, processor: DocumentProcessor) -> None:
        """Empty content returns empty list."""
        chunks = processor.process("", source_format="pdf")

        assert chunks == []

    def test_pptx_splits_by_slide(self, processor: DocumentProcessor) -> None:
        """PPTX format splits on --- horizontal rules (slide separators)."""
        slides = "Slide 1 content\n\n---\n\n" + "Word " * 200 + "\n\n---\n\nSlide 3 content"
        chunks = processor.process(slides, source_format="pptx", title="Deck")

        assert len(chunks) >= 2

    def test_no_headings_returns_single_chunk(self) -> None:
        """Content without headings but under limit returns single chunk."""
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "Just some plain text without any headings."
        chunks = proc.process(content, source_format="csv")

        assert len(chunks) == 1
        assert chunks[0].content == content

    def test_chunk_indices_are_sequential(self, processor: DocumentProcessor) -> None:
        """Chunks have sequential index values starting at 0."""
        sections = []
        for i in range(5):
            sections.append(f"# Section {i}\n\n" + "Word " * 200)
        content = "\n\n".join(sections)

        chunks = processor.process(content, source_format="pdf", title="Multi")

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_processor.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'src.services.processor'`

- [ ] **Step 3: Write DocumentProcessor implementation**

Create `backend/src/services/processor.py`:

```python
from __future__ import annotations
"""Document post-processing pipeline.

Handles smart chunking of Markdown content by heading hierarchy,
token estimation, and format-specific adaptation.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of a document after processing.

    Attributes:
        content: Markdown content of this chunk.
        index: Zero-based chunk index.
        total: Total number of chunks.
        section_path: Path from doc title to this section (e.g. ["Title", "Chapter 2"]).
        source_format: Original file format (e.g. "pdf", "docx").
        token_count: Estimated token count for this chunk.
    """

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
        """Initialize the processor.

        Args:
            chunk_token_limit: Maximum estimated tokens per chunk.
        """
        self.chunk_token_limit = chunk_token_limit

    def process(
        self,
        content: str,
        source_format: str,
        title: str = "",
    ) -> list[DocumentChunk]:
        """Process Markdown content into chunks.

        Args:
            content: Markdown content from MarkItDown.
            source_format: Original file format extension (e.g. "pdf").
            title: Document title for context.

        Returns:
            List of DocumentChunk instances.
        """
        content = content.strip()
        if not content:
            return []

        # PPTX: split by horizontal rules (slide separators)
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
        """Estimate token count using len/4 heuristic.

        Works reasonably for mixed Chinese/English text.

        Args:
            text: Text to estimate tokens for.

        Returns:
            Estimated token count.
        """
        return max(1, len(text) // 4)

    def _split_by_headings(
        self,
        content: str,
        source_format: str,
        title: str,
    ) -> list[DocumentChunk]:
        """Split content by Markdown heading hierarchy.

        First tries splitting by # (H1), then recursively by ## (H2)
        if a section still exceeds the token limit.

        Args:
            content: Markdown content.
            source_format: Original format.
            title: Document title.

        Returns:
            List of chunks split at heading boundaries.
        """
        # Split by H1 headings
        sections = re.split(r"(?=^# [^#])", content, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]

        chunks: list[DocumentChunk] = []
        for section in sections:
            token_count = self._estimate_tokens(section)
            if token_count <= self.chunk_token_limit:
                heading = self._extract_heading(section)
                chunks.append(DocumentChunk(
                    content=section,
                    index=0,  # Will be fixed below
                    total=0,
                    section_path=[title, heading] if title else [heading],
                    source_format=source_format,
                    token_count=token_count,
                ))
            else:
                # Recursively split by H2
                sub_chunks = self._split_by_h2(section, source_format, title)
                chunks.extend(sub_chunks)

        # Fix index and total
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
        """Split a section by ## (H2) headings.

        Args:
            section: Markdown section content.
            source_format: Original format.
            title: Document title.

        Returns:
            List of sub-chunks.
        """
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
        """Split PPTX content by horizontal rules (slide separators).

        Args:
            content: Markdown content with --- separators.
            source_format: "pptx".
            title: Document title.

        Returns:
            List of chunks, one per slide.
        """
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
        """Extract the first heading text from Markdown content.

        Args:
            markdown: Markdown text.

        Returns:
            Heading text without the # prefix, or "Untitled" if none found.
        """
        match = re.match(r"^#{1,3}\s+(.+)$", markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_processor.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/services/processor.py backend/tests/unit/test_processor.py
git commit -m "feat(r004): add DocumentProcessor with smart chunking"
```

---

### Task 5: Add format-specific prompt templates

**Files:**
- Modify: `backend/src/llm/prompts.py`
- Modify: `backend/tests/unit/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

Add these test classes to the end of `backend/tests/unit/test_prompts.py`:

```python


class TestCompileForFormat:
    """Tests for format-specific prompt routing."""

    def test_table_data_format(self) -> None:
        """xlsx format uses COMPILE_TABLE_DATA template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="xlsx",
            title="Sales Report",
            type="data",
            source="local",
            content="| Product | Revenue |\n|---|---|\n| Widget | $1000 |",
            source_id="doc_1",
            original_title="Q4 Report",
        )
        assert "Sales Report" in prompt
        assert "Widget" in prompt
        assert "data" in prompt.lower() or "table" in prompt.lower() or "accuracy" in prompt.lower()

    def test_presentation_format(self) -> None:
        """pptx format uses COMPILE_PRESENTATION template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="pptx",
            title="Quarterly Review",
            type="presentation",
            source="local",
            content="## Slide 1\n\nKey point",
            source_id="doc_2",
            original_title="Review",
        )
        assert "Quarterly Review" in prompt
        assert "Slide 1" in prompt

    def test_paper_format(self) -> None:
        """pdf format uses COMPILE_PAPER template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="pdf",
            title="Research Paper",
            type="paper",
            source="local",
            content="# Abstract\n\nThis paper presents...",
            source_id="doc_3",
            original_title="Paper",
        )
        assert "Research Paper" in prompt
        assert "Abstract" in prompt

    def test_unknown_format_uses_generic(self) -> None:
        """Unknown format falls back to COMPILE_DOCUMENT."""
        prompt = PromptTemplates.compile_for_format(
            source_format="epub",
            title="A Novel",
            type="book",
            source="local",
            content="Chapter 1 content",
            source_id="doc_4",
            original_title="Novel",
        )
        assert "A Novel" in prompt
        assert "Chapter 1 content" in prompt
        # Should use the generic template (has wiki-link instructions)
        assert "[[" in prompt

    def test_csv_uses_table_template(self) -> None:
        """csv format uses COMPILE_TABLE_DATA template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="csv",
            title="Data Export",
            type="data",
            source="local",
            content="Name,Value\nA,1",
            source_id="doc_5",
            original_title="Export",
        )
        assert "Data Export" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_prompts.py::TestCompileForFormat -v`

Expected: FAIL — `AttributeError: type object 'PromptTemplates' has no attribute 'compile_for_format'`

- [ ] **Step 3: Add format-specific templates and router to PromptTemplates**

Open `backend/src/llm/prompts.py`. After the `QA_ANSWER` template string (line 118), add these three new templates and the format router:

```python

    # 表格数据编译模板
    COMPILE_TABLE_DATA = """You are a data analysis editor. Your task is to compile tabular data into a well-structured wiki page.

## Input Document Information
- **Title**: {title}
- **Type**: {type}
- **Source**: {source}
- **Source ID**: {source_id}
- **Original Title**: {original_title}

## Raw Content (Tabular Data)
{content}

## Instructions
1. Compile this tabular data into a clear, well-structured wiki page in **{output_language}**.
2. **Preserve all numerical data accurately** — do not round, approximate, or omit any values.
3. Keep tables in Markdown table format when they contain structured data.
4. Use `[[concept name]]` for key entities, metrics, or categories that merit a separate page.
5. Add a brief summary of the data at the beginning.
6. Highlight key trends, totals, or notable values.

## Output
Please provide the compiled wiki page in {output_language}:"""

    # 演示文稿编译模板
    COMPILE_PRESENTATION = """You are a presentation editor. Your task is to compile slide content into a coherent, flowing wiki page.

## Input Document Information
- **Title**: {title}
- **Type**: {type}
- **Source**: {source}
- **Source ID**: {source_id}
- **Original Title**: {original_title}

## Raw Slide Content
{content}

## Instructions
1. Compile this presentation content into a coherent wiki page in **{output_language}**.
2. **Add narrative transitions** between slide topics to create a flowing document.
3. Expand bullet points into complete sentences and paragraphs where appropriate.
4. Use proper Markdown formatting (headers, lists, etc.).
5. Use `[[concept name]]` for key terms that merit a separate page.
6. Include a brief summary at the beginning.

## Output
Please provide the compiled wiki page in {output_language}:"""

    # 学术论文编译模板
    COMPILE_PAPER = """You are an academic knowledge editor. Your task is to compile an academic paper into a well-structured wiki page.

## Input Document Information
- **Title**: {title}
- **Type**: {type}
- **Source**: {source}
- **Source ID**: {source_id}
- **Original Title**: {original_title}

## Raw Content
{content}

## Instructions
1. Compile this paper into a structured wiki page in **{output_language}**.
2. Identify and preserve the academic structure: Abstract, Introduction, Methodology, Results, Discussion, Conclusion.
3. Extract key findings and contributions clearly.
4. Use `[[concept name]]` for technical terms, methods, or entities that merit a separate page.
5. Include a brief summary at the beginning.
6. Keep mathematical notation and formulas where present.

## Output
Please provide the compiled wiki page in {output_language}:"""
```

Then add the format mapping and router method after the `qa_answer` method (at the end of the class):

```python

    # 格式到模板的映射
    FORMAT_TEMPLATES: dict[str, str] = {
        "xlsx": "COMPILE_TABLE_DATA",
        "xls": "COMPILE_TABLE_DATA",
        "csv": "COMPILE_TABLE_DATA",
        "pptx": "COMPILE_PRESENTATION",
        "pdf": "COMPILE_PAPER",
    }

    @classmethod
    def compile_for_format(
        cls,
        source_format: str,
        title: str,
        type: str,
        source: str,
        content: str,
        source_id: str,
        original_title: str,
        output_language: str = "中文",
    ) -> str:
        """根据源文件格式选择编译模板

        Args:
            source_format: 源文件格式 (pdf, docx, pptx, xlsx, csv, html, etc.)
            title: 文档标题
            type: 文档类型
            source: 来源URL
            content: 文档内容
            source_id: 源文档ID
            original_title: 原始标题
            output_language: 输出语言

        Returns:
            构建好的Prompt字符串
        """
        template_name = cls.FORMAT_TEMPLATES.get(source_format, "COMPILE_DOCUMENT")
        template = getattr(cls, template_name)
        return template.format(
            title=title,
            type=type,
            source=source,
            content=content,
            source_id=source_id,
            original_title=original_title,
            output_language=output_language,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/test_prompts.py -v`

Expected: All tests PASS (both old and new).

- [ ] **Step 5: Commit**

```bash
git add backend/src/llm/prompts.py backend/tests/unit/test_prompts.py
git commit -m "feat(r004): add format-specific prompt templates and router"
```

---

### Task 6: Update IngestService

**Files:**
- Modify: `backend/src/services/ingest.py`
- Modify: `backend/src/parsers/__init__.py`

- [ ] **Step 1: Update parsers/__init__.py**

Open `backend/src/parsers/__init__.py` and replace the entire content with:

```python
"""Content parsers for extracting data from various sources."""

from src.parsers.base import BaseParser, ParseResult
from src.parsers.github import GitHubParser
from src.parsers.markitdown import MarkItDownParser
from src.parsers.video import VideoParser

__all__ = ["BaseParser", "GitHubParser", "MarkItDownParser", "ParseResult", "VideoParser"]
```

- [ ] **Step 2: Rewrite IngestService**

Open `backend/src/services/ingest.py` and replace the entire content with:

```python
from __future__ import annotations
"""Ingest service for importing documents from URLs and files."""

import uuid
from pathlib import Path
from typing import Optional

from src.config import Settings, get_settings
from src.database import Database
from src.parsers.base import ParseResult
from src.parsers.github import GitHubParser
from src.parsers.markitdown import MarkItDownParser
from src.parsers.video import VideoParser
from src.services.processor import DocumentProcessor


# Maps file extension to doc_type for database categorization
DOC_TYPE_MAP: dict[str, str] = {
    ".pdf": "paper",
    ".docx": "paper",
    ".pptx": "presentation",
    ".xlsx": "data",
    ".xls": "data",
    ".csv": "data",
    ".epub": "book",
    ".html": "web",
    ".htm": "web",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".ipynb": "code",
    ".zip": "archive",
}


class IngestResult:
    """Result of an ingest operation.

    Attributes:
        success: Whether the ingest was successful.
        doc_id: Document ID if successful.
        title: Document title.
        path: Storage path in the vault.
        error: Error message if failed.
    """

    def __init__(
        self,
        success: bool,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Initialize the ingest result."""
        self.success = success
        self.doc_id = doc_id
        self.title = title
        self.path = path
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.doc_id:
            result["doc_id"] = self.doc_id
        if self.title:
            result["title"] = self.title
        if self.path:
            result["path"] = self.path
        if self.error:
            result["error"] = self.error
        return result


class IngestService:
    """Service for importing documents from various sources.

    Routes to the correct pipeline (document/video/code) based on input,
    processes through the DocumentProcessor pipeline, and persists results.
    """

    def __init__(self, db: Database, settings: Optional[Settings] = None) -> None:
        """Initialize the ingest service.

        Args:
            db: Database instance for storing document records.
            settings: Application settings (uses default if not provided).
        """
        self.db = db
        self.settings = settings or get_settings()
        self.vault_path = Path(self.settings.vault_path)
        self.markdown_parser = MarkItDownParser()
        self.video_parser = VideoParser()
        self.github_parser = GitHubParser()
        self.processor = DocumentProcessor(
            chunk_token_limit=self.settings.chunk_token_limit,
        )

    async def ingest_url(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a URL.

        Args:
            url: The URL to import content from.
            tags: Optional list of tags to associate with the document.

        Returns:
            IngestResult with the outcome of the import.
        """
        parse_result = await self.markdown_parser.parse_url(url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/web/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="web",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_file(
        self,
        path: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a local file.

        Args:
            path: Path to the local file to import.
            tags: Optional list of tags to associate with the document.

        Returns:
            IngestResult with the outcome of the import.
        """
        file_path = Path(path)

        if not file_path.exists():
            return IngestResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return IngestResult(success=False, error=f"Path is not a file: {path}")

        suffix = file_path.suffix.lower()
        doc_type = DOC_TYPE_MAP.get(suffix, "web")

        parse_result = await self.markdown_parser.parse_file(file_path)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        type_dir = self._type_to_dir(doc_type)
        storage_path = f"raw/{type_dir}/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type=doc_type,
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_video(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a video URL.

        Args:
            url: The video URL (YouTube or Bilibili).
            tags: Optional list of tags.

        Returns:
            IngestResult with the outcome of the import.
        """
        parse_result = await self.video_parser.parse_url(url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/videos/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="video",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_github(
        self,
        repo_url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a GitHub repository.

        Args:
            repo_url: The GitHub repository URL.
            tags: Optional list of tags.

        Returns:
            IngestResult with the outcome of the import.
        """
        parse_result = await self.github_parser.parse_url(repo_url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/code/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="code",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    def _generate_id(self) -> str:
        """Generate a unique document ID."""
        return str(uuid.uuid4())

    def _type_to_dir(self, doc_type: str) -> str:
        """Map doc_type to vault subdirectory name.

        Args:
            doc_type: Document type string.

        Returns:
            Directory name for the vault.
        """
        mapping = {
            "paper": "papers",
            "presentation": "papers",
            "data": "papers",
            "book": "papers",
            "image": "papers",
            "web": "web",
            "code": "code",
            "archive": "papers",
        }
        return mapping.get(doc_type, "web")

    async def _save_document(
        self,
        storage_path: str,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Save parsed content to the vault."""
        full_path = self.vault_path / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._build_markdown(parse_result, tags)
        full_path.write_text(content, encoding="utf-8")

    def _build_markdown(
        self,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> str:
        """Build markdown content from parse result."""
        lines: list[str] = []

        lines.append("---")
        lines.append(f"title: {parse_result.title or 'Untitled'}")

        if parse_result.metadata.get("source_url"):
            lines.append(f"source: {parse_result.metadata['source_url']}")

        if parse_result.metadata.get("source_format"):
            lines.append(f"format: {parse_result.metadata['source_format']}")

        if tags:
            lines.append(f"tags: [{', '.join(tags)}]")

        if parse_result.metadata.get("author"):
            lines.append(f"author: {parse_result.metadata['author']}")

        lines.append("---")
        lines.append("")
        lines.append(f"# {parse_result.title or 'Untitled'}")
        lines.append("")
        lines.append(parse_result.content)

        return "\n".join(lines)

    async def _create_db_record(
        self,
        doc_id: str,
        doc_type: str,
        path: str,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Create a database record for the document."""
        metadata = dict(parse_result.metadata)
        if tags:
            metadata["tags"] = tags

        await self.db.create_document(
            doc_id=doc_id,
            doc_type=doc_type,
            path=path,
            title=parse_result.title,
            status="pending",
            metadata=metadata,
        )
```

- [ ] **Step 3: Run existing ingest tests**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/integration/test_ingest.py -v`

Expected: Tests may need adjustments if they import PDFParser or WebParser directly. If failures occur, update those test imports to use MarkItDownParser.

- [ ] **Step 4: Run all unit tests**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/unit/ -v --ignore=tests/unit/test_pdf_parser.py --ignore=tests/unit/test_web_parser.py`

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/services/ingest.py backend/src/parsers/__init__.py
git commit -m "feat(r004): update IngestService to use MarkItDownParser and DocumentProcessor"
```

---

### Task 7: Delete old parsers and tests

**Files:**
- Delete: `backend/src/parsers/pdf.py`
- Delete: `backend/src/parsers/web.py`
- Delete: `backend/tests/unit/test_pdf_parser.py`
- Delete: `backend/tests/unit/test_web_parser.py`

- [ ] **Step 1: Delete old parser files**

```bash
rm backend/src/parsers/pdf.py backend/src/parsers/web.py backend/tests/unit/test_pdf_parser.py backend/tests/unit/test_web_parser.py
```

- [ ] **Step 2: Verify no remaining imports of deleted modules**

Run: `cd backend && grep -r "from src.parsers.pdf import\|from src.parsers.web import\|from src.parsers import PDFParser\|from src.parsers import WebParser" src/ tests/`

Expected: No output (no remaining references).

- [ ] **Step 3: Run full test suite**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/ -v --tb=short`

Expected: All PASS. Any failures should be investigated and fixed.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore(r004): remove old PDFParser and WebParser, replaced by MarkItDownParser"
```

---

### Task 8: Verify end-to-end and update changelog

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Quick smoke test with a real file**

Create a test CSV and verify the pipeline works end-to-end:

Run:
```bash
cd backend && source venv/bin/activate && python -c "
import asyncio
from src.parsers.markitdown import MarkItDownParser
from src.services.processor import DocumentProcessor
from pathlib import Path
import tempfile

async def smoke_test():
    # 1. Parse a CSV file
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as f:
        f.write('Name,Age,City\nAlice,30,NYC\nBob,25,LA\n')
        csv_path = f.name

    parser = MarkItDownParser()
    result = await parser.parse_file(Path(csv_path))
    print('=== Parse Result ===')
    print(f'Success: {result.success}')
    print(f'Format: {result.metadata.get(\"source_format\")}')
    print(f'Content:\n{result.content[:200]}')

    # 2. Process through chunker
    processor = DocumentProcessor()
    chunks = processor.process(result.content, source_format='csv', title='Test CSV')
    print(f'\n=== Chunks: {len(chunks)} ===')
    for chunk in chunks:
        print(f'  [{chunk.index}/{chunk.total}] tokens={chunk.token_count}')

asyncio.run(smoke_test())
"
```

Expected: Success output showing CSV parsed to Markdown table, single chunk.

- [ ] **Step 2: Update CHANGELOG.md**

Open `CHANGELOG.md`. Under the `## [Unreleased]` section, under `### Added`, add:

```
- **R004 MarkItDown Integration**: Replace PDFParser and WebParser with unified MarkItDown engine
  - New file format support: DOCX, PPTX, XLSX, EPUB, CSV, images, Jupyter notebooks
  - Output preserves document structure as Markdown (headings, tables, lists)
  - DocumentProcessor: smart chunking by heading hierarchy with token estimation
  - Format-specific LLM compile prompts (tables, presentations, academic papers)
  - Removed PyMuPDF and readability-lxml dependencies
```

- [ ] **Step 3: Final full test run**

Run: `cd backend && source venv/bin/activate && python -m pytest tests/ -v --tb=short`

Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(r004): update CHANGELOG for MarkItDown integration"
```
