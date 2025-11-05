"use client";

import { useState, useCallback } from "react";

export function useAppState() {
  const [state, setState] = useState({
    selectedRubric: null,
    selectedQuestion: null,
    selectedSubmission: null,
    fusion: null,
    result: null,
    messages: [],
    loading: "idle",
  });

  const addMessage = useCallback((content, type = "assistant") => {
    setState((prev) => ({
      ...prev,
      messages: [
        ...prev.messages,
        {
          id: Date.now().toString(),
          type,
          content,
          timestamp: new Date(),
        },
      ],
    }));
  }, []);

  const setLoading = useCallback((loading) => {
    setState((prev) => ({ ...prev, loading }));
  }, []);

  const resetSelections = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedQuestion: null,
      selectedSubmission: null,
      fusion: null,
      result: null,
    }));
  });

  return {
    state,
    setState,
    addMessage,
    setLoading,
    resetSelections,
  };
}
