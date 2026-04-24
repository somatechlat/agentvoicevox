import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ovosApi } from '../services/voice-api';

@customElement('view-settings')
export class ViewSettings extends LitElement {
  @state() private config: Record<string, any> = {};
  @state() private plugins: { tts: string[]; stt: string[] } = { tts: [], stt: [] };
  @state() private loading = true;
  @state() private showRawJson = false;
  @state() private rawJsonText = '';
  @state() private saveStatus: 'idle' | 'saving' | 'success' | 'error' = 'idle';

  static styles = css`
    :host {
      display: block;
      padding: 2rem;
      font-family: 'Inter', sans-serif;
      color: #333;
      background: #f8fafc;
      min-height: 100vh;
    }

    .header {
      margin-bottom: 2rem;
    }

    h1 {
      font-size: 2.5rem;
      margin: 0;
      color: #0f172a;
      font-weight: 800;
      letter-spacing: -0.025em;
    }

    p.subtitle {
      color: #64748b;
      font-size: 1.1rem;
      margin-top: 0.5rem;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.7);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.5);
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
      margin-bottom: 2rem;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .glass-card:hover {
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
    }

    h2 {
      font-size: 1.5rem;
      margin-top: 0;
      margin-bottom: 1.5rem;
      color: #1e293b;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 0.5rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    label {
      display: block;
      font-size: 0.95rem;
      font-weight: 600;
      color: #475569;
      margin-bottom: 0.5rem;
    }

    select, input[type="text"], input[type="number"], textarea {
      width: 100%;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      background: rgba(255, 255, 255, 0.9);
      font-size: 1rem;
      color: #334155;
      font-family: inherit;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-sizing: border-box;
    }

    select:focus, input:focus, textarea:focus {
      outline: none;
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    .toggle-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.5rem;
      padding: 1rem;
      background: rgba(241, 245, 249, 0.5);
      border-radius: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.75rem 1.5rem;
      font-weight: 600;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
      font-family: inherit;
      font-size: 1rem;
    }

    .btn-primary {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: white;
      box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 8px -1px rgba(99, 102, 241, 0.4);
    }

    .btn-secondary {
      background: #e2e8f0;
      color: #475569;
    }

    .btn-secondary:hover {
      background: #cbd5e1;
    }

    .flex-row {
      display: flex;
      gap: 1rem;
    }
    
    .flex-1 {
      flex: 1;
    }

    .spinner {
      display: inline-block;
      width: 40px;
      height: 40px;
      border: 4px solid rgba(99, 102, 241, 0.2);
      border-radius: 50%;
      border-top-color: #6366f1;
      animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .status-msg {
      margin-left: 1rem;
      font-weight: 600;
    }

    .success { color: #10b981; }
    .error { color: #ef4444; }
  `;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadData();
  }

  async loadData() {
    this.loading = true;
    try {
      const [configRes, pluginsRes] = await Promise.all([
        ovosApi.getConfig(),
        ovosApi.getPlugins()
      ]);
      
      if (configRes.data) {
        this.config = configRes.data;
        this.rawJsonText = JSON.stringify(this.config, null, 2);
      }
      if (pluginsRes.data) {
        this.plugins = pluginsRes.data;
      }
    } catch (e) {
      console.error('Failed to load OVOS configuration', e);
    } finally {
      this.loading = false;
    }
  }

  handleInputChange(e: Event, section: string, key: string) {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const val = target.type === 'number' ? Number(target.value) : target.value;
    
    if (!this.config[section]) {
      this.config[section] = {};
    }
    this.config[section][key] = val;
    this.requestUpdate();
  }

  handleJsonChange(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    this.rawJsonText = target.value;
  }

  async saveConfig() {
    this.saveStatus = 'saving';
    try {
      let patchPayload = this.config;
      
      if (this.showRawJson) {
        patchPayload = JSON.parse(this.rawJsonText);
        this.config = patchPayload;
      }
      
      await ovosApi.updateConfig(patchPayload);
      this.saveStatus = 'success';
      setTimeout(() => this.saveStatus = 'idle', 3000);
    } catch (e) {
      console.error('Save failed', e);
      this.saveStatus = 'error';
    }
  }

  renderForm() {
    const ttsModule = this.config?.tts?.module || 'default';
    const sttModule = this.config?.stt?.module || 'default';
    const lang = this.config?.lang || 'en-us';
    const log_level = this.config?.log_level || 'INFO';
    const listenerEnergy = this.config?.listener?.energy_ratio || 1.5;

    return html`
      <div class="flex-row">
        <div class="glass-card flex-1">
          <h2>Core Intelligence</h2>
          <div class="form-group">
            <label>Primary Language</label>
            <input type="text" .value="${lang}" @change="${(e: Event) => { this.config.lang = (e.target as HTMLInputElement).value; this.requestUpdate(); }}" placeholder="en-us">
          </div>
          
          <div class="form-group">
            <label>Text-to-Speech (TTS) Engine</label>
            <select @change="${(e: Event) => this.handleInputChange(e, 'tts', 'module')}">
              ${this.plugins.tts.map(p => html`<option value="${p}" ?selected="${p === ttsModule}">${p}</option>`)}
              ${!this.plugins.tts.includes(ttsModule) ? html`<option value="${ttsModule}" selected>${ttsModule}</option>` : ''}
            </select>
          </div>

          <div class="form-group">
            <label>Speech-to-Text (STT) Engine</label>
            <select @change="${(e: Event) => this.handleInputChange(e, 'stt', 'module')}">
              ${this.plugins.stt.map(p => html`<option value="${p}" ?selected="${p === sttModule}">${p}</option>`)}
              ${!this.plugins.stt.includes(sttModule) ? html`<option value="${sttModule}" selected>${sttModule}</option>` : ''}
            </select>
          </div>
        </div>

        <div class="glass-card flex-1">
          <h2>Listener & Audio (VAD)</h2>
          <div class="form-group">
            <label>Energy Ratio Threshold</label>
            <input type="number" step="0.1" .value="${listenerEnergy}" @change="${(e: Event) => this.handleInputChange(e, 'listener', 'energy_ratio')}">
            <p style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">Adjusts Voice Activity Detection sensitivity. Higher = less sensitive.</p>
          </div>
          
          <div class="form-group">
            <label>System Log Level</label>
            <select @change="${(e: Event) => { this.config.log_level = (e.target as HTMLSelectElement).value; this.requestUpdate(); }}">
              <option value="DEBUG" ?selected="${log_level === 'DEBUG'}">DEBUG</option>
              <option value="INFO" ?selected="${log_level === 'INFO'}">INFO</option>
              <option value="WARNING" ?selected="${log_level === 'WARNING'}">WARNING</option>
              <option value="ERROR" ?selected="${log_level === 'ERROR'}">ERROR</option>
            </select>
          </div>
        </div>
      </div>
    `;
  }

  renderRawJson() {
    return html`
      <div class="glass-card">
        <h2>Raw Configuration (mycroft.conf)</h2>
        <textarea rows="20" style="font-family: monospace; font-size: 0.9rem;" @change="${this.handleJsonChange}">${this.rawJsonText}</textarea>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div style="display:flex; justify-content:center; align-items:center; height: 50vh;">
          <div class="spinner"></div>
        </div>
      `;
    }

    return html`
      <div class="header">
        <h1>OVOS Configuration</h1>
        <p class="subtitle">Directly manage the OpenVoiceOS cognitive core parameters.</p>
      </div>

      <div class="toggle-container">
        <span style="font-weight: 600; color: #334155;">Advanced Mode (Raw JSON)</span>
        <button class="btn btn-secondary" @click="${() => this.showRawJson = !this.showRawJson}">
          ${this.showRawJson ? 'Switch to UI Forms' : 'Edit Raw JSON'}
        </button>
      </div>

      ${this.showRawJson ? this.renderRawJson() : this.renderForm()}

      <div style="display: flex; align-items: center; margin-bottom: 3rem;">
        <button class="btn btn-primary" @click="${this.saveConfig}" ?disabled="${this.saveStatus === 'saving'}">
          ${this.saveStatus === 'saving' ? 'Applying...' : 'Apply Configuration to Node'}
        </button>
        ${this.saveStatus === 'success' ? html`<span class="status-msg success">✓ Live patched successfully!</span>` : ''}
        ${this.saveStatus === 'error' ? html`<span class="status-msg error">✗ Failed to patch config.</span>` : ''}
      </div>
    `;
  }
}
