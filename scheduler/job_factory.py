"""Factory functions for creating validated Job instances.

This is the single place where user-supplied input (from the CLI) is
turned into Job objects. Keeping validation here -- rather than
scattered across the CLI or inside Job.__init__ -- means there is one
place to check when asking "where does bad input get rejected?" Job
IDs themselves are NOT typed by the user; the CLI generates them
automatically via Scheduler.generate_job_id() and passes the result
in here as job_id.
"""

from datetime import datetime

from exceptions.errors import InvalidJobError
from models.job import Job
from models.job_types import (
    BackupJob,
    FileProcessingJob,
    NotificationJob,
    ReportJob,
)

VALID_JOB_TYPES = ("FileProcessingJob", "ReportJob", "BackupJob", "NotificationJob")


def _validate_common(
    job_id: str,
    name: str,
    priority: int,
    max_retries: int,
) -> None:
    if not job_id or not job_id.strip():
        raise InvalidJobError("Job ID cannot be empty")
    if not name or not name.strip():
        raise InvalidJobError("Job name cannot be empty")
    if priority < 0:
        raise InvalidJobError("Priority must be a non-negative integer")
    if max_retries < 0:
        raise InvalidJobError("Max retries must be a non-negative integer")


def create_job(
    job_type: str,
    job_id: str,
    name: str,
    priority: int,
    scheduled_at: datetime,
    dependencies: list[str] | None = None,
    max_retries: int = 3,
    **type_specific_fields: str,
) -> Job:
    _validate_common(job_id, name, priority, max_retries)

    dependencies = dependencies or []
    common_kwargs = {
        "job_id": job_id,
        "name": name,
        "priority": priority,
        "scheduled_at": scheduled_at,
        "dependencies": dependencies,
        "max_retries": max_retries,
    }

    try:
        if job_type == "FileProcessingJob":
            return FileProcessingJob(
                **common_kwargs, file_path=type_specific_fields["file_path"]
            )
        if job_type == "ReportJob":
            return ReportJob(
                **common_kwargs, report_type=type_specific_fields["report_type"]
            )
        if job_type == "BackupJob":
            return BackupJob(
                **common_kwargs, source_path=type_specific_fields["source_path"]
            )
        if job_type == "NotificationJob":
            return NotificationJob(
                **common_kwargs,
                recipient=type_specific_fields["recipient"],
                message=type_specific_fields["message"],
            )
    except KeyError as exc:
        raise InvalidJobError(
            f"Missing required field {exc} for job type '{job_type}'"
        ) from exc

    raise InvalidJobError(
        f"Unknown job_type '{job_type}'. Must be one of {VALID_JOB_TYPES}"
    )