from __future__ import annotations
"""文档模型"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """文档类型"""

    WEB = "web"
    PAPER = "paper"
    VIDEO = "video"
    CODE = "code"


class DocumentStatus(str, Enum):
    """文档状态"""

    PENDING = "pending"
    PROCESSED = "processed"


class DocumentBase(BaseModel):
    """文档基类"""

    type: DocumentType = Field(..., description="文档类型")
    title: str = Field(..., min_length=1, description="文档标题")
    content: str = Field(..., min_length=1, description="文档内容")
    source_url: Optional[str] = Field(None, description="来源 URL")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentCreate(DocumentBase):
    """创建文档请求"""

    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING, description="文档状态"
    )


class Document(DocumentBase):
    """完整文档模型"""

    id: str = Field(..., description="文档 ID")
    path: str = Field(..., description="文档存储路径")
    status: DocumentStatus = Field(..., description="文档状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = []

        # 标题
        lines.append(f"# {self.title}")
        lines.append("")

        # 元信息
        lines.append("---")
        lines.append(f"ID: {self.id}")
        lines.append(f"Type: {self.type.value}")
        lines.append(f"Status: {self.status.value}")
        if self.source_url:
            lines.append(f"Source: {self.source_url}")
        if self.tags:
            lines.append(f"Tags: {', '.join(self.tags)}")
        lines.append(f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("---")
        lines.append("")

        # 正文内容
        lines.append(self.content)

        return "\n".join(lines)


class DocumentSummary(BaseModel):
    """文档摘要"""

    id: str = Field(..., description="文档 ID")
    title: str = Field(..., description="文档标题")
    type: DocumentType = Field(..., description="文档类型")
    status: DocumentStatus = Field(..., description="文档状态")
    created_at: datetime = Field(..., description="创建时间")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class DocumentListResponse(BaseModel):
    """文档列表响应"""

    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    limit: int = Field(..., description="每页数量")
    items: list[DocumentSummary] = Field(..., description="文档列表")


class SearchResult(BaseModel):
    """搜索结果"""

    id: str = Field(..., description="文档 ID")
    title: str = Field(..., description="文档标题")
    snippet: str = Field(..., description="内容片段")
    score: float = Field(..., ge=0.0, le=1.0, description="相关性分数")
