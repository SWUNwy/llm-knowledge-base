from __future__ import annotations
"""Prompt模板模块

提供用于LLM交互的结构化Prompt模板
"""

from typing import Optional


class PromptTemplates:
    """Prompt模板类

    提供三种主要模板：
    - COMPILE_DOCUMENT: 将原始文档编译为wiki格式
    - EXTRACT_CONCEPTS: 从文档中提取概念
    - QA_ANSWER: 基于源文档回答问题
    """

    # 文档编译模板
    COMPILE_DOCUMENT = """You are a knowledge base editor. Your task is to compile a raw document into a well-structured wiki page.

## Input Document Information
- **Title**: {title}
- **Type**: {type}
- **Source URL**: {source}
- **Source ID**: {source_id}
- **Original Title**: {original_title}

## Raw Content
{content}

## Instructions
1. Rewrite this document into a clear, well-structured wiki page in **{output_language}**.
2. Use proper Markdown formatting (headers, lists, code blocks, etc.).
3. When you mention key concepts, entities, or terms that deserve their own wiki pages, create wiki-links using the `[[term]]` syntax.
4. Keep the original meaning and important details.
5. Add appropriate sections and structure if the content is unstructured.
6. Include a brief summary at the beginning.

## Wiki-Link Guidelines
- Use `[[concept name]]` for concepts, terms, people, organizations, or topics that merit a separate page.
- Example: "Machine learning is a subset of [[Artificial Intelligence]]."
- Only create links for significant concepts, not every word.

## Output
Please provide the compiled wiki page in {output_language}:"""

    # 概念提取模板
    EXTRACT_CONCEPTS = """You are a knowledge extraction specialist. Your task is to identify and extract key concepts from a document.

## Document Content
{content}

## Instructions
1. Identify important concepts, terms, entities, and topics mentioned in the document.
2. For each concept, provide the information requested below.
3. Respond in **{output_language}**.

## Output Format
Return a JSON array where each concept has the following structure:
```json
{{
  "concepts": [
    {{
      "name": "Concept name",
      "type": "concept|entity|term|technology|person|organization|other",
      "confidence": 0.95,
      "definition": "Brief definition or explanation of the concept",
      "aliases": ["alternative name 1", "alternative name 2"]
    }}
  ]
}}
```

## Guidelines
- `name`: The primary name/term for the concept.
- `type`: Categorize the concept appropriately.
- `confidence`: A value between 0.0 and 1.0 indicating how confident you are that this is a meaningful concept.
- `definition`: A concise definition or explanation based on the document context.
- `aliases`: Alternative names, abbreviations, or related terms.

Only include concepts with confidence >= 0.5. Return only valid JSON, no additional text.

## Output
Please provide the extracted concepts as JSON:"""

    # 问答模板
    QA_ANSWER = """You are a knowledgeable assistant. Answer the user's question based on the provided source documents.

## Question
{question}

## Source Documents

{sources}

## Source References
- Source IDs: {source_ids}
- Titles: {titles}

## Instructions
1. Answer the question in a comprehensive and helpful way.
2. Base your answer primarily on the provided source documents.
3. When mentioning concepts or terms that might have wiki pages, use wiki-links `[[term]]`.
4. At the end of your answer, cite the sources you used by referencing the source IDs (e.g., [source:doc_1]).
5. If the sources don't contain enough information to fully answer the question, acknowledge this and provide what information is available.

## Wiki-Link Guidelines
- Use `[[concept name]]` for concepts, terms, or topics that might have their own pages.
- Example: "According to [[Machine Learning]] research..."

## Source Citation Format
When you reference information from a source, include the source ID in brackets:
- For a single source: [source:doc_1]
- For multiple sources: [source:doc_1, doc_2]

## Output
Please provide your answer:"""

    @classmethod
    def compile_document(
        cls,
        title: str,
        type: str,
        source: str,
        content: str,
        source_id: str,
        original_title: str,
        output_language: str = "中文",
    ) -> str:
        """构建文档编译Prompt

        Args:
            title: 文档标题
            type: 文档类型 (web, paper, video, code)
            source: 来源URL
            content: 文档原始内容
            source_id: 源文档ID
            original_title: 原始标题
            output_language: 输出语言，默认为中文

        Returns:
            构建好的Prompt字符串
        """
        return cls.COMPILE_DOCUMENT.format(
            title=title,
            type=type,
            source=source,
            content=content,
            source_id=source_id,
            original_title=original_title,
            output_language=output_language,
        )

    @classmethod
    def extract_concepts(
        cls,
        content: str,
        output_language: str = "中文",
    ) -> str:
        """构建概念提取Prompt

        Args:
            content: 文档内容
            output_language: 输出语言，默认为中文

        Returns:
            构建好的Prompt字符串
        """
        return cls.EXTRACT_CONCEPTS.format(
            content=content,
            output_language=output_language,
        )

    @classmethod
    def qa_answer(
        cls,
        question: str,
        sources: str,
        source_ids: list[str],
        titles: list[str],
    ) -> str:
        """构建问答Prompt

        Args:
            question: 用户问题
            sources: 源文档文本内容
            source_ids: 源文档ID列表
            titles: 源文档标题列表

        Returns:
            构建好的Prompt字符串
        """
        return cls.QA_ANSWER.format(
            question=question,
            sources=sources,
            source_ids=", ".join(source_ids),
            titles=", ".join(titles),
        )
