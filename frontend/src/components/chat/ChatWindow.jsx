/**
 * components/chat/ChatWindow.jsx — Main Chat Area
 * 
 * The central panel showing:
 *   - Welcome screen (when no messages)
 *   - Message history
 *   - Typing indicator (when loading)
 *   - Chat input at the bottom
 */

import { useEffect, useRef } from 'react';
import useAppStore from '../../store/useAppStore';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import WelcomeScreen from './WelcomeScreen';
import ChatInput from './ChatInput';
import { askQuestion } from '../../api/chat';
import { listChats } from '../../api/chat';

export default function ChatWindow() {
  const {
    messages, addMessage, setMessages,
    currentChatId, setCurrentChatId,
    currentRepository,
    isLoading, setLoading,
    error, setError, clearError,
    chatList, setChatList,
  } = useAppStore();

  // Ref to the bottom of the message list — for auto-scrolling
  const bottomRef = useRef(null);

  // Auto-scroll to the bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (question) => {
    if (!currentRepository) return;

    clearError();

    // Immediately add the user's message to the UI
    addMessage({
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: question,
      citations: [],
      created_at: new Date().toISOString(),
    });

    setLoading(true);

    try {
      const result = await askQuestion({
        repositoryId: currentRepository.id,
        question,
        chatId: currentChatId,
      });

      // If this was a new chat, save the chat ID
      if (!currentChatId) {
        setCurrentChatId(result.chat_id);
        // Refresh chat list
        const chats = await listChats(currentRepository.id);
        setChatList(chats);
      }

      // Add AI response with smooth typewriter animation
      addMessage({
        id: `temp-ai-${Date.now()}`,
        role: 'assistant',
        content: result.answer,
        citations: result.citations || [],
        confidence_score: result.confidence_score,
        query_type: result.query_type,
        follow_up_questions: result.follow_up_questions || [],
        isStreaming: true,
        created_at: new Date().toISOString(),
      });

    } catch (err) {
      setError(err.message);
      // Add error message inline
      addMessage({
        id: `temp-error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err.message}`,
        citations: [],
        created_at: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExampleQuestion = (question) => {
    handleSend(question);
  };

  const repoName = currentRepository?.name || '';

  return (
    <div className="chat-window">
      {/* Header */}
      <div className="chat-header">
        <div>
          <div className="chat-header-title">
            {messages.length > 0
              ? messages.find((m) => m.role === 'user')?.content?.slice(0, 50) || 'Chat'
              : repoName
              ? `Chat about ${repoName}`
              : 'CodeMind'}
          </div>
          {repoName && (
            <div className="chat-header-repo">
              {repoName} · {currentRepository?.chunks_count || 0} chunks indexed
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="chat-messages" id="chat-messages">
        {messages.length === 0 ? (
          <WelcomeScreen
            repoName={repoName}
            onSelectQuestion={handleExampleQuestion}
          />
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSelectFollowUp={handleSend}
              />
            ))}
            {isLoading && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Chat Input */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        disabled={!currentRepository || currentRepository.status !== 'ready'}
      />
    </div>
  );
}
