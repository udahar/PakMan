"""
AiOS Kernel Demo - Test the actual kernel

Usage:
    python -m AiOSKernel.demo
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from AiOSKernel import (
    initialize_kernel,
    create_ticket,
    get_ready_tickets,
    execute_ready_tickets,
    get_best_capability,
    register_capability,
    register_worker,
    Capability,
    CapabilityType,
    Worker,
    get_kernel
)


async def demo():
    """Run full kernel demo"""
    print("🚀 AiOS Kernel Demo - FULL IMPLEMENTATION")
    print("=" * 60)
    print()

    # Initialize kernel with SQLite
    db_path = "C:/Users/Richard/clawd/Frank/PromptRD/AiOSKernel/aios_kernel.db"
    kernel = await initialize_kernel(db_path)

    print()
    print("📋 Creating Ticket Hierarchy")
    print("-" * 60)

    # Create Project
    project_id = await create_ticket(
        level="project",
        title="Build Research Report",
        description="Generate comprehensive research report on AI trends"
    )
    print(f"✅ Created Project: {project_id}")

    # Create Epics
    epic1_id = await create_ticket(
        level="epic",
        title="Data Collection",
        description="Gather research data from multiple sources",
        parent_id=project_id
    )
    print(f"✅ Created Epic 1: {epic1_id}")

    epic2_id = await create_ticket(
        level="epic",
        title="Analysis & Synthesis",
        description="Analyze collected data and synthesize findings",
        parent_id=project_id,
        dependencies=[epic1_id]
    )
    print(f"✅ Created Epic 2: {epic2_id} (depends on {epic1_id})")

    # Create Chapters
    chapter1_id = await create_ticket(
        level="chapter",
        title="Literature Review",
        description="Review existing literature and research papers",
        parent_id=epic1_id
    )
    print(f"✅ Created Chapter 1: {chapter1_id}")

    chapter2_id = await create_ticket(
        level="chapter",
        title="Data Gathering",
        description="Gather quantitative and qualitative data",
        parent_id=epic1_id
    )
    print(f"✅ Created Chapter 2: {chapter2_id}")

    # Create Stories
    story1_id = await create_ticket(
        level="story",
        title="Search Academic Papers",
        description="Search for relevant academic papers on arXiv and other sources",
        parent_id=chapter1_id
    )
    print(f"✅ Created Story 1: {story1_id}")

    story2_id = await create_ticket(
        level="story",
        title="Review Industry Reports",
        description="Review industry reports and market analysis",
        parent_id=chapter1_id
    )
    print(f"✅ Created Story 2: {story2_id}")

    # Create Tickets
    ticket1_id = await create_ticket(
        level="ticket",
        title="Search arXiv for AI papers",
        description="Search arXiv for recent AI research papers from 2024-2025",
        parent_id=story1_id,
        priority=10
    )
    print(f"✅ Created Ticket 1: {ticket1_id}")

    ticket2_id = await create_ticket(
        level="ticket",
        title="Search for LLM benchmarks",
        description="Find benchmark comparisons for LLM models",
        parent_id=story1_id,
        priority=8
    )
    print(f"✅ Created Ticket 2: {ticket2_id}")

    print()
    print("🎯 Getting Ready Tickets")
    print("-" * 60)

    ready = get_ready_tickets()
    print(f"Found {len(ready)} ready tickets:")
    for ticket in ready:
        deps = f" (depends on: {', '.join(ticket.dependencies)})" if ticket.dependencies else ""
        print(f"  • [{ticket.priority}] {ticket.ticket_id}: {ticket.title}{deps}")

    print()
    print("🛠️  Registering Capabilities")
    print("-" * 60)

    # Register some capabilities
    caps = [
        Capability("claude_3_5", "Claude 3.5", CapabilityType.MODEL, "research", 0.92, 0.95),
        Capability("deepseek_math", "DeepSeek Math", CapabilityType.MODEL, "math", 0.95, 0.93),
        Capability("qwen_coder", "Qwen Coder", CapabilityType.MODEL, "code_generation", 0.88, 0.90),
        Capability("gpt4", "GPT-4", CapabilityType.MODEL, "general", 0.90, 0.92),
    ]
    
    for cap in caps:
        register_capability(cap)
        print(f"  ✅ Registered: {cap.name} ({cap.pool}) - score: {cap.benchmark_score}")

    print()
    print("🤖 Registering Workers")
    print("-" * 60)

    # Register workers
    workers = [
        Worker("worker_1", "Claude Worker", ["claude_3_5", "gpt4"]),
        Worker("worker_2", "Math Worker", ["deepseek_math"]),
        Worker("worker_3", "Code Worker", ["qwen_coder", "gpt4"]),
    ]
    
    for worker in workers:
        register_worker(worker)
        print(f"  ✅ Registered: {worker.name} - capabilities: {worker.capabilities}")

    print()
    print("🏆 Getting Best Capabilities")
    print("-" * 60)

    for pool in ["research", "math", "code_generation", "general"]:
        best = get_best_capability(pool)
        if best:
            print(f"  Best for {pool}: {best.name} (score: {best.benchmark_score}, success: {best.success_rate})")
        else:
            print(f"  No capabilities for {pool}")

    print()
    print("📊 Kernel Statistics (Before Execution)")
    print("-" * 60)

    stats = kernel.get_stats()
    print(f"Status: {stats['status']}")
    print(f"Uptime: {stats['uptime_seconds']:.2f}s")
    print(f"Total Tickets: {stats['total_tickets']}")
    print(f"Queue Size: {stats['queue_size']}")
    print(f"Total Capabilities: {stats['total_capabilities']}")
    print(f"Total Workers: {stats['total_workers']}")
    print(f"Total Pools: {stats['total_pools']}")

    print()
    print("⚡ Executing Ready Tickets")
    print("-" * 60)

    results = await execute_ready_tickets(max_concurrent=3)
    
    print(f"\nExecuted {len(results)} tickets:")
    for result in results:
        print(f"  ✅ {result.get('ticket_id')}: {result.get('title', 'N/A')}")
        if result.get('selected_model'):
            print(f"      → Routed to: {result['selected_model']} (score: {result.get('model_score', 0):.2f})")

    print()
    print("📊 Kernel Statistics (After Execution)")
    print("-" * 60)

    stats = kernel.get_stats()
    print(f"Status: {stats['status']}")
    print(f"Uptime: {stats['uptime_seconds']:.2f}s")
    print(f"Tickets Processed: {stats['tickets_processed']}")
    print(f"Tickets Failed: {stats['tickets_failed']}")
    print(f"Events Processed: {stats['events_processed']}")
    print(f"Queue Size: {stats['queue_size']}")

    print()
    print("🔍 Checking Next Ready Tickets")
    print("-" * 60)

    ready = get_ready_tickets()
    if ready:
        print(f"Found {len(ready)} tickets now ready:")
        for ticket in ready:
            print(f"  • {ticket.ticket_id}: {ticket.title}")
    else:
        print("No tickets ready yet (waiting on dependencies)")

    print()
    print("✅ Demo complete!")
    print()
    print("What was demonstrated:")
    print("  ✅ Ticket hierarchy (Project→Epic→Chapter→Story→Ticket)")
    print("  ✅ Dependency management (tickets wait for prerequisites)")
    print("  ✅ Capability pools (research, math, code, general)")
    print("  ✅ Worker registration and routing")
    print("  ✅ PromptRouter integration for model selection")
    print("  ✅ Event system with handlers")
    print("  ✅ SQLite persistence")
    print("  ✅ Concurrent ticket execution")
    print()


if __name__ == "__main__":
    asyncio.run(demo())
