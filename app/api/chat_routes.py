"""
Chat API Routes for Post-Evaluation Q&A

Provides endpoints for creating chat sessions and sending messages
about evaluation results. Sessions are temporary and not persisted.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.chat.service import ChatService
from app.core.chat.models import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel
from app.core.store.repo import get_repository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response Models
class ChatSessionCreate(BaseModel):
    """Request to create a new chat session."""
    eval_id: str = Field(description="Evaluation ID to chat about")
    question_id: str = Field(description="Question ID")
    rubric_id: str = Field(description="Rubric ID")
    submission_id: str = Field(description="Submission ID")


class ChatMessageRequest(BaseModel):
    """Request to send a message in a chat session."""
    message: str = Field(description="User's question or message")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Max response tokens")


class ChatMessageResponse(BaseModel):
    """Response containing assistant's message."""
    role: str = Field(description="Message role (assistant)")
    content: str = Field(description="Assistant's response text")
    timestamp: str = Field(description="Message timestamp")


class ChatSessionResponse(BaseModel):
    """Response containing session information."""
    session_id: str = Field(description="Session ID for future requests")
    eval_id: str
    question_id: str
    rubric_id: str
    submission_id: str
    message_count: int = Field(description="Number of messages (excluding system)")
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Response containing conversation history."""
    messages: List[Dict[str, Any]] = Field(description="List of messages with role and content")
    total_count: int = Field(description="Total number of messages")


# In-memory session storage (sessions are temporary)
# Key: session_id (generated), Value: ChatSessionModel
_active_sessions: Dict[str, ChatSessionModel] = {}


def _generate_session_id() -> str:
    """Generate a simple session ID for temporary storage."""
    import uuid
    return f"session_{uuid.uuid4().hex[:12]}"


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(request: ChatSessionCreate):
    """
    Create a new chat session for an evaluation.
    
    This creates an in-memory chat session that allows users to ask questions
    about their evaluation results. The session includes full context from the
    evaluation, rubric, question, and submission.
    
    **Note**: Sessions are not persisted and will be lost when the server restarts.
    """
    try:
        repo = get_repository()
        chat_service = ChatService(repo)
        
        # Create session
        session = chat_service.create_session(
            eval_id=request.eval_id,
            question_id=request.question_id,
            rubric_id=request.rubric_id,
            submission_id=request.submission_id
        )
        
        # Store in memory with generated ID
        session_id = _generate_session_id()
        _active_sessions[session_id] = session
        
        logger.info(f"Created chat session {session_id} for eval {request.eval_id}")
        
        return ChatSessionResponse(
            session_id=session_id,
            eval_id=session.eval_id,
            question_id=session.question_id,
            rubric_id=session.rubric_id,
            submission_id=session.submission_id,
            message_count=session.message_count(),
            created_at=session.created_at.isoformat()
        )
        
    except KeyError as e:
        logger.error(f"Entity not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(session_id: str, request: ChatMessageRequest):
    """
    Send a message in a chat session and get AI response.
    
    The assistant will respond based on the full evaluation context including
    the rubric criteria, question, student submission, and evaluation feedback.
    
    **Parameters:**
    - `session_id`: The session ID returned from session creation
    - `message`: The user's question or message
    - `temperature`: LLM temperature (0.0-1.0, default 0.7)
    - `max_tokens`: Maximum tokens in response (100-4000, default 1000)
    """
    try:
        # Get session from memory
        session = _active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        
        # Get chat service
        repo = get_repository()
        chat_service = ChatService(repo)
        
        # Send message and get response
        response_text = chat_service.send_message(
            session=session,
            user_message=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Get the last assistant message
        assistant_messages = session.get_assistant_messages()
        if assistant_messages:
            last_msg = assistant_messages[-1]
            return ChatMessageResponse(
                role=last_msg.role,
                content=last_msg.content,
                timestamp=last_msg.timestamp.isoformat()
            )
        else:
            # Fallback if no message found
            return ChatMessageResponse(
                role="assistant",
                content=response_text,
                timestamp=datetime.now().isoformat()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, max_messages: int = 20):
    """
    Get conversation history for a session.
    
    Returns recent messages from the conversation (excluding the system prompt).
    
    **Parameters:**
    - `session_id`: The session ID
    - `max_messages`: Maximum number of recent messages to return (default 20)
    """
    try:
        session = _active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        
        # Get messages (exclude system message)
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages[1:]  # Skip system message
        ]
        
        # Limit to max_messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        return ChatHistoryResponse(
            messages=recent_messages,
            total_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session from memory.
    
    This is useful for cleanup, though sessions will be automatically lost
    when the server restarts anyway.
    """
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        logger.info(f"Deleted chat session {session_id}")
        return {"status": "success", "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


# Add helper endpoint to check active sessions (for debugging)
@router.get("/sessions")
async def list_active_sessions():
    """
    List all active chat sessions (for debugging).
    
    **Note**: This is a debug endpoint and should be removed in production.
    """
    return {
        "active_sessions": len(_active_sessions),
        "session_ids": list(_active_sessions.keys())
    }
