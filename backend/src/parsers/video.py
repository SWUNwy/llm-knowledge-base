from __future__ import annotations
"""Video parser for extracting subtitles from YouTube and Bilibili."""

import re
from typing import Optional

from src.parsers.base import BaseParser, ParseResult


class VideoParser(BaseParser):
    """Parser for video content.

    Supports extracting subtitles from YouTube and Bilibili videos.
    """

    async def parse_url(self, url: str) -> ParseResult:
        """Parse content from a video URL.

        Args:
            url: The video URL (YouTube or Bilibili).

        Returns:
            ParseResult with the extracted subtitle content.
        """
        if self._is_youtube_url(url):
            return await self._parse_youtube(url)
        elif self._is_bilibili_url(url):
            return await self._parse_bilibili(url)
        else:
            return ParseResult(
                success=False,
                error="Unsupported video URL. Supported platforms: YouTube, Bilibili",
            )

    async def _parse_youtube(self, url: str) -> ParseResult:
        """Parse a YouTube video and extract its transcript.

        Args:
            url: YouTube video URL.

        Returns:
            ParseResult with the transcript content.
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # Extract video ID from URL
            video_id = self._extract_youtube_id(url)
            if not video_id:
                return ParseResult(
                    success=False,
                    error="Could not extract YouTube video ID from URL",
                )

            # Get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["zh", "zh-Hans", "en"])

            if not transcript:
                return ParseResult(
                    success=False,
                    error="No transcript available for this video",
                )

            # Format transcript as readable text
            content = self._format_transcript(transcript)
            title = f"YouTube Video: {video_id}"

            return ParseResult(
                success=True,
                title=title,
                content=content,
                metadata={
                    "source_url": url,
                    "video_id": video_id,
                    "platform": "youtube",
                },
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Failed to parse YouTube video: {str(e)}",
            )

    async def _parse_bilibili(self, url: str) -> ParseResult:
        """Parse a Bilibili video and extract its subtitle.

        Args:
            url: Bilibili video URL.

        Returns:
            ParseResult with the subtitle content.
        """
        try:
            import httpx

            # Extract BV ID from URL
            bv_id = self._extract_bilibili_bv(url)
            if not bv_id:
                return ParseResult(
                    success=False,
                    error="Could not extract Bilibili BV ID from URL",
                )

            # Fetch video page to get subtitle info
            # Note: This is a simplified implementation. Full Bilibili subtitle
            # extraction requires handling their API and authentication.
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to get the video info page
                response = await client.get(f"https://www.bilibili.com/video/{bv_id}")
                response.raise_for_status()

            # For now, return a placeholder result
            # A full implementation would parse the HTML and call Bilibili's subtitle API
            return ParseResult(
                success=False,
                error="Bilibili subtitle extraction requires additional setup. "
                      "Please use a different method or manually download subtitles.",
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Failed to parse Bilibili video: {str(e)}",
            )

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube URL."""
        youtube_patterns = [
            r"youtube\.com/watch\?",
            r"youtu\.be/",
            r"youtube\.com/shorts/",
        ]
        return any(re.search(pattern, url) for pattern in youtube_patterns)

    def _is_bilibili_url(self, url: str) -> bool:
        """Check if URL is a Bilibili URL."""
        return bool(re.search(r"bilibili\.com/video/", url))

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL.

        Args:
            url: YouTube URL.

        Returns:
            Video ID or None if not found.
        """
        # Handle youtu.be short URLs
        short_match = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", url)
        if short_match:
            return short_match.group(1)

        # Handle standard youtube.com URLs
        standard_match = re.search(r"[?&]v=([a-zA-Z0-9_-]+)", url)
        if standard_match:
            return standard_match.group(1)

        # Handle shorts
        shorts_match = re.search(r"youtube\.com/shorts/([a-zA-Z0-9_-]+)", url)
        if shorts_match:
            return shorts_match.group(1)

        return None

    def _extract_bilibili_bv(self, url: str) -> Optional[str]:
        """Extract Bilibili BV ID from URL.

        Args:
            url: Bilibili URL.

        Returns:
            BV ID or None if not found.
        """
        # Bilibili uses BV IDs like BV1xx411c7mD
        match = re.search(r"(BV[a-zA-Z0-9]+)", url)
        return match.group(1) if match else None

    def _format_transcript(self, transcript: list[dict]) -> str:
        """Format transcript as readable text.

        Args:
            transcript: List of transcript segments with 'text' and 'start' keys.

        Returns:
            Formatted text content.
        """
        lines: list[str] = []

        for segment in transcript:
            text = segment.get("text", "").strip()
            if text:
                lines.append(text)

        # Join with double newlines for readability
        content = "\n\n".join(lines)

        # Clean up common subtitle artifacts
        content = re.sub(r"\[.*?\]", "", content)  # Remove [Music], [Applause], etc.
        content = re.sub(r"\(.*?\)", "", content)  # Remove (laughs), etc.
        content = re.sub(r"\s+", " ", content)  # Normalize whitespace
        content = content.strip()

        return content
