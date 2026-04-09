from __future__ import annotations
"""GitHub repository parser for extracting README and documentation files."""

import tempfile
from pathlib import Path
from typing import Optional

from src.parsers.base import BaseParser, ParseResult


class GitHubParser(BaseParser):
    """Parser for GitHub repositories.

    Clones the repository and extracts README and documentation files.
    """

    def __init__(self, max_file_size: int = 1024 * 1024) -> None:
        """Initialize the GitHub parser.

        Args:
            max_file_size: Maximum file size in bytes to read (default 1MB).
        """
        self.max_file_size = max_file_size

    # File extensions to look for documentation
    DOC_EXTENSIONS = {
        ".md", ".rst", ".txt", ".adoc",
    }

    # Directories to search for docs
    DOC_DIRS = {
        "docs", "doc", "documentation", "wiki",
    }

    # Directories to skip
    SKIP_DIRS = {
        "node_modules", ".git", "__pycache__", "venv", ".venv",
        "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    }

    async def parse_url(self, url: str) -> ParseResult:
        """Parse a GitHub repository URL.

        Args:
            url: GitHub repository URL.

        Returns:
            ParseResult with the extracted documentation content.
        """
        try:
            import git as gitpython
        except ImportError:
            return ParseResult(
                success=False,
                error="GitPython is not installed. Run: pip install GitPython",
            )

        try:
            # Parse the repo URL
            repo_info = self._parse_github_url(url)
            if not repo_info:
                return ParseResult(
                    success=False,
                    error="Invalid GitHub URL. Expected format: https://github.com/owner/repo",
                )

            owner, repo_name = repo_info

            # Clone the repo to a temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_url = f"https://github.com/{owner}/{repo_name}.git"
                repo = gitpython.Repo.clone_from(
                    clone_url,
                    tmpdir,
                    depth=1,  # Shallow clone for speed
                )

                # Extract content
                content = self._extract_content(Path(tmpdir), owner, repo_name)

                if not content.strip():
                    return ParseResult(
                        success=False,
                        error="No documentation files found in the repository",
                    )

                return ParseResult(
                    success=True,
                    title=f"{owner}/{repo_name}",
                    content=content,
                    metadata={
                        "source_url": url,
                        "platform": "github",
                        "owner": owner,
                        "repo_name": repo_name,
                    },
                )
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Failed to parse GitHub repository: {str(e)}",
            )

    async def parse_file(self, path: Path) -> ParseResult:
        """Not supported for GitHub parser.

        Args:
            path: Not used.

        Returns:
            ParseResult indicating this method is not supported.
        """
        return ParseResult(
            success=False,
            error="GitHub parser only supports URL parsing",
        )

    def _parse_github_url(self, url: str) -> Optional[tuple[str, str]]:
        """Parse a GitHub URL and extract owner and repo name.

        Args:
            url: GitHub URL.

        Returns:
            Tuple of (owner, repo_name) or None if parsing fails.
        """
        import re

        # Handle various GitHub URL formats
        patterns = [
            # https://github.com/owner/repo
            r"github\.com/([^/]+)/([^/]+?)(?:\.git|/|$)",
            # git@github.com:owner/repo.git
            r"github\.com:([^/]+)/([^/]+?)(?:\.git|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

        return None

    def _extract_content(
        self,
        repo_path: Path,
        owner: str,
        repo_name: str,
    ) -> str:
        """Extract documentation content from a cloned repository.

        Args:
            repo_path: Path to the cloned repository.
            owner: Repository owner.
            repo_name: Repository name.

        Returns:
            Combined documentation content.
        """
        sections: list[str] = []

        # 1. Try to find and read README
        readme_content = self._find_readme(repo_path)
        if readme_content:
            sections.append(f"# README\n\n{readme_content}")

        # 2. Find documentation files in docs/ directory
        docs_content = self._find_docs(repo_path)
        if docs_content:
            sections.append(docs_content)

        # 3. Find other markdown files in root and first-level dirs
        other_md = self._find_other_markdown(repo_path)
        if other_md:
            sections.append(other_md)

        return "\n\n---\n\n".join(sections)

    def _find_readme(self, repo_path: Path) -> Optional[str]:
        """Find and read README file.

        Args:
            repo_path: Path to the cloned repository.

        Returns:
            README content or None.
        """
        readme_names = ["README.md", "README.rst", "README.txt", "README"]
        for name in readme_names:
            readme_path = repo_path / name
            if readme_path.exists() and readme_path.is_file():
                return self._read_file(readme_path)
        return None

    def _find_docs(self, repo_path: Path) -> Optional[str]:
        """Find and read documentation files.

        Args:
            repo_path: Path to the cloned repository.

        Returns:
            Combined documentation content or None.
        """
        sections: list[str] = []

        for doc_dir_name in self.DOC_DIRS:
            doc_dir = repo_path / doc_dir_name
            if not doc_dir.exists() or not doc_dir.is_dir():
                continue

            for file_path in sorted(doc_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in self.DOC_EXTENSIONS:
                    continue
                if self._should_skip(file_path):
                    continue

                content = self._read_file(file_path)
                if content:
                    relative_path = file_path.relative_to(repo_path)
                    sections.append(f"## {relative_path}\n\n{content}")

        return "\n\n".join(sections) if sections else None

    def _find_other_markdown(self, repo_path: Path) -> Optional[str]:
        """Find markdown files in root and first-level directories.

        Args:
            repo_path: Path to the cloned repository.

        Returns:
            Combined markdown content or None.
        """
        sections: list[str] = []

        # Only look at root level and one level deep
        for file_path in sorted(repo_path.glob("*.md")):
            if file_path.name.upper().startswith("README"):
                continue  # Already handled
            content = self._read_file(file_path)
            if content:
                sections.append(f"## {file_path.name}\n\n{content}")

        for file_path in sorted(repo_path.glob("*/*.md")):
            if self._should_skip(file_path):
                continue
            content = self._read_file(file_path)
            if content:
                relative_path = file_path.relative_to(repo_path)
                sections.append(f"## {relative_path}\n\n{content}")

        return "\n\n".join(sections) if sections else None

    def _should_skip(self, path: Path) -> bool:
        """Check if a path should be skipped.

        Args:
            path: File path to check.

        Returns:
            True if the path should be skipped.
        """
        for part in path.parts:
            if part in self.SKIP_DIRS:
                return True
        return False

    def _read_file(self, path: Path) -> Optional[str]:
        """Read a file with size limit.

        Args:
            path: File path to read.

        Returns:
            File content or None if file is too large or unreadable.
        """
        try:
            if path.stat().st_size > self.max_file_size:
                return None

            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
