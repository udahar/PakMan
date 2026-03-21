# Prompt Blueprints - Your Personal Prompt Library

**Concept:** Save your best prompts, then reuse them with simple triggers.

**Bonus:** Auto-catalogs your build sessions and learns from them!

---

## How It Works

### 1. Save a Prompt
```
[Save Blueprint]
Name: streetpunk
Trigger: "like a streetpunk"
Full Prompt: "Write in the style of an urban street punk. Use slang, 
              informal grammar, rebellious tone, reference city life..."
Tags: style, casual, creative
```

### 2. Use It
```
You type: "Explain quantum computing like a streetpunk"

System expands to:
"Write in the style of an urban street punk. Use slang, informal grammar, 
rebellious tone, reference city life, be irreverent...

Explain quantum computing"
```

### 3. It Just Works
- No config files
- No version numbers
- Just: trigger → expansion → great output

---

## Use Cases

### Daily Life
- `like my lawyer` → Formal, precise language
- `explain like I'm 5` → Simple, clear explanations
- `roast me` → Sarcastic, funny criticism
- `like a streetpunk` → Urban slang, rebellious

### Development
- `code review` → Detailed, security-focused analysis
- `write tests` → Comprehensive edge case coverage
- `document this` → Clear, example-rich docs
- `debug help` → Systematic troubleshooting

### AI Roles
- `planner mode` → Strategic thinking prompt
- `engineer mode` → Code expert prompt
- `critic mode` → Loki-style criticism prompt

---

## Files

- `blueprint_db.json` - Your saved prompts
- `expander.py` - Expands triggers to full prompts
- `cli.py` - Command line management
- `web_ui.py` - Visual interface (future)

---

## Quick Start

```bash
# Save a prompt
python blueprints/cli.py save streetpunk "Write like a street punk..."

# Use it (in Frank/Alfred)
"Explain taxes like a streetpunk" → auto-expands

# List your blueprints
python blueprints/cli.py list

# Test one
python blueprints/cli.py test streetpunk "Hello world"
```

---

## Integration with Frank

```python
# In frank.py, before sending to AI:
from blueprints.expander import expand_prompt

user_input = "Explain quantum like a streetpunk"
expanded = expand_prompt(user_input)

# expanded = "Write in the style of an urban street punk... 
#             Explain quantum"

response = call_ai(expanded)
```

---

**This is the tool you actually need.** 🎯
