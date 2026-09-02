/**
 * App.jsx — Root Application Component
 * 
 * Manages the top-level view:
 *   - If no repository is selected or switching repo → show RepoSetupScreen
 *   - If a repository is selected and ready → show the chat interface
 */

import { useState, useEffect } from 'react';
import useAppStore from './store/useAppStore';
import Sidebar from './components/layout/Sidebar';
import ChatWindow from './components/chat/ChatWindow';
import RepoSetupScreen from './components/repo/RepoSetupScreen';
import { listRepositories } from './api/repositories';
import './globals.css';

export default function App() {
  const {
    currentRepository,
    setCurrentRepository,
    setRepositories,
    startNewChat,
  } = useAppStore();

  // Whether the user explicitly wants to switch/add a repo
  const [showSetup, setShowSetup] = useState(false);

  // On initial mount, fetch existing repositories
  useEffect(() => {
    async function initRepos() {
      try {
        const repos = await listRepositories();
        if (repos && repos.length > 0) {
          setRepositories(repos);
          const readyRepo = repos.find((r) => r.status === 'ready');
          if (readyRepo && !currentRepository) {
            setCurrentRepository(readyRepo);
          }
        }
      } catch (err) {
        console.warn('Could not fetch existing repositories on load:', err);
      }
    }
    initRepos();
  }, []);

  function handleSwitchRepo() {
    // Show setup screen explicitly and reset chat
    setShowSetup(true);
    startNewChat();
  }

  function handleRepoSelectedOrReady(repo) {
    setCurrentRepository(repo);
    setShowSetup(false);
  }

  const isReady = currentRepository?.status === 'ready';
  const showChat = isReady && !showSetup;

  return (
    <div className="app-layout">
      {/* Left Sidebar */}
      <Sidebar
        onSwitchRepo={handleSwitchRepo}
        onSelectRepo={(repo) => {
          setCurrentRepository(repo);
          setShowSetup(false);
          startNewChat();
        }}
      />

      {/* Main content area */}
      {showChat ? (
        <ChatWindow />
      ) : (
        <RepoSetupScreen
          onSelectRepo={handleRepoSelectedOrReady}
          onCancel={isReady ? () => setShowSetup(false) : null}
        />
      )}
    </div>
  );
}
