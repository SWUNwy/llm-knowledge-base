# R004: MarkItDown 文件解析引擎集成

## 背景

当前知识库项目的文件解析能力存在以下问题：

1. **格式覆盖有限**：仅支持 PDF、HTML、视频字幕、GitHub 仓库，不支持 DOCX/PPTX/XLSX/EPUB 等常见格式
2. **解析质量低**：PDF 用 PyMuPDF 提取纯文本（丢失表格/结构），HTML 用 readability 提取纯文本（丢失列表/链接）
3. **LLM 效率低**：所有内容以纯文本送入 LLM 编译，LLM 需要自行推断文档结构，浪费 token

## 目标

集成微软 MarkItDown 库作为底层解析引擎，构建文档处理管道，提升解析质量和 LLM 编译效率。

### 核心价值

- **格式扩展**：PDF、DOCX、PPTX、XLSX、HTML、EPUB、图片、CSV、Jupyter 等统一处理
- **结构保留**：输出 Markdown 而非纯文本，保留标题/表格/列表/链接结构
- **LLM 效率提升**：智能分块避免超 context window，格式定制 prompt 提高编译质量

## 范围

### 包含

- MarkItDownParser：统一文件解析器，替换 PDFParser 和 WebParser
- DocumentProcessor：后处理管道（智能分块 + 格式适配）
- PromptTemplates 增强：格式定制编译模板
- IngestService 改造：新路由逻辑 + 分块存储
- 图片 LLM 描述功能
- 依赖管理：添加 markitdown，移除 PyMuPDF 和 readability-lxml

### 不包含

- VideoParser 和 GitHubParser 保持不变
- 前端 UI 变更（后续需求）
- MCP Server 集成（后续需求）
- OCR 插件集成（后续需求）

## 依赖

- `markitdown[all]>=0.1.0`（核心依赖）
- `litellm`（已有，用于图片描述）

## 技术方案

详见 `design.md`
