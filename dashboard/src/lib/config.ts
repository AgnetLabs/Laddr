/**
 * Configuration helpers for API URLs
 * Uses relative paths so nginx can proxy requests to the API server
 */

/**
 * Get the API base URL
 * In browser (production), always use empty string so requests go to same origin
 * Nginx will proxy /api/* requests to the API server
 * In development with Vite dev server, Vite's proxy handles this
 */
export function getApiBaseUrl(): string {
  // Always use relative paths in browser - nginx/vite proxy handles routing
  // Empty string means axios will use the current origin (window.location.origin)
  // Since all API paths start with /api/, they'll be: origin + /api/...
  return '';
}

/**
 * Get the WebSocket base URL
 * Uses relative paths so nginx can proxy WebSocket connections
 */
export function getWebSocketBaseUrl(): string {
  // In browser, use same origin with ws/wss protocol
  // Nginx will proxy /ws/* to the API server
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }
  
  // Fallback for build time (shouldn't be used in browser)
  return 'ws://localhost:8000';
}

/**
 * Get the API documentation URL
 * Uses relative path so it works through nginx proxy
 */
export function getApiDocsUrl(): string {
  // Use relative path - nginx will proxy /api/* requests
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/docs`;
  }
  // Fallback for build time
  return 'http://localhost:8000/docs';
}

