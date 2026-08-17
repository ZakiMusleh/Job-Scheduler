"""Graph structure representing dependencies between jobs.

Each job is a node. An edge from job A to job B means "A depends on B"
(B must complete before A can run). This module is responsible for two
things only: tracking those edges, and refusing to create a cycle. It
knows nothing about job status, priority, or execution.
"""

from exceptions.errors import CircularDependencyError


class DependencyGraph:
    def __init__(self) -> None:
        self._edges: dict[str, set[str]] = {}

    def add_job(self, job_id: str) -> None:
        self._edges.setdefault(job_id, set())

    def remove_job(self, job_id: str) -> None:
        self._edges.pop(job_id, None)
        for dependents in self._edges.values():
            dependents.discard(job_id)

    def _can_reach(self, start: str, target: str) -> bool:
        visited: set[str] = set()
        stack: list[str] = [start]

        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._edges.get(current, set()))

        return False

    def add_dependency(self, job_id: str, depends_on: str) -> None:
        self.add_job(job_id)
        self.add_job(depends_on)

        if job_id == depends_on:
            raise CircularDependencyError(f"Job '{job_id}' cannot depend on itself")

        if self._can_reach(depends_on, job_id):
            raise CircularDependencyError(
                f"Adding dependency '{job_id}' -> '{depends_on}' "
                f"would create a circular dependency"
            )

        self._edges[job_id].add(depends_on)

    def get_dependencies(self, job_id: str) -> set[str]:
        return set(self._edges.get(job_id, set()))

    def get_dependents(self, job_id: str) -> set[str]:
        return {jid for jid, deps in self._edges.items() if job_id in deps}

    def get_dependency_chain(self, job_id: str) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []

        def _visit(node: str) -> None:
            for dep in self._edges.get(node, set()):
                if dep not in visited:
                    visited.add(dep)
                    _visit(dep)
                    order.append(dep)

        _visit(job_id)
        return order

    def __contains__(self, job_id: str) -> bool:
        return job_id in self._edges

    def __len__(self) -> int:
        return len(self._edges)

    def __repr__(self) -> str:
        return f"DependencyGraph({self._edges!r})"