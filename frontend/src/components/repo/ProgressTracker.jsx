/**
 * components/repo/ProgressTracker.jsx — Dynamic Real-Time Progress Bar
 * 
 * Features:
 *   - Continuously tracks actual chunk storage progress (e.g., 192/295 chunks)
 *   - Smooth interpolation without ever getting stuck at 96%
 *   - Live backend status text display
 *   - Smooth transition to 100% upon completion
 */

import { useState, useEffect, useRef } from 'react';

export default function ProgressTracker({ status, progressMessage, onComplete }) {
  const [progress, setProgress] = useState(0);
  const targetProgressRef = useRef(10);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // Calculate target progress from status and progressMessage
  useEffect(() => {
    if (status === 'ready') {
      targetProgressRef.current = 100;
      return;
    }

    if (progressMessage) {
      // Check for "Embedded and stored X/Y code chunks"
      const chunkMatch = progressMessage.match(/(\d+)\s*\/\s*(\d+)/);
      if (chunkMatch) {
        const stored = parseInt(chunkMatch[1], 10);
        const total = parseInt(chunkMatch[2], 10);
        if (total > 0) {
          // Map stored/total chunks to 35% -> 98%
          const fraction = Math.min(1, stored / total);
          targetProgressRef.current = Math.max(targetProgressRef.current, 35 + fraction * 63);
          return;
        }
      }

      // Check for earlier phases
      if (progressMessage.toLowerCase().includes('cloning')) {
        targetProgressRef.current = Math.max(targetProgressRef.current, 15);
      } else if (progressMessage.toLowerCase().includes('scanning') || progressMessage.toLowerCase().includes('found')) {
        targetProgressRef.current = Math.max(targetProgressRef.current, 25);
      } else if (progressMessage.toLowerCase().includes('chunking') || progressMessage.toLowerCase().includes('ast')) {
        targetProgressRef.current = Math.max(targetProgressRef.current, 35);
      } else if (progressMessage.toLowerCase().includes('embedding') || progressMessage.toLowerCase().includes('computing')) {
        targetProgressRef.current = Math.max(targetProgressRef.current, 45);
      }
    }
  }, [status, progressMessage]);

  // Smooth frame ticker that glides progress toward targetProgress
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        const target = targetProgressRef.current;

        if (status === 'ready') {
          if (prev >= 100) return 100;
          return Math.min(100, +(prev + Math.max(1, (100 - prev) * 0.3)).toFixed(1));
        }

        if (prev < target) {
          // Smooth glide toward target
          const diff = target - prev;
          const step = Math.max(0.2, diff * 0.15);
          return Math.min(target, +(prev + step).toFixed(1));
        }

        // Slight micro-increment to keep it feeling active while waiting
        if (prev < 98 && target < 98) {
          targetProgressRef.current = Math.min(98, target + 0.1);
          return +(prev + 0.05).toFixed(1);
        }

        return prev;
      });
    }, 60);

    return () => clearInterval(interval);
  }, [status]);

  // Trigger completion once 100% is reached
  useEffect(() => {
    if (progress >= 100 && status === 'ready') {
      const timer = setTimeout(() => {
        if (onCompleteRef.current) {
          onCompleteRef.current();
        }
      }, 400);
      return () => clearTimeout(timer);
    }
  }, [progress, status]);

  // Derive user-friendly display text
  const displayText = status === 'ready' && progress >= 100
    ? 'Indexing complete! Starting chat...'
    : progressMessage || (
        progress < 20 ? 'Cloning repository from GitHub...' :
        progress < 35 ? 'Scanning and parsing source code...' :
        progress < 50 ? 'Generating semantic embeddings...' :
        'Storing vector representations in database...'
      );

  return (
    <div className="smooth-progress-container">
      {/* Top Status & Percentage Row */}
      <div className="progress-info-row">
        <div className="progress-status-label">
          <span className="status-live-indicator" />
          <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {displayText}
          </span>
        </div>
        <div className="progress-number-display">{Math.floor(progress)}%</div>
      </div>

      {/* Royal Blue Progress Bar Track */}
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${Math.min(100, Math.max(3, progress))}%`, transition: 'width 0.1s ease-out' }}
        />
      </div>
    </div>
  );
}
