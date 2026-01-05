import { useState, useCallback, useEffect } from "react";
import { chatAPI } from "@/lib/chatClient";

export const useChatSession = (evalData) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (evalData) {
      createSession();
    }
  }, [evalData?.eval_id]);

  useEffect(() => {
    return () => {
      if (sessionId) {
        chatAPI
          .deleteSession(sessionId)
          .catch((err) =>
            console.error("Failed to cleanup chat session:", err)
          );
      }
    };
  }, [sessionId]);

  const createSession = useCallback(async () => {
    try {
      setError(null);
      const data = await chatAPI.createSession(evalData);
      setSessionId(data.session_id || data.eval_id);
      setMessages([]);
    } catch (err) {
      console.error("[useChatSession] Failed to create chat session:", err);
      setError(err.message);
    }
  }, [evalData]);

  const loadHistory = useCallback(async () => {
    if (!sessionId) return;

    try {
      setError(null);
      const data = await chatAPI.getHistory(sessionId);
      setMessages(data.messages);
    } catch (err) {
      setError(err.message);
      console.error("Failed to load chat history:", err);
    }
  }, [sessionId]);

  const sendMessage = useCallback(
    async (userMessage) => {
      if (!sessionId || !userMessage.trim()) return;

      try {
        setError(null);
        setLoading(true);

        const userMsg = {
          role: "user",
          content: userMessage,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg]);

        const assistantMsg = await chatAPI.sendMessage(sessionId, userMessage);
        setMessages((prev) => [...prev, assistantMsg]);

        return assistantMsg;
      } catch (err) {
        setError(err.message);
        console.error("Failed to send message:", err);
        setMessages((prev) => prev.slice(0, -1));
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    sessionId,
    messages,
    loading,
    error,
    createSession,
    loadHistory,
    sendMessage,
    clearError,
  };
};
