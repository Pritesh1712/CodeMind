/**
 * components/layout/Sidebar.jsx — Left Sidebar
 * 
 * Features:
 *   - Logo & branding
 *   - Multiple Repositories List with active indicator & 1-click delete
 *   - New Chat button
 *   - Repository-specific chat list (strictly isolated per repo)
 *   - Clean Three-Dots (⋮) menu on each chat for Pin, Rename, and Delete
 *   - "+ Add Repository" / "Analyze Different Repo"
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

  // Close three-dots dropdown if user clicks outside
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

  // Fetch chats ONLY for the currently active repository
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
      // Filter strictly by current repository id
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
    if (!window.confirm('Delete this chat conversation?')) return;
    try {
      await deleteChat(chatId);
      removeChatFromList(chatId);
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  }

  async function handleDeleteRepo(e, repo) {
    e.stopPropagation();
    if (!window.confirm(`Delete repository "${repo.name || repo.url}" and all its vector embeddings & chats?`)) {
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
        <div className="sidebar-logo-icon">🧠</div>
        <span className="sidebar-logo-text">CodeMind</span>
      </div>

      {/* ── Repositories Section ────────────────────────────────────────────── */}
      <div className="sidebar-section-repos">
        <div className="sidebar-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Repositories ({repositories.length})</span>
          <button
            className="sidebar-add-repo-btn"
            onClick={onSwitchRepo}
            title="Analyze a new repository"
            type="button"
          >
            + Add
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
                  <span className="repo-card-icon">📦</span>
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
                  🗑️
                </button>
              </div>
            );
          })}

          {repositories.length === 0 && (
            <div className="sidebar-empty-hint">No repositories indexed yet.</div>
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
            style={{ gap: '8px', fontSize: '13px', padding: '9px 12px' }}
            type="button"
          >
            ✏️ New Chat
          </button>
        </div>
      )}

      {/* ── Chats for Active Repository ─────────────────────────────────────── */}
      <div className="sidebar-chats">
        <div className="sidebar-label" style={{ padding: '6px 8px' }}>
          {currentRepository?.name
            ? `Chats · ${currentRepository.name}`
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
                  {chat.is_pinned && <span className="pin-icon" title="Pinned chat">📌 </span>}
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
                  ⋮
                </button>

                {/* Dropdown Menu */}
                {isMenuOpen && (
                  <div className="chat-dropdown-menu">
                    <button
                      className="chat-dropdown-item"
                      onClick={(e) => handleTogglePin(e, chat)}
                      type="button"
                    >
                      <span className="dropdown-item-icon">📌</span>
                      <span>{chat.is_pinned ? 'Unpin Chat' : 'Pin to Top'}</span>
                    </button>
                    <button
                      className="chat-dropdown-item"
                      onClick={(e) => handleStartRename(e, chat)}
                      type="button"
                    >
                      <span className="dropdown-item-icon">✏️</span>
                      <span>Rename</span>
                    </button>
                    <div className="dropdown-divider" />
                    <button
                      className="chat-dropdown-item dropdown-item-delete"
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                      type="button"
                    >
                      <span className="dropdown-item-icon">🗑️</span>
                      <span>Delete Chat</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {currentRepository?.status === 'ready' && chatList.length === 0 && (
          <div className="sidebar-empty-chats">
            No chats for this repository yet.<br />
            Ask your first question!
          </div>
        )}
      </div>

      {/* Switch / Analyze Different Repo Footer Button */}
      <div style={{ padding: '8px', borderTop: '1px solid var(--border-color)' }}>
        <button
          className="btn btn-ghost btn-full"
          onClick={onSwitchRepo}
          style={{ fontSize: '13px' }}
          id="switch-repo-button"
          type="button"
        >
          🔄 Analyze Different Repo
        </button>
      </div>
    </aside>
  );
}
