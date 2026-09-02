/**
 * components/repo/ProgressTracker.jsx — Smooth Continuous Progress Bar
 * 
 * Features:
 *   - Continuous smooth 0% -> 100% counter without sticking
 *   - Pure text-based status display (no icons)
 *   - Royal Blue animated glowing progress bar
 *   - Automatically triggers onComplete when 100% is reached and ready
 */

import { useState, useEffect, useRef } from 'react';

export default function ProgressTracker({ status, progressMessage, onComplete }) {
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('Connecting to GitHub repository...');
  const progressRef = useRef(0);

  // Smooth continuous progress ticker
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        // If backend is ready, smoothly accelerate to 100%
        if (status === 'ready') {
          const next = Math.min(100, prev + (prev < 90 ? 4 : 2));
          progressRef.current = next;
          return next;
        }

        // Natural smooth progression: fast at start, steadily continues towards 96%
        let increment = 1;
        if (prev < 30) increment = 2.5;
        else if (prev < 60) increment = 1.6;
        else if (prev < 85) increment = 0.9;
        else if (prev < 96) increment = 0.3;
        else increment = 0; // Wait at 96% until backend is ready

        const next = Math.min(96, +(prev + increment).toFixed(1));
        progressRef.current = next;
        return next;
      });
    }, 80);

    return () => clearInterval(interval);
  }, [status]);

  // Update dynamic status text based on progress percentage
  useEffect(() => {
    if (progress >= 100 && status === 'ready') {
      setStatusText('Indexing complete. Initializing chat...');
      const timer = setTimeout(() => {
        if (onComplete) onComplete();
      }, 500);
      return () => clearTimeout(timer);
    } else if (progress >= 85) {
      setStatusText('Storing vectors in ChromaDB database...');
    } else if (progress >= 60) {
      setStatusText('Generating 384-dimensional semantic embeddings...');
    } else if (progress >= 35) {
      setStatusText('Parsing AST functions, classes, and code chunks...');
    } else if (progress >= 15) {
      setStatusText('Scanning repository and discovering source files...');
    } else {
      setStatusText('Cloning repository from GitHub...');
    }
  }, [progress, status, onComplete]);

  return (
    <div className="smooth-progress-container">
      {/* Top Status & Percentage Row */}
      <div className="progress-info-row">
        <div className="progress-status-label">
          <span className="status-live-indicator" />
          <span>{statusText}</span>
        </div>
        <div className="progress-number-display">{Math.floor(progress)}%</div>
      </div>

      {/* Royal Blue Progress Bar Track */}
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Backend detail message if available */}
      {progressMessage && (
        <div className="progress-detail-text">
          {progressMessage}
        </div>
      )}
    </div>
  );
}
