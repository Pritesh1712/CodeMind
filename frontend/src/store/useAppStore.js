/**
 * store/useAppStore.js — Global Application State
 * 
 * We use Zustand for state management.
 */

import { create } from 'zustand';

const useAppStore = create((set, get) => ({
  // ── Repository State ────────────────────────────────────────────────────────
  
  // The repository currently active/selected
  currentRepository: null,        // { id, url, name, status, chunks_count, ... }
  
  // List of all indexed repositories
  repositories: [],
  
  setRepositories: (repositories) => set({ repositories }),

  setCurrentRepository: (repo) => set({ currentRepository: repo }),
  
  updateRepository: (updatedRepo) => set((state) => ({
    currentRepository: state.currentRepository?.id === updatedRepo.id
      ? updatedRepo
      : state.currentRepository,
    repositories: state.repositories.map((r) =>
      r.id === updatedRepo.id ? updatedRepo : r
    ),
  })),

  removeRepositoryFromList: (repoId) => set((state) => {
    const updated = state.repositories.filter((r) => r.id !== repoId);
    const isCurrent = state.currentRepository?.id === repoId;
    return {
      repositories: updated,
      currentRepository: isCurrent ? null : state.currentRepository,
      currentChatId: isCurrent ? null : state.currentChatId,
      messages: isCurrent ? [] : state.messages,
      chatList: isCurrent ? [] : state.chatList,
    };
  }),

  // ── Chat State ───────────────────────────────────────────────────────────────
  
  // The currently open chat
  currentChatId: null,
  
  // All messages in the current chat
  messages: [],
  
  // Sidebar list of all past chats
  chatList: [],
  
  setCurrentChatId: (id) => set({ currentChatId: id }),
  
  setMessages: (messages) => set({ messages }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  
  updateMessage: (id, updater) => set((state) => ({
    messages: state.messages.map((m) => m.id === id ? { ...m, ...updater } : m),
  })),

  setChatList: (chatList) => set({ chatList }),

  updateChatInList: (chatId, updates) => set((state) => ({
    chatList: state.chatList
      .map((c) => c.id === chatId ? { ...c, ...updates } : c)
      .sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0)),
  })),
  
  removeChatFromList: (chatId) => set((state) => ({
    chatList: state.chatList.filter((c) => c.id !== chatId),
    currentChatId: state.currentChatId === chatId ? null : state.currentChatId,
    messages: state.currentChatId === chatId ? [] : state.messages,
  })),

  // Start a fresh chat
  startNewChat: () => set({
    currentChatId: null,
    messages: [],
  }),

  // ── UI State ─────────────────────────────────────────────────────────────────
  
  isLoading: false,            // is the AI generating an answer?
  isIndexing: false,           // is a repo being indexed?
  error: null,                 // current error message
  
  setLoading: (loading) => set({ isLoading: loading }),
  setIndexing: (indexing) => set({ isIndexing: indexing }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

export default useAppStore;
