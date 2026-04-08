"""Tests for the GitHub parser."""

import tempfile
from pathlib import Path

import pytest

from src.parsers.github import GitHubParser


@pytest.fixture
def parser() -> GitHubParser:
    """Create a GitHubParser instance."""
    return GitHubParser()


class TestParseGitHubUrl:
    """Tests for GitHub URL parsing."""

    def test_standard_https_url(self, parser: GitHubParser) -> None:
        result = parser._parse_github_url("https://github.com/owner/repo")
        assert result == ("owner", "repo")

    def test_url_with_git_suffix(self, parser: GitHubParser) -> None:
        result = parser._parse_github_url("https://github.com/owner/repo.git")
        assert result == ("owner", "repo")

    def test_url_with_trailing_slash(self, parser: GitHubParser) -> None:
        result = parser._parse_github_url("https://github.com/owner/repo/")
        assert result == ("owner", "repo")

    def test_url_with_subpath(self, parser: GitHubParser) -> None:
        result = parser._parse_github_url("https://github.com/owner/repo/tree/main/docs")
        assert result == ("owner", "repo")

    def test_ssh_url(self, parser: GitHubParser) -> None:
        result = parser._parse_github_url("git@github.com:owner/repo.git")
        assert result == ("owner", "repo")

    def test_invalid_url(self, parser: GitHubParser) -> None:
        assert parser._parse_github_url("https://example.com") is None


class TestExtractContent:
    """Tests for content extraction from a local directory."""

    def test_finds_readme(self, parser: GitHubParser) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            readme = Path(tmpdir) / "README.md"
            readme.write_text("# My Project\n\nThis is a test project.")

            content = parser._extract_content(Path(tmpdir), "owner", "repo")
            assert "# My Project" in content
            assert "This is a test project" in content

    def test_finds_docs_directory(self, parser: GitHubParser) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            guide = docs_dir / "guide.md"
            guide.write_text("# Guide\n\nHow to use this project.")

            content = parser._extract_content(Path(tmpdir), "owner", "repo")
            assert "# Guide" in content
            assert "How to use this project" in content

    def test_finds_root_markdown(self, parser: GitHubParser) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            changelog = Path(tmpdir) / "CHANGELOG.md"
            changelog.write_text("# Changelog\n\n## v1.0\n- Initial release")

            content = parser._extract_content(Path(tmpdir), "owner", "repo")
            assert "# Changelog" in content

    def test_empty_repo(self, parser: GitHubParser) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = parser._extract_content(Path(tmpdir), "owner", "repo")
            assert content == ""

    def test_skips_node_modules(self, parser: GitHubParser) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            nm_dir = Path(tmpdir) / "node_modules"
            nm_dir.mkdir()
            pkg = nm_dir / "package.md"
            pkg.write_text("Should be skipped")

            content = parser._extract_content(Path(tmpdir), "owner", "repo")
            assert "Should be skipped" not in content


class TestReadFile:
    """Tests for file reading with size limits."""

    def test_reads_normal_file(self, parser: GitHubParser) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Hello world")
            f.flush()

            content = parser._read_file(Path(f.name))
            assert content == "Hello world"

    def test_skips_large_file(self, parser: GitHubParser) -> None:
        parser_small = GitHubParser(max_file_size=10)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("A" * 100)
            f.flush()

            content = parser_small._read_file(Path(f.name))
            assert content is None


class TestParseFileNotSupported:
    """Tests for parse_file (not supported)."""

    @pytest.mark.asyncio
    async def test_parse_file_not_supported(self, parser: GitHubParser) -> None:
        result = await parser.parse_file(Path("/some/path"))
        assert not result.success
        assert "URL" in result.error
