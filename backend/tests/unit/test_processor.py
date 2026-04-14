"""Tests for DocumentProcessor."""

import pytest

from src.services.processor import DocumentChunk, DocumentProcessor


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_chunk_fields(self) -> None:
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
        return DocumentProcessor(chunk_token_limit=100)

    def test_small_document_no_chunking(self) -> None:
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "# Short Doc\n\nSome content here."
        chunks = proc.process(content, source_format="pdf", title="Short Doc")

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].total == 1
        assert chunks[0].index == 0
        assert chunks[0].source_format == "pdf"

    def test_splits_by_h1(self, processor: DocumentProcessor) -> None:
        section_a = "# Chapter A\n\n" + "Word " * 200
        section_b = "# Chapter B\n\n" + "Word " * 200
        content = section_a + "\n\n" + section_b

        chunks = processor.process(content, source_format="pdf", title="Big Doc")

        assert len(chunks) == 2
        assert "# Chapter A" in chunks[0].content
        assert "# Chapter B" in chunks[1].content
        assert all(c.source_format == "pdf" for c in chunks)
        assert all(c.total == 2 for c in chunks)

    def test_splits_by_h2_when_h1_too_large(self, processor: DocumentProcessor) -> None:
        big_section = "# Big Chapter\n\n## Part A\n\n" + "Word " * 200 + "\n\n## Part B\n\n" + "Word " * 200
        content = big_section

        chunks = processor.process(content, source_format="docx", title="Big")

        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_section_path_carries_title(self) -> None:
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "# My Doc\n\nContent."
        chunks = proc.process(content, source_format="html", title="My Doc")

        assert chunks[0].section_path == ["My Doc"]

    def test_section_path_includes_heading(self, processor: DocumentProcessor) -> None:
        section_a = "# Alpha\n\n" + "Word " * 200
        section_b = "# Beta\n\n" + "Word " * 200
        content = section_a + "\n\n" + section_b

        chunks = processor.process(content, source_format="pdf", title="Doc")

        assert "Alpha" in chunks[0].section_path[-1] or "Alpha" in chunks[0].content
        assert "Beta" in chunks[1].section_path[-1] or "Beta" in chunks[1].content

    def test_token_estimation(self, processor: DocumentProcessor) -> None:
        tokens = processor._estimate_tokens("Hello world, this is a test.")
        assert tokens > 0
        assert tokens < 100

    def test_empty_content(self, processor: DocumentProcessor) -> None:
        chunks = processor.process("", source_format="pdf")

        assert chunks == []

    def test_pptx_splits_by_slide(self, processor: DocumentProcessor) -> None:
        slides = "Slide 1 content\n\n---\n\n" + "Word " * 200 + "\n\n---\n\nSlide 3 content"
        chunks = processor.process(slides, source_format="pptx", title="Deck")

        assert len(chunks) >= 2

    def test_no_headings_returns_single_chunk(self) -> None:
        proc = DocumentProcessor(chunk_token_limit=6000)
        content = "Just some plain text without any headings."
        chunks = proc.process(content, source_format="csv")

        assert len(chunks) == 1
        assert chunks[0].content == content

    def test_chunk_indices_are_sequential(self, processor: DocumentProcessor) -> None:
        sections = []
        for i in range(5):
            sections.append(f"# Section {i}\n\n" + "Word " * 200)
        content = "\n\n".join(sections)

        chunks = processor.process(content, source_format="pdf", title="Multi")

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
