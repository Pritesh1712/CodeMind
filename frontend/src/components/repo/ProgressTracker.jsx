/**
 * components/repo/ProgressTracker.jsx — Step-by-Step Flow Pipeline Animation
 * 
 * Guarantees a smooth, sequential visual pipeline where:
 *   1. Step 1 (Git Clone) is active -> completes with green checkmark (✓)
 *   2. Step 2 (Codebase Scanner) is active -> completes with green checkmark (✓)
 *   3. Step 3 (AST Code Parsing) is active -> completes with green checkmark (✓)
 *   4. Step 4 (Embedding Engine) is active -> completes with green checkmark (✓)
 *   5. Step 5 (ChromaDB Vector Store) is active -> completes with green checkmark (✓)
 *   6. Step 6 (Ready to Chat) lights up completed with green checkmark (✓)
 *   7. Auto-launches chat smoothly after all steps finish!
 */

import { useState, useEffect } from 'react';

const PIPELINE_STEPS = [
  {
    key: 'cloning',
    title: '1. Git Repository Clone',
    desc: 'Fetching source code and repository structure from GitHub',
    icon: '📥',
    duration: 800,
  },
  {
    key: 'scanning',
    title: '2. Codebase Scanner & Filter',
    desc: 'Filtering lockfiles, images, binaries and discovering source files',
    icon: '🔍',
    duration: 700,
  },
  {
    key: 'chunking',
    title: '3. AST Code Parsing & Line Splitter',
    desc: 'Extracting functions, classes, and line-range chunks',
    icon: '🧩',
    duration: 800,
  },
  {
    key: 'embedding',
    title: '4. Semantic Embedding Engine',
    desc: 'Converting code chunks into 384-dimensional vector embeddings',
    icon: '🧠',
    duration: 900,
  },
  {
    key: 'indexing',
    title: '5. Vector Index Storage (ChromaDB)',
    desc: 'Saving embeddings to persistent vector store for instant retrieval',
    icon: '🗄️',
    duration: 700,
  },
  {
    key: 'ready',
    title: '6. Ready to Chat',
    desc: 'Repository fully indexed — AI code assistant initialized',
    icon: '✨',
    duration: 900,
  },
];

export default function ProgressTracker({ status, progressMessage, onComplete }) {
  // Current active step index (0 to 5)
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  // Advance steps sequentially
  useEffect(() => {
    // If not at the final step, schedule next step transition
    if (currentStepIdx < PIPELINE_STEPS.length - 1) {
      const stepDuration = PIPELINE_STEPS[currentStepIdx].duration;
      const timer = setTimeout(() => {
        setCurrentStepIdx((prev) => prev + 1);
      }, stepDuration);
      return () => clearTimeout(timer);
    }
    
    // If at final step and backend is ready, notify parent after a short celebration pause
    if (currentStepIdx >= PIPELINE_STEPS.length - 1 && status === 'ready') {
      const readyTimer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 900);
      return () => clearTimeout(readyTimer);
    }
  }, [currentStepIdx, status, onComplete]);

  // If backend was waiting at intermediate step, finish smoothly when ready
  useEffect(() => {
    if (status === 'ready' && currentStepIdx >= PIPELINE_STEPS.length - 1) {
      const finishTimer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 900);
      return () => clearTimeout(finishTimer);
    }
  }, [status, currentStepIdx, onComplete]);

  return (
    <div className="flow-pipeline-container">
      {/* Pipeline Header Badge */}
      <div className="pipeline-header-badge">
        <span className="pipeline-pulse-indicator" />
        <span className="pipeline-header-text">
          {currentStepIdx === PIPELINE_STEPS.length - 1 && status === 'ready'
            ? '✅ Indexing Complete — Launching Chat'
            : `⚡ Executing Step ${currentStepIdx + 1} of 6`}
        </span>
      </div>

      {/* Connected Steps List */}
      <div className="pipeline-steps-wrapper">
        {PIPELINE_STEPS.map((step, index) => {
          let state = 'pending';
          if (index < currentStepIdx) {
            state = 'done';
          } else if (index === currentStepIdx) {
            // If at the last step and backend is ready, mark it done
            if (index === PIPELINE_STEPS.length - 1 && status === 'ready') {
              state = 'done';
            } else {
              state = 'active';
            }
          }

          const isLast = index === PIPELINE_STEPS.length - 1;

          return (
            <div key={step.key} className={`pipeline-step-item pipeline-step-${state}`}>
              <div className="pipeline-node-row">
                {/* Node Badge Icon */}
                <div className={`pipeline-node-icon pipeline-node-${state}`}>
                  {state === 'done' ? (
                    <span className="pipeline-check-icon">✓</span>
                  ) : state === 'active' ? (
                    <span className="pipeline-spinner-ring" />
                  ) : (
                    <span className="pipeline-static-icon">{step.icon}</span>
                  )}
                </div>

                {/* Node Details */}
                <div className="pipeline-node-content">
                  <div className="pipeline-node-title">
                    <span className="pipeline-title-text">{step.title}</span>
                    {state === 'active' && <span className="pipeline-badge-active">IN PROGRESS</span>}
                    {state === 'done' && <span className="pipeline-badge-done">COMPLETED ✓</span>}
                  </div>
                  <div className="pipeline-node-desc">{step.desc}</div>
                </div>
              </div>

              {/* Connecting Laser Line to Next Step */}
              {!isLast && (
                <div className={`pipeline-connector-track connector-${state}`}>
                  <div
                    className={`pipeline-connector-line ${
                      state === 'active'
                        ? 'animating-flow'
                        : state === 'done'
                        ? 'connector-done'
                        : ''
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Live Status Message Ticker */}
      {progressMessage && (
        <div className="pipeline-live-ticker">
          <span className="live-ticker-dot" />
          <span className="live-ticker-text">{progressMessage}</span>
        </div>
      )}
    </div>
  );
}
