# Requirements Document: Keycloak OAuth and Infrastructure Fix

## Introduction

This document specifies the requirements for fixing the Keycloak OAuth configuration and Temporal workflow infrastructure in the AgentVoiceBox platform. The current implementation has missing OAuth scopes causing authentication failures and no running Temporal workflows.

## Glossary

- **Keycloak**: Open-source identity and access management solution providing SSO and OAuth2/OIDC
- **Client_Scope**: A Keycloak concept that defines a set of claims and mappers to include in tokens
- **Identity_Provider**: External authentication provider (Google, GitHub) integrated via Keycloak
- **Temporal**: Workflow orchestration platform for durable execution of business processes
- **Temporal_Namespace**: Isolated environment within Temporal for organizing workflows
- **Onboarding_Workflow**: Temporal workflow that provisions new tenants with required resources

---

## Requirements

### Requirement 1: Keycloak Client Scopes Configuration

**User Story:** As a developer, I want Keycloak to have properly configured OAuth scopes, so that authentication flows work correctly with standard OIDC scopes.

#### Acceptance Criteria

1. THE Keycloak realm SHALL define `openid` client scope with standard OIDC claims
2. THE Keycloak realm SHALL define `profile` client scope with name, given_name, family_name claims
3. THE Keycloak realm SHALL define `email` client scope with email and email_verified claims
4. THE Keycloak realm SHALL define `roles` client scope with realm and client role mappings
5. WHEN a client requests `openid profile email roles` scopes THEN Keycloak SHALL accept and process the request
6. THE `agentvoicebox-portal` client SHALL have all four scopes as default client scopes
7. THE `agentvoicebox-api` client SHALL have all four scopes as default client scopes

---

### Requirement 2: Google Identity Provider Configuration

**User Story:** As a user, I want to sign in with Google, so that I can use my existing Google account for authentication.

#### Acceptance Criteria

1. THE Google identity provider SHALL be enabled in Keycloak
2. THE Google identity provider SHALL use the configured client ID and secret
3. WHEN a user authenticates via Google THEN Keycloak SHALL create or link a user account
4. WHEN a new user authenticates via Google THEN Keycloak SHALL assign the `viewer` role by default
5. THE Google identity provider SHALL request `openid profile email` scopes from Google
6. WHEN Google authentication succeeds THEN the user SHALL be redirected to the portal callback URL

---

### Requirement 3: Portal Frontend OAuth Flow

**User Story:** As a developer, I want the portal frontend to correctly initiate OAuth flows, so that users can authenticate successfully.

#### Acceptance Criteria

1. WHEN initiating Keycloak login THEN the portal SHALL request `openid profile email roles` scopes
2. WHEN initiating Google login THEN the portal SHALL use direct Google OAuth with `openid email profile` scopes
3. THE portal SHALL use PKCE (S256) for all Keycloak authorization code flows
4. WHEN receiving an authorization code THEN the portal SHALL exchange it for tokens
5. IF token exchange fails THEN the portal SHALL display a user-friendly error message
6. THE portal SHALL store tokens securely in session storage and cookies

---

### Requirement 4: Temporal Namespace and Workflow Registration

**User Story:** As a platform operator, I want Temporal workflows to be properly registered, so that tenant onboarding and other business processes execute correctly.

#### Acceptance Criteria

1. THE Temporal namespace `agentvoicebox` SHALL exist and be accessible
2. THE Temporal worker SHALL connect to the `agentvoicebox` namespace
3. THE Temporal worker SHALL register all defined workflows (onboarding, billing, etc.)
4. THE Temporal worker SHALL register all defined activities
5. WHEN the Temporal worker starts THEN it SHALL log successful registration of workflows and activities
6. IF the namespace does not exist THEN the worker SHALL create it or fail with a clear error

---

### Requirement 5: Tenant Onboarding Workflow

**User Story:** As a new user, I want my tenant to be automatically provisioned, so that I can start using the platform immediately after registration.

#### Acceptance Criteria

1. WHEN a new user registers THEN the system SHALL trigger the onboarding workflow
2. THE onboarding workflow SHALL create a tenant record in the database
3. THE onboarding workflow SHALL provision default API keys for the tenant
4. THE onboarding workflow SHALL set up default rate limits and quotas
5. THE onboarding workflow SHALL create a Lago customer for billing
6. WHEN onboarding completes THEN the user SHALL be able to access the dashboard
7. IF any onboarding step fails THEN the workflow SHALL retry with exponential backoff

---

### Requirement 6: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages when authentication fails, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN OAuth scope validation fails THEN the system SHALL display "Invalid OAuth configuration" error
2. WHEN token exchange fails THEN the system SHALL display the specific error from the provider
3. WHEN Keycloak is unreachable THEN the system SHALL display "Authentication service unavailable"
4. THE error page SHALL provide a "Try Again" button to restart authentication
5. THE error page SHALL provide a link to contact support for persistent issues

