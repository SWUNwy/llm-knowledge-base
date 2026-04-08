"""Pytest fixtures for LLM Knowledge Base tests."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest

from src.config import get_settings
from src.database import Database


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Set up test environment variables and clear settings cache.

    This fixture automatically sets up required environment variables for tests
    and clears the settings cache before and after each test.
    """
    # Clear settings cache before test
    get_settings.cache_clear()

    # Set required environment variables
    monkeypatch.setenv("VAULT_PATH", "/tmp/test_vault")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key-for-jwt-testing")

    yield

    # Clear settings cache after test
    get_settings.cache_clear()


@pytest.fixture
async def temp_vault() -> AsyncGenerator[Path, None]:
    """Create a temporary vault directory with the required structure.

    Creates a temporary directory with the following structure:
        temp_vault/
        ├── .wiki/
        ├── raw/
        │   ├── web/
        │   ├── papers/
        │   ├── videos/
        │   └── code/
        ├── wiki/
        │   ├── concepts/
        │   ├── sources/
        │   └── connections/
        └── outputs/
            └── answers/

    Yields:
        Path to the temporary vault directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "test_vault"
        vault_path.mkdir()

        # Create .wiki directory for metadata
        (vault_path / ".wiki").mkdir()

        # Create raw subdirectories
        for subdir in ["web", "papers", "videos", "code"]:
            (vault_path / "raw" / subdir).mkdir(parents=True)

        # Create wiki subdirectories
        for subdir in ["concepts", "sources", "connections"]:
            (vault_path / "wiki" / subdir).mkdir(parents=True)

        # Create outputs subdirectories
        (vault_path / "outputs" / "answers").mkdir(parents=True)

        yield vault_path


@pytest.fixture
async def db(temp_vault: Path) -> AsyncGenerator[Database, None]:
    """Create a test database in the temporary vault.

    Args:
        temp_vault: Path to the temporary vault directory.

    Yields:
        Initialized Database instance.
    """
    db_path = temp_vault / ".wiki" / "metadata.db"
    database = Database(db_path)
    await database.connect()
    await database.initialize()
    yield database
    await database.close()


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample markdown content for testing."""
    return """---
id: test-doc-001
type: web
source: https://example.com/article
title: Test Article
created: 2024-01-15
tags: [test, example]
status: pending
---

# Test Article

This is a test article with some content.

## Section 1

Some content in section 1.

## Section 2

Some content in section 2.

[[related-concept]]
"""


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Sample PDF content for testing (minimal valid PDF)."""
    # Minimal PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Root 1 0 R /Size 4 >>
startxref
190
%%EOF
"""
