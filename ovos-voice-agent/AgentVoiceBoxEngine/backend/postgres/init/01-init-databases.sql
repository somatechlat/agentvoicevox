-- ==========================================================================
-- AgentVoiceBox PostgreSQL Initialization
-- ==========================================================================
-- Creates additional databases required by services

-- Create Keycloak database
CREATE DATABASE keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO agentvoicebox;

-- Create SpiceDB database
CREATE DATABASE spicedb;
GRANT ALL PRIVILEGES ON DATABASE spicedb TO agentvoicebox;

-- Create Temporal databases
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
GRANT ALL PRIVILEGES ON DATABASE temporal TO agentvoicebox;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO agentvoicebox;

-- Enable required extensions on main database
\c agentvoicebox;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schema for audit logs (separate for performance)
CREATE SCHEMA IF NOT EXISTS audit;
GRANT ALL ON SCHEMA audit TO agentvoicebox;
