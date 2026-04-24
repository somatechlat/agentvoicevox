import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { ovosApi } from '../services/voice-api';
import { t, setLanguage, getCurrentLanguage, onLanguageChange, SupportedLanguage } from '../utils/i18n';

type AdminTab = 'core' | 'audio' | 'plugins' | 'pipeline' | 'transformers' | 'skills' | 'raw';

@customElement('view-settings')
export class ViewSettings extends LitElement {
  @state() private config: Record<string, any> = {};
  @state() private plugins: { tts: string[]; stt: string[]; wake_word?: string[]; vad?: string[] } = { tts: [], stt: [] };
  @state() private loading = true;
  @state() private activeTab: AdminTab = 'core';
  @state() private rawJsonText = '';
  @state() private saveStatus: 'idle' | 'saving' | 'success' | 'error' = 'idle';

  private unsubscribeI18n!: () => void;

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100vh;
      font-family: 'Inter', sans-serif;
      color: #333;
      background: #f8fafc;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem 2rem;
      background: white;
      border-bottom: 1px solid #e2e8f0;
      z-index: 10;
    }

    .topbar h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 800;
      color: #0f172a;
    }

    .topbar p {
      margin: 0;
      font-size: 0.9rem;
      color: #64748b;
    }

    .layout-container {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .sidebar {
      width: 280px;
      background: #ffffff;
      border-right: 1px solid #e2e8f0;
      overflow-y: auto;
      padding: 1rem 0;
    }

    .tab-btn {
      display: block;
      width: 100%;
      text-align: left;
      padding: 1rem 1.5rem;
      background: none;
      border: none;
      font-size: 0.95rem;
      font-weight: 600;
      color: #475569;
      cursor: pointer;
      transition: background 0.2s, color 0.2s;
      border-left: 3px solid transparent;
    }

    .tab-btn:hover {
      background: #f1f5f9;
      color: #0f172a;
    }

    .tab-btn.active {
      background: #eff6ff;
      color: #2563eb;
      border-left-color: #2563eb;
    }

    .content-area {
      flex: 1;
      padding: 2rem;
      overflow-y: auto;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
      margin-bottom: 2rem;
      max-width: 800px;
    }

    h2 {
      font-size: 1.25rem;
      margin-top: 0;
      margin-bottom: 1.5rem;
      color: #1e293b;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 0.5rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    label {
      display: inline-block;
      font-size: 0.9rem;
      font-weight: 600;
      color: #475569;
      margin-bottom: 0.5rem;
    }

    select, input[type="text"], input[type="number"], textarea {
      width: 100%;
      padding: 0.6rem 0.75rem;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      font-size: 0.95rem;
      color: #334155;
      font-family: inherit;
      box-sizing: border-box;
    }

    select:focus, input:focus, textarea:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    
    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .checkbox-group input { width: auto; }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.6rem 1.2rem;
      font-weight: 600;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.95rem;
    }

    .btn-primary {
      background: #2563eb;
      color: white;
    }
    .btn-primary:hover { background: #1d4ed8; }

    .lang-switcher select {
      padding: 0.4rem;
      border-radius: 4px;
      border: 1px solid #cbd5e1;
      font-weight: 600;
    }

    .spinner {
      width: 40px; height: 40px;
      border: 4px solid rgba(37, 99, 235, 0.2);
      border-radius: 50%;
      border-top-color: #2563eb;
      animation: spin 1s infinite;
      margin: 2rem auto;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .status-msg { margin-left: 1rem; font-weight: 600; font-size: 0.9rem; }
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
      if (this.activeTab === 'raw') {
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

  renderTabNav() {
    const tabs: {id: AdminTab, labelKey: string}[] = [
      { id: 'core', labelKey: 'tab.core' },
      { id: 'audio', labelKey: 'tab.audio' },
      { id: 'plugins', labelKey: 'tab.plugins' },
      { id: 'pipeline', labelKey: 'tab.pipeline' },
      { id: 'transformers', labelKey: 'tab.transformers' },
      { id: 'skills', labelKey: 'tab.skills' },
      { id: 'raw', labelKey: 'settings.advanced_mode' },
    ];

    return html`
      <div class="sidebar">
        ${tabs.map(tab => html`
          <button 
            class="tab-btn ${this.activeTab === tab.id ? 'active' : ''}" 
            @click="${() => this.activeTab = tab.id}">
            ${t(tab.labelKey)}
          </button>
        `)}
      </div>
    `;
  }

  renderCoreTab() {
    const lang = this.config?.lang || 'en-us';
    const log_level = this.config?.log_level || 'INFO';
    const city = this.config?.location?.city?.name || 'LocalCity';
    const timezone = this.config?.location?.timezone?.code || 'UTC';
    const idleScreen = this.config?.gui?.idle_display_skill || '';

    return html`
      <div class="glass-card">
        <h2>${t('tab.core')}</h2>
        
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

        <div class="form-group">
          <label>${t('settings.gui.idle')}</label>
          <ui-tooltip text="${t('tooltip.gui.idle')}"></ui-tooltip>
          <input type="text" .value="${idleScreen}" @change="${(e: Event) => this.handleInputChange(e, 'gui', 'idle_display_skill')}">
        </div>
      </div>
    `;
  }

  renderAudioTab() {
    const ttsModule = this.config?.tts?.module || 'default';
    const sttModule = this.config?.stt?.module || 'default';

    return html`
      <div class="glass-card">
        <h2>${t('tab.audio')}</h2>
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
      </div>
    `;
  }

  renderPluginsTab() {
    const wakeModule = this.config?.listener?.wake_word || 'hey_mycroft';
    const wakeThreshold = this.config?.hotwords?.[wakeModule]?.threshold || '1e-90';
    const vadModule = this.config?.listener?.VAD?.module || 'silero';
    const listenerEnergy = this.config?.listener?.energy_ratio || 1.5;

    return html`
      <div class="glass-card">
        <h2>${t('tab.plugins')}</h2>
        <div class="form-group">
          <label>${t('settings.wakeword.module')}</label>
          <ui-tooltip text="${t('tooltip.wakeword.module')}"></ui-tooltip>
          <input type="text" .value="${wakeModule}" @change="${(e: Event) => this.handleInputChange(e, 'listener', 'wake_word')}">
        </div>
        <div class="form-group">
          <label>${t('settings.wakeword.threshold')}</label>
          <ui-tooltip text="${t('tooltip.wakeword.threshold')}"></ui-tooltip>
          <input type="text" .value="${wakeThreshold}" @change="${(e: Event) => this.handleNestedChange(e, 'hotwords', wakeModule, 'threshold')}">
        </div>
        <div class="form-group">
          <label>${t('settings.vad.module')}</label>
          <ui-tooltip text="${t('tooltip.vad.module')}"></ui-tooltip>
          <input type="text" .value="${vadModule}" @change="${(e: Event) => this.handleNestedChange(e, 'listener', 'VAD', 'module')}">
        </div>
        <div class="form-group">
          <label>${t('settings.vad_energy')}</label>
          <ui-tooltip text="${t('tooltip.vad_energy')}"></ui-tooltip>
          <input type="number" step="0.1" .value="${listenerEnergy}" @change="${(e: Event) => this.handleInputChange(e, 'listener', 'energy_ratio', 'number')}">
        </div>
      </div>
    `;
  }

  renderPipelineTab() {
    const pipeline = (this.config?.intents?.pipeline || ['converse', 'padatious_high', 'adapt', 'fallback_high']).join(', ');
    
    return html`
      <div class="glass-card">
        <h2>${t('tab.pipeline')}</h2>
        <div class="form-group">
          <label>${t('settings.pipeline.order')}</label>
          <ui-tooltip text="${t('tooltip.pipeline.order')}"></ui-tooltip>
          <input type="text" .value="${pipeline}" @change="${(e: Event) => this.handleNestedChange(e, 'intents', 'pipeline', 'list')}">
        </div>
      </div>
    `;
  }

  renderTransformersTab() {
    const audioTrans = (this.config?.audio_transformers?.plugins || []).join(', ');
    const uttTrans = (this.config?.utterance_transformers?.plugins || []).join(', ');
    const dialogTrans = (this.config?.dialog_transformers?.plugins || []).join(', ');

    return html`
      <div class="glass-card">
        <h2>${t('tab.transformers')}</h2>
        <div class="form-group">
          <label>${t('settings.transformers.audio')}</label>
          <ui-tooltip text="${t('tooltip.transformers.audio')}"></ui-tooltip>
          <input type="text" .value="${audioTrans}" @change="${(e: Event) => this.handleNestedChange(e, 'audio_transformers', 'plugins', 'list')}">
        </div>
        <div class="form-group">
          <label>${t('settings.transformers.utterance')}</label>
          <ui-tooltip text="${t('tooltip.transformers.utterance')}"></ui-tooltip>
          <input type="text" .value="${uttTrans}" @change="${(e: Event) => this.handleNestedChange(e, 'utterance_transformers', 'plugins', 'list')}">
        </div>
        <div class="form-group">
          <label>${t('settings.transformers.dialog')}</label>
          <ui-tooltip text="${t('tooltip.transformers.dialog')}"></ui-tooltip>
          <input type="text" .value="${dialogTrans}" @change="${(e: Event) => this.handleNestedChange(e, 'dialog_transformers', 'plugins', 'list')}">
        </div>
      </div>
    `;
  }

  renderSkillsTab() {
    const blacklistedSkills = (this.config?.skills?.blacklisted_skills || []).join(', ');
    const prioritySkills = (this.config?.skills?.priority_skills || []).join(', ');
    const autoUpdate = this.config?.skills?.auto_update ?? true;
    const continuous = this.config?.listener?.continuous_listen ?? false;

    return html`
      <div class="glass-card">
        <h2>${t('tab.skills')}</h2>
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

        <h2 style="margin-top:2rem;">Dialog Options</h2>
        <div class="form-group checkbox-group">
          <input type="checkbox" .checked="${continuous}" @change="${(e: Event) => this.handleInputChange(e, 'listener', 'continuous_listen', 'checkbox')}">
          <label style="margin:0;">${t('settings.continuous.enabled')}</label>
          <ui-tooltip text="${t('tooltip.continuous.enabled')}"></ui-tooltip>
        </div>
      </div>
    `;
  }

  renderRawJson() {
    return html`
      <div class="glass-card" style="max-width:100%;">
        <h2>${t('settings.advanced_mode')}</h2>
        <textarea rows="30" style="font-family: monospace; font-size: 0.85rem;" @change="${this.handleJsonChange}">${this.rawJsonText}</textarea>
      </div>
    `;
  }

  renderContent() {
    switch (this.activeTab) {
      case 'core': return this.renderCoreTab();
      case 'audio': return this.renderAudioTab();
      case 'plugins': return this.renderPluginsTab();
      case 'pipeline': return this.renderPipelineTab();
      case 'transformers': return this.renderTransformersTab();
      case 'skills': return this.renderSkillsTab();
      case 'raw': return this.renderRawJson();
      default: return html``;
    }
  }

  render() {
    if (this.loading) {
      return html`<div class="spinner"></div>`;
    }

    return html`
      <div class="topbar">
        <div>
          <h1>${t('settings.title')}</h1>
          <p>${t('settings.subtitle')}</p>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
          <div class="lang-switcher">
            <select @change="${this.changeLang}">
              <option value="en" ?selected="${getCurrentLanguage() === 'en'}">English</option>
              <option value="es" ?selected="${getCurrentLanguage() === 'es'}">Español</option>
            </select>
          </div>
          <button class="btn btn-primary" @click="${this.saveConfig}" ?disabled="${this.saveStatus === 'saving'}">
            ${this.saveStatus === 'saving' ? t('settings.btn_applying') : t('settings.btn_apply')}
          </button>
          ${this.saveStatus === 'success' ? html`<span class="status-msg success">✓ Live patched!</span>` : ''}
          ${this.saveStatus === 'error' ? html`<span class="status-msg error">✗ Error</span>` : ''}
        </div>
      </div>

      <div class="layout-container">
        ${this.renderTabNav()}
        <div class="content-area">
          ${this.renderContent()}
        </div>
      </div>
    `;
  }
}
