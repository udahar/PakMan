"""
NLP Text Processing Module

Core NLP utilities for text analysis including:
- Tokenization
- Stop word removal
- Text normalization
- N-gram extraction
- Stemming and Lemmatization
- POS tagging

Based on Azure Language concepts and NLP fundamentals.
"""

import logging
from typing import List, Set, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Default English stop words
DEFAULT_STOP_WORDS: Set[str] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "its",
    "our",
    "their",
    "this",
    "that",
    "these",
    "those",
    "in",
    "on",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "if",
    "then",
    "else",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "now",
    "here",
    "there",
    "of",
    "as",
}


class TextNormalizer:
    """Normalize text for analysis."""

    @staticmethod
    def lowercase(text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()

    @staticmethod
    def remove_punctuation(text: str) -> str:
        """Remove punctuation from text."""
        import string

        return text.translate(str.maketrans("", "", string.punctuation))

    @staticmethod
    def normalize(text: str, lowercase: bool = True, remove_punct: bool = True) -> str:
        """Apply all normalization steps."""
        if lowercase:
            text = TextNormalizer.lowercase(text)
        if remove_punct:
            text = TextNormalizer.remove_punctuation(text)
        return text


class Tokenizer:
    """Split text into tokens."""

    def __init__(self, lowercase: bool = True):
        self.lowercase = lowercase

    def tokenize(self, text: str) -> List[str]:
        """Split text into word tokens."""
        if self.lowercase:
            text = text.lower()
        return text.split()

    def tokenize_with_position(self, text: str) -> List[Tuple[str, int]]:
        """Return tokens with their starting positions."""
        normalized = text.lower() if self.lowercase else text
        tokens = normalized.split()
        positions = []
        pos = 0
        for token in tokens:
            start = normalized.find(token, pos)
            positions.append((token, start))
            pos = start + len(token)
        return positions


class StopWordFilter:
    """Filter stop words from tokens."""

    def __init__(self, stop_words: Set[str] = None):
        self.stop_words = stop_words or DEFAULT_STOP_WORDS

    def filter(self, tokens: List[str]) -> List[str]:
        """Remove stop words from token list."""
        return [t for t in tokens if t.lower() not in self.stop_words]

    def add_stop_words(self, words: List[str]) -> None:
        """Add words to stop word set."""
        self.stop_words.update(w.lower() for w in words)

    def remove_stop_words(self, words: List[str]) -> None:
        """Remove words from stop word set."""
        self.stop_words.difference_update(w.lower() for w in words)


class NGramExtractor:
    """Extract n-grams (bigrams, trigrams, etc.) from tokens."""

    @staticmethod
    def extract_ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
        """Extract all n-grams of size n."""
        if n < 1 or n > len(tokens):
            return []
        return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]

    @staticmethod
    def extract_all(
        tokens: List[str], max_n: int = 3
    ) -> Dict[int, List[Tuple[str, ...]]]:
        """Extract n-grams for all sizes from 1 to max_n."""
        return {
            n: NGramExtractor.extract_ngrams(tokens, n) for n in range(1, max_n + 1)
        }


class Stemmer:
    """Stem words to their root form using Porter stemmer."""

    def __init__(self):
        try:
            from nltk.stem import PorterStemmer

            self.stemmer = PorterStemmer()
        except ImportError:
            self.stemmer = None

    def stem(self, word: str) -> str:
        """Stem a single word."""
        if self.stemmer:
            return self.stemmer.stem(word)
        # Simple fallback: just lowercase
        return word.lower()

    def stem_batch(self, words: List[str]) -> List[str]:
        """Stem a list of words."""
        return [self.stem(w) for w in words]


class Lemmatizer:
    """Lemmatize words to their dictionary form."""

    def __init__(self):
        try:
            from nltk.stem import WordNetLemmatizer

            self.lemmatizer = WordNetLemmatizer()
        except ImportError:
            self.lemmatizer = None

    def lemmatize(self, word: str, pos: str = "n") -> str:
        """Lemmatize a single word."""
        if self.lemmatizer:
            try:
                return self.lemmatizer.lemmatize(word, pos)
            except Exception:
                logger.warning("NLTK wordnet not available, using lowercase")
                return word.lower()
        return word.lower()

    def lemmatize_batch(self, words: List[str], pos: str = "n") -> List[str]:
        """Lemmatize a list of words."""
        return [self.lemmatize(w, pos) for w in words]


class POSTagger:
    """Part-of-speech tagger."""

    def __init__(self):
        try:
            import nltk

            self.tagger = nltk.pos_tag
        except ImportError:
            self.tagger = None

    def tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """Tag tokens with POS labels."""
        if self.tagger:
            return self.tagger(tokens)
        # Fallback: return token with 'NN' (noun)
        return [(t, "NN") for t in tokens]

    POS_LABELS = {
        "NN": "noun",
        "NNS": "noun (plural)",
        "NNP": "proper noun",
        "VB": "verb",
        "VBD": "verb (past)",
        "VBG": "verb (gerund)",
        "JJ": "adjective",
        "JJR": "adj (comparative)",
        "JJS": "adj (superlative)",
        "RB": "adverb",
        "RBR": "adv (comparative)",
        "RBS": "adv (superlative)",
    }


class SentimentAnalyzer:
    """
    Rule-based sentiment analysis with opinion mining.

    Scores text as positive/negative/neutral with per-sentence breakdown.
    Based on Azure Language sentiment analysis concepts.

    Usage:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("The food was amazing but the service was terrible.")
        print(result['document_sentiment'])   # 'mixed'
        print(result['sentences'])            # per-sentence breakdown
    """

    POSITIVE_WORDS = {
        "good",
        "great",
        "excellent",
        "amazing",
        "wonderful",
        "fantastic",
        "love",
        "best",
        "perfect",
        "happy",
        "beautiful",
        "awesome",
        "outstanding",
        "superb",
        "brilliant",
        "enjoy",
        "nice",
        "pleased",
        "impressive",
        "exceptional",
        "delicious",
        "terrific",
        "helpful",
        "recommend",
        "satisfied",
        "friendly",
        "efficient",
        "fast",
        "clean",
        "reliable",
        "professional",
        "quality",
        "superior",
        "elegant",
        "intuitive",
        "smooth",
        "powerful",
        "innovative",
        "easy",
    }

    NEGATIVE_WORDS = {
        "bad",
        "terrible",
        "awful",
        "horrible",
        "worst",
        "hate",
        "poor",
        "disappointing",
        "fail",
        "broken",
        "slow",
        "ugly",
        "useless",
        "annoying",
        "frustrating",
        "expensive",
        "difficult",
        "complicated",
        "confusing",
        "unreliable",
        "unprofessional",
        "rude",
        "dirty",
        "overpriced",
        "mediocre",
        "boring",
        "outdated",
        "clunky",
        "avoid",
        "never",
        "waste",
        "regret",
        "pathetic",
        "disgusting",
        "nightmare",
        "disaster",
        "scam",
        "fraud",
    }

    NEGATORS = {
        "not",
        "n't",
        "no",
        "never",
        "neither",
        "nor",
        "hardly",
        "barely",
        "scarcely",
    }

    INTENSIFIERS = {
        "very",
        "extremely",
        "incredibly",
        "absolutely",
        "totally",
        "really",
        "so",
        "highly",
    }

    def __init__(self, pos_words=None, neg_words=None):
        logger.debug("Initializing SentimentAnalyzer")
        self.pos_words = pos_words or self.POSITIVE_WORDS
        self.neg_words = neg_words or self.NEGATIVE_WORDS

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Returns dict with:
        - document_sentiment: 'positive', 'negative', 'neutral', or 'mixed'
        - document_scores: {'positive': float, 'negative': float, 'neutral': float}
        - sentences: list of per-sentence analysis
        """
        sentences = self._split_sentences(text)
        sent_results = []

        pos_total = 0.0
        neg_total = 0.0

        for sent in sentences:
            scores = self._score_sentence(sent)
            sent_results.append(scores)
            pos_total += scores["positive"]
            neg_total += scores["negative"]

        n = len(sentences) if sentences else 1
        pos_avg = pos_total / n
        neg_avg = neg_total / n
        neutral_avg = max(0, 1.0 - pos_avg - neg_avg)

        # Document-level sentiment
        if abs(pos_avg - neg_avg) < 0.1 and pos_avg > 0.1:
            doc_sentiment = "mixed"
        elif pos_avg > neg_avg:
            doc_sentiment = "positive"
        elif neg_avg > pos_avg:
            doc_sentiment = "negative"
        else:
            doc_sentiment = "neutral"

        logger.debug(f"Sentiment analysis result: {doc_sentiment}")
        return {
            "document_sentiment": doc_sentiment,
            "document_scores": {
                "positive": round(pos_avg, 3),
                "negative": round(neg_avg, 3),
                "neutral": round(neutral_avg, 3),
            },
            "sentences": sent_results,
        }

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re

        parts = re.split(r"[.!?]+", text)
        return [s.strip() for s in parts if s.strip()]

    def _score_sentence(self, sentence: str) -> Dict[str, Any]:
        """Score a single sentence."""
        tokens = sentence.lower().split()
        pos_score = 0.0
        neg_score = 0.0
        negated = False

        for i, token in enumerate(tokens):
            # Check for negation
            if token in self.NEGATORS or token.endswith("n't"):
                negated = True
                continue

            # Check for intensifier
            intensifier = 1.5 if (i > 0 and tokens[i - 1] in self.INTENSIFIERS) else 1.0

            # Score the token
            if token in self.pos_words:
                if negated:
                    neg_score += 0.5 * intensifier
                else:
                    pos_score += 0.5 * intensifier
                negated = False
            elif token in self.neg_words:
                if negated:
                    pos_score += 0.3 * intensifier
                else:
                    neg_score += 0.5 * intensifier
                negated = False
            else:
                # Negation scope resets after 3 words
                if negated and i > 0:
                    negated = False

        total = pos_score + neg_score
        if total > 0:
            pos_norm = pos_score / total
            neg_norm = neg_score / total
        else:
            pos_norm = 0.0
            neg_norm = 0.0

        if pos_norm > neg_norm:
            label = "positive"
        elif neg_norm > pos_norm:
            label = "negative"
        else:
            label = "neutral"

        return {
            "text": sentence,
            "sentiment": label,
            "positive": round(pos_norm, 3),
            "negative": round(neg_norm, 3),
            "neutral": round(max(0, 1.0 - pos_norm - neg_norm), 3),
        }


class KeyPhraseExtractor:
    """
    Extract key phrases from text using statistical and linguistic heuristics.

    Based on Azure Language key phrase extraction concepts.

    Usage:
        extractor = KeyPhraseExtractor()
        phrases = extractor.extract("Azure Language provides NLP services for sentiment analysis.")
        # ['Azure Language', 'NLP services', 'sentiment analysis']
    """

    def __init__(self, max_phrases: int = 10, min_word_length: int = 3):
        self.max_phrases = max_phrases
        self.min_word_length = min_word_length
        self._stop_words = None

    def extract(self, text: str) -> List[str]:
        """
        Extract key phrases from text.

        Returns list of key phrases ranked by importance.
        """
        import re

        # Tokenize
        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(text)

        # Get stop words
        if self._stop_words is None:
            self._stop_words = StopWordFilter().stop_words

        # Extract candidate noun phrases (sequences of non-stop words)
        candidates = self._extract_candidate_phrases(tokens)

        # Score candidates
        scored = self._score_candidates(candidates, tokens)

        # Return top phrases
        scored.sort(key=lambda x: x[1], reverse=True)
        return [phrase for phrase, score in scored[: self.max_phrases]]

    def _extract_candidate_phrases(self, tokens: List[str]) -> List[str]:
        """Extract candidate phrases from tokens."""
        candidates = []
        current_phrase = []

        for token in tokens:
            clean = token.lower().strip(".,;:!?()[]\"'")
            if len(clean) < self.min_word_length or clean in self._stop_words:
                if current_phrase:
                    candidates.append(" ".join(current_phrase))
                    current_phrase = []
            else:
                current_phrase.append(clean)

        if current_phrase:
            candidates.append(" ".join(current_phrase))

        return candidates

    def _score_candidates(
        self, candidates: List[str], all_tokens: List[str]
    ) -> List[Tuple[str, float]]:
        """Score candidate phrases by frequency and word importance."""
        from collections import Counter

        # Count word frequencies
        clean_tokens = [t.lower().strip(".,;:!?()[]\"'") for t in all_tokens]
        word_freq = Counter(clean_tokens)
        total_tokens = len(clean_tokens)

        # Score each candidate phrase
        scored = []
        seen = set()

        for phrase in candidates:
            if phrase in seen:
                continue
            seen.add(phrase)

            words = phrase.split()
            # Score = sum of IDF-like weights
            score = sum(1.0 / (word_freq.get(w, 1) / total_tokens) for w in words)
            # Normalize by phrase length (favor shorter, dense phrases)
            score = score / (len(words) ** 0.5)

            scored.append((phrase, score))

        return scored

    def extract_with_scores(self, text: str) -> List[Tuple[str, float]]:
        """Extract key phrases with their importance scores."""
        import re

        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(text)

        if self._stop_words is None:
            self._stop_words = StopWordFilter().stop_words

        candidates = self._extract_candidate_phrases(tokens)
        scored = self._score_candidates(candidates, tokens)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[: self.max_phrases]


class LanguageDetector:
    """
    Detect the language of text.

    Uses character n-gram profiles for language identification.
    Based on Azure Language detection concepts.

    Usage:
        detector = LanguageDetector()
        result = detector.detect("Bonjour le monde")
        # {'language': 'fr', 'name': 'French', 'confidence': 0.95}
    """

    # Common words per language (high-frequency function words)
    LANGUAGE_MARKERS = {
        "en": {
            "the",
            "is",
            "are",
            "was",
            "were",
            "have",
            "has",
            "been",
            "this",
            "that",
            "with",
            "from",
            "they",
            "been",
            "will",
            "would",
            "could",
            "should",
            "not",
            "but",
            "and",
            "for",
            "you",
            "all",
            "can",
            "had",
            "her",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "its",
            "may",
            "new",
            "now",
            "old",
            "see",
            "way",
            "who",
            "did",
        },
        "fr": {
            "le",
            "la",
            "les",
            "de",
            "des",
            "du",
            "et",
            "est",
            "en",
            "que",
            "qui",
            "dans",
            "pour",
            "pas",
            "sur",
            "une",
            "avec",
            "tout",
            "fait",
            "sont",
            "nous",
            "vous",
            "ils",
            "elle",
            "mais",
            "plus",
            "aussi",
            "comme",
            "quand",
            "tres",
            "bien",
            "etre",
            "avoir",
            "fait",
            "leur",
            "ces",
        },
        "es": {
            "el",
            "la",
            "los",
            "las",
            "de",
            "del",
            "en",
            "es",
            "que",
            "por",
            "con",
            "para",
            "una",
            "como",
            "pero",
            "todo",
            "esta",
            "son",
            "muy",
            "mas",
            "tambien",
            "nos",
            "les",
            "sus",
            "hay",
            "ser",
            "fue",
            "tiene",
            "puede",
            "donde",
            "este",
            "esto",
            "cuando",
            "entre",
            "sobre",
            "desde",
            "hasta",
            "mucho",
        },
        "de": {
            "der",
            "die",
            "das",
            "den",
            "dem",
            "des",
            "und",
            "ist",
            "ein",
            "eine",
            "einer",
            "eines",
            "auf",
            "mit",
            "fur",
            "von",
            "sich",
            "nicht",
            "auch",
            "als",
            "wie",
            "aber",
            "oder",
            "wenn",
            "noch",
            "nach",
            "nur",
            "vor",
            "zum",
            "zur",
            "bei",
            "uber",
            "unter",
            "aus",
            "bis",
            "durch",
            "ohne",
            "um",
            "sehr",
            "mehr",
            "schon",
            "kann",
            "hat",
            "war",
            "werden",
        },
        "it": {
            "il",
            "lo",
            "la",
            "le",
            "gli",
            "di",
            "del",
            "della",
            "dei",
            "delle",
            "e",
            "che",
            "non",
            "si",
            "un",
            "una",
            "per",
            "con",
            "sono",
            "come",
            "piu",
            "anche",
            "alla",
            "dal",
            "nel",
            "alla",
            "questo",
            "quello",
            "tutto",
            "molto",
            "bene",
            "cosi",
            "dove",
            "quando",
            "perche",
            "ogni",
            "altro",
            "prima",
            "dopo",
            "sempre",
        },
        "pt": {
            "o",
            "a",
            "os",
            "as",
            "de",
            "do",
            "da",
            "dos",
            "das",
            "em",
            "no",
            "na",
            "nos",
            "nas",
            "e",
            "que",
            "um",
            "uma",
            "para",
            "com",
            "por",
            "como",
            "mas",
            "mais",
            "nao",
            "se",
            "foi",
            "sao",
            "tem",
            "pode",
            "esta",
            "este",
            "isso",
            "aquilo",
            "muito",
            "bem",
            "onde",
            "quando",
            "porque",
            "tambem",
            "ainda",
            "ja",
            "so",
            "ate",
        },
        "nl": {
            "de",
            "het",
            "een",
            "van",
            "in",
            "is",
            "dat",
            "op",
            "te",
            "en",
            "voor",
            "met",
            "zijn",
            "die",
            "niet",
            "ook",
            "maar",
            "om",
            "als",
            "dan",
            "nog",
            "bij",
            "uit",
            "al",
            "naar",
            "zo",
            "over",
            "kan",
            "meer",
            "geen",
            "wel",
            "dit",
            "wat",
            "zeer",
            "waar",
            "hoe",
            "wie",
            "waarom",
        },
        "pl": {
            "nie",
            "si",
            "jest",
            "na",
            "do",
            "ze",
            "za",
            "co",
            "jak",
            "ale",
            "od",
            "po",
            "przez",
            "przy",
            "bez",
            "nad",
            "pod",
            "przed",
            "bardzo",
            "tak",
            "tylko",
            "jeszcze",
            "juz",
            "moze",
            "jednak",
            "tego",
            "ktory",
            "ktora",
            "ktore",
        },
        "ru": {
            "не",
            "на",
            "я",
            "что",
            "то",
            "все",
            "он",
            "как",
            "а",
            "но",
            "да",
            "ты",
            "у",
            "за",
            "с",
            "же",
            "ну",
            "вы",
            "бы",
            "по",
            "только",
            "ее",
            "мне",
            "было",
            "вот",
            "от",
            "меня",
            "еще",
            "нет",
            "о",
            "из",
            "ему",
            "теперь",
            "когда",
            "даже",
            "ведь",
            "если",
        },
        "zh": {
            "的",
            "是",
            "在",
            "了",
            "不",
            "和",
            "有",
            "大",
            "这",
            "中",
            "人",
            "为",
            "们",
            "我",
            "到",
            "他",
            "会",
            "来",
            "上",
            "个",
            "也",
            "你",
            "就",
            "那",
            "要",
            "她",
            "时",
            "说",
            "对",
            "可以",
            "与",
            "用",
            "都",
            "而",
            "把",
            "被",
        },
        "ja": {
            "の",
            "は",
            "に",
            "を",
            "が",
            "と",
            "で",
            "も",
            "た",
            "て",
            "だ",
            "い",
            "す",
            "る",
            "から",
            "な",
            "し",
            "か",
            "こ",
            "れ",
            "ない",
            "ます",
            "この",
            "ため",
            "その",
            "よう",
            "など",
            "ある",
            "いる",
            "お",
            "よる",
            "なる",
            "できる",
        },
        "ko": {
            "이",
            "가",
            "을",
            "를",
            "에",
            "의",
            "는",
            "은",
            "와",
            "과",
            "도",
            "로",
            "으로",
            "에서",
            "부터",
            "까지",
            "만",
            "보다",
            "처럼",
            "같은",
            "그",
            "저",
            "이것",
            "그것",
            "것",
            "수",
            "등",
            "및",
            "또는",
            "하지만",
            "그리고",
            "그래서",
        },
    }

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of text.

        Returns dict with:
        - language: ISO 639-1 code (e.g., 'en', 'fr')
        - name: Human-readable name
        - confidence: 0-1 confidence score
        """
        import re

        # Clean text
        words = set(re.findall(r"\b\w+\b", text.lower()))

        if not words:
            return {"language": "unknown", "name": "Unknown", "confidence": 0.0}

        # Score each language
        scores = {}
        for lang, markers in self.LANGUAGE_MARKERS.items():
            overlap = len(words & markers)
            scores[lang] = overlap / len(words) if words else 0

        # Get best match
        if not scores or max(scores.values()) == 0:
            # Fall back to character analysis
            return self._detect_by_script(text)

        best_lang = max(scores, key=scores.get)
        confidence = min(scores[best_lang] * 3, 1.0)  # Scale up but cap at 1.0

        lang_names = {
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "pl": "Polish",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
        }

        return {
            "language": best_lang,
            "name": lang_names.get(best_lang, best_lang),
            "confidence": round(confidence, 3),
        }

    def _detect_by_script(self, text: str) -> Dict[str, Any]:
        """Detect language by Unicode script ranges."""
        import re

        # Check for CJK characters
        if re.search(r"[\u4e00-\u9fff]", text):
            if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
                return {"language": "ja", "name": "Japanese", "confidence": 0.8}
            return {"language": "zh", "name": "Chinese", "confidence": 0.7}

        # Korean Hangul
        if re.search(r"[\uac00-\ud7af]", text):
            return {"language": "ko", "name": "Korean", "confidence": 0.8}

        # Cyrillic
        if re.search(r"[\u0400-\u04ff]", text):
            return {"language": "ru", "name": "Russian", "confidence": 0.7}

        # Arabic
        if re.search(r"[\u0600-\u06ff]", text):
            return {"language": "ar", "name": "Arabic", "confidence": 0.7}

        return {"language": "unknown", "name": "Unknown", "confidence": 0.0}


# Convenience function for quick processing
def process_text(
    text: str,
    lowercase: bool = True,
    remove_stop: bool = True,
    stem: bool = False,
    max_ngram: int = 0,
) -> Dict[str, any]:
    """
    Process text through full NLP pipeline.

    Returns dict with:
    - original: original text
    - normalized: normalized text
    - tokens: word tokens
    - filtered_tokens: tokens after stop word removal
    - stems: stemmed tokens (if stem=True)
    - ngrams: n-grams (if max_ngram > 0)
    """
    normalizer = TextNormalizer()
    tokenizer = Tokenizer(lowercase=lowercase)
    stop_filter = StopWordFilter()
    stemmer = Stemmer()
    ngram_extractor = NGramExtractor()

    normalized = normalizer.normalize(text)
    tokens = tokenizer.tokenize(text)
    filtered_tokens = stop_filter.filter(tokens) if remove_stop else tokens
    stems = stemmer.stem_batch(filtered_tokens) if stem else filtered_tokens
    ngrams = (
        ngram_extractor.extract_all(filtered_tokens, max_ngram) if max_ngram > 0 else {}
    )

    return {
        "original": text,
        "normalized": normalized,
        "tokens": tokens,
        "filtered_tokens": filtered_tokens,
        "stems": stems,
        "ngrams": ngrams,
    }
