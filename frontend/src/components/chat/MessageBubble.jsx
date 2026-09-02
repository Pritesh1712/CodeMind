/**
 * components/chat/MessageBubble.jsx — Individual Chat Message with Smooth Streaming Animation
 * 
 * Features:
 *   - ChatGPT-style typewriter streaming animation for newly generated answers
 *   - Blinking cursor indicator during generation
 *   - Fades in citations, confidence badge, and clickable follow-up pills upon completion
 *   - 1-click skip animation on click
 */

import { useState, useEffect, useRef } from 'react';
import MarkdownRenderer from '../ui/MarkdownRenderer';
import CitationBadge from '../citations/CitationBadge';

export default function MessageBubble({ message, onSelectFollowUp, isLastMessage }) {
  const isUser = message.role === 'user';
  const citations = message.citations || [];
  const followUps = message.follow_up_questions || [];

  // Typewriter streaming state for newly received AI messages
  const shouldAnimate = !isUser && message.isStreaming;
  const [displayedText, setDisplayedText] = useState(shouldAnimate ? '' : message.content);
  const [isTyping, setIsTyping] = useState(shouldAnimate);

  const fullText = message.content || '';
  const indexRef = useRef(0);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedText(fullText);
      setIsTyping(false);
      return;
    }

    // Start ChatGPT-style word/chunk streaming animation
    indexRef.current = 0;
    setDisplayedText('');
    setIsTyping(true);

    // Stream in chunks of words for natural, smooth reading flow
    const words = fullText.split(/(\s+)/);
    let currentIdx = 0;
    let accumulated = '';

    const interval = setInterval(() => {
      if (currentIdx < words.length) {
        // Take 1 to 2 words per tick
        const nextChunk = (words[currentIdx] || '') + (words[currentIdx + 1] || '');
        currentIdx += 2;
        accumulated += nextChunk;
        setDisplayedText(accumulated);
      } else {
        clearInterval(interval);
        setDisplayedText(fullText);
        setIsTyping(false);
      }
    }, 22); // ~45 tokens/sec reading speed

    timerRef.current = interval;

    return () => clearInterval(interval);
  }, [fullText, shouldAnimate]);

  // Allow clicking anywhere on the message to instantly finish streaming
  const handleSkipAnimation = () => {
    if (isTyping) {
      if (timerRef.current) clearInterval(timerRef.current);
      setDisplayedText(fullText);
      setIsTyping(false);
    }
  };

  return (
    <div className={`message ${isUser ? 'message-user' : ''}`}>
      {/* Avatar */}
      <div className={`message-avatar ${isUser ? 'message-avatar-user' : 'message-avatar-ai'}`}>
        {isUser ? '👤' : '🤖'}
      </div>

      {/* Content */}
      <div className="message-content" onClick={handleSkipAnimation}>
        <div className={`message-bubble ${isUser ? 'message-bubble-user' : 'message-bubble-ai'}`}>
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <div className="ai-response-stream-wrapper">
              <MarkdownRenderer content={displayedText} />
              {isTyping && <span className="streaming-cursor">▊</span>}
            </div>
          )}
        </div>

        {/* Citations, Confidence & Follow-ups (revealed once typing completes) */}
        {!isUser && !isTyping && (
          <div className="message-meta-section animate-fade-in">
            {/* Citations */}
            {citations.length > 0 && (
              <div className="citations-section">
                {citations.map((citation, index) => (
                  <CitationBadge
                    key={`${citation.file_path}-${citation.start_line}-${index}`}
                    citation={citation}
                  />
                ))}
              </div>
            )}

            {/* Confidence badge */}
            {message.confidence_score !== undefined && (
              <div style={{ marginTop: '8px' }}>
                <span className={`confidence-badge ${
                  message.confidence_score >= 0.25 ? 'confidence-high' : 'confidence-low'
                }`}>
                  {message.confidence_score >= 0.25 ? '✓' : '⚠'} Confidence:{' '}
                  {Math.round(message.confidence_score * 100)}%
                </span>
              </div>
            )}

            {/* Interactive Follow-up Questions (1-click exploration) */}
            {followUps.length > 0 && (
              <div className="followup-questions-container">
                <div className="followup-questions-title">
                  <span>💡 Suggested Next Questions:</span>
                </div>
                <div className="followup-questions-list">
                  {followUps.map((question, idx) => (
                    <button
                      key={idx}
                      className="followup-pill-btn"
                      onClick={() => onSelectFollowUp && onSelectFollowUp(question)}
                      type="button"
                    >
                      <span className="followup-pill-icon">💬</span>
                      <span className="followup-pill-text">{question}</span>
                      <span className="followup-pill-arrow">→</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
