import time
from datetime import datetime

from exceptions.errors import JobExecutionError
from models.execution_result import ExecutionResult
from models.job import Job
from utils.decorators import log_execution

class Executor:

    @log_execution
    def run(self, job: Job) -> ExecutionResult:
        attempt_number = job.retries + 1
        start = time.perf_counter()
        output: str | None = None
        error_message: str | None = None
        success = False

        try:
            output = str(job.execute())
            success = True
        except Exception as exc:
            wrapped = JobExecutionError(
                f"Job '{job.job_id}' failed on attempt {attempt_number}: {exc}"
            )
            error_message = str(wrapped)
        finally:
            duration = time.perf_counter() - start
        return ExecutionResult(
            job_id=job.job_id,
            job_type=job.job_type,
            success=success,
            duration=duration,
            timestamp=datetime.now(),
            attempt_number=attempt_number,
            output=output,
            error_message=error_message,
        )



