#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from behavior_profile import BehaviorProfile, example_from_job_event


def main() -> None:
    profile = BehaviorProfile()
    examples = [
        example_from_job_event(applied=True, ai_role=True, remote_canada=True, fit_score=88, priority=90),
        example_from_job_event(saved=True, ai_role=True, fit_score=72, priority=70),
        example_from_job_event(opened=True, public_sector=True, fit_score=66, priority=60),
        example_from_job_event(ai_role=False, public_sector=False, fit_score=25, priority=30),
    ]
    profile.train(examples, epochs=25)
    output = {
        "event_count": profile.event_count,
        "top_weights": profile.top_weights(),
        "sample_scores": {
            "ai_remote_job": profile.score(
                {"ai_role": 1.0, "remote_canada": 1.0, "public_sector": 0.0, "fit_score": 0.84, "priority": 0.8}
            ),
            "generic_low_fit_job": profile.score(
                {"ai_role": 0.0, "remote_canada": 0.0, "public_sector": 0.0, "fit_score": 0.2, "priority": 0.3}
            ),
        },
    }
    save_path = Path(__file__).resolve().parent.parent / "artifacts" / "behavior_profile_demo.json"
    profile.save(save_path)
    print(json.dumps(output, indent=2))
    print(f"saved_profile={save_path}")


if __name__ == "__main__":
    main()
