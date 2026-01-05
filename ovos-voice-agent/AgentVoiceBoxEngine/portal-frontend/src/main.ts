import { html, render } from 'lit';
import './components/saas-layout';
import './views/view-login';
import './views/view-setup';
import './views/view-auth-callback';

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
