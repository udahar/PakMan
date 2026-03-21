"""Claw Core - Thin CLI wrapper for Alfred AI platform."""

import sys
import json
import time
import requests
from typing import Dict, Any, Optional


class ClawClient:
    """Thin client for interacting with Alfred AI platform."""

    def __init__(self, alfred_url: str = "http://localhost:5001"):
        """Initialize Claw client.

        Args:
            alfred_url: Base URL for Alfred API
        """
        self.alfred_url = alfred_url.rstrip("/")

    def submit_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit a task to Alfred.

        Args:
            task_type: Type of task to submit
            payload: Task payload data

        Returns:
            Task ID for tracking

        Raises:
            requests.RequestException: If the request fails
        """
        response = requests.post(
            f"{self.alfred_url}/task", json={"type": task_type, "payload": payload}
        )
        response.raise_for_status()
        return response.json()["task_id"]

    def wait_for_result(self, task_id: str) -> Any:
        """Wait for task completion and return result.

        Args:
            task_id: ID of task to wait for

        Returns:
            Task result

        Raises:
            RuntimeError: If task fails
            requests.RequestException: If request fails
        """
        while True:
            response = requests.get(f"{self.alfred_url}/task/{task_id}")
            data = response.json()

            if data["status"] == "complete":
                return data["result"]

            if data["status"] == "error":
                raise RuntimeError(data["error"])

            time.sleep(1)

    def ask(self, prompt: str) -> str:
        """Ask a question using Alfred's best model.

        Args:
            prompt: Question or prompt to ask

        Returns:
            Response from Alfred
        """
        task_id = self.submit_task("ask", {"prompt": prompt})
        return self.wait_for_result(task_id)

    def bench(self, model: str) -> Dict[str, Any]:
        """Benchmark a specific model.

        Args:
            model: Model name to benchmark

        Returns:
            Benchmark results
        """
        task_id = self.submit_task("benchmark", {"model": model})
        return self.wait_for_result(task_id)

    def models(self) -> Dict[str, Any]:
        """Get available models from Alfred.

        Returns:
            Available models information
        """
        response = requests.get(f"{self.alfred_url}/models")
        response.raise_for_status()
        return response.json()

    def arena(self, prompt: str) -> Dict[str, Any]:
        """Run the same task across multiple models for comparison.

        Args:
            prompt: Task to run across models

        Returns:
            Arena comparison results
        """
        task_id = self.submit_task("arena", {"prompt": prompt})
        return self.wait_for_result(task_id)

    def crown(self) -> Dict[str, Any]:
        """Get current model rankings/king-of-the-hill.

        Returns:
            Current model rankings
        """
        task_id = self.submit_task("crown", {})
        return self.wait_for_result(task_id)


# Convenience functions for direct usage
def submit_task(
    task_type: str, payload: Dict[str, Any], alfred_url: str = "http://localhost:5001"
) -> str:
    """Submit a task to Alfred (convenience function).

    Args:
        task_type: Type of task to submit
        payload: Task payload data
        alfred_url: Base URL for Alfred API

    Returns:
        Task ID for tracking
    """
    client = ClawClient(alfred_url)
    return client.submit_task(task_type, payload)


def wait_for_result(task_id: str, alfred_url: str = "http://localhost:5001") -> Any:
    """Wait for task completion and return result (convenience function).

    Args:
        task_id: ID of task to wait for
        alfred_url: Base URL for Alfred API

    Returns:
        Task result
    """
    client = ClawClient(alfred_url)
    return client.wait_for_result(task_id)


def claw_ask(prompt: str, alfred_url: str = "http://localhost:5001") -> str:
    """Ask a question using Alfred (convenience function).

    Args:
        prompt: Question or prompt to ask
        alfred_url: Base URL for Alfred API

    Returns:
        Response from Alfred
    """
    client = ClawClient(alfred_url)
    return client.ask(prompt)


def claw_bench(model: str, alfred_url: str = "http://localhost:5001") -> Dict[str, Any]:
    """Benchmark a model (convenience function).

    Args:
        model: Model name to benchmark
        alfred_url: Base URL for Alfred API

    Returns:
        Benchmark results
    """
    client = ClawClient(alfred_url)
    return client.bench(model)


def claw_models(alfred_url: str = "http://localhost:5001") -> Dict[str, Any]:
    """Get available models (convenience function).

    Args:
        alfred_url: Base URL for Alfred API

    Returns:
        Available models information
    """
    client = ClawClient(alfred_url)
    return client.models()


def claw_arena(
    prompt: str, alfred_url: str = "http://localhost:5001"
) -> Dict[str, Any]:
    """Run arena comparison (convenience function).

    Args:
        prompt: Task to run across models
        alfred_url: Base URL for Alfred API

    Returns:
        Arena comparison results
    """
    client = ClawClient(alfred_url)
    return client.arena(prompt)


def claw_crown(alfred_url: str = "http://localhost:5001") -> Dict[str, Any]:
    """Get model rankings (convenience function).

    Args:
        alfred_url: Base URL for Alfred API

    Returns:
        Current model rankings
    """
    client = ClawClient(alfred_url)
    return client.crown()
