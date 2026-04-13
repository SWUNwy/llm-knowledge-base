# R004 Design: MarkItDown 文件解析引擎集成

## 架构概览

```
┌──────────────────────────────────────────────────────┐
│  IngestService (编排层)                                │
│  路由: URL/file → 选择处理管道                          │
├───────────────┬──────────────┬───────────────────────┤
│ 文档管道       │ 视频管道      │ 代码管道               │
│               │ (保留)        │ (保留)                 │
│ ┌───────────┐ │              │                        │
│ │MarkItDown │ │ VideoParser  │ GitHubParser           │
│ │ 引擎       │ │              │                        │
│ └─────┬─────┘ └──────────────┘────────────────────────┤
│       │ Markdown output                               │
│ ┌─────▼──────────────────────┐                        │
│ │ DocumentProcessor           │                        │
│ │ ├─ 格式识别                  │                        │
│ │ ├─ 智能分块(按标题切分)       │                        │
│ │ ├─ Token 估算                │                        │
│ │ └─ 格式适配                  │                        │
│ └─────┬──────────────────────┘                        │
│       │ Chunked Markdown                               │
│ ┌─────▼──────────────────────┐                        │
│ │ PromptTemplates 增强         │                        │
│ │ ├─ COMPILE_TABLE_DATA       │                        │
│ │ ├─ COMPILE_PRESENTATION     │                        │
│ │ ├─ COMPILE_PAPER            │                        │
│ │ └─ COMPILE_DOCUMENT (通用)  │                        │
│ └────────────────────────────┘                        │
└──────────────────────────────────────────────────────┘
```

## 组件设计

### 1. MarkItDownParser (`parsers/markitdown.py`)

薄包装 markitdown 库，统一处理所有支持的文件格式。

**继承**：`BaseParser`

**支持格式**：
- `.pdf` — pdfplumber 表格提取 + pdfminer fallback
- `.docx` — mammoth → HTML → Markdown
- `.pptx` — PowerPoint 结构提取
- `.xlsx` / `.xls` — Excel 表格转 Markdown
- `.html` / `.htm` — HTML → Markdown
- `.epub` — 电子书
- `.csv` — CSV 表格
- `.jpg` / `.jpeg` / `.png` — EXIF 元数据 + LLM 图片描述
- `.ipynb` — Jupyter notebook
- `.zip` — 递归处理压缩包内容

**关键设计决策**：
- MarkItDown 是同步库，用 `asyncio.to_thread()` 包装为异步
- 输出 `ParseResult.content` 为 Markdown 格式（核心变化：从纯文本到结构化 Markdown）
- `metadata["source_format"]` 标记原始格式（如 "pdf", "docx"）供下游使用
- 通过 `llm_client` 参数支持图片 LLM 描述（可选）

```python
class MarkItDownParser(BaseParser):
    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
        ".html", ".htm", ".epub", ".csv",
        ".jpg", ".jpeg", ".png", ".ipynb", ".zip",
    }

    def __init__(self, llm_client=None, llm_model=None):
        self._md = MarkItDown(llm_client=llm_client, llm_model=llm_model)

    async def parse_file(self, path: Path) -> ParseResult:
        result = await asyncio.to_thread(self._md.convert, str(path))
        return ParseResult(
            success=True,
            title=result.title or "",
            content=result.markdown,
            metadata={"source_format": path.suffix.lstrip(".")},
        )

    async def parse_url(self, url: str) -> ParseResult:
        result = await asyncio.to_thread(self._md.convert, url)
        return ParseResult(
            success=True,
            title=result.title or "",
            content=result.markdown,
            metadata={"source_format": "html", "source_url": url},
        )
```

### 2. DocumentProcessor (`services/processor.py`)

后处理管道，接收 Markdown 内容，执行智能分块和格式适配。

#### 数据结构

```python
@dataclass
class DocumentChunk:
    content: str               # Markdown 内容片段
    index: int                 # 分块序号（从 0 开始）
    total: int                 # 总分块数
    section_path: list[str]    # 章节路径 ["Chapter 2", "Section 2.1"]
    source_format: str         # "pdf", "docx", etc.
    token_count: int           # 估算的 token 数
```

#### 智能分块策略

按 Markdown 标题层级递归切分：

1. **估算 token 数**：按 `len(content) / 4` 粗估（中文约 1 字 = 1-2 tokens）
2. **不超限**：低于 `CHUNK_TOKEN_LIMIT`（默认 6000），返回单块
3. **按 `#` 切分**：在一级标题处分割
4. **递归**：单节仍超限则按 `##` 二级标题再切分
5. **上下文携带**：每个分块包含文档标题和所属章节路径

#### 格式适配

根据 `source_format` 做格式特定的后处理：

| 格式 | 适配策略 |
|------|---------|
| PDF | 检测 Markdown 表格块，标记为 `content_type="table"` |
| DOCX | 保留标题层级结构不变 |
| PPTX | 用 `---` (horizontal rule) 作为幻灯片分隔符，每张幻灯片作为独立分块 |
| XLSX | 每个 sheet 分开，标记为 `content_type="spreadsheet"` |
| HTML | 保留链接和列表结构 |
| 通用 | 无额外处理 |

```python
class DocumentProcessor:
    CHUNK_TOKEN_LIMIT = 6000

    def process(self, content: str, source_format: str, title: str = "") -> list[DocumentChunk]:
        token_count = self._estimate_tokens(content)
        if token_count <= self.CHUNK_TOKEN_LIMIT:
            return [DocumentChunk(
                content=content, index=0, total=1,
                section_path=[title] if title else [],
                source_format=source_format, token_count=token_count,
            )]
        return self._split_by_headings(content, source_format, title)
```

### 3. PromptTemplates 增强 (`llm/prompts.py`)

根据 `source_format` 选择不同的编译策略。

#### 新增模板

| 模板 | 适用格式 | 编译侧重 |
|------|---------|---------|
| `COMPILE_DOCUMENT` | HTML、EPUB、通用 | 保留原文结构，提取 wiki-links |
| `COMPILE_TABLE_DATA` | PDF(表格)、XLSX、CSV | 数据准确性，表格保留 |
| `COMPILE_PRESENTATION` | PPTX | 叙事连贯性，补充幻灯片间过渡 |
| `COMPILE_PAPER` | PDF(纯文本) | 学术结构，提取摘要/方法论/结论 |

#### 格式路由

```python
FORMAT_TEMPLATES = {
    "xlsx": "COMPILE_TABLE_DATA",
    "xls": "COMPILE_TABLE_DATA",
    "csv": "COMPILE_TABLE_DATA",
    "pptx": "COMPILE_PRESENTATION",
    "pdf": "COMPILE_PAPER",
}

@classmethod
def compile_for_format(cls, source_format: str, **kwargs) -> str:
    template_name = FORMAT_TEMPLATES.get(source_format, "COMPILE_DOCUMENT")
    template = getattr(cls, template_name)
    return template.format(**kwargs)
```

### 4. IngestService 改造 (`services/ingest.py`)

保持轻量编排层职责。

**变化**：
- 移除 `PDFParser` 和 `WebParser` 实例
- 新增 `MarkItDownParser` 和 `DocumentProcessor` 实例
- `ingest_file()` 中根据扩展名路由到 `MarkItDownParser`
- `ingest_url()` 中一般 URL 走 `MarkItDownParser.parse_url()`
- 新增分块存储逻辑

**doc_type 映射**：

```python
DOC_TYPE_MAP = {
    ".pdf": "paper",
    ".docx": "paper",
    ".pptx": "presentation",
    ".xlsx": "data",
    ".xls": "data",
    ".csv": "data",
    ".epub": "book",
    ".html": "web",
    ".htm": "web",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".ipynb": "code",
}
```

### 5. 配置变更 (`config.py`)

```python
# 新增
markitdown_llm_image_description: bool = True  # 图片 LLM 描述
chunk_token_limit: int = 6000                   # 分块阈值
```

## 文件变更清单

### 新增

| 文件 | 说明 |
|------|------|
| `parsers/markitdown.py` | MarkItDown 包装器 |
| `services/processor.py` | DocumentProcessor 后处理管道 |

### 修改

| 文件 | 变更 |
|------|------|
| `services/ingest.py` | 替换 parser，增加分块逻辑 |
| `llm/prompts.py` | 增加 3 个格式定制模板 + 路由方法 |
| `config.py` | 增加 2 个配置项 |
| `parsers/__init__.py` | 导出变更 |

### 删除

| 文件 | 原因 |
|------|------|
| `parsers/pdf.py` | 被 markitdown.py 替代 |
| `parsers/web.py` | 被 markitdown.py 替代 |

## 依赖变更

### 新增

```
markitdown[all]>=0.1.0
```

### 移除

```
PyMuPDF          # 被 markitdown 的 pdfplumber+pdfminer 替代
readability-lxml  # 被 markitdown 的 HTML converter 替代
```

## 数据流示例

### 示例 1：上传 Word 文档

```
用户上传 report.docx (5 页, ~3000 tokens)
    │
    ▼ MarkItDownParser.parse_file()
    ParseResult(
      content="# 报告标题\n## 第一章\n...\n## 第二章\n...",
      source_format="docx"
    )
    │
    ▼ DocumentProcessor.process()
    [DocumentChunk(content=..., total=1)]  # 不超限，不分块
    │
    ▼ 存储 vault/raw/papers/{id}.md
    ▼ 数据库记录 (status="pending")
    │
    ▼ 后台编译: PromptTemplates.compile_for_format("docx", ...)
    ▼ LLM → vault/compiled/{id}.md
```

### 示例 2：上传大型 PDF

```
用户上传 thesis.pdf (100 页, ~20000 tokens)
    │
    ▼ MarkItDownParser.parse_file()
    ParseResult(content="# 摘要\n...\n# 第一章\n...\n# 第二章\n...", source_format="pdf")
    │
    ▼ DocumentProcessor.process()
    [
      Chunk(content="# 摘要\n...", section_path=["摘要"], total=4),
      Chunk(content="# 第一章\n...", section_path=["第一章"], total=4),
      Chunk(content="# 第二章\n...", section_path=["第二章"], total=4),
      Chunk(content="# 第三章\n...", section_path=["第三章"], total=4),
    ]
    │
    ▼ 存储 vault/raw/papers/{id}.md
    ▼ 数据库: 4 条 chunk 记录 (status="pending")
    │
    ▼ 后台编译: 每块独立送入 LLM，使用 COMPILE_PAPER 模板
    ▼ 合并结果 → vault/compiled/{id}.md
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 不支持的文件格式 | 返回 `ParseResult(success=False, error="...")` |
| MarkItDown 转换失败 | 捕获异常，返回 `ParseResult(success=False)` |
| 分块后某块过大 | 递归切分直到低于阈值；如果单个段落仍超限，强制截断 |
| LLM 图片描述失败 | 静默跳过，仅返回 EXIF 元数据 |
| 文件损坏/加密 | MarkItDown 内部处理，返回错误 |

## 测试要点

- 各格式文件解析正确性
- 分块逻辑：大文件按标题切分、小文件不分块
- 格式路由：不同 source_format 对应正确的 prompt 模板
- 异步包装：asyncio.to_thread 正常工作
- 错误处理：损坏文件、不支持的格式
- IngestService 路由：扩展名正确路由到对应 parser
