/**
 * components/chat/MessageBubble.jsx — Modern Chat Bubble with User & AI Logos
 */

import { useState, useEffect, useRef } from 'react';
import MarkdownRenderer from '../ui/MarkdownRenderer';
import CitationBadge from '../citations/CitationBadge';

export default function MessageBubble({ message, onSelectFollowUp, isLastMessage }) {
  const isUser = message.role === 'user';
  const citations = message.citations || [];
  const followUps = message.follow_up_questions || [];

  const shouldAnimate = !isUser && message.isStreaming;
  const [displayedText, setDisplayedText] = useState(shouldAnimate ? '' : message.content);
  const [isTyping, setIsTyping] = useState(shouldAnimate);

  const fullText = message.content || '';
  const timerRef = useRef(null);

  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedText(fullText);
      setIsTyping(false);
      return;
    }

    setDisplayedText('');
    setIsTyping(true);

    const words = fullText.split(/(\s+)/);
    let currentIdx = 0;
    let accumulated = '';

    const interval = setInterval(() => {
      if (currentIdx < words.length) {
        const nextChunk = (words[currentIdx] || '') + (words[currentIdx + 1] || '');
        currentIdx += 2;
        accumulated += nextChunk;
        setDisplayedText(accumulated);
      } else {
        clearInterval(interval);
        setDisplayedText(fullText);
        setIsTyping(false);
      }
    }, 20);

    timerRef.current = interval;
    return () => clearInterval(interval);
  }, [fullText, shouldAnimate]);

  const handleSkipAnimation = () => {
    if (isTyping) {
      if (timerRef.current) clearInterval(timerRef.current);
      setDisplayedText(fullText);
      setIsTyping(false);
    }
  };

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-ai'}`}>
      {/* Avatar with SVG Logo */}
      <div className={`message-avatar ${isUser ? 'message-avatar-user' : 'message-avatar-ai'}`}>
        {isUser ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
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

        {/* Citations, Confidence & Follow-ups */}
        {!isUser && !isTyping && (
          <div className="message-meta-section animate-fade-in">
            {/* Citations */}
            {citations.length > 0 && (
              <div className="citations-section">
                {citations.map((citation, index) => (
                  <CitationBadge key={index} citation={citation} />
                ))}
              </div>
            )}

            {/* Confidence Score */}
            {message.confidence_score !== undefined && (
              <div className="confidence-pill">
                Confidence: {Math.round((message.confidence_score || 0) * 100)}%
              </div>
            )}

            {/* Suggested Follow-up Questions */}
            {followUps.length > 0 && (
              <div className="follow-up-container">
                <div className="follow-up-header">
                  Suggested Next Questions
                </div>
                <div className="follow-up-list">
                  {followUps.map((q, idx) => (
                    <button
                      key={idx}
                      className="follow-up-pill"
                      onClick={() => onSelectFollowUp && onSelectFollowUp(q)}
                      type="button"
                    >
                      {q}
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
