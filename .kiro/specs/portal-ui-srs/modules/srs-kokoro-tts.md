# Software Requirements Specification (SRS)

## Kokoro TTS Configuration Module

**Document Identifier:** AVB-SRS-UI-KOKORO-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Parent Document:** AVB-SRS-UI-001  

---

## 1. Module Overview

### 1.1 Purpose

This module provides the UI for configuring Kokoro Text-to-Speech (TTS) with full voice catalog, model management, and real-time synthesis testing.

### 1.2 Lit Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| TTS Dashboard | `<eog-tts-dashboard>` | Main TTS configuration page |
| Voice Catalog | `<eog-voice-catalog>` | Browse and select voices |
| Voice Card | `<eog-voice-card>` | Individual voice preview |
| Voice Player | `<eog-voice-player>` | Audio playback control |
| TTS Settings | `<eog-tts-settings>` | Configuration form |
| TTS Test | `<eog-tts-test>` | Live synthesis testing |
| Audio Waveform | `<eog-audio-waveform>` | Waveform visualization |

### 1.3 Communication Protocols

| Protocol | Endpoint | Purpose |
|----------|----------|---------|
| REST | `/api/v1/voice/tts/config` | TTS configuration CRUD |
| REST | `/api/v1/voice/tts/voices` | Voice catalog listing |
| REST | `/api/v1/voice/tts/synthesize` | One-shot synthesis |
| WebSocket | `/ws/v1/tts/stream` | Streaming audio synthesis |
| WebSocket | `/ws/v1/tts/model-status` | Model loading status |

---

## 2. Functional Requirements

### 2.1 TTS Dashboard (F-TTS-DASH)

**Route:** `/dashboard/voice/tts`  
**Component:** `<eog-tts-dashboard>`  
**Access:** ADMIN, DEVELOPER  

#### F-TTS-DASH-001: Dashboard Layout

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-DASH-001.1 | The `<eog-tts-dashboard>` SHALL display at route `/dashboard/voice/tts` | Critical | Test |
| F-TTS-DASH-001.2 | The component SHALL use AgentSkin `--eog-bg-void` for page background | High | Inspection |
| F-TTS-DASH-001.3 | The component SHALL display current TTS engine status via `<eog-status-badge>` | High | Test |
| F-TTS-DASH-001.4 | The component SHALL display active voice name and language | High | Test |
| F-TTS-DASH-001.5 | The component SHALL display model info (82M/200M) and compute device | High | Test |
| F-TTS-DASH-001.6 | The component SHALL update status via WebSocket `/ws/v1/tts/model-status` | High | Test |

### 2.2 Voice Catalog (F-TTS-VOICES)

**Route:** `/dashboard/voice/tts/voices`  
**Component:** `<eog-voice-catalog>`  
**Access:** ADMIN, DEVELOPER  

#### F-TTS-VOICES-001: Voice Browser

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-VOICES-001.1 | The `<eog-voice-catalog>` SHALL display voices in responsive grid | Critical | Test |
| F-TTS-VOICES-001.2 | The component SHALL use `--eog-spacing-md` for grid gap | High | Inspection |
| F-TTS-VOICES-001.3 | The component SHALL support filtering by language (15+ languages) | High | Test |
| F-TTS-VOICES-001.4 | The component SHALL support filtering by gender (male, female, neutral) | High | Test |
| F-TTS-VOICES-001.5 | The component SHALL support filtering by style (natural, expressive, news) | Medium | Test |
| F-TTS-VOICES-001.6 | The component SHALL support search by voice name | High | Test |
| F-TTS-VOICES-001.7 | The component SHALL indicate currently active voice with `--eog-accent-primary` border | High | Test |

#### F-TTS-VOICES-002: Voice Card Component

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-VOICES-002.1 | The `<eog-voice-card>` SHALL display voice name, language, gender | Critical | Test |
| F-TTS-VOICES-002.2 | The component SHALL use `--eog-glass-surface` for card background | High | Inspection |
| F-TTS-VOICES-002.3 | The component SHALL use `--eog-radius-lg` for card border radius | High | Inspection |
| F-TTS-VOICES-002.4 | The component SHALL provide "Preview" button to play sample | High | Test |
| F-TTS-VOICES-002.5 | The component SHALL provide "Select" button to activate voice | High | Test |
| F-TTS-VOICES-002.6 | The component SHALL display audio waveform during preview | High | Test |
| F-TTS-VOICES-002.7 | The component SHALL emit `eog-voice-selected` custom event | High | Test |

**Kokoro Voice Catalog:**

| Voice ID | Language | Gender | Style |
|----------|----------|--------|-------|
| af_heart | English (US) | Female | Natural |
| af_bella | English (US) | Female | Expressive |
| af_nicole | English (US) | Female | News |
| af_sarah | English (US) | Female | Conversational |
| af_sky | English (US) | Female | Young |
| am_adam | English (US) | Male | Natural |
| am_michael | English (US) | Male | Deep |
| bf_emma | English (UK) | Female | British |
| bf_isabella | English (UK) | Female | Formal |
| bm_george | English (UK) | Male | British |
| bm_lewis | English (UK) | Male | Narrator |
| af_alloy | English (US) | Female | OpenAI-style |
| am_echo | English (US) | Male | OpenAI-style |
| am_fable | English (US) | Male | Storyteller |
| am_onyx | English (US) | Male | Deep |
| af_nova | English (US) | Female | Bright |
| af_shimmer | English (US) | Female | Warm |
| jf_alpha | Japanese | Female | Natural |
| jf_gongitsune | Japanese | Female | Anime |
| jm_kumo | Japanese | Male | Natural |
| zf_xiaobei | Chinese | Female | Natural |
| zf_xiaoni | Chinese | Female | Young |
| zm_yunjian | Chinese | Male | Natural |
| ef_dora | Spanish | Female | Natural |
| em_alex | Spanish | Male | Natural |
| ff_siwis | French | Female | Natural |
| hf_alpha | Hindi | Female | Natural |
| hf_beta | Hindi | Female | Expressive |
| if_sara | Italian | Female | Natural |
| im_nicola | Italian | Male | Natural |
| pf_dora | Portuguese | Female | Natural |
| pm_alex | Portuguese | Male | Natural |

### 2.3 TTS Settings (F-TTS-SETTINGS)

**Route:** `/dashboard/voice/tts/settings`  
**Component:** `<eog-tts-settings>`  
**Access:** ADMIN, DEVELOPER  

#### F-TTS-SETTINGS-001: Model Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-SETTINGS-001.1 | The `<eog-tts-settings>` SHALL allow model selection: `kokoro-82m`, `kokoro-200m` | Critical | Test |
| F-TTS-SETTINGS-001.2 | The component SHALL display model comparison (quality vs speed vs memory) | High | Inspection |
| F-TTS-SETTINGS-001.3 | The component SHALL allow device selection: `auto`, `cpu`, `cuda` | High | Test |
| F-TTS-SETTINGS-001.4 | The component SHALL display estimated VRAM usage | High | Test |
| F-TTS-SETTINGS-001.5 | The component SHALL require confirmation on model change | High | Test |

#### F-TTS-SETTINGS-002: Synthesis Parameters

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-SETTINGS-002.1 | The component SHALL provide speed slider (0.5x - 2.0x, default 1.0) | High | Test |
| F-TTS-SETTINGS-002.2 | The slider SHALL use `<eog-slider>` with `--eog-accent-primary` track | High | Inspection |
| F-TTS-SETTINGS-002.3 | The component SHALL provide pitch adjustment (-12 to +12 semitones) | Medium | Test |
| F-TTS-SETTINGS-002.4 | The component SHALL provide volume normalization toggle | Medium | Test |
| F-TTS-SETTINGS-002.5 | The component SHALL provide silence trimming toggle | Medium | Test |
| F-TTS-SETTINGS-002.6 | The component SHALL provide sentence splitting toggle | Medium | Test |

#### F-TTS-SETTINGS-003: Audio Output Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-SETTINGS-003.1 | The component SHALL allow sample rate selection: 22050, 24000, 44100, 48000 Hz | High | Test |
| F-TTS-SETTINGS-003.2 | The component SHALL allow audio format selection: PCM16, Float32 | High | Test |
| F-TTS-SETTINGS-003.3 | The component SHALL allow output format: WAV, MP3, OGG, OPUS | High | Test |
| F-TTS-SETTINGS-003.4 | The component SHALL display estimated file size per minute | Medium | Test |

### 2.4 TTS Test Interface (F-TTS-TEST)

**Route:** `/dashboard/voice/tts/test`  
**Component:** `<eog-tts-test>`  
**Access:** ADMIN, DEVELOPER, OPERATOR  

#### F-TTS-TEST-001: Text Input

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-TEST-001.1 | The `<eog-tts-test>` SHALL provide text input area (max 5000 characters) | Critical | Test |
| F-TTS-TEST-001.2 | The textarea SHALL use `--eog-glass-surface` background | High | Inspection |
| F-TTS-TEST-001.3 | The component SHALL display character count | High | Test |
| F-TTS-TEST-001.4 | The component SHALL provide sample text templates | Medium | Test |
| F-TTS-TEST-001.5 | The component SHALL support SSML input toggle | Medium | Test |

#### F-TTS-TEST-002: Synthesis Controls

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-TEST-002.1 | The component SHALL provide "Synthesize" button using `<eog-button variant="primary">` | Critical | Test |
| F-TTS-TEST-002.2 | The component SHALL provide "Stream" button for real-time streaming | High | Test |
| F-TTS-TEST-002.3 | WHEN streaming THEN connect to WebSocket `/ws/v1/tts/stream` | Critical | Test |
| F-TTS-TEST-002.4 | The component SHALL display synthesis progress bar | High | Test |
| F-TTS-TEST-002.5 | The component SHALL display synthesis latency (time to first audio) | High | Test |
| F-TTS-TEST-002.6 | The component SHALL display real-time factor (RTF) | High | Test |

#### F-TTS-TEST-003: Audio Playback

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TTS-TEST-003.1 | The `<eog-voice-player>` SHALL display play/pause/stop controls | Critical | Test |
| F-TTS-TEST-003.2 | The component SHALL display audio waveform via `<eog-audio-waveform>` | High | Test |
| F-TTS-TEST-003.3 | The waveform SHALL use `--eog-accent-primary` for played portion | High | Inspection |
| F-TTS-TEST-003.4 | The component SHALL display current time / total duration | High | Test |
| F-TTS-TEST-003.5 | The component SHALL provide seek functionality | High | Test |
| F-TTS-TEST-003.6 | The component SHALL provide "Download" button | High | Test |
| F-TTS-TEST-003.7 | The component SHALL provide playback speed control (0.5x - 2.0x) | Medium | Test |

---

## 3. Lit Component Specifications

### 3.1 `<eog-voice-card>` Component

```typescript
@customElement('eog-voice-card')
export class EogVoiceCard extends LitElement {
  static styles = css`
    :host {
      display: block;
    }
    .card {
      background: var(--eog-glass-surface);
      border: 1px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-lg);
      padding: var(--eog-spacing-md);
      transition: all 0.2s ease;
    }
    .card:hover {
      transform: translateY(-2px);
      box-shadow: var(--eog-shadow-soft);
    }
    .card.active {
      border-color: var(--eog-accent-primary);
      box-shadow: 0 0 0 2px var(--eog-accent-primary);
    }
    .voice-name {
      font-family: var(--eog-font-sans);
      font-size: var(--eog-text-lg);
      color: var(--eog-text-main);
      margin-bottom: var(--eog-spacing-xs);
    }
    .voice-meta {
      font-size: var(--eog-text-sm);
      color: var(--eog-text-dim);
    }
    .actions {
      display: flex;
      gap: var(--eog-spacing-sm);
      margin-top: var(--eog-spacing-md);
    }
  `;

  @property({ type: Object }) voice!: Voice;
  @property({ type: Boolean }) active = false;
  @state() private playing = false;

  render() {
    return html`
      <div class="card ${this.active ? 'active' : ''}">
        <div class="voice-name">${this.voice.name}</div>
        <div class="voice-meta">
          <eog-badge>${this.voice.language}</eog-badge>
          <eog-badge variant="secondary">${this.voice.gender}</eog-badge>
        </div>
        <eog-audio-waveform 
          .src=${this.voice.sampleUrl}
          .playing=${this.playing}
        ></eog-audio-waveform>
        <div class="actions">
          <eog-button 
            variant="secondary" 
            @eog-click=${this._handlePreview}
          >
            ${this.playing ? 'Stop' : 'Preview'}
          </eog-button>
          <eog-button 
            variant="primary"
            ?disabled=${this.active}
            @eog-click=${this._handleSelect}
          >
            ${this.active ? 'Active' : 'Select'}
          </eog-button>
        </div>
      </div>
    `;
  }

  private _handlePreview() {
    this.playing = !this.playing;
    this.dispatchEvent(new CustomEvent('eog-voice-preview', {
      detail: { voice: this.voice, playing: this.playing },
      bubbles: true, composed: true
    }));
  }

  private _handleSelect() {
    this.dispatchEvent(new CustomEvent('eog-voice-selected', {
      detail: { voice: this.voice },
      bubbles: true, composed: true
    }));
  }
}
```

### 3.2 `<eog-audio-waveform>` Component

```typescript
@customElement('eog-audio-waveform')
export class EogAudioWaveform extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 60px;
    }
    canvas {
      width: 100%;
      height: 100%;
      border-radius: var(--eog-radius-sm);
      background: var(--eog-bg-elevated);
    }
  `;

  @property({ type: String }) src = '';
  @property({ type: Boolean }) playing = false;
  @property({ type: Number }) progress = 0;
  
  private canvas?: HTMLCanvasElement;
  private audioContext?: AudioContext;
  private analyser?: AnalyserNode;

  render() {
    return html`<canvas></canvas>`;
  }

  // Waveform rendering using --eog-accent-primary for played portion
  // and --eog-text-dim for unplayed portion
}
```

---

## 4. WebSocket Protocol

### 4.1 TTS Streaming Protocol

**Endpoint:** `/ws/v1/tts/stream`

#### Client → Server

```typescript
// Start streaming synthesis
{
  "type": "tts.stream.start",
  "text": "Hello, this is a test of the Kokoro TTS system.",
  "voice": "af_heart",
  "config": {
    "speed": 1.0,
    "pitch": 0,
    "sample_rate": 24000,
    "format": "pcm16"
  }
}

// Cancel streaming
{
  "type": "tts.stream.cancel"
}
```

#### Server → Client

```typescript
// Audio chunk (base64 PCM16)
{
  "type": "tts.audio.chunk",
  "audio": "base64_encoded_audio",
  "chunk_index": 0,
  "is_final": false
}

// Synthesis complete
{
  "type": "tts.stream.complete",
  "total_chunks": 15,
  "duration_ms": 3200,
  "latency_ms": 120,
  "rtf": 0.15
}

// Error
{
  "type": "tts.error",
  "code": "VOICE_NOT_FOUND",
  "message": "Voice 'af_heart' not available"
}
```

---

## 5. RBAC Permissions

| Action | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|----------|-------|-----------|----------|--------|---------|
| View TTS Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Browse Voice Catalog | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Select Voice | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Change Model | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Edit Settings | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Run Tests | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Download Audio | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
