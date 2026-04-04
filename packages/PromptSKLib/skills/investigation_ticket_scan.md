# Skill: Investigation Ticket Scan

**skill_id:** `investigation_ticket_scan_001`
**name:** investigation_ticket_scan
**category:** workflow
**version:** 1.0

## Description

Use the bounded `investigation.ticket.scan` tool first for intake, email, clarification, and investigation work. It performs one deterministic pass across PM state, recent ticket events, workspace tree, code search, and optional file reads so the model does not improvise or loop.

## Primitive Tags

- investigation.ticket.scan
- deterministic_investigation
- email_intake
- project_fit
- novelty_assessment
- hydration
- bounded_tool_use
- no_tool_loop
- bridge_tree
- bridge_search
- bridge_read
- projman.ticket.get
- projman.ticket.events

## Prompt Strategy

```
For deterministic ticket investigation:

1. START WITH THE WRAPPER
   - Call `investigation.ticket.scan` first
   - Provide:
     - ticket_id
     - query derived from the ticket title/brief
     - root_path when a narrower subtree is known
   - Do not start with freeform tool chaining if the wrapper can answer it

2. TREAT THE RESULT AS THE INVESTIGATION PACKET
   - The wrapper returns:
     - current ticket row
     - recent ticket events
     - workspace tree snapshot
     - search hits
     - optional file reads
   - Base conclusions on that packet, not on memory or guesswork

3. WRITE BACK INTO TICKET FIELDS
   - Update:
     - intake_summary_md
     - intake_classification_md
     - novelty_assessment_md
     - investigation_md
   - Do not overwrite brief_md

4. STAY IN INVESTIGATION UNTIL READY
   - If the packet does not show enough evidence, remain in investigation
   - If scope is ambiguous, request clarification
   - Do not promote to coding just because a request sounds technical

5. ONLY ESCALATE TO DIRECT TOOLS IF NEEDED
   - Use direct `bridge.read` / `bridge.search` calls only when the wrapper result is insufficient
   - Keep the follow-up bounded and file-specific
```

## Solution Summary

### Use When

- Email intake arrives as a chat export or vague request
- A ticket needs novelty/project-fit validation
- A story/task is blocked in investigation
- The model needs evidence before decomposition or coding

### Avoid When

- The task is already in explicit coding with known target files
- The ticket already has a complete investigation packet and only needs implementation

### Expected Outcome

- One bounded investigation pass
- No multi-round tool flailing
- Durable ticket hydration fields populated
- Clear next action: clarify, review, decompose, or implement
