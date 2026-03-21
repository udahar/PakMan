## 🐰 SupDoc — Runtime Documentation Engine

“Eh… what’s up, Doc?”

SupDoc is the self-documenting layer of the Alfred ecosystem.
It automatically analyzes skills, extracts intent, and generates structured documentation.

Originally built as AutoDoc, SupDoc now acts as a continuous documentation system
that turns skills into readable, categorized, and usable knowledge.

---

## What it does

- 🧠 Analyzes skill prompts to detect purpose and category
- 🏷️ Classifies capabilities (coding, analysis, research, etc.)
- 📊 Estimates complexity
- 🔍 Extracts inputs and outputs automatically
- 🧾 Generates clean, structured documentation\

# Auto-Doc - Generate Skill Documentation

Auto-document what each skill does.

## Usage

```python
from auto_doc import AutoDoc

doc = AutoDoc()

# Generate docs for specific skill
skill_doc = doc.generate("humble_inquiry")

# Generate for all skills in a directory
all_docs = doc.generate_all("/path/to/skills")
```

## Features

- **Prompt Analysis** - Understand what skill does
- **Auto-Summarization** - Generate descriptions
- **Example Generation** - Create usage examples

## Status

✅ Production Ready


---

## 🥕 SupDoc Behavior

- “Eh… looks like this one’s a coding skill.”
- “Simple job, Doc. Nothing fancy.”
- “This one’s complex… might wanna keep an eye on it.”

SupDoc doesn’t just document skills.
It figures out what they are… and tells the story.