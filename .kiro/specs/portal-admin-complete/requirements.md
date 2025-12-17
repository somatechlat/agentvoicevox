# Requirements Document

## Introduction

This document specifies the requirements for a complete, production-ready multi-portal system for the AgentVoiceBox platform. The system consists of three distinct portals serving different audiences:

1. **SaaS Admin Portal** - For platform operators to manage all tenants, system health, global billing, and infrastructure
2. **Tenant Portal** - For organization administrators to manage their tenant's API keys, team members, projects, and billing
3. **User Portal** - For end users within an organization to access personal settings and view-only dashboards

All portals share a common codebase but present different navigation, features, and permissions based on the authenticated user's role.

## Glossary

- **Portal**: The Next.js web application providing the administration interface
- **SaaS Admin**: A platform operator with access to all tenants and system configuration
- **Tenant Admin**: An organization owner or admin managing their own tenant
- **User**: An end user within an organization with limited permissions
- **Tenant**: An organization/customer account with isolated data and resources
- **Project**: A logical grouping of API keys and sessions within a tenant (e.g., production, staging, development)
- **Session**: A voice conversation instance between a client and the AgentVoiceBox platform
- **API Key**: Authentication credential for accessing the AgentVoiceBox API
- **Gateway**: The WebSocket/REST service handling real-time voice connections
- **Worker**: Background services processing STT, TTS, or LLM requests
- **Lago**: The billing engine handling usage metering and invoicing
- **Keycloak**: The identity provider handling authentication and user management

---

## PART A: SAAS ADMIN PORTAL

### Requirement A1: SaaS Admin Dashboard

**User Story:** As a SaaS admin, I want to see platform-wide metrics and health status, so that I can monitor the entire system and respond to issues.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to the admin dashboard THEN the Portal SHALL display total tenant count, total active sessions, total API requests, and total revenue
2. WHEN displaying system health THEN the Portal SHALL show real-time status of Gateway, Redis, PostgreSQL, Kafka, and all Workers with latency metrics
3. WHEN displaying tenant activity THEN the Portal SHALL show the top 10 tenants by usage with request counts and audio minutes
4. WHEN an alert condition exists THEN the Portal SHALL display a prominent alert banner with severity and affected services
5. WHEN the dashboard auto-refreshes every 30 seconds THEN the Portal SHALL update all metrics without requiring a full page reload
6. WHEN clicking on a metric THEN the Portal SHALL navigate to the detailed view for that metric category

---

### Requirement A2: Tenant Management

**User Story:** As a SaaS admin, I want to manage all tenants on the platform, so that I can onboard customers, handle support issues, and enforce policies.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Tenants THEN the Portal SHALL display a paginated list of all tenants with name, plan, status, creation date, and usage summary
2. WHEN searching for a tenant THEN the Portal SHALL filter tenants by name, email, or tenant ID in real-time
3. WHEN viewing a tenant detail THEN the Portal SHALL display full tenant profile, subscription details, usage history, team members, and API keys
4. WHEN a SaaS admin suspends a tenant THEN the Portal SHALL disable all API keys, terminate active sessions, and mark the tenant as suspended
5. WHEN a SaaS admin reactivates a tenant THEN the Portal SHALL restore API key functionality and update tenant status to active
6. WHEN a SaaS admin impersonates a tenant THEN the Portal SHALL switch context to view the Tenant Portal as that tenant without modifying data

---

### Requirement A3: Global Billing Administration

**User Story:** As a SaaS admin, I want to manage billing across all tenants, so that I can handle payment issues, apply credits, and generate reports.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Billing THEN the Portal SHALL display total MRR, ARR, outstanding invoices, and payment failure count
2. WHEN viewing invoices THEN the Portal SHALL display all invoices across tenants with filtering by status (paid, pending, overdue, failed)
3. WHEN a SaaS admin applies a credit THEN the Portal SHALL create a credit note in Lago and apply it to the tenant's next invoice
4. WHEN a SaaS admin voids an invoice THEN the Portal SHALL mark the invoice as void in Lago and notify the tenant
5. WHEN exporting billing data THEN the Portal SHALL generate a CSV report with all invoice and payment data for the selected period
6. WHEN viewing payment failures THEN the Portal SHALL display failed payment attempts with error details and retry options

---

### Requirement A4: Plan Management

**User Story:** As a SaaS admin, I want to create and manage subscription plans, so that I can offer different pricing tiers to customers.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Plans THEN the Portal SHALL display all plans from Lago with name, price, features, and subscriber count
2. WHEN creating a new plan THEN the Portal SHALL call Lago API to create the plan with specified pricing, features, and usage limits
3. WHEN editing a plan THEN the Portal SHALL update the plan in Lago and apply changes to new subscriptions only
4. WHEN deprecating a plan THEN the Portal SHALL mark the plan as unavailable for new subscriptions while maintaining existing subscribers
5. WHEN viewing plan subscribers THEN the Portal SHALL display all tenants subscribed to that plan with their usage metrics
6. WHEN configuring usage-based pricing THEN the Portal SHALL define billable metrics, tiers, and overage rates in Lago

---

### Requirement A5: System Monitoring

**User Story:** As a SaaS admin, I want to monitor all platform services, so that I can ensure reliability and respond to incidents.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Monitoring THEN the Portal SHALL display service health for all components (Gateway, Portal API, PostgreSQL, Redis, Keycloak, Lago, OVOS Messagebus, STT Worker, TTS Worker, LLM Worker) with uptime percentages
2. WHEN viewing metrics THEN the Portal SHALL display Prometheus metrics including request rates, error rates, and latency percentiles (p50/p95/p99)
3. WHEN viewing worker status THEN the Portal SHALL show STT Worker (Faster-Whisper), TTS Worker (Kokoro), and LLM Worker health with queue depth, processing rate, and error counts
4. WHEN configuring alerts THEN the Portal SHALL allow setting thresholds for metrics that trigger notifications
5. WHEN an incident occurs THEN the Portal SHALL display incident timeline with affected services and resolution status
6. WHEN viewing logs THEN the Portal SHALL display aggregated logs from all services with filtering by level, service, and time range
7. WHEN viewing voice pipeline metrics THEN the Portal SHALL display STT transcription latency, TTS synthesis latency, and LLM response latency per tenant

---

### Requirement A6: Audit and Compliance

**User Story:** As a SaaS admin, I want to view audit logs across all tenants, so that I can investigate security incidents and maintain compliance.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Audit THEN the Portal SHALL display a paginated audit log with actor, action, resource, timestamp, and tenant
2. WHEN filtering audit logs THEN the Portal SHALL support filtering by tenant, action type, actor, date range, and resource type
3. WHEN viewing an audit entry THEN the Portal SHALL display full details including request payload, response, and IP address
4. WHEN exporting audit logs THEN the Portal SHALL generate a CSV or JSON export for the selected filters and date range
5. WHEN searching audit logs THEN the Portal SHALL support full-text search across action descriptions and resource identifiers
6. WHEN retention policies apply THEN the Portal SHALL display audit log retention period and archive status

---

### Requirement A7: User Management (Platform-Wide)

**User Story:** As a SaaS admin, I want to manage all users across the platform, so that I can handle support requests and enforce security policies.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Users THEN the Portal SHALL display all users from Keycloak with name, email, tenant, role, and status
2. WHEN searching for a user THEN the Portal SHALL filter users by name, email, or tenant in real-time
3. WHEN viewing a user detail THEN the Portal SHALL display user profile, assigned roles, login history, and associated tenant
4. WHEN a SaaS admin disables a user THEN the Portal SHALL deactivate the user in Keycloak and terminate their active sessions
5. WHEN a SaaS admin resets a user password THEN the Portal SHALL trigger a password reset email via Keycloak
6. WHEN viewing login failures THEN the Portal SHALL display failed login attempts with IP address and timestamp for security analysis

---

## PART B: TENANT PORTAL

### Requirement B1: Tenant Dashboard

**User Story:** As a tenant admin, I want to see my organization's usage and status, so that I can monitor our consumption and costs.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to the dashboard THEN the Portal SHALL display usage metrics for their tenant only including API requests, audio minutes, and tokens
2. WHEN displaying billing summary THEN the Portal SHALL fetch current plan, amount due, and next billing date from Lago for their tenant
3. WHEN displaying system health THEN the Portal SHALL show service status relevant to their usage (Gateway, API availability)
4. WHEN displaying recent activity THEN the Portal SHALL show the last 10 events from their tenant's audit log
5. WHEN the dashboard auto-refreshes every 60 seconds THEN the Portal SHALL update all metrics without requiring a full page reload
6. WHEN usage approaches plan limits THEN the Portal SHALL display a warning banner with upgrade options

---

### Requirement B2: Voice Sessions Management

**User Story:** As a tenant admin, I want to view and manage my organization's voice sessions, so that I can monitor conversations and troubleshoot issues.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Sessions THEN the Portal SHALL fetch session data for their tenant only showing session ID, status, creation time, and duration
2. WHEN filtering sessions THEN the Portal SHALL support filtering by status (active, closed), project, date range, and API key
3. WHEN viewing a session detail THEN the Portal SHALL display conversation history with user and assistant messages and timestamps
4. WHEN viewing an active session THEN the Portal SHALL display real-time status including connected client and persona configuration
5. WHEN ending an active session THEN the Portal SHALL call the session close endpoint and update the UI immediately
6. WHEN exporting session data THEN the Portal SHALL generate a CSV with session metadata for the selected filters

---

### Requirement B3: Projects Management

**User Story:** As a tenant admin, I want to organize my API keys and sessions into projects, so that I can separate environments and track usage by project.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Projects THEN the Portal SHALL display projects for their tenant with name, environment, key count, and session count
2. WHEN creating a project THEN the Portal SHALL persist the project with name and environment type (production, staging, development)
3. WHEN viewing a project THEN the Portal SHALL display associated API keys, recent sessions, and aggregated usage metrics
4. WHEN editing a project THEN the Portal SHALL update the project configuration and reflect changes immediately
5. WHEN deleting a project THEN the Portal SHALL require confirmation, offer to revoke associated keys, and remove the project
6. WHEN assigning an API key to a project THEN the Portal SHALL update the key's project association in the database

---

### Requirement B4: API Key Management

**User Story:** As a tenant admin, I want to create and manage API keys, so that I can securely authenticate my applications.

#### Acceptance Criteria

1. WHEN a tenant admin views API keys THEN the Portal SHALL display keys for their tenant with name, prefix, scopes, status, and last used date
2. WHEN creating an API key THEN the Portal SHALL generate the key, display the full secret exactly once, and store the hashed key
3. WHEN rotating an API key THEN the Portal SHALL create a new key with 24-hour grace period for the old key
4. WHEN revoking an API key THEN the Portal SHALL immediately invalidate the key in Redis and PostgreSQL
5. WHEN viewing key usage THEN the Portal SHALL display request counts and last used timestamp for each key
6. WHEN configuring key scopes THEN the Portal SHALL allow selecting from available permissions (realtime, sessions, usage)

---

### Requirement B5: Usage Analytics

**User Story:** As a tenant admin, I want to view detailed usage analytics, so that I can understand consumption patterns and optimize costs.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Usage THEN the Portal SHALL display metrics for their tenant including requests, audio minutes, and tokens
2. WHEN selecting a time period THEN the Portal SHALL query usage data for 7d, 30d, or 90d and display aggregated metrics
3. WHEN displaying the usage chart THEN the Portal SHALL render daily usage data as a bar or line chart
4. WHEN showing breakdowns THEN the Portal SHALL display separate metrics for STT/TTS audio and LLM input/output tokens
5. WHEN filtering by project THEN the Portal SHALL display usage metrics aggregated for the selected project only
6. WHEN exporting usage data THEN the Portal SHALL generate a CSV with daily usage records for the selected period

---

### Requirement B6: Billing and Subscription

**User Story:** As a tenant admin, I want to manage my subscription and payments, so that I can control spending and maintain service.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Billing THEN the Portal SHALL display current plan, usage against limits, and billing period from Lago
2. WHEN viewing available plans THEN the Portal SHALL display plan options with pricing, features, and usage limits
3. WHEN upgrading a plan THEN the Portal SHALL process the upgrade in Lago with prorated charges
4. WHEN downgrading a plan THEN the Portal SHALL schedule the downgrade for end of billing period
5. WHEN viewing invoices THEN the Portal SHALL display invoice history with status, amount, and PDF download
6. WHEN managing payment methods THEN the Portal SHALL integrate with Stripe Elements for secure card management

---

### Requirement B7: Team Management

**User Story:** As a tenant admin, I want to manage my team members, so that I can collaborate securely within my organization.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Team THEN the Portal SHALL display members for their tenant with name, email, role, and status
2. WHEN inviting a member THEN the Portal SHALL create an invitation in Keycloak and send an email with the specified role
3. WHEN changing a member's role THEN the Portal SHALL update the role in Keycloak and log the change
4. WHEN removing a member THEN the Portal SHALL deactivate the user, revoke their sessions, and log the action
5. WHEN viewing pending invitations THEN the Portal SHALL display invitations with status and expiration date
6. WHEN team size limit is reached THEN the Portal SHALL display an upgrade prompt instead of the invite button

---

### Requirement B8: Organization Settings

**User Story:** As a tenant admin, I want to configure my organization settings, so that I can customize the platform for my needs.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Settings THEN the Portal SHALL display organization profile with name, email, and timezone
2. WHEN updating organization profile THEN the Portal SHALL persist changes and display a success confirmation
3. WHEN configuring notifications THEN the Portal SHALL allow enabling/disabling email notifications for billing, usage alerts, and security events
4. WHEN creating a webhook THEN the Portal SHALL validate the URL, store the configuration, and generate a signing secret
5. WHEN testing a webhook THEN the Portal SHALL send a test payload and display the response status
6. WHEN viewing webhook logs THEN the Portal SHALL display recent delivery attempts with status and response time

---

### Requirement B9: Voice Configuration

**User Story:** As a tenant admin, I want to configure voice settings for my organization, so that I can customize the voice experience for my applications.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Voice Settings THEN the Portal SHALL display current voice configuration including default voice, speed, and persona
2. WHEN selecting a TTS voice THEN the Portal SHALL display available Kokoro voices (am_onyx, am_adam, af_sarah, af_nicole, bf_emma, bm_george, etc.) with audio preview capability
3. WHEN configuring voice speed THEN the Portal SHALL allow setting speed between 0.5x and 2.0x with real-time preview
4. WHEN configuring a persona THEN the Portal SHALL allow setting system instructions that define the assistant's behavior
5. WHEN saving voice configuration THEN the Portal SHALL persist settings and apply them to new sessions immediately
6. WHEN viewing voice usage THEN the Portal SHALL display STT minutes, TTS minutes, and LLM tokens consumed by voice sessions

---

### Requirement B10: STT Configuration

**User Story:** As a tenant admin, I want to configure speech-to-text settings, so that I can optimize transcription quality for my use case.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to STT Settings THEN the Portal SHALL display current STT configuration including model size, language, and compute settings
2. WHEN selecting an STT model THEN the Portal SHALL display available Faster-Whisper models (tiny, base, small, medium, large-v2, large-v3) with accuracy/speed tradeoffs
3. WHEN selecting a language THEN the Portal SHALL display supported BCP-47 language codes with auto-detect option
4. WHEN configuring VAD (Voice Activity Detection) THEN the Portal SHALL allow enabling/disabling VAD filtering
5. WHEN viewing STT metrics THEN the Portal SHALL display average transcription latency and accuracy statistics
6. WHEN testing STT configuration THEN the Portal SHALL allow uploading a test audio file and displaying the transcription result

---

### Requirement B11: LLM Configuration

**User Story:** As a tenant admin, I want to configure LLM settings, so that I can choose the AI model and behavior for my voice assistant.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to LLM Settings THEN the Portal SHALL display current LLM configuration including provider, model, and parameters
2. WHEN selecting an LLM provider THEN the Portal SHALL display available providers (Groq, OpenAI, Ollama) with their available models
3. WHEN configuring temperature THEN the Portal SHALL allow setting temperature between 0.0 and 2.0 with explanation of effects
4. WHEN configuring max tokens THEN the Portal SHALL allow setting maximum output tokens between 256 and 4096
5. WHEN providing API keys (BYOK) THEN the Portal SHALL securely store tenant-provided API keys for OpenAI or Groq
6. WHEN testing LLM configuration THEN the Portal SHALL allow sending a test prompt and displaying the response

---

### Requirement B12: Persona Management

**User Story:** As a tenant admin, I want to create and manage AI personas, so that I can customize the assistant's personality and capabilities.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Personas THEN the Portal SHALL display all configured personas with name, description, and status
2. WHEN creating a persona THEN the Portal SHALL allow setting name, system prompt, voice, and solver plugins
3. WHEN configuring solver plugins THEN the Portal SHALL display available OVOS solvers (Wikipedia, DuckDuckGo, Wolfram Alpha, WordNet) with drag-and-drop ordering
4. WHEN editing a persona THEN the Portal SHALL allow modifying all persona settings and preview the changes
5. WHEN testing a persona THEN the Portal SHALL allow sending test messages and hearing/seeing the persona's responses
6. WHEN setting a default persona THEN the Portal SHALL apply the selected persona to all new sessions for the tenant

---

### Requirement B13: Voice Cloning (Future)

**User Story:** As a tenant admin, I want to clone custom voices, so that I can create unique voice experiences for my brand.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Voice Cloning THEN the Portal SHALL display existing custom voices and the option to create new ones
2. WHEN uploading a voice sample THEN the Portal SHALL accept audio files (WAV, MP3) between 10 seconds and 5 minutes
3. WHEN cloning a voice THEN the Portal SHALL process the sample and create a custom voice model within 5 minutes
4. WHEN previewing a cloned voice THEN the Portal SHALL allow entering text and playing the synthesized audio
5. WHEN managing custom voices THEN the Portal SHALL allow renaming, deleting, and setting as default
6. WHEN voice cloning fails THEN the Portal SHALL display clear error messages with guidance on improving the source audio

---

## PART C: USER PORTAL

### Requirement C1: User Dashboard

**User Story:** As a user, I want to see a summary of my organization's status, so that I can understand the platform availability.

#### Acceptance Criteria

1. WHEN a user navigates to the dashboard THEN the Portal SHALL display read-only usage summary for their tenant
2. WHEN displaying system health THEN the Portal SHALL show service availability status (operational, degraded, down)
3. WHEN displaying recent activity THEN the Portal SHALL show recent sessions and events relevant to the user's permissions
4. WHEN a user lacks permissions for detailed metrics THEN the Portal SHALL display a simplified view without sensitive data
5. WHEN the dashboard loads THEN the Portal SHALL not display billing information unless the user has billing:view permission
6. WHEN clicking on restricted features THEN the Portal SHALL display a message indicating insufficient permissions

---

### Requirement C2: Personal Settings

**User Story:** As a user, I want to manage my personal account settings, so that I can update my profile and security preferences.

#### Acceptance Criteria

1. WHEN a user navigates to Personal Settings THEN the Portal SHALL display their profile with name, email, and avatar
2. WHEN updating profile information THEN the Portal SHALL persist changes to Keycloak and display a success confirmation
3. WHEN changing password THEN the Portal SHALL validate password requirements and update via Keycloak
4. WHEN enabling two-factor authentication THEN the Portal SHALL guide the user through TOTP setup via Keycloak
5. WHEN viewing login history THEN the Portal SHALL display recent login attempts with timestamp, IP, and device
6. WHEN managing sessions THEN the Portal SHALL allow the user to terminate other active sessions

---

### Requirement C3: View-Only Sessions

**User Story:** As a user, I want to view voice sessions I have access to, so that I can review conversations relevant to my work.

#### Acceptance Criteria

1. WHEN a user navigates to Sessions THEN the Portal SHALL display sessions based on their permission level
2. WHEN a user has sessions:view permission THEN the Portal SHALL display session list with read-only access
3. WHEN a user lacks sessions:view permission THEN the Portal SHALL display an empty state with permission request guidance
4. WHEN viewing a session detail THEN the Portal SHALL display conversation history in read-only mode
5. WHEN attempting to end a session THEN the Portal SHALL display an error if the user lacks sessions:manage permission
6. WHEN filtering sessions THEN the Portal SHALL apply the same filters as the Tenant Portal but with read-only results

---

### Requirement C4: View-Only API Keys

**User Story:** As a user, I want to view API keys I have access to, so that I can use them in my development work.

#### Acceptance Criteria

1. WHEN a user navigates to API Keys THEN the Portal SHALL display keys based on their permission level
2. WHEN a user has api_keys:view permission THEN the Portal SHALL display key list with masked secrets
3. WHEN a user lacks api_keys:view permission THEN the Portal SHALL display an empty state with permission request guidance
4. WHEN attempting to create or revoke a key THEN the Portal SHALL display an error if the user lacks api_keys:manage permission
5. WHEN viewing key details THEN the Portal SHALL display key metadata without the ability to modify
6. WHEN copying a key prefix THEN the Portal SHALL allow copying the visible prefix for reference

---

## PART E: OVOS INTEGRATION REQUIREMENTS

### Requirement E1: OVOS Messagebus Management

**User Story:** As a SaaS admin, I want to monitor and manage the OVOS Messagebus, so that I can ensure reliable communication between voice components.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to OVOS Messagebus THEN the Portal SHALL display connection status, message throughput, and connected clients
2. WHEN viewing messagebus metrics THEN the Portal SHALL show messages per second, queue depth, and latency percentiles
3. WHEN a client disconnects unexpectedly THEN the Portal SHALL log the event and display it in the activity feed
4. WHEN viewing connected clients THEN the Portal SHALL display client ID, connection time, and message count
5. WHEN the messagebus is unhealthy THEN the Portal SHALL display an alert with diagnostic information
6. WHEN restarting the messagebus THEN the Portal SHALL gracefully disconnect clients and restore connections

---

### Requirement E2: Skills Management

**User Story:** As a tenant admin, I want to manage OVOS skills for my organization, so that I can customize the voice assistant capabilities.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Skills THEN the Portal SHALL display installed skills with name, version, and status
2. WHEN installing a skill THEN the Portal SHALL download from the OVOS skill store and register with the skills bus
3. WHEN enabling a skill THEN the Portal SHALL activate the skill and make its intents available
4. WHEN disabling a skill THEN the Portal SHALL deactivate the skill without removing it
5. WHEN viewing skill details THEN the Portal SHALL display supported intents, sample utterances, and configuration options
6. WHEN configuring a skill THEN the Portal SHALL persist settings and reload the skill with new configuration

---

### Requirement E3: Persona Management

**User Story:** As a tenant admin, I want to create and manage voice personas, so that I can customize the assistant's personality and behavior.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Personas THEN the Portal SHALL display all personas with name, voice, and usage count
2. WHEN creating a persona THEN the Portal SHALL allow setting name, system instructions, voice, speed, and language
3. WHEN editing a persona THEN the Portal SHALL update the configuration and apply to new sessions immediately
4. WHEN deleting a persona THEN the Portal SHALL require confirmation and reassign sessions to default persona
5. WHEN previewing a persona THEN the Portal SHALL play a sample audio clip with the configured voice and speed
6. WHEN assigning a persona to a project THEN the Portal SHALL set it as the default for all sessions in that project

---

### Requirement E4: Wake Word Configuration

**User Story:** As a tenant admin, I want to configure wake words for my organization, so that users can activate the voice assistant naturally.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Wake Words THEN the Portal SHALL display configured wake words with sensitivity settings
2. WHEN adding a wake word THEN the Portal SHALL validate the phrase and set detection sensitivity
3. WHEN testing a wake word THEN the Portal SHALL allow recording audio and display detection confidence
4. WHEN adjusting sensitivity THEN the Portal SHALL update the detection threshold and apply immediately
5. WHEN disabling a wake word THEN the Portal SHALL stop detection without removing the configuration
6. WHEN viewing wake word analytics THEN the Portal SHALL display detection rate, false positives, and missed activations

---

### Requirement E5: Intent Analytics

**User Story:** As a tenant admin, I want to view intent analytics, so that I can understand how users interact with the voice assistant.

#### Acceptance Criteria

1. WHEN a tenant admin navigates to Intent Analytics THEN the Portal SHALL display top intents by frequency
2. WHEN viewing intent details THEN the Portal SHALL show sample utterances, success rate, and average confidence
3. WHEN filtering by date range THEN the Portal SHALL display intent metrics for the selected period
4. WHEN viewing failed intents THEN the Portal SHALL display unrecognized utterances for training improvement
5. WHEN exporting intent data THEN the Portal SHALL generate a CSV with intent, utterance, confidence, and timestamp
6. WHEN viewing intent trends THEN the Portal SHALL display a chart showing intent frequency over time

---

### Requirement E6: Voice Pipeline Monitoring

**User Story:** As a SaaS admin, I want to monitor the complete voice pipeline, so that I can ensure end-to-end voice processing quality.

#### Acceptance Criteria

1. WHEN a SaaS admin navigates to Voice Pipeline THEN the Portal SHALL display the complete pipeline flow (Audio → STT → Intent → Skill → LLM → TTS → Audio)
2. WHEN viewing pipeline metrics THEN the Portal SHALL show end-to-end latency, success rate, and error breakdown by stage
3. WHEN a pipeline stage fails THEN the Portal SHALL highlight the failed stage and display error details
4. WHEN viewing per-tenant pipeline metrics THEN the Portal SHALL show latency and success rate per tenant
5. WHEN configuring pipeline thresholds THEN the Portal SHALL allow setting latency alerts per stage
6. WHEN viewing pipeline history THEN the Portal SHALL display recent pipeline executions with timing breakdown

---

### Requirement E7: OpenAI Realtime API Compatibility

**User Story:** As a developer, I want the platform to be compatible with OpenAI Realtime API, so that I can use existing SDKs without modification.

#### Acceptance Criteria

1. WHEN a developer connects via WebSocket THEN the Gateway SHALL accept OpenAI Realtime API message formats
2. WHEN sending audio data THEN the Gateway SHALL process it through the OVOS pipeline and return compatible events
3. WHEN receiving response.audio.delta events THEN the client SHALL receive audio chunks in OpenAI-compatible format
4. WHEN using ephemeral tokens THEN the Gateway SHALL validate and hydrate session state from persistence
5. WHEN rate limits are exceeded THEN the Gateway SHALL return rate_limits.updated events in OpenAI format
6. WHEN errors occur THEN the Gateway SHALL return error envelopes with type, code, message, and param fields

---

---

## PART E: TECHNICAL REQUIREMENTS

### Requirement E1: Remove Mock Data and Dev Bypass

**User Story:** As a developer, I want the portal to use real backend APIs exclusively, so that the UI reflects actual system state.

#### Acceptance Criteria

1. WHEN the Portal is deployed THEN the Portal SHALL NOT include any DEV_BYPASS_AUTH mode or mock data fallbacks
2. WHEN making API calls THEN the Portal SHALL always call real Portal API endpoints at /api/v1/*
3. WHEN authentication fails THEN the Portal SHALL redirect to Keycloak login rather than using mock users
4. WHEN API calls fail THEN the Portal SHALL display error states rather than falling back to mock data
5. WHEN displaying metrics THEN the Portal SHALL fetch real data from Prometheus and Lago
6. WHEN the backend is unavailable THEN the Portal SHALL display appropriate error messages with retry options

---

### Requirement E2: OpenAI Realtime API Compatibility

**User Story:** As a developer, I want the platform to be fully compatible with OpenAI Realtime API, so that existing SDKs work without modification.

#### Acceptance Criteria

1. WHEN a client connects via WebSocket THEN the Gateway SHALL accept OpenAI-compatible authentication headers
2. WHEN processing WebSocket events THEN the Gateway SHALL support all OpenAI Realtime API event types (session.update, input_audio_buffer.*, response.*, etc.)
3. WHEN generating responses THEN the Gateway SHALL emit events in OpenAI-compatible format (response.audio.delta, response.done, etc.)
4. WHEN handling errors THEN the Gateway SHALL return OpenAI-compatible error envelopes (type, code, message, param)
5. WHEN rate limiting THEN the Gateway SHALL emit rate_limits.updated events with remaining quota
6. WHEN the session expires THEN the Gateway SHALL close the WebSocket with appropriate close code

---

### Requirement E3: Voice Pipeline Integration

**User Story:** As a platform operator, I want the voice pipeline to be fully integrated, so that STT, TTS, and LLM work together seamlessly.

#### Acceptance Criteria

1. WHEN audio is received THEN the STT Worker (Faster-Whisper) SHALL transcribe within 500ms p99 latency
2. WHEN text is synthesized THEN the TTS Worker (Kokoro) SHALL produce first audio byte within 200ms p99 latency
3. WHEN LLM generates text THEN the LLM Worker SHALL produce first token within 300ms p99 latency
4. WHEN workers communicate THEN the system SHALL use Redis Streams for work queues
5. WHEN a worker fails THEN the system SHALL retry with exponential backoff and circuit breaker
6. WHEN monitoring workers THEN the Portal SHALL display queue depth, processing rate, and error counts

---

### Requirement E4: Multi-Tenant Data Isolation

**User Story:** As a platform operator, I want complete tenant data isolation, so that customers cannot access each other's data.

#### Acceptance Criteria

1. WHEN storing data THEN the database SHALL include tenant_id on all tables (sessions, conversation_items, api_keys, etc.)
2. WHEN querying data THEN the Portal API SHALL filter by tenant_id from the authenticated user's JWT claims
3. WHEN accessing Redis THEN the system SHALL use tenant-prefixed keys for session state
4. WHEN processing Kafka events THEN the system SHALL include tenant_id in all event payloads
5. WHEN enforcing policies THEN OPA SHALL validate tenant ownership before allowing access
6. WHEN auditing actions THEN the audit log SHALL record tenant_id for all operations

---

### Requirement E5: Billing Metering Integration

**User Story:** As a platform operator, I want accurate usage metering, so that customers are billed correctly.

#### Acceptance Criteria

1. WHEN an API request is made THEN the system SHALL record the event in Lago with tenant_id
2. WHEN audio is transcribed THEN the system SHALL meter audio_minutes_input in Lago
3. WHEN audio is synthesized THEN the system SHALL meter audio_minutes_output in Lago
4. WHEN LLM tokens are consumed THEN the system SHALL meter llm_tokens_input and llm_tokens_output in Lago
5. WHEN displaying usage THEN the Portal SHALL fetch real metrics from Lago API
6. WHEN generating invoices THEN Lago SHALL calculate charges based on metered usage and plan pricing

---

## PART D: SHARED REQUIREMENTS

### Requirement D1: Authentication and Authorization

**User Story:** As any user, I want secure authentication, so that my account and data are protected.

#### Acceptance Criteria

1. WHEN a user accesses the portal THEN the Portal SHALL redirect unauthenticated users to Keycloak login
2. WHEN authentication succeeds THEN the Portal SHALL store the JWT token and redirect to the appropriate dashboard based on role
3. WHEN the JWT token expires THEN the Portal SHALL attempt silent refresh or redirect to login
4. WHEN checking permissions THEN the Portal SHALL validate the user's roles and permissions from the JWT claims
5. WHEN a user lacks permission for a route THEN the Portal SHALL display a 403 page with guidance
6. WHEN a user logs out THEN the Portal SHALL clear tokens, terminate the Keycloak session, and redirect to login

---

### Requirement D2: Role-Based Navigation

**User Story:** As any user, I want to see only the features I have access to, so that the interface is not cluttered with unavailable options.

#### Acceptance Criteria

1. WHEN rendering the sidebar THEN the Portal SHALL display only navigation items the user has permission to access
2. WHEN a SaaS admin is authenticated THEN the Portal SHALL display the full admin navigation including Tenants, Plans, Monitoring, and Audit
3. WHEN a tenant admin is authenticated THEN the Portal SHALL display customer navigation including Dashboard, Sessions, Projects, API Keys, Usage, Billing, Team, and Settings
4. WHEN a user is authenticated THEN the Portal SHALL display limited navigation including Dashboard, Sessions (if permitted), API Keys (if permitted), and Personal Settings
5. WHEN permissions change THEN the Portal SHALL update the navigation on the next page load
6. WHEN hovering over a disabled item THEN the Portal SHALL display a tooltip explaining the required permission

---

### Requirement D3: Responsive Design

**User Story:** As any user, I want to use the portal on any device, so that I can manage my account from desktop, tablet, or mobile.

#### Acceptance Criteria

1. WHEN viewing on desktop THEN the Portal SHALL display a full sidebar with expanded navigation
2. WHEN viewing on tablet THEN the Portal SHALL display a collapsible sidebar with icon-only mode
3. WHEN viewing on mobile THEN the Portal SHALL display a hamburger menu with slide-out navigation
4. WHEN interacting with tables THEN the Portal SHALL provide horizontal scrolling or card view on small screens
5. WHEN interacting with forms THEN the Portal SHALL stack form fields vertically on small screens
6. WHEN displaying charts THEN the Portal SHALL resize charts responsively while maintaining readability

---

### Requirement D4: Error Handling

**User Story:** As any user, I want clear feedback when operations succeed or fail, so that I understand the system state.

#### Acceptance Criteria

1. WHEN an API call succeeds THEN the Portal SHALL display a success toast notification
2. WHEN an API call fails THEN the Portal SHALL display an error toast with the error message
3. WHEN a form has validation errors THEN the Portal SHALL display inline error messages
4. WHEN a destructive action is requested THEN the Portal SHALL display a confirmation dialog
5. WHEN loading data THEN the Portal SHALL display skeleton loaders
6. WHEN no data exists THEN the Portal SHALL display an empty state with guidance

---

### Requirement D5: Real-Time Updates

**User Story:** As any user, I want to see data updates without manual refresh, so that I have current information.

#### Acceptance Criteria

1. WHEN viewing dashboards THEN the Portal SHALL auto-refresh metrics at configured intervals
2. WHEN viewing active sessions THEN the Portal SHALL update status changes within 5 seconds
3. WHEN a background operation completes THEN the Portal SHALL display a toast notification
4. WHEN network connectivity is lost THEN the Portal SHALL display an offline indicator
5. WHEN connectivity is restored THEN the Portal SHALL resume updates and sync pending actions
6. WHEN data changes externally THEN the Portal SHALL reflect changes on the next refresh cycle

---

### Requirement D6: Backend API Integration

**User Story:** As a developer, I want the portal to use real backend APIs, so that all data is persisted and consistent.

#### Acceptance Criteria

1. WHEN the Portal makes API calls THEN the Portal SHALL use the Portal API endpoints at /api/v1/* with proper authentication
2. WHEN authentication is required THEN the Portal SHALL include the JWT token in the Authorization header
3. WHEN the API returns paginated results THEN the Portal SHALL implement pagination controls
4. WHEN the API returns an error THEN the Portal SHALL parse and display the appropriate error message
5. WHEN making mutations THEN the Portal SHALL invalidate relevant cached queries
6. WHEN the session expires THEN the Portal SHALL redirect to login with a session expired message
