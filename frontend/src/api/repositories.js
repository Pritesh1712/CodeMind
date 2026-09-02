/**
 * api/repositories.js — Repository API Functions
 * 
 * Functions for interacting with repository endpoints.
 * Each function corresponds to one backend API endpoint.
 */

import apiClient from './client';

/**
 * Submit a GitHub URL for indexing.
 * Returns immediately; use pollStatus() to track progress.
 */
export async function analyzeRepository(url) {
  const response = await apiClient.post('/api/repositories/analyze', { url });
  return response.data;
}

/**
 * Poll the indexing status of a repository.
 * Call this every 2 seconds until status === "ready" or "failed".
 */
export async function getRepositoryStatus(repoId) {
  const response = await apiClient.get(`/api/repositories/${repoId}/status`);
  return response.data;
}

/**
 * Get full repository details.
 */
export async function getRepository(repoId) {
  const response = await apiClient.get(`/api/repositories/${repoId}`);
  return response.data;
}

/**
 * List all indexed repositories.
 */
export async function listRepositories() {
  const response = await apiClient.get('/api/repositories');
  return response.data;
}

/**
 * Delete a repository, all its chats, and its vector embeddings.
 */
export async function deleteRepository(repoId) {
  const response = await apiClient.delete(`/api/repositories/${repoId}`);
  return response.data;
}
