/**
 * api/chat.js — Chat API Functions
 */

import apiClient from './client';

/**
 * Ask a question about a repository.
 * This is the main chat endpoint that returns an AI answer + citations.
 */
export async function askQuestion({ repositoryId, question, chatId }) {
  const response = await apiClient.post('/api/chat', {
    repository_id: repositoryId,
    question,
    chat_id: chatId || null,
  });
  return response.data;
}

/**
 * Get all chats, optionally filtered by repository.
 */
export async function listChats(repositoryId) {
  const params = repositoryId ? { repository_id: repositoryId } : {};
  const response = await apiClient.get('/api/chats', { params });
  return response.data;
}

/**
 * Get a specific chat with all its messages.
 */
export async function getChat(chatId) {
  const response = await apiClient.get(`/api/chats/${chatId}`);
  return response.data;
}

/**
 * Update a chat's title or pinned status.
 */
export async function updateChat(chatId, { title, is_pinned }) {
  const response = await apiClient.patch(`/api/chats/${chatId}`, {
    title,
    is_pinned,
  });
  return response.data;
}

/**
 * Delete a chat and all its messages.
 */
export async function deleteChat(chatId) {
  const response = await apiClient.delete(`/api/chats/${chatId}`);
  return response.data;
}
