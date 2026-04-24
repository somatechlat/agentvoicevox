import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { personasApi, Persona } from '../services/voice-api';

@customElement('view-voice-manager')
export class ViewVoiceManager extends LitElement {
  @state() private personas: Persona[] = [];
  
  static styles = css`
    :host {
      display: block;
      padding: 2rem;
      font-family: 'Inter', sans-serif;
      color: #333;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
    }

    h1 {
      font-size: 2rem;
      margin: 0;
      color: #111;
    }

    .btn-primary {
      background: #4f46e5;
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    
    .btn-primary:hover {
      background: #4338ca;
    }

    table {
      width: 100%;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      border-collapse: collapse;
      box-shadow: 0 4px 6px rgba(0,0,0,0.05);
      border: 1px solid #eee;
    }

    th, td {
      padding: 1rem;
      text-align: left;
      border-bottom: 1px solid #eee;
    }

    th {
      background: #f9fafb;
      font-weight: 600;
      color: #4b5563;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
    }

    .badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      background: #e0e7ff;
      color: #4338ca;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    this.loadPersonas();
  }

  async loadPersonas() {
    try {
      const response = await personasApi.list();
      if (response.data) {
        this.personas = response.data;
      }
    } catch (err) {
      console.error("Failed to load personas from backend:", err);
    }
  }

  render() {
    return html`
      <div class="header">
        <div>
          <h1>Voice Personas</h1>
          <p>Configure OVOS voices and LLM system prompts.</p>
        </div>
        <button class="btn-primary" @click=${this.createNew}>Create Persona</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Voice ID</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${this.personas.map(p => html`
            <tr>
              <td><strong>${p.name}</strong></td>
              <td>${p.voice}</td>
              <td><span class="badge">Active</span></td>
              <td>
                <button style="border:none;background:none;color:#4f46e5;cursor:pointer;">Edit</button>
              </td>
            </tr>
          `)}
          ${this.personas.length === 0 ? html`
            <tr><td colspan="4" style="text-align:center;color:#666;">No personas found.</td></tr>
          ` : ''}
        </tbody>
      </table>
    `;
  }

  async createNew() {
    // Basic implementation of real creation payload using the API wrapper
    const newPersona: Persona = {
      name: "New Custom Persona " + Math.floor(Math.random() * 100),
      voice: "af_heart",
      language: "en-US",
      system_prompt: "You are a helpful assistant."
    };
    try {
      await personasApi.create(newPersona);
      await this.loadPersonas();
    } catch (err) {
      console.error("Failed to create persona:", err);
    }
  }
}
