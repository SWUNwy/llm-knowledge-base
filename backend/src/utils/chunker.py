"""文本分块器模块

将长文档拆分为适合 LLM 处理的小块，支持按字符、段落和 Markdown 标题分块。
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """分块配置

    Args:
        chunk_size: 每个分块的最大字符数
        chunk_overlap: 分块之间的重叠字符数
        min_chunk_size: 最小分块大小，低于此值的尾部块会合并到前一个块
    """

    chunk_size: int = 500
    chunk_overlap: int = 100
    min_chunk_size: int = 100


class TextChunker:
    """文本分块器

    提供多种策略将长文本拆分为较小的块，用于 LLM 处理。
    """

    def chunk_text(self, text: str, config: ChunkingConfig | None = None) -> list[str]:
        """按固定字符数分块

        使用滑动窗口将文本拆分为固定大小的块，相邻块之间有重叠。
        如果最后一个块小于 min_chunk_size，则合并到前一个块中。

        Args:
            text: 要分块的文本
            config: 分块配置，为 None 时使用默认配置

        Returns:
            分块后的文本列表
        """
        if config is None:
            config = ChunkingConfig()

        text = text.strip()
        if not text:
            return []

        chunk_size = config.chunk_size
        overlap = config.chunk_overlap
        step = chunk_size - overlap

        # Ensure step is positive
        if step <= 0:
            step = chunk_size

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            if end >= len(text):
                break
            start += step

        # Merge last chunk into previous if it's too small
        if len(chunks) >= 2 and len(chunks[-1]) < config.min_chunk_size:
            chunks[-2] = chunks[-2] + chunks[-1]
            chunks.pop()

        return chunks

    def chunk_by_paragraphs(
        self, text: str, config: ChunkingConfig | None = None
    ) -> list[str]:
        """按段落分块

        以双换行符分隔段落，将多个段落合并到同一个块中直到达到 chunk_size。
        不会在段落中间拆分。

        Args:
            text: 要分块的文本
            config: 分块配置，为 None 时使用默认配置

        Returns:
            分块后的文本列表
        """
        if config is None:
            config = ChunkingConfig()

        text = text.strip()
        if not text:
            return []

        paragraphs = re.split(r"\n\n+", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return []

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_size = 0
        separator = "\n\n"

        for para in paragraphs:
            para_len = len(para)

            # If adding this paragraph would exceed chunk_size and we already
            # have content, start a new chunk
            if current_chunk and current_size + len(separator) + para_len > config.chunk_size:
                chunks.append(separator.join(current_chunk))
                # Apply overlap: include last paragraphs that fit within overlap
                overlap_chunks: list[str] = []
                overlap_size = 0
                for prev_para in reversed(current_chunk):
                    if overlap_size + len(prev_para) <= config.chunk_overlap:
                        overlap_chunks.insert(0, prev_para)
                        overlap_size += len(prev_para) + len(separator)
                    else:
                        break
                current_chunk = overlap_chunks
                current_size = sum(len(p) for p in current_chunk) + len(separator) * max(
                    0, len(current_chunk) - 1
                )

            current_chunk.append(para)
            current_size += para_len + (len(separator) if len(current_chunk) > 1 else 0)

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # Merge last chunk into previous if it's too small
        if len(chunks) >= 2 and len(chunks[-1]) < config.min_chunk_size:
            chunks[-2] = chunks[-2] + separator + chunks[-1]
            chunks.pop()

        return chunks

    def chunk_markdown_by_headers(self, text: str) -> list[str]:
        """按 Markdown H2 标题分块

        以 ## 标题作为分块点，将每个 H2 节及其内容作为一个块。
        H1 标题被视为文档标题，与后续内容一起包含在第一个块中。
        H3 及以下标题不会触发分块。

        Args:
            text: Markdown 格式的文本

        Returns:
            分块后的文本列表
        """
        text = text.strip()
        if not text:
            return []

        # Split on ## headers (but not ### or deeper)
        sections = re.split(r"(?=^## [^#])", text, flags=re.MULTILINE)

        chunks: list[str] = []
        for section in sections:
            section = section.strip()
            if section:
                chunks.append(section)

        return chunks
