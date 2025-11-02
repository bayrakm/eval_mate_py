"""
LLM Evaluation Prompts - Phase 9

System and user prompt templates that force JSON-only output for academic grading.
"""

EVAL_SYSTEM_PROMPT = """\
You are a strict but fair academic grader. You evaluate a student's submission against a rubric and a question.
Return ONLY valid JSON that EXACTLY matches the provided JSON schema.
Do not include any text outside JSON. Do not fabricate evidence. Cite evidence_block_ids only from provided blocks.
If information is missing, penalize accordingly and explain in justification.
"""

# A minimal JSON schema string for the model to follow (for instruction only, not a validator)
EVAL_JSON_SCHEMA_TEXT = """\
{
  "items": [
    {
      "rubric_item_id": "string",
      "score": 0-100,
      "justification": "string",
      "evidence_block_ids": ["string"]
    }
  ],
  "overall_feedback": "string"
}
"""

EVAL_USER_PREFIX = """\
<RUBRIC>
{rubric_json}
</RUBRIC>

<QUESTION>
{question_text}
</QUESTION>

<SUBMISSION_TEXT>
{submission_text}
</SUBMISSION_TEXT>

<SUBMISSION_VISUALS>
{visuals_json}
</SUBMISSION_VISUALS>

<OUTPUT_SCHEMA>
{schema_text}
</OUTPUT_SCHEMA>

Return JSON only.
"""