# NLP Text Processing Module

Tokenization, stop word removal, normalization, N-grams, stemming, lemmatization.

## Quick Start

```python
from modules.nlp_text_processing import Tokenizer, StopWordFilter, process_text

# Simple tokenization
tokenizer = Tokenizer(lowercase=True)
tokens = tokenizer.tokenize("Hello world!")

# Full pipeline
result = process_text("Natural language processing is amazing!", remove_stop=True, stem=True)
```
