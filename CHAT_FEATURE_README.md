# Chat Feature Documentation for Frontend Implementation

## Overview

The chat feature allows students to ask questions about their evaluation results immediately after an evaluation is completed. The chat session is **temporary** and **in-memory only** - no database persistence. When the session ends or the server restarts, the chat history is deleted.

## Architecture

### Backend Components

1. **Chat Models** (`app/core/chat/models.py`)
   - `ChatMessage`: Individual message with role (user/assistant/system), content, and timestamp
   - `ChatSession`: In-memory session containing conversation history and links to evaluation context

2. **Chat Service** (`app/core/chat/service.py`)
   - `ChatService`: Handles session creation and message processing
   - Integrates with OpenAI GPT-4o for AI responses
   - Builds comprehensive system prompts with full evaluation context

3. **API Routes** (`app/api/chat_routes.py`)
   - RESTful endpoints for chat functionality
   - Session management in server memory
   - Session IDs generated on-the-fly

### Context Provided to AI

The AI assistant has access to:
- **Rubric criteria** (ground truth - what's expected)
- **Assignment question** (ground truth - what was asked)
- **Student submission** (their actual work)
- **Evaluation feedback** (narrative evaluation, strengths, gaps, guidance)
- **Conversation history** (previous questions and answers)

## API Endpoints

### Base URL
```
http://localhost:8000/chat
```

### 1. Create Chat Session

**POST** `/chat/sessions`

Creates a new chat session for an evaluation.

**Request Body:**
```json
{
  "eval_id": "eval_1234567890_abc123",
  "question_id": "ques_1234567890_xyz789",
  "rubric_id": "rubr_1234567890_def456",
  "submission_id": "subm_1234567890_ghi789"
}
```

**Response (200 OK):**
```json
{
  "eval_id": "eval_1234567890_abc123",
  "question_id": "ques_1234567890_xyz789",
  "rubric_id": "rubr_1234567890_def456",
  "submission_id": "subm_1234567890_ghi789",
  "message_count": 0,
  "created_at": "2025-12-25T10:30:00"
}
```

**Response Headers:**
- `session_id` is returned in the response (stored in backend memory)

**Error Responses:**
- `404`: Evaluation or related entity not found
- `500`: Server error creating session

---

### 2. Send Message

**POST** `/chat/sessions/{session_id}/messages`

Send a user message and receive AI assistant response.

**Path Parameters:**
- `session_id`: Session ID from session creation (e.g., `session_abc123def456`)

**Request Body:**
```json
{
  "message": "Why did I lose points on the algorithm section?",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Request Fields:**
- `message` (required): User's question or message
- `temperature` (optional): LLM creativity (0.0-1.0, default: 0.7)
- `max_tokens` (optional): Max response length (100-4000, default: 1000)

**Response (200 OK):**
```json
{
  "role": "assistant",
  "content": "Based on the rubric criteria for algorithms...",
  "timestamp": "2025-12-25T10:31:15"
}
```

**Error Responses:**
- `404`: Session not found or expired
- `500`: Error processing message

---

### 3. Get Conversation History

**GET** `/chat/sessions/{session_id}/history?max_messages=20`

Retrieve conversation history (excludes system prompt).

**Path Parameters:**
- `session_id`: Session ID

**Query Parameters:**
- `max_messages` (optional): Max recent messages to return (default: 20)

**Response (200 OK):**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Why did I lose points?",
      "timestamp": "2025-12-25T10:31:00"
    },
    {
      "role": "assistant",
      "content": "Based on the rubric...",
      "timestamp": "2025-12-25T10:31:15"
    }
  ],
  "total_count": 2
}
```

---

### 4. Delete Session

**DELETE** `/chat/sessions/{session_id}`

Delete a chat session from memory (cleanup).

**Path Parameters:**
- `session_id`: Session ID

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Session session_abc123 deleted"
}
```

---

### 5. List Active Sessions (Debug)

**GET** `/chat/sessions`

List all active sessions (for debugging only).

**Response (200 OK):**
```json
{
  "active_sessions": 3,
  "session_ids": ["session_abc123", "session_def456", "session_ghi789"]
}
```

## Frontend Implementation Guide

### Workflow

1. **After Evaluation Completes:**
   ```javascript
   // User just received their evaluation results
   const evalResult = { 
     id: "eval_123...",
     question_id: "ques_456...",
     rubric_id: "rubr_789...",
     submission_id: "subm_012..."
   };
   ```

2. **Create Chat Session:**
   ```javascript
   const response = await fetch('http://localhost:8000/chat/sessions', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       eval_id: evalResult.id,
       question_id: evalResult.question_id,
       rubric_id: evalResult.rubric_id,
       submission_id: evalResult.submission_id
     })
   });
   
   const sessionData = await response.json();
   const sessionId = sessionData.session_id; // Store this!
   ```

3. **Display Chat Interface:**
   ```jsx
   // Show chat UI component
   <ChatInterface 
     sessionId={sessionId}
     evalId={evalResult.id}
   />
   ```

4. **Send User Messages:**
   ```javascript
   async function sendMessage(sessionId, userMessage) {
     const response = await fetch(
       `http://localhost:8000/chat/sessions/${sessionId}/messages`,
       {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           message: userMessage,
           temperature: 0.7,
           max_tokens: 1000
         })
       }
     );
     
     const assistantReply = await response.json();
     return assistantReply.content;
   }
   ```

5. **Display Conversation:**
   ```javascript
   async function loadHistory(sessionId) {
     const response = await fetch(
       `http://localhost:8000/chat/sessions/${sessionId}/history?max_messages=50`
     );
     
     const history = await response.json();
     return history.messages; // Array of {role, content, timestamp}
   }
   ```

6. **Clean Up When Done:**
   ```javascript
   async function endChat(sessionId) {
     await fetch(`http://localhost:8000/chat/sessions/${sessionId}`, {
       method: 'DELETE'
     });
   }
   ```

### Example React Component

```jsx
import React, { useState, useEffect } from 'react';

function ChatInterface({ sessionId, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, [sessionId]);

  async function loadHistory() {
    try {
      const res = await fetch(
        `http://localhost:8000/chat/sessions/${sessionId}/history`
      );
      const data = await res.json();
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  }

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    // Add user message to UI immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }]);

    try {
      const res = await fetch(
        `http://localhost:8000/chat/sessions/${sessionId}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage })
        }
      );

      const assistantReply = await res.json();

      // Add assistant response to UI
      setMessages(prev => [...prev, assistantReply]);
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Error sending message. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleClose() {
    // Delete session on close
    await fetch(`http://localhost:8000/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    });
    onClose();
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Ask Questions About Your Evaluation</h3>
        <button onClick={handleClose}>Close</button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-role">
              {msg.role === 'user' ? 'You' : 'AI Assistant'}
            </div>
            <div className="message-content">{msg.content}</div>
            <div className="message-time">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && <div className="loading">Thinking...</div>}
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask a question about your evaluation..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

## Important Notes

### Session Lifecycle
- **Sessions are NOT persisted** - they exist only in server memory
- **Server restart = all sessions deleted**
- **Frontend should handle 404 errors** when session expires
- **Recommend**: Show warning when user tries to refresh page

### Best Practices

1. **Create session immediately after evaluation**
   ```javascript
   // In your evaluation results component
   useEffect(() => {
     if (evaluationComplete) {
       createChatSession();
     }
   }, [evaluationComplete]);
   ```

2. **Store session ID in component state (not localStorage)**
   ```javascript
   // Don't persist - session won't survive page refresh anyway
   const [chatSessionId, setChatSessionId] = useState(null);
   ```

3. **Handle errors gracefully**
   ```javascript
   if (response.status === 404) {
     alert('Chat session expired. Please start a new evaluation.');
     redirectToEvaluationList();
   }
   ```

4. **Delete session on component unmount**
   ```javascript
   useEffect(() => {
     return () => {
       if (sessionId) {
         fetch(`/chat/sessions/${sessionId}`, { method: 'DELETE' });
       }
     };
   }, [sessionId]);
   ```

### Security Considerations

- **No authentication** in current implementation
- **CORS is wide open** (`allow_origins=["*"]`)
- **TODO for production**: Add user authentication and session validation
- **Rate limiting**: Consider adding rate limits to prevent abuse

### Performance

- **Context size**: System prompt includes full evaluation context (~2000 chars)
- **Token limits**: Default max_tokens=1000 per response
- **History limit**: Default max 20 messages in history
- **Concurrent sessions**: Limited only by server memory

## Testing the API

### Using cURL

```bash
# 1. Create session
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "eval_id": "eval_1735128670999_uRk9lQ",
    "question_id": "ques_1735128668829_pu1W7w",
    "rubric_id": "rubr_1735128668645_8XYunA",
    "submission_id": "subm_1735128669187_2AcbTw"
  }'

# 2. Send message
curl -X POST http://localhost:8000/chat/sessions/session_abc123/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Why did I get this score?"
  }'

# 3. Get history
curl http://localhost:8000/chat/sessions/session_abc123/history

# 4. Delete session
curl -X DELETE http://localhost:8000/chat/sessions/session_abc123
```

### Using Python

```python
import requests

# Create session
response = requests.post(
    'http://localhost:8000/chat/sessions',
    json={
        'eval_id': 'eval_123...',
        'question_id': 'ques_456...',
        'rubric_id': 'rubr_789...',
        'submission_id': 'subm_012...'
    }
)
session_id = response.json()['session_id']

# Send message
response = requests.post(
    f'http://localhost:8000/chat/sessions/{session_id}/messages',
    json={'message': 'Why did I lose points?'}
)
print(response.json()['content'])

# Get history
response = requests.get(
    f'http://localhost:8000/chat/sessions/{session_id}/history'
)
print(response.json()['messages'])

# Delete session
requests.delete(f'http://localhost:8000/chat/sessions/{session_id}')
```

## CLI Testing

The chat feature is also available in the CLI for testing:

```bash
# Run evaluation with chat enabled (default)
uv run evalmate_cli.py test

# Run evaluation without chat
uv run evalmate_cli.py test --no-chat

# After evaluation, you can ask questions:
# > Why did I get this score?
# > Can you explain the rubric criteria?
# > How can I improve my submission?
# > exit  (to end chat)
```

## Questions?

Contact the backend team if you need:
- Additional API endpoints
- Different response formats
- Session persistence (requires database changes)
- Authentication/authorization
- Rate limiting configuration
