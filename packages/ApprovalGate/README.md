# ApprovalGate
> **Status:** 🔬 IN PROGRESS

## What It Is
A safety interlock middleware that pauses AI thread execution on destructive/expensive operations until human consent is received. Think of it as `sudo` for AI agents.

## Why It Matters
Without this, an autonomous agent could push bad code, delete production files, or spend your API credits. This ensures humans stay in control at critical decision points.

## How It Works

```
Agent wants to run: rm -rf /data/*
         │
         ▼
  ┌──────────────┐
  │ ApprovalGate │ ← Detects flagged operation
  └──────────────┘
         │  Sends alert ──► Telegram / CLI notification
         │
         ▼
  ⏸️ Thread paused...
         │
  Human replies "y"
         │
         ▼
  ✅ Thread resumes
```

### Flagged Operations (Configurable)
| Category | Examples |
|---|---|
| File Ops | `rm`, `shutil.rmtree`, `os.unlink` |
| Git | `git push`, `git reset --hard` |
| API | Stripe charges, bulk email sends |
| Network | Outbound POST to prod endpoints |

### Approval Methods
- **CLI prompt** – blocks inline: `[ApprovalGate] Allow? (y/n):`
- **Telegram** – non-blocking, agent waits for webhook reply
- **Auto-approve** – flag for trusted CI environments

## Integration Points
- `AiOSKernel` → wraps dangerous tool calls at the ToolAdapter layer
- `SwarmProtocol` → can intercept risky OFFER messages before routing

## Roadmap
- [ ] Define flagged operation registry (configurable `.yaml`)
- [ ] Build CLI & Telegram notification backends
- [ ] Write async approval wait loop with timeout
- [ ] Log all approvals/rejections to audit trail
