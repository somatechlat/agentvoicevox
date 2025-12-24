"""
Task queue configuration for Temporal workflows.

Defines task queues and routing rules for different workflow types.
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TaskQueueConfig:
    """Configuration for a task queue."""

    name: str
    description: str
    workflows: List[str]
    max_concurrent_activities: int = 100
    max_concurrent_workflows: int = 100


# Task queue definitions
TASK_QUEUES: Dict[str, TaskQueueConfig] = {
    "default": TaskQueueConfig(
        name="default",
        description="Default task queue for general workflows",
        workflows=[
            "CleanupWorkflow",
            "MetricsAggregationWorkflow",
            "TenantOnboardingWorkflow",
        ],
        max_concurrent_activities=100,
        max_concurrent_workflows=100,
    ),
    "voice-processing": TaskQueueConfig(
        name="voice-processing",
        description="Task queue for voice processing workflows (STT, TTS, LLM)",
        workflows=[
            "VoiceSessionWorkflow",
        ],
        max_concurrent_activities=50,  # Lower due to resource intensity
        max_concurrent_workflows=50,
    ),
    "billing": TaskQueueConfig(
        name="billing",
        description="Task queue for billing-related workflows",
        workflows=[
            "BillingSyncWorkflow",
        ],
        max_concurrent_activities=20,
        max_concurrent_workflows=20,
    ),
    "notifications": TaskQueueConfig(
        name="notifications",
        description="Task queue for notification workflows",
        workflows=[],  # Notifications are activities, not workflows
        max_concurrent_activities=100,
        max_concurrent_workflows=10,
    ),
}


def get_task_queue_for_workflow(workflow_type: str) -> str:
    """
    Get the appropriate task queue for a workflow type.

    Args:
        workflow_type: Name of the workflow

    Returns:
        Task queue name
    """
    for queue_name, config in TASK_QUEUES.items():
        if workflow_type in config.workflows:
            return queue_name

    return "default"


def get_all_task_queues() -> List[str]:
    """Get all defined task queue names."""
    return list(TASK_QUEUES.keys())


def get_task_queue_config(queue_name: str) -> TaskQueueConfig:
    """
    Get configuration for a task queue.

    Args:
        queue_name: Name of the task queue

    Returns:
        TaskQueueConfig for the queue

    Raises:
        KeyError: If queue doesn't exist
    """
    return TASK_QUEUES[queue_name]
