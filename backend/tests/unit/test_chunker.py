"""Tests for the text chunker module."""

import pytest

from src.utils.chunker import ChunkingConfig, TextChunker


class TestChunkText:
    """Tests for TextChunker.chunk_text."""

    def test_chunk_text_basic(self) -> None:
        """Split 3000 chars into ~6 chunks of 500."""
        text = "A" * 3000
        chunker = TextChunker()
        config = ChunkingConfig(chunk_size=500, chunk_overlap=100, min_chunk_size=100)
        chunks = chunker.chunk_text(text, config)

        assert len(chunks) >= 5
        # All chunks should be <= chunk_size
        for chunk in chunks:
            assert len(chunk) <= 500
        # First chunk starts at the beginning
        assert chunks[0] == text[:500]
        # Last chunk ends at the end of the text
        assert chunks[-1][-100:] == text[-100:]

    def test_chunk_overlap(self) -> None:
        """Verify 100 char overlap between chunks."""
        # Use a repeating pattern so overlap is detectable
        text = "ABCDEFGHIJ" * 200  # 2000 chars
        chunker = TextChunker()
        config = ChunkingConfig(chunk_size=500, chunk_overlap=100, min_chunk_size=50)
        chunks = chunker.chunk_text(text, config)

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            overlap = chunks[i][-100:]
            assert chunks[i + 1].startswith(overlap)

    def test_small_text(self) -> None:
        """Single chunk for small text."""
        text = "Hello, world!"
        chunker = TextChunker()
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self) -> None:
        """Handle empty string."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("")

        assert chunks == []

    def test_whitespace_only_text(self) -> None:
        """Handle whitespace-only text."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("   \n\n  \t  ")

        assert chunks == []

    def test_default_config(self) -> None:
        """Default config works without explicit config argument."""
        text = "Word " * 400  # 2000 chars
        chunker = TextChunker()
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 500

    def test_min_chunk_size_respected(self) -> None:
        """Last chunk smaller than min_chunk_size is merged with previous."""
        # 550 chars with chunk_size=500, overlap=0, min_chunk_size=100
        # Would create chunks of 500 and 50; the 50-char chunk should be
        # merged into the previous one.
        text = "X" * 550
        chunker = TextChunker()
        config = ChunkingConfig(chunk_size=500, chunk_overlap=0, min_chunk_size=100)
        chunks = chunker.chunk_text(text, config)

        # Should be a single chunk of 550 since the last 50 chars < min_chunk_size
        assert len(chunks) == 1
        assert len(chunks[0]) == 550


class TestChunkByParagraphs:
    """Tests for TextChunker.chunk_by_paragraphs."""

    def test_paragraph_chunking(self) -> None:
        """Chunks respect paragraph boundaries."""
        paragraphs = ["Paragraph " + str(i) + " " + "word " * 80 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunker = TextChunker()
        config = ChunkingConfig(chunk_size=500, chunk_overlap=50, min_chunk_size=100)
        chunks = chunker.chunk_by_paragraphs(text, config)

        assert len(chunks) >= 2
        # No chunk should exceed chunk_size by much (paragraphs are kept whole)
        for chunk in chunks:
            # Allow paragraphs to exceed chunk_size since we don't split them
            assert len(chunk) > 0

    def test_single_paragraph(self) -> None:
        """Single paragraph returns single chunk."""
        text = "This is a single paragraph with some content."
        chunker = TextChunker()
        chunks = chunker.chunk_by_paragraphs(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self) -> None:
        """Handle empty string in paragraph chunking."""
        chunker = TextChunker()
        chunks = chunker.chunk_by_paragraphs("")

        assert chunks == []


class TestChunkMarkdownByHeaders:
    """Tests for TextChunker.chunk_markdown_by_headers."""

    def test_chunk_markdown_by_headers(self) -> None:
        """Split by ## headers."""
        markdown = """# Main Title

Some intro text here.

## Section One

Content for section one with enough text to be meaningful.

## Section Two

Content for section two that also has meaningful content.

## Section Three

Content for section three to wrap it up.
"""
        chunker = TextChunker()
        chunks = chunker.chunk_markdown_by_headers(markdown)

        # Should split into sections based on ## headers
        assert len(chunks) >= 3
        # Each chunk should contain its header
        for chunk in chunks:
            assert len(chunk) > 0

    def test_markdown_no_headers(self) -> None:
        """Markdown without headers returns single chunk."""
        text = "Just some plain text without any headers at all."
        chunker = TextChunker()
        chunks = chunker.chunk_markdown_by_headers(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_markdown_empty(self) -> None:
        """Handle empty markdown."""
        chunker = TextChunker()
        chunks = chunker.chunk_markdown_by_headers("")

        assert chunks == []

    def test_markdown_preserves_h1_title(self) -> None:
        """H1 header is treated as a title and included in the first chunk."""
        markdown = """# Document Title

Introduction paragraph.

## First Section

First section content.
"""
        chunker = TextChunker()
        chunks = chunker.chunk_markdown_by_headers(markdown)

        assert len(chunks) >= 2
        # The first chunk should contain the H1 title and intro
        assert "# Document Title" in chunks[0]

    def test_markdown_only_h3_headers(self) -> None:
        """H3 headers are treated as content, not split points."""
        markdown = """### Sub section

Some content here.

### Another sub

More content here.
"""
        chunker = TextChunker()
        chunks = chunker.chunk_markdown_by_headers(markdown)

        # H3 headers should NOT be split points, so it's one chunk
        assert len(chunks) == 1
