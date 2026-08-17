"""Command-line entry point for the Task Automation and Job Scheduler.

This module contains no scheduling, execution, or persistence logic
of its own -- it only orchestrates calls into Scheduler, Executor,
JobRepository, and ReportGenerator, and handles user I/O. Keeping it
thin means the "real" logic stays independently testable in its own
modules (as demonstrated throughout this project's tests).
"""

from __future__ import annotations

import logging
from datetime import datetime

from exceptions.errors import SchedulerError
from executors.executor import Executor
from models.execution_result import ExecutionResult
from reports.report_generator import ReportGenerator
from repositories.job_repository import JobRepository
from scheduler.job_factory import VALID_JOB_TYPES, create_job
from scheduler.scheduler import Scheduler

logging.getLogger("job_scheduler").setLevel(logging.WARNING)

DATA_FILE = "data/scheduler_state.json"
JOBS_CSV = "data/jobs_export.csv"
HISTORY_CSV = "data/history_export.csv"

MENU = """
==================== Task Scheduler ====================
 1. Create job
 2. View jobs
 3. View job details
 4. Cancel job
 5. Run scheduler
 6. Retry failed job
 7. Show dependency tree
 8. Search and filter jobs
 9. View execution history
10. Generate reports
11. Export CSV
12. Save state
 0. Exit
==========================================================
"""


def prompt(text: str) -> str:
    return input(text).strip()


def prompt_int(text: str, default: int | None = None) -> int:
    raw = prompt(text)
    if not raw and default is not None:
        return default
    return int(raw)


def create_job_flow(scheduler: Scheduler) -> None:
    print(f"Job types: {', '.join(VALID_JOB_TYPES)}")
    job_type = prompt("Job type: ")
    job_id = scheduler.generate_job_id()
    name = prompt("Job name: ")
    priority = prompt_int("Priority (integer, higher = more urgent): ")
    max_retries = prompt_int("Max retries [3]: ", default=3)
    deps_raw = prompt("Dependency job IDs (comma-separated, blank for none): ")
    dependencies = [d.strip() for d in deps_raw.split(",") if d.strip()]

    type_fields: dict[str, str] = {}
    if job_type == "FileProcessingJob":
        type_fields["file_path"] = prompt("File path: ")
    elif job_type == "ReportJob":
        type_fields["report_type"] = prompt("Report type: ")
    elif job_type == "BackupJob":
        type_fields["source_path"] = prompt("Source path: ")
    elif job_type == "NotificationJob":
        type_fields["recipient"] = prompt("Recipient: ")
        type_fields["message"] = prompt("Message: ")

    job = create_job(
        job_type=job_type,
        job_id=job_id,
        name=name,
        priority=priority,
        scheduled_at=datetime.now(),
        dependencies=dependencies,
        max_retries=max_retries,
        **type_fields,
    )
    scheduler.add_job(job)
    print(f"Created {job} (assigned ID: {job_id})")


def view_jobs(scheduler: Scheduler) -> None:
    jobs = scheduler.all_jobs()
    if not jobs:
        print("No jobs yet.")
        return
    for job in jobs:
        print(f"  {job}")


def view_job_details(scheduler: Scheduler) -> None:
    job_id = prompt("Job ID: ")
    job = scheduler.get_job(job_id)
    print(repr(job))


def cancel_job_flow(scheduler: Scheduler) -> None:
    job_id = prompt("Job ID to cancel: ")
    scheduler.cancel_job(job_id)
    print(f"Job '{job_id}' cancelled.")


def run_scheduler_flow(
    scheduler: Scheduler, executor: Executor, history: list[ExecutionResult]
) -> None:
    now = datetime.now()
    ran_any = False
    while True:
        job = scheduler.select_next_job(now)
        if job is None:
            break
        ran_any = True
        result = executor.run(job)
        history.append(result)
        if result.success:
            scheduler.record_success(job.job_id)
        else:
            scheduler.record_failure(job.job_id)
        print(f"  {result}")
    if not ran_any:
        print("No eligible jobs to run right now.")


def retry_job_flow(scheduler: Scheduler) -> None:
    job_id = prompt("Failed job ID to retry: ")
    scheduler.retry_job(job_id)
    print(f"Job '{job_id}' reset to Pending and ready to retry.")


def show_dependency_tree(scheduler: Scheduler) -> None:
    job_id = prompt("Job ID: ")
    scheduler.get_job(job_id)  # validates the ID exists; raises JobNotFoundError if not
    chain = scheduler.get_dependency_chain(job_id)
    if not chain:
        print(f"'{job_id}' has no dependencies.")
        return
    print(
        f"Dependency chain for '{job_id}' (deepest first): {' -> '.join(chain)} -> {job_id}"
    )


def search_and_filter(scheduler: Scheduler) -> None:
    status_filter = prompt("Filter by status (blank for any): ")
    type_filter = prompt("Filter by job type (blank for any): ")

    results = scheduler.all_jobs()
    if status_filter:
        results = [
            j for j in results if j.status.value.lower() == status_filter.lower()
        ]
    if type_filter:
        results = [j for j in results if j.job_type.lower() == type_filter.lower()]

    if not results:
        print("No matching jobs.")
        return
    for job in results:
        print(f"  {job}")


def view_execution_history(report: ReportGenerator) -> None:
    job_id = prompt("Job ID (blank for all): ")
    results = report.iter_history(job_id or None)
    count = 0
    for result in results:
        print(f"  {result}")
        count += 1
    if count == 0:
        print("No execution history yet.")


def generate_reports(report: ReportGenerator) -> None:
    summary = report.summary()
    print("Jobs by status:      ", summary["total_jobs_by_status"])
    print("Failed + retries:    ", summary["failed_jobs_with_retries"])
    print("Avg duration (s):    ", summary["average_duration_seconds"])
    print("Most frequent types: ", summary["most_frequent_job_types"])
    print("Blocked job IDs:     ", summary["blocked_job_ids"])
    print("Exceeded retry limit:", summary["jobs_exceeded_retry_limit"])


def export_csv(report: ReportGenerator) -> None:
    report.export_jobs_csv(JOBS_CSV)
    report.export_history_csv(HISTORY_CSV)
    print(f"Exported jobs to {JOBS_CSV} and history to {HISTORY_CSV}")


def save_state(scheduler: Scheduler, repo: JobRepository) -> None:
    repo.save(scheduler)
    print(f"Saved scheduler state to {DATA_FILE}")


def main() -> None:
    scheduler = Scheduler()
    executor = Executor()
    history: list[ExecutionResult] = []
    repo = JobRepository(DATA_FILE)

    repo.load_into(scheduler)
    if len(scheduler) > 0:
        print(f"Restored {len(scheduler)} job(s) from {DATA_FILE}")

    actions = {
        "1": lambda: create_job_flow(scheduler),
        "2": lambda: view_jobs(scheduler),
        "3": lambda: view_job_details(scheduler),
        "4": lambda: cancel_job_flow(scheduler),
        "5": lambda: run_scheduler_flow(scheduler, executor, history),
        "6": lambda: retry_job_flow(scheduler),
        "7": lambda: show_dependency_tree(scheduler),
        "8": lambda: search_and_filter(scheduler),
        "9": lambda: view_execution_history(ReportGenerator(scheduler, history)),
        "10": lambda: generate_reports(ReportGenerator(scheduler, history)),
        "11": lambda: export_csv(ReportGenerator(scheduler, history)),
        "12": lambda: save_state(scheduler, repo),
    }

    while True:
        print(MENU)
        choice = prompt("Choose an option: ")

        if choice == "0":
            save_state(scheduler, repo)
            print("Goodbye.")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid option, try again.")
            continue

        try:
            action()
        except SchedulerError as exc:
            print(f"Error: {exc}")
        except ValueError as exc:
            print(f"Invalid input: {exc}")
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting.")
            break


if __name__ == "__main__":
    main()