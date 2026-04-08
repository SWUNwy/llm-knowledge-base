"""Tests for the video parser."""

import pytest

from src.parsers.video import VideoParser


@pytest.fixture
def parser() -> VideoParser:
    """Create a VideoParser instance."""
    return VideoParser()


class TestYouTubeUrlDetection:
    """Tests for YouTube URL detection."""

    def test_standard_youtube_url(self, parser: VideoParser) -> None:
        assert parser._is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_short_youtube_url(self, parser: VideoParser) -> None:
        assert parser._is_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_youtube_shorts(self, parser: VideoParser) -> None:
        assert parser._is_youtube_url("https://www.youtube.com/shorts/abc123")

    def test_non_youtube_url(self, parser: VideoParser) -> None:
        assert not parser._is_youtube_url("https://example.com/video")


class TestBilibiliUrlDetection:
    """Tests for Bilibili URL detection."""

    def test_bilibili_url(self, parser: VideoParser) -> None:
        assert parser._is_bilibili_url("https://www.bilibili.com/video/BV1xx411c7mD")

    def test_non_bilibili_url(self, parser: VideoParser) -> None:
        assert not parser._is_bilibili_url("https://youtube.com/watch?v=abc")


class TestExtractYouTubeId:
    """Tests for YouTube video ID extraction."""

    def test_standard_url(self, parser: VideoParser) -> None:
        video_id = parser._extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_short_url(self, parser: VideoParser) -> None:
        video_id = parser._extract_youtube_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_url_with_params(self, parser: VideoParser) -> None:
        video_id = parser._extract_youtube_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42"
        )
        assert video_id == "dQw4w9WgXcQ"

    def test_shorts_url(self, parser: VideoParser) -> None:
        video_id = parser._extract_youtube_id("https://www.youtube.com/shorts/abc123")
        assert video_id == "abc123"

    def test_invalid_url(self, parser: VideoParser) -> None:
        assert parser._extract_youtube_id("https://example.com") is None


class TestExtractBilibiliBv:
    """Tests for Bilibili BV ID extraction."""

    def test_standard_url(self, parser: VideoParser) -> None:
        bv = parser._extract_bilibili_bv("https://www.bilibili.com/video/BV1xx411c7mD")
        assert bv == "BV1xx411c7mD"

    def test_url_with_params(self, parser: VideoParser) -> None:
        bv = parser._extract_bilibili_bv(
            "https://www.bilibili.com/video/BV1xx411c7mD?p=1"
        )
        assert bv == "BV1xx411c7mD"

    def test_invalid_url(self, parser: VideoParser) -> None:
        assert parser._extract_bilibili_bv("https://example.com") is None


class TestFormatTranscript:
    """Tests for transcript formatting."""

    def test_basic_formatting(self, parser: VideoParser) -> None:
        transcript = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.0, "duration": 2.0},
        ]
        result = parser._format_transcript(transcript)
        assert "Hello world" in result
        assert "This is a test" in result

    def test_removes_bracketed_text(self, parser: VideoParser) -> None:
        transcript = [
            {"text": "Hello [Music] world", "start": 0.0, "duration": 2.0},
        ]
        result = parser._format_transcript(transcript)
        assert "[Music]" not in result
        assert "Hello" in result
        assert "world" in result

    def test_removes_parenthetical_text(self, parser: VideoParser) -> None:
        transcript = [
            {"text": "Hello (laughs) world", "start": 0.0, "duration": 2.0},
        ]
        result = parser._format_transcript(transcript)
        assert "(laughs)" not in result

    def test_empty_transcript(self, parser: VideoParser) -> None:
        result = parser._format_transcript([])
        assert result == ""


class TestParseUnsupportedUrl:
    """Tests for unsupported URL handling."""

    @pytest.mark.asyncio
    async def test_unsupported_platform(self, parser: VideoParser) -> None:
        result = await parser.parse_url("https://vimeo.com/12345")
        assert not result.success
        assert "Unsupported" in result.error
