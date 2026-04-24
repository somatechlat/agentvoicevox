import { LitElement, html, css } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';
import { customVoicesApi, CustomVoice } from '../services/voice-api';

@customElement('view-voice-cloning')
export class ViewVoiceCloning extends LitElement {
  @state() private voices: CustomVoice[] = [];
  @state() private loading = true;
  @state() private isUploading = false;
  
  @query('#audioFile') audioFileInput!: HTMLInputElement;
  @query('#voiceName') voiceNameInput!: HTMLInputElement;
  @query('#voiceLang') voiceLangInput!: HTMLSelectElement;

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
      background: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.5);
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
      margin-bottom: 2rem;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.5rem;
    }

    .voice-card {
      background: white;
      border-radius: 12px;
      padding: 1.5rem;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
      transition: transform 0.2s, box-shadow 0.2s;
      position: relative;
    }

    .voice-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .voice-card.default-voice {
      border-color: #10b981;
      background: #f0fdf4;
    }

    .badge {
      position: absolute;
      top: 1rem;
      right: 1rem;
      padding: 0.25rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
    }

    .badge-processing { background: #fef3c7; color: #d97706; }
    .badge-ready { background: #d1fae5; color: #059669; }
    .badge-failed { background: #fee2e2; color: #dc2626; }
    
    .default-badge {
      position: absolute;
      bottom: 1rem;
      right: 1rem;
      color: #10b981;
      font-weight: bold;
      font-size: 0.85rem;
    }

    h3 {
      margin-top: 0;
      margin-bottom: 0.5rem;
      color: #1e293b;
      font-size: 1.25rem;
    }

    .voice-details {
      font-size: 0.85rem;
      color: #64748b;
      margin-bottom: 1rem;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.5rem 1rem;
      font-weight: 600;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      transition: background 0.2s;
      font-size: 0.85rem;
      text-decoration: none;
    }

    .btn-primary { background: #4f46e5; color: white; }
    .btn-primary:hover { background: #4338ca; }
    .btn-danger { background: #ef4444; color: white; }
    .btn-danger:hover { background: #dc2626; }
    .btn-outline { background: transparent; border: 1px solid #cbd5e1; color: #475569; }
    .btn-outline:hover { background: #f1f5f9; }

    .actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    /* Form styles */
    .form-group {
      margin-bottom: 1rem;
    }
    label {
      display: block;
      font-weight: 600;
      margin-bottom: 0.25rem;
      color: #475569;
    }
    input[type="text"], select, input[type="file"] {
      width: 100%;
      padding: 0.75rem;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      box-sizing: border-box;
      font-family: inherit;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadVoices();
  }

  async loadVoices() {
    this.loading = true;
    try {
      const res = await customVoicesApi.list();
      this.voices = res.data || [];
    } catch (e) {
      console.error('Failed to load custom voices', e);
    } finally {
      this.loading = false;
    }
  }

  async handleUpload(e: Event) {
    e.preventDefault();
    if (!this.audioFileInput.files || this.audioFileInput.files.length === 0) {
      alert("Please select an audio file.");
      return;
    }

    const file = this.audioFileInput.files[0];
    const name = this.voiceNameInput.value.trim();
    const lang = this.voiceLangInput.value;

    if (!name) {
      alert("Please enter a voice name.");
      return;
    }

    this.isUploading = true;
    try {
      const formData = new FormData();
      formData.append('audio', file);
      formData.append('name', name);
      formData.append('language', lang);
      formData.append('quality', 'balanced');

      await customVoicesApi.create(formData);
      
      // Reset form
      this.voiceNameInput.value = '';
      this.audioFileInput.value = '';
      
      // Reload voices
      await this.loadVoices();
    } catch (err) {
      console.error('Upload failed', err);
      alert('Failed to initiate voice cloning process.');
    } finally {
      this.isUploading = false;
    }
  }

  async handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this custom voice?')) return;
    try {
      await customVoicesApi.delete(id);
      await this.loadVoices();
    } catch (err) {
      console.error('Failed to delete voice', err);
    }
  }

  async handleSetDefault(id: string) {
    try {
      await customVoicesApi.setDefault(id);
      await this.loadVoices();
    } catch (err) {
      console.error('Failed to set default', err);
    }
  }

  render() {
    return html`
      <div class="header">
        <h1>Voice Cloning Library</h1>
        <p class="subtitle">Upload high-quality audio samples to clone voices for your agents.</p>
      </div>

      <div class="glass-card">
        <h2>Clone a New Voice</h2>
        <form @submit="${this.handleUpload}" style="display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap;">
          <div class="form-group" style="flex: 1; min-width: 200px;">
            <label>Voice Name</label>
            <input type="text" id="voiceName" placeholder="e.g., Marketing CEO Voice" required>
          </div>
          <div class="form-group" style="flex: 1; min-width: 150px;">
            <label>Language</label>
            <select id="voiceLang">
              <option value="en">English (en)</option>
              <option value="es">Spanish (es)</option>
              <option value="fr">French (fr)</option>
            </select>
          </div>
          <div class="form-group" style="flex: 2; min-width: 250px;">
            <label>Audio Sample (WAV/MP3)</label>
            <input type="file" id="audioFile" accept="audio/wav,audio/mpeg" required>
          </div>
          <div class="form-group">
            <button type="submit" class="btn btn-primary" style="padding: 0.75rem 1.5rem;" ?disabled="${this.isUploading}">
              ${this.isUploading ? 'Uploading...' : 'Start Cloning Process'}
            </button>
          </div>
        </form>
      </div>

      <div class="grid">
        ${this.loading ? html`<p>Loading voices...</p>` : 
          this.voices.length === 0 ? html`<p style="color: #64748b;">No cloned voices found. Upload an audio sample to get started.</p>` :
          this.voices.map(voice => html`
            <div class="voice-card ${voice.is_default ? 'default-voice' : ''}">
              <span class="badge badge-${voice.status}">${voice.status}</span>
              <h3>${voice.name}</h3>
              <div class="voice-details">
                <div>Language: <strong>${voice.language}</strong></div>
                <div>Created: ${new Date(voice.created_at).toLocaleDateString()}</div>
                ${voice.sample_duration_seconds ? html`<div>Duration: ${voice.sample_duration_seconds.toFixed(1)}s</div>` : ''}
              </div>
              
              ${voice.is_default ? html`<div class="default-badge">★ Default</div>` : ''}
              
              <div class="actions">
                ${voice.sample_url ? html`
                  <a href="${voice.sample_url}" target="_blank" class="btn btn-outline" download>Download Sample</a>
                ` : ''}
                ${!voice.is_default && voice.status === 'ready' ? html`
                  <button class="btn btn-primary" @click="${() => this.handleSetDefault(voice.id)}">Set Default</button>
                ` : ''}
                <button class="btn btn-danger" @click="${() => this.handleDelete(voice.id)}">Delete</button>
              </div>
              ${voice.error_message ? html`<div style="color:red; font-size:0.8rem; margin-top:0.5rem;">Error: ${voice.error_message}</div>` : ''}
            </div>
          `)
        }
      </div>
    `;
  }
}
