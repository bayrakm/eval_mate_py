// API Configuration
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API Endpoints
export const API_ENDPOINTS = {
  // Rubrics
  RUBRICS_UPLOAD: `${API_BASE_URL}/rubrics/upload`,
  RUBRICS_LIST: `${API_BASE_URL}/rubrics/`,
  RUBRIC_DETAIL: (id) => `${API_BASE_URL}/rubrics/${id}`,

  // Questions
  QUESTIONS_UPLOAD: `${API_BASE_URL}/questions/upload`,
  QUESTIONS_LIST: `${API_BASE_URL}/questions/`,
  QUESTION_DETAIL: (id) => `${API_BASE_URL}/questions/${id}`,

  // Submissions
  SUBMISSIONS_UPLOAD: `${API_BASE_URL}/submissions/upload`,
  SUBMISSIONS_LIST: `${API_BASE_URL}/submissions/`,
  SUBMISSION_DETAIL: (id) => `${API_BASE_URL}/submissions/${id}`,

  // Evaluation
  EVALUATE: `${API_BASE_URL}/evaluate/`,
  EVAL_RESULT: (submissionId) =>
    `${API_BASE_URL}/evaluate/result/${submissionId}`,
  EVAL_STATUS: (submissionId) =>
    `${API_BASE_URL}/evaluate/status/${submissionId}`,

  // Fusion
  FUSION_BUILD: `${API_BASE_URL}/fusion/build`,
  FUSION_LIST: `${API_BASE_URL}/fusion/`,
  FUSION_DETAIL: (id) => `${API_BASE_URL}/fusion/${id}`,

  // Health
  HEALTH: `${API_BASE_URL}/health`,
};

// Loading states
export const LOADING_STATES = {
  IDLE: "idle",
  UPLOADING: "uploading",
  BUILDING: "building",
  EVALUATING: "evaluating",
};

// File upload constraints
export const UPLOAD_CONSTRAINTS = {
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  ALLOWED_FORMATS: ["pdf", "docx", "jpg", "png"],
};

// Evaluation criteria
export const CRITERIA = {
  CONTENT: "content",
  ACCURACY: "accuracy",
  STRUCTURE: "structure",
  VISUALS: "visuals",
  CITATIONS: "citations",
  ORIGINALITY: "originality",
};

// File types for upload components
export const FILE_TYPES = {
  RUBRIC: {
    accept:
      "application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx",
    label: "Rubric (PDF, DOCX)",
  },
  QUESTION: {
    accept:
      "application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx",
    label: "Question (PDF, DOCX)",
  },
  SUBMISSION: {
    accept:
      "application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx,image/jpeg,.jpg,image/png,.png",
    label: "Submission (PDF, DOCX, JPG, PNG)",
  },
};
