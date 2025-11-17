const cleanBaseUrl = (baseUrl) => {
  if (!baseUrl) {
    return "";
  }
  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
};

export const API_BASE_URL = cleanBaseUrl(
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
);

export const LOADING_STATES = {
  IDLE: "idle",
  UPLOADING: "uploading",
  BUILDING: "building",
  EVALUATING: "evaluating",
};

const COMMON_ACCEPTED_TYPES = [
  ".pdf",
  ".doc",
  ".docx",
  ".png",
  ".jpg",
  ".jpeg",
];

export const FILE_TYPES = {
  RUBRIC: {
    accept: COMMON_ACCEPTED_TYPES.join(","),
  },
  QUESTION: {
    accept: COMMON_ACCEPTED_TYPES.join(","),
  },
  SUBMISSION: {
    accept: COMMON_ACCEPTED_TYPES.join(","),
  },
};

export const REQUEST_TIMEOUT_MS = 120000;
