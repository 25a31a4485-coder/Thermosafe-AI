/**
 * THERMOSAFE AI — SIH26162 Runtime Production Configuration
 * 
 * Target Backend API URL for ThermoSafe AI:
 * - Production Deployed FastAPI Backend: https://thermosafe-ai-2.onrender.com (or current origin)
 * - Local Development: http://localhost:8000 (or http://127.0.0.1:8000)
 * 
 * Automatically resolves localhost during local development and connects to the
 * live production backend when accessed on the deployed public domain (https://thermosafe-ai-2.onrender.com/)
 * or other cloud and mobile clients.
 */
window.__THERMOSAFE_API_URL__ = window.__THERMOSAFE_API_URL__ || (function () {
  if (typeof window === 'undefined' || !window.location) {
    return 'https://thermosafe-ai-2.onrender.com';
  }
  const host = window.location.hostname;
  const port = window.location.port;

  // Local development environments
  if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
    if (port === '8000') {
      return ''; // Direct FastAPI server on local machine
    }
    return 'http://localhost:8000';
  }

  // Deployed on Render / cloud host:
  // If accessed directly on the backend's own domain or unified deployment, use origin
  if (host.endsWith('.onrender.com') || host.endsWith('.railway.app') || host.endsWith('.pages.dev')) {
    return window.location.origin ? window.location.origin.replace(/\/+$/, '') : '';
  }

  // Deployed public prototype or mobile/external client fallback
  if (window.location.origin && window.location.origin !== 'null' && window.location.protocol.startsWith('http')) {
    return window.location.origin.replace(/\/+$/, '');
  }

  return 'https://thermosafe-ai-2.onrender.com';
})();