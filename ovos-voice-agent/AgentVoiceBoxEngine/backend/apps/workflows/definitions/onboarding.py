"""
Tenant onboarding workflow.

Handles the complete tenant setup process with durable execution.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class OnboardingInput:
    """Input for tenant onboarding workflow."""

    tenant_id: str
    tenant_name: str
    admin_email: str
    tier: str = "free"
    settings: Dict[str, Any] = None


@dataclass
class OnboardingResult:
    """Result of tenant onboarding workflow."""

    tenant_id: str
    success: bool
    steps_completed: List[str]
    errors: List[str]
    duration_ms: float


@workflow.defn(name="TenantOnboardingWorkflow")
class TenantOnboardingWorkflow:
    """
    Workflow for onboarding new tenants.

    Handles:
    - Keycloak group creation
    - SpiceDB permission setup
    - Lago customer creation
    - Default project creation
    - Welcome notification
    """

    def __init__(self):
        self.steps_completed: List[str] = []
        self.errors: List[str] = []

    @workflow.run
    async def run(self, input: OnboardingInput) -> OnboardingResult:
        """
        Run the tenant onboarding workflow.

        Args:
            input: OnboardingInput with tenant details

        Returns:
            OnboardingResult with onboarding status
        """
        import time

        start_time = time.time()

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        workflow.logger.info(
            f"Starting onboarding for tenant {input.tenant_id}"
        )

        # 1. Create Keycloak group
        try:
            await workflow.execute_activity(
                "onboarding_create_keycloak_group",
                input.tenant_id,
                input.tenant_name,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("keycloak_group")
            workflow.logger.info("Created Keycloak group")

        except Exception as e:
            self.errors.append(f"Keycloak group: {str(e)}")
            workflow.logger.error(f"Failed to create Keycloak group: {e}")

        # 2. Setup SpiceDB permissions
        try:
            await workflow.execute_activity(
                "onboarding_setup_spicedb_permissions",
                input.tenant_id,
                input.admin_email,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("spicedb_permissions")
            workflow.logger.info("Setup SpiceDB permissions")

        except Exception as e:
            self.errors.append(f"SpiceDB permissions: {str(e)}")
            workflow.logger.error(f"Failed to setup SpiceDB permissions: {e}")

        # 3. Create Lago customer
        try:
            await workflow.execute_activity(
                "onboarding_create_lago_customer",
                input.tenant_id,
                input.tenant_name,
                input.tier,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("lago_customer")
            workflow.logger.info("Created Lago customer")

        except Exception as e:
            self.errors.append(f"Lago customer: {str(e)}")
            workflow.logger.error(f"Failed to create Lago customer: {e}")

        # 4. Create default project
        try:
            await workflow.execute_activity(
                "onboarding_create_default_project",
                input.tenant_id,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("default_project")
            workflow.logger.info("Created default project")

        except Exception as e:
            self.errors.append(f"Default project: {str(e)}")
            workflow.logger.error(f"Failed to create default project: {e}")

        # 5. Send welcome notification
        try:
            from apps.workflows.activities.notifications import (
                NotificationActivities,
                NotificationRequest,
            )

            await workflow.execute_activity(
                NotificationActivities.send_notification,
                NotificationRequest(
                    tenant_id=input.tenant_id,
                    user_id=None,
                    notification_type="success",
                    title="Welcome to AgentVoiceBox!",
                    message=(
                        f"Your organization '{input.tenant_name}' has been set up. "
                        "Get started by creating your first voice agent."
                    ),
                    channel="in_app",
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("welcome_notification")
            workflow.logger.info("Sent welcome notification")

        except Exception as e:
            self.errors.append(f"Welcome notification: {str(e)}")
            workflow.logger.error(f"Failed to send welcome notification: {e}")

        # 6. Activate tenant
        try:
            await workflow.execute_activity(
                "onboarding_activate_tenant",
                input.tenant_id,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            self.steps_completed.append("tenant_activated")
            workflow.logger.info("Activated tenant")

        except Exception as e:
            self.errors.append(f"Tenant activation: {str(e)}")
            workflow.logger.error(f"Failed to activate tenant: {e}")

        duration = (time.time() - start_time) * 1000
        success = len(self.errors) == 0

        workflow.logger.info(
            f"Onboarding {'completed' if success else 'completed with errors'} "
            f"for tenant {input.tenant_id} in {duration:.0f}ms"
        )

        return OnboardingResult(
            tenant_id=input.tenant_id,
            success=success,
            steps_completed=self.steps_completed,
            errors=self.errors,
            duration_ms=duration,
        )

    @workflow.query(name="get_progress")
    def get_progress(self) -> Dict[str, Any]:
        """Query current onboarding progress."""
        return {
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "total_steps": 6,
            "completed_count": len(self.steps_completed),
        }
