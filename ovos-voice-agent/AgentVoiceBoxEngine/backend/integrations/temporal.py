"""
Temporal workflow orchestration client.

Provides workflow execution and management via Temporal.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional, Type

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class WorkflowExecution:
    """Workflow execution result."""

    workflow_id: str
    run_id: str
    status: str


@dataclass
class WorkflowInfo:
    """Workflow information."""

    workflow_id: str
    run_id: str
    workflow_type: str
    status: str
    start_time: Optional[str] = None
    close_time: Optional[str] = None


class TemporalClient:
    """
    Temporal client for workflow orchestration.

    Handles:
    - Workflow execution
    - Activity management
    - Schedule management
    - Workflow queries
    """

    def __init__(self):
        """Initialize Temporal client from Django settings."""
        self.host = settings.TEMPORAL["HOST"]
        self.namespace = settings.TEMPORAL["NAMESPACE"]
        self.task_queue = settings.TEMPORAL["TASK_QUEUE"]

        self._client = None

    async def connect(self) -> None:
        """Connect to Temporal server."""
        try:
            from temporalio.client import Client

            self._client = await Client.connect(
                self.host,
                namespace=self.namespace,
            )
            logger.info(f"Connected to Temporal at {self.host}")
        except Exception as e:
            logger.error(f"Failed to connect to Temporal: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Temporal server."""
        self._client = None

    async def _get_client(self):
        """Get or create Temporal client."""
        if self._client is None:
            await self.connect()
        return self._client

    async def start_workflow(
        self,
        workflow: str,
        workflow_id: str,
        args: List[Any],
        task_queue: Optional[str] = None,
        execution_timeout: Optional[timedelta] = None,
        run_timeout: Optional[timedelta] = None,
        task_timeout: Optional[timedelta] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """
        Start a workflow execution.

        Args:
            workflow: Workflow class or name
            workflow_id: Unique workflow ID
            args: Workflow arguments
            task_queue: Task queue (defaults to configured queue)
            execution_timeout: Total workflow timeout
            run_timeout: Single run timeout
            task_timeout: Task timeout
            retry_policy: Retry configuration

        Returns:
            WorkflowExecution with workflow_id and run_id
        """
        try:
            from temporalio.client import Client
            from temporalio.common import RetryPolicy

            client = await self._get_client()

            # Build retry policy if provided
            temporal_retry = None
            if retry_policy:
                temporal_retry = RetryPolicy(
                    initial_interval=timedelta(
                        seconds=retry_policy.get("initial_interval_seconds", 1)
                    ),
                    backoff_coefficient=retry_policy.get("backoff_coefficient", 2.0),
                    maximum_interval=timedelta(
                        seconds=retry_policy.get("maximum_interval_seconds", 60)
                    ),
                    maximum_attempts=retry_policy.get("maximum_attempts", 3),
                )

            handle = await client.start_workflow(
                workflow,
                *args,
                id=workflow_id,
                task_queue=task_queue or self.task_queue,
                execution_timeout=execution_timeout,
                run_timeout=run_timeout,
                task_timeout=task_timeout,
                retry_policy=temporal_retry,
            )

            return WorkflowExecution(
                workflow_id=handle.id,
                run_id=handle.result_run_id,
                status="running",
            )

        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_id}: {e}")
            raise

    async def execute_workflow(
        self,
        workflow: str,
        workflow_id: str,
        args: List[Any],
        task_queue: Optional[str] = None,
        execution_timeout: Optional[timedelta] = None,
    ) -> Any:
        """
        Execute a workflow and wait for result.

        Args:
            workflow: Workflow class or name
            workflow_id: Unique workflow ID
            args: Workflow arguments
            task_queue: Task queue
            execution_timeout: Total workflow timeout

        Returns:
            Workflow result
        """
        try:
            client = await self._get_client()

            result = await client.execute_workflow(
                workflow,
                *args,
                id=workflow_id,
                task_queue=task_queue or self.task_queue,
                execution_timeout=execution_timeout,
            )

            return result

        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise

    async def get_workflow_handle(self, workflow_id: str, run_id: Optional[str] = None):
        """Get a handle to an existing workflow."""
        client = await self._get_client()
        return client.get_workflow_handle(workflow_id, run_id=run_id)

    async def get_workflow_result(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> Any:
        """Get the result of a completed workflow."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        return await handle.result()

    async def cancel_workflow(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> None:
        """Cancel a running workflow."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        await handle.cancel()

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: str = "",
        run_id: Optional[str] = None,
    ) -> None:
        """Terminate a running workflow."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        await handle.terminate(reason=reason)

    async def signal_workflow(
        self,
        workflow_id: str,
        signal: str,
        args: List[Any],
        run_id: Optional[str] = None,
    ) -> None:
        """Send a signal to a workflow."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        await handle.signal(signal, *args)

    async def query_workflow(
        self,
        workflow_id: str,
        query: str,
        args: List[Any] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """Query a workflow for its current state."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        return await handle.query(query, *(args or []))

    async def describe_workflow(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> WorkflowInfo:
        """Get information about a workflow execution."""
        handle = await self.get_workflow_handle(workflow_id, run_id)
        desc = await handle.describe()

        return WorkflowInfo(
            workflow_id=desc.id,
            run_id=desc.run_id,
            workflow_type=desc.workflow_type,
            status=str(desc.status),
            start_time=str(desc.start_time) if desc.start_time else None,
            close_time=str(desc.close_time) if desc.close_time else None,
        )

    async def list_workflows(
        self,
        query: Optional[str] = None,
        page_size: int = 100,
    ) -> List[WorkflowInfo]:
        """List workflow executions."""
        client = await self._get_client()

        workflows = []
        async for workflow in client.list_workflows(query=query, page_size=page_size):
            workflows.append(
                WorkflowInfo(
                    workflow_id=workflow.id,
                    run_id=workflow.run_id,
                    workflow_type=workflow.workflow_type,
                    status=str(workflow.status),
                    start_time=str(workflow.start_time) if workflow.start_time else None,
                    close_time=str(workflow.close_time) if workflow.close_time else None,
                )
            )

        return workflows


# Singleton instance
temporal_client = TemporalClient()
