"""Base abstract class representing a job in the job scheduling system.

The Job class provides the common attributes and functionality shared by
all job types, including job identification, name, priority, status,
scheduling time, dependencies, and retry management.

It uses the Status enum to track the current state of a job and defines
methods for changing that state. The execute() method is abstract and must
be implemented by subclasses to define the specific work performed by
each job.

The class also provides string representations, equality comparison, and
hashing based on the job ID, allowing jobs to be stored and managed in
collections such as dictionaries and sets.
"""
import datetime
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any


class Status(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    BLOCKED = "BLOCKED"

class Job(ABC):
    def __init__(self,
                 job_id: int,
                 name: str,
                 priority: int,
                 scheduled_at: datetime.datetime,
                 dependencies: list[int] | None = None,
                 max_retries: int = 3)-> None:
        self.job_id: str = job_id
        self.name: str = name
        self.priority: int = priority
        self.status: Status = Status.PENDING
        self.created_at: datetime = datetime.now()
        self.scheduled_at: datetime = scheduled_at
        self.dependencies: list[str] = dependencies if dependencies is not None else []
        self.retries: int = 0
        self.max_retries: int = max_retries

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
        self.status = Status.CANCELED

    def mark_blocked(self) -> None:
        self.status = Status.BLOCKED

    def register_retry(self) -> None:
        self.retries += 1

    def has_exceeded_retries(self) -> bool:
        return self.retries >= self.max_retries

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
