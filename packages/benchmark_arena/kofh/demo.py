#!/usr/bin/env python3
"""
King-of-the-Hill Demo

Watch models compete for throne seats!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kofh import TournamentSystem
from kofh.leaderboard import Leaderboard


def demo_basic_evaluation():
    """Demonstrate basic model evaluation."""
    print("=" * 60)
    print("  KOFH DEMO - Basic Evaluation")
    print("=" * 60)
    
    tournament = TournamentSystem()
    
    # Evaluate some models
    models = [
        ("qwen-coder", "engineer", {"quality": 91.0, "reliability": 94.0, "latency_ms": 420}),
        ("codex", "engineer", {"quality": 96.0, "reliability": 97.0, "latency_ms": 520}),
        ("deepseek", "engineer", {"quality": 88.0, "reliability": 91.0, "latency_ms": 380}),
        ("claude", "planner", {"quality": 94.0, "reliability": 96.0, "latency_ms": 890}),
        ("gemini", "planner", {"quality": 90.0, "reliability": 93.0, "latency_ms": 650}),
    ]
    
    print("\nEvaluating models...\n")
    
    for model, role, metrics in models:
        breakdown = tournament.evaluate_model(model, role, metrics)
        print(f"  {model} ({role}): {breakdown.final_score:.1f}")
    
    print()


def demo_throne_challenges():
    """Demonstrate throne challenges."""
    print("=" * 60)
    print("  KOFH DEMO - Throne Challenges")
    print("=" * 60)
    
    tournament = TournamentSystem()
    
    # First challenger auto-crowns
    print("\n1. First challenger (auto-crown):")
    result = tournament.challenge_throne(
        model="qwen-coder",
        role="engineer",
        test_results={"quality": 91.0, "reliability": 94.0, "latency_ms": 420}
    )
    print(f"   Result: {result['reason']}")
    print(f"   Engineer King: {tournament.get_throne_holder('engineer')}")
    
    # Second challenger - might dethrone
    print("\n2. Second challenger (higher score):")
    result = tournament.challenge_throne(
        model="codex",
        role="engineer",
        test_results={"quality": 96.0, "reliability": 97.0, "latency_ms": 520}
    )
    if result.get('dethroned'):
        print(f"   🔄 THRONE SWAP! {result['dethroned']} → {result['new_king']}")
    else:
        print(f"   King survives: {result.get('king_survives')}")
    
    # Third challenger - below threshold
    print("\n3. Third challenger (below threshold):")
    result = tournament.challenge_throne(
        model="weak-model",
        role="engineer",
        test_results={"quality": 50.0, "reliability": 60.0, "latency_ms": 100}
    )
    print(f"   Result: {result['reason']}")
    
    print()


def demo_leaderboards():
    """Display leaderboards."""
    print("=" * 60)
    print("  KOFH DEMO - Leaderboards")
    print("=" * 60)
    
    tournament = TournamentSystem()
    
    # Populate with data
    test_data = [
        ("codex", "engineer", {"quality": 96.0, "reliability": 97.0, "latency_ms": 520}),
        ("qwen-coder", "engineer", {"quality": 91.0, "reliability": 94.0, "latency_ms": 420}),
        ("claude", "planner", {"quality": 94.0, "reliability": 96.0, "latency_ms": 890}),
        ("gemini", "planner", {"quality": 90.0, "reliability": 93.0, "latency_ms": 650}),
        ("llama", "scientist", {"quality": 85.0, "reliability": 91.0, "latency_ms": 120}),
    ]
    
    for model, role, metrics in test_data:
        tournament.challenge_throne(model, role, metrics)
    
    # Display leaderboards
    print(tournament.get_all_leaderboards())
    print()


def demo_stats():
    """Show tournament statistics."""
    print("=" * 60)
    print("  KOFH DEMO - Statistics")
    print("=" * 60)
    
    tournament = TournamentSystem()
    
    # Run some evaluations
    for _ in range(10):
        tournament.evaluate_model(
            f"model-{_}",
            "engineer",
            {"quality": 80 + _, "reliability": 85 + _, "latency_ms": 500 - _ * 10}
        )
    
    stats = tournament.get_stats()
    
    print(f"\nTournament Statistics:")
    print(f"  Total evaluations: {stats['evaluations']}")
    print(f"  Filled thrones: {stats['thrones']['filled_thrones']}/{stats['thrones']['total_thrones']}")
    print(f"  Average reign: {stats['thrones']['avg_reign_duration_days']:.1f} days")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  KING-OF-THE-HILL TOURNAMENT SYSTEM")
    print("=" * 60)
    print("\n👑 Models compete for council throne seats")
    print("⚔️  No permanent positions - only performance matters")
    print("📊 Leaderboards track all challengers")
    print()
    
    try:
        demo_basic_evaluation()
        demo_throne_challenges()
        demo_leaderboards()
        demo_stats()
        
        print("=" * 60)
        print("  ALL DEMOS COMPLETED")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
