import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { personasApi, sessionsApi } from '../services/voice-api';

@customElement('view-dashboard')
export class ViewDashboard extends LitElement {
  @state() private personaCount = 0;
  @state() private sessionCount = 0;

  static styles = css`
    :host {
      display: block;
      padding: 2rem;
      font-family: 'Inter', sans-serif;
      color: #333;
    }

    .header {
      margin-bottom: 2rem;
    }

    h1 {
      font-size: 2rem;
      margin: 0;
      color: #111;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .card {
      background: white;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 6px rgba(0,0,0,0.05);
      border: 1px solid #eee;
    }

    .card-title {
      font-size: 1rem;
      color: #666;
      margin-bottom: 0.5rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .card-value {
      font-size: 2.5rem;
      font-weight: 700;
      color: #4f46e5;
    }

    .quick-actions {
      margin-top: 3rem;
    }

    .btn {
      display: inline-block;
      padding: 0.75rem 1.5rem;
      background: #4f46e5;
      color: white;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      transition: background 0.2s;
    }

    .btn:hover {
      background: #4338ca;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadStats();
  }

  async loadStats() {
    try {
      const [personasRes, sessionsRes] = await Promise.all([
        personasApi.list(),
        sessionsApi.list({ status: 'active' })
      ]);
      
      if (personasRes.data) {
        this.personaCount = personasRes.data.length;
      }
      
      if (sessionsRes.data) {
        this.sessionCount = sessionsRes.data.total || sessionsRes.data.sessions.length;
      }
    } catch (err) {
      console.error("Failed to load dashboard stats:", err);
    }
  }

  render() {
    return html`
      <div class="header">
        <h1>Overview</h1>
        <p>Welcome to the AgentVoiceBox Administration Panel.</p>
      </div>

      <div class="grid">
        <div class="card">
          <div class="card-title">Active Personas</div>
          <div class="card-value">${this.personaCount}</div>
        </div>
        
        <div class="card">
          <div class="card-title">Active Sessions</div>
          <div class="card-value">${this.sessionCount}</div>
        </div>
        
        <div class="card">
          <div class="card-title">System Status</div>
          <div class="card-value" style="color: #10b981; font-size: 1.5rem; margin-top: 0.5rem;">
            ● All Systems Nominal
          </div>
        </div>
      </div>

      <div class="quick-actions">
        <h2>Quick Actions</h2>
        <div style="display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap;">
          <a href="/voice-manager" class="btn">Manage Personas</a>
          <a href="/cloning" class="btn" style="background: #8b5cf6;">Voice Cloning Library</a>
          <a href="/settings" class="btn" style="background: #3b82f6;">OVOS Core Settings</a>
          <a href="/playground" class="btn" style="background: #10b981;">Test Realtime WebSocket</a>
        </div>
      </div>
    `;
  }
}
