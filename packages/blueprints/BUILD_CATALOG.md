# Build Catalog - Auto-Learning Build Prompts

**The Problem:** You build things repeatedly. Each time, you start from scratch.

**The Solution:** System remembers what worked, merges patterns, suggests better prompts.

---

## How It Works

### 1. You Build Something

```
You: "Build a Rust CLI tool"
AI: [Creates great solution]
You: [Rate it 5 stars]
```

### 2. System Learns

```python
catalog.record_build(
    what_built="Rust CLI tool",
    conversation=conversation,
    quality_rating=0.95,
)
```

### 3. Next Time, It's Smarter

```
You: "Build a Rust web service"

System generates enhanced prompt:
"Build this: Rust web service

Based on 3 similar successful builds:
1. Use actix-web for performance
2. Structure with separate crates
3. Add proper error handling with thiserror

Use these proven approaches..."
```

---

## Usage

```python
from blueprints.build_catalog import BuildCatalog

catalog = BuildCatalog()

# Record a build
catalog.record_build(
    what_built="Python API client",
    conversation=messages,
    quality_rating=0.9,
    tags=["python", "api"],
)

# Next time, generate enhanced prompt
prompt = catalog.generate_build_prompt("Build Python REST client")

# Uses learnings from similar builds!
```

---

## What Gets Tracked

| Field | Description |
|-------|-------------|
| `what_built` | What you asked to build |
| `initial_prompt` | Your first request |
| `ai_approach` | How AI approached it |
| `successful_prompts` | Prompts that worked |
| `failed_prompts` | What didn't work |
| `build_quality` | Your rating (0-1) |
| `tags` | Auto-generated categories |

---

## Pattern Merging

System automatically merges similar builds:

```
Tag: "rust"
├─ Build 1: CLI tool (quality: 0.9)
├─ Build 2: Web service (quality: 0.85)
├─ Build 3: Parser (quality: 0.95)
└─ Merged Pattern:
   ├─ Common approaches: [cargo init, clap, serde]
   ├─ Avg quality: 0.90
   └─ Best practices: [error handling, testing, docs]
```

---

## Integration with AI Systems

```python
# In your AI system
from blueprints.build_catalog import BuildCatalog

catalog = BuildCatalog()

def build_something(request):
    # Generate enhanced prompt from history
    prompt = catalog.generate_build_prompt(request)
    
    # Send to AI
    response = call_ai(prompt)
    
    # Record the conversation
    catalog.record_build(
        what_built=request,
        conversation=conversation,
        quality_rating=user_rating,
    )
    
    return response
```

---

## Benefits

### 1. No More Starting From Scratch
- Every build makes future builds easier
- System accumulates wisdom

### 2. Automatic Best Practices
- Merges successful approaches
- Filters out what didn't work

### 3. Debugging Aid
- See what prompts worked before
- Avoid repeating mistakes

### 4. Design Assistance
- "Based on 5 similar builds, here's the pattern"
- Suggests approaches you might not think of

---

## Example Output

```
Query: "Build a Python data pipeline"

Enhanced Prompt:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Build this: Python data pipeline

Based on 4 similar successful builds:

1. Use pandas for data transformation
2. Add proper logging with structlog
3. Implement retry logic for API calls
4. Use Pydantic for data validation
5. Add unit tests with pytest

Common patterns:
- Error handling: try/except with logging
- Testing: pytest with fixtures
- Documentation: docstrings + README

Use these proven approaches. Focus on quality.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Commands

```python
# Record build
catalog.record_build(what, conversation, quality)

# Find similar builds
similar = catalog.find_similar_builds("Rust CLI")

# Get best practices
practices = catalog.get_best_practices("rust")

# Generate enhanced prompt
prompt = catalog.generate_build_prompt("Build Rust tool")

# Stats
stats = catalog.get_stats()
```

---

**This is your build memory.** 🧠

The more you build, the smarter it gets.
