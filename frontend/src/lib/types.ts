// Type definitions mirroring backend schemas

export type RubricMeta = {
  id: string;
  course: string;
  assignment: string;
  version: string;
};

export type RubricItem = {
  id: string;
  title: string;
  description: string;
  weight: number;
  criterion: string;
};

export type Rubric = {
  id: string;
  course: string;
  assignment: string;
  version: string;
  items: RubricItem[];
};

export type QuestionMeta = {
  id: string;
  title: string;
  rubric_id: string;
};

export type Question = {
  id: string;
  title: string;
  rubric_id: string;
  text: string;
  metadata: Record<string, any>;
};

export type SubmissionMeta = {
  id: string;
  rubric_id: string;
  question_id: string;
  student_handle: string;
};

export type Submission = {
  id: string;
  rubric_id: string;
  question_id: string;
  student_handle: string;
  text: string;
  visuals: VisualBlock[];
  metadata: Record<string, any>;
};

export type VisualBlock = {
  id: string;
  type: string;
  caption: string;
  ocr_text?: string | null;
};

export type FusionContext = {
  id: string;
  rubric_id: string;
  question_id: string;
  submission_id: string;
  rubric_items: {
    id: string;
    title: string;
    desc: string;
    weight: number;
    criterion?: string;
  }[];
  question_text: string;
  submission_text: string;
  submission_visuals: VisualBlock[];
  token_estimate: number;
  visual_count: number;
  text_block_count: number;
};

export type EvalScoreItem = {
  rubric_item_id: string;
  score: number;
  justification: string;
  evidence_block_ids: string[];
};

export type EvalResult = {
  submission_id: string;
  rubric_id: string;
  total: number;
  items: EvalScoreItem[];
  overall_feedback: string;
  metadata: Record<string, string>;
};

// API Response wrappers
export type ApiListResponse<T> = {
  items: T[];
  total: number;
};

export type UploadResponse = {
  id: string;
  message: string;
  metadata?: Record<string, any>;
};

// Chat UI types
export type ChatMessage = {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
};

export type LoadingState = 
  | 'idle' 
  | 'uploading' 
  | 'building' 
  | 'evaluating';

export type AppState = {
  selectedRubric: Rubric | null;
  selectedQuestion: Question | null;
  selectedSubmission: Submission | null;
  fusion: FusionContext | null;
  result: EvalResult | null;
  messages: ChatMessage[];
  loading: LoadingState;
};