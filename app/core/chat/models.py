"""
Chat Models - Simple In-Memory Chat for Post-Evaluation Q&A

No database persistence - chat exists only during the session.
Messages are kept in memory and discarded when the session ends.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """
    Single chat message in memory.
    
    Attributes:
        role: The sender role (user, assistant, or system)
        content: The message text content
        timestamp: When the message was created
    """
    role: Literal["user", "assistant", "system"] = Field(description="Message role/sender")
    content: str = Field(description="Message text content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message creation time")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM API calls."""
        return {
            "role": self.role,
            "content": self.content
        }


class ChatSession(BaseModel):
    """
    In-memory chat session for post-evaluation Q&A.
    
    Lives only during the evaluation review session. No database persistence.
    Contains the full conversation history and links to evaluation context.
    
    Attributes:
        eval_id: ID of the evaluation being discussed
        question_id: ID of the assignment question
        rubric_id: ID of the rubric used for evaluation
        submission_id: ID of the student submission
        messages: List of all messages in the conversation
        created_at: When the session was created
    """
    eval_id: str = Field(description="Evaluation ID")
    question_id: str = Field(description="Question ID")
    rubric_id: str = Field(description="Rubric ID")
    submission_id: str = Field(description="Submission ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    created_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    
    def add_message(self, role: str, content: str) -> ChatMessage:
        """
        Add a new message to the conversation.
        
        Args:
            role: The role of the message sender (user, assistant, or system)
            content: The message content
            
        Returns:
            ChatMessage: The created message
        """
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        return msg
    
    def get_conversation_history(self, max_messages: int = 20) -> List[Dict[str, str]]:
        """
        Get recent conversation history formatted for LLM API.
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [msg.to_dict() for msg in recent]
    
    def get_user_messages(self) -> List[ChatMessage]:
        """Get all user messages from the conversation."""
        return [msg for msg in self.messages if msg.role == "user"]
    
    def get_assistant_messages(self) -> List[ChatMessage]:
        """Get all assistant messages from the conversation."""
        return [msg for msg in self.messages if msg.role == "assistant"]
    
    def message_count(self) -> int:
        """Get total number of messages (excluding system message)."""
        return len([msg for msg in self.messages if msg.role != "system"])
