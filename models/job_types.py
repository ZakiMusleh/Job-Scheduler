"""Concrete job types.

Each class inherits from Job and overrides execute() with its own
simulated behavior (random short delay, small chance of simulated
failure). The Scheduler and Executor never need to know which
concrete type they are dealing with -- they only ever call
job.execute() through the Job interface, so a new job type can be
added here without touching either of them.
"""

import random
import time
from datetime import datetime
from typing import Any

from models.job import Job


class FileProcessingJob(Job):

    def __init__(self, *args: Any, file_path: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.file_path: str = file_path

    def execute(self) -> str:
        time.sleep(random.uniform(0.05, 0.2))
        if random.random() < 0.15:
            raise RuntimeError(f"Failed to process file '{self.file_path}'")
        return f"Processed file '{self.file_path}' successfully"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["file_path"] = self.file_path
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileProcessingJob":
        job = cls(
            job_id=data["job_id"],
            name=data["name"],
            priority=data["priority"],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
            dependencies=data["dependencies"],
            max_retries=data["max_retries"],
            file_path=data["file_path"],
        )
        job._restore_runtime_state(data)
        return job


class ReportJob(Job):
    def __init__(self, *args: Any, report_type: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.report_type: str = report_type

    def execute(self) -> str:
        time.sleep(random.uniform(0.05, 0.2))
        if random.random() < 0.15:
            raise RuntimeError(f"Failed to generate report '{self.report_type}'")
        return f"Generated '{self.report_type}' report successfully"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["report_type"] = self.report_type
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportJob":
        job = cls(
            job_id=data["job_id"],
            name=data["name"],
            priority=data["priority"],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
            dependencies=data["dependencies"],
            max_retries=data["max_retries"],
            report_type=data["report_type"],
        )
        job._restore_runtime_state(data)
        return job


class BackupJob(Job):
    def __init__(self, *args: Any, source_path: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.source_path: str = source_path

    def execute(self) -> str:
        time.sleep(random.uniform(0.05, 0.2))
        if random.random() < 0.15:
            raise RuntimeError(f"Backup failed for '{self.source_path}'")
        return f"Backed up '{self.source_path}' successfully"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["source_path"] = self.source_path
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupJob":
        job = cls(
            job_id=data["job_id"],
            name=data["name"],
            priority=data["priority"],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
            dependencies=data["dependencies"],
            max_retries=data["max_retries"],
            source_path=data["source_path"],
        )
        job._restore_runtime_state(data)
        return job


class NotificationJob(Job):
    def __init__(self, *args: Any, recipient: str, message: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.recipient: str = recipient
        self.message: str = message

    def execute(self) -> str:
        time.sleep(random.uniform(0.05, 0.2))
        if random.random() < 0.15:
            raise RuntimeError(f"Failed to notify '{self.recipient}'")
        return f"Notified '{self.recipient}': {self.message}"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["recipient"] = self.recipient
        data["message"] = self.message
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationJob":
        job = cls(
            job_id=data["job_id"],
            name=data["name"],
            priority=data["priority"],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
            dependencies=data["dependencies"],
            max_retries=data["max_retries"],
            recipient=data["recipient"],
            message=data["message"],
        )
        job._restore_runtime_state(data)
        return job


JOB_TYPE_REGISTRY: dict[str, type[Job]] = {
    "FileProcessingJob": FileProcessingJob,
    "ReportJob": ReportJob,
    "BackupJob": BackupJob,
    "NotificationJob": NotificationJob,
}


def job_from_dict(data: dict[str, Any]) -> Job:
    job_type = data["job_type"]
    job_cls = JOB_TYPE_REGISTRY.get(job_type)
    if job_cls is None:
        raise ValueError(f"Unknown job_type '{job_type}' in saved data")
    job: Job = job_cls.from_dict(data)  # type: ignore[attr-defined]
    return job