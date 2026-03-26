"""Tests for ner_extraction module."""
import pytest
from ner_extraction import (
    NERExtractor,
    RegexNERExtractor,
    ExtractionResult,
    Entity,
    EntityType,
    NERPipeline,
    create_ner_extractor,
)


class TestEntity:
    """Test Entity dataclass."""

    def test_entity_creation(self):
        """Test creating an Entity."""
        entity = Entity(
            text="John",
            entity_type="PERSON",
            confidence=0.95,
        )
        assert entity.text == "John"
        assert entity.entity_type == "PERSON"


class TestExtractionResult:
    """Test ExtractionResult dataclass."""

    def test_result_creation(self):
        """Test creating an ExtractionResult."""
        result = ExtractionResult(
            text="John lives in Boston",
            entities=[
                Entity(text="John", entity_type="PERSON"),
                Entity(text="Boston", entity_type="LOCATION"),
            ],
        )
        assert len(result.entities) == 2


class TestRegexNERExtractor:
    """Test RegexNERExtractor."""

    def test_extract_email(self):
        """Test email extraction."""
        extractor = RegexNERExtractor()
        result = extractor.extract("Contact me at john@example.com please")
        emails = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(emails) >= 1
        assert "john@example.com" in [e.text for e in emails]

    def test_extract_url(self):
        """Test URL extraction."""
        extractor = RegexNERExtractor()
        result = extractor.extract("Visit https://example.com for more")
        urls = [e for e in result.entities if e.entity_type == "URL"]
        assert len(urls) >= 1

    def test_extract_phone(self):
        """Test phone number extraction."""
        extractor = RegexNERExtractor()
        result = extractor.extract("Call 555-123-4567 today")
        phones = [e for e in result.entities if e.entity_type == "PHONE"]
        assert len(phones) >= 1

    def test_extract_ip_address(self):
        """Test IP address extraction."""
        extractor = RegexNERExtractor()
        result = extractor.extract("Server at 192.168.1.1 is running")
        ips = [e for e in result.entities if e.entity_type == "IP_ADDRESS"]
        assert len(ips) >= 1

    def test_extract_date(self):
        """Test date extraction."""
        extractor = RegexNERExtractor()
        result = extractor.extract("Meeting on 12/25/2024")
        dates = [e for e in result.entities if e.entity_type == "DATE_TIME"]
        assert len(dates) >= 1

    def test_extract_batch(self):
        """Test batch extraction."""
        extractor = RegexNERExtractor()
        texts = ["Email john@test.com", "Visit https://example.com"]
        results = extractor.extract_batch(texts)
        assert len(results) == 2


class TestNERPipeline:
    """Test NERPipeline."""

    def test_pipeline_with_single_extractor(self):
        """Test pipeline with single extractor."""
        pipeline = NERPipeline()
        result = pipeline.extract("Contact john@test.com")
        assert len(result.entities) >= 1

    def test_pipeline_with_multiple_extractors(self):
        """Test pipeline with multiple extractors."""
        pipeline = NERPipeline([RegexNERExtractor(), RegexNERExtractor()])
        result = pipeline.extract("Email test@example.com")
        emails = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(emails) >= 1

    def test_pipeline_deduplication(self):
        """Test that pipeline deduplicates entities."""
        pipeline = NERPipeline([RegexNERExtractor(), RegexNERExtractor()])
        result = pipeline.extract("john@test.com and JOHN@TEST.COM")
        emails = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(emails) <= 2


class TestCreateNERExtractor:
    """Test create_ner_extractor factory function."""

    def test_create_regex_extractor(self):
        """Test creating regex extractor."""
        extractor = create_ner_extractor("regex")
        assert isinstance(extractor, RegexNERExtractor)

    def test_invalid_extractor_type(self):
        """Test error for invalid extractor type."""
        with pytest.raises(ValueError):
            create_ner_extractor("invalid_type")
