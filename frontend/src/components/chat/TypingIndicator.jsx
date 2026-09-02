/**
 * components/chat/TypingIndicator.jsx — Animated "AI is thinking" indicator
 */

export default function TypingIndicator() {
  return (
    <div className="message">
      <div className="message-avatar message-avatar-ai">🤖</div>
      <div className="message-content">
        <div className="message-bubble message-bubble-ai">
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        </div>
      </div>
    </div>
  );
}
