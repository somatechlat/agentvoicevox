"""
Django management command for running Temporal workers.

Usage:
    python manage.py run_temporal_worker
    python manage.py run_temporal_worker --task-queue voice-processing
    python manage.py run_temporal_worker --create-schedules
"""

import asyncio
import logging
import signal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to run Temporal workers."""

    help = "Run Temporal workflow worker"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--task-queue",
            type=str,
            default=None,
            help="Task queue to listen on (default: from settings)",
        )
        parser.add_argument(
            "--task-queues",
            type=str,
            nargs="+",
            default=None,
            help="Multiple task queues to listen on",
        )
        parser.add_argument(
            "--max-concurrent-activities",
            type=int,
            default=100,
            help="Maximum concurrent activities (default: 100)",
        )
        parser.add_argument(
            "--max-concurrent-workflows",
            type=int,
            default=100,
            help="Maximum concurrent workflows (default: 100)",
        )
        parser.add_argument(
            "--create-schedules",
            action="store_true",
            help="Create workflow schedules before starting worker",
        )
        parser.add_argument(
            "--delete-schedules",
            action="store_true",
            help="Delete workflow schedules and exit",
        )

    def handle(self, *args, **options):
        """Handle the command."""
        self.stdout.write(self.style.SUCCESS("Starting Temporal worker..."))

        try:
            asyncio.run(self._run_worker(options))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nWorker stopped by user"))
        except Exception as e:
            raise CommandError(f"Worker failed: {e}")

    async def _run_worker(self, options):
        """Run the Temporal worker."""
        from temporalio.client import Client
        from temporalio.worker import Worker

        from apps.workflows.activities import (
            BillingActivities,
            CleanupActivities,
            LLMActivities,
            NotificationActivities,
            STTActivities,
            TTSActivities,
        )

        # Import workflows and activities
        from apps.workflows.definitions import (
            BillingSyncWorkflow,
            CleanupWorkflow,
            TenantOnboardingWorkflow,
            VoiceSessionWorkflow,
        )
        from apps.workflows.definitions.cleanup import MetricsAggregationWorkflow

        # Connect to Temporal
        temporal_settings = settings.TEMPORAL
        client = await Client.connect(
            temporal_settings["HOST"],
            namespace=temporal_settings["NAMESPACE"],
        )

        self.stdout.write(
            self.style.SUCCESS(f"Connected to Temporal at {temporal_settings['HOST']}")
        )

        # Handle schedule operations
        if options["delete_schedules"]:
            from apps.workflows.schedules.periodic import delete_schedules

            results = await delete_schedules(client)
            for schedule_id, result in results.items():
                if result["status"] == "deleted":
                    self.stdout.write(
                        self.style.SUCCESS(f"Deleted schedule: {schedule_id}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to delete {schedule_id}: {result.get('error')}"
                        )
                    )
            return

        if options["create_schedules"]:
            from apps.workflows.schedules.periodic import create_schedules

            results = await create_schedules(client)
            for schedule_id, result in results.items():
                if result["status"] == "created":
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created schedule: {schedule_id} ({result['interval']})"
                        )
                    )
                elif result["status"] == "exists":
                    self.stdout.write(
                        self.style.WARNING(f"Schedule exists: {schedule_id}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to create {schedule_id}: {result.get('error')}"
                        )
                    )

        # Determine task queues
        task_queues = options.get("task_queues") or []
        if options.get("task_queue"):
            task_queues.append(options["task_queue"])
        if not task_queues:
            task_queues = [temporal_settings["TASK_QUEUE"]]

        # All workflows
        workflows = [
            VoiceSessionWorkflow,
            BillingSyncWorkflow,
            CleanupWorkflow,
            TenantOnboardingWorkflow,
            MetricsAggregationWorkflow,
        ]

        # All activity instances
        activities = [
            STTActivities(),
            TTSActivities(),
            LLMActivities(),
            BillingActivities(),
            NotificationActivities(),
            CleanupActivities(),
        ]

        # Collect all activity methods
        activity_methods = []
        for activity_instance in activities:
            for attr_name in dir(activity_instance):
                attr = getattr(activity_instance, attr_name)
                if hasattr(attr, "__temporal_activity_definition"):
                    activity_methods.append(attr)

        # Create workers for each task queue
        workers = []
        for task_queue in task_queues:
            worker = Worker(
                client,
                task_queue=task_queue,
                workflows=workflows,
                activities=activity_methods,
                max_concurrent_activities=options["max_concurrent_activities"],
                max_concurrent_workflow_tasks=options["max_concurrent_workflows"],
            )
            workers.append(worker)

            self.stdout.write(
                self.style.SUCCESS(f"Worker configured for queue: {task_queue}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting {len(workers)} worker(s) with "
                f"{len(workflows)} workflows and {len(activity_methods)} activities"
            )
        )

        # Setup graceful shutdown
        shutdown_event = asyncio.Event()

        def signal_handler():
            """
            Handles OS signals for graceful shutdown.

            Sets the `shutdown_event` to signal workers to stop.
            """
            self.stdout.write(self.style.WARNING("\nShutting down workers..."))
            shutdown_event.set()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        # Run workers
        try:
            async with asyncio.TaskGroup() as tg:
                for worker in workers:
                    tg.create_task(worker.run())

                # Wait for shutdown signal
                await shutdown_event.wait()

                # Cancel all worker tasks
                for task in tg._tasks:
                    task.cancel()

        except* asyncio.CancelledError:
            pass

        self.stdout.write(self.style.SUCCESS("Workers stopped gracefully"))
