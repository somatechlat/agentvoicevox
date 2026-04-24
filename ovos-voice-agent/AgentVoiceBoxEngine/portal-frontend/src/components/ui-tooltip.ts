import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('ui-tooltip')
export class UiTooltip extends LitElement {
  @property({ type: String }) text = '';

  static styles = css`
    :host {
      display: inline-flex;
      align-items: center;
      position: relative;
      cursor: help;
      margin-left: 0.5rem;
    }

    .icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #cbd5e1;
      color: white;
      font-size: 11px;
      font-weight: bold;
      transition: background 0.2s;
    }

    :host(:hover) .icon {
      background: #6366f1;
    }

    .tooltip {
      visibility: hidden;
      opacity: 0;
      position: absolute;
      bottom: 125%;
      left: 50%;
      transform: translateX(-50%) translateY(5px);
      background: #1e293b;
      color: white;
      text-align: center;
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: normal;
      width: max-content;
      max-width: 250px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      z-index: 50;
      transition: opacity 0.2s, transform 0.2s, visibility 0.2s;
      pointer-events: none;
    }

    .tooltip::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -5px;
      border-width: 5px;
      border-style: solid;
      border-color: #1e293b transparent transparent transparent;
    }

    :host(:hover) .tooltip {
      visibility: visible;
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  `;

  render() {
    return html`
      <div class="icon">?</div>
      <div class="tooltip">${this.text}</div>
    `;
  }
}
