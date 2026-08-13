import heapq

from models.job import Job


class JobQueue:
    def __init__(self) -> None:
        self._heap: list[Job] = []

    def push(self, job: Job) -> None:
        heapq.heappush(self._heap, job)

    def pop(self) -> Job:
        return heapq.heappop(self._heap)

    def peek(self) -> Job | None:
        return self._heap[0] if self._heap else None

    def remove(self, job_id: str) -> bool:
        original_len = len(self._heap)
        self._heap = [job for job in self._heap if job.job_id != job_id]
        if len(self._heap) == original_len:
            return False
        heapq.heapify(self._heap)
        return True

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def __repr__(self) -> str:
        return f"JobQueue({[job.job_id for job in self._heap]!r})"
