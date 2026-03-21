# Context Manager - Smart Context Window

**Status:** 📋 Concept - Medium Priority

---

## The Problem

Your AI system has **too much context**:
- 26 skills in PromptSKLib
- Multiple blueprints
- Council roles
- Courtroom context
- StockAI data
- Memory Graph entities
- User preferences
- Conversation history

**Result:**
- Token limits exceeded
- AI gets confused
- Important info buried in noise
- Wasted money on irrelevant tokens

---

## The Solution

A **smart context manager** that:
1. **Scores relevance** - What matters for THIS task?
2. **Auto-prunes** - Drop irrelevant context
3. **Layers memory** - Short-term, long-term, working
4. **Task-based selection** - Different context for different tasks

---

## Architecture

```
context_manager/
├── manager.py           # Core context management
├── relevance.py         # Relevance scoring algorithms
├── layers.py            # Memory layer system
├── selectors.py         # Task-based context selection
├── compressor.py        # Context compression
└── cli.py               # Command-line interface
```

---

## Features

### 1. Relevance Scoring

**Score each piece of context:**

```python
from context_manager import RelevanceScorer

scorer = RelevanceScorer()

# Score context items
scores = scorer.score_all(
    query="Build a Rust CLI tool",
    context_items=[
        ("rust_blueprints", blueprint_data),
        ("council_roles", council_data),
        ("user_prefs", user_preferences),
        ("recent_conversation", conversation),
    ]
)

# Results:
# rust_blueprints: 0.95 ← Highly relevant
# council_roles: 0.30   ← Not relevant now
# user_prefs: 0.60      ← Somewhat relevant
# recent_conversation: 0.75 ← Contextually relevant
```

**Scoring factors:**
- Keyword matching
- Semantic similarity (embeddings)
- Recency
- Usage frequency
- Task type

---

### 2. Auto-Pruning

**Drop irrelevant context automatically:**

```python
from context_manager import ContextManager

ctx = ContextManager(max_tokens=4000)

# Add context
ctx.add("skill_inquiry", inquiry_skill_prompt)
ctx.add("skill_engineering", engineering_skill_prompt)
ctx.add("blueprint_streetpunk", streetpunk_blueprint)
ctx.add("user_preference", "likes concise answers")

# Prune to fit token limit
pruned = ctx.prune(target_tokens=2000)

# Result: Keeps most relevant, drops least relevant
```

**Pruning strategies:**
- **Least relevant first** - Drop low-scoring items
- **Oldest first** - Drop old context
- **Compress first** - Summarize before dropping
- **Layer-based** - Drop from specific layers

---

### 3. Memory Layers

**Organize context by type:**

```python
from context_manager import MemoryLayers

layers = MemoryLayers()

# Short-term (current conversation)
layers.add_to_layer("short_term", "User asked about Rust", ttl=10_minutes)

# Long-term (user preferences, learned info)
layers.add_to_layer("long_term", "User prefers Rust over Python")

# Working (current task context)
layers.add_to_layer("working", "Building Rust CLI tool")

# Skills (relevant skills for task)
layers.add_to_layer("skills", "engineering_skill_prompt")

# Get all, prioritized
context = layers.get_all(max_tokens=4000)
```

**Layer hierarchy:**
1. **Short-term** - Current conversation (expires fast)
2. **Working** - Current task (expires when done)
3. **Skills** - Task-relevant skills (selected dynamically)
4. **Long-term** - User preferences, learned info (persistent)
5. **Reference** - Documentation, blueprints (on-demand)

---

### 4. Task-Based Selection

**Different context for different tasks:**

```python
from context_manager import TaskSelector

selector = TaskSelector()

# For code generation task
context = selector.select_for_task(
    task_type="code_generation",
    query="Build Rust CLI"
)

# Returns:
# - Engineering skill prompts
# - Rust blueprints
# - Code-related context
# - NOT: inquiry skills, unrelated blueprints

# For research task
context = selector.select_for_task(
    task_type="research",
    query="Research quantum computing"
)

# Returns:
# - Inquiry skill prompts
# - Research blueprints
# - Knowledge graph context
```

**Task types:**
- `code_generation`
- `code_review`
- `research`
- `analysis`
- `creative_writing`
- `problem_solving`
- `planning`

---

### 5. Context Compression

**Summarize context to save tokens:**

```python
from context_manager import ContextCompressor

compressor = ContextCompressor(model="qwen2.5:7b")

# Compress long context
long_context = "..."  # 2000 tokens

compressed = compressor.compress(
    long_context,
    target_tokens=500,
    preserve=["key_facts", "decisions", "action_items"]
)

# Result: 500 tokens, key info preserved
```

**Compression strategies:**
- **Summarize** - LLM generates summary
- **Extract** - Pull key sentences
- **Template** - Fill structured template
- **Hierarchical** - Summary + details on-demand

---

## Usage

### Basic

```python
from context_manager import ContextManager

ctx = ContextManager(max_tokens=4000)

# Add context
ctx.add("user_name", "Richard")
ctx.add("preference", "Likes concise answers")
ctx.add("current_task", "Building Rust CLI")

# Get optimized context
optimized = ctx.get_optimized(query="What should I build next?")

# Send to AI
response = call_ai(optimized)
```

### Advanced

```python
from context_manager import ContextManager, MemoryLayers, TaskSelector

# Initialize
ctx = ContextManager(max_tokens=8000)
layers = MemoryLayers()
selector = TaskSelector()

# Add to layers
layers.add_to_layer("short_term", "User conversation")
layers.add_to_layer("long_term", "User preferences")
layers.add_to_layer("skills", "Relevant skills")

# Select for task
selected = selector.select_for_task("code_generation", "Build Rust tool")

# Add selected to context
for item in selected:
    ctx.add(item.name, item.content)

# Prune to fit
final_context = ctx.prune(target_tokens=4000)

# Use with AI
response = call_ai(final_context)
```

---

## Integration Points

### With Frank/Alfred

```python
# In frank.py
from context_manager import ContextManager

ctx = ContextManager(max_tokens=8000)

def process_user_input(user_input):
    # Add conversation to short-term
    ctx.add_to_layer("short_term", user_input)
    
    # Select relevant context
    relevant = ctx.get_relevant(user_input)
    
    # Send to AI
    response = call_ai(relevant)
    
    # Store response
    ctx.add_to_layer("short_term", response)
    
    return response
```

### With Blueprints

```python
# Only load relevant blueprints
from blueprints import BlueprintLibrary
from context_manager import TaskSelector

lib = BlueprintLibrary()
selector = TaskSelector()

# Get blueprints for task
relevant_blueprints = selector.select_blueprints("code_review")

# Load only those
for bp in relevant_blueprints:
    ctx.add(f"blueprint_{bp.name}", bp.full_prompt)
```

### With Council

```python
# Council gets optimized context
from council import CouncilSession
from context_manager import ContextManager

ctx = ContextManager()
session = CouncilSession()

# Add only relevant context for deliberation
ctx.add_for_task("council_deliberation", task_info)

# Council deliberates with focused context
decision = session.deliberate(ctx.get_context())
```

---

## Benefits

**Before:**
- Flood AI with all context
- Token limits exceeded
- Important info buried
- Wasted tokens on irrelevant info

**After:**
- Only relevant context sent
- Token limits respected
- Key info prominent
- Efficient token usage

---

## Implementation Plan

### Phase 1: Core Manager (2 hours)
- [ ] Create `manager.py`
- [ ] Implement add/get/prune
- [ ] Basic relevance scoring
- [ ] Simple tests

### Phase 2: Memory Layers (2 hours)
- [ ] Create `layers.py`
- [ ] Implement layer system
- [ ] TTL/expiration
- [ ] Layer prioritization

### Phase 3: Task Selection (2 hours)
- [ ] Create `selectors.py`
- [ ] Task type definitions
- [ ] Context selection logic
- [ ] Integration with skills/blueprints

### Phase 4: Compression (Later)
- [ ] LLM-based summarization
- [ ] Key info extraction
- [ ] Hierarchical context
- [ ] Testing & tuning

---

## Files to Create

```
context_manager/
├── __init__.py
├── manager.py           # Core context manager
├── relevance.py         # Scoring algorithms
├── layers.py            # Memory layers
├── selectors.py         # Task-based selection
├── compressor.py        # Context compression
├── cli.py               # CLI
└── README.md
```

---

**This makes your AI smarter by sending LESS context, not more.** 🎯

Quality over quantity.
