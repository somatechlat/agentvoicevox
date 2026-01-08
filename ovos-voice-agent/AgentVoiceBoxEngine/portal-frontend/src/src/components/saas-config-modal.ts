import { LitElement, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('saas-config-modal')
export class SaasConfigModal extends LitElement {
  @property({ type: Boolean }) open = false;
  @property({ type: String }) service = '';
  @state() private activeTab = 'connection';

  createRenderRoot() { return this; }

  render() {
    if (!this.open) return html``;

    return html`
      <!-- Full-screen Overlay -->
      <div class="fixed inset-0 z-[9999] flex items-center justify-center font-sans">
        <!-- Dark backdrop -->
        <div 
          class="absolute inset-0 bg-black/40 backdrop-blur-md transition-opacity duration-300"
          @click="${this.close}"
        ></div>

        <!-- Modal Container - Clean white with subtle shadow -->
        <div class="relative z-10 w-[92vw] h-[88vh] overflow-hidden rounded-xl bg-white shadow-2xl flex flex-col animate-[scaleIn_0.2s_ease-out]">
          
          <!-- Header - Minimal and clean -->
          <div class="border-b border-gray-200 px-8 py-5 flex items-center justify-between bg-white">
            <div class="flex items-center gap-4">
              ${this.renderServiceIcon()}
              <h2 class="text-2xl font-normal text-gray-900">${this.service}</h2>
            </div>
            <button 
              @click="${this.close}"
              class="w-10 h-10 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center text-gray-400 hover:text-gray-600"
            >
              <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="currentColor">
                <path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z"/>
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="flex flex-1 overflow-hidden bg-gray-50">
            <!-- Sidebar Navigation - Clean minimal -->
            <div class="w-56 border-r border-gray-200 bg-white px-4 py-6">
              <div class="text-xs font-medium uppercase tracking-wider text-gray-500 mb-4 px-3">Settings</div>
              ${this.renderNavigation()}
            </div>

            <!-- Settings Panel -->
            <div class="flex-1 p-10 overflow-y-auto">
              ${this.renderSettings()}
            </div>
          </div>

          <!-- Footer Actions - Clean -->
          <div class="border-t border-gray-200 px-8 py-5 flex items-center justify-between bg-white">
            <button class="px-5 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors">
              Test Connection
            </button>
            <div class="flex gap-3">
              <button 
                @click="${this.close}"
                class="px-5 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button class="px-5 py-2.5 rounded-lg bg-black text-sm font-medium text-white hover:bg-gray-800 transition-colors">
                Save Changes
              </button>
            </div>
          </div>

        </div>
      </div>
    `;
  }

  private renderServiceIcon() {
    if (this.service === 'PostgreSQL Database') {
      return html`
        <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="#2563eb">
            <path d="M480-120q-151 0-255.5-46.5T120-280v-400q0-66 105.5-113T480-840q149 0 254.5 47T840-680v400q0 67-104.5 113.5T480-120Zm0-479q89 0 179-25.5T760-679q-11-29-100.5-55T480-760q-91 0-178.5 25.5T200-679q14 30 101.5 55T480-599Zm0 199q42 0 81-4t74.5-11.5q35.5-7.5 67-18.5t57.5-25v-120q-26 14-57.5 25t-67 18.5Q600-528 561-524t-81 4q-42 0-82-4t-75.5-11.5Q287-543 256-554t-56-25v120q25 14 56 25t66.5 18.5Q358-408 398-404t82 4Zm0 200q46 0 93.5-7t87.5-18.5q40-11.5 67-26t32-29.5v-98q-26 14-57.5 25t-67 18.5Q600-328 561-324t-81 4q-42 0-82-4t-75.5-11.5Q287-343 256-354t-56-25v99q5 15 31.5 29t66.5 25.5q40 11.5 88 18.5t94 7Z"/>
          </svg>
        </div>
      `;
    }
    if (this.service === 'Redis Cache') {
      return html`
        <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="#dc2626">
            <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm80-80h400v-80H280v80Zm0-160h400v-80H280v80Zm0-160h400v-80H280v80Z"/>
          </svg>
        </div>
      `;
    }
    if (this.service === 'Temporal Workflows') {
      return html`
        <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="#9333ea">
            <path d="m612-292 56-56-148-148v-184h-80v216l172 172ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-400Zm0 320q133 0 226.5-93.5T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160Z"/>
          </svg>
        </div>
      `;
    }
    return html``;
  }

  private renderNavigation() {
    const tabs = this.getServiceTabs();
    return tabs.map(tab => html`
      <div 
        class="px-3 py-2.5 mb-1 rounded-lg cursor-pointer transition-all text-sm ${this.activeTab === tab.id
        ? 'bg-gray-100 text-gray-900 font-medium'
        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      }"
        @click="${() => this.activeTab = tab.id}"
      >
        ${tab.label}
      </div>
    `);
  }

  private getServiceTabs() {
    if (this.service === 'PostgreSQL Database') {
      return [
        { id: 'connection', label: 'Connection' },
        { id: 'pool', label: 'Connection Pool' },
        { id: 'performance', label: 'Performance' },
        { id: 'monitoring', label: 'Monitoring' }
      ];
    } else if (this.service === 'Redis Cache') {
      return [
        { id: 'connection', label: 'Connection' },
        { id: 'memory', label: 'Memory' },
        { id: 'persistence', label: 'Persistence' },
        { id: 'channels', label: 'Channels' }
      ];
    } else if (this.service === 'Temporal Workflows') {
      return [
        { id: 'connection', label: 'Connection' },
        { id: 'workers', label: 'Workers' },
        { id: 'namespace', label: 'Namespace' }
      ];
    }
    return [{ id: 'general', label: 'General' }];
  }

  private renderSettings() {
    if (this.service === 'PostgreSQL Database') return this.renderPostgresSettings();
    if (this.service === 'Redis Cache') return this.renderRedisSettings();
    if (this.service === 'Temporal Workflows') return this.renderTemporalSettings();
    return html``;
  }

  private renderPostgresSettings() {
    if (this.activeTab === 'connection') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Database Connection</h3>
          <p class="text-sm text-gray-600 mb-8">Configure PostgreSQL connection parameters</p>

          ${this.renderInput('Host', 'text', 'localhost', 'Database server hostname or IP address')}
          ${this.renderInput('Port', 'number', '5432', 'PostgreSQL server port (default: 5432)')}
          ${this.renderInput('Database Name', 'text', 'agentvoicebox', '')}
          ${this.renderInput('Username', 'text', 'agentvoicebox', '')}
          ${this.renderInput('Password', 'password', '', 'Database user password')}

          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-900 mb-2">Connection Status</label>
            <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-50 border border-green-200">
              <div class="w-2 h-2 rounded-full bg-green-500"></div>
              <span class="text-sm font-medium text-green-700">Connected</span>
            </div>
          </div>
        </div>
      `;
    }
    if (this.activeTab === 'pool') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Connection Pooling</h3>
          <p class="text-sm text-gray-600 mb-8">Optimize database connection management</p>

          ${this.renderInput('Pool Size', 'number', '10', 'Number of connections to maintain in the pool')}
          ${this.renderInput('Max Overflow', 'number', '5', 'Additional connections beyond pool size')}
          ${this.renderInput('Connection Max Age (seconds)', 'number', '60', 'Maximum lifetime for a single connection')}
        </div>
      `;
    }
    if (this.activeTab === 'performance') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Performance Tuning</h3>
          <p class="text-sm text-gray-600 mb-8">Advanced PostgreSQL performance settings</p>

          ${this.renderInput('Shared Buffers', 'text', '256MB', 'Amount of memory for shared buffer cache')}
          ${this.renderInput('Effective Cache Size', 'text', '1GB', "Planner's assumption about cache size")}
          ${this.renderInput('Work Memory', 'text', '4MB', 'Memory per operation (sort, hash)')}
        </div>
      `;
    }
    if (this.activeTab === 'monitoring') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Query Monitoring</h3>
          <p class="text-sm text-gray-600 mb-8">Enable query logging and monitoring</p>

          ${this.renderToggle('Log SQL Queries', false, 'Enable query logging for debugging')}
          ${this.renderToggle('Slow Query Logging', true, 'Log queries exceeding duration threshold')}
          ${this.renderInput('Slow Query Threshold (ms)', 'number', '1000', '')}
        </div>
      `;
    }
    return html``;
  }

  private renderRedisSettings() {
    if (this.activeTab === 'connection') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Redis Connection</h3>
          <p class="text-sm text-gray-600 mb-8">Configure Redis server connection</p>

          ${this.renderInput('Redis URL', 'text', 'redis://localhost:6379/0', 'Full Redis connection URL')}
          ${this.renderInput('Max Connections', 'number', '200', 'Maximum number of Redis connections')}
          ${this.renderInput('Socket Timeout (seconds)', 'number', '5.0', '')}
          ${this.renderToggle('Retry on Timeout', true, 'Automatically retry failed operations')}
        </div>
      `;
    }
    if (this.activeTab === 'memory') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Memory Management</h3>
          <p class="text-sm text-gray-600 mb-8">Configure Redis memory usage and eviction</p>

          ${this.renderInput('Max Memory', 'text', '512MB', 'Maximum memory Redis can use')}
          ${this.renderSelect('Eviction Policy', ['volatile-lru', 'allkeys-lru', 'volatile-ttl', 'noeviction'], 'volatile-lru', 'How Redis evicts keys when memory limit is reached')}
        </div>
      `;
    }
    if (this.activeTab === 'channels') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Redis Databases</h3>
          <p class="text-sm text-gray-600 mb-8">Separate databases for different purposes</p>

          ${this.renderInput('Cache Database', 'number', '1', 'Database index for caching')}
          ${this.renderInput('Session Database', 'number', '2', 'Database index for session storage')}
          ${this.renderInput('Channel Database', 'number', '3', 'Database index for pub/sub channels')}
        </div>
      `;
    }
    return html``;
  }

  private renderTemporalSettings() {
    if (this.activeTab === 'connection') {
      return html`
        <div class="max-w-2xl">
          <h3 class="text-xl font-normal text-gray-900 mb-2">Temporal Server</h3>
          <p class="text-sm text-gray-600 mb-8">Configure connection to Temporal workflow engine</p>

          ${this.renderInput('Temporal Host', 'text', 'localhost:7233', 'Temporal server address and port')}
          ${this.renderInput('Namespace', 'text', 'agentvoicebox', 'Temporal namespace for workflow isolation')}
          ${this.renderInput('Task Queue', 'text', 'default', 'Default task queue name')}
        </div>
      `;
    }
    return html``;
  }

  // Helper Methods - Clean and minimal
  private renderInput(label: string, type: string, value: string, help: string) {
    return html`
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-900 mb-2">${label}</label>
        <input 
          type="${type}"
          value="${value}"
          class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-shadow"
          placeholder="${value}"
        />
        ${help ? html`<p class="text-xs text-gray-500 mt-1.5">${help}</p>` : ''}
      </div>
    `;
  }

  private renderSelect(label: string, options: string[], selected: string, help: string) {
    return html`
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-900 mb-2">${label}</label>
        <select class="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-shadow">
          ${options.map(opt => html`<option ?selected="${opt === selected}">${opt}</option>`)}
        </select>
        ${help ? html`<p class="text-xs text-gray-500 mt-1.5">${help}</p>` : ''}
      </div>
    `;
  }

  private renderToggle(label: string, checked: boolean, help: string) {
    return html`
      <div class="mb-6 flex items-start justify-between gap-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-900 mb-1">${label}</label>
          ${help ? html`<p class="text-xs text-gray-500">${help}</p>` : ''}
        </div>
        <div class="relative w-11 h-6 rounded-full cursor-pointer transition-colors ${checked ? 'bg-black' : 'bg-gray-300'
      }">
          <div class="absolute top-0.5 ${checked ? 'right-0.5' : 'left-0.5'} w-5 h-5 bg-white rounded-full shadow transition-all duration-200"></div>
        </div>
      </div>
    `;
  }

  private close() {
    this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-config-modal': SaasConfigModal;
  }
}
