#!/usr/bin/env python3
"""
Prompt Version Control - Git for Prompts
Starter implementation
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PromptVersion:
    id: str
    prompt: str
    system: str
    model: str
    created_at: str
    parent_id: str | None
    commit_message: str
    metrics: dict | None


class PromptRepo:
    def __init__(self, repo_path: str = ".prompt_repo"):
        self.repo_path = Path(repo_path)
        self.commits_path = self.repo_path / "commits"
        self.commits_path.mkdir(parents=True, exist_ok=True)

    def init(self, name: str):
        config = {"name": name, "created_at": datetime.now().isoformat()}
        with open(self.repo_path / "config.json", "w") as f:
            json.dump(config, f)

    def commit(
        self,
        prompt: str,
        system: str = "",
        model: str = "qwen2.5:7b",
        message: str = "",
        parent_id: str = None,
    ) -> str:
        version_id = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        version = PromptVersion(
            id=version_id,
            prompt=prompt,
            system=system,
            model=model,
            created_at=datetime.now().isoformat(),
            parent_id=parent_id,
            commit_message=message,
            metrics=None,
        )

        with open(self.commits_path / f"{version_id}.json", "w") as f:
            json.dump(asdict(version), f)

        return version_id

    def checkout(self, version_id: str) -> PromptVersion:
        with open(self.commits_path / f"{version_id}.json") as f:
            data = json.load(f)
        return PromptVersion(**data)

    def log(self, limit: int = 10) -> list[PromptVersion]:
        versions = []
        for f in sorted(self.commits_path.glob("*.json"), reverse=True)[:limit]:
            with open(f) as fp:
                data = json.load(fp)
                versions.append(PromptVersion(**data))
        return versions

    def diff(self, id1: str, id2: str) -> dict:
        v1 = self.checkout(id1)
        v2 = self.checkout(id2)

        return {
            "id1": id1,
            "id2": id2,
            "prompt_diff": {"old": v1.prompt, "new": v2.prompt},
            "system_diff": {"old": v1.system, "new": v2.system},
        }

    def branch(self, from_version: str, branch_name: str) -> str:
        # For now, just return the version
        # Full implementation would create branch refs
        return from_version

    def test(self, version_id: str, test_prompt: str) -> dict:
        """Test a prompt version"""
        from langchain_ollama import ChatOllama

        version = self.checkout(version_id)

        llm = ChatOllama(model=version.model)

        messages = []
        if version.system:
            messages.append({"role": "system", "content": version.system})
        messages.append({"role": "user", "content": test_prompt})

        start = datetime.now()
        response = llm.invoke(messages)
        latency = (datetime.now() - start).total_seconds()

        return {
            "version_id": version_id,
            "response": response.content,
            "latency": latency,
            "model": version.model,
        }


# CLI
def main():
    import sys

    repo = PromptRepo()

    if len(sys.argv) < 2:
        print("Usage: prompt_vc.py <command>")
        print("Commands: init, commit, log, checkout, diff, test")
        return

    cmd = sys.argv[1]

    if cmd == "init":
        name = sys.argv[2] if len(sys.argv) > 2 else "my_prompts"
        repo.init(name)
        print(f"Initialized prompt repo: {name}")

    elif cmd == "commit":
        prompt = sys.argv[2] if len(sys.argv) > 2 else ""
        message = sys.argv[3] if len(sys.argv) > 3 else "Update"
        version_id = repo.commit(prompt, message=message)
        print(f"Committed: {version_id}")

    elif cmd == "log":
        versions = repo.log()
        for v in versions:
            print(f"{v.id}: {v.commit_message} ({v.created_at})")

    elif cmd == "checkout":
        version_id = sys.argv[2]
        v = repo.checkout(version_id)
        print(f"Prompt: {v.prompt}")

    elif cmd == "test":
        version_id = sys.argv[2]
        test_prompt = sys.argv[3] if len(sys.argv) > 3 else "Hello"
        result = repo.test(version_id, test_prompt)
        print(f"Response: {result['response']}")
        print(f"Latency: {result['latency']:.2f}s")


if __name__ == "__main__":
    main()
