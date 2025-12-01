# EvalMate 🎓

**Intelligent Student Assignment Feedback System**

EvalMate is a comprehensive AI-powered assessment platform that automatically evaluates student submissions against custom rubrics using Large Language Model technology. It supports multiple document formats, provides detailed feedback, and offers both web interface and API access.

## 🚀 Key Features

- **🔍 Multi-format Document Processing**: PDF, DOCX, and image files
- **🤖 AI-Powered Evaluation**: GPT-4 powered assessment with detailed feedback
- **📋 Smart Rubric Processing**: Automatic rubric parsing from uploaded documents
- **🎯 Structured Scoring**: Criterion-based evaluation with evidence citations
- **🌐 Multiple Interfaces**: 
  - **Web UI** (Next.js) - Modern React-based interface with Mantine components
  - **REST API** (FastAPI) - Full-featured backend API with OpenAPI docs
  - **CLI Tools** - Unified CLI (`evalmate_cli.py`) and specialized modules
- **💾 Flexible Storage**: SQLite database with optional JSON backup
- **📊 Rich Export Options**: JSON and CSV result formats
- **🖼️ Visual Content Support**: Image extraction, OCR, and multimodal processing
- **🔧 Enterprise Ready**: Robust error handling and scalable architecture

## 📁 Project Architecture

```
44_eval_mate/
├── 🎯 Frontend (Next.js 15)
│   └── next_js/
│       ├── src/
│       │   ├── app/                    # Next.js App Router
│       │   │   ├── page.js             # Home page
│       │   │   ├── layout.js           # Root layout
│       │   │   ├── globals.css         # Global styles
│       │   │   ├── login/              # Authentication pages
│       │   │   └── api/                # API routes
│       │   │       └── auth/           # NextAuth.js handlers
│       │   │
│       │   ├── components/             # React components
│       │   │   ├── actions/            # Action buttons
│       │   │   │   └── ActionButtons.js
│       │   │   ├── auth/               # Authentication
│       │   │   │   ├── LoginForm.js
│       │   │   │   └── ProtectedRoute.js
│       │   │   ├── display/            # Results display
│       │   │   │   ├── MessageList.js
│       │   │   │   ├── ProgressIndicator.js
│       │   │   │   ├── ResultsPanel.js
│       │   │   │   └── ScoreCard.js
│       │   │   ├── layout/             # Layout components
│       │   │   │   ├── AppLayout.js
│       │   │   │   └── Sidebar.js
│       │   │   ├── resources/          # Resource selectors
│       │   │   │   ├── QuestionSelector.js
│       │   │   │   ├── RubricSelector.js
│       │   │   │   └── SubmissionSelector.js
│       │   │   └── upload/             # File upload forms
│       │   │       ├── UploadQuestion.js
│       │   │       ├── UploadRubric.js
│       │   │       └── UploadSubmission.js
│       │   │
│       │   ├── hooks/                  # Custom React hooks
│       │   │   └── useAppState.js
│       │   │
│       │   └── lib/                    # Utilities
│       │       ├── apiClient.js        # Backend API client
│       │       ├── constants.js        # App constants
│       │       └── utils.js            # Helper functions
│       │
│       ├── package.json                # Frontend dependencies
│       └── next.config.js              # Next.js configuration
│
├── 🔧 Backend (FastAPI + Python 3.12)
│   ├── app/
│   │   ├── main.py                     # Application entry point
│   │   ├── config.py                   # Configuration management
│   │   │
│   │   ├── api/                        # REST API layer
│   │   │   ├── server.py               # FastAPI server setup
│   │   │   ├── schemas.py              # API request/response schemas
│   │   │   ├── evaluate_routes.py      # Evaluation endpoints
│   │   │   └── fusion_routes.py        # Fusion context endpoints
│   │   │
│   │   ├── core/                       # Core business logic
│   │   │   ├── types.py                # Type definitions
│   │   │   ├── visual_extraction.py    # Image & table extraction
│   │   │   │
│   │   │   ├── io/                     # Document processing
│   │   │   │   ├── ingest.py           # Multi-format ingestion
│   │   │   │   ├── rubric_parser.py    # Rubric parsing
│   │   │   │   ├── captioning.py       # Image captioning
│   │   │   │   ├── caption_heuristics.py # Caption strategies
│   │   │   │   ├── ocr.py              # OCR processing
│   │   │   │   ├── pdf_utils.py        # PDF utilities
│   │   │   │   ├── docx_utils.py       # DOCX utilities
│   │   │   │   ├── table_extraction.py # Table extraction
│   │   │   │   └── text_utils.py       # Text processing
│   │   │   │
│   │   │   ├── fusion/                 # Context assembly
│   │   │   │   ├── builder.py          # FusionContext builder
│   │   │   │   ├── schema.py           # Fusion schemas
│   │   │   │   └── utils.py            # Fusion utilities
│   │   │   │
│   │   │   ├── llm/                    # AI evaluation engine
│   │   │   │   ├── evaluator.py        # Main evaluator
│   │   │   │   ├── prompts.py          # Prompt templates
│   │   │   │   ├── model_api.py        # OpenAI integration
│   │   │   │   ├── model_config.py     # Model configuration
│   │   │   │   ├── json_guard.py       # JSON validation
│   │   │   │   ├── rate_limit.py       # Rate limiting
│   │   │   │   ├── chunking.py         # Content chunking
│   │   │   │   └── multimodal_context.py # Multimodal handling
│   │   │   │
│   │   │   ├── models/                 # Data schemas
│   │   │   │   ├── schemas.py          # Pydantic models
│   │   │   │   ├── ids.py              # ID generation
│   │   │   │   └── validators.py       # Custom validators
│   │   │   │
│   │   │   └── store/                  # Data persistence
│   │   │       ├── repo.py             # Repository interface
│   │   │       ├── sqlite_store.py     # SQLite backend
│   │   │       ├── json_store.py       # JSON file backend
│   │   │       └── backend_selector.py # Storage selection
│   │   │
│   │   ├── ui/                         # CLI interfaces
│   │   │   ├── cli.py                  # Main CLI (legacy)
│   │   │   ├── cli_fusion.py           # Fusion CLI commands
│   │   │   └── cli_evaluate.py         # Evaluation CLI commands
│   │   │
│   │   └── tests/                      # Test suite
│   │
│   └── evalmate_cli.py                 # Unified CLI entry point
│
├── 📁 Data Storage
│   ├── app/data/                       # Backend data (managed by config.py)
│   │   ├── db.sqlite3                  # SQLite database
│   │   ├── rubrics/                    # Uploaded rubrics
│   │   ├── questions/                  # Assignment questions
│   │   ├── submissions/                # Student submissions
│   │   └── evals/                      # Evaluation results
│   │
│   └── data/                           # Root data directory
│       ├── assets/                     # Extracted visuals/images
│       ├── fusion/                     # Fusion context cache
│       ├── uploads/                    # File upload staging
│       │   ├── rubrics/
│       │   ├── questions/
│       │   └── submissions/
│       ├── rubrics/                    # Additional rubrics
│       ├── questions/                  # Additional questions
│       └── submissions/                # Additional submissions
│
└── 🧪 Configuration & Build
    ├── pyproject.toml                  # Python dependencies
    ├── uv.lock                         # UV lock file
    ├── .env.example                    # Environment template
    ├── .gitignore                      # Git ignore rules
    └── README.md                       # This file
```

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd 44_eval_mate

# 2. Install backend dependencies
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the unified CLI (easiest way to get started)
uv run python evalmate_cli.py run

# OR start the API server
uv run uvicorn app.api.server:app --reload

# OR setup frontend (optional)
cd next_js
npm install
npm run dev
```

## 🔧 Technology Stack

### Backend
- **Python 3.12+** - Core language
- **FastAPI** - Modern web framework for APIs
- **Pydantic** - Data validation and settings management
- **SQLite** - Database (with optional JSON storage)
- **OpenAI API** - GPT-4 powered evaluation
- **UV** - Fast Python package installer
- **Typer** - CLI interface framework

### Frontend
- **Next.js 15** - React framework with App Router
- **React 18** - UI library
- **Mantine UI** - Component library
- **NextAuth.js** - Authentication
- **Axios** - HTTP client

### Document Processing
- **PDFPlumber** - PDF text extraction
- **python-docx** - DOCX file handling
- **Camelot & Tabula** - Table extraction
- **PyMuPDF (fitz)** - PDF rendering and image extraction
- **Pillow** - Image processing
- **pytesseract** - OCR capabilities
- **OpenCV** - Computer vision operations

## �🛠️ Installation & Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- OpenAI API key

### 1. Clone and Setup Backend

```bash
git clone <repository-url>
cd 44_eval_mate

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies with uv (recommended)
pip install uv
uv sync

# Or install with pip
pip install -e .
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
OPENAI_API_KEY=sk-your-openai-key-here
EVALMATE_STORAGE_MODE=sqlite
OPENAI_MODEL=gpt-4o
```

### 3. Initialize Database

```bash
# Initialize SQLite database and data directories
uv run python app/main.py
```

### 3. Setup Frontend (Optional)

```bash
cd next_js

# Install dependencies
npm install

# Build for production
npm run build

# Or run development server
npm run dev
```

## 🚀 Deployment Options

### Option 1: Backend API Server

```bash
# Start FastAPI server
uv run uvicorn app.api.server:app --host 0.0.0.0 --port 8000

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### Option 2: Full-Stack with Frontend

```bash
# Terminal 1: Start backend
uv run uvicorn app.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd next_js
npm run start
```

### Option 3: CLI Only

```bash
# Check system status
uv run python evalmate_cli.py status

# Run interactive evaluation
uv run python evalmate_cli.py run
```

All data is stored in two main directories:

**Backend Data (`app/data/`):**
- `app/data/db.sqlite3` - SQLite database (when using SQLite mode)
- `app/data/rubrics/` - Grading rubrics
- `app/data/questions/` - Assignment questions
- `app/data/submissions/` - Student submissions
- `app/data/evals/` - Evaluation results

**Root Data (`data/`):**
- `data/assets/` - Extracted images and visual content
- `data/fusion/` - Cached fusion contexts
- `data/uploads/` - File upload staging area

## 🧪 Testing

Run the complete test suite:

```bash
pytest app/tests/ -v
```

Run with coverage:

```bash
pytest app/tests/ --cov=app --cov-report=html
```

## � API & CLI Usage

### REST API Server

Start the FastAPI server:

```bash
# Start the server
uvicorn app.api.server:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

#### API Endpoints

**Rubrics:**

```bash
# Upload a rubric file
curl -X POST "http://localhost:8000/rubrics/upload" \
  -F "file=@rubric.pdf" \
  -F "params={\"course\": \"CS101\", \"assignment\": \"A1\", \"version\": \"v1\"}"

# List all rubrics
curl "http://localhost:8000/rubrics/"

# Get specific rubric
curl "http://localhost:8000/rubrics/{rubric_id}"
```

**Questions:**

```bash
# Upload a question file
curl -X POST "http://localhost:8000/questions/upload" \
  -F "file=@question.docx" \
  -F "params={\"title\": \"Problem 1\", \"rubric_id\": \"rubric_123\"}"

# List questions (with optional filtering)
curl "http://localhost:8000/questions/?rubric_id=rubric_123"

# Get specific question
curl "http://localhost:8000/questions/{question_id}"
```

**Submissions:**

```bash
# Upload a submission file
curl -X POST "http://localhost:8000/submissions/upload" \
  -F "file=@submission.pdf" \
  -F "params={\"rubric_id\": \"rubric_123\", \"question_id\": \"question_456\", \"student_handle\": \"alice\"}"

# List submissions (with optional filtering)
curl "http://localhost:8000/submissions/?student=alice&rubric_id=rubric_123"

# Get specific submission
curl "http://localhost:8000/submissions/{submission_id}"
```

### Command Line Interface

#### Global Commands

```bash
# Show help
python -m app.ui.cli --help

# Show rubric commands
python -m app.ui.cli rubrics --help
```

#### Rubric Management

```bash
# Upload and parse a rubric
python -m app.ui.cli rubrics upload --file rubric.pdf --course CS101 --assignment A1 --version v1

# List all rubrics
python -m app.ui.cli rubrics list

# Get rubric details
python -m app.ui.cli rubrics get --id rubric_123
```

#### Question Management

```bash
# Upload a question
python -m app.ui.cli questions upload --file question.docx --title "Problem 1" --rubric-id rubric_123

# List questions (optionally filtered by rubric)
python -m app.ui.cli questions list --rubric-id rubric_123

# Get question details
python -m app.ui.cli questions get --id question_456
```

#### Submission Management

```bash
# Upload a submission
python -m app.ui.cli submissions upload --file submission.pdf --rubric-id rubric_123 --question-id question_456 --student alice

# List submissions (optionally filtered)
python -m app.ui.cli submissions list --student alice --rubric-id rubric_123

# Get submission details
python -m app.ui.cli submissions get --id submission_789
```

## � Core Features

### Document Processing

- **Multi-format Ingestion**: PDF, DOCX, and image files
- **Text Extraction**: Clean text extraction with preprocessing
- **Visual Element Detection**: Extract images and tables from documents
- **OCR Support**: Text extraction from images and visual content

### Rubric Management

- **Intelligent Parsing**: Handle bulleted lists, numbered lists, and tables
- **Weight Normalization**: Automatic percentage/point conversion
- **Criterion Mapping**: Smart classification of evaluation criteria
- **Multi-format Support**: PDF and DOCX rubric documents

### Evaluation Engine

- **OpenAI Integration**: GPT-4o multimodal evaluation
- **Per-criterion Assessment**: Individual scoring with evidence
- **Weighted Scoring**: Automatic total score calculation
- **JSON Output**: Structured evaluation results

### Storage & API

- **Dual Backend**: SQLite or JSON file storage
- **REST API**: Complete FastAPI endpoints
- **CLI Interface**: Rich command-line tools
- **File Management**: Organized upload and asset storage

## 🔧 System Configuration

### Environment Variables

```bash
# OpenAI API (required for evaluation)
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4o  # optional override

# Optional: OpenAI Organization ID
export OPENAI_ORG_ID=org-your-org-id

# Storage backend (default: sqlite)
export EVALMATE_STORAGE_MODE=sqlite  # or 'json'

# Optional: Logging configuration
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Optional: Data directories (defaults to ./data and ./data/assets)
export DATA_DIR=data
export ASSETS_DIR=data/assets
```

### Storage Backends

- **SQLite** (default): Single file database with full SQL support
- **JSON**: File-based storage for simple deployment scenarios

### Phase 1: Robust Data Schemas ✅

- [x] **Pydantic Models**: Comprehensive type-safe schemas for all entities
- [x] **ID Management**: Deterministic URL-safe ID generation and validation
- [x] **Cross-Model Validation**: Business rule enforcement and data integrity
- [x] **JSON Serialization**: Round-trip compatible serialization utilities
- [x] **Comprehensive Testing**: Validation and serialization test suites

#### Phase 1 Schemas & Models:

- **Core Blocks**: `VisualBlock`, `DocBlock` with strict content validation
- **Documents**: `CanonicalDoc` with structured content blocks
- **Evaluation**: `Rubric`, `RubricItem` with weight validation
- **Assignment**: `Question`, `Submission` with referential integrity
- **Results**: `EvalResult`, `ScoreItem` with evidence tracking

#### Phase 1 Testing:

Run the complete schema test suite:

```bash
# Test round-trip JSON serialization
python app/tests/test_schemas_roundtrip.py

# Test validation rules (pass/fail scenarios)
python app/tests/test_validations.py

# Run all tests with pytest (once dependencies installed)
python -m pytest app/tests/ -v
```

### Phase 2: Document Ingestion ✅

- [x] **PDF Text Extraction**: Extract and clean text from PDF files using pdfplumber
- [x] **DOCX Processing**: Parse Word documents and extract paragraphs
- [x] **Image Support**: Placeholder for future OCR capabilities
- [x] **Text Utilities**: Comprehensive text cleaning and preprocessing
- [x] **Batch Processing**: Ingest multiple files in one operation
- [x] **Auto-Detection**: Automatic file type detection and routing

#### Phase 2 Features:

- **Document Formats**: PDF, DOCX, and image files (images return empty blocks for now)
- **Text Processing**: Clean extracted text, remove artifacts, normalize whitespace
- **Structured Output**: Convert documents into `CanonicalDoc` with `DocBlock` segments
- **Error Handling**: Comprehensive error handling with informative messages
- **Testing**: Complete test suite with mocking for external dependencies

#### Phase 2 Usage:

```python
from app.core.io.ingest import ingest_any, batch_ingest

# Ingest a single document
doc = ingest_any("student_essay.pdf")
print(f"Extracted {len(doc.blocks)} text blocks")

# Batch ingest multiple files
docs = batch_ingest(["essay1.pdf", "report.docx", "image.jpg"])
print(f"Processed {len(docs)} documents")
```

#### Phase 2 Dependencies:

```bash
pip install pdfplumber python-docx  # Install document processing libraries
```

### Phase 3: Persistence & Catalog ✅

- [x] **Unified Repository Interface**: Single API for all CRUD operations across entities
- [x] **Dual Backend Support**: Seamless switching between JSON and SQLite storage
- [x] **Complete CRUD Operations**: Save, retrieve, list, and delete for rubrics, questions, submissions, and evaluation results
- [x] **Backend Abstraction**: Pluggable storage system with consistent interface
- [x] **Automatic Database Initialization**: SQLite schema creation and migration handling
- [x] **Comprehensive Testing**: Full test coverage for both storage backends and error scenarios

#### Phase 3 Features:

- **Repository Pattern**: Clean separation between business logic and data persistence
- **Backend Selection**: Environment-driven backend switching (`EVALMATE_STORAGE_MODE`)
- **Metadata Extraction**: Efficient listing with extracted metadata (no full object loading)
- **Error Handling**: Robust error handling with informative logging
- **Data Integrity**: Referential integrity and validation across storage backends
- **Atomic Operations**: Safe atomic writes for JSON backend, transaction support for SQLite

#### Phase 3 Usage:

```python
from app.core.store import repo

# Save entities
rubric_id = repo.save_rubric(my_rubric)
question_id = repo.save_question(my_question)
submission_id = repo.save_submission(my_submission)
eval_id = repo.save_eval_result(my_eval_result)

# List entities with metadata
rubrics = repo.list_rubrics()
questions = repo.list_questions(rubric_id="RUB001")  # Filter by rubric
submissions = repo.list_submissions(rubric_id="RUB001")  # Filter by rubric
evaluations = repo.list_eval_results(submission_id="SUB001")  # Filter by submission

# Retrieve full entities
rubric = repo.get_rubric("RUB001")
question = repo.get_question("Q001")
submission = repo.get_submission("SUB001")
evaluation = repo.get_eval_result("EVAL001")
```

#### Phase 3 Backend Configuration:

```bash
# Use SQLite backend (default)
export EVALMATE_STORAGE_MODE=sqlite

# Use JSON file backend
export EVALMATE_STORAGE_MODE=json
```

#### Phase 3 Testing:

```bash
# Run repository tests
pytest tests/test_repo_storage.py -v

# Test with different backends
EVALMATE_STORAGE_MODE=json pytest tests/test_repo_storage.py -v
EVALMATE_STORAGE_MODE=sqlite pytest tests/test_repo_storage.py -v

# Run repository smoke test
python app/main.py
```

### Phase 4: Rubric Structuring Engine ✅

Phase 4 implements a robust rubric structuring engine that converts CanonicalDoc objects (from Phase 2 ingestion) into normalized Rubric.items lists with intelligent parsing, weight normalization, and criterion mapping.

#### Phase 4 Features:

- **Multi-format Rubric Parsing**: Handle rubrics authored as bulleted lists, numbered lists, and tables
- **Table Extraction**: Extract tables from DOCX and PDF documents using camelot-py and tabula-py
- **Weight Normalization**: Automatic normalization of percentages, points, or equal distribution
- **Criterion Mapping**: Intelligent classification of rubric items to RubricCriterion enum values
- **Graceful Fallbacks**: Resilient parsing with deterministic output even for edge cases
- **Comprehensive Testing**: 22 test cases covering all parsing scenarios and edge cases

#### Phase 4 Usage:

```python
from app.core.io.rubric_parser import parse_rubric_to_items, ParseConfig
from app.core.models.schemas import CanonicalDoc

# Basic usage - parse any rubric structure
canonical_doc = load_canonical_doc("rubric.docx")  # From Phase 2
rubric_items = parse_rubric_to_items(canonical_doc)

# Advanced configuration
config = ParseConfig(
    prefer_tables=True,                    # Prioritize table parsing
    normalize_missing_weights=True,        # Equal distribution for missing weights
    criterion_keywords={                   # Custom criterion mapping
        "accuracy": ["correct", "precise"],
        "content": ["depth", "understanding"]
    },
    default_criterion="content"
)

items = parse_rubric_to_items(canonical_doc, config)

# Each item has normalized weights and mapped criteria
for item in items:
    print(f"{item.title}: {item.weight:.1%} ({item.criterion.value})")
    print(f"  {item.description}")
```

#### Phase 4 Dependencies:

- **camelot-py[cv]>=0.11.0**: PDF table extraction with computer vision
- **tabula-py>=2.9.0**: Alternative PDF table extraction
- **regex>=2024.4.28**: Advanced pattern matching for text parsing

#### Phase 4 Testing:

- **Text Utilities**: Bullet/numbered detection, weight parsing, heading/body splitting (7 tests)
- **Bullet/Numbered Parsing**: List-based rubrics with various weight formats (2 tests)
- **Table Parsing**: DOCX/PDF tables with and without headers (2 tests)
- **Weight Normalization**: Percentage/point conversion, missing weight handling (2 tests)
- **Criterion Mapping**: Keyword-based classification, custom mappings (2 tests)
- **Fallback Behaviors**: Unstructured text, empty documents, configuration preferences (3 tests)
- **Data Integrity**: Weight validation, description completeness, enum validity (3 tests)
- **Graceful Degradation**: External dependency handling (1 test)

### Phase 5: API & CLI User Flows ✅

Phase 5 implements complete user flows for uploading and managing rubrics, questions, and submissions through both REST API and command-line interfaces, providing full parity between programmatic and interactive access.

#### Phase 5 Features:

- **FastAPI Server**: Complete REST API with automatic documentation and validation
- **CLI Interface**: Full-featured command-line interface with rich table output
- **File Upload Management**: Secure file handling with sanitization and organized storage
- **Metadata Inference**: Auto-detection of entity metadata from filenames and content
- **Type Detection**: Automatic file type detection and appropriate ingestion routing
- **Validation & Error Handling**: Comprehensive validation with informative error messages
- **Repository Integration**: Seamless integration with Phase 3 storage layer
- **Comprehensive Testing**: 42 test cases covering API endpoints and CLI commands

#### Phase 5 API Endpoints:

- **Rubrics**: `POST /rubrics/upload`, `GET /rubrics/`, `GET /rubrics/{id}`
- **Questions**: `POST /questions/upload`, `GET /questions/`, `GET /questions/{id}`
- **Submissions**: `POST /submissions/upload`, `GET /submissions/`, `GET /submissions/{id}`
- **Health Check**: `GET /health` for service monitoring

#### Phase 5 CLI Commands:

- **Rubrics**: `rubrics upload`, `rubrics list`, `rubrics get`
- **Questions**: `questions upload`, `questions list`, `questions get`
- **Submissions**: `submissions upload`, `submissions list`, `submissions get`

#### Phase 5 Dependencies:

- **fastapi>=0.110.0**: Modern async web framework with automatic validation
- **uvicorn>=0.29.0**: High-performance ASGI server for FastAPI
- **python-multipart>=0.0.9**: Multipart form data support for file uploads
- **typer>=0.12.0**: Modern CLI framework with rich output formatting
- **httpx>=0.24.0**: HTTP client for testing API endpoints

#### Phase 5 Testing:

```bash
# Run API tests
pytest tests/test_api_phase5.py -v

# Run CLI tests
pytest tests/test_cli_phase5.py -v

# Run both together
pytest tests/test_api_phase5.py tests/test_cli_phase5.py -v
```

### Phase 6: Visual Extraction ✅

- ✅ PDF/DOCX visual element detection
- ✅ Image and table extraction from documents
- ✅ OCR processing for visual text content
- ✅ Asset management and storage
- ✅ Visual metadata enrichment

### Phase 7: Multimodal LLM Integration ✅

- ✅ OpenAI GPT-4o multimodal API integration
- ✅ Image captioning with semantic understanding
- ✅ Visual content description generation
- ✅ Environment configuration management
- ✅ Token estimation and cost optimization

### Phase 8: Fusion Builder (Unified Evaluation Context) ✅

This phase merges rubric, question, and submission into a single structured JSON
called FusionContext — ready for the LLM evaluator in Phase 9.

#### Phase 8 Components:

- ✅ FusionContext schema with all required fields for evaluation
- ✅ Builder assembles and validates rubric, question, submission
- ✅ Token estimation via tiktoken for cost management
- ✅ FusionContext JSON saved under `data/fusion/` for reuse
- ✅ API endpoints for fusion creation and inspection
- ✅ CLI commands for building and managing fusion contexts
- ✅ Comprehensive unit tests ensuring completeness

#### Phase 8 CLI Usage:

```bash
# Build fusion context
uv run python -m app.ui.cli_fusion build --rubric-id R1 --question-id Q1 --submission-id S1

# List all fusion contexts
uv run python -m app.ui.cli_fusion list

# View specific fusion context
uv run python -m app.ui.cli_fusion view FUSION-S1

# Validate fusion context
uv run python -m app.ui.cli_fusion validate FUSION-S1

# Get statistics
uv run python -m app.ui.cli_fusion stats
```

#### Phase 8 API Endpoints:

```bash
# Build fusion context
POST /fusion/build
GET /fusion/build?rubric_id=R1&question_id=Q1&submission_id=S1

# Get fusion context
GET /fusion/FUSION-S1

# List all fusion contexts
GET /fusion/

# Get fusion summary
GET /fusion/FUSION-S1/summary

# Validate fusion context
GET /fusion/FUSION-S1/validate

# Get text content
GET /fusion/FUSION-S1/text

# Get statistics
GET /fusion/stats/overview
```

#### Phase 8 Testing:

```bash
uv run pytest tests/test_fusion_builder.py -v
```

## Phase 9 – Evaluation & Feedback Agent

This phase introduces the LLM grader that evaluates each rubric item and returns strict JSON results with per-criterion scores, justifications, and evidence block IDs, plus a weighted total.

### Features

- **OpenAI Integration**: Uses GPT models for intelligent evaluation
- **Strict JSON Output**: Enforced schema compliance with repair mechanisms
- **Per-Criterion Assessment**: Individual evaluation of each rubric item
- **Evidence Citation**: Links scores to specific submission blocks
- **Weighted Scoring**: Computes total scores based on rubric weights
- **Token Management**: Efficient content chunking and cost control
- **Retry Logic**: Robust error handling with exponential backoff

### Environment Setup

```bash
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4o  # optional override
```

### Run via CLI

```bash
# Evaluate a submission
uv run python -m app.ui.cli_evaluate run --rubric-id R1 --question-id Q1 --submission-id S1

# Check evaluation status
uv run python -m app.ui.cli_evaluate status --submission-id S1

# View evaluation results
uv run python -m app.ui.cli_evaluate result --submission-id S1
```

### Run via API

```bash
# Start the server
uv run python -m app.api.server

# Evaluate submission
POST /evaluate?rubric_id=R1&question_id=Q1&submission_id=S1

# Get evaluation result
GET /evaluate/result/S1

# Check status
GET /evaluate/status/S1
```

### Key Components

#### LLM Evaluator (`app/core/llm/evaluator.py`)

- Main evaluation pipeline that consumes FusionContext
- Per-item LLM calls with keyword-based content slicing
- Weighted total computation and result validation

#### Prompt Engineering (`app/core/llm/prompts.py`)

- System prompts that enforce JSON-only outputs
- Structured templates for rubric and submission data
- Schema instructions for consistent formatting

#### JSON Guard (`app/core/llm/json_guard.py`)

- Strict JSON parsing with repair mechanisms
- Handles common LLM output formatting issues
- Fallback strategies for malformed responses

#### Rate Limiting (`app/core/llm/rate_limit.py`)

- Exponential backoff for API rate limits
- Retry logic for transient failures
- Request logging and monitoring

### Implementation Notes

- **Deterministic**: temperature=0.0 for consistent results
- **Cost Optimized**: Per-criterion chunking reduces token usage
- **Validated**: Evidence block IDs must reference actual submission content
- **Persistent**: Results saved via `repo.save_eval_result()`
- **Robust**: Graceful fallbacks for API failures

#### Phase 9 Testing:

```bash
uv run pytest tests/test_evaluator_phase9.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) section
2. Review the test suite for examples
3. Ensure your environment meets the requirements
4. Verify the initialization completed successfully

## 🙏 Acknowledgments

- Built with modern Python best practices
- Designed for educational technology applications
- Inspired by the need for intelligent, scalable assessment tools
