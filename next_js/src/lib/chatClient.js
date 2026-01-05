const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const chatAPI = {
  async createSession(evalData) {
    const url = `${API_BASE_URL}/chat/sessions`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        eval_id: evalData.eval_id,
        question_id: evalData.question_id,
        rubric_id: evalData.rubric_id,
        submission_id: evalData.submission_id,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[Chat] Error response:", errorText);
      throw new Error(
        `Failed to create chat session: ${response.status} - ${errorText}`
      );
    }

    return await response.json();
  },

  async sendMessage(sessionId, message, temperature = 0.7, maxTokens = 1000) {
    const response = await fetch(
      `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          temperature,
          max_tokens: maxTokens,
        }),
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Chat session expired");
      }
      throw new Error(`Failed to send message: ${response.status}`);
    }

    return await response.json();
  },

  async getHistory(sessionId, maxMessages = 20) {
    const response = await fetch(
      `${API_BASE_URL}/chat/sessions/${sessionId}/history?max_messages=${maxMessages}`
    );

    if (!response.ok) {
      throw new Error(`Failed to load chat history: ${response.status}`);
    }

    return await response.json();
  },

  async deleteSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to delete session: ${response.status}`);
    }

    return await response.json();
  },
};
