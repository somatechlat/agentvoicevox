yES # Software Requirements Specification (SRS)

## LLM Provider Configuration Module

**Document Identifier:** AVB-SRS-UI-LLM-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Parent Document:** AVB-SRS-UI-001  

---

## 1. Module Overview

### 1.1 Purpose

This module provides UI for configuring Large Language Model (LLM) providers including Groq, OpenAI, and local models (Ollama, llama.cpp).

### 1.2 Lit Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| LLM Dashboard | `<eog-llm-dashboard>` | Main LLM configuration page |
| Provider Selector | `<eog-llm-provider-selector>` | Provider selection cards |
| Provider Card | `<eog-llm-provider-card>` | Individual provider config |
| Model Selector | `<eog-llm-model-selector>` | Model dropdown with details |
| Prompt Editor | `<eog-prompt-editor>` | System prompt editor |
| Token Counter | `<eog-token-counter>` | Real-time token counting |
| Cost Estimator | `<eog-cost-estimator>` | Usage cost estimation |
| LLM Test | `<eog-llm-test>` | Chat completion testing |

### 1.3 Communication Protocols

| Protocol | Endpoint | Purpose |
|----------|----------|---------|
| REST | `/api/v1/voice/llm/config` | LLM configuration CRUD |
| REST | `/api/v1/voice/llm/providers` | Available providers list |
| REST | `/api/v1/voice/llm/models` | Models per provider |
| REST | `/api/v1/voice/llm/test` | One-shot completion test |
| WebSocket | `/ws/v1/llm/stream` | Streaming completions |
| WebSocket | `/ws/v1/llm/usage` | Real-time usage updates |

---

## 2. Functional Requirements

### 2.1 LLM Dashboard (F-LLM-DASH)

**Route:** `/dashboard/voice/llm`  
**Component:** `<eog-llm-dashboard>`  
**Access:** ADMIN, DEVELOPER  

#### F-LLM-DASH-001: Dashboard Overview

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-DASH-001.1 | The `<eog-llm-dashboard>` SHALL display at route `/dashboard/voice/llm` | Critical | Test |
| F-LLM-DASH-001.2 | The component SHALL display active provider and model | High | Test |
| F-LLM-DASH-001.3 | The component SHALL display API key status (configured/missing) | High | Test |
| F-LLM-DASH-001.4 | The component SHALL display today's usage (requests, tokens, cost) | High | Test |
| F-LLM-DASH-001.5 | The component SHALL update usage via WebSocket `/ws/v1/llm/usage` | High | Test |
| F-LLM-DASH-001.6 | The component SHALL display rate limit status | High | Test |

### 2.2 Provider Selection (F-LLM-PROVIDER)

**Route:** `/dashboard/voice/llm/provider`  
**Component:** `<eog-llm-provider-selector>`  
**Access:** ADMIN, DEVELOPER  

#### F-LLM-PROVIDER-001: Provider Cards

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROVIDER-001.1 | The component SHALL display provider cards: Groq, OpenAI, Ollama, Custom | Critical | Test |
| F-LLM-PROVIDER-001.2 | Each `<eog-llm-provider-card>` SHALL use `--eog-glass-surface` background | High | Inspection |
| F-LLM-PROVIDER-001.3 | The active provider card SHALL have `--eog-accent-primary` border | High | Inspection |
| F-LLM-PROVIDER-001.4 | Each card SHALL display: Logo, Name, Description, Status | High | Test |
| F-LLM-PROVIDER-001.5 | Each card SHALL display supported models count | High | Test |
| F-LLM-PROVIDER-001.6 | Each card SHALL display pricing tier (free/paid) | High | Test |

#### F-LLM-PROVIDER-002: Groq Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROVIDER-002.1 | The component SHALL provide API key input (masked) | Critical | Test |
| F-LLM-PROVIDER-002.2 | The component SHALL provide "Test Connection" button | High | Test |
| F-LLM-PROVIDER-002.3 | The component SHALL display connection status with latency | High | Test |
| F-LLM-PROVIDER-002.4 | The component SHALL allow model selection from Groq models | High | Test |

**Groq Models:**

| Model | Context | Speed | Use Case |
|-------|---------|-------|----------|
| llama-3.3-70b-versatile | 128K | Fast | General purpose |
| llama-3.1-70b-versatile | 128K | Fast | General purpose |
| llama-3.1-8b-instant | 128K | Ultra-fast | Quick responses |
| llama-guard-3-8b | 8K | Fast | Content moderation |
| mixtral-8x7b-32768 | 32K | Fast | Complex reasoning |
| gemma2-9b-it | 8K | Fast | Instruction following |

#### F-LLM-PROVIDER-003: OpenAI Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROVIDER-003.1 | The component SHALL provide API key input (masked) | Critical | Test |
| F-LLM-PROVIDER-003.2 | The component SHALL provide organization ID input (optional) | Medium | Test |
| F-LLM-PROVIDER-003.3 | The component SHALL provide base URL override (for Azure) | Medium | Test |
| F-LLM-PROVIDER-003.4 | The component SHALL allow model selection from OpenAI models | High | Test |

**OpenAI Models:**

| Model | Context | Input $/1M | Output $/1M | Use Case |
|-------|---------|------------|-------------|----------|
| gpt-4o | 128K | $2.50 | $10.00 | Best quality |
| gpt-4o-mini | 128K | $0.15 | $0.60 | Cost-effective |
| gpt-4-turbo | 128K | $10.00 | $30.00 | Complex tasks |
| gpt-3.5-turbo | 16K | $0.50 | $1.50 | Fast, cheap |
| o1-preview | 128K | $15.00 | $60.00 | Reasoning |
| o1-mini | 128K | $3.00 | $12.00 | Reasoning (fast) |

#### F-LLM-PROVIDER-004: Ollama Configuration (Local)

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROVIDER-004.1 | The component SHALL provide Ollama server URL input | Critical | Test |
| F-LLM-PROVIDER-004.2 | The component SHALL default to `http://localhost:11434` | High | Test |
| F-LLM-PROVIDER-004.3 | The component SHALL fetch available models from Ollama API | High | Test |
| F-LLM-PROVIDER-004.4 | The component SHALL display model size and quantization | High | Test |
| F-LLM-PROVIDER-004.5 | The component SHALL provide "Pull Model" action | Medium | Test |

### 2.3 Model Configuration (F-LLM-MODEL)

**Route:** `/dashboard/voice/llm/model`  
**Component:** `<eog-llm-model-selector>`  
**Access:** ADMIN, DEVELOPER  

#### F-LLM-MODEL-001: Model Selection

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-MODEL-001.1 | The `<eog-llm-model-selector>` SHALL display models for active provider | Critical | Test |
| F-LLM-MODEL-001.2 | The component SHALL display model details: context window, pricing | High | Test |
| F-LLM-MODEL-001.3 | The component SHALL indicate recommended models | Medium | Test |
| F-LLM-MODEL-001.4 | The component SHALL allow custom model ID input | Medium | Test |

#### F-LLM-MODEL-002: Generation Parameters

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-MODEL-002.1 | The component SHALL provide temperature slider (0.0 - 2.0, default 0.7) | High | Test |
| F-LLM-MODEL-002.2 | The component SHALL provide max_tokens input (1 - context_max) | High | Test |
| F-LLM-MODEL-002.3 | The component SHALL provide top_p slider (0.0 - 1.0, default 1.0) | Medium | Test |
| F-LLM-MODEL-002.4 | The component SHALL provide frequency_penalty slider (-2.0 - 2.0) | Medium | Test |
| F-LLM-MODEL-002.5 | The component SHALL provide presence_penalty slider (-2.0 - 2.0) | Medium | Test |
| F-LLM-MODEL-002.6 | The component SHALL provide stop sequences input (array) | Medium | Test |
| F-LLM-MODEL-002.7 | All sliders SHALL use `<eog-slider>` with AgentSkin styling | High | Inspection |

### 2.4 System Prompt Editor (F-LLM-PROMPT)

**Route:** `/dashboard/voice/llm/prompt`  
**Component:** `<eog-prompt-editor>`  
**Access:** ADMIN, DEVELOPER  

#### F-LLM-PROMPT-001: Prompt Editor

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROMPT-001.1 | The `<eog-prompt-editor>` SHALL provide multi-line text editor | Critical | Test |
| F-LLM-PROMPT-001.2 | The editor SHALL use `--eog-font-mono` for text | High | Inspection |
| F-LLM-PROMPT-001.3 | The editor SHALL use `--eog-glass-surface` background | High | Inspection |
| F-LLM-PROMPT-001.4 | The component SHALL display real-time token count via `<eog-token-counter>` | High | Test |
| F-LLM-PROMPT-001.5 | The component SHALL warn when prompt exceeds 50% of context window | High | Test |
| F-LLM-PROMPT-001.6 | The component SHALL provide syntax highlighting for variables | Medium | Test |
| F-LLM-PROMPT-001.7 | The component SHALL support template variables: `{{user_name}}`, `{{date}}`, etc. | Medium | Test |

#### F-LLM-PROMPT-002: Prompt Templates

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-PROMPT-002.1 | The component SHALL provide built-in prompt templates | High | Test |
| F-LLM-PROMPT-002.2 | Templates SHALL include: Assistant, Customer Service, Technical Support, Creative | High | Inspection |
| F-LLM-PROMPT-002.3 | The component SHALL allow saving custom templates | High | Test |
| F-LLM-PROMPT-002.4 | The component SHALL allow importing/exporting templates (JSON) | Medium | Test |

### 2.5 Cost Estimation (F-LLM-COST)

**Component:** `<eog-cost-estimator>`  
**Access:** ADMIN, DEVELOPER, BILLING  

#### F-LLM-COST-001: Cost Display

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-COST-001.1 | The `<eog-cost-estimator>` SHALL display estimated cost per request | High | Test |
| F-LLM-COST-001.2 | The component SHALL calculate based on: prompt tokens + estimated response | High | Test |
| F-LLM-COST-001.3 | The component SHALL display daily/monthly projected cost | High | Test |
| F-LLM-COST-001.4 | The component SHALL update in real-time as settings change | High | Test |
| F-LLM-COST-001.5 | The component SHALL use `--eog-accent-warning` for high cost warnings | High | Inspection |

### 2.6 LLM Test Interface (F-LLM-TEST)

**Route:** `/dashboard/voice/llm/test`  
**Component:** `<eog-llm-test>`  
**Access:** ADMIN, DEVELOPER, OPERATOR  

#### F-LLM-TEST-001: Chat Interface

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-LLM-TEST-001.1 | The `<eog-llm-test>` SHALL provide chat-style test interface | Critical | Test |
| F-LLM-TEST-001.2 | The component SHALL display message history | High | Test |
| F-LLM-TEST-001.3 | The component SHALL stream responses via WebSocket `/ws/v1/llm/stream` | Critical | Test |
| F-LLM-TEST-001.4 | The component SHALL display typing indicator during streaming | High | Test |
| F-LLM-TEST-001.5 | The component SHALL display token usage per message | High | Test |
| F-LLM-TEST-001.6 | The component SHALL display response latency | High | Test |
| F-LLM-TEST-001.7 | The component SHALL provide "Clear History" button | Medium | Test |
| F-LLM-TEST-001.8 | The component SHALL provide "Copy Response" button | Medium | Test |

---

## 3. Lit Component Specifications

### 3.1 `<eog-llm-provider-card>` Component

```typescript
@customElement('eog-llm-provider-card')
export class EogLlmProviderCard extends LitElement {
  static styles = css`
    :host {
      display: block;
    }
    .card {
      background: var(--eog-glass-surface);
      border: 1px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-lg);
      padding: var(--eog-spacing-lg);
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .card:hover {
      transform: translateY(-2px);
      box-shadow: var(--eog-shadow-soft);
    }
    .card.active {
      border-color: var(--eog-accent-primary);
    }
    .card.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .logo {
      width: 48px;
      height: 48px;
      margin-bottom: var(--eog-spacing-md);
    }
    .name {
      font-family: var(--eog-font-sans);
      font-size: var(--eog-text-lg);
      font-weight: 600;
      color: var(--eog-text-main);
    }
    .description {
      font-size: var(--eog-text-sm);
      color: var(--eog-text-dim);
      margin-top: var(--eog-spacing-xs);
    }
    .status {
      display: flex;
      align-items: center;
      gap: var(--eog-spacing-xs);
      margin-top: var(--eog-spacing-md);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: var(--eog-radius-full);
    }
    .status-dot.connected {
      background: var(--eog-accent-success);
    }
    .status-dot.disconnected {
      background: var(--eog-accent-danger);
    }
    .status-dot.unconfigured {
      background: var(--eog-accent-warning);
    }
  `;

  @property({ type: Object }) provider!: LLMProvider;
  @property({ type: Boolean }) active = false;
  @property({ type: String }) status: 'connected' | 'disconnected' | 'unconfigured' = 'unconfigured';

  render() {
    return html`
      <div class="card ${this.active ? 'active' : ''}" @click=${this._handleSelect}>
        <img class="logo" src=${this.provider.logo} alt=${this.provider.name} />
        <div class="name">${this.provider.name}</div>
        <div class="description">${this.provider.description}</div>
        <div class="status">
          <span class="status-dot ${this.status}"></span>
          <span>${this._getStatusText()}</span>
        </div>
        <eog-badge>${this.provider.modelsCount} models</eog-badge>
      </div>
    `;
  }

  private _getStatusText(): string {
    switch (this.status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Connection failed';
      case 'unconfigured': return 'Not configured';
    }
  }

  private _handleSelect() {
    this.dispatchEvent(new CustomEvent('eog-provider-selected', {
      detail: { provider: this.provider },
      bubbles: true, composed: true
    }));
  }
}
```

### 3.2 `<eog-token-counter>` Component

```typescript
@customElement('eog-token-counter')
export class EogTokenCounter extends LitElement {
  static styles = css`
    :host {
      display: inline-flex;
      align-items: center;
      gap: var(--eog-spacing-xs);
      font-family: var(--eog-font-mono);
      font-size: var(--eog-text-sm);
    }
    .count {
      color: var(--eog-text-main);
    }
    .limit {
      color: var(--eog-text-dim);
    }
    .warning {
      color: var(--eog-accent-warning);
    }
    .danger {
      color: var(--eog-accent-danger);
    }
  `;

  @property({ type: Number }) tokens = 0;
  @property({ type: Number }) limit = 4096;

  render() {
    const percentage = (this.tokens / this.limit) * 100;
    const colorClass = percentage > 90 ? 'danger' : percentage > 70 ? 'warning' : '';
    
    return html`
      <span class="count ${colorClass}">${this.tokens.toLocaleString()}</span>
      <span class="limit">/ ${this.limit.toLocaleString()} tokens</span>
    `;
  }
}
```

---

## 4. WebSocket Protocol

### 4.1 LLM Streaming Protocol

**Endpoint:** `/ws/v1/llm/stream`

#### Client → Server

```typescript
// Start completion
{
  "type": "llm.completion.start",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "config": {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7,
    "max_tokens": 1024
  }
}

// Cancel completion
{
  "type": "llm.completion.cancel"
}
```

#### Server → Client

```typescript
// Token delta
{
  "type": "llm.token.delta",
  "content": "Hello",
  "finish_reason": null
}

// Completion done
{
  "type": "llm.completion.done",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  },
  "latency_ms": 1200,
  "cost_usd": 0.0002
}

// Error
{
  "type": "llm.error",
  "code": "RATE_LIMITED",
  "message": "Rate limit exceeded. Retry after 60 seconds."
}
```

---

## 5. RBAC Permissions

| Action | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|----------|-------|-----------|----------|--------|---------|
| View LLM Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Configure Provider | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Set API Keys | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Select Model | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Edit Parameters | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Edit System Prompt | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Run Tests | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| View Usage/Cost | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
