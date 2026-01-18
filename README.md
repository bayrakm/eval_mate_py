# EvalMate

Intelligent Student Assignment Feedback System.

EvalMate is an AI-powered assessment platform that evaluates student submissions against custom rubrics. It supports PDFs, DOCX, and images, produces structured feedback, and exposes REST API + CLI workflows.

## Key Features

- Multi-format document processing (PDF, DOCX, images)
- ADE-based rubric extraction (text, tables, images, transposed tables)
- GPT-powered evaluation with structured JSON output
- FastAPI REST API and CLI tools
- SQLite or JSON storage backends

## Project Structure

```
44_eval_mate/
|-- app/
|   |-- api/                      # FastAPI routes
|   |-- core/                     # Core logic (io, llm, models, store)
|   |-- ui/                       # CLI modules
|   |-- data/                     # SQLite + app-managed data
|-- data/
|   |-- assets/                   # Extracted visuals/images
|   |-- fusion/                   # Fusion context cache
|   |-- uploads/                  # Upload staging
|   |-- rubrics_extracted/        # ADE rubric JSON output
|-- evalmate_cli.py               # Unified CLI entry point
|-- pyproject.toml
|-- README.md
```

## Quick Start (Backend)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and VISION_AGENT_API_KEY

# 4. Run the CLI
uv run python evalmate_cli.py run

# Or start the API server
uv run uvicorn app.api.server:app --reload
```

## Environment Variables

```bash
OPENAI_API_KEY=sk-your-openai-key-here
VISION_AGENT_API_KEY=your-landingai-key-here
OPENAI_MODEL=gpt-4o
EVALMATE_STORAGE_MODE=sqlite  # or json
```

## Rubric Extraction (ADE)

Rubric files are parsed with LandingAI ADE and normalized into a structured JSON schema. The output is saved under `data/rubrics_extracted/` and also used to build `Rubric.items` for LLM evaluation.

Example workflow:

```bash
# Extract rubric JSON and save it
uv run python evalmate_cli.py rubric --file path/to/rubric.pdf
```

## REST API Overview

Rubrics:

```bash
curl -X POST "http://localhost:8000/rubrics/upload" \
  -F "file=@rubric.pdf" \
  -F "params={\"course\": \"CS101\", \"assignment\": \"A1\", \"version\": \"v1\"}"

curl "http://localhost:8000/rubrics/"
curl "http://localhost:8000/rubrics/{rubric_id}"
```

Questions:

```bash
curl -X POST "http://localhost:8000/questions/upload" \
  -F "file=@question.docx" \
  -F "params={\"title\": \"Problem 1\", \"rubric_id\": \"rubric_123\"}"

curl "http://localhost:8000/questions/?rubric_id=rubric_123"
curl "http://localhost:8000/questions/{question_id}"
```

Submissions:

```bash
curl -X POST "http://localhost:8000/submissions/upload" \
  -F "file=@submission.pdf" \
  -F "params={\"rubric_id\": \"rubric_123\", \"question_id\": \"question_456\", \"student_handle\": \"alice\"}"

curl "http://localhost:8000/submissions/?rubric_id=rubric_123"
curl "http://localhost:8000/submissions/{submission_id}"
```

Evaluation:

```bash
# Run evaluation
curl -X POST "http://localhost:8000/evaluate?rubric_id=R1&question_id=Q1&submission_id=S1"

# Get result
curl "http://localhost:8000/evaluate/result/S1"
```

## CLI Overview

```bash
# Upload and parse a rubric
uv run python -m app.ui.cli rubrics upload --file rubric.pdf --course CS101 --assignment A1 --version v1

# Run an evaluation
uv run python -m app.ui.cli_evaluate run --rubric-id R1 --question-id Q1 --submission-id S1
```

## Data Storage

- `app/data/db.sqlite3` stores the SQLite database (default backend).
- `app/data/rubrics/`, `app/data/questions/`, `app/data/submissions/`, `app/data/evals/` store JSON entities when `EVALMATE_STORAGE_MODE=json`.
- `data/rubrics_extracted/` stores ADE rubric JSON extractions.

## Frontend Notes

The frontend relies on the same API endpoints listed above. The API contracts remain compatible with the previous backend: upload rubric/question/submission, then evaluate with rubric + question + submission IDs.
