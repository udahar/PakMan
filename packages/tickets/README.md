# Tickets Directory

Task tickets are stored here as JSON files.

## Ticket Format

```json
{
  "ticket_id": "20260308_1234",
  "title": "Research quantum computing",
  "description": "I need to understand...",
  "status": "completed",
  "assigned_skills": ["humble_inquiry", "rag"],
  "strategy": "chain_of_thought",
  "result": {...},
  "execution_log": [...]
}
```

## Workflow

1. Create ticket → `frank.py "Task description"`
2. Execute → Auto-selects skills, runs them
3. Results saved here for review


