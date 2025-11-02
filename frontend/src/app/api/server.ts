import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  withCredentials: false,
  headers: { 
    "Accept": "application/json" 
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error?.response?.data?.detail || error.message || "Request failed";
    console.error("API Error:", msg);
    return Promise.reject(new Error(msg));
  }
);