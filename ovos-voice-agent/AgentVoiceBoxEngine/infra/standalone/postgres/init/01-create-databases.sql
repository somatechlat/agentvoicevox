-- ==========================================================================
-- SHARED POSTGRESQL - Database Initialization
-- ==========================================================================
-- Creates databases for all applications that use this shared PostgreSQL
-- ==========================================================================

-- Create Keycloak database
CREATE DATABASE keycloak
    WITH OWNER = shared_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create AgentVoiceBox database
CREATE DATABASE agentvoicebox
    WITH OWNER = shared_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create Temporal database
CREATE DATABASE temporal
    WITH OWNER = shared_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create Temporal visibility database
CREATE DATABASE temporal_visibility
    WITH OWNER = shared_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE keycloak TO shared_admin;
GRANT ALL PRIVILEGES ON DATABASE agentvoicebox TO shared_admin;
GRANT ALL PRIVILEGES ON DATABASE temporal TO shared_admin;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO shared_admin;

-- Log completion
\echo 'Shared databases created successfully!'
\echo 'Databases: keycloak, agentvoicebox, temporal, temporal_visibility'
