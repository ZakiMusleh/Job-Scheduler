"""Represents the outcome of a single job execution attempt.

An ExecutionResult is created every time the Executor runs a job --
whether that attempt succeeds or fails. A list of these forms the
execution history used for reports and CSV export.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionResult:
    job_id: str
    job_type: str
    success: bool
    duration: float
    timestamp: datetime
    attempt_number: int
    output: str | None = None
    error_message: str | None = None

    def __str__(self) -> str:
        outcome = "SUCCESS" if self.success else "FAILURE"
        detail = self.output if self.success else self.error_message
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.job_id} "
            f"(attempt {self.attempt_number}) -> {outcome}: {detail} "
            f"({self.duration:.3f}s)"
        )