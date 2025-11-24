"""
Entropy-Reducing Scheduler (ERS) for Phonomicon.

ABX-Core: Scheduler reduces compute resource ambiguity by explicit priority queuing.
Every scheduled job must justify its priority in terms of entropy reduction.

SEED: Deterministic job execution order based on priority and submission time.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Coroutine, Optional
from uuid import uuid4

from phonomicon.config import get_settings

logger = logging.getLogger(__name__)


class JobPriority(IntEnum):
    """
    Job priority levels.

    ABX-Core: Explicit prioritization reduces scheduling ambiguity.

    Priority guidelines:
    - CRITICAL: User-facing operations (e.g., mint requests, real-time analysis)
    - HIGH: Interactive operations (e.g., visual rendering for preview)
    - NORMAL: Batch processing (e.g., corpus feature extraction)
    - LOW: Background tasks (e.g., metric computation, index updates)
    """

    CRITICAL = 4
    HIGH = 3
    NORMAL = 2
    LOW = 1


class JobStatus(IntEnum):
    """Job execution status."""

    QUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5


@dataclass
class Job:
    """
    A scheduled job in the ERS.

    SEED: Complete provenance for job execution.
    """

    job_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = field(default="unnamed_job")
    priority: JobPriority = field(default=JobPriority.NORMAL)
    status: JobStatus = field(default=JobStatus.QUEUED)

    # Job function to execute (async callable)
    func: Optional[Callable[..., Coroutine[Any, Any, Any]]] = field(default=None)
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    # Result and error tracking
    result: Any = field(default=None)
    error: Optional[Exception] = field(default=None)

    # Timestamps (SEED: provenance tracking)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)

    # Resource hints (for future GPU/memory scheduling)
    requires_gpu: bool = field(default=False)
    estimated_memory_mb: Optional[int] = field(default=None)

    def __lt__(self, other: "Job") -> bool:
        """
        Compare jobs for priority queue ordering.

        Higher priority jobs come first. Within same priority, earlier jobs come first.
        ABX-Core: Deterministic ordering reduces execution ambiguity.
        """
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority = lower in min-heap
        return self.created_at < other.created_at  # Earlier = higher priority


class ERSScheduler:
    """
    Entropy-Reducing Scheduler for heavy/async operations.

    ABX-Core: Centralized scheduling reduces compute resource contention (entropy).

    This scheduler:
    - Maintains a priority queue of jobs
    - Executes jobs with worker pool
    - Tracks job provenance (created, started, completed)
    - Provides hooks for GPU resource management
    - Ensures deterministic execution order

    Usage:
        scheduler = ERSScheduler()
        await scheduler.start()

        # Submit a job
        job = await scheduler.submit(
            analyze_audio_heavy,
            args=(audio_data,),
            priority=JobPriority.HIGH,
            requires_gpu=True
        )

        # Wait for completion
        result = await scheduler.wait_for(job.job_id)

        await scheduler.stop()
    """

    def __init__(self, max_workers: int | None = None, gpu_enabled: bool | None = None):
        """
        Initialize ERS scheduler.

        Args:
            max_workers: Maximum concurrent workers (defaults to config)
            gpu_enabled: Whether GPU is available (defaults to config)
        """
        settings = get_settings()

        self.max_workers = max_workers or settings.scheduler_worker_threads
        self.gpu_enabled = gpu_enabled if gpu_enabled is not None else settings.scheduler_gpu_enabled

        # Job storage
        self._queue: asyncio.PriorityQueue[Job] = asyncio.PriorityQueue(
            maxsize=settings.scheduler_queue_size
        )
        self._jobs: dict[str, Job] = {}

        # Worker management
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"ERS Scheduler initialized: workers={self.max_workers}, gpu={self.gpu_enabled}"
        )

    async def start(self) -> None:
        """
        Start scheduler workers.

        ABX-Core: Explicit start/stop reduces lifecycle ambiguity.
        """
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._shutdown_event.clear()

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(worker_id=i))
            self._workers.append(worker)

        logger.info(f"Started {self.max_workers} scheduler workers")

    async def stop(self, timeout: float = 10.0) -> None:
        """
        Stop scheduler workers gracefully.

        Args:
            timeout: Maximum time to wait for workers to finish
        """
        if not self._running:
            return

        logger.info("Stopping scheduler...")
        self._running = False
        self._shutdown_event.set()

        # Wait for workers with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._workers, return_exceptions=True), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Scheduler stop timed out, cancelling workers")
            for worker in self._workers:
                worker.cancel()

        self._workers.clear()
        logger.info("Scheduler stopped")

    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple = (),
        kwargs: dict | None = None,
        name: str = "unnamed_job",
        priority: JobPriority = JobPriority.NORMAL,
        requires_gpu: bool = False,
    ) -> Job:
        """
        Submit a job to the scheduler.

        ABX-Core: Explicit priority declaration reduces scheduling ambiguity.

        Args:
            func: Async function to execute
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            name: Human-readable job name
            priority: Job priority
            requires_gpu: Whether job requires GPU

        Returns:
            Job instance with job_id for tracking

        Raises:
            RuntimeError: If scheduler is not running
            asyncio.QueueFull: If queue is at capacity
        """
        if not self._running:
            raise RuntimeError("Scheduler is not running. Call start() first.")

        job = Job(
            name=name,
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs or {},
            requires_gpu=requires_gpu,
        )

        self._jobs[job.job_id] = job
        await self._queue.put(job)

        logger.debug(
            f"Job submitted: {job.job_id} ({job.name}) priority={job.priority.name}"
        )

        return job

    async def wait_for(self, job_id: str, timeout: float | None = None) -> Any:
        """
        Wait for a job to complete and return its result.

        Args:
            job_id: Job identifier
            timeout: Optional timeout in seconds

        Returns:
            Job result

        Raises:
            KeyError: If job_id not found
            asyncio.TimeoutError: If timeout exceeded
            Exception: If job failed (raises job's exception)
        """
        if job_id not in self._jobs:
            raise KeyError(f"Job not found: {job_id}")

        job = self._jobs[job_id]
        start_time = asyncio.get_event_loop().time()

        # Poll for completion (TODO: replace with asyncio.Event per job)
        while job.status not in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Job {job_id} timed out after {timeout}s")

            await asyncio.sleep(0.1)

        if job.status == JobStatus.FAILED:
            raise job.error or Exception(f"Job {job_id} failed with unknown error")

        if job.status == JobStatus.CANCELLED:
            raise asyncio.CancelledError(f"Job {job_id} was cancelled")

        return job.result

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    async def _worker_loop(self, worker_id: int) -> None:
        """
        Worker loop that processes jobs from the queue.

        ABX-Core: Deterministic job execution reduces scheduling entropy.
        """
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # Get next job (with timeout to check shutdown)
                try:
                    job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Check GPU requirement
                if job.requires_gpu and not self.gpu_enabled:
                    logger.warning(
                        f"Job {job.job_id} requires GPU but GPU is not enabled, skipping"
                    )
                    job.status = JobStatus.FAILED
                    job.error = RuntimeError("GPU not available")
                    continue

                # Execute job
                await self._execute_job(job, worker_id)

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")

    async def _execute_job(self, job: Job, worker_id: int) -> None:
        """
        Execute a single job.

        SEED: Records complete execution provenance.
        """
        logger.debug(f"Worker {worker_id} executing job {job.job_id} ({job.name})")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        try:
            # Execute the job function
            if job.func:
                result = await job.func(*job.args, **job.kwargs)
                job.result = result

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()

            duration = (job.completed_at - job.started_at).total_seconds()
            logger.debug(
                f"Job {job.job_id} completed in {duration:.2f}s by worker {worker_id}"
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = e
            job.completed_at = datetime.utcnow()

            logger.error(
                f"Job {job.job_id} failed: {e}", exc_info=True
            )
