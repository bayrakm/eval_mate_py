import { API_ENDPOINTS } from "./constants";

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

/**
 * Upload file to API
 */
export async function uploadFile(endpoint, file, params = {}) {
  const formData = new FormData();
  formData.append("file", file);

  if (Object.keys(params).length > 0) {
    formData.append("params", JSON.stringify(params));
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Upload Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Upload Error:", error);
    throw error;
  }
}

// ===== Rubric API Calls =====

export async function uploadRubric(file, params = {}) {
  return uploadFile(API_ENDPOINTS.RUBRICS_UPLOAD, file, params);
}

export async function listRubrics() {
  return apiFetch(API_ENDPOINTS.RUBRICS_LIST);
}

export async function getRubric(id) {
  return apiFetch(API_ENDPOINTS.RUBRIC_DETAIL(id));
}

// ===== Question API Calls =====

export async function uploadQuestion(file, params = {}) {
  return uploadFile(API_ENDPOINTS.QUESTIONS_UPLOAD, file, params);
}

export async function listQuestions(rubricId = null) {
  const url = rubricId
    ? `${API_ENDPOINTS.QUESTIONS_LIST}?rubric_id=${rubricId}`
    : API_ENDPOINTS.QUESTIONS_LIST;
  return apiFetch(url);
}

export async function getQuestion(id) {
  return apiFetch(API_ENDPOINTS.QUESTION_DETAIL(id));
}

// ===== Submission API Calls =====

export async function uploadSubmission(file, params = {}) {
  return uploadFile(API_ENDPOINTS.SUBMISSIONS_UPLOAD, file, params);
}

export async function listSubmissions(filters = {}) {
  const params = new URLSearchParams(filters);
  const url = params.toString()
    ? `${API_ENDPOINTS.SUBMISSIONS_LIST}?${params}`
    : API_ENDPOINTS.SUBMISSIONS_LIST;
  return apiFetch(url);
}

export async function getSubmission(id) {
  return apiFetch(API_ENDPOINTS.SUBMISSION_DETAIL(id));
}

// ===== Evaluation API Calls =====

export async function evaluate(rubricId, questionId, submissionId) {
  const params = new URLSearchParams({
    rubric_id: rubricId,
    question_id: questionId,
    submission_id: submissionId,
  });
  return apiFetch(`${API_ENDPOINTS.EVALUATE}?${params.toString()}`, {
    method: "POST",
  });
}

export async function getEvaluationResult(submissionId) {
  return apiFetch(API_ENDPOINTS.EVAL_RESULT(submissionId));
}

export async function checkEvaluationStatus(submissionId) {
  return apiFetch(API_ENDPOINTS.EVAL_STATUS(submissionId));
}

// ===== Fusion API Calls =====

export async function buildFusion(rubricId, questionId, submissionId) {
  return apiFetch(API_ENDPOINTS.FUSION_BUILD, {
    method: "POST",
    body: JSON.stringify({
      rubric_id: rubricId,
      question_id: questionId,
      submission_id: submissionId,
    }),
  });
}

export async function listFusions() {
  return apiFetch(API_ENDPOINTS.FUSION_LIST);
}

export async function getFusion(id) {
  return apiFetch(API_ENDPOINTS.FUSION_DETAIL(id));
}

// ===== Health Check =====

export async function checkHealth() {
  try {
    return await apiFetch(API_ENDPOINTS.HEALTH);
  } catch {
    return { status: "unhealthy" };
  }
}
