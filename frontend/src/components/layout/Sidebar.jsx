/**
 * components/layout/Sidebar.jsx — Navigation Sidebar with Modern Icons
 */

import { useState, useEffect, useRef } from 'react';
import useAppStore from '../../store/useAppStore';
import { listChats, deleteChat, updateChat, getChat } from '../../api/chat';
import { deleteRepository, listRepositories } from '../../api/repositories';

export default function Sidebar({ onSwitchRepo, onSelectRepo }) {
  const {
    currentRepository, setCurrentRepository,
    currentChatId, setCurrentChatId,
    chatList, setChatList,
    updateChatInList,
    removeChatFromList,
    setMessages,
    startNewChat,
    repositories, setRepositories,
    removeRepositoryFromList,
  } = useAppStore();

  const [activeMenuChatId, setActiveMenuChatId] = useState(null);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const menuRef = useRef(null);

  // Close dropdown if user clicks outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenuChatId(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch all repositories on mount
  useEffect(() => {
    async function loadAllRepos() {
      try {
        const repos = await listRepositories();
        setRepositories(repos || []);
      } catch (err) {
        console.error('Failed to load repos:', err);
      }
    }
    loadAllRepos();
  }, []);

  // Fetch chats ONLY for current active repository
  useEffect(() => {
    if (currentRepository?.id) {
      loadRepoChats(currentRepository.id);
    } else {
      setChatList([]);
    }
  }, [currentRepository?.id]);

  async function loadRepoChats(repoId) {
    try {
      const chats = await listChats(repoId);
      const repoChats = (chats || []).filter((c) => c.repository_id === repoId);
      setChatList(repoChats);
    } catch (err) {
      console.error('Failed to load chats for repo:', err);
      setChatList([]);
    }
  }

  async function handleSelectChat(chatId) {
    if (chatId === currentChatId) return;
    setActiveMenuChatId(null);
    try {
      const chat = await getChat(chatId);
      setCurrentChatId(chatId);
      setMessages(
        (chat.messages || []).map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations || [],
          confidence_score: m.confidence_score,
          follow_up_questions: m.follow_up_questions || [],
          created_at: m.created_at,
        }))
      );
    } catch (err) {
      console.error('Failed to load chat:', err);
    }
  }

  async function handleTogglePin(e, chat) {
    e.stopPropagation();
    setActiveMenuChatId(null);
    const newPinned = !chat.is_pinned;
    try {
      await updateChat(chat.id, { is_pinned: newPinned });
      updateChatInList(chat.id, { is_pinned: newPinned });
    } catch (err) {
      console.error('Failed to update pin status:', err);
    }
  }

  function handleStartRename(e, chat) {
    e.stopPropagation();
    setActiveMenuChatId(null);
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  }

  async function handleSaveRename(chatId) {
    if (!editingTitle.trim()) {
      setEditingChatId(null);
      return;
    }
    try {
      const updated = await updateChat(chatId, { title: editingTitle.trim() });
      updateChatInList(chatId, { title: updated.title });
    } catch (err) {
      console.error('Failed to rename chat:', err);
    } finally {
      setEditingChatId(null);
    }
  }

  async function handleDeleteChat(e, chatId) {
    e.stopPropagation();
    setActiveMenuChatId(null);
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await deleteChat(chatId);
      removeChatFromList(chatId);
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  }

  async function handleDeleteRepo(e, repo) {
    e.stopPropagation();
    if (!window.confirm(`Delete repository "${repo.name || repo.url}" and all its data?`)) {
      return;
    }

    try {
      await deleteRepository(repo.id);
      removeRepositoryFromList(repo.id);
      if (currentRepository?.id === repo.id) {
        onSwitchRepo();
      }
    } catch (err) {
      alert('Failed to delete repository: ' + err.message);
    }
  }

  return (
    <aside className="sidebar">
      {/* App Logo */}
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="sidebar-brand-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
          </div>
          <span className="sidebar-brand-name">CodeMind</span>
        </div>
        <span className="sidebar-brand-badge">RAG</span>
      </div>

      {/* ── Repositories Section ────────────────────────────────────────────── */}
      <div className="sidebar-section-repos">
        <div className="sidebar-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Repositories ({repositories.length})</span>
          <button
            className="sidebar-add-repo-btn"
            onClick={onSwitchRepo}
            title="Index a new repository"
            type="button"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Add</span>
          </button>
        </div>

        <div className="sidebar-repo-list">
          {repositories.map((repo) => {
            const isActive = currentRepository?.id === repo.id;
            return (
              <div
                key={repo.id}
                className={`sidebar-repo-card ${isActive ? 'repo-card-active' : ''}`}
                onClick={() => onSelectRepo && onSelectRepo(repo)}
                title={`Switch to ${repo.name || repo.url}`}
              >
                <div className="repo-card-main">
                  <div className="repo-card-info">
                    <div className="repo-card-name">{repo.name || repo.url}</div>
                    <div className="repo-card-sub">
                      {repo.status === 'ready'
                        ? `${repo.chunks_count || 0} chunks`
                        : repo.status}
                    </div>
                  </div>
                </div>

                <button
                  className="repo-card-delete-btn"
                  onClick={(e) => handleDeleteRepo(e, repo)}
                  title="Delete repository"
                  type="button"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </div>
            );
          })}

          {repositories.length === 0 && (
            <div className="sidebar-empty-hint">No repositories indexed.</div>
          )}
        </div>
      </div>

      {/* ── Action: New Chat ────────────────────────────────────────────────── */}
      {currentRepository?.status === 'ready' && (
        <div style={{ padding: '8px 12px' }}>
          <button
            className="btn btn-primary btn-full"
            onClick={startNewChat}
            id="new-chat-button"
            style={{ fontSize: '13px', padding: '9px 12px', fontWeight: 600, gap: '6px' }}
            type="button"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>New Chat</span>
          </button>
        </div>
      )}

      {/* ── Chats for Active Repository ─────────────────────────────────────── */}
      <div className="sidebar-chats">
        <div className="sidebar-label" style={{ padding: '6px 8px' }}>
          {currentRepository?.name
            ? `Chats : ${currentRepository.name}`
            : 'Recent Chats'}
        </div>

        {chatList.map((chat) => {
          const isMenuOpen = activeMenuChatId === chat.id;
          const isActive = chat.id === currentChatId;

          return (
            <div
              key={chat.id}
              className={`chat-list-item ${isActive ? 'active' : ''} ${chat.is_pinned ? 'pinned' : ''}`}
              onClick={() => handleSelectChat(chat.id)}
              role="button"
              tabIndex={0}
            >
              {/* Title / Inline Rename */}
              {editingChatId === chat.id ? (
                <input
                  type="text"
                  className="chat-rename-input"
                  value={editingTitle}
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onBlur={() => handleSaveRename(chat.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveRename(chat.id);
                    if (e.key === 'Escape') setEditingChatId(null);
                  }}
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="chat-list-item-title">
                  {chat.is_pinned && (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" style={{ color: 'var(--accent-cyan)', flexShrink: 0 }}>
                      <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                    </svg>
                  )}
                  {chat.title}
                </span>
              )}

              {/* Three-Dots Menu Button */}
              <div className="chat-menu-container" ref={isMenuOpen ? menuRef : null}>
                <button
                  className={`chat-threedots-btn ${isMenuOpen ? 'threedots-active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMenuChatId(isMenuOpen ? null : chat.id);
                  }}
                  title="Chat options"
                  type="button"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5" r="2" />
                    <circle cx="12" cy="12" r="2" />
                    <circle cx="12" cy="19" r="2" />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {isMenuOpen && (
                  <div className="chat-dropdown-menu">
                    <button
                      className="chat-dropdown-item"
                      onClick={(e) => handleTogglePin(e, chat)}
                      type="button"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                      </svg>
                      <span>{chat.is_pinned ? 'Unpin' : 'Pin to Top'}</span>
                    </button>
                    <button
                      className="chat-dropdown-item"
                      onClick={(e) => handleStartRename(e, chat)}
                      type="button"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
                      </svg>
                      <span>Rename</span>
                    </button>
                    <div className="dropdown-divider" />
                    <button
                      className="chat-dropdown-item dropdown-item-delete"
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                      type="button"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                      <span>Delete</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {currentRepository?.status === 'ready' && chatList.length === 0 && (
          <div className="sidebar-empty-chats">
            No chats for this repository.<br />
            Ask your first question below.
          </div>
        )}
      </div>

      {/* Switch / Analyze Different Repo Footer Button */}
      <div style={{ padding: '8px', borderTop: '1px solid var(--border-color)' }}>
        <button
          className="btn btn-ghost btn-full"
          onClick={onSwitchRepo}
          style={{ fontSize: '12px', gap: '6px' }}
          id="switch-repo-button"
          type="button"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          <span>Switch Repository</span>
        </button>
      </div>
    </aside>
  );
}
