"""文档模型测试"""

import pytest
from datetime import datetime

from src.models.document import (
    DocumentType,
    DocumentStatus,
    DocumentBase,
    DocumentCreate,
    Document,
    DocumentSummary,
    DocumentListResponse,
    SearchResult,
)


class TestDocumentType:
    """测试文档类型枚举"""

    def test_document_types_exist(self) -> None:
        """验证所有文档类型存在"""
        assert DocumentType.WEB
        assert DocumentType.PAPER
        assert DocumentType.VIDEO
        assert DocumentType.CODE

    def test_document_type_values(self) -> None:
        """验证文档类型值"""
        assert DocumentType.WEB.value == "web"
        assert DocumentType.PAPER.value == "paper"
        assert DocumentType.VIDEO.value == "video"
        assert DocumentType.CODE.value == "code"


class TestDocumentStatus:
    """测试文档状态枚举"""

    def test_document_statuses_exist(self) -> None:
        """验证所有文档状态存在"""
        assert DocumentStatus.PENDING
        assert DocumentStatus.PROCESSED

    def test_document_status_values(self) -> None:
        """验证文档状态值"""
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.PROCESSED.value == "processed"


class TestDocumentBase:
    """测试文档基类"""

    def test_document_base_required_fields(self) -> None:
        """验证必填字段"""
        doc = DocumentBase(
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
        )
        assert doc.type == DocumentType.WEB
        assert doc.title == "Test Document"
        assert doc.content == "Test content"

    def test_document_base_optional_fields(self) -> None:
        """验证可选字段"""
        doc = DocumentBase(
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
            source_url="https://example.com",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
        )
        assert doc.source_url == "https://example.com"
        assert doc.tags == ["tag1", "tag2"]
        assert doc.metadata == {"key": "value"}

    def test_document_base_defaults(self) -> None:
        """验证默认值"""
        doc = DocumentBase(
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
        )
        assert doc.source_url is None
        assert doc.tags == []
        assert doc.metadata == {}


class TestDocumentCreate:
    """测试创建文档请求"""

    def test_document_create_defaults(self) -> None:
        """验证创建文档的默认值"""
        doc_create = DocumentCreate(
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
        )
        # status 默认值应为 "pending"
        assert doc_create.status == DocumentStatus.PENDING

    def test_document_create_custom_status(self) -> None:
        """验证可以自定义 status"""
        doc_create = DocumentCreate(
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
            status=DocumentStatus.PROCESSED,
        )
        assert doc_create.status == DocumentStatus.PROCESSED


class TestDocument:
    """测试完整文档模型"""

    def test_document_fields(self) -> None:
        """验证文档字段"""
        now = datetime.now()
        doc = Document(
            id="doc-abc123",
            type=DocumentType.WEB,
            title="Test Document",
            content="Test content",
            path="/documents/doc-abc123.md",
            status=DocumentStatus.PROCESSED,
            created_at=now,
            updated_at=now,
        )
        assert doc.id == "doc-abc123"
        assert doc.path == "/documents/doc-abc123.md"
        assert doc.status == DocumentStatus.PROCESSED
        assert doc.created_at == now
        assert doc.updated_at == now

    def test_document_to_markdown(self) -> None:
        """验证 markdown 输出格式"""
        now = datetime(2024, 1, 15, 10, 30, 0)
        doc = Document(
            id="doc-abc123",
            type=DocumentType.WEB,
            title="Test Document",
            content="# Hello\n\nThis is test content.",
            path="/documents/doc-abc123.md",
            status=DocumentStatus.PROCESSED,
            created_at=now,
            updated_at=now,
            source_url="https://example.com/article",
            tags=["test", "example"],
        )
        markdown = doc.to_markdown()

        # 验证 markdown 包含必要信息
        assert "# Test Document" in markdown
        assert "Type: web" in markdown
        assert "Status: processed" in markdown
        assert "https://example.com/article" in markdown
        assert "test, example" in markdown
        assert "# Hello" in markdown
        assert "This is test content." in markdown
        assert "2024-01-15" in markdown

    def test_document_to_markdown_minimal(self) -> None:
        """验证最小文档的 markdown 输出"""
        now = datetime(2024, 1, 15, 10, 30, 0)
        doc = Document(
            id="doc-xyz",
            type=DocumentType.PAPER,
            title="Minimal Doc",
            content="Simple content",
            path="/documents/doc-xyz.md",
            status=DocumentStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        markdown = doc.to_markdown()

        assert "# Minimal Doc" in markdown
        assert "Type: paper" in markdown
        assert "Status: pending" in markdown
        assert "Simple content" in markdown


class TestDocumentSummary:
    """测试文档摘要"""

    def test_document_summary_fields(self) -> None:
        """验证摘要字段"""
        now = datetime.now()
        summary = DocumentSummary(
            id="doc-abc123",
            title="Test Document",
            type=DocumentType.WEB,
            status=DocumentStatus.PROCESSED,
            created_at=now,
            tags=["tag1", "tag2"],
        )
        assert summary.id == "doc-abc123"
        assert summary.title == "Test Document"
        assert summary.type == DocumentType.WEB
        assert summary.status == DocumentStatus.PROCESSED
        assert summary.created_at == now
        assert summary.tags == ["tag1", "tag2"]


class TestDocumentListResponse:
    """测试文档列表响应"""

    def test_document_list_response(self) -> None:
        """验证列表响应"""
        now = datetime.now()
        items = [
            DocumentSummary(
                id="doc-1",
                title="Doc 1",
                type=DocumentType.WEB,
                status=DocumentStatus.PROCESSED,
                created_at=now,
                tags=[],
            ),
            DocumentSummary(
                id="doc-2",
                title="Doc 2",
                type=DocumentType.PAPER,
                status=DocumentStatus.PENDING,
                created_at=now,
                tags=["research"],
            ),
        ]
        response = DocumentListResponse(
            total=100,
            page=1,
            limit=10,
            items=items,
        )
        assert response.total == 100
        assert response.page == 1
        assert response.limit == 10
        assert len(response.items) == 2
        assert response.items[0].id == "doc-1"
        assert response.items[1].id == "doc-2"


class TestSearchResult:
    """测试搜索结果"""

    def test_search_result_fields(self) -> None:
        """验证搜索结果字段"""
        result = SearchResult(
            id="doc-abc123",
            title="Test Document",
            snippet="This is a relevant snippet...",
            score=0.95,
        )
        assert result.id == "doc-abc123"
        assert result.title == "Test Document"
        assert result.snippet == "This is a relevant snippet..."
        assert result.score == 0.95

    def test_search_result_score_range(self) -> None:
        """验证搜索分数范围"""
        # 高分
        result_high = SearchResult(
            id="doc-1",
            title="High Match",
            snippet="...",
            score=1.0,
        )
        assert result_high.score == 1.0

        # 低分
        result_low = SearchResult(
            id="doc-2",
            title="Low Match",
            snippet="...",
            score=0.01,
        )
        assert result_low.score == 0.01
