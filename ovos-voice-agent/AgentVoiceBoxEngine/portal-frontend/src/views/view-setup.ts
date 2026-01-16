import { LitElement, html } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-layout';

/**
 * PERFECT SINGLE-CLICK CONFIGURATION UI
 * 
 * Design Philosophy:
 * - ZERO MODALS: All settings visible on main screen
 * - ONE CLICK: Select service → see ALL settings immediately
 * - SMART GROUPING: Logical organization (Connection → Performance → Advanced)
 * - VISUAL HIERARCHY: Color, typography, spacing communicate importance
 * - SCANNABLE: Quickly find any setting without hunting
 * - PROGRESSIVE DISCLOSURE: Common settings prominent, advanced collapsed
 * 
 * Information Architecture:
 * LEFT (20%): Service selector with health status
 * RIGHT (80%): Expandable accordion panels for all settings
 */

type Service = 'postgresql' | 'redis' | 'temporal' | 'keycloak' | 'vault' | 'opa' | 'kafka' | 'lago' | 'paypal' | 'llm' | 'stt' | 'tts' | 'app';

@customElement('view-setup')
export class ViewSetup extends LitElement {
  @state() private selectedService: Service = 'postgresql';
  @state() private expandedSections = new Set<string>(['connection']);

  createRenderRoot() { return this; }

  render() {
    return html`
      <saas-layout>
        <!-- Sticky Header -->
        <div class="sticky top-0 z-50 bg-white border-b border-gray-200 px-8 py-4 shadow-sm">
          <div class="flex items-center justify-between max-w-[1920px] mx-auto">
            <div>
              <h1 class="text-xl font-medium text-gray-900">Infrastructure Configuration</h1>
              <p class="text-sm text-gray-500 mt-0.5">All 100+ settings visible in one screen • Zero modals • Instant access</p>
            </div>
            <div class="flex items-center gap-3">
              <button class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-300 transition-colors">
                🧪 Test All Connections
              </button>
              <button class="px-5 py-2 rounded-lg bg-black text-sm font-medium text-white hover:bg-gray-800 transition-colors shadow-sm">
                💾 Save Configuration
              </button>
            </div>
          </div>
        </div>

        <!-- Main Layout -->
        <div class="flex h-[calc(100vh-73px)] overflow-hidden">
          
          <!-- LEFT PANEL: Service Selector -->
          <div class="w-72 border-r border-gray-200 bg-gray-50 overflow-y-auto">
            <div class="p-6 space-y-2">
              <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Infrastructure Services</div>
              ${this.renderServiceTab('postgresql', 'PostgreSQL', 'connected', '🗄️')}
              ${this.renderServiceTab('redis', 'Redis', 'connected', '⚡')}
              ${this.renderServiceTab('temporal', 'Temporal', 'connected', '⏱️')}
              ${this.renderServiceTab('keycloak', 'Keycloak', 'warning', '🔐')}
              ${this.renderServiceTab('vault', 'Vault', 'connected', '🔒')}
              ${this.renderServiceTab('opa', 'OPA', 'connected', '📜')}
              ${this.renderServiceTab('kafka', 'Kafka', 'error', '📡')}
              ${this.renderServiceTab('lago', 'Lago', 'connected', '💵')}
              ${this.renderServiceTab('paypal', 'PayPal', 'connected', '💳')}
              
              <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-6 mb-3">AI Workers</div>
              ${this.renderServiceTab('llm', 'LLM Providers', 'connected', '🤖')}
              ${this.renderServiceTab('stt', 'Speech-to-Text', 'connected', '🎤')}
              ${this.renderServiceTab('tts', 'Text-to-Speech', 'connected', '🔊')}
              
              <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-6 mb-3">Platform</div>
              ${this.renderServiceTab('app', 'App Settings', 'connected', '⚙️')}
            </div>
          </div>

          <!-- RIGHT PANEL: Settings Display -->
          <div class="flex-1 overflow-y-auto bg-white">
            <div class="max-w-6xl mx-auto p-8">
              ${this.renderServiceSettings()}
            </div>
          </div>

        </div>
      </saas-layout>
    `;
  }

  private renderServiceTab(id: Service, name: string, status: 'connected' | 'warning' | 'error', icon: string) {
    const isSelected = this.selectedService === id;
    const statusColors = {
      connected: 'bg-green-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-500'
    };

    return html`
      <div 
        @click="${() => this.selectedService = id}"
        class="group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${isSelected
        ? 'bg-white shadow-sm border border-gray-200'
        : 'hover:bg-white/50'
      }"
      >
        <span class="text-2xl">${icon}</span>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-900 truncate">${name}</div>
          <div class="flex items-center gap-1.5 mt-0.5">
            <div class="w-1.5 h-1.5 rounded-full ${statusColors[status]}"></div>
            <span class="text-xs text-gray-500">${status}</span>
          </div>
        </div>
      </div>
    `;
  }

  private renderServiceSettings() {
    switch (this.selectedService) {
      case 'postgresql': return this.renderPostgreSQLSettings();
      case 'redis': return this.renderRedisSettings();
      case 'temporal': return this.renderTemporalSettings();
      case 'keycloak': return this.renderKeycloakSettings();
      case 'vault': return this.renderVaultSettings();
      case 'opa': return this.renderOPASettings();
      case 'kafka': return this.renderKafkaSettings();
      case 'lago': return this.renderLagoSettings();
      case 'paypal': return this.renderPayPalSettings();
      case 'llm': return this.renderLLMSettings();
      case 'stt': return this.renderSTTSettings();
      case 'tts': return this.renderTTSSettings();
      case 'app': return this.renderAppSettings();
      default: return html``;
    }
  }

  // ==================== POSTGRESQL ====================
  private renderPostgreSQLSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-3xl shadow-lg">
            🗄️
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">PostgreSQL Database</h2>
            <p class="text-sm text-gray-600 mt-1">Primary relational database for all tenant data, sessions, and audit logs</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Connection Details', [
      this.renderInput('DB_HOST', 'Host', 'localhost', 'Database server hostname or IP address'),
      this.renderInput('DB_PORT', 'Port', '5432', 'PostgreSQL server port', 'number'),
      this.renderInput('DB_NAME', 'Database Name', 'agentvoicebox', 'Database name'),
      this.renderInput('DB_USER', 'Username', 'agentvoicebox', 'Database user'),
      this.renderInput('DB_PASSWORD', 'Password', '••••••••', 'Database password', 'password'),
    ])}

        ${this.renderSection('pool', 'Connection Pool', [
      this.renderInput('DB_CONN_MAX_AGE', 'Max Age (seconds)', '60', 'Maximum lifetime for a connection', 'number'),
      this.renderToggle('CONN_HEALTH_CHECKS', 'Health Checks', true, 'Periodic connection health verification'),
      this.renderInput('CONN_TIMEOUT', 'Connect Timeout (s)', '10', 'Connection timeout seconds', 'number'),
    ])}

        ${this.renderSection('performance', 'Performance Tuning', [
      this.renderInput('SHARED_BUFFERS', 'Shared Buffers', '256MB', 'Buffer cache size'),
      this.renderInput('WORK_MEM', 'Work Memory', '4MB', 'Memory per operation'),
      this.renderInput('EFFECTIVE_CACHE_SIZE', 'Cache Size', '1GB', 'Planner cache assumption'),
      this.renderToggle('QUERY_LOGGING', 'Query Logging', false, 'Log all SQL queries (debug only)'),
    ])}
      </div>
    `;
  }

  // ==================== REDIS ====================
  private renderRedisSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center text-3xl shadow-lg">
            ⚡
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Redis Cache & Pub/Sub</h2>
            <p class="text-sm text-gray-600 mt-1">In-memory data store for caching, sessions, and real-time messaging</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Connection', [
      this.renderInput('REDIS_URL', 'Redis URL', 'redis://localhost:6379/0', 'Full Redis connection URL'),
      this.renderInput('REDIS_MAX_CONNECTIONS', 'Max Connections', '200', 'Connection pool size', 'number'),
      this.renderInput('REDIS_SOCKET_TIMEOUT', 'Socket Timeout (s)', '5.0', 'Socket timeout', 'number'),
      this.renderInput('REDIS_SOCKET_CONNECT_TIMEOUT', 'Connect Timeout (s)', '5.0', 'Connection timeout', 'number'),
      this.renderToggle('REDIS_RETRY_ON_TIMEOUT', 'Retry on Timeout', true, 'Automatically retry failed operations'),
      this.renderInput('REDIS_HEALTH_CHECK_INTERVAL', 'Health Check (s)', '30', 'Health check interval', 'number'),
    ])}

        ${this.renderSection('databases', 'Database Indices', [
      this.renderInput('REDIS_CACHE_DB', 'Cache DB', '1', 'Django cache database index', 'number'),
      this.renderInput('REDIS_SESSION_DB', 'Session DB', '2', 'User sessions database index', 'number'),
      this.renderInput('REDIS_CHANNEL_DB', 'Channel DB', '3', 'WebSocket channels database index', 'number'),
    ])}

        ${this.renderSection('memory', 'Memory Management', [
      this.renderInput('MAX_MEMORY', 'Max Memory', '512MB', 'Maximum memory Redis can use'),
      this.renderSelect('EVICTION_POLICY', 'Eviction Policy', ['volatile-lru', 'allkeys-lru', 'volatile-ttl', 'noeviction'], 'volatile-lru', 'Key eviction strategy'),
      this.renderToggle('PERSISTENCE', 'Persistence', false, 'Enable RDB/AOF persistence'),
    ])}
      </div>
    `;
  }

  // ==================== TEMPORAL ====================
  private renderTemporalSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-3xl shadow-lg">
            ⏱️
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Temporal Workflows</h2>
            <p class="text-sm text-gray-600 mt-1">Distributed workflow orchestration for long-running tasks</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Server Configuration', [
      this.renderInput('TEMPORAL_HOST', 'Host', 'localhost:7233', 'Temporal server address:port'),
      this.renderInput('TEMPORAL_NAMESPACE', 'Namespace', 'agentvoicebox', 'Workflow namespace'),
      this.renderInput('TEMPORAL_TASK_QUEUE', 'Task Queue', 'default', 'Default task queue name'),
    ])}

        ${this.renderSection('workers', 'Worker Streams', [
      this.renderInput('LLM_STREAM_REQUESTS', 'LLM Stream', 'llm:requests', 'Redis stream for LLM requests'),
      this.renderInput('LLM_GROUP_WORKERS', 'LLM Group', 'llm-workers', 'LLM consumer group'),
      this.renderInput('STT_STREAM_AUDIO', 'STT Stream', 'audio:stt', 'Redis stream for STT audio'),
      this.renderInput('STT_GROUP_WORKERS', 'STT Group', 'stt-workers', 'STT consumer group'),
      this.renderInput('TTS_STREAM_REQUESTS', 'TTS Stream', 'tts:requests', 'Redis stream for TTS'),
      this.renderInput('TTS_GROUP_WORKERS', 'TTS Group', 'tts-workers', 'TTS consumer group'),
    ])}
      </div>
    `;
  }

  // ==================== KEYCLOAK ====================
  private renderKeycloakSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center text-3xl shadow-lg">
            🔐
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Keycloak Authentication</h2>
            <p class="text-sm text-gray-600 mt-1">OAuth2/OIDC identity provider for SSO and JWT authentication</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Server Configuration', [
      this.renderInput('KEYCLOAK_URL', 'Server URL', 'http://localhost:8080', 'Keycloak server URL'),
      this.renderInput('KEYCLOAK_REALM', 'Realm', 'agentvoicebox', 'Keycloak realm name'),
      this.renderInput('KEYCLOAK_CLIENT_ID', 'Client ID', 'agentvoicebox-backend', 'OAuth client ID'),
      this.renderInput('KEYCLOAK_CLIENT_SECRET', 'Client Secret', '••••••••', 'OAuth client secret (confidential clients)', 'password'),
    ])}
      </div>
    `;
  }

  // ==================== VAULT ====================
  private renderVaultSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center text-3xl shadow-lg">
            🔒
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">HashiCorp Vault</h2>
            <p class="text-sm text-gray-600 mt-1">Secrets management for API keys, passwords, and encryption keys</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Connection', [
      this.renderInput('VAULT_ADDR', 'Server Address', 'http://localhost:8200', 'Vault server URL'),
      this.renderInput('VAULT_TOKEN', 'Root Token', '••••••••', 'Development only - DO NOT use in production', 'password'),
      this.renderInput('VAULT_MOUNT_POINT', 'Mount Point', 'secret', 'KV secrets engine mount point'),
      this.renderToggle('VAULT_FAIL_FAST', 'Fail Fast', true, 'Fail startup if Vault unavailable'),
    ])}

        ${this.renderSection('approle', 'AppRole Authentication (Production)', [
      this.renderInput('VAULT_ROLE_ID', 'Role ID', '', 'AppRole role ID', 'password'),
      this.renderInput('VAULT_SECRET_ID', 'Secret ID', '', 'AppRole secret ID', 'password'),
    ])}
      </div>
    `;
  }

  // ==================== OPA ====================
  private renderOPASettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-3xl shadow-lg">
            📜
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Open Policy Agent (OPA)</h2>
            <p class="text-sm text-gray-600 mt-1">Policy-based authorization and access control</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Configuration', [
      this.renderInput('OPA_URL', 'Server URL', 'http://localhost:8181', 'OPA server address'),
      this.renderInput('OPA_DECISION_PATH', 'Decision Path', '/v1/data/agentvoicebox/allow', 'OPA policy decision endpoint'),
      this.renderInput('OPA_TIMEOUT_SECONDS', 'Timeout (s)', '3', 'Request timeout seconds', 'number'),
      this.renderToggle('OPA_ENABLED', 'Enabled', true, 'Enable OPA policy enforcement'),
    ])}
      </div>
    `;
  }

  // ==================== KAFKA ====================
  private renderKafkaSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center text-3xl shadow-lg">
            📡
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Apache Kafka</h2>
            <p class="text-sm text-gray-600 mt-1">Event streaming platform for real-time data pipelines</p>
          </div>
        </div>

        ${this.renderSection('connection', 'Connection', [
      this.renderInput('KAFKA_BOOTSTRAP_SERVERS', 'Bootstrap Servers', 'localhost:9092', 'Comma-separated broker addresses'),
      this.renderInput('KAFKA_CONSUMER_GROUP', 'Consumer Group', 'agentvoicebox-backend', 'Consumer group ID'),
      this.renderSelect('KAFKA_SECURITY_PROTOCOL', 'Security Protocol', ['PLAINTEXT', 'SSL', 'SASL_PLAINTEXT', 'SASL_SSL'], 'PLAINTEXT', 'Security protocol'),
      this.renderToggle('KAFKA_ENABLED', 'Enabled', false, 'Enable Kafka event streaming'),
    ])}
      </div>
    `;
  }

  // ==================== LAGO ====================
  private renderLagoSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center text-3xl shadow-lg">
            💵
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Lago Billing</h2>
            <p class="text-sm text-gray-600 mt-1">Usage-based billing and invoice generation</p>
          </div>
        </div>

        ${this.renderSection('connection', 'API Configuration', [
      this.renderInput('LAGO_API_URL', 'API URL', 'http://localhost:3000', 'Lago API server URL'),
      this.renderInput('LAGO_API_KEY', 'API Key', '••••••••', 'Lago authentication key', 'password'),
      this.renderInput('LAGO_WEBHOOK_SECRET', 'Webhook Secret', '••••••••', 'HMAC webhook validation secret', 'password'),
    ])}
      </div>
    `;
  }

  // ==================== PAYPAL ====================
  private renderPayPalSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-3xl shadow-lg">
            💳
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">PayPal Payments</h2>
            <p class="text-sm text-gray-600 mt-1">Subscription billing and one-time payments via PayPal</p>
          </div>
        </div>

        ${this.renderSection('connection', 'API Configuration', [
      this.renderInput('PAYPAL_CLIENT_ID', 'Client ID', 'your-paypal-client-id', 'PayPal REST API client ID'),
      this.renderInput('PAYPAL_CLIENT_SECRET', 'Client Secret', '••••••••', 'PayPal REST API client secret', 'password'),
      this.renderSelect('PAYPAL_ENVIRONMENT', 'Environment', ['sandbox', 'live'], 'sandbox', 'PayPal API environment'),
      this.renderInput('PAYPAL_WEBHOOK_ID', 'Webhook ID', '', 'PayPal webhook ID for signature verification'),
      this.renderToggle('PAYPAL_ENABLED', 'Enabled', false, 'Enable PayPal payment processing'),
    ])}

        ${this.renderSection('subscription', 'Subscription Plans', [
      this.renderInput('PAYPAL_PLAN_STARTER', 'Starter Plan ID', '', 'PayPal plan ID for Starter tier'),
      this.renderInput('PAYPAL_PLAN_PRO', 'Pro Plan ID', '', 'PayPal plan ID for Pro tier'),
      this.renderInput('PAYPAL_PLAN_ENTERPRISE', 'Enterprise Plan ID', '', 'PayPal plan ID for Enterprise tier'),
    ])}

        ${this.renderSection('webhooks', 'Webhook Events', [
      this.renderToggle('PAYPAL_WEBHOOK_PAYMENT_COMPLETED', 'Payment Completed', true, 'Handle PAYMENT.CAPTURE.COMPLETED events'),
      this.renderToggle('PAYPAL_WEBHOOK_SUBSCRIPTION_CREATED', 'Subscription Created', true, 'Handle BILLING.SUBSCRIPTION.CREATED events'),
      this.renderToggle('PAYPAL_WEBHOOK_SUBSCRIPTION_CANCELLED', 'Subscription Cancelled', true, 'Handle BILLING.SUBSCRIPTION.CANCELLED events'),
    ])}
      </div>
    `;
  }

  // ==================== LLM ====================
  private renderLLMSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center text-3xl shadow-lg">
            🤖
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">LLM Providers</h2>
            <p class="text-sm text-gray-600 mt-1">Large language model configuration for conversation AI</p>
          </div>
        </div>

        ${this.renderSection('providers', 'Providers', [
      this.renderInput('GROQ_API_KEY', 'Groq API Key', '••••••••', 'Groq API key', 'password'),
      this.renderInput('GROQ_API_BASE', 'Groq Base URL', 'https://api.groq.com/openai/v1', 'Groq API base URL'),
      this.renderInput('OPENAI_API_KEY', 'OpenAI API Key', '••••••••', 'OpenAI API key', 'password'),
      this.renderInput('OPENAI_API_BASE', 'OpenAI Base URL', 'https://api.openai.com/v1', 'OpenAI API base URL'),
      this.renderInput('OLLAMA_BASE_URL', 'Ollama URL', 'http://localhost:11434', 'Ollama self-hosted LLM URL'),
    ])}

        ${this.renderSection('defaults', 'Default Configuration', [
      this.renderSelect('LLM_DEFAULT_PROVIDER', 'Default Provider', ['groq', 'openai', 'ollama'], 'groq', 'Primary LLM provider'),
      this.renderInput('LLM_DEFAULT_MODEL', 'Default Model', 'llama-3.1-70b-versatile', 'Default model name'),
      this.renderInput('LLM_PROVIDER_PRIORITY', 'Provider Priority', 'groq,openai,ollama', 'Failover priority (comma-separated)'),
      this.renderInput('LLM_MAX_TOKENS', 'Max Tokens', '1024', 'Default max tokens', 'number'),
      this.renderInput('LLM_TEMPERATURE', 'Temperature', '0.7', 'Sampling temperature', 'number'),
      this.renderInput('LLM_MAX_HISTORY_ITEMS', 'Max History', '40', 'Conversation history items', 'number'),
    ])}

        ${this.renderSection('circuit-breaker', 'Circuit Breaker', [
      this.renderInput('LLM_CIRCUIT_BREAKER_THRESHOLD', 'Failure Threshold', '5', 'Failures before circuit opens', 'number'),
      this.renderInput('LLM_CIRCUIT_BREAKER_TIMEOUT', 'Timeout (s)', '30', 'Circuit open duration', 'number'),
    ])}
      </div>
    `;
  }

  // ==================== STT ====================
  private renderSTTSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center text-3xl shadow-lg">
            🎤
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Speech-to-Text Worker</h2>
            <p class="text-sm text-gray-600 mt-1">Whisper model configuration for audio transcription</p>
          </div>
        </div>

        ${this.renderSection('model', 'Model Configuration', [
      this.renderSelect('STT_MODEL', 'Model Size', ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'], 'base', 'Whisper model size'),
      this.renderSelect('STT_DEVICE', 'Device', ['cpu', 'cuda', 'auto'], 'auto', 'Processing device'),
      this.renderSelect('STT_COMPUTE_TYPE', 'Compute Type', ['int8', 'float16', 'float32'], 'float16', 'Computation precision'),
      this.renderInput('STT_BATCH_SIZE', 'Batch Size', '4', 'Concurrent transcriptions', 'number'),
      this.renderInput('STT_SAMPLE_RATE', 'Sample Rate', '16000', 'Audio sample rate (Hz)', 'number'),
    ])}
      </div>
    `;
  }

  // ==================== TTS ====================
  private renderTTSSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-3xl shadow-lg">
            🔊
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Text-to-Speech Worker</h2>
            <p class="text-sm text-gray-600 mt-1">Kokoro ONNX model configuration for speech synthesis</p>
          </div>
        </div>

        ${this.renderSection('model', 'Model Configuration', [
      this.renderInput('TTS_MODEL_DIR', 'Model Directory', '/app/cache/kokoro', 'Kokoro model directory path'),
      this.renderInput('TTS_MODEL_FILE', 'Model File', 'kokoro-v1.0.onnx', 'ONNX model filename'),
      this.renderInput('TTS_VOICES_FILE', 'Voices File', 'voices-v1.0.bin', 'Voices binary filename'),
      this.renderInput('TTS_DEFAULT_VOICE', 'Default Voice', 'am_onyx', 'Default voice ID'),
      this.renderInput('TTS_DEFAULT_SPEED', 'Default Speed', '1.1', 'Playback speed multiplier', 'number'),
      this.renderInput('TTS_CHUNK_SIZE', 'Chunk Size', '24000', 'Audio chunk size (samples)', 'number'),
    ])}
      </div>
    `;
  }

  // ==================== APP SETTINGS ====================
  private renderAppSettings() {
    return html`
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-slate-500 to-slate-600 flex items-center justify-center text-3xl shadow-lg">
            ⚙️
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">Application Settings</h2>
            <p class="text-sm text-gray-600 mt-1">Django core configuration, CORS, rate limiting, and observability</p>
          </div>
        </div>

        ${this.renderSection('django', 'Django Core', [
      this.renderInput('DJANGO_SECRET_KEY', 'Secret Key', '••••••••', 'Cryptographic signing key (50+ chars)', 'password'),
      this.renderToggle('DJANGO_DEBUG', 'Debug Mode', false, 'Enable debug mode (dev only)'),
      this.renderInput('DJANGO_ALLOWED_HOSTS', 'Allowed Hosts', 'localhost,127.0.0.1', 'Comma-separated allowed hosts'),
      this.renderInput('VOICE_AGENT_BASE_URL', 'API Base URL', 'http://localhost:65020', 'Public HTTP base URL'),
      this.renderInput('VOICE_AGENT_WS_BASE_URL', 'WebSocket URL', 'ws://localhost:65020', 'Public WebSocket URL'),
    ])}

        ${this.renderSection('cors', 'CORS Configuration', [
      this.renderInput('CORS_ALLOWED_ORIGINS', 'Allowed Origins', 'http://localhost:3000,http://localhost:5173', 'Comma-separated CORS origins'),
      this.renderToggle('CORS_ALLOW_CREDENTIALS', 'Allow Credentials', true, 'Allow cookies and auth headers'),
    ])}

        ${this.renderSection('rate-limits', 'Rate Limiting', [
      this.renderInput('RATE_LIMIT_DEFAULT', 'Default (per min)', '60', 'Default rate limit', 'number'),
      this.renderInput('RATE_LIMIT_API_KEY', 'API Key (per min)', '120', 'API key rate limit', 'number'),
      this.renderInput('RATE_LIMIT_ADMIN', 'Admin (per min)', '300', 'Admin rate limit', 'number'),
      this.renderInput('REALTIME_REQUESTS_PER_MINUTE', 'Realtime Requests', '100', 'Realtime requests/min', 'number'),
      this.renderInput('REALTIME_TOKENS_PER_MINUTE', 'Realtime Tokens', '10000', 'Realtime tokens/min', 'number'),
    ])}

        ${this.renderSection('observability', 'Logging & Monitoring', [
      this.renderSelect('LOG_LEVEL', 'Log Level', ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 'INFO', 'Application logging level'),
      this.renderSelect('LOG_FORMAT', 'Log Format', ['json', 'console'], 'json', 'Log output format'),
      this.renderInput('SENTRY_DSN', 'Sentry DSN', '', 'Sentry error tracking DSN (optional)'),
      this.renderToggle('PROMETHEUS_ENABLED', 'Prometheus Metrics', true, 'Enable /metrics endpoint'),
    ])}
      </div>
    `;
  }

  // ==================== RENDER HELPERS ====================

  private renderSection(id: string, title: string, fields: any[]) {
    const isExpanded = this.expandedSections.has(id);

    return html`
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div 
          @click="${() => this.toggleSection(id)}"
          class="flex items-center justify-between px-5 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
        >
          <h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wide">${title}</h3>
          <svg 
            class="w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </div>
        ${isExpanded ? html`
          <div class="p-5 bg-white grid grid-cols-2 gap-x-6 gap-y-4">
            ${fields}
          </div>
        ` : ''}
      </div>
    `;
  }

  private renderInput(id: string, label: string, value: string, help: string, type: string = 'text') {
    return html`
      <div>
        <label class="block text-sm font-medium text-gray-900 mb-1.5">
          ${label}
          <span class="text-xs font-mono text-gray-500 ml-2">${id}</span>
        </label>
        <input 
          type="${type}"
          value="${value}"
          placeholder="${value}"
          class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent font-mono"
        />
        ${help ? html`<p class="text-xs text-gray-500 mt-1">${help}</p>` : ''}
      </div>
    `;
  }

  private renderSelect(id: string, label: string, options: string[], selected: string, help: string) {
    return html`
      <div>
        <label class="block text-sm font-medium text-gray-900 mb-1.5">
          ${label}
          <span class="text-xs font-mono text-gray-500 ml-2">${id}</span>
        </label>
        <select class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent">
          ${options.map(opt => html`<option ?selected="${opt === selected}">${opt}</option>`)}
        </select>
        ${help ? html`<p class="text-xs text-gray-500 mt-1">${help}</p>` : ''}
      </div>
    `;
  }

  private renderToggle(id: string, label: string, checked: boolean, help: string) {
    return html`
      <div class="flex items-start justify-between">
        <div class="flex-1 pr-4">
          <label class="block text-sm font-medium text-gray-900">
            ${label}
            <span class="text-xs font-mono text-gray-500 ml-2">${id}</span>
          </label>
          ${help ? html`<p class="text-xs text-gray-500 mt-1">${help}</p>` : ''}
        </div>
        <div class="relative w-11 h-6 rounded-full cursor-pointer transition-colors ${checked ? 'bg-black' : 'bg-gray-300'}">
          <div class="absolute top-0.5 ${checked ? 'right-0.5' : 'left-0.5'} w-5 h-5 bg-white rounded-full shadow transition-all duration-200"></div>
        </div>
      </div>
    `;
  }

  private toggleSection(id: string) {
    if (this.expandedSections.has(id)) {
      this.expandedSections.delete(id);
    } else {
      this.expandedSections.add(id);
    }
    this.requestUpdate();
  }
}
