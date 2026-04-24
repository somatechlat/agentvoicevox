import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ovosApi } from '../services/voice-api';
import { t, setLanguage, getCurrentLanguage, onLanguageChange, SupportedLanguage } from '../utils/i18n';

@customElement('view-settings')
export class ViewSettings extends LitElement {
  @state() private config: Record<string, any> = {};
  @state() private plugins: { tts: string[]; stt: string[] } = { tts: [], stt: [] };
  @state() private loading = true;
  @state() private showRawJson = false;
  @state() private rawJsonText = '';
  @state() private saveStatus: 'idle' | 'saving' | 'success' | 'error' = 'idle';

  private unsubscribeI18n!: () => void;

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
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
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

    .lang-switcher select {
      padding: 0.5rem;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      font-weight: 600;
      background: white;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.7);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.5);
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
      margin-bottom: 2rem;
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
      display: inline-block;
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
      box-sizing: border-box;
    }

    select:focus, input:focus, textarea:focus {
      outline: none;
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    
    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .checkbox-group input {
      width: auto;
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
      font-family: inherit;
    }

    .btn-primary {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: white;
    }
    .btn-primary:hover { background: #4338ca; }
    .btn-secondary { background: #e2e8f0; color: #475569; }
    .btn-secondary:hover { background: #cbd5e1; }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    .spinner {
      width: 40px; height: 40px;
      border: 4px solid rgba(99,102,241,0.2);
      border-radius: 50%;
      border-top-color: #6366f1;
      animation: spin 1s infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .status-msg { margin-left: 1rem; font-weight: 600; }
    .success { color: #10b981; }
    .error { color: #ef4444; }
  `;

  async connectedCallback() {
    super.connectedCallback();
    this.unsubscribeI18n = onLanguageChange(() => this.requestUpdate());
    await this.loadData();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.unsubscribeI18n) this.unsubscribeI18n();
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
      console.error('Failed to load configuration', e);
    } finally {
      this.loading = false;
    }
  }

  handleInputChange(e: Event, section: string, key: string, type: string = 'text') {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    let val: any = target.value;
    if (type === 'number') val = Number(target.value);
    if (type === 'checkbox') val = (target as HTMLInputElement).checked;
    if (type === 'list') val = target.value.split(',').map(s => s.trim()).filter(Boolean);
    
    if (!this.config[section]) this.config[section] = {};
    this.config[section][key] = val;
    this.requestUpdate();
  }
  
  handleNestedChange(e: Event, section: string, subSection: string, key: string) {
    const target = e.target as HTMLInputElement;
    if (!this.config[section]) this.config[section] = {};
    if (!this.config[section][subSection]) this.config[section][subSection] = {};
    this.config[section][subSection][key] = target.value;
    this.requestUpdate();
  }

  handleJsonChange(e: Event) {
    this.rawJsonText = (e.target as HTMLTextAreaElement).value;
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
      this.saveStatus = 'error';
    }
  }

  changeLang(e: Event) {
    setLanguage((e.target as HTMLSelectElement).value as SupportedLanguage);
  }

  renderForm() {
    const ttsModule = this.config?.tts?.module || 'default';
    const sttModule = this.config?.stt?.module || 'default';
    const lang = this.config?.lang || 'en-us';
    const log_level = this.config?.log_level || 'INFO';
    const listenerEnergy = this.config?.listener?.energy_ratio || 1.5;
    const blacklistedSkills = (this.config?.skills?.blacklisted_skills || []).join(', ');
    const prioritySkills = (this.config?.skills?.priority_skills || []).join(', ');
    const autoUpdate = this.config?.skills?.auto_update ?? true;
    const city = this.config?.location?.city?.name || 'LocalCity';
    const timezone = this.config?.location?.timezone?.code || 'UTC';
    const idleScreen = this.config?.gui?.idle_display_skill || '';

    return html`
      <div class="grid-2">
        <!-- Core & Audio -->
        <div class="glass-card">
          <h2>${t('settings.core')}</h2>
          
          <div class="form-group">
            <label>${t('settings.lang')}</label>
            <ui-tooltip text="${t('tooltip.lang')}"></ui-tooltip>
            <input type="text" .value="${lang}" @change="${(e: Event) => { this.config.lang = (e.target as HTMLInputElement).value; this.requestUpdate(); }}">
          </div>
          
          <div class="form-group">
            <label>${t('settings.log_level')}</label>
            <ui-tooltip text="${t('tooltip.log_level')}"></ui-tooltip>
            <select @change="${(e: Event) => { this.config.log_level = (e.target as HTMLSelectElement).value; this.requestUpdate(); }}">
              ${['DEBUG', 'INFO', 'WARNING', 'ERROR'].map(l => html`<option value="${l}" ?selected="${log_level === l}">${l}</option>`)}
            </select>
          </div>

          <h2 style="margin-top:2rem;">${t('settings.vad')}</h2>
          <div class="form-group">
            <label>${t('settings.tts')}</label>
            <ui-tooltip text="${t('tooltip.tts')}"></ui-tooltip>
            <select @change="${(e: Event) => this.handleInputChange(e, 'tts', 'module')}">
              ${this.plugins.tts.map(p => html`<option value="${p}" ?selected="${p === ttsModule}">${p}</option>`)}
              ${!this.plugins.tts.includes(ttsModule) ? html`<option value="${ttsModule}" selected>${ttsModule}</option>` : ''}
            </select>
          </div>

          <div class="form-group">
            <label>${t('settings.stt')}</label>
            <ui-tooltip text="${t('tooltip.stt')}"></ui-tooltip>
            <select @change="${(e: Event) => this.handleInputChange(e, 'stt', 'module')}">
              ${this.plugins.stt.map(p => html`<option value="${p}" ?selected="${p === sttModule}">${p}</option>`)}
              ${!this.plugins.stt.includes(sttModule) ? html`<option value="${sttModule}" selected>${sttModule}</option>` : ''}
            </select>
          </div>

          <div class="form-group">
            <label>${t('settings.vad_energy')}</label>
            <ui-tooltip text="${t('tooltip.vad_energy')}"></ui-tooltip>
            <input type="number" step="0.1" .value="${listenerEnergy}" @change="${(e: Event) => this.handleInputChange(e, 'listener', 'energy_ratio', 'number')}">
          </div>
        </div>

        <!-- Skills & Location -->
        <div class="glass-card">
          <h2>${t('settings.skills')}</h2>
          
          <div class="form-group checkbox-group">
            <input type="checkbox" .checked="${autoUpdate}" @change="${(e: Event) => this.handleInputChange(e, 'skills', 'auto_update', 'checkbox')}">
            <label style="margin:0;">${t('settings.skills.auto_update')}</label>
            <ui-tooltip text="${t('tooltip.skills.auto_update')}"></ui-tooltip>
          </div>

          <div class="form-group">
            <label>${t('settings.skills.blacklisted')}</label>
            <ui-tooltip text="${t('tooltip.skills.blacklisted')}"></ui-tooltip>
            <input type="text" .value="${blacklistedSkills}" @change="${(e: Event) => this.handleInputChange(e, 'skills', 'blacklisted_skills', 'list')}">
          </div>
          
          <div class="form-group">
            <label>${t('settings.skills.priority')}</label>
            <ui-tooltip text="${t('tooltip.skills.priority')}"></ui-tooltip>
            <input type="text" .value="${prioritySkills}" @change="${(e: Event) => this.handleInputChange(e, 'skills', 'priority_skills', 'list')}">
          </div>

          <h2 style="margin-top:2rem;">${t('settings.location')}</h2>
          <div class="form-group">
            <label>${t('settings.location.city')}</label>
            <ui-tooltip text="${t('tooltip.location.city')}"></ui-tooltip>
            <input type="text" .value="${city}" @change="${(e: Event) => this.handleNestedChange(e, 'location', 'city', 'name')}">
          </div>
          <div class="form-group">
            <label>${t('settings.location.timezone')}</label>
            <ui-tooltip text="${t('tooltip.location.timezone')}"></ui-tooltip>
            <input type="text" .value="${timezone}" @change="${(e: Event) => this.handleNestedChange(e, 'location', 'timezone', 'code')}">
          </div>

          <h2 style="margin-top:2rem;">${t('settings.gui')}</h2>
          <div class="form-group">
            <label>${t('settings.gui.idle')}</label>
            <ui-tooltip text="${t('tooltip.gui.idle')}"></ui-tooltip>
            <input type="text" .value="${idleScreen}" @change="${(e: Event) => this.handleInputChange(e, 'gui', 'idle_display_skill')}">
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
      return html`<div style="display:flex; justify-content:center; align-items:center; height: 50vh;"><div class="spinner"></div></div>`;
    }

    return html`
      <div class="header">
        <div>
          <h1>${t('settings.title')}</h1>
          <p class="subtitle">${t('settings.subtitle')}</p>
        </div>
        <div class="lang-switcher">
          <select @change="${this.changeLang}">
            <option value="en" ?selected="${getCurrentLanguage() === 'en'}">English</option>
            <option value="es" ?selected="${getCurrentLanguage() === 'es'}">Español</option>
          </select>
        </div>
      </div>

      <div class="toggle-container">
        <span style="font-weight: 600; color: #334155;">${t('settings.advanced_mode')}</span>
        <button class="btn btn-secondary" @click="${() => this.showRawJson = !this.showRawJson}">
          ${this.showRawJson ? t('settings.switch_ui') : t('settings.edit_json')}
        </button>
      </div>

      ${this.showRawJson ? this.renderRawJson() : this.renderForm()}

      <div style="display: flex; align-items: center; margin-bottom: 3rem;">
        <button class="btn btn-primary" @click="${this.saveConfig}" ?disabled="${this.saveStatus === 'saving'}">
          ${this.saveStatus === 'saving' ? t('settings.btn_applying') : t('settings.btn_apply')}
        </button>
        ${this.saveStatus === 'success' ? html`<span class="status-msg success">✓ Live patched successfully!</span>` : ''}
        ${this.saveStatus === 'error' ? html`<span class="status-msg error">✗ Failed to patch config.</span>` : ''}
      </div>
    `;
  }
}
