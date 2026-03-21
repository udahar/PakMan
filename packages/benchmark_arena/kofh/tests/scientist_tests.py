"""
Scientist Role Test Suite

Tests data analysis and interpretation capabilities.
"""

SCIENTIST_TESTS = [
    {
        "name": "analyze_telemetry",
        "description": "Interpret system metrics",
        "input": {
            "metrics": {
                "tool_runs": 100,
                "success_rate": 0.85,
                "avg_latency_ms": 450,
                "p95_latency_ms": 890,
            }
        },
        "expected_output_contains": ["success", "latency", "recommendation"],
        "scoring": {
            "insight_quality": 0.4,
            "accuracy": 0.4,
            "actionability": 0.2,
        }
    },
    {
        "name": "compare_pipelines",
        "description": "A/B test analysis",
        "input": {
            "pipeline_a": {"success": 95, "latency": 450},
            "pipeline_b": {"success": 92, "latency": 320},
        },
        "expected_output_contains": ["trade-off", "recommendation"],
        "scoring": {
            "statistical_rigor": 0.4,
            "practical_advice": 0.4,
            "clarity": 0.2,
        }
    },
    {
        "name": "detect_anomalies",
        "description": "Find outliers in data",
        "input": {
            "baseline_latency": [100, 105, 98, 102, 450, 99, 101],
        },
        "expected_anomalies": [450],
        "scoring": {
            "detection_accuracy": 0.5,
            "false_positives": 0.3,
            "explanation": 0.2,
        }
    },
    {
        "name": "recommend_optimization",
        "description": "Suggest improvements based on data",
        "input": {
            "current_performance": {
                "success_rate": 0.75,
                "avg_time": 890,
                "bottleneck": "llm_latency"
            }
        },
        "expected_output_contains": ["optimize", "improve", "reduce"],
        "scoring": {
            "feasibility": 0.3,
            "impact": 0.4,
            "specificity": 0.3,
        }
    },
    {
        "name": "statistical_significance",
        "description": "Validate results significance",
        "input": {
            "control": [85, 87, 86, 88, 84],
            "treatment": [90, 92, 89, 91, 93],
        },
        "expected_output_contains": ["significant", "p-value"],
        "scoring": {
            "methodology": 0.4,
            "accuracy": 0.4,
            "interpretation": 0.2,
        }
    },
]
