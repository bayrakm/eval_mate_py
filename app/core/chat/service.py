"""
Chat Service - In-Memory Conversational Interface for Evaluations

Provides temporary, session-based chat about evaluation results.
No persistence - chat history is deleted when the session ends.
"""

import os
import logging
from typing import Optional
from openai import OpenAI

from app.core.chat.models import ChatSession, ChatMessage
from app.core.store.repo import Repository
from app.core.models.schemas import EvalResult, Rubric, Question, Submission

logger = logging.getLogger(__name__)


class ChatService:
    """
    Handles temporary chat sessions about evaluations.
    
    Creates in-memory chat sessions that allow students to ask questions
    about their evaluation results. Sessions are not persisted and are
    discarded when the conversation ends.
    """
    
    def __init__(self, repo: Repository):
        """
        Initialize the chat service.
        
        Args:
            repo: Repository for accessing evaluations, rubrics, questions, and submissions
        """
        self.repo = repo
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        logger.info(f"ChatService initialized with model: {self.model}")
    
    def create_session(
        self,
        eval_id: str,
        question_id: str,
        rubric_id: str,
        submission_id: str
    ) -> ChatSession:
        """
        Create a new in-memory chat session for an evaluation.
        
        Args:
            eval_id: The evaluation ID to chat about
            question_id: The question ID
            rubric_id: The rubric ID used for evaluation
            submission_id: The submission ID that was evaluated
            
        Returns:
            ChatSession: A new chat session with system prompt initialized
            
        Raises:
            KeyError: If evaluation or related entities not found
        """
        logger.info(f"Creating chat session for evaluation: {eval_id}")
        
        # Create session
        session = ChatSession(
            eval_id=eval_id,
            question_id=question_id,
            rubric_id=rubric_id,
            submission_id=submission_id
        )
        
        # Build and add system message with full context
        system_prompt = self._build_system_prompt(
            eval_id=eval_id,
            question_id=question_id,
            rubric_id=rubric_id,
            submission_id=submission_id
        )
        session.add_message("system", system_prompt)
        
        logger.info(f"Chat session created with {len(session.messages)} messages")
        return session
    
    def send_message(
        self,
        session: ChatSession,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Send a user message and get AI assistant response.
        
        Args:
            session: The active chat session
            user_message: The user's question or message
            temperature: LLM temperature (0-1, higher = more creative)
            max_tokens: Maximum tokens in response
            
        Returns:
            str: The assistant's response text
        """
        logger.info(f"Processing message for eval {session.eval_id}")
        
        # Add user message to session
        session.add_message("user", user_message)
        
        # Get conversation history for LLM
        messages = session.get_conversation_history()
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to session
            session.add_message("assistant", assistant_response)
            
            logger.info(f"Assistant response generated ({len(assistant_response)} chars)")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Chat LLM error: {e}")
            error_msg = "I apologize, but I encountered an error processing your question. Please try again."
            session.add_message("assistant", error_msg)
            return error_msg
    
    def _build_system_prompt(
        self,
        eval_id: str,
        question_id: str,
        rubric_id: str,
        submission_id: str
    ) -> str:
        """
        Build comprehensive system prompt with evaluation context.
        
        Args:
            eval_id: Evaluation ID
            question_id: Question ID
            rubric_id: Rubric ID
            submission_id: Submission ID
            
        Returns:
            str: Complete system prompt with all context
        """
        # Load all entities
        try:
            eval_result = self.repo.get_eval_result(eval_id)
            rubric = self.repo.get_rubric(rubric_id)
            question = self.repo.get_question(question_id)
            submission = self.repo.get_submission(submission_id)
        except Exception as e:
            logger.error(f"Failed to load entities for system prompt: {e}")
            raise
        
        # Extract text content from documents
        question_text = self._extract_text_from_doc(question.canonical) if question.canonical else "N/A"
        submission_text = self._extract_text_from_doc(submission.canonical) if submission.canonical else "N/A"
        
        # Build rubric summary
        rubric_items_text = "\n".join([
            f"- **{item.title}** (Weight: {item.weight}): {item.description}"
            for item in rubric.items
        ])
        
        # Build evaluation summary from narrative fields
        eval_summary_parts = []
        
        if hasattr(eval_result, 'narrative_evaluation') and eval_result.narrative_evaluation:
            eval_summary_parts.append(f"**Overall Evaluation:**\n{eval_result.narrative_evaluation}")
        
        if hasattr(eval_result, 'narrative_strengths') and eval_result.narrative_strengths:
            eval_summary_parts.append(f"**Strengths:**\n{eval_result.narrative_strengths}")
        
        if hasattr(eval_result, 'narrative_gaps') and eval_result.narrative_gaps:
            eval_summary_parts.append(f"**Gaps/Areas for Improvement:**\n{eval_result.narrative_gaps}")
        
        if hasattr(eval_result, 'narrative_guidance') and eval_result.narrative_guidance:
            eval_summary_parts.append(f"**Guidance for Improvement:**\n{eval_result.narrative_guidance}")
        
        eval_summary = "\n\n".join(eval_summary_parts) if eval_summary_parts else "No detailed feedback available."
        
        # Truncate long texts for context window management
        question_text = question_text[:2000] + "..." if len(question_text) > 2000 else question_text
        submission_text = submission_text[:2000] + "..." if len(submission_text) > 2000 else submission_text
        
        # Build comprehensive system prompt
        system_prompt = f"""You are an educational AI assistant helping a student understand their assignment evaluation.

## ASSIGNMENT QUESTION (Ground Truth - What Was Asked)
{question_text}

## RUBRIC CRITERIA (Ground Truth - What's Expected)
{rubric_items_text}

## STUDENT'S SUBMISSION (Their Actual Work)
{submission_text}

## EVALUATION FEEDBACK PROVIDED
{eval_summary}

---

## YOUR ROLE
You are here to help the student understand their evaluation by:

1. **Answering questions** about the feedback they received
2. **Clarifying** why certain aspects were evaluated the way they were
3. **Explaining** rubric criteria and what was expected
4. **Helping them understand** specific gaps or issues identified
5. **Providing concrete examples** of how to improve based on the guidance
6. **Connecting** their work to rubric requirements
7. **Being encouraging** while being honest about areas for improvement

## GUIDELINES
- Base all answers on the rubric (ground truth) and their actual submission content
- Quote specific parts of the rubric or their work when it helps clarity
- **Do NOT change the evaluation or scores** - your job is to explain them
- Be constructive, educational, and supportive in tone
- Help them understand **WHY** things were evaluated as they were, not just **WHAT** the scores are
- Reference the "Guidance for Improvement" section when discussing how to do better
- Keep responses concise but thorough (aim for 100-300 words)
- Use clear, student-friendly language
- Focus on learning and growth, not just grades

Remember: You're a tutor helping them learn from their evaluation, not re-evaluating their work."""

        return system_prompt
    
    def _extract_text_from_doc(self, canonical_doc) -> str:
        """
        Extract text content from a CanonicalDoc.
        
        Args:
            canonical_doc: The document to extract text from
            
        Returns:
            str: Concatenated text from all text blocks
        """
        if not canonical_doc or not hasattr(canonical_doc, 'blocks'):
            return ""
        
        text_parts = []
        for block in canonical_doc.blocks:
            if hasattr(block, 'text') and block.text:
                text_parts.append(block.text)
        
        return "\n".join(text_parts)
