import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { sessionsApi } from '../services/voice-api';

@customElement('view-voice-playground')
export class ViewVoicePlayground extends LitElement {
  @state() private active = false;
  @state() private transcription = '';
  @state() private responseText = '';
  @state() private volume = 0;
  @state() private status: 'idle' | 'connecting' | 'listening' | 'speaking' | 'error' = 'idle';

  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private microStream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;

  static styles = css`
    :host {
      display: block;
      padding: 2rem;
      color: white;
      font-family: 'Inter', sans-serif;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      padding: 3rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      text-align: center;
    }

    h1 {
      font-size: 2.5rem;
      margin-bottom: 0.5rem;
      background: linear-gradient(135deg, #fff 0%, #aaa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .orb-container {
      position: relative;
      width: 200px;
      height: 200px;
      margin: 4rem auto;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .orb {
      width: 120px;
      height: 120px;
      border-radius: 50%;
      background: radial-gradient(circle at 30% 30%, #4f46e5, #0ea5e9);
      box-shadow: 0 0 50px rgba(14, 165, 233, 0.5);
      transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2;
    }

    .orb:hover {
      transform: scale(1.05);
      box-shadow: 0 0 70px rgba(14, 165, 233, 0.8);
    }

    .orb.active {
      animation: pulse 2s infinite;
    }

    .orb.speaking {
      background: radial-gradient(circle at 30% 30%, #ec4899, #8b5cf6);
      box-shadow: 0 0 50px rgba(236, 72, 153, 0.5);
    }

    @keyframes pulse {
      0% { transform: scale(1); box-shadow: 0 0 50px rgba(14, 165, 233, 0.5); }
      50% { transform: scale(1.1); box-shadow: 0 0 100px rgba(14, 165, 233, 0.8); }
      100% { transform: scale(1); box-shadow: 0 0 50px rgba(14, 165, 233, 0.5); }
    }

    .visualizer {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      border: 2px solid rgba(255, 255, 255, 0.1);
      transition: transform 0.1s ease-out;
    }

    .transcript-container {
      margin-top: 3rem;
      text-align: left;
      min-height: 150px;
    }

    .label {
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: rgba(255, 255, 255, 0.4);
      margin-bottom: 0.5rem;
    }

    .text-box {
      font-size: 1.25rem;
      line-height: 1.6;
      color: rgba(255, 255, 255, 0.9);
      min-height: 1.6em;
    }

    .status-badge {
      display: inline-block;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 2rem;
    }

    .status-idle { background: rgba(255, 255, 255, 0.1); color: #aaa; }
    .status-connecting { background: rgba(234, 179, 8, 0.2); color: #facc15; }
    .status-listening { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
    .status-speaking { background: rgba(236, 72, 153, 0.2); color: #f472b6; }
    .status-error { background: rgba(239, 68, 68, 0.2); color: #f87171; }

    button.primary {
      background: white;
      color: black;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    button.primary:hover {
      background: #eee;
      transform: translateY(-2px);
    }
  `;

  render() {
    return html`
      <div class="container">
        <h1>Voice Playground</h1>
        
        <div class="status-badge status-${this.status}">
          ${this.status.toUpperCase()}
        </div>

        <div class="orb-container">
          <div 
            class="visualizer" 
            style="transform: scale(${1 + (this.volume / 100)})"
          ></div>
          <div 
            class="orb ${this.status === 'listening' ? 'active' : ''} ${this.status === 'speaking' ? 'speaking' : ''}"
            @click=${this.toggleSession}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              ${this.active 
                ? html`<rect x="6" y="6" width="12" height="12"></rect>`
                : html`<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line>`
              }
            </svg>
          </div>
        </div>

        <div class="transcript-container">
          <div class="label">You said</div>
          <div class="text-box">${this.transcription || '...'}</div>
          
          <div style="margin-top: 2rem;"></div>
          
          <div class="label">Agent response</div>
          <div class="text-box">${this.responseText || '...'}</div>
        </div>

        <div style="margin-top: 3rem;">
          ${!this.active ? html`
            <button class="primary" @click=${this.toggleSession}>Start Realtime Session</button>
          ` : html`
            <button class="primary" style="background: rgba(239, 68, 68, 0.1); color: #f87171;" @click=${this.toggleSession}>End Session</button>
          `}
        </div>
      </div>
    `;
  }

  async toggleSession() {
    if (this.active) {
      this.stopSession();
    } else {
      await this.startSession();
    }
  }

  async startSession() {
    this.status = 'connecting';
    try {
      // 1. Create a session on the backend
      const sessionRes = await sessionsApi.create({
        model: 'gpt-4o-realtime-preview',
        instructions: 'You are a helpful assistant from AgentVoiceBox.'
      });
      
      if (!sessionRes.data) throw new Error('Failed to create session');
      const session = sessionRes.data;

      // 2. Get client secret (standard OpenAI-like flow)
      const tokenRes = await sessionsApi.createClientSecret({
        session: { id: session.id }
      });
      
      if (!tokenRes.data) throw new Error('Failed to get token');
      const token = tokenRes.data.value;

      // 3. Connect WebSocket
      const wsUrl = `ws://localhost:65020/ws/v2/sessions/${session.id}?token=${token}`;
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        this.active = true;
        this.status = 'listening';
        this.startMicrophone();
      };
      
      this.ws.onmessage = (e) => {
        const event = JSON.parse(e.data);
        console.log('[WS] Event:', event.type, event);
        this.handleServerEvent(event);
      };

      this.ws.onerror = (e) => {
        console.error('[WS] Error:', e);
        this.status = 'error';
      };

      this.ws.onclose = () => {
        this.active = false;
        this.status = 'idle';
        this.stopMicrophone();
      };

    } catch (err) {
      console.error('Failed to start session:', err);
      this.status = 'error';
    }
  }

  stopSession() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private audioQueue: string[] = [];
  private isPlaying = false;

  handleServerEvent(event: any) {
    switch (event.type) {
      case 'conversation.item.input_audio_transcription.completed':
        this.transcription = event.transcript;
        break;
      case 'response.audio_transcript.delta':
        this.responseText += event.delta;
        this.status = 'speaking';
        break;
      case 'response.audio.delta':
        this.audioQueue.push(event.delta);
        if (!this.isPlaying) {
          this.playNextChunk();
        }
        break;
      case 'response.done':
        if (!this.isPlaying) this.status = 'listening';
        break;
      case 'input_audio_buffer.speech_started':
        this.status = 'listening';
        this.transcription = '';
        this.responseText = '';
        this.audioQueue = []; // Clear any pending speech
        break;
    }
  }

  async playNextChunk() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      if (this.status === 'speaking') this.status = 'listening';
      return;
    }

    this.isPlaying = true;
    const base64 = this.audioQueue.shift()!;
    const arrayBuffer = this.base64ToArrayBuffer(base64);

    try {
      if (!this.audioContext) {
        this.audioContext = new AudioContext({ sampleRate: 16000 });
      }
      
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);
      
      source.onended = () => {
        this.playNextChunk();
      };
      
      source.start();
    } catch (err) {
      console.error('Audio playback error:', err);
      this.playNextChunk();
    }
  }

  private base64ToArrayBuffer(base64: string) {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  async startMicrophone() {
    try {
      this.microStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new AudioContext({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.microStream);
      
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      // Raw PCM processing
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);

      this.processor.onaudioprocess = (e) => {
        if (!this.active || this.status !== 'listening') return;
        
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Visualize volume
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        this.volume = Math.sqrt(sum / inputData.length) * 100;

        // Convert to PCM16
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcm16[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
        }

        // Send to backend
        const base64 = this.arrayBufferToBase64(pcm16.buffer);
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: base64
          }));
        }
      };

    } catch (err) {
      console.error('Microphone error:', err);
    }
  }

  stopMicrophone() {
    if (this.microStream) {
      this.microStream.getTracks().forEach(t => t.stop());
      this.microStream = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    this.volume = 0;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }
}
