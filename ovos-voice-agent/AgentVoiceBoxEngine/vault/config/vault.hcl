# HashiCorp Vault Configuration for AgentVoiceBox
# All secrets are stored in Vault - NO hardcoded credentials

storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true  # Enable TLS in production with proper certs
}

api_addr = "http://vault:8200"
cluster_addr = "http://vault:8201"

ui = true

# Disable mlock for Docker
disable_mlock = true

# Telemetry for Prometheus
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}
