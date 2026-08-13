# Task Automation and Job Scheduler

A command-line job scheduler that creates, schedules, prioritizes, executes,
monitors, and persists jobs, with support for dependencies, retries, and
reporting.

## Installation

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt # only needed for mypy; the app itself
                                 # has no third-party dependencies
```

## Usage

Run the CLI from the project root:

```bash
python main.py
```

On startup, the scheduler automatically restores any previously saved state
from `data/scheduler_state.json` (if it exists). Use menu option **12 (Save
state)** or **0 (Exit)** to persist your current jobs to that file.

### Menu options

| Option | Action |
|---|---|
| 1 | Create a new job (prompts for type-specific fields) |
| 2 | View all jobs |
| 3 | View full details of one job |
| 4 | Cancel a job |
| 5 | Run the scheduler (executes all currently eligible jobs) |
| 6 | Retry a Failed job (resets its retry counter) |
| 7 | Show a job's dependency chain |
| 8 | Search/filter jobs by status or type |
| 9 | View execution history (optionally filtered by job) |
| 10 | Generate summary reports |
| 11 | Export jobs and history to CSV |
| 12 | Save state to disk |
| 0 | Save and exit |

### Supported job types

- `FileProcessingJob` (requires `file_path`)
- `ReportJob` (requires `report_type`)
- `BackupJob` (requires `source_path`)
- `NotificationJob` (requires `recipient`, `message`)

## Project structure

```
job_scheduler/
├── main.py                        # CLI entry point / menu loop
├── models/
│   ├── job.py                     # Abstract Job base class, Status enum
│   ├── job_types.py                # 4 concrete job types + serialization
│   └── execution_result.py         # Outcome of one execution attempt
├── scheduler/
│   ├── job_queue.py                 # Priority queue (heapq wrapper)
│   ├── dependency_graph.py          # Dependency edges + cycle detection
│   ├── job_factory.py               # Validated job creation
│   └── scheduler.py                 # Orchestrates selection/execution rules
├── executors/
│   └── executor.py                  # Runs one job attempt, times it
├── repositories/
│   └── job_repository.py            # JSON persistence
├── reports/
│   └── report_generator.py          # Section 15 reports + CSV export
├── exceptions/
│   └── errors.py                    # Custom exception hierarchy
├── utils/
│   └── decorators.py                # Logging/timing decorator
└── data/
    ├── scheduler_state.json         # Sample persisted state
    ├── jobs_export.csv              # Sample CSV export
    └── history_export.csv           # Sample CSV export
```

## Architecture and design decisions

**Data structures.** Jobs are stored in a `dict[str, Job]` for O(1) lookup by
ID. Eligible jobs are ordered using a `heapq`-based `JobQueue`, since only a
min-heap gives O(log n) selection of the highest-priority, earliest-scheduled
job without sorting the entire job list on every selection. Dependencies are
modeled as a `DependencyGraph` (adjacency list of `dict[str, set[str]]`)
rather than a matrix, since each job typically depends on only a handful of
others — a matrix would waste memory on mostly-empty cells. Completed job IDs
are tracked in a `set` for O(1) membership checks when validating whether a
job's dependencies are satisfied.

**Eligibility recomputation.** Rather than keeping a persistent heap of
"pending" jobs, the `Scheduler` recomputes the eligible set on every call to
`select_next_job()`. A static heap can't react on its own to a dependency
completing or the clock passing a job's `scheduled_at` time, so recomputing a
filtered list each time — then building a short-lived `JobQueue` from it —
keeps the logic correct at the cost of an O(n) scan per selection, which is
an acceptable tradeoff at this scale.

**Circular dependency detection.** Before inserting a new dependency edge,
`DependencyGraph` performs a DFS from the target node to check whether it can
already reach back to the source node. If so, adding the edge would close a
loop, so the edge is rejected before any mutation happens — the graph is
never left in an invalid state, even when a bad dependency is refused.

**Separation of execution and retry policy.** `Job.execute()` only knows how
to perform (simulate) its own operation and raise on failure. The `Executor`
times a single attempt and turns the outcome into an `ExecutionResult`
without ever crashing the caller. The `Scheduler` owns the retry *policy*
(how many attempts, when a job becomes permanently `Failed`). This means a
new job type can be added without touching either the `Executor` or the
`Scheduler` — it only needs to implement `execute()`.

**Persistence.** Every job type implements `to_dict()`/`from_dict()`. A small
type registry (`JOB_TYPE_REGISTRY`) maps a saved `job_type` string back to
the correct class, so `JobRepository` can reconstruct polymorphic job objects
from a flat JSON list without a long if/elif chain — and adding a new job
type only requires one new registry entry.

## Known limitations

- Execution is simulated (per Section 14 of the assignment); no real files,
  reports, backups, or notifications are actually created or sent.
- `JobQueue.remove()` rebuilds the heap in O(n), which is an acceptable
  tradeoff since cancellations are expected to be rare relative to normal
  push/pop activity.
