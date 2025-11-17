import axios from "axios";
import { API_BASE_URL, REQUEST_TIMEOUT_MS } from "./constants";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
});

const extractErrorMessage = (error) => {
  if (error.response?.data) {
    const detail = error.response.data.detail || error.response.data.message;
    if (detail) {
      return Array.isArray(detail) ? detail.join(", ") : detail;
    }
  }
  if (error.message) {
    return error.message;
  }
  return "Request failed";
};

const postMultipart = async (url, formData, onProgress) => {
  try {
    const response = await api.post(url, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (event) => {
        if (!onProgress || !event.total) {
          return;
        }
        const percentage = Math.round((event.loaded / event.total) * 100);
        onProgress(percentage);
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const uploadRubric = (file, metadata = {}, onProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("params", JSON.stringify(metadata || {}));
  return postMultipart("/rubrics/upload", formData, onProgress);
};

export const uploadQuestion = (
  rubricId,
  file,
  title,
  onProgress
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append(
    "params",
    JSON.stringify({
      rubric_id: rubricId,
      ...(title ? { title } : {}),
    })
  );
  return postMultipart("/questions/upload", formData, onProgress);
};

export const uploadSubmission = (
  rubricId,
  questionId,
  studentHandle,
  file,
  onProgress
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append(
    "params",
    JSON.stringify({
      rubric_id: rubricId,
      question_id: questionId,
      student_handle: studentHandle,
    })
  );
  return postMultipart("/submissions/upload", formData, onProgress);
};

const getJson = async (url) => {
  try {
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getRubric = (rubricId) => getJson(`/rubrics/${rubricId}`);
export const getQuestion = (questionId) => getJson(`/questions/${questionId}`);
export const getSubmission = (submissionId) =>
  getJson(`/submissions/${submissionId}`);

export const buildFusion = async (rubricId, questionId, submissionId) => {
  try {
    const response = await api.post("/fusion/build", {
      rubric_id: rubricId,
      question_id: questionId,
      submission_id: submissionId,
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const evaluate = async (rubricId, questionId, submissionId) => {
  try {
    const response = await api.post("/evaluate", null, {
      params: {
        rubric_id: rubricId,
        question_id: questionId,
        submission_id: submissionId,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};
