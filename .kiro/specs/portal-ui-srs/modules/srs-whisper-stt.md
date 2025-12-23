# Software Requirements Specification (SRS)

## Whisper STT Configuration Module

**Document Identifier:** AVB-SRS-UI-WHISPER-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Parent Document:** AVB-SRS-UI-001  

---

## 1. Module Overview

### 1.1 Purpose

This module provides the user interface for configuring Whisper Speech-to-Text (STT) settings within the AgentVoiceBox platform. It supports both OpenAI Whisper and Faster-Whisper implementations with full configuration control.

### 1.2 Scope

- Whisper model management (download, selection, deletion)
- Engine selection (whisper, faster-whisper)
- Compute configuration (CPU, CUDA, ROCm)
- Language and transcription settings
- VAD (Voice Activity Detection) configuration
- Real-time transcription monitoring via WebSocket

### 1.3 Communication Protocols

| Protocol | Endpoint | Purpose |
|----------|----------|---------|
| REST | `/api/v1/voice/stt/config` | CRUD operations for STT configuration |
| REST | `/api/v1/voice/stt/models` | Model management (list, download, delete) |
| WebSocket | `/ws/v1/stt/transcription` | Real-time transcription streaming |
| WebSocket | `/ws/v1/stt/model-download` | Model download progress updates |
| SSE | `/api/v1/voice/stt/status` | Fallback for transcription status |

---

## 2. Functional Requirements

### 2.1 STT Dashboard (F-STT-DASH)

**Route:** `/dashboard/voice/stt`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-DASH-001: Dashboard Overview

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-DASH-001.1 | The system SHALL display STT dashboard at route `/dashboard/voice/stt` | Critical | Test |
| F-STT-DASH-001.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-STT-DASH-001.3 | The system SHALL display current STT engine status (active/inactive) | High | Test |
| F-STT-DASH-001.4 | The system SHALL display currently loaded model name and size | High | Test |
| F-STT-DASH-001.5 | The system SHALL display compute device in use (CPU/CUDA/ROCm) | High | Test |
| F-STT-DASH-001.6 | The system SHALL display GPU memory usage if CUDA active | High | Test |
| F-STT-DASH-001.7 | The system SHALL display transcription statistics (requests/day, avg latency) | High | Test |
| F-STT-DASH-001.8 | The system SHALL update statistics via WebSocket every 5 seconds | High | Test |
| F-STT-DASH-001.9 | The system SHALL provide quick links to: Models, Settings, Test, Logs | Medium | Test |

### 2.2 Engine Selection (F-STT-ENGINE)

**Route:** `/dashboard/voice/stt/engine`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-ENGINE-001: Engine Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-ENGINE-001.1 | The system SHALL allow selection of STT engine: `whisper`, `faster-whisper` | Critical | Test |
| F-STT-ENGINE-001.2 | The system SHALL display engine comparison table (speed, accuracy, memory) | High | Inspection |
| F-STT-ENGINE-001.3 | WHEN `whisper` is selected THEN the system SHALL display OpenAI Whisper settings | High | Test |
| F-STT-ENGINE-001.4 | WHEN `faster-whisper` is selected THEN the system SHALL display CTranslate2 settings | High | Test |
| F-STT-ENGINE-001.5 | The system SHALL validate engine availability before selection | High | Test |
| F-STT-ENGINE-001.6 | The system SHALL require service restart confirmation on engine change | High | Test |
| F-STT-ENGINE-001.7 | The system SHALL emit `stt.engine.changed` WebSocket event on change | High | Test |

#### F-STT-ENGINE-002: Faster-Whisper Specific Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-ENGINE-002.1 | The system SHALL allow compute type selection: `int8`, `int8_float16`, `float16`, `float32` | High | Test |
| F-STT-ENGINE-002.2 | The system SHALL display compute type trade-offs (speed vs accuracy vs memory) | Medium | Inspection |
| F-STT-ENGINE-002.3 | The system SHALL allow device selection: `auto`, `cpu`, `cuda` | High | Test |
| F-STT-ENGINE-002.4 | The system SHALL allow device index selection for multi-GPU systems | Medium | Test |
| F-STT-ENGINE-002.5 | The system SHALL allow CPU threads configuration (1-32) | Medium | Test |
| F-STT-ENGINE-002.6 | The system SHALL allow num_workers configuration (1-8) | Medium | Test |
| F-STT-ENGINE-002.7 | The system SHALL display estimated memory usage based on settings | High | Test |

### 2.3 Model Management (F-STT-MODELS)

**Route:** `/dashboard/voice/stt/models`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-MODELS-001: Model List

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-MODELS-001.1 | The system SHALL display available Whisper models in table | Critical | Test |
| F-STT-MODELS-001.2 | The system SHALL display for each model: Name, Size, Parameters, Languages, Status | High | Test |
| F-STT-MODELS-001.3 | The system SHALL indicate downloaded models with checkmark | High | Test |
| F-STT-MODELS-001.4 | The system SHALL indicate currently active model with highlight | High | Test |
| F-STT-MODELS-001.5 | The system SHALL display disk space used by each downloaded model | High | Test |
| F-STT-MODELS-001.6 | The system SHALL display total available disk space | High | Test |

#### F-STT-MODELS-002: Model Details

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-MODELS-002.1 | The system SHALL support models: `tiny`, `tiny.en`, `base`, `base.en`, `small`, `small.en`, `medium`, `medium.en`, `large`, `large-v2`, `large-v3` | Critical | Inspection |
| F-STT-MODELS-002.2 | The system SHALL display model specifications table | High | Inspection |

**Model Specifications:**

| Model | Parameters | English-only | Multilingual | VRAM | Relative Speed |
|-------|------------|--------------|--------------|------|----------------|
| tiny | 39M | tiny.en | tiny | ~1GB | ~32x |
| base | 74M | base.en | base | ~1GB | ~16x |
| small | 244M | small.en | small | ~2GB | ~6x |
| medium | 769M | medium.en | medium | ~5GB | ~2x |
| large | 1550M | N/A | large | ~10GB | 1x |
| large-v2 | 1550M | N/A | large-v2 | ~10GB | 1x |
| large-v3 | 1550M | N/A | large-v3 | ~10GB | 1x |

#### F-STT-MODELS-003: Model Download

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-MODELS-003.1 | The system SHALL provide "Download" button for each non-downloaded model | High | Test |
| F-STT-MODELS-003.2 | The system SHALL display download progress bar | High | Test |
| F-STT-MODELS-003.3 | The system SHALL stream download progress via WebSocket `/ws/v1/stt/model-download` | High | Test |
| F-STT-MODELS-003.4 | The system SHALL display download speed (MB/s) | Medium | Test |
| F-STT-MODELS-003.5 | The system SHALL display estimated time remaining | Medium | Test |
| F-STT-MODELS-003.6 | The system SHALL allow canceling download in progress | High | Test |
| F-STT-MODELS-003.7 | The system SHALL verify model checksum after download | Critical | Test |
| F-STT-MODELS-003.8 | The system SHALL display error message on download failure | High | Test |
| F-STT-MODELS-003.9 | The system SHALL emit `stt.model.downloaded` WebSocket event on completion | High | Test |

#### F-STT-MODELS-004: Model Actions

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-MODELS-004.1 | The system SHALL provide "Activate" action for downloaded models | High | Test |
| F-STT-MODELS-004.2 | The system SHALL provide "Delete" action for downloaded models | High | Test |
| F-STT-MODELS-004.3 | The system SHALL require confirmation for model deletion | High | Test |
| F-STT-MODELS-004.4 | The system SHALL prevent deletion of currently active model | Critical | Test |
| F-STT-MODELS-004.5 | The system SHALL display model loading progress on activation | High | Test |
| F-STT-MODELS-004.6 | The system SHALL emit `stt.model.activated` WebSocket event | High | Test |
| F-STT-MODELS-004.7 | The system SHALL emit `stt.model.deleted` WebSocket event | High | Test |

### 2.4 Language Configuration (F-STT-LANG)

**Route:** `/dashboard/voice/stt/language`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-LANG-001: Language Selection

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-LANG-001.1 | The system SHALL allow language selection from 99 supported languages | Critical | Test |
| F-STT-LANG-001.2 | The system SHALL provide searchable language dropdown | High | Test |
| F-STT-LANG-001.3 | The system SHALL allow "auto" for automatic language detection | High | Test |
| F-STT-LANG-001.4 | The system SHALL display language code and native name | High | Test |
| F-STT-LANG-001.5 | The system SHALL indicate languages with better model support | Medium | Test |
| F-STT-LANG-001.6 | The system SHALL persist language preference per tenant | High | Test |

**Supported Languages (partial list):**

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | es | Spanish |
| fr | French | de | German |
| it | Italian | pt | Portuguese |
| nl | Dutch | pl | Polish |
| ru | Russian | zh | Chinese |
| ja | Japanese | ko | Korean |
| ar | Arabic | hi | Hindi |
| tr | Turkish | vi | Vietnamese |
| th | Thai | id | Indonesian |
| ... | (99 total) | ... | ... |

### 2.5 Transcription Settings (F-STT-TRANS)

**Route:** `/dashboard/voice/stt/settings`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-TRANS-001: Basic Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-TRANS-001.1 | The system SHALL allow task selection: `transcribe`, `translate` | High | Test |
| F-STT-TRANS-001.2 | WHEN task is `translate` THEN the system SHALL translate to English | High | Test |
| F-STT-TRANS-001.3 | The system SHALL allow word timestamps toggle (on/off) | High | Test |
| F-STT-TRANS-001.4 | The system SHALL allow initial prompt configuration (max 224 tokens) | High | Test |
| F-STT-TRANS-001.5 | The system SHALL provide initial prompt templates | Medium | Test |
| F-STT-TRANS-001.6 | The system SHALL allow condition on previous text toggle | Medium | Test |

#### F-STT-TRANS-002: Advanced Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-TRANS-002.1 | The system SHALL allow temperature configuration (0.0 - 1.0, default 0.0) | High | Test |
| F-STT-TRANS-002.2 | The system SHALL allow temperature increment for fallback (0.0 - 0.5) | Medium | Test |
| F-STT-TRANS-002.3 | The system SHALL allow beam size configuration (1-10, default 5) | High | Test |
| F-STT-TRANS-002.4 | The system SHALL allow best_of configuration (1-10, default 5) | Medium | Test |
| F-STT-TRANS-002.5 | The system SHALL allow patience configuration (0.0 - 2.0, default 1.0) | Medium | Test |
| F-STT-TRANS-002.6 | The system SHALL allow length penalty configuration (-2.0 - 2.0) | Medium | Test |
| F-STT-TRANS-002.7 | The system SHALL allow compression ratio threshold (0.0 - 10.0, default 2.4) | Medium | Test |
| F-STT-TRANS-002.8 | The system SHALL allow log probability threshold (-10.0 - 0.0, default -1.0) | Medium | Test |
| F-STT-TRANS-002.9 | The system SHALL allow no speech threshold (0.0 - 1.0, default 0.6) | Medium | Test |
| F-STT-TRANS-002.10 | The system SHALL provide "Reset to Defaults" button | High | Test |
| F-STT-TRANS-002.11 | The system SHALL display setting descriptions on hover/focus | High | Test |

### 2.6 VAD Configuration (F-STT-VAD)

**Route:** `/dashboard/voice/stt/vad`  
**Access:** ADMIN, DEVELOPER  

#### F-STT-VAD-001: VAD Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-VAD-001.1 | The system SHALL allow VAD filter toggle (on/off) | High | Test |
| F-STT-VAD-001.2 | The system SHALL allow VAD method selection: `silero`, `webrtc`, `both` | High | Test |
| F-STT-VAD-001.3 | The system SHALL allow VAD threshold configuration (0.0 - 1.0) | High | Test |
| F-STT-VAD-001.4 | The system SHALL allow min silence duration (ms) configuration | High | Test |
| F-STT-VAD-001.5 | The system SHALL allow min speech duration (ms) configuration | High | Test |
| F-STT-VAD-001.6 | The system SHALL allow speech pad (ms) configuration | Medium | Test |
| F-STT-VAD-001.7 | The system SHALL display VAD visualization during test | High | Test |

### 2.7 Real-Time Test (F-STT-TEST)

**Route:** `/dashboard/voice/stt/test`  
**Access:** ADMIN, DEVELOPER, OPERATOR  

#### F-STT-TEST-001: Transcription Test Interface

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-TEST-001.1 | The system SHALL provide microphone input for live testing | Critical | Test |
| F-STT-TEST-001.2 | The system SHALL provide file upload for audio testing | High | Test |
| F-STT-TEST-001.3 | The system SHALL accept audio formats: WAV, MP3, FLAC, OGG, M4A | High | Test |
| F-STT-TEST-001.4 | The system SHALL display real-time transcription via WebSocket | Critical | Test |
| F-STT-TEST-001.5 | The system SHALL connect to `/ws/v1/stt/transcription` for streaming | Critical | Test |
| F-STT-TEST-001.6 | The system SHALL display word-level timestamps if enabled | High | Test |
| F-STT-TEST-001.7 | The system SHALL display confidence scores per segment | High | Test |
| F-STT-TEST-001.8 | The system SHALL display processing latency | High | Test |
| F-STT-TEST-001.9 | The system SHALL display detected language if auto-detect enabled | High | Test |
| F-STT-TEST-001.10 | The system SHALL provide "Copy Transcript" button | Medium | Test |
| F-STT-TEST-001.11 | The system SHALL provide "Download Transcript" (TXT, SRT, VTT) | Medium | Test |

#### F-STT-TEST-002: Audio Visualization

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-STT-TEST-002.1 | The system SHALL display audio waveform during recording | High | Test |
| F-STT-TEST-002.2 | The system SHALL display audio level meter | High | Test |
| F-STT-TEST-002.3 | The system SHALL highlight VAD-detected speech regions | High | Test |
| F-STT-TEST-002.4 | The system SHALL display spectrogram visualization (optional) | Medium | Test |

---

## 3. WebSocket Events

### 3.1 STT WebSocket Protocol

**Endpoint:** `/ws/v1/stt/transcription`

#### Client → Server Messages

```typescript
// Start transcription session
{
  "type": "stt.session.start",
  "config": {
    "language": "en",
    "task": "transcribe",
    "word_timestamps": true,
    "vad_filter": true
  }
}

// Send audio chunk (base64 PCM16 24kHz)
{
  "type": "stt.audio.chunk",
  "audio": "base64_encoded_audio_data"
}

// End transcription session
{
  "type": "stt.session.end"
}
```

#### Server → Client Messages

```typescript
// Transcription segment (partial)
{
  "type": "stt.transcription.partial",
  "text": "Hello world",
  "is_final": false
}

// Transcription segment (final)
{
  "type": "stt.transcription.final",
  "text": "Hello world, how are you?",
  "segments": [
    {
      "start": 0.0,
      "end": 1.5,
      "text": "Hello world,",
      "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.98},
        {"word": "world,", "start": 0.6, "end": 1.0, "probability": 0.95}
      ]
    }
  ],
  "language": "en",
  "language_probability": 0.99
}

// VAD event
{
  "type": "stt.vad.speech_start"
}

{
  "type": "stt.vad.speech_end"
}

// Error
{
  "type": "stt.error",
  "code": "MODEL_NOT_LOADED",
  "message": "No STT model is currently loaded"
}
```

### 3.2 Model Download WebSocket Protocol

**Endpoint:** `/ws/v1/stt/model-download`

```typescript
// Download progress
{
  "type": "stt.model.download.progress",
  "model": "large-v3",
  "downloaded_bytes": 1073741824,
  "total_bytes": 3221225472,
  "percent": 33.3,
  "speed_mbps": 45.2,
  "eta_seconds": 48
}

// Download complete
{
  "type": "stt.model.download.complete",
  "model": "large-v3",
  "checksum_valid": true
}

// Download error
{
  "type": "stt.model.download.error",
  "model": "large-v3",
  "error": "Network timeout"
}
```

---

## 4. Data Models

### 4.1 STT Configuration Schema

```typescript
interface STTConfig {
  engine: 'whisper' | 'faster-whisper';
  model: string;
  language: string | 'auto';
  task: 'transcribe' | 'translate';
  
  // Compute settings
  device: 'auto' | 'cpu' | 'cuda';
  device_index: number;
  compute_type: 'int8' | 'int8_float16' | 'float16' | 'float32';
  cpu_threads: number;
  num_workers: number;
  
  // Transcription settings
  word_timestamps: boolean;
  initial_prompt: string | null;
  condition_on_previous_text: boolean;
  
  // Decoding settings
  temperature: number;
  temperature_increment_on_fallback: number;
  beam_size: number;
  best_of: number;
  patience: number;
  length_penalty: number;
  
  // Thresholds
  compression_ratio_threshold: number;
  log_prob_threshold: number;
  no_speech_threshold: number;
  
  // VAD settings
  vad_filter: boolean;
  vad_method: 'silero' | 'webrtc' | 'both';
  vad_threshold: number;
  min_silence_duration_ms: number;
  min_speech_duration_ms: number;
  speech_pad_ms: number;
}
```

### 4.2 STT Model Schema

```typescript
interface STTModel {
  name: string;
  size: string;
  parameters: string;
  multilingual: boolean;
  english_only: boolean;
  vram_required: string;
  relative_speed: string;
  downloaded: boolean;
  active: boolean;
  disk_size_bytes: number;
  download_url: string;
  checksum: string;
}
```

---

## 5. UI Wireframes

### 5.1 STT Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STT Configuration                                              [?] [Save]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Status: ● Active    Engine: faster-whisper    Model: large-v3      │   │
│  │  Device: CUDA (RTX 4090)    VRAM: 8.2GB / 24GB    Latency: 0.3s    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Models     │ │   Settings   │ │     VAD      │ │     Test     │      │
│  │   [5/11]     │ │   [Config]   │ │   [Silero]   │ │   [Live]     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Today's Statistics                                    [Refresh]    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │ Requests    │ │ Avg Latency │ │ Total Audio │ │ Errors      │   │   │
│  │  │   1,234     │ │   0.32s     │ │   4.2 hrs   │ │   12        │   │   │
│  │  │   +15%      │ │   -8%       │ │   +22%      │ │   -50%      │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Model Management Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STT Models                                          Disk: 12.4GB / 100GB   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Model      │ Size   │ Params │ VRAM  │ Speed │ Status    │ Actions │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ tiny       │ 75MB   │ 39M    │ ~1GB  │ ~32x  │ ✓ Ready   │ [Act]   │   │
│  │ base       │ 145MB  │ 74M    │ ~1GB  │ ~16x  │ ✓ Ready   │ [Act]   │   │
│  │ small      │ 488MB  │ 244M   │ ~2GB  │ ~6x   │ ✓ Ready   │ [Act]   │   │
│  │ medium     │ 1.5GB  │ 769M   │ ~5GB  │ ~2x   │ ○ Not DL  │ [DL]    │   │
│  │ large-v3   │ 3.1GB  │ 1550M  │ ~10GB │ 1x    │ ★ Active  │ [Del]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Downloading: medium                                                │   │
│  │  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  45%              │   │
│  │  675MB / 1.5GB    Speed: 42.3 MB/s    ETA: 20s         [Cancel]    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling

| Error Code | Description | User Message | Recovery Action |
|------------|-------------|--------------|-----------------|
| STT_001 | Model not loaded | "No STT model is loaded. Please activate a model." | Link to model management |
| STT_002 | CUDA out of memory | "GPU memory insufficient. Try a smaller model or CPU mode." | Suggest smaller model |
| STT_003 | Audio format unsupported | "Audio format not supported. Use WAV, MP3, FLAC, OGG, or M4A." | Show supported formats |
| STT_004 | Model download failed | "Failed to download model. Check network connection." | Retry button |
| STT_005 | Checksum mismatch | "Model file corrupted. Please re-download." | Auto-delete and retry |
| STT_006 | Language not supported | "Selected language not supported by this model." | Suggest compatible model |
| STT_007 | VAD initialization failed | "Voice activity detection failed to initialize." | Disable VAD option |

---

## 7. RBAC Permissions

| Action | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|----------|-------|-----------|----------|--------|---------|
| View STT Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Change Engine | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Download Models | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Delete Models | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Activate Models | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Edit Settings | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Run Tests | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| View Statistics | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
