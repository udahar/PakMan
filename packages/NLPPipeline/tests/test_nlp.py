"""Tests for nlp_text_processing module."""
import pytest
from nlp_text_processing import (
    TextNormalizer,
    Tokenizer,
    StopWordFilter,
    NGramExtractor,
    Stemmer,
    Lemmatizer,
    SentimentAnalyzer,
    KeyPhraseExtractor,
    LanguageDetector,
    process_text,
)


class TestTextNormalizer:
    """Test TextNormalizer."""

    def test_lowercase(self):
        """Test lowercase conversion."""
        result = TextNormalizer.lowercase("Hello World")
        assert result == "hello world"

    def test_remove_punctuation(self):
        """Test punctuation removal."""
        result = TextNormalizer.remove_punctuation("Hello, World!")
        assert result == "Hello World"

    def test_normalize(self):
        """Test full normalization."""
        result = TextNormalizer.normalize("Hello, World!")
        assert result == "hello world"


class TestTokenizer:
    """Test Tokenizer."""

    def test_tokenize(self):
        """Test basic tokenization."""
        tokenizer = Tokenizer(lowercase=True)
        tokens = tokenizer.tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_tokenize_preserves_case(self):
        """Test tokenization without lowercasing."""
        tokenizer = Tokenizer(lowercase=False)
        tokens = tokenizer.tokenize("Hello World")
        assert tokens == ["Hello", "World"]

    def test_tokenize_with_position(self):
        """Test tokenization with positions."""
        tokenizer = Tokenizer(lowercase=True)
        tokens_pos = tokenizer.tokenize_with_position("Hello World")
        assert len(tokens_pos) == 2


class TestStopWordFilter:
    """Test StopWordFilter."""

    def test_filter(self):
        """Test stop word filtering."""
        filter = StopWordFilter()
        tokens = ["the", "quick", "brown", "fox"]
        filtered = filter.filter(tokens)
        assert "the" not in filtered

    def test_add_stop_words(self):
        """Test adding custom stop words."""
        filter = StopWordFilter()
        filter.add_stop_words(["quick"])
        tokens = ["the", "quick", "brown"]
        filtered = filter.filter(tokens)
        assert "quick" not in filtered


class TestNGramExtractor:
    """Test NGramExtractor."""

    def test_extract_bigrams(self):
        """Test bigram extraction."""
        tokens = ["the", "quick", "brown", "fox"]
        bigrams = NGramExtractor.extract_ngrams(tokens, 2)
        assert len(bigrams) == 3
        assert ("the", "quick") in bigrams

    def test_extract_all(self):
        """Test extracting all n-grams."""
        tokens = ["a", "b", "c"]
        all_ngrams = NGramExtractor.extract_all(tokens, max_n=2)
        assert 1 in all_ngrams
        assert 2 in all_ngrams


class TestStemmer:
    """Test Stemmer."""

    def test_stem(self):
        """Test stemming."""
        stemmer = Stemmer()
        result = stemmer.stem("running")
        assert result in ["run", "running"]


class TestLemmatizer:
    """Test Lemmatizer."""

    def test_lemmatize(self):
        """Test lemmatization."""
        lemmatizer = Lemmatizer()
        result = lemmatizer.lemmatize("running")
        assert len(result) > 0


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer."""

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This is amazing and wonderful!")
        assert result["document_sentiment"] in ["positive", "mixed"]

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This is terrible and awful.")
        assert result["document_sentiment"] in ["negative", "mixed"]

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("The file is on the desk.")
        assert "document_sentiment" in result

    def test_mixed_sentiment(self):
        """Test mixed sentiment detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("The food was great but the service was terrible!")
        assert "document_sentiment" in result
        assert "sentences" in result


class TestKeyPhraseExtractor:
    """Test KeyPhraseExtractor."""

    def test_extract(self):
        """Test key phrase extraction."""
        extractor = KeyPhraseExtractor(max_phrases=5)
        text = "Azure Language provides NLP services for sentiment analysis and text processing"
        phrases = extractor.extract(text)
        assert len(phrases) <= 5

    def test_extract_with_scores(self):
        """Test key phrase extraction with scores."""
        extractor = KeyPhraseExtractor()
        phrases_scores = extractor.extract_with_scores("Python programming is great for data science")
        assert len(phrases_scores) > 0


class TestLanguageDetector:
    """Test LanguageDetector."""

    def test_detect_english(self):
        """Test English detection."""
        detector = LanguageDetector()
        result = detector.detect("The quick brown fox jumps over the lazy dog")
        assert result["language"] == "en"

    def test_detect_french(self):
        """Test French detection."""
        detector = LanguageDetector()
        result = detector.detect("Le chat est sur la table")
        assert result["language"] == "fr"

    def test_detect_german(self):
        """Test German detection."""
        detector = LanguageDetector()
        result = detector.detect("Der Hund ist im Garten")
        assert result["language"] == "de"

    def test_detect_unknown(self):
        """Test unknown language handling."""
        detector = LanguageDetector()
        result = detector.detect("xyz abc")
        assert "confidence" in result


class TestProcessText:
    """Test process_text convenience function."""

    def test_process_text(self):
        """Test full text processing."""
        result = process_text("Hello, World! The quick brown fox.")
        assert "original" in result
        assert "tokens" in result
        assert "filtered_tokens" in result
