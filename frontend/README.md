# EvalMate Frontend

A modern Next.js frontend for the EvalMate Student Assignment Feedback App with a ChatGPT-like interface.

## Features

- **Chat-style Interface**: Intuitive conversational UI for uploading and managing resources
- **Rubric Management**: Upload and select rubrics from PDF/DOCX files
- **Question Handling**: Upload questions and map them to rubrics
- **Submission Processing**: Upload student submissions with support for multiple file formats
- **AI Evaluation**: Build fusion context and run LLM-powered evaluation
- **Results Visualization**: Detailed score cards with justifications and evidence references
- **Export Capabilities**: Download results as JSON or CSV
- **Real-time Updates**: Live progress tracking for all operations

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with shadcn/ui-inspired design
- **HTTP Client**: Axios with typed API client
- **Testing**: Vitest + React Testing Library
- **Icons**: Lucide React

## Getting Started

### Prerequisites

Make sure you have the backend running first:

```bash
# In the project root (not frontend/)
uv run fastapi dev app/api/server.py
# Backend runs on http://localhost:8000
```

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
pnpm install
# or
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
```

4. Start the development server:
```bash
pnpm dev
# or
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage

### Basic Workflow

1. **Upload Rubric**: Start by uploading a rubric file (PDF/DOCX) using the file picker
2. **Upload Question**: Once a rubric is selected, upload a question file and optionally provide a title
3. **Upload Submission**: With both rubric and question selected, upload a student submission
4. **Build Fusion**: Click "Build Fusion" to create the context for evaluation
5. **Run Evaluation**: Click "Run Evaluation" to get AI-powered grading
6. **View Results**: See detailed scores, justifications, and evidence in the results panel
7. **Export Data**: Download results as JSON or CSV files

### File Format Support

- **Rubrics**: PDF, DOCX
- **Questions**: PDF, DOCX, TXT
- **Submissions**: PDF, DOCX, TXT, PNG, JPG, JPEG

### Interface Overview

#### Left Sidebar - Resource Picker
- **Rubrics Tab**: Browse and select uploaded rubrics
- **Questions Tab**: Browse questions for the selected rubric
- **Submissions Tab**: Browse submissions for the selected rubric and question

#### Main Area - Chat Interface
- **Message List**: Shows conversation history with status updates
- **Composer**: File upload controls and action buttons
- **Progress Indicators**: Real-time feedback on operations

#### Right Sidebar - Summary & Results
- **Summary Panel**: Fusion context details and export buttons
- **Results Panel**: Detailed score cards for each rubric item

## API Integration

The frontend integrates with these FastAPI endpoints:

### Rubrics
- `POST /rubrics/upload` - Upload new rubric
- `GET /rubrics` - List all rubrics
- `GET /rubrics/{id}` - Get rubric details

### Questions
- `POST /questions/upload` - Upload new question
- `GET /questions` - List questions (with optional rubric filter)
- `GET /questions/{id}` - Get question details

### Submissions
- `POST /submissions/upload` - Upload new submission
- `GET /submissions` - List submissions (with optional filters)
- `GET /submissions/{id}` - Get submission details

### Fusion & Evaluation
- `POST /fusion/build` - Build fusion context
- `GET /fusion/{id}` - Get fusion context
- `POST /evaluate` - Run LLM evaluation

## Development

### Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── api/             # API client configuration
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main application page
│   ├── components/
│   │   ├── chat/            # Chat interface components
│   │   │   ├── ChatShell.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── Composer.tsx
│   │   ├── panels/          # Sidebar panel components
│   │   │   ├── Picker.tsx
│   │   │   ├── Summary.tsx
│   │   │   └── ScoreCard.tsx
│   │   └── ui/              # Base UI primitives
│   ├── lib/
│   │   ├── types.ts         # TypeScript type definitions
│   │   ├── apiClient.ts     # Typed API client functions
│   │   ├── format.ts        # Formatting and export utilities
│   │   └── utils.ts         # General utilities
│   ├── styles/
│   │   └── globals.css      # Global styles and Tailwind setup
│   └── test/                # Test files
├── package.json
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
└── vitest.config.ts
```

### Key Components

#### ChatShell
Main container component that orchestrates the chat interface, managing message flow and user interactions.

#### MessageList
Displays conversation history with different message types (user, assistant, system) and proper formatting.

#### Composer
Handles file uploads and action buttons with real-time validation and progress feedback.

#### Picker
Three-tab interface for selecting rubrics, questions, and submissions with lazy loading and state management.

#### Summary
Shows fusion context details and evaluation results with export functionality.

#### ScoreCard
Detailed display of individual rubric item scores with justifications and evidence references.

### State Management

The app uses a centralized state pattern with React hooks:

```typescript
type AppState = {
  selectedRubric: Rubric | null;
  selectedQuestion: Question | null;
  selectedSubmission: Submission | null;
  fusion: FusionContext | null;
  result: EvalResult | null;
  messages: ChatMessage[];
  loading: LoadingState;
}
```

### API Client

Typed API client with automatic error handling:

```typescript
// Example usage
const rubrics = await api.listRubrics();
const result = await api.evaluate(rubricId, questionId, submissionId);
```

## Testing

Run tests with:

```bash
pnpm test        # Run all tests
pnpm test:watch  # Run in watch mode
```

Test coverage includes:
- Component rendering and interaction
- API client error handling  
- Utility function behavior
- Export functionality

## Building for Production

```bash
pnpm build       # Build for production
pnpm start       # Start production server
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

## Error Handling

The frontend includes comprehensive error handling:

- **API Errors**: Friendly error messages displayed in chat
- **File Upload**: Validation and progress feedback
- **Network Issues**: Automatic retry with exponential backoff
- **Invalid States**: Prevention of invalid operations

## Performance Considerations

- **Lazy Loading**: Components and resources loaded on demand
- **Memoization**: React.memo and useCallback for optimization
- **Efficient Updates**: Minimal re-renders with proper state management
- **File Handling**: Chunked uploads for large files

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions  
- Safari: Latest 2 versions

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Use TypeScript strictly (no `any` types)
5. Follow React best practices

## Troubleshooting

### Common Issues

**Backend Connection Failed**
- Ensure the FastAPI server is running on http://localhost:8000
- Check CORS configuration in the backend
- Verify environment variables are set correctly

**File Upload Issues**  
- Check file format support (PDF, DOCX, TXT, images)
- Ensure files are not corrupted
- Verify backend upload directory permissions

**Build Errors**
- Clear node_modules and reinstall dependencies
- Check TypeScript errors with `pnpm typecheck`
- Verify all environment variables are set

## License

This project is part of the EvalMate Student Assignment Feedback App.