#!/bin/bash
# Initialize Temporal namespace for AgentVoiceBox
# This script creates the agentvoicebox namespace if it doesn't exist

set -e

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-temporal:7233}"
NAMESPACE="${TEMPORAL_NAMESPACE:-agentvoicebox}"

echo "Waiting for Temporal server to be ready..."
until temporal operator cluster health --address "$TEMPORAL_ADDRESS" 2>/dev/null; do
    echo "Temporal not ready, waiting..."
    sleep 5
done

echo "Temporal server is ready. Checking namespace..."

# Check if namespace exists
if temporal operator namespace describe "$NAMESPACE" --address "$TEMPORAL_ADDRESS" 2>/dev/null; then
    echo "Namespace '$NAMESPACE' already exists."
else
    echo "Creating namespace '$NAMESPACE'..."
    temporal operator namespace create "$NAMESPACE" \
        --address "$TEMPORAL_ADDRESS" \
        --retention 72h \
        --description "AgentVoiceBox workflow namespace"
    echo "Namespace '$NAMESPACE' created successfully."
fi

echo "Namespace initialization complete."
