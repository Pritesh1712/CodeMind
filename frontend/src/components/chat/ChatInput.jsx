/**
 * components/chat/ChatInput.jsx — Message Input Box
 * 
 * Features:
 *   - Auto-resizing textarea
 *   - Enter to send (Shift+Enter for newline)
 *   - Disabled while loading
 *   - Send button
 */

import { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSend, isLoading, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea as user types
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';  // reset first
      textarea.style.height = `${textarea.scrollHeight}px`;  // then set to content height
    }
  }, [text]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();  // prevent newline
      handleSend();
    }
    // Shift+Enter = newline (default browser behavior, no need to handle)
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading || disabled) return;
    
    onSend(trimmed);
    setText('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="chat-input-area">
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? 'Please analyze a repository first...'
                : 'Ask a question about the codebase...'
            }
            disabled={isLoading || disabled}
            rows={1}
            id="chat-input"
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!text.trim() || isLoading || disabled}
            aria-label="Send message"
            id="chat-send-button"
          >
            {isLoading ? (
              // Loading spinner
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeDasharray="40" strokeDashoffset="10">
                  <animate attributeName="stroke-dashoffset" from="40" to="0" dur="1s" repeatCount="indefinite" />
                </path>
              </svg>
            ) : (
              // Send arrow icon
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
        <div className="input-hint">
          Press <strong>Enter</strong> to send · <strong>Shift+Enter</strong> for new line
        </div>
      </div>
    </div>
  );
}
