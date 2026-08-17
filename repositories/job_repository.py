"""JSON persistence for the scheduler's job state.

JobRepository is deliberately the only module in the project that
touches the filesystem for job data. Everything else (Scheduler,
Executor, CLI) works with Job objects in memory; this module is
responsible purely for turning that state into JSON on disk and back.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.job import Job
from models.job_types import job_from_dict
from scheduler.scheduler import Scheduler


class JobRepository:

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def save(self, scheduler: Scheduler) -> None:

        payload: list[dict[str, Any]] = [job.to_dict() for job in scheduler.all_jobs()]
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load(self) -> list[Job]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return []

        raw = json.loads(content)
        return [job_from_dict(entry) for entry in raw]

    def load_into(self, scheduler: Scheduler) -> None:
        for job in self.load():
            scheduler.add_job(job)
        scheduler.sync_completed_from_status()