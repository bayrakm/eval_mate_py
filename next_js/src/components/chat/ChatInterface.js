'use client';

import { useState, useRef, useEffect } from 'react';
import { useChatSession } from '@/hooks/useChatSession';
import styles from './ChatInterface.module.css';

export default function ChatInterface({ evalData, onClose }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const { sessionId, messages, loading, error, sendMessage, clearError } = 
    useChatSession(evalData);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');

    try {
      await sendMessage(userMessage);
    } catch (err) {
      setInput(userMessage);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.chatHeader}>
        <h3>Ask Questions About Your Evaluation</h3>
        <button onClick={onClose} className={styles.closeBtn}>
          ✕
        </button>
      </div>

      {!sessionId && (
        <div className={styles.loadingState}>
          <p>Initializing chat session...</p>
        </div>
      )}

      {error && (
        <div className={styles.errorBanner}>
          <p>{error}</p>
          <button onClick={clearError}>Dismiss</button>
        </div>
      )}

      <div className={styles.messagesContainer}>
        {messages.length === 0 && sessionId && !loading && (
          <div className={styles.emptyState}>
            <p>No messages yet. Ask a question about your evaluation!</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`${styles.message} ${styles[msg.role]}`}>
            <div className={styles.messageBubble}>
              <div className={styles.messageContent}>{msg.content}</div>
              <div className={styles.messageTime}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className={`${styles.message} ${styles.assistant}`}>
            <div className={styles.messageBubble}>
              <div className={styles.loadingIndicator}>
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {sessionId && (
        <div className={styles.inputContainer}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your evaluation..."
            disabled={loading}
            className={styles.input}
            rows={2}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            className={styles.sendBtn}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
