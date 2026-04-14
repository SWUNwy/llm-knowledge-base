"""Prompt模板测试"""

from src.llm.prompts import PromptTemplates


class TestCompileDocumentPrompt:
    """测试文档编译Prompt"""

    def test_compile_document_prompt(self) -> None:
        """验证所有字段都出现在编译文档Prompt中"""
        prompt = PromptTemplates.compile_document(
            title="Introduction to Machine Learning",
            type="paper",
            source="https://arxiv.org/abs/2401.00001",
            content="Machine learning is a subset of artificial intelligence...",
            source_id="doc_abc123",
            original_title="ML Intro Paper",
            output_language="English",
        )

        # Verify all input fields are present in the prompt
        assert "Introduction to Machine Learning" in prompt
        assert "paper" in prompt
        assert "https://arxiv.org/abs/2401.00001" in prompt
        assert "Machine learning is a subset of artificial intelligence..." in prompt
        assert "doc_abc123" in prompt
        assert "ML Intro Paper" in prompt
        assert "English" in prompt

    def test_compile_document_contains_wiki_link_instructions(self) -> None:
        """验证编译文档Prompt包含wiki-link指令"""
        prompt = PromptTemplates.compile_document(
            title="Test",
            type="web",
            source="https://example.com",
            content="Some content",
            source_id="doc_1",
            original_title="Test Title",
            output_language="English",
        )

        assert "[[" in prompt
        assert "]]" in prompt
        assert "wiki" in prompt.lower()

    def test_compile_document_default_language(self) -> None:
        """验证默认输出语言为中文"""
        prompt = PromptTemplates.compile_document(
            title="测试文档",
            type="web",
            source="https://example.com",
            content="测试内容",
            source_id="doc_1",
            original_title="Test",
        )

        assert "中文" in prompt


class TestExtractConceptsPrompt:
    """测试概念提取Prompt"""

    def test_extract_concepts_prompt(self) -> None:
        """验证内容和语言出现在概念提取Prompt中"""
        prompt = PromptTemplates.extract_concepts(
            content="Neural networks are computing systems inspired by biological neural networks.",
            output_language="English",
        )

        assert "Neural networks are computing systems" in prompt
        assert "English" in prompt

    def test_extract_concepts_json_format(self) -> None:
        """验证概念提取Prompt包含JSON格式要求"""
        prompt = PromptTemplates.extract_concepts(
            content="Some content about concepts.",
            output_language="English",
        )

        # Should request JSON output with specific fields
        assert "JSON" in prompt or "json" in prompt
        assert "name" in prompt
        assert "type" in prompt
        assert "confidence" in prompt
        assert "definition" in prompt
        assert "aliases" in prompt

    def test_extract_concepts_default_language(self) -> None:
        """验证默认输出语言为中文"""
        prompt = PromptTemplates.extract_concepts(
            content="这是关于机器学习的内容。",
        )

        assert "中文" in prompt


class TestQAAnswerPrompt:
    """测试问答Prompt"""

    def test_qa_answer_prompt(self) -> None:
        """验证问题和源出现在问答Prompt中"""
        prompt = PromptTemplates.qa_answer(
            question="What is machine learning?",
            sources="Machine learning is a field of AI that enables systems to learn from data.",
            source_ids=["doc_1", "doc_2"],
            titles=["ML Introduction", "AI Overview"],
        )

        assert "What is machine learning?" in prompt
        assert "Machine learning is a field of AI" in prompt
        assert "doc_1" in prompt
        assert "doc_2" in prompt
        assert "ML Introduction" in prompt
        assert "AI Overview" in prompt

    def test_qa_answer_contains_wiki_link_instructions(self) -> None:
        """验证问答Prompt包含wiki-link和引用指令"""
        prompt = PromptTemplates.qa_answer(
            question="What is deep learning?",
            sources="Deep learning uses neural networks with multiple layers.",
            source_ids=["doc_3"],
            titles=["Deep Learning Guide"],
        )

        assert "[[" in prompt
        assert "]]" in prompt
        assert "source" in prompt.lower() or "引用" in prompt or "来源" in prompt


class TestCompileForFormat:
    """Tests for format-specific prompt routing."""

    def test_table_data_format(self) -> None:
        """xlsx format uses COMPILE_TABLE_DATA template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="xlsx",
            title="Sales Report",
            type="data",
            source="local",
            content="| Product | Revenue |\n|---|---|\n| Widget | $1000 |",
            source_id="doc_1",
            original_title="Q4 Report",
        )
        assert "Sales Report" in prompt
        assert "Widget" in prompt
        assert "data" in prompt.lower() or "table" in prompt.lower() or "accuracy" in prompt.lower()

    def test_presentation_format(self) -> None:
        """pptx format uses COMPILE_PRESENTATION template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="pptx",
            title="Quarterly Review",
            type="presentation",
            source="local",
            content="## Slide 1\n\nKey point",
            source_id="doc_2",
            original_title="Review",
        )
        assert "Quarterly Review" in prompt
        assert "Slide 1" in prompt

    def test_paper_format(self) -> None:
        """pdf format uses COMPILE_PAPER template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="pdf",
            title="Research Paper",
            type="paper",
            source="local",
            content="# Abstract\n\nThis paper presents...",
            source_id="doc_3",
            original_title="Paper",
        )
        assert "Research Paper" in prompt
        assert "Abstract" in prompt

    def test_unknown_format_uses_generic(self) -> None:
        """Unknown format falls back to COMPILE_DOCUMENT."""
        prompt = PromptTemplates.compile_for_format(
            source_format="epub",
            title="A Novel",
            type="book",
            source="local",
            content="Chapter 1 content",
            source_id="doc_4",
            original_title="Novel",
        )
        assert "A Novel" in prompt
        assert "Chapter 1 content" in prompt
        assert "[[" in prompt

    def test_csv_uses_table_template(self) -> None:
        """csv format uses COMPILE_TABLE_DATA template."""
        prompt = PromptTemplates.compile_for_format(
            source_format="csv",
            title="Data Export",
            type="data",
            source="local",
            content="Name,Value\nA,1",
            source_id="doc_5",
            original_title="Export",
        )
        assert "Data Export" in prompt
