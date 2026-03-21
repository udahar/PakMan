"""
Dashboard Integration - Real-time Experiment Monitoring

Feeds experiment results to Alfred Dashboard for:
- Real-time monitoring
- Visualization
- Activity logging
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class ForgeDashboard:
    """
    Dashboard integration for PromptForge.
    
    Features:
    - Real-time experiment logging
    - Activity feed
    - Statistics tracking
    - Export for visualization
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize dashboard integration.
        
        Args:
            storage_path: Path for storing dashboard data
        """
        self.storage_path = storage_path or "PromptForge/dashboard_data.json"
        
        # Activity feed
        self.activity_log: List[Dict] = []
        
        # Experiment history
        self.experiments: List[Dict] = []
        
        # Statistics
        self.stats = {
            "total_experiments": 0,
            "total_runs": 0,
            "strategies_tested": set(),
            "best_strategies": {},
        }
        
        # Load existing data
        self._load()
    
    def log_experiment(self, experiment_result: Dict):
        """
        Log an experiment to dashboard.
        
        Args:
            experiment_result: A/B test result dict
        """
        # Add to experiments
        self.experiments.append(experiment_result)
        
        # Update stats
        self.stats["total_experiments"] += 1
        self.stats["total_runs"] += experiment_result.get("total_runs", 0)
        
        # Track strategies tested
        for result in experiment_result.get("results", []):
            strategy_key = ",".join(sorted(result.get("strategy", [])))
            self.stats["strategies_tested"].add(strategy_key)
        
        # Track winner
        winner = experiment_result.get("winner")
        if winner:
            task_type = experiment_result.get("task_type", "unknown")
            winner_key = ",".join(sorted(winner.get("strategy", [])))
            
            if task_type not in self.stats["best_strategies"]:
                self.stats["best_strategies"][task_type] = {}
            
            if winner_key not in self.stats["best_strategies"][task_type]:
                self.stats["best_strategies"][task_type][winner_key] = 0
            
            self.stats["best_strategies"][task_type][winner_key] += 1
        
        # Log activities
        self._log_activity(
            "EXPERIMENT_COMPLETE",
            f"{experiment_result.get('strategies_tested', 0)} strategies tested"
        )
        
        if winner:
            self._log_activity(
                "WINNER_SELECTED",
                f"Strategy {winner.get('strategy_key', 'unknown')} won with {winner.get('fitness', 0):.2f} fitness"
            )
        
        # Log individual strategy results
        analysis = experiment_result.get("analysis", {})
        by_strategy = analysis.get("by_strategy", {})
        
        for strategy_key, data in by_strategy.items():
            if data.get("fitness", 0) > 0.7:
                self._log_activity(
                    "STRATEGY_PERFORMED_WELL",
                    f"{strategy_key}: {data.get('fitness', 0):.2f} fitness"
                )
            elif data.get("fitness", 0) < 0.3:
                self._log_activity(
                    "STRATEGY_PERFORMED_POORLY",
                    f"{strategy_key}: {data.get('fitness', 0):.2f} fitness"
                )
        
        # Auto-save
        if len(self.experiments) % 20 == 0:
            self._save()
    
    def _log_activity(self, event_type: str, details: str):
        """Log an activity event."""
        self.activity_log.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "details": details,
        })
        
        # Keep last 200 events
        self.activity_log = self.activity_log[-200:]
    
    def get_recent_activities(self, limit: int = 20) -> List[Dict]:
        """
        Get recent activity events.
        
        Args:
            limit: Max events to return
        
        Returns:
            List of activity events
        """
        return self.activity_log[-limit:]
    
    def get_experiment_summary(self, limit: int = 10) -> List[Dict]:
        """
        Get summary of recent experiments.
        
        Args:
            limit: Max experiments to return
        
        Returns:
            List of experiment summaries
        """
        summaries = []
        
        for exp in self.experiments[-limit:]:
            summary = {
                "prompt": exp.get("prompt", "")[:50],
                "model": exp.get("model", "unknown"),
                "task_type": exp.get("task_type", "unknown"),
                "strategies_tested": exp.get("strategies_tested", 0),
                "winner": exp.get("winner", {}).get("strategy_key", "none"),
                "timestamp": exp.get("timestamp", ""),
            }
            summaries.append(summary)
        
        return summaries
    
    def get_strategy_leaderboard(self, task_type: Optional[str] = None) -> List[Dict]:
        """
        Get strategy leaderboard (most wins).
        
        Args:
            task_type: Optional task type filter
        
        Returns:
            List of strategies with win counts
        """
        if task_type:
            strategies = self.stats["best_strategies"].get(task_type, {})
        else:
            # Aggregate across all task types
            strategies = {}
            for task_strategies in self.stats["best_strategies"].values():
                for strategy, count in task_strategies.items():
                    strategies[strategy] = strategies.get(strategy, 0) + count
        
        # Sort by wins
        leaderboard = [
            {"strategy": s, "wins": c}
            for s, c in strategies.items()
        ]
        
        leaderboard.sort(key=lambda x: x["wins"], reverse=True)
        
        return leaderboard[:20]  # Top 20
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        
        Returns:
            Dashboard data dict
        """
        return {
            "stats": {
                "total_experiments": self.stats["total_experiments"],
                "total_runs": self.stats["total_runs"],
                "strategies_tested": len(self.stats["strategies_tested"]),
            },
            "recent_activities": self.get_recent_activities(20),
            "recent_experiments": self.get_experiment_summary(10),
            "leaderboard": self.get_strategy_leaderboard(),
            "best_strategies_by_task": self.stats["best_strategies"],
        }
    
    def export_dashboard_data(self, path: Optional[str] = None) -> str:
        """Export dashboard data to JSON."""
        export_path = path or self.storage_path
        
        data = {
            "dashboard_data": self.get_dashboard_data(),
            "all_experiments": self.experiments[-100:],  # Last 100
            "all_activities": self.activity_log,
            "exported_at": time.time(),
        }
        
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return export_path
    
    def _save(self):
        """Save dashboard data."""
        self.export_dashboard_data()
    
    def _load(self):
        """Load dashboard data."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Load stats
                dashboard_data = data.get("dashboard_data", {})
                self.stats.update(dashboard_data.get("stats", {}))
                self.stats["strategies_tested"] = set(self.stats["strategies_tested"])
                
                # Load activities
                self.activity_log = data.get("all_activities", [])[-200:]
                
                print(f"[ForgeDashboard] Loaded dashboard data")
        except Exception as e:
            print(f"[ForgeDashboard] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return {
            "total_experiments": self.stats["total_experiments"],
            "total_runs": self.stats["total_runs"],
            "strategies_tested": len(self.stats["strategies_tested"]),
            "activity_log_size": len(self.activity_log),
        }
