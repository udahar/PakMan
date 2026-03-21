# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Job Definitions
Inspired by picoclaw's cron - custom Python implementation
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DISABLED = "disabled"


@dataclass
class Job:
    """
    A scheduled job definition.

    Similar to picoclaw's cron jobs but in Python.
    """

    job_id: str
    name: str
    command: str
    schedule: str
    enabled: bool = True
    description: str = ""

    status: JobStatus = JobStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    last_output: Optional[str] = None
    last_error: Optional[str] = None
    run_count: int = 0
    success_count: int = 0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "command": self.command,
            "schedule": self.schedule,
            "enabled": self.enabled,
            "description": self.description,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_output": self.last_output,
            "last_error": self.last_error,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "success_rate": self.success_count / self.run_count
            if self.run_count > 0
            else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create from dictionary."""
        job = cls(
            job_id=data.get("job_id", ""),
            name=data.get("name", ""),
            command=data.get("command", ""),
            schedule=data.get("schedule", ""),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )

        if "status" in data:
            job.status = JobStatus(data["status"])

        if data.get("last_run"):
            job.last_run = datetime.fromisoformat(data["last_run"])
        if data.get("next_run"):
            job.next_run = datetime.fromisoformat(data["next_run"])

        job.last_output = data.get("last_output")
        job.last_error = data.get("last_error")
        job.run_count = data.get("run_count", 0)
        job.success_count = data.get("success_count", 0)
        job.metadata = data.get("metadata", {})

        return job

    def mark_running(self):
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.updated_at = datetime.now()

    def mark_completed(self, output: str):
        """Mark job as completed successfully."""
        self.status = JobStatus.COMPLETED
        self.last_output = output
        self.last_run = datetime.now()
        self.run_count += 1
        self.success_count += 1
        self.updated_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.last_error = error
        self.last_run = datetime.now()
        self.run_count += 1
        self.updated_at = datetime.now()

    def toggle(self) -> bool:
        """Toggle enabled/disabled."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.status = JobStatus.DISABLED
        self.updated_at = datetime.now()
        return self.enabled

    def get_summary(self) -> str:
        """Get job summary."""
        return (
            f"Job: {self.name}\n"
            f"  ID: {self.job_id}\n"
            f"  Schedule: {self.schedule}\n"
            f"  Status: {self.status.value}\n"
            f"  Runs: {self.run_count} (success: {self.success_count})\n"
            f"  Last run: {self.last_run.isoformat() if self.last_run else 'Never'}"
        )


def create_job(
    name: str, command: str, schedule: str, description: str = "", enabled: bool = True
) -> Job:
    """Factory function to create a job."""
    return Job(
        job_id=str(uuid.uuid4())[:8],
        name=name,
        command=command,
        schedule=schedule,
        description=description,
        enabled=enabled,
    )


class JobStore:
    """In-memory job storage with JSON persistence."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.jobs: Dict[str, Job] = {}

        if storage_path:
            self._load()

    def add(self, job: Job) -> Job:
        """Add a job."""
        self.jobs[job.job_id] = job
        self._save()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def get_all(self) -> List[Job]:
        """Get all jobs."""
        return list(self.jobs.values())

    def get_enabled(self) -> List[Job]:
        """Get all enabled jobs."""
        return [j for j in self.jobs.values() if j.enabled]

    def remove(self, job_id: str) -> bool:
        """Remove a job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save()
            return True
        return False

    def update(self, job: Job) -> bool:
        """Update a job."""
        if job.job_id in self.jobs:
            self.jobs[job.job_id] = job
            self._save()
            return True
        return False

    def _load(self):
        """Load jobs from file."""
        if not self.storage_path:
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for job_data in data.get("jobs", []):
                    job = Job.from_dict(job_data)
                    self.jobs[job.job_id] = job
        except FileNotFoundError:
            pass
        except Exception:
            pass

    def _save(self):
        """Save jobs to file."""
        if not self.storage_path:
            return

        data = {"jobs": [job.to_dict() for job in self.jobs.values()]}

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def to_json(self) -> str:
        """Export all jobs as JSON."""
        return json.dumps(
            {"jobs": [job.to_dict() for job in self.jobs.values()]}, indent=2
        )
