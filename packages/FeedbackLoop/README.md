# FeedbackLoop
> **Status:** 🔬 IN PROGRESS

## What It Is
Silently captures when humans manually correct AI-generated output (code, text, docs), computes the diff, and feeds it back into the learning system to prevent the same mistake recurring.

## Why It Matters
When you edit ChatGPT's response in your editor, that edit is pure gold. You're expressing exactly what should have been different. FeedbackLoop harvests that signal automatically.

## How It Works

```
AI generates response → saved to: .feedbackloop/hash_abc.txt
         │
User opens the file, tweaks a few lines...
         │
FeedbackLoop daemon notices file was changed:
   diff(original, modified) =
     - "use asyncio.run(main())"
     + "if __name__ == '__main__': asyncio.run(main())"
         │
         ▼
  Wraps diff as reinforcement signal:
  {
    "original": "...",
    "correction": "...",
    "signal": "negative",
    "context": "Python async pattern"
  }
         │
         ▼
  Stores in PromptOS genome as negative reinforcement
  → Future prompts for "Python async" include correction context
```

### Detection Strategies
| Method | How |
|---|---|
| File Watcher | `watchdog` library monitors known output files |
| Clipboard | Detects paste-then-edit cycles |
| Git Diff | Post-commit hook compares AI output to committed code |

## Integration Points
- `PromptOS` → genome/evolution system absorbs correction signals
- `PromptForge` → lowers scoring for strategies that generated corrected content

## Roadmap
- [ ] Implement file watcher daemon using `watchdog`
- [ ] Build diff → signal formatter
- [ ] Connect to PromptOS genome as `feedback_record()`
- [ ] Add opt-out flag for private/sensitive files
