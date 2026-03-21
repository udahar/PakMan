# Health Monitor - System Wellness Dashboard

**Status:** 📋 Concept - High Priority

---

## The Problem

You have **20+ packages** running:
- Blueprints
- Safety Sentry
- Council
- Courtroom
- StockAI
- Rust utilities (52 tools!)
- Memory Graph
- PkgMan
- etc.

**Things WILL break.** You need to know:
- What's working?
- What's failing?
- What needs attention?
- Is my AI system healthy?

---

## The Solution

A **system monitoring dashboard** that:
1. **Checks all subsystems** - Ping each package
2. **Shows status visually** - Green/yellow/red indicators
3. **Alerts on failures** - Notify when something breaks
4. **Provides diagnostics** - Debug tools built-in
5. **Suggests fixes** - Auto-recovery recommendations

---

## Architecture

```
health_monitor/
├── monitor.py           # Core monitoring engine
├── checks.py            # Health check definitions
├── alerts.py            # Alert system (email, desktop, etc.)
├── dashboard.py         # Visual dashboard (Streamlit)
├── diagnostics.py       # Debug tools
├── recovery.py          # Auto-recovery suggestions
└── cli.py               # Command-line interface
```

---

## Features

### 1. System Checks

```python
# Check all subsystems
checks = {
    "blueprints": check_blueprints(),
    "safety_sentry": check_sentry(),
    "council": check_council(),
    "courtroom": check_courtroom(),
    "stockai": check_stockai(),
    "rust_utils": check_rust_tools(),
    "memory_graph": check_memory_graph(),
    "ollama": check_ollama(),
    "qdrant": check_qdrant(),
    "postgres": check_postgres(),
}
```

**Each check returns:**
- ✅ **Healthy** - Working normally
- ⚠️ **Degraded** - Working but issues detected
- ❌ **Failed** - Not working
- ❓ **Unknown** - Can't determine

---

### 2. Dashboard View

```
╔══════════════════════════════════════════════════════════╗
║           ALFRED SYSTEM HEALTH                           ║
║           Last checked: 2026-03-12 15:30:00              ║
╠══════════════════════════════════════════════════════════╣
║                                                           ║
║  CORE SYSTEMS                                            ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │  Blueprints        ✅  Healthy                     │ ║
║  │  Safety Sentry     ✅  Healthy                     │ ║
║  │  Council           ✅  Healthy                     │ ║
║  │  Courtroom         ⚠️  Degraded (Ollama slow)     │ ║
║  └────────────────────────────────────────────────────┘ ║
║                                                           ║
║  DATA LAYER                                              ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │  Ollama            ✅  Healthy (120ms)            │ ║
║  │  Qdrant            ✅  Healthy (45ms)             │ ║
║  │  PostgreSQL        ❌  Failed (connection refused)│ ║
║  │  Memory Graph      ❓  Unknown                    │ ║
║  └────────────────────────────────────────────────────┘ ║
║                                                           ║
║  RUST UTILITIES                                          ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │  rustutils         ✅  Healthy                     │ ║
║  │  52 crates         ✅  All compiled               │ ║
║  └────────────────────────────────────────────────────┘ ║
║                                                           ║
║  SUMMARY                                                 ║
║  ┌────────────────────────────────────────────────────┐ ║
║  │  Overall: ⚠️  DEGRADED                             │ ║
║  │  Healthy: 8  |  Degraded: 1  |  Failed: 1         │ ║
║  │                                                    │ ║
║  │  Action needed: PostgreSQL connection failed      │ ║
║  └────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════╝
```

---

### 3. Alerts

**When something fails:**

```python
# Desktop notification
notify("PostgreSQL connection failed!")

# Log to file
log_alert("postgres", "Connection refused", severity="HIGH")

# Optional: Email/Slack/Discord
send_alert("Database down! Check health_monitor dashboard")
```

**Alert levels:**
- **INFO** - Something changed
- **WARNING** - Degraded performance
- **CRITICAL** - System failed
- **EMERGENCY** - Multiple systems failed

---

### 4. Diagnostics

**Built-in debug tools:**

```bash
# Run diagnostics
python -m health_monitor diagnose

# Check specific subsystem
python -m health_monitor check ollama

# View logs
python -m health_monitor logs --tail 100

# Test recovery
python -m health_monitor recover postgres
```

**Diagnostics include:**
- Connection tests
- Performance benchmarks
- Log analysis
- Resource usage (CPU, memory, disk)
- Dependency checks

---

### 5. Auto-Recovery

**Suggest fixes automatically:**

```python
# PostgreSQL failed
if check_postgres() == FAILED:
    suggest([
        "1. Check if PostgreSQL is running",
        "2. Verify connection string",
        "3. Check firewall rules",
        "4. Restart PostgreSQL service",
    ])
    
    # Optional: Auto-recover
    if auto_recover_enabled:
        try:
            restart_postgres()
            log("PostgreSQL restarted successfully")
        except Exception as e:
            log(f"Auto-recovery failed: {e}")
```

---

## Usage

### Command Line

```bash
# Quick status
python -m health_monitor status

# Full check
python -m health_monitor check --all

# Watch mode (continuous monitoring)
python -m health_monitor watch --interval 60

# Run diagnostics
python -m health_monitor diagnose ollama

# View alerts
python -m health_monitor alerts --today
```

### Python API

```python
from health_monitor import HealthMonitor

monitor = HealthMonitor()

# Check all systems
health = monitor.check_all()

# Check specific system
ollama_health = monitor.check("ollama")

# Get recommendations
if ollama_health.status == "DEGRADED":
    fixes = monitor.get_recovery_steps("ollama")
    print(fixes)

# Export report
monitor.export_report("health_report.json")
```

### Dashboard (Streamlit)

```bash
# Launch visual dashboard
streamlit run health_monitor/dashboard.py
```

Opens at `localhost:8501` with:
- Real-time status
- Historical trends
- Alert history
- Resource usage graphs
- Quick actions (restart, recover, etc.)

---

## Implementation Plan

### Phase 1: Core Monitoring (2 hours)
- [ ] Create `monitor.py` with check engine
- [ ] Implement checks for top 5 systems
- [ ] CLI for status checks
- [ ] Basic logging

### Phase 2: Dashboard (2 hours)
- [ ] Streamlit dashboard
- [ ] Visual status indicators
- [ ] Alert history
- [ ] Quick action buttons

### Phase 3: Alerts & Recovery (2 hours)
- [ ] Alert system (desktop notifications)
- [ ] Recovery suggestions
- [ ] Auto-recovery for common issues
- [ ] Email/Slack integration (optional)

### Phase 4: Advanced (Later)
- [ ] Historical trending
- [ ] Performance benchmarks
- [ ] Resource monitoring
- [ ] Predictive alerts (before failures)

---

## Integration Points

### With Frank/Alfred
```python
# In frank.py, check health before operations
from health_monitor import HealthMonitor

monitor = HealthMonitor()

def process_request(user_input):
    # Check critical systems
    health = monitor.check_critical()
    
    if not health.all_healthy():
        notify_user(f"System degraded: {health.failed_systems}")
    
    # Continue with request...
```

### With Blueprints
```python
# Save health check prompts
from blueprints import BlueprintLibrary

lib = BlueprintLibrary()
lib.save(
    "system_diagnose",
    "diagnose system issue",
    "Analyze this system failure and suggest fixes..."
)
```

### With Council
```python
# Council can review health reports
from council import CouncilSession

session = CouncilSession()
health_report = monitor.generate_report()

# Ask council to analyze
decision = session.deliberate(
    f"System health degraded: {health_report.failed_systems}. What should we do?"
)
```

---

## Files to Create

```
health_monitor/
├── __init__.py
├── monitor.py           # Core engine
├── checks/
│   ├── __init__.py
│   ├── ollama_check.py
│   ├── qdrant_check.py
│   ├── postgres_check.py
│   ├── blueprints_check.py
│   └── rust_check.py
├── alerts.py
├── dashboard.py
├── diagnostics.py
├── recovery.py
├── cli.py
└── README.md
```

---

## Benefits

**Before:**
- Systems fail silently
- You don't know what's broken
- Manual debugging
- Downtime while you figure it out

**After:**
- Instant failure detection
- Clear status dashboard
- Built-in diagnostics
- Auto-recovery suggestions
- Minimal downtime

---

**This is your system's early warning system.** 🚨

Build it once, use it forever.
