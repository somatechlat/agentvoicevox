/**
 * Voice API Service - Connects to AgentVoiceBox Gateway
 * Endpoints: Sessions, STT, TTS, LLM, Personas, Audio Config
 * Gateway URL: configured via VITE_GATEWAY_URL
 */

import { apiClient, ApiResponse } from './api-client';

// Get environment variables from Vite or use defaults
const getEnv = (name: string, defaultValue: string): string => {
  const envVar = (import.meta as any).env?.[name];
  return envVar || defaultValue;
};

// Gateway base URL
const GATEWAY_URL = getEnv('VITE_GATEWAY_URL', 'http://localhost:65020');

// Create gateway client
const gatewayClient = new (apiClient.constructor as typeof import('./api-client').ApiClient)(GATEWAY_URL);

// ============================================================================
// Types - Voice Sessions
// ============================================================================

export interface VoiceSession {
  id: string;
  tenant_id: string;
  project_id: string;
  status: 'active' | 'closed' | 'error';
  model: string;
  instructions?: string;
  persona?: Persona;
  audio_config?: AudioConfig;
  output_modalities: string[];
  tools?: Tool[];
  created_at: string;
  closed_at?: string;
  expires_at?: string;
}

export interface Persona {
  name: string;
  voice: string;
  language: string;
  personality?: string;
  system_prompt?: string;
}

export interface AudioConfig {
  input: {
    format: { type: string; rate: number };
    transcription?: Record<string, unknown>;
    noise_reduction?: Record<string, unknown>;
    turn_detection?: Record<string, unknown>;
  };
  output: {
    format: { type: string; rate: number };
    voice: string;
    speed: number;
  };
}

export interface Tool {
  type: string;
  name: string;
  description: string;
  parameters?: Record<string, unknown>;
}

export interface ConversationItem {
  id: number;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: Record<string, unknown>;
  created_at: string;
}

// ============================================================================
// Types - Workers (STT, TTS, LLM)
// ============================================================================

export interface WorkerStatus {
  id: string;
  type: 'stt' | 'tts' | 'llm';
  status: 'running' | 'idle' | 'error' | 'offline';
  queue_depth: number;
  processed_count: number;
  error_count: number;
  last_heartbeat: string;
  config: Record<string, unknown>;
}

export interface STTConfig {
  model: string;
  device: 'cpu' | 'cuda';
  compute_type: string;
  batch_size: number;
  language?: string;
}

export interface TTSConfig {
  model_dir: string;
  default_voice: string;
  default_speed: number;
  available_voices: string[];
}

export interface LLMConfig {
  default_provider: 'groq' | 'openai' | 'anthropic' | 'local';
  model: string;
  max_tokens: number;
  temperature: number;
  circuit_breaker_threshold: number;
  circuit_breaker_timeout: number;
}

// ============================================================================
// Types - Realtime
// ============================================================================

export interface ClientSecretRequest {
  expires_after?: { anchor: string; seconds: number };
  session?: Partial<VoiceSession>;
}

export interface ClientSecretResponse {
  value: string;
  expires_at: number;
  session: VoiceSession;
}

// ============================================================================
// Voice Sessions API
// ============================================================================

export const sessionsApi = {
  /**
   * List all voice sessions
   */
  async list(params?: {
    status?: string;
    tenant_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<{ sessions: VoiceSession[]; total: number }>> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.tenant_id) query.set('tenant_id', params.tenant_id);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    return gatewayClient.get(`/v1/realtime/sessions?${query}`);
  },

  /**
   * Get session by ID
   */
  async get(sessionId: string): Promise<ApiResponse<VoiceSession>> {
    return gatewayClient.get(`/v1/realtime/sessions/${sessionId}`);
  },

  /**
   * Create a new session
   */
  async create(data: {
    model?: string;
    instructions?: string;
    persona?: Persona;
    audio_config?: AudioConfig;
    tools?: Tool[];
  }): Promise<ApiResponse<VoiceSession>> {
    return gatewayClient.post('/v1/realtime/sessions', data);
  },

  /**
   * Close a session
   */
  async close(sessionId: string): Promise<ApiResponse<VoiceSession>> {
    return gatewayClient.post(`/v1/realtime/sessions/${sessionId}/close`, {});
  },

  /**
   * Get conversation history for a session
   */
  async getConversation(sessionId: string): Promise<ApiResponse<ConversationItem[]>> {
    return gatewayClient.get(`/v1/realtime/sessions/${sessionId}/conversation`);
  },

  /**
   * Create client secret for WebSocket connection
   */
  async createClientSecret(request: ClientSecretRequest): Promise<ApiResponse<ClientSecretResponse>> {
    return gatewayClient.post('/v1/realtime/client_secrets', request);
  },
};

// ============================================================================
// Workers API (STT, TTS, LLM)
// ============================================================================

export const workersApi = {
  /**
   * Get all worker statuses
   */
  async listAll(): Promise<ApiResponse<WorkerStatus[]>> {
    return gatewayClient.get('/v1/admin/workers');
  },

  /**
   * Get STT worker status and config
   */
  async getSTT(): Promise<ApiResponse<{ status: WorkerStatus; config: STTConfig }>> {
    return gatewayClient.get('/v1/admin/workers/stt');
  },

  /**
   * Update STT configuration
   */
  async updateSTT(config: Partial<STTConfig>): Promise<ApiResponse<STTConfig>> {
    return gatewayClient.put('/v1/admin/workers/stt/config', config);
  },

  /**
   * Get TTS worker status and config
   */
  async getTTS(): Promise<ApiResponse<{ status: WorkerStatus; config: TTSConfig }>> {
    return gatewayClient.get('/v1/admin/workers/tts');
  },

  /**
   * Update TTS configuration
   */
  async updateTTS(config: Partial<TTSConfig>): Promise<ApiResponse<TTSConfig>> {
    return gatewayClient.put('/v1/admin/workers/tts/config', config);
  },

  /**
   * Get available TTS voices
   */
  async getVoices(): Promise<ApiResponse<string[]>> {
    return gatewayClient.get('/v1/admin/workers/tts/voices');
  },

  /**
   * Get LLM worker status and config
   */
  async getLLM(): Promise<ApiResponse<{ status: WorkerStatus; config: LLMConfig }>> {
    return gatewayClient.get('/v1/admin/workers/llm');
  },

  /**
   * Update LLM configuration
   */
  async updateLLM(config: Partial<LLMConfig>): Promise<ApiResponse<LLMConfig>> {
    return gatewayClient.put('/v1/admin/workers/llm/config', config);
  },
};

// ============================================================================
// Personas API
// ============================================================================

export const personasApi = {
  /**
   * List all personas
   */
  async list(): Promise<ApiResponse<Persona[]>> {
    return gatewayClient.get('/v1/admin/personas');
  },

  /**
   * Get persona by name
   */
  async get(name: string): Promise<ApiResponse<Persona>> {
    return gatewayClient.get(`/v1/admin/personas/${name}`);
  },

  /**
   * Create a new persona
   */
  async create(persona: Persona): Promise<ApiResponse<Persona>> {
    return gatewayClient.post('/v1/admin/personas', persona);
  },

  /**
   * Update a persona
   */
  async update(name: string, persona: Partial<Persona>): Promise<ApiResponse<Persona>> {
    return gatewayClient.put(`/v1/admin/personas/${name}`, persona);
  },

  /**
   * Delete a persona
   */
  async delete(name: string): Promise<ApiResponse<void>> {
    return gatewayClient.delete(`/v1/admin/personas/${name}`);
  },
};

// ============================================================================
// Health & Metrics API
// ============================================================================

export const healthApi = {
  /**
   * Get gateway health status
   */
  async getHealth(): Promise<ApiResponse<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: Record<string, { status: string; latency_ms: number }>;
  }>> {
    return gatewayClient.get('/health');
  },

  /**
   * Get Prometheus metrics (raw text)
   */
  async getMetrics(): Promise<string> {
    const response = await fetch(`${GATEWAY_URL}/metrics`);
    return response.text();
  },
};

// ============================================================================
// OVOS Settings API
// ============================================================================
export const ovosApi = {
  async getConfig(): Promise<ApiResponse<Record<string, unknown>>> {
    return gatewayClient.get('/v1/voice/ovos/config');
  },
  async updateConfig(config: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
    return gatewayClient.patch('/v1/voice/ovos/config', config);
  },
  async getPlugins(): Promise<ApiResponse<{tts: string[], stt: string[]}>> {
    return gatewayClient.get('/v1/voice/ovos/plugins');
  }
};

// ============================================================================
// Custom Voices (Cloning) API
// ============================================================================
export interface CustomVoice {
  id: string;
  name: string;
  language: string;
  quality: string;
  status: string;
  created_at: string;
  sample_duration_seconds: number;
  is_default: boolean;
  sample_url?: string;
  error_message?: string;
}

export const customVoicesApi = {
  async list(): Promise<ApiResponse<CustomVoice[]>> {
    return gatewayClient.get('/v1/voice/voices');
  },
  async get(id: string): Promise<ApiResponse<CustomVoice>> {
    return gatewayClient.get(`/v1/voice/voices/${id}`);
  },
  async create(formData: FormData): Promise<ApiResponse<CustomVoice>> {
    const url = `${GATEWAY_URL}/v1/voice/voices`;
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    const data = await response.json();
    return { data, status: response.status } as ApiResponse<CustomVoice>;
  },
  async delete(id: string): Promise<ApiResponse<void>> {
    return gatewayClient.delete(`/v1/voice/voices/${id}`);
  },
  async setDefault(id: string): Promise<ApiResponse<CustomVoice>> {
    return gatewayClient.post(`/v1/voice/voices/${id}/default`, {});
  }
};

export { gatewayClient };
