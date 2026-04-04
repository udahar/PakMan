# Forge Package Index

87 packages across 27 categories. Install any package with:

```bash
forge install <PackageName>
```

---

## Agents
| Package | Description | Status |
|---------|-------------|--------|
| [AgentBazaar](packages/AgentBazaar/) | Agent discovery marketplace. Browse, register, and compose agents by capability. | beta |
| [ApprovalGate](packages/ApprovalGate/) | Human-in-the-loop approval gate. Pauses pipelines for human review before proceeding. | beta |
| [Council](packages/Council/) | Multi-agent debate council. Routes a question through multiple models and synthesizes a consensus answer. | beta |
| [SwarmProtocol](packages/SwarmProtocol/) | Agent swarm coordination protocol. Negotiates task allocation across a pool of agents. | beta |

## Context
| Package | Description | Status |
|---------|-------------|--------|
| [BrowserMemory](packages/BrowserMemory/) | Browser-based persistent memory. Stores and retrieves context across sessions using IndexedDB. | beta |
| [ContextCache](packages/ContextCache/) | Lightweight caching layer for LLM context. Avoids redundant re-computation of expensive context windows. | beta |
| [ContextCompressor](packages/ContextCompressor/) | Context window compressor. Reduces token usage by summarizing and pruning context mid-flight. | beta |
| [ContextDistiller](packages/ContextDistiller/) | Context distillation engine. Compresses long context windows into dense, relevant summaries. | beta |
| [ContextManager](packages/ContextManager/) | Smart context window manager. Tracks token budgets and prioritizes content for optimal LLM performance. | beta |
| [RecursiveContext](packages/RecursiveContext/) | Recursive context builder. Assembles context from nested documents with depth control. | beta |

## Cost & Tokens
| Package | Description | Status |
|---------|-------------|--------|
| [costs](packages/costs/) | Cost tracking and reporting. Logs per-request token costs and generates spend reports across vendors. | stable |
| [CostOptimizer](packages/CostOptimizer/) | Token cost optimizer. Routes tasks to cheapest capable model and enforces per-task spend limits. | beta |
| [TokenBank](packages/TokenBank/) | Token budget bank. Allocates, tracks, and enforces per-agent token spend limits. | beta |

## Evaluation
| Package | Description | Status |
|---------|-------------|--------|
| [Bench](packages/Bench/) | Evaluation framework for package candidates. Tests and measures fitness. | beta |
| [BenchmarkArena](packages/BenchmarkArena/) | Model tournament arena. Runs head-to-head benchmark battles and ranks models. | beta |
| [EvalFramework](packages/EvalFramework/) | Evaluation framework. Define metrics, run benchmarks, and compare model outputs systematically. | beta |
| [EvaluationEngine](packages/EvaluationEngine/) | Flexible evaluation engine for scoring and comparing model outputs with custom metrics. | beta |
| [GapMan](packages/GapMan/) | Gap analysis engine. Finds what your model can't do yet and generates targeted hard tests. | beta |

## Evolution
| Package | Description | Status |
|---------|-------------|--------|
| [Autocoder](packages/Autocoder/) | Code generation from specs. Generates package code automatically. | beta |
| [Mutation](packages/Mutation/) | Mutation engine for package evolution. Combines fragments into package candidates. | beta |
| [PatternMiner](packages/PatternMiner/) | Pattern mining engine. Extract design patterns from repos without copying code. | beta |
| [SanityFilter](packages/SanityFilter/) | Quality gate for package candidates. Filters candidates before development. | beta |
| [SpecGenerator](packages/SpecGenerator/) | Build spec generator. Creates project specifications from candidates. | beta |

## Execution
| Package | Description | Status |
|---------|-------------|--------|
| [CodeSandbox](packages/CodeSandbox/) | Isolated code execution sandbox. Run untrusted code safely with WASM isolation. | beta |
| [Claw](packages/Claw/) | Thin CLI wrapper for Alfred AI platform. | beta |
| [Courtroom](packages/Courtroom/) | Code review loop. Iterates generated code through a judge-model until quality gates pass. | beta |

## Infrastructure
| Package | Description | Status |
|---------|-------------|--------|
| [AiOSKernel](packages/AiOSKernel/) | Core kernel for AI operating system primitives — process model, memory model, I/O model. | alpha |
| [apikey](packages/apikey/) | Secure API key management. Store, rotate, and scope API keys for AI services. | stable |
| [EnvSyncer](packages/EnvSyncer/) | Environment secrets syncer. Keeps .env files consistent across services and machines. | beta |
| [PakManLock](packages/PakManLock/) | Deterministic lockfile manager for Forge. Pins exact package versions for reproducible installs. | beta |
| [Scheduler](packages/Scheduler/) | Task scheduler for AI workflows. Cron-like scheduling with dependency tracking and retries. | beta |

## Ingestion
| Package | Description | Status |
|---------|-------------|--------|
| [DocumentShredder](packages/DocumentShredder/) | Document ingestion engine. Parses, chunks, and indexes documents for RAG pipelines. | beta |

## Integration
| Package | Description | Status |
|---------|-------------|--------|
| [email](packages/email/) | Email intake integration. Auto-ingest inbound email into projects, epics, and tickets. | stable |
| [telegram](packages/telegram/) | Telegram bot integration. Scout pool, chat pool, and report delivery via the Alfred Telegram bot. | stable |
| [WebHooker](packages/WebHooker/) | Webhook integration hub. Receives, validates, and routes webhook events to AI pipelines. | beta |

## Knowledge
| Package | Description | Status |
|---------|-------------|--------|
| [LinkedIn_Export](packages/LinkedIn_Export/) | Import your LinkedIn connections into Qdrant for intelligent network search and relationship mapping. | beta |
| [WikiPak](packages/WikiPak/) | Unified documentation generator. Reads every installed package README and builds a searchable Zola static site. | beta |

## Machine Learning
| Package | Description | Status |
|---------|-------------|--------|
| [AutoDistiller](packages/AutoDistiller/) | Automated model distillation. Trains compact student models from larger teacher outputs. | beta |
| [FeedbackLoop](packages/FeedbackLoop/) | Reinforcement feedback loop. Collects model outputs, scores them, and feeds back for improvement. | beta |
| [LearningTypes](packages/LearningTypes/) | Type definitions and schemas for machine learning data pipelines. | beta |
| [LoRA](packages/LoRA/) | LoRA fine-tuning modules for Alfred platform models. Training scripts, datasets, and adapter management. | beta |
| [MLStack](packages/MLStack/) | Shared ML environment: PyTorch, TensorFlow, ONNX, PEFT, DSPy, and accelerate. | beta |
| [MLUtils](packages/MLUtils/) | Shared ML utility helpers: normalization, metrics, and numpy wrappers. | beta |
| [NeuralNetworks](packages/NeuralNetworks/) | Lightweight neural network building blocks and layer abstractions. | beta |
| [PredictiveAnalytics](packages/PredictiveAnalytics/) | Predictive analytics and forecasting utilities for time-series and tabular data. | beta |
| [TrainValidateTest](packages/TrainValidateTest/) | Train/validate/test split utilities and dataset management helpers. | beta |

## Memory
| Package | Description | Status |
|---------|-------------|--------|
| [GraphMemory](packages/GraphMemory/) | Semantic knowledge graph for AI conversational memory. SQLite-backed, zero runtime deps. | beta |

## Modalities
| Package | Description | Status |
|---------|-------------|--------|
| [AudioBridge](packages/AudioBridge/) | Local audio/voice bridge. Transcribe, synthesize, and route audio to AI pipelines. | beta |
| [Vision](packages/Vision/) | Vision and image processing utilities for multimodal AI pipelines. | beta |

## Monitoring
| Package | Description | Status |
|---------|-------------|--------|
| [AnomalyEngine](packages/AnomalyEngine/) | Anomaly detection engine for AI agent behavior and system metrics. | beta |
| [PakHealth](packages/PakHealth/) | System wellness dashboard for Forge. Monitors package health, import status, and dependency integrity. | beta |
| [TerminalObserver](packages/TerminalObserver/) | Terminal session observer daemon. Monitors shell output and surfaces anomalies to the AI layer. | beta |
| [TraceLog](packages/TraceLog/) | Distributed trace logger. Captures and correlates spans across multi-agent pipelines. | beta |

## NLP
| Package | Description | Status |
|---------|-------------|--------|
| [NERExtractor](packages/NERExtractor/) | Named-entity recognition extraction pipeline for AI text analysis. | beta |
| [NLPPipeline](packages/NLPPipeline/) | NLP text processing pipeline: tokenization, normalization, and feature extraction. | beta |

## Observability
| Package | Description | Status |
|---------|-------------|--------|
| [TraceLog](packages/TraceLog/) | Distributed trace logger. Captures and correlates spans across multi-agent pipelines. | beta |

## Performance
| Package | Description | Status |
|---------|-------------|--------|
| [SemanticCache](packages/SemanticCache/) | Semantic response cache. Deduplicates LLM calls by embedding-similarity with configurable threshold. | beta |

## Productivity
| Package | Description | Status |
|---------|-------------|--------|
| [AutoCode](packages/AutoCode/) | Automated code generation pipeline. Task → brief → code → validate → commit. | beta |
| [AutoDocGen](packages/AutoDocGen/) | Auto documentation generator. Self-documents code and packages from source. | beta |
| [ProjMan](packages/ProjMan/) | CLI tools for Alfred ProjectManager integration. Create and query projects, epics, stories, and tickets. | beta |
| [ProjManSpec](packages/ProjManSpec/) | Spec generator for ProjectManager. Turns candidates into buildable build specs via debate loop. | beta |
| [SupDoc](packages/SupDoc/) | Runtime documentation engine for the Alfred ecosystem. Self-documents installed capabilities. | beta |
| [TicketExecutor](packages/TicketExecutor/) | Automated ticket executor: runs tasks from the ProjectManager ticket queue. | beta |
| [tickets](packages/tickets/) | Lightweight ticket and task tracker for AI workflows. | beta |

## Prompting
| Package | Description | Status |
|---------|-------------|--------|
| [prompt_version_control](packages/prompt_version_control/) | Git-style version control for prompts. Diff, branch, and roll back prompts. | alpha |
| [PromptEvolution](packages/PromptEvolution/) | Prompt evolution engine. Generates prompt variants, benchmarks them, and promotes winners. | beta |
| [PromptForge](packages/PromptForge/) | A/B prompt testing and prompt evolution pipeline. Benchmark prompts against each other. | beta |
| [PromptLibrary](packages/PromptLibrary/) | Searchable prompt library. Tag, version, and retrieve prompts by task type or keyword. | beta |
| [PromptOS](packages/PromptOS/) | Prompt runtime with memory, routing, and state management. | beta |
| [PromptRouter](packages/PromptRouter/) | Experimental prompt routing layer. Selects optimal prompt strategy and target model based on task type. | beta |
| [PromptSKLib](packages/PromptSKLib/) | 26 reusable AI reasoning skills and strategy scaffolds. Injected into task briefs automatically. | stable |

## Routing
| Package | Description | Status |
|---------|-------------|--------|
| [ModelRouter](packages/ModelRouter/) | Intelligent model router. Selects the best model for each task based on capability, cost, and latency. | beta |
| [MultiModelOrchestrator](packages/MultiModelOrchestrator/) | Multi-model orchestrator. Fans out tasks across multiple models and merges results. | beta |
| [RomAI](packages/RomAI/) | Token and vendor orchestrator: budget enforcement, circuit breaking, and cost optimization. | beta |
| [tool_composer](packages/tool_composer/) | Compose multiple tools into pipelines. Chain tool calls with routing and fallback. | alpha |
| [ToolBuilder](packages/ToolBuilder/) | Tool builder. Scaffold new Forge tools from spec, with type hints and tests. | beta |
| [ToolRouter](packages/ToolRouter/) | Tool router. Selects the right tool for a given intent using semantic matching. | beta |

## Safety
| Package | Description | Status |
|---------|-------------|--------|
| [ApprovalGate](packages/ApprovalGate/) | Human-in-the-loop approval gate. Pauses pipelines for human review before proceeding. | beta |
| [RedTeamer](packages/RedTeamer/) | Adversarial red-teaming suite. Generates jailbreak and edge-case prompts to stress-test models. | beta |
| [SafetySentry](packages/SafetySentry/) | LLM output safety guard. Reviews generated code and content before use. | beta |

## Scaffolding
| Package | Description | Status |
|---------|-------------|--------|
| [blueprints](packages/blueprints/) | Project and app blueprints. Templates for common AI app patterns, pre-wired with Forge. | alpha |

## Skills
| Package | Description | Status |
|---------|-------------|--------|
| [SkillComposer](packages/SkillComposer/) | Skill composer. Chain multiple skills into DAG pipelines with branching and fallback. | beta |
| [SkillEvolver](packages/SkillEvolver/) | Skill evolver. Tests skills against benchmarks and auto-generates improved variants. | beta |
| [SkillsFramework](packages/SkillsFramework/) | Core skills framework. Discover, load, and execute skills with a standardized interface. | beta |
| [SkillsRegistry](packages/SkillsRegistry/) | Skill registry. Central catalog of available skills with metadata and capability declarations. | beta |

## Domain-Specific
| Package | Description | Status |
|---------|-------------|--------|
| [BrowserDriver](packages/BrowserDriver/) | Browser automation driver. Controls headless browsers for web scraping and vision tasks. | beta |
| [StockAI](packages/StockAI/) | AI-powered stock analysis. Pattern identification and LLM-assisted investment recommendations. | beta |
| [ZolaPress](packages/ZolaPress/) | Documentation and site generation utilities for ZolaPress static sites. | beta |

---

## Quick Reference by Use Case

**I want to route tasks to the right model** → `ModelRouter`, `PromptRouter`, `RomAI`

**I want to manage context/memory** → `GraphMemory`, `ContextDistiller`, `ContextCompressor`, `ContextManager`, `SemanticCache`

**I want to run multi-agent workflows** → `Council`, `SwarmProtocol`, `AgentBazaar`, `MultiModelOrchestrator`

**I want to evaluate/benchmark models** → `EvalFramework`, `BenchmarkArena`, `GapMan`, `RedTeamer`

**I want to build prompts** → `PromptSKLib`, `PromptForge`, `PromptOS`, `PromptEvolution`

**I want to process documents** → `DocumentShredder`, `NLPPipeline`, `NERExtractor`

**I want to manage costs** → `TokenBank`, `CostOptimizer`, `costs`

**I want to write/manage code automatically** → `AutoCode`, `Autocoder`, `CodeSandbox`, `TicketExecutor`

**I want safety/security** → `SafetySentry`, `ApprovalGate`, `RedTeamer`, `apikey`

**I want to fine-tune models** → `LoRA`, `MLStack`, `AutoDistiller`, `FeedbackLoop`
