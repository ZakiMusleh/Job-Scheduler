import csv
from collections import Counter
from functools import reduce
from pathlib import Path
from typing import Iterator

from models.execution_result import ExecutionResult
from models.job import Job, Status
from scheduler.scheduler import Scheduler

class ReportGenerator:

    def __init__(self, scheduler: Scheduler, history: list[ExecutionResult]) -> None:
        self.scheduler = scheduler
        self.history = history

    def iter_history(self, job_id: str | None = None) -> Iterator[ExecutionResult]:
        for result in self.history:
            if job_id is None or result.job_id == job_id:
                yield result

    def total_jobs_by_status(self) -> dict[str, int]:
        counts = Counter(job.status.value for job in self.scheduler.all_jobs())
        return dict(counts)

    def failed_jobs_with_retry_counts(self) -> list[tuple[str, int]]:

        failed = filter(lambda j: j.status == Status.FAILED, self.scheduler.all_jobs())
        return [(job.job_id, job.retries) for job in failed]

    def average_execution_duration(self) -> float:
        if not self.history:
            return 0.0
        total = reduce(lambda acc, result: acc + result.duration, self.history, 0.0)
        return total / len(self.history)

    def most_frequent_job_types(self) -> list[tuple[str, int]]:
        type_counts = Counter(result.job_type for result in self.history)
        return type_counts.most_common()

    def jobs_blocked_by_dependencies(self) -> list[Job]:
        return list(filter(lambda j: j.status == Status.BLOCKED, self.scheduler.all_jobs()))

    def jobs_exceeded_retry_limit(self) -> list[Job]:
        return [
            job
            for job in self.scheduler.all_jobs()
            if job.status == Status.FAILED and job.retries >= job.max_retries
        ]

    def execution_history_for_job(self, job_id: str) -> list[ExecutionResult]:
        return list(self.iter_history(job_id))

    def jobs_sorted_by_priority(self) -> list[Job]:
        return sorted(self.scheduler.all_jobs(), key=lambda job: job.priority, reverse=True)

    def export_history_csv(self, file_path: str | Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "job_id",
            "job_type",
            "attempt_number",
            "success",
            "duration",
            "timestamp",
            "output",
            "error_message",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.iter_history():
                writer.writerow(
                    {
                        "job_id": result.job_id,
                        "job_type": result.job_type,
                        "attempt_number": result.attempt_number,
                        "success": result.success,
                        "duration": f"{result.duration:.4f}",
                        "timestamp": result.timestamp.isoformat(),
                        "output": result.output or "",
                        "error_message": result.error_message or "",
                    }
                )

    def export_jobs_csv(self, file_path: str | Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "job_id",
            "job_type",
            "name",
            "priority",
            "status",
            "scheduled_at",
            "dependencies",
            "retries",
            "max_retries",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for job in self.jobs_sorted_by_priority():
                writer.writerow(
                    {
                        "job_id": job.job_id,
                        "job_type": job.job_type,
                        "name": job.name,
                        "priority": job.priority,
                        "status": job.status.value,
                        "scheduled_at": job.scheduled_at.isoformat(),
                        "dependencies": ";".join(job.dependencies),
                        "retries": job.retries,
                        "max_retries": job.max_retries,
                    }
                )
    def summary(self) -> dict[str, object]:
        return {
            "total_jobs_by_status": self.total_jobs_by_status(),
            "failed_jobs_with_retries": self.failed_jobs_with_retry_counts(),
            "average_duration_seconds": round(self.average_execution_duration(), 4),
            "most_frequent_job_types": self.most_frequent_job_types(),
            "blocked_job_ids": list(map(lambda j: j.job_id, self.jobs_blocked_by_dependencies())),
            "jobs_exceeded_retry_limit": list(
                map(lambda j: j.job_id, self.jobs_exceeded_retry_limit())
            ),
        }
