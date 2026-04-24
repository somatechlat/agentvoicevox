import { html, render } from 'lit';
import './components/saas-layout';
import './views/view-login';
import './views/view-setup';
import './views/view-auth-callback';
import './views/view-voice-playground';
import './views/view-settings';
import './views/view-voice-cloning';
import './components/ui-tooltip';

// Get the app container
const appContainer = document.getElementById('app');

if (!appContainer) {
    throw new Error('Could not find #app element');
}

// Simple router implementation
function navigate() {
    const path = window.location.pathname;
    console.log('[Router] Navigating to:', path);

    let template;
    if (path === '/admin/setup') {
        template = html`<view-setup></view-setup>`;
    } else if (path === '/auth/callback') {
        template = html`<view-auth-callback></view-auth-callback>`;
    } else if (path === '/voice-playground') {
        template = html`<view-voice-playground></view-voice-playground>`;
    } else if (path === '/settings') {
        template = html`<saas-layout><view-settings></view-settings></saas-layout>`;
    } else if (path === '/cloning') {
        template = html`<saas-layout><view-voice-cloning></view-voice-cloning></saas-layout>`;
    } else if (path === '/dashboard') {
        template = html`<saas-layout><view-dashboard></view-dashboard></saas-layout>`;
    } else {
        // Default to login for all other paths
        template = html`<view-login></view-login>`;
    }

    render(template, appContainer);
}

// Listen for navigation events
window.addEventListener('popstate', navigate);

// Initial render
navigate();

console.log('[App] Lit 3 frontend initialized');
