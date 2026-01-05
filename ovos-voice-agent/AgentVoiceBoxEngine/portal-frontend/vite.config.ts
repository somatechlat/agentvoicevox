import { defineConfig } from 'vite';

/**
 * Vite Configuration for AgentVoiceBox Portal
 * Port Authority Compliance: 28100 (Frontend Dev Server)
 */

export default defineConfig({
    server: {
        port: 65027,  // Port Authority: 65000-65099 (AgentVoiceBox services)
        host: '0.0.0.0',  // Allow external connections
        strictPort: true,  // Fail if port is already in use
    },
    build: {
        rollupOptions: {
            input: './index.html',
        },
    },
});
