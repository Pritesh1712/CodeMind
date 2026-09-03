/**
 * api/client.js — Axios HTTP Client
 * 
 * Configures axios to talk to our FastAPI backend.
 * All API calls go through this client.
 * 
 * Student note:
 *   Centralizing the API client means we only need to change the
 *   base URL in one place if we deploy to a different server.
 */

import axios from 'axios';

// Use VITE_API_URL in production, or relative URL in development (forwarded by Vite proxy)
const baseURL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes timeout for cloning/indexing operations
});

// ── Response interceptor ──────────────────────────────────────────────────────
// This runs on every response. We use it to extract user-friendly error messages.
apiClient.interceptors.response.use(
  (response) => response, // pass through successful responses
  (error) => {
    // Format error messages nicely
    const message =
      error.response?.data?.detail ||  // FastAPI error detail
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
