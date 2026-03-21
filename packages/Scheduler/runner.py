# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Job Runner
Executes scheduled jobs
Inspired by picoclaw's cron - custom Python implementation
"""

import subprocess
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from .jobs import Job, JobStore, JobStatus, create_job


class JobRunner:
    """
    Job execution engine.

    Runs jobs on schedule using APScheduler-like functionality.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        on_job_complete: Optional[Callable[[Job], None]] = None,
    ):
        self.store = JobStore(storage_path)
        self.on_job_complete = on_job_complete
        self.running_jobs: Dict[str, threading.Thread] = {}

    def add_job(
        self, name: str, command: str, schedule: str, description: str = ""
    ) -> Job:
        """Add a new job."""
        job = create_job(name, command, schedule, description)
        self.store.add(job)
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove a job."""
        return self.store.remove(job_id)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.store.get(job_id)

    def list_jobs(self) -> List[Job]:
        """List all jobs."""
        return self.store.get_all()

    def list_enabled_jobs(self) -> List[Job]:
        """List all enabled jobs."""
        return self.store.get_enabled()

    def run_job(self, job_id: str) -> bool:
        """
        Run a job immediately.

        Args:
            job_id: The job ID to run

        Returns:
            True if job started successfully
        """
        job = self.store.get(job_id)
        if not job:
            return False

        if job.status == JobStatus.RUNNING:
            return False

        thread = threading.Thread(target=self._execute_job, args=(job,))
        thread.daemon = True
        thread.start()

        self.running_jobs[job_id] = thread
        return True

    def _execute_job(self, job: Job):
        """Execute a job."""
        job.mark_running()
        self.store.update(job)

        try:
            result = subprocess.run(
                job.command, shell=True, capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                output = result.stdout or "Job completed successfully"
                job.mark_completed(output)
            else:
                error = result.stderr or f"Exit code: {result.returncode}"
                job.mark_failed(error)

        except subprocess.TimeoutExpired:
            job.mark_failed("Job timed out (300s)")
        except Exception as e:
            job.mark_failed(str(e))

        self.store.update(job)

        if self.on_job_complete:
            self.on_job_complete(job)

    def run_all_enabled(self):
        """Run all enabled jobs."""
        for job in self.store.get_enabled():
            self.run_job(job.job_id)

    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        job = self.store.get(job_id)
        if job:
            job.enabled = True
            job.status = JobStatus.PENDING
            self.store.update(job)
            return True
        return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        job = self.store.get(job_id)
        if job:
            job.enabled = False
            job.status = JobStatus.DISABLED
            self.store.update(job)
            return True
        return False

    def toggle_job(self, job_id: str) -> bool:
        """Toggle job enabled/disabled."""
        job = self.store.get(job_id)
        if job:
            job.toggle()
            self.store.update(job)
            return job.enabled
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get runner status."""
        jobs = self.store.get_all()

        return {
            "total_jobs": len(jobs),
            "enabled_jobs": len([j for j in jobs if j.enabled]),
            "running_jobs": len([j for j in jobs if j.status == JobStatus.RUNNING]),
            "jobs": [j.to_dict() for j in jobs],
        }

    def get_job_history(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get job execution history."""
        job = self.store.get(job_id)
        if not job:
            return []

        history = []
        if job.last_run:
            history.append(
                {
                    "timestamp": job.last_run.isoformat(),
                    "status": job.status.value,
                    "output": job.last_output,
                    "error": job.last_error,
                }
            )

        return history[:limit]

    def validate_schedule(self, schedule: str) -> bool:
        """Validate a schedule expression."""
        valid_prefixes = ["@hourly", "@daily", "@weekly", "@monthly", "*/"]
        return (
            any(schedule.startswith(p) for p in valid_prefixes)
            or schedule.count(" ") >= 4
        )


def create_job_runner(
    storage_path: Optional[str] = None,
    on_complete: Optional[Callable[[Job], None]] = None,
) -> JobRunner:
    """Factory function to create job runner."""
    return JobRunner(storage_path, on_complete)
