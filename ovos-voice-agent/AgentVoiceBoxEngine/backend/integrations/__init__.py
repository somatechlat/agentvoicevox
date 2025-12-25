"""
External service integrations.

Contains clients for:
- Keycloak (authentication)
- SpiceDB (authorization)
- OPA (policy enforcement)
- Kafka (event streaming)
- Lago (billing)
- Vault (secrets)
- Temporal (workflows)
"""
from integrations.kafka import KafkaClient, KafkaEvent, kafka_client
from integrations.opa import OPAClient, PolicyDecision, opa_client
from integrations.spicedb import Permission, Relationship, SpiceDBClient, spicedb_client

__all__ = [
    # OPA
    "OPAClient",
    "PolicyDecision",
    "opa_client",
    # Kafka
    "KafkaClient",
    "KafkaEvent",
    "kafka_client",
    # SpiceDB
    "SpiceDBClient",
    "Permission",
    "Relationship",
    "spicedb_client",
]
