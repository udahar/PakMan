# PakMan 📦

**Package manager for AI-native capabilities**

Install a capability once. Every AI app on your machine gains it automatically.

No wiring. No config. Just restart the app.

![PakMan Demo](./pakman_demo.png)


---

## ⚡ What PakMan Is

PakMan is a local-first package manager designed specifically for AI systems.

It installs **capabilities** — not libraries.

* Prompting strategies n- Context management
* Routing logic
* Memory modules
* Evaluation tools

Once installed, any PakMan-aware app can discover and use them instantly.

---

## 🔥 Why It Matters

Today:

* Every AI app ships its own features
* Nothing composes cleanly
* Everything is duplicated

PakMan fixes that.

> Install once → reuse everywhere

It turns AI tools into a **modular ecosystem instead of isolated apps**.

---

## 🚀 Quick Start

```bash
pip install git+https://github.com/udahar/PakMan.git

pakman install PromptSKLib
pakman install context_distiller
pakman list
```

---

## 🧠 How It Works

PakMan installs packages into:

```
~/.pakman/
  packages/
  pakman.db
  hashes/
```

Then PakMan-aware apps call `hotload()` on startup:

```
pakman install PromptSKLib
        ↓
~/.pakman/packages/PromptSKLib/
        ↓
App restarts
        ↓
Capability is automatically available
```

No imports. No config. No glue code.

---

🧩 System Diagram

           ┌──────────────────────────────┐
           │        PakMan CLI                       │
           │  (install / update / remove)            │
           └─────────────┬────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ ~/.pakman/            │
                │ packages/             │
                │ pakman.db             │
                │ hashes/               │
                └───────┬─────────┘
                        │
        ┌───────────────┼──────────────────┐
        │               │                  │
        ▼               ▼                  ▼
 ┌────────────┐  ┌────────────┐   ┌────────────┐
 │   App A         │  │   App B        │   │   App C        │
 │ (Claw)          │  │ (Alfred)       │   │ (Other)        │
 └─────┬──────┘  └─────┬──────┘   └─────┬──────┘
       │               │                │
       ▼               ▼                ▼
     hotload()      hotload()       hotload()
       │               │                │
       └───────┬───────┴────────────┬───┘
               ▼                    ▼
        ┌───────────────┐   ┌───────────────┐
        │ Installed           │   │ Installed           │
        │ Packages            │   │ Capabilities        │
        │ (PromptSKLib)       │   │ (Routing, etc)      │
        └───────────────┘   └───────────────┘

🔄 Flow

pakman install PromptSKLib
        ↓
~/.pakman/packages/PromptSKLib/
        ↓
App restarts
        ↓
hotload() scans packages
        ↓
Capability is available instantly

No imports. No config. No glue code.




## 🧩 Core Features

### 📦 Capability Packages

* Drop-in functionality for AI apps
* Zero manual integration

### ⚡ Sparse Installs

* Uses git sparse-checkout
* Downloads only what’s needed

### 🔁 Auto Discovery

* Apps scan installed packages at startup
* Capabilities load automatically

### 🔐 Security Model

* Trusted registry (udahar only)
* SHA256 integrity checks
* Explicit opt-in for community packages

### 🧪 Health System

```bash
pakman health
```

Detects broken packages and missing dependencies before runtime

---

## 🛠 CLI Overview

```bash
# Install
pakman install PromptSKLib
pakman install ./local_package

# Update
pakman update

# Remove
pakman remove PromptSKLib

# Search
pakman search prompt

# Inspect
pakman info PromptSKLib

# Health check
pakman health
```

---

## 🔥 Example Flow

```
pakman install cost_optimizer
        ↓
Restart your AI app
        ↓
Routing logic now available
```

No code changes required.

---

## 🧱 Package Structure

```
my_package/
├── __init__.py
├── README.md
└── requirements.txt
```

Install locally:

```bash
pakman install ./my_package
```

---

## 🌐 Ecosystem

PakMan is part of a larger AI-native stack:

* Guardian → system health + stability
* Alfred → orchestration + execution
* Claw → agent runtime

PakMan → capability layer that connects everything

---

## 🧨 Philosophy

PakMan is built on one idea:

> AI tools should be composable, not monolithic.

---

## 📜 License

MIT
