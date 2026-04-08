"""Tests for the prompts router."""

from src.routers.prompts import DEFAULT_TEMPLATES
from src.llm.prompts import PromptTemplates


class TestDefaultTemplates:
    """Test that all default templates exist."""

    def test_compile_template_exists(self):
        assert "compile" in DEFAULT_TEMPLATES

    def test_extract_concepts_template_exists(self):
        assert "extract_concepts" in DEFAULT_TEMPLATES

    def test_qa_answer_template_exists(self):
        assert "qa_answer" in DEFAULT_TEMPLATES

    def test_all_templates_have_name(self):
        for template_id, info in DEFAULT_TEMPLATES.items():
            assert "name" in info
            assert info["name"]

    def test_all_templates_have_description(self):
        for template_id, info in DEFAULT_TEMPLATES.items():
            assert "description" in info
            assert info["description"]

    def test_all_templates_have_template_text(self):
        for template_id, info in DEFAULT_TEMPLATES.items():
            assert "template" in info
            assert len(info["template"]) > 10


class TestPromptTemplates:
    """Test PromptTemplates class methods."""

    def test_compile_document_returns_string(self):
        result = PromptTemplates.compile_document(
            title="Test",
            type="web",
            source="http://example.com",
            source_id="abc",
            original_title="Original",
            content="Some content here",
        )
        assert isinstance(result, str)
        assert "Test" in result
        assert "Some content here" in result

    def test_extract_concepts_returns_string(self):
        result = PromptTemplates.extract_concepts(
            content="Python is a programming language",
        )
        assert isinstance(result, str)
        assert "Python" in result

    def test_qa_answer_returns_string(self):
        result = PromptTemplates.qa_answer(
            question="What is Python?",
            sources="Python is a high-level programming language.",
            source_ids=["doc-1"],
            titles=["Python Intro"],
        )
        assert isinstance(result, str)
        assert "What is Python?" in result
