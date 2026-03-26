# DocumentShredder
> **Status:** 🔬 IN PROGRESS

## What It Is
Universal document ingestion pipeline. Takes messy real-world files (PDFs, Word docs, Excel sheets, screenshots, ChatGPT exports) and converts them into perfectly structured, clean Markdown chunks ready for AI consumption.

## Why It Matters
You take ChatGPT suggestions and give them to your project manager, but the AI gets confused by the format. DocumentShredder pre-digests that content into a canonical format every downstream AI can understand instantly.

## The Core Problem It Solves
```
Raw ChatGPT export HTML  ──┐
Scanned PDF with tables   ──┤→  DocumentShredder  →  Clean Markdown chunks
Excel with pivot tables   ──┤                         (ready for RAG / LLM)
Screenshot of a diagram   ──┘
```

## How It Works

### Pipeline Stages
```
1. DETECT     → Sniff file type (PDF, DOCX, XLSX, HTML, PNG)
2. EXTRACT    → Route to correct parser
3. NORMALIZE  → Convert tables → Markdown tables, charts → captions
4. CHUNK      → Split into semantic units (≤ 512 tokens each)
5. TAG        → Auto-label chunks (type: table, code, prose, list)
6. EMIT       → Output JSONL, Markdown, or direct Qdrant upsert
```

### Parser Map
| Input | Engine |
|---|---|
| PDF (text) | PyMuPDF / pdfplumber |
| PDF (scanned) | Tesseract OCR |
| Word (DOCX) | python-docx |
| Excel (XLSX) | openpyxl → Markdown tables |
| HTML export | BeautifulSoup → stripped Markdown |
| Image/Diagram | LLaVA / Moondream caption |
| ChatGPT HTML | Custom parser → clean Q&A pairs |

### Output Format
```json
{
  "source": "chatgpt_export.html",
  "chunk_id": 12,
  "type": "code",
  "content": "```python\ndef main():\n    pass\n```",
  "tokens": 18,
  "tags": ["python", "code"]
}
```

## Integration Points
- `AiOSKernel` → any agent can call `shred(filepath)` as a tool
- `SemanticCache` → chunked output cached for reuse
- `PromptOS` → direct RAG ingestion

## Roadmap
- [ ] Core parser routing engine
- [ ] ChatGPT HTML export parser (priority!)
- [ ] Excel → Markdown table converter
- [ ] Semantic chunker (sentence-aware splits)
- [ ] Direct Qdrant upsert mode
