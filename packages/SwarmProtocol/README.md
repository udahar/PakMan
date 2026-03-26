# SwarmProtocol
> **Status:** 🔬 IN PROGRESS

## What It Is
A standardized inter-agent communication protocol. Specialized agents (Coder, Researcher, Validator) negotiate tasks via structured messages, eliminating single-agent monolith bottlenecks.

## Why It Matters
Today, if Frank needs to "research a topic AND write code AND validate it," one agent context gets overwhelmed. SwarmProtocol lets agents split this naturally, just like a dev team.

## How It Works

```
┌──────────────┐   OFFER task?  ┌──────────────────┐
│  AiOSKernel  │ ─────────────► │   CoderAgent     │
│  (Broker)    │ ◄───────────── │   (ACCEPT)       │
└──────────────┘  DONE+output   └──────────────────┘
       │
       │ OFFER sub-task?
       ▼
┌──────────────────┐
│  ValidatorAgent  │ (ACCEPT -> runs tests -> DONE)
└──────────────────┘
```

### Message Schema
```json
{
  "id": "swarm_a1b2",
  "type": "OFFER | ACCEPT | REJECT | DONE | FAIL",
  "from": "AiOSKernel",
  "to": "CoderAgent",
  "payload": { "task": "Refactor auth module", "context": "..." },
  "timeout_seconds": 120
}
```

### Communication Bus Options
- **SQLite Pub/Sub** (local, no deps)
- **Redis Streams** (multi-process, recommended for prod)
- **Async Event Loop** (lightweight, single-process)

## Integration Points
- `AiOSKernel` → is the broker assigning Tickets to agents
- `ApprovalGate` → can intercept OFFER messages requiring human confirmation

## Roadmap
- [ ] Define final message schema
- [ ] Implement SQLite event bus
- [ ] Wire into AiOSKernel ticket flow
- [ ] Add agent capability advertising
