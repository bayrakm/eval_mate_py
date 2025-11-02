import { api } from "@/app/api/server";
import type { 
  RubricMeta, 
  Rubric, 
  QuestionMeta, 
  Question,
  SubmissionMeta, 
  Submission,
  FusionContext, 
  EvalResult,
  ApiListResponse,
  UploadResponse
} from "./types";

// Rubrics
export const listRubrics = async (): Promise<RubricMeta[]> => {
  const response = await api.get<ApiListResponse<RubricMeta>>("/rubrics");
  return response.data.items;
};

export const getRubric = async (id: string): Promise<Rubric> => {
  const response = await api.get<Rubric>(`/rubrics/${id}`);
  return response.data;
};

export const uploadRubric = async (
  file: File, 
  params?: Record<string, any>
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  if (params) {
    formData.append("params", JSON.stringify(params));
  }
  
  const response = await api.post<UploadResponse>("/rubrics/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

// Questions
export const listQuestions = async (rubric_id?: string): Promise<QuestionMeta[]> => {
  const response = await api.get<ApiListResponse<QuestionMeta>>("/questions", {
    params: rubric_id ? { rubric_id } : undefined
  });
  return response.data.items;
};

export const getQuestion = async (id: string): Promise<Question> => {
  const response = await api.get<Question>(`/questions/${id}`);
  return response.data;
};

export const uploadQuestion = async (
  rubric_id: string, 
  file: File, 
  title?: string
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("params", JSON.stringify({ rubric_id, title }));
  
  const response = await api.post<UploadResponse>("/questions/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

// Submissions
export const listSubmissions = async (filters?: {
  rubric_id?: string;
  question_id?: string;
  student_handle?: string;
}): Promise<SubmissionMeta[]> => {
  const response = await api.get<ApiListResponse<SubmissionMeta>>("/submissions", {
    params: filters
  });
  return response.data.items;
};

export const getSubmission = async (id: string): Promise<Submission> => {
  const response = await api.get<Submission>(`/submissions/${id}`);
  return response.data;
};

export const uploadSubmission = async (
  rubric_id: string,
  question_id: string,
  student_handle: string,
  file: File
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("params", JSON.stringify({ 
    rubric_id, 
    question_id, 
    student_handle 
  }));
  
  const response = await api.post<UploadResponse>("/submissions/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

// Fusion Context
export const buildFusion = async (
  rubric_id: string,
  question_id: string,
  submission_id: string
): Promise<FusionContext> => {
  const response = await api.post<FusionContext>("/fusion/build", null, {
    params: { rubric_id, question_id, submission_id }
  });
  return response.data;
};

export const getFusion = async (fusion_id: string): Promise<FusionContext> => {
  const response = await api.get<FusionContext>(`/fusion/${fusion_id}`);
  return response.data;
};

// Evaluation
export const evaluate = async (
  rubric_id: string,
  question_id: string,
  submission_id: string
): Promise<EvalResult> => {
  const response = await api.post<EvalResult>("/evaluate", null, {
    params: { rubric_id, question_id, submission_id }
  });
  return response.data;
};