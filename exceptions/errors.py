"""Custom exceptions for the task automation and scheduler."""


class SchedulerError(Exception):

    """Base class for all scheduler-related exceptions."""


class JobNotFoundError(SchedulerError):
    """Raised when a job ID does not exist in the scheduler."""


class InvalidJobError(SchedulerError):
    """Raised when job data fails validation (bad priority, missing fields, etc.)."""


class DependencyError(SchedulerError):
    """Raised when a job depends on a job that does not exist or is invalid."""


class CircularDependencyError(SchedulerError):
    """Raised when adding a dependency would create a cycle (e.g. A -> B -> C -> A)."""


class JobExecutionError(SchedulerError):
    """Raised when a job fails during execution."""