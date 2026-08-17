"""Core Scheduler: combines job storage, dependency tracking, and
priority-based selection into the scheduling rules.

Design decision: rather than keeping jobs permanently sitting inside a
JobQueue heap, the Scheduler keeps the authoritative job dictionary
and dependency graph, and builds a *temporary* JobQueue each time it
needs to pick the next job to run. This avoids a "stale heap" problem:
a job's eligibility can change at any moment (a dependency completes,
the clock passes its scheduled_at time) in ways a static heap can't
react to on its own.
"""

from __future__ import annotations

from datetime import datetime

from exceptions.errors import (
    DependencyError,
    InvalidJobError,
    JobNotFoundError,
)
from models.job import Job, Status
from scheduler.dependency_graph import DependencyGraph
from scheduler.job_queue import JobQueue


class Scheduler:

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._graph: DependencyGraph = DependencyGraph()
        self._completed_ids: set[str] = set()
        self._id_counter: int = 0

    def generate_job_id(self) -> str:
        """Generate a unique job ID automatically, e.g. 'J0001', 'J0002'.

        The counter only ever increases within this Scheduler
        instance, and every candidate is also checked against
        currently registered jobs -- so IDs stay unique even after
        jobs are restored from persistence (which can leave the
        counter "behind" jobs that already exist).
        """
        while True:
            self._id_counter += 1
            candidate = f"J{self._id_counter:04d}"
            if candidate not in self._jobs:
                return candidate

    def add_job(self, job: Job) -> None:
        if job.job_id in self._jobs:
            raise InvalidJobError(f"A job with ID '{job.job_id}' already exists")

        for dep_id in job.dependencies:
            if dep_id not in self._jobs:
                raise DependencyError(
                    f"Job '{job.job_id}' depends on unknown job '{dep_id}'"
                )

        self._jobs[job.job_id] = job
        self._graph.add_job(job.job_id)
        for dep_id in job.dependencies:
            self._graph.add_dependency(job.job_id, dep_id)

    def get_job(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise JobNotFoundError(f"No job found with ID '{job_id}'")
        return self._jobs[job_id]

    def all_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def cancel_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        job.mark_cancelled()

    def _dependencies_completed(self, job: Job) -> bool:
        """True if every dependency of `job` has completed successfully."""
        return all(dep_id in self._completed_ids for dep_id in job.dependencies)

    def _dependencies_dead(self, job: Job) -> bool:
        for dep_id in job.dependencies:
            dep = self._jobs.get(dep_id)
            if dep is not None and dep.status in (Status.FAILED, Status.CANCELLED):
                return True
        return False

    def _is_eligible(self, job: Job, now: datetime) -> bool:
        """Check all Section 3 rules for whether `job` can run right now."""
        if job.status not in (Status.PENDING, Status.BLOCKED):
            return False
        if job.scheduled_at > now:
            return False
        if self._dependencies_dead(job):
            return False
        if not self._dependencies_completed(job):
            return False
        return True

    def refresh_statuses(self, now: datetime | None = None) -> None:
        now = now or datetime.now()
        for job in self._jobs.values():
            if job.status not in (Status.PENDING, Status.BLOCKED):
                continue
            if self._dependencies_dead(job):
                job.mark_blocked()
            elif not self._dependencies_completed(job):
                job.mark_blocked()
            else:
                job.status = Status.PENDING

    def get_eligible_jobs(self, now: datetime | None = None) -> list[Job]:
        now = now or datetime.now()
        return [job for job in self._jobs.values() if self._is_eligible(job, now)]

    def select_next_job(self, now: datetime | None = None) -> Job | None:
        now = now or datetime.now()
        self.refresh_statuses(now)
        eligible = self.get_eligible_jobs(now)
        if not eligible:
            return None

        temp_queue = JobQueue()
        for job in eligible:
            temp_queue.push(job)
        next_job = temp_queue.pop()
        next_job.mark_running()
        return next_job

    def record_success(self, job_id: str) -> None:
        job = self.get_job(job_id)
        job.mark_completed()
        self._completed_ids.add(job_id)

    def record_failure(self, job_id: str) -> None:
        job = self.get_job(job_id)
        job.register_retry()
        if job.has_exceeded_retries():
            job.mark_failed()
        else:
            job.status = Status.PENDING  # eligible to be retried

    def retry_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if job.status != Status.FAILED:
            raise InvalidJobError(
                f"Job '{job_id}' is not Failed (current status: {job.status.value})"
            )
        job.retries = 0
        job.status = Status.PENDING

    def sync_completed_from_status(self) -> None:

        self._completed_ids = {
            job.job_id for job in self._jobs.values() if job.status == Status.COMPLETED
        }

    def get_dependency_chain(self, job_id: str) -> list[str]:
        """Return all jobs `job_id` transitively depends on, deepest first.

        Delegates to the internal DependencyGraph without exposing it
        directly, so callers (like the CLI) don't need to know the
        Scheduler keeps a graph object internally.
        """
        return self._graph.get_dependency_chain(job_id)

    def __len__(self) -> int:
        return len(self._jobs)

    def __repr__(self) -> str:
        return (
            f"Scheduler({len(self._jobs)} jobs, {len(self._completed_ids)} completed)"
        )