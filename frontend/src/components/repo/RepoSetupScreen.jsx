/**
 * components/repo/RepoSetupScreen.jsx — Repository Input & Selection Screen
 * 
 * Allows users to:
 *   1. Paste a new GitHub repository URL to index
 *   2. Select from previously indexed repositories
 *   3. Delete any indexed repository
 */

import { useState, useEffect, useRef } from 'react';
import useAppStore from '../../store/useAppStore';
import ProgressTracker from './ProgressTracker';
import {
  analyzeRepository,
  getRepositoryStatus,
  listRepositories,
  deleteRepository,
} from '../../api/repositories';

export default function RepoSetupScreen({ onSelectRepo, onCancel }) {
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [isFlowAnimating, setIsFlowAnimating] = useState(false);

  const {
    currentRepository, setCurrentRepository,
    isIndexing, setIndexing,
    repositories, setRepositories,
    removeRepositoryFromList,
  } = useAppStore();

  const pollIntervalRef = useRef(null);

  // Refresh repo list on mount
  useEffect(() => {
    async function loadRepoList() {
      try {
        const list = await listRepositories();
        setRepositories(list || []);
      } catch (e) {
        console.error('Failed to load repositories:', e);
      }
    }
    loadRepoList();
  }, []);

  // Poll for indexing status every 1 second while indexing
  useEffect(() => {
    if (
      currentRepository &&
      currentRepository.status !== 'ready' &&
      currentRepository.status !== 'failed'
    ) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const status = await getRepositoryStatus(currentRepository.id);
          const updated = { ...currentRepository, ...status };
          setCurrentRepository(updated);

          if (status.status === 'ready') {
            clearInterval(pollIntervalRef.current);
            setIndexing(false);
            const list = await listRepositories();
            setRepositories(list || []);
          } else if (status.status === 'failed') {
            clearInterval(pollIntervalRef.current);
            setIndexing(false);
            setIsFlowAnimating(false);
          }
        } catch (err) {
          clearInterval(pollIntervalRef.current);
        }
      }, 1000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [currentRepository?.id, currentRepository?.status]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!url.trim()) {
      setFormError('Please enter a GitHub repository URL.');
      return;
    }

    setIsSubmitting(true);
    setIsFlowAnimating(true);
    setIndexing(true);

    try {
      const repo = await analyzeRepository(url.trim());
      setCurrentRepository(repo);
      setUrl('');

      // Refresh list in background
      const list = await listRepositories();
      setRepositories(list || []);
    } catch (err) {
      setFormError(err.message || 'Failed to analyze repository');
      setIndexing(false);
      setIsFlowAnimating(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRepo = async (e, repoId) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this repository and all its chat history?')) {
      return;
    }

    setDeletingId(repoId);
    try {
      await deleteRepository(repoId);
      removeRepositoryFromList(repoId);
    } catch (err) {
      alert('Failed to delete repository: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const isIndexingInProgress =
    currentRepository &&
    currentRepository.status !== 'ready' &&
    currentRepository.status !== 'failed';

  const hasFailed = currentRepository?.status === 'failed';

  return (
    <div className="repo-setup">
      <div className="repo-setup-card">
        {/* Back button if a repo was already active */}
        {onCancel && (
          <div style={{ marginBottom: '12px' }}>
            <button
              className="btn btn-ghost"
              onClick={onCancel}
              style={{ fontSize: '12px', padding: '4px 8px' }}
              type="button"
            >
              ← Back to Chat
            </button>
          </div>
        )}

        {/* Icon */}
        <div className="repo-setup-icon">🧠</div>

        {/* Title */}
        <h1 className="repo-setup-title">CodeMind</h1>
        <p className="repo-setup-subtitle">
          Analyze any public GitHub repository and explore its codebase with AI
        </p>

        {/* URL Input Form */}
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label className="input-label" htmlFor="repo-url">
              GitHub Repository URL
            </label>
            <input
              id="repo-url"
              type="text"
              className="text-input"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/username/repository"
              disabled={isSubmitting || isFlowAnimating}
            />
          </div>

          {formError && (
            <div className="error-banner" style={{ marginBottom: '16px' }}>
              <span>⚠️ {formError}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={isSubmitting || isFlowAnimating}
            id="analyze-repo-button"
          >
            {isSubmitting ? 'Starting...' : isFlowAnimating ? 'Analyzing...' : '🔍 Analyze Repository'}
          </button>
        </form>

        {/* Progress tracker while indexing & animating */}
        {currentRepository && isFlowAnimating && (
          <div style={{ marginTop: '24px' }}>
            <div className="sidebar-label" style={{ marginBottom: '12px' }}>
              Indexing {currentRepository.name || currentRepository.url}
            </div>
            <ProgressTracker
              status={currentRepository.status}
              progressMessage={currentRepository.progress_message}
              onComplete={() => {
                setIsFlowAnimating(false);
                if (onSelectRepo) onSelectRepo(currentRepository);
              }}
            />
          </div>
        )}

        {/* Error state */}
        {hasFailed && (
          <div className="error-banner" style={{ marginTop: '16px' }}>
            <div>
              <strong>Indexing failed</strong><br />
              {currentRepository.error_message}
              <br /><br />
              You can try again with the same URL.
            </div>
          </div>
        )}

        {/* Indexed Repositories List */}
        {repositories.length > 0 && !isIndexingInProgress && (
          <div style={{ marginTop: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <div className="sidebar-label" style={{ marginBottom: '10px' }}>
              Indexed Repositories ({repositories.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
              {repositories.map((repo) => (
                <div
                  key={repo.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div
                    style={{ cursor: 'pointer', flex: 1, overflow: 'hidden' }}
                    onClick={() => onSelectRepo && onSelectRepo(repo)}
                  >
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      📦 {repo.name || repo.url}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {repo.chunks_count || 0} chunks indexed
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '11px', padding: '4px 8px' }}
                      onClick={() => onSelectRepo && onSelectRepo(repo)}
                      type="button"
                    >
                      Open Chat
                    </button>
                    <button
                      className="btn btn-ghost"
                      style={{ fontSize: '12px', padding: '4px 6px', color: 'var(--error)' }}
                      onClick={(e) => handleDeleteRepo(e, repo.id)}
                      disabled={deletingId === repo.id}
                      title="Delete repository"
                      type="button"
                    >
                      {deletingId === repo.id ? '...' : '🗑️'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Example repos */}
        {!isIndexingInProgress && repositories.length === 0 && (
          <div style={{ marginTop: '24px' }}>
            <div className="sidebar-label" style={{ marginBottom: '8px' }}>
              Try these repositories
            </div>
            {[
              'https://github.com/tiangolo/fastapi',
              'https://github.com/pallets/flask',
              'https://github.com/psf/requests',
            ].map((example) => (
              <button
                key={example}
                className="btn btn-ghost btn-full"
                style={{ marginBottom: '6px', justifyContent: 'flex-start', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
                onClick={() => setUrl(example)}
                disabled={isSubmitting || isIndexingInProgress}
                type="button"
              >
                {example}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
