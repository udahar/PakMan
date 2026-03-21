# Skill Composer - Chain Skills Together

Combine multiple skills into mega-skills.

## Usage

```python
from skill_composer import Composer

composer = Composer()

# Create chain
chain = composer.chain("humble_inquiry", "code_review", "error_repair")

# Execute
result = chain.execute("Review and fix this code")
```

## Features

- **Skill Chains** - Sequence multiple skills
- **Parallel Execution** - Run skills concurrently
- **Conditional Chains** - If skill A fails, try B

## Status

✅ Production Ready
