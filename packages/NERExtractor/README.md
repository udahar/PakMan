# NER Extraction Module

Named Entity Recognition with support for multiple backends.

## Quick Start

```python
from modules.ner_extraction import RegexNERExtractor, create_ner_extractor

# Regex-based extraction
extractor = RegexNERExtractor()
result = extractor.extract("Email: test@example.com")

# spaCy-based (requires spacy)
extractor = create_ner_extractor("spacy")
result = extractor.extract("Bill Gates works at Microsoft.")
```

## Components

- **RegexNERExtractor** - Rule-based regex patterns
- **SimpleNLPNERExtractor** - spaCy NER
- **AzureLanguageNERExtractor** - Azure Language integration
- **PakmanNERExtractor** - Pakman NLP API
- **NERPipeline** - Chain multiple extractors

## Supported Entity Types

PERSON, LOCATION, ORGANIZATION, DATE_TIME, QUANTITY, URL, EMAIL, PHONE, IP_ADDRESS
