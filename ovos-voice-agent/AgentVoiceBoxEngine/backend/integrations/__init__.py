"""
External service integrations.

Contains clients for:
- Keycloak (authentication)
- OPA (policy enforcement)
- Kafka (event streaming)
- Lago (billing)
- Vault (secrets)
- Temporal (workflows)
"""

from integrations.kafka import KafkaClient, KafkaEvent, kafka_client
from integrations.opa import OPAClient, PolicyDecision, opa_client

__all__ = [
    # OPA
    "OPAClient",
    "PolicyDecision",
    "opa_client",
    # Kafka
    "KafkaClient",
    "KafkaEvent",
    "kafka_client",
]
