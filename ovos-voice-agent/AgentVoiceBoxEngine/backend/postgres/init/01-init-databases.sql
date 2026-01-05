-- Create additional databases for Keycloak and Temporal
CREATE DATABASE keycloak;
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE keycloak TO agentvoicebox;
GRANT ALL PRIVILEGES ON DATABASE temporal TO agentvoicebox;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO agentvoicebox;
