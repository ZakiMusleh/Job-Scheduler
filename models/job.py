"""Base abstract class representing a job in the job scheduling system.

The Job class provides the common attributes and functionality shared by
all job types, including job identification, name, priority, status,
scheduling time, dependencies, and retry management.

It uses the Status enum to track the current state of a job and defines
methods for changing that state. The execute() method is abstract and must
be implemented by subclasses to define the specific work performed by
each job.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any


class Status(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class Job(ABC):
    def __init__(
        self,
        job_id: str,
        name: str,
        priority: int,
        scheduled_at: datetime,
        dependencies: list[str] | None = None,
        max_retries: int = 3,
    ) -> None:
        self.job_id: str = job_id
        self.name: str = name
        self.priority: int = priority
        self.status: Status = Status.PENDING
        self.created_at: datetime = datetime.now()
        self.scheduled_at: datetime = scheduled_at
        self.dependencies: list[str] = dependencies if dependencies is not None else []
        self.retries: int = 0
        self.max_retries: int = max_retries

    @property
    def job_type(self) -> str:
        """The job's type, derived from its concrete class name."""
        return self.__class__.__name__

    @abstractmethod
    def execute(self) -> Any:
        """Execute the job, must be overridden by subclass,
        it should perform the work and return a result"""
        ...

    def mark_running(self) -> None:
        self.status = Status.RUNNING

    def mark_completed(self) -> None:
        self.status = Status.COMPLETED

    def mark_failed(self) -> None:
        self.status = Status.FAILED

    def mark_cancelled(self) -> None:
        self.status = Status.CANCELLED

    def mark_blocked(self) -> None:
        self.status = Status.BLOCKED

    def register_retry(self) -> None:
        self.retries += 1

    def has_exceeded_retries(self) -> bool:
        return self.retries >= self.max_retries

    def to_dict(self) -> dict[str, Any]:
        """Serialize the common Job fields to a JSON dict.
        """
        return {
            "job_type": self.job_type,
            "job_id": self.job_id,
            "name": self.name,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat(),
            "dependencies": list(self.dependencies),
            "retries": self.retries,
            "max_retries": self.max_retries,
        }

    def _restore_runtime_state(self, data: dict[str, Any]) -> None:
        """Restore fields that aren't constructor parameters.
        """
        self.status = Status(data["status"])
        self.retries = data["retries"]
        self.created_at = datetime.fromisoformat(data["created_at"])

    def __lt__(self, other: "Job") -> bool:
        """Ordering for use in a priority queue / heap.

        Higher priority first; if priorities are equal, the job with
        the earlier scheduled_at goes first.
        """
        if not isinstance(other, Job):
            return NotImplemented
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.scheduled_at < other.scheduled_at

    def __str__(self) -> str:
        return (
            f"[{self.job_id}] {self.name} "
            f"(Priority: {self.priority}, Status: {self.status.value})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(job_id={self.job_id!r}, name={self.name!r}, "
            f"priority={self.priority!r}, status={self.status!r}, "
            f"scheduled_at={self.scheduled_at!r}, dependencies={self.dependencies!r}, "
            f"retries={self.retries!r}/{self.max_retries!r})"
        )

    def __hash__(self) -> int:
        """To help storing jobs in a dictionary"""
        return hash(self.job_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.job_id == other.job_id