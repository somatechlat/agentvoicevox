"""Seed Lago with billable metrics and plans."""

import json
from pathlib import Path

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def load_json(filename: str) -> dict:
    """Load JSON file from seed directory."""
    seed_dir = Path(settings.BASE_DIR).parent / "lago" / "seed"
    path = seed_dir / filename
    if not path.exists():
        raise CommandError(f"Seed file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def create_billable_metrics(client: httpx.Client, api_url: str, api_key: str) -> None:
    """Create billable metrics in Lago."""
    data = load_json("billable_metrics.json")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for metric in data.get("billable_metrics", []):
        payload = {"billable_metric": metric}
        response = client.post(
            f"{api_url}/api/v1/billable_metrics",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            continue
        if response.status_code == 422:
            response = client.put(
                f"{api_url}/api/v1/billable_metrics/{metric['code']}",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                continue
        raise CommandError(f"Failed to create/update metric {metric['code']}: {response.text}")


def create_plans(client: httpx.Client, api_url: str, api_key: str) -> None:
    """Create subscription plans in Lago."""
    data = load_json("plans.json")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for plan in data.get("plans", []):
        payload = {"plan": plan}
        response = client.post(
            f"{api_url}/api/v1/plans",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            continue
        if response.status_code == 422:
            response = client.put(
                f"{api_url}/api/v1/plans/{plan['code']}",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                continue
        raise CommandError(f"Failed to create/update plan {plan['code']}: {response.text}")


class Command(BaseCommand):
    """
    Django management command to seed the Lago billing system with AgentVoiceBox's
    billable metrics and plans.

    This command is used to initialize or update the billing configuration in Lago,
    ensuring that the platform's usage tracking and subscription plans are correctly
    defined in the external billing provider.
    """

    help = "Seed Lago with AgentVoiceBox billing configuration"

    def add_arguments(self, parser):
        """
        Adds command-line arguments to the management command.

        Args:
            parser: The argument parser object.
        """
        parser.add_argument("--api-key", required=True, help="Lago API key")

    def handle(self, *args, **options):
        """
        Executes the command to connect to Lago and seed it with billing data.

        This method performs a health check on the Lago API, then calls helper
        functions to create or update billable metrics and plans.
        """
        api_key = options["api_key"]
        api_url = getattr(settings, "LAGO_API_URL", None)
        if not api_url:
            raise CommandError("LAGO_API_URL is required")

        with httpx.Client(timeout=30.0) as client:
            try:
                response = client.get(f"{api_url}/health")
                response.raise_for_status()
            except httpx.RequestError as exc:
                raise CommandError(f"Cannot connect to Lago at {api_url}: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                raise CommandError(f"Lago health check failed: {exc.response.status_code}") from exc

            create_billable_metrics(client, api_url, api_key)
            create_plans(client, api_url, api_key)

        self.stdout.write(self.style.SUCCESS("Lago seeding complete"))
