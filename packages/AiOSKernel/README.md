# AiOSKernel - AI Operating System Kernel

**Purpose:** Core reasoning loop that orchestrates all AI operations

**Architecture:** HYBRID
- **Conversational Core** - Main reasoning loop
- **Event Driven** - Handlers for external triggers
- **Scheduler Driven** - Queued tasks for background work
- **Ticket Hierarchy** - Project → Epic → Chapter → Story → Ticket

---

## Quick Start

```python
from AiOSKernel import get_kernel, create_ticket, get_ready_tickets

# Initialize
kernel = await get_kernel().initialize()

# Create ticket hierarchy
project_id = await create_ticket(
    level="project",
    title="Build Research Report",
    description="Generate comprehensive report"
)

epic_id = await create_ticket(
    level="epic",
    title="Data Collection",
    parent_id=project_id
)

# Get tickets ready to execute
ready = get_ready_tickets()
for ticket in ready:
    await kernel.execute_ticket(ticket)
```

---

## Ticket Hierarchy

```
Project (highest level)
  └─ Epic
      └─ Chapter
          └─ Story
              └─ Ticket (lowest level)
```

### Creating Tickets

```python
# Create project
project = await create_ticket(
    level="project",
    title="AI Research",
    description="Research AI trends"
)

# Create epic with dependency
epic = await create_ticket(
    level="epic",
    title="Analysis",
    parent_id=project,
    dependencies=[project]  # Must wait for project to start
)

# Create ticket with priority
ticket = await create_ticket(
    level="ticket",
    title="Search papers",
    parent_id=story,
    priority=10  # High priority
)
```

---

## Capability Pools

Workers register capabilities in pools:

```python
from AiOSKernel import Capability, CapabilityType

# Register research capability
research_cap = Capability(
    capability_id="claude_research",
    name="Claude 3.5",
    capability_type=CapabilityType.MODEL,
    pool="research",
    benchmark_score=92.0,
    success_rate=0.95
)

kernel.register_capability(research_cap)

# Get best capability for pool
best = kernel.get_best_capability("research")
print(f"Best for research: {best.name} (score: {best.benchmark_score})")
```

### Built-in Pools

- `research` - Research tasks
- `code_generation` - Writing code
- `debugging` - Fixing bugs
- `analysis` - Data analysis
- `summarization` - Summarizing content
- `system_design` - Architecture design

---

## Dependency Graph

Tickets can have dependencies:

```python
# Ticket B depends on Ticket A
ticket_a = await create_ticket(
    level="ticket",
    title="Gather data"
)

ticket_b = await create_ticket(
    level="ticket",
    title="Analyze data",
    dependencies=[ticket_a.ticket_id]  # Waits for ticket_a
)

# Only ticket_a is ready initially
ready = get_ready_tickets()  # Returns [ticket_a]

# After ticket_a completes, ticket_b becomes ready
```

---

## Worker System

Workers execute tickets:

```python
from AiOSKernel import Worker

# Register worker
worker = Worker(
    worker_id="worker_1",
    name="Claude Worker",
    capabilities=["claude_research", "claude_code"],
    status="idle"
)

kernel.register_worker(worker)

# Get idle worker for capability pool
idle_worker = kernel.get_idle_worker("research")
```

---

## Event System

Subscribe to events:

```python
async def on_ticket_created(event):
    ticket_id = event["payload"]["ticket_id"]
    print(f"Ticket created: {ticket_id}")

kernel.register_handler("ticket.created", on_ticket_created)

# Events are emitted automatically
await create_ticket(...)  # Emits "ticket.created"
```

---

## Database

Kernel uses SQLite for persistence:

```python
# Use file database
kernel = await get_kernel("/path/to/aios.db").initialize()

# Or in-memory
kernel = await get_kernel(":memory:").initialize()
```

### Tables

- `tickets` - All tickets
- `capabilities` - Registered capabilities
- `workers` - Registered workers

---

## Monitoring

```python
# Get kernel state
state = kernel.get_state()
print(f"Status: {state.status}")
print(f"Tickets processed: {state.tickets_processed}")

# Get statistics
stats = kernel.get_stats()
print(f"Total tickets: {stats['total_tickets']}")
print(f"Queue size: {stats['queue_size']}")
print(f"Active workers: {stats['active_workers']}")
```

---

## Execution Flow

```
1. Create tickets (with dependencies)
   ↓
2. Get ready tickets (dependencies satisfied)
   ↓
3. For each ready ticket:
   a. Get best capability for task
   b. Get idle worker with that capability
   c. Execute ticket
   d. Emit completion event
   ↓
4. Repeat until all tickets complete
```

---

## Demo

```bash
# Run demo
python3 -m AiOSKernel.demo

# Output:
# 🚀 AiOS Kernel Demo
# ============================================================
# 
# ✅ AiOS Kernel initialized
#    Status: running
#    Tickets: 0
#    Workers: 0
#    Capabilities: 0
# 
# 📋 Creating Ticket Hierarchy
# ------------------------------------------------------------
# ✅ Created Project: project_abc123
# ✅ Created Epic 1: epic_def456
# ✅ Created Epic 2: epic_ghi789 (depends on epic_def456)
# ...
```

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Kernel implementation | ~650 |
| `demo.py` | Demo script | ~150 |

**Total:** ~800 lines

---

**Status:** ✅ Implemented  
**Database:** SQLite  
**Next:** Integrate with PromptRD skills and /src/modules/ workers
