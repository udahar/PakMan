#!/usr/bin/env python3
"""
Real KOFH Demo - Actually evaluates models!

This runs real tests against local Ollama models.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kofh import TournamentSystem
from kofh.evaluator import RealModelEvaluator, get_test_suite_for_role


def demo_real_evaluation():
    """Evaluate real models via Ollama."""
    print("=" * 60)
    print("  KOFH DEMO - Real Model Evaluation")
    print("=" * 60)
    
    tournament = TournamentSystem()
    evaluator = RealModelEvaluator()
    
    # Models to test (must be available in Ollama)
    models_to_test = [
        ("qwen2.5:7b", "engineer"),
        ("qwen2.5:7b", "planner"),
        # Add more models as available
    ]
    
    print("\nLoading test suites...")
    
    for model, role in models_to_test:
        print(f"\nEvaluating {model} for {role} role...")
        
        # Get test suite
        test_suite = get_test_suite_for_role(role)
        print(f"  Running {len(test_suite)} tests...")
        
        # Run real evaluation
        metrics = evaluator.evaluate(model, role, test_suite)
        
        print(f"  Quality: {metrics['quality']:.1f}")
        print(f"  Reliability: {metrics['reliability']:.1f}%")
        print(f"  Avg Latency: {metrics['latency_ms']:.0f}ms")
        
        # Challenge throne with real scores
        result = tournament.challenge_throne(model, role, metrics)
        
        if result.get('success'):
            if result.get('crowned'):
                print(f"  👑 Crowned as {role} King!")
            elif result.get('dethroned'):
                print(f"  🔄 THRONE SWAP! {result['dethroned']} → {result['new_king']}")
            else:
                print(f"  ✓ Challenge successful")
        else:
            print(f"  ✗ Challenge failed: {result.get('reason')}")
    
    print()


def demo_leaderboards():
    """Display current leaderboards."""
    print("=" * 60)
    print("  KOFH DEMO - Current Leaderboards")
    print("=" * 60)
    
    tournament = TournamentSystem()
    
    print(tournament.get_all_leaderboards())
    print()


def main():
    """Run real evaluations."""
    print("\n" + "=" * 60)
    print("  KING-OF-THE-HILL - REAL EVALUATION")
    print("=" * 60)
    print("\n⚠️  This will call Ollama models and run real tests!")
    print("⏱️  May take several minutes depending on models")
    print()
    
    try:
        demo_real_evaluation()
        demo_leaderboards()
        
        print("=" * 60)
        print("  EVALUATION COMPLETE")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
