# The Courtroom - AI Code Review Architecture

**Status:** 👨‍⚖️ In Development

A structured disagreement system where AI agents argue about code quality before it reaches the harness.

---

## The Philosophy

> "Code written while thinking is garbage. Code written from a contract is engineering."

Separate **thinking** from **writing**.

---

## The Four Roles

### 1. Scribe 📝
**Role:** Code writer (dumb, follows ticket)  
**Input:** Filled ticket (the contract)  
**Output:** Code implementation  
**Does NOT:** Think, research, question

### 2. Critic (Loki) 🔥
**Role:** Prosecution - prove code wrong  
**Input:** Code + Ticket  
**Output:** List of flaws, bugs, violations  
**Does NOT:** Write code, approve

### 3. Judge ⚖️
**Role:** Decision maker  
**Input:** Code + Criticism  
**Output:** Pass to harness OR reject  
**Does NOT:** Write code, argue

### 4. Harness 🛡️
**Role:** Final authority (supreme court)  
**Input:** Code + Ticket  
**Output:** Deterministic pass/fail  
**Does NOT:** Argue, debate

---

## The Flow

```
Ticket Created
    ↓
Analysis Agents (fill ticket)
    ↓
┌─────────────────────────────────┐
│  COURTROOM LOOP                 │
│                                 │
│  Scribe → writes code           │
│     ↓                           │
│  Critic → attacks code          │
│     ↓                           │
│  Judge → reviews arguments      │
│     ↓                           │
│  [If approved]                  │
│     ↓                           │
│  Harness → final verdict        │
│                                 │
│  [If rejected]                  │
│     ↓                           │
│  Back to Scribe (revision)      │
└─────────────────────────────────┘
    ↓
Deploy / Merge
```

---

## Ticket Contract Format

```json
{
  "objective": "Create Rust utility for file hashing",
  "constraints": [
    "Must support MD5 and SHA256",
    "Must handle files up to 1GB",
    "Must output JSON format"
  ],
  "files_to_modify": ["crates/file_hash/src/main.rs"],
  "files_to_create": [],
  "reference_patterns": ["existing tool structure"],
  "expected_output": {
    "type": "rust_binary",
    "acceptance_criteria": [
      "Compiles without errors",
      "Passes all tests",
      "Outputs valid JSON"
    ]
  },
  "reasoning_notes": "...",
  "research_findings": "..."
}
```

---

## Scribe Behavior

```python
# Scribe does NOT think
def write_code(ticket):
    prompt = f"""
    Write code that fulfills this ticket EXACTLY.
    
    TICKET CONTRACT:
    {ticket.objective}
    
    CONSTRAINTS:
    {bullet_list(ticket.constraints)}
    
    FILES TO MODIFY:
    {ticket.files_to_modify}
    
    DO NOT:
    - Question the ticket
    - Add features not requested
    - Modify files not listed
    - Think about architecture
    
    JUST WRITE THE CODE.
    """
    
    return call_model(prompt, model="scribe-model")
```

---

## Critic (Loki) Behavior

```python
# Loki's job: DESTROY the code
def attack(code, ticket):
    prompt = f"""
    Your job is to PROVE this code is WRONG.
    
    Find:
    - Bugs
    - Edge cases not handled
    - Ticket violations
    - Security issues
    - Performance problems
    - Missing error handling
    
    CODE:
    {code}
    
    TICKET:
    {ticket}
    
    Be BRUTAL. Find EVERY flaw.
    """
    
    return call_model(prompt, model="loki")
```

---

## Judge Behavior

```python
# Judge decides: pass to harness or reject
def decide(code, criticism, ticket):
    prompt = f"""
    Review the critic's arguments.
    
    Are the flaws:
    - Critical? → Reject
    - Minor? → Pass with notes
    - Invalid? → Dismiss and pass
    
    Output:
    {{
      "decision": "pass" | "reject",
      "reasoning": "...",
      "required_fixes": [...]
    }}
    """
    
    return call_model(prompt, model="judge-model")
```

---

## Harness (Final Authority)

```python
# Deterministic verification
def verify(code, ticket):
    checks = [
        check_compiles(code),
        check_tests_pass(code),
        check_files_match(ticket.files_to_modify),
        check_no_extra_edits(code, ticket),
        check_acceptance_criteria(code, ticket.expected_output),
    ]
    
    return all(checks)  # Binary pass/fail
```

---

## Files

- `courtroom/__init__.py` - Package exports
- `courtroom/scribe.py` - Code writer
- `courtroom/critic.py` - Loki (prosecutor)
- `courtroom/judge.py` - Decision maker
- `courtroom/harness.py` - Final verification
- `courtroom/session.py` - Courtroom session management
- `courtroom/demo.py` - Demo script

---

## Usage

```python
from courtroom import CourtroomSession

session = CourtroomSession()

# Submit ticket
ticket = create_ticket("Build file hasher")

# Run courtroom loop
result = session.run(ticket)

if result.passed:
    print("✅ Code approved by harness")
else:
    print(f"❌ Rejected: {result.reason}")
    print(f"Revision {result.revisions} needed")
```

---

## Integration Points

### With Autocode
```python
# Autocode becomes the Scribe
from autocode import CoderAgent

scribe = CoderAgent()
code = scribe.implement(ticket)
```

### With Loki
```python
# Loki is the Critic
from guardian import LokiAgent

critic = LokiAgent()
criticism = critic.attack(code, ticket)
```

### With Harness
```python
# Existing harness is final authority
from frank import Harness

harness = Harness()
verdict = harness.verify(code, ticket)
```

---

## Why This Works

### 1. Separation of Concerns
- Thinkers think
- Scribes write
- Critics attack
- Judges decide
- Harness verifies

### 2. Structured Disagreement
- Loki CAN'T write code
- Scribe CAN'T argue
- Judge CAN'T ignore criticism
- Harness is FINAL

### 3. Ticket as Contract
- No ambiguity
- Clear acceptance criteria
- Scope enforcement
- Revision tracking

### 4. Weak Models, Strong Process
- Even mediocre models perform well
- Process does half the work
- System > individual intelligence

---

## Status

| Component | Status |
|-----------|--------|
| Scribe | 📝 Ready to implement |
| Critic (Loki) | 🔥 Loki exists, needs integration |
| Judge | ⚖️ Ready to implement |
| Harness | 🛡️ Exists in Frank |
| Session Mgmt | 📋 Ready to implement |

---

**The Court is Now in Session.** ⚖️👨‍⚖️
