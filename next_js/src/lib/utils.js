/**
 * Format file size to human readable format
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

/**
 * Format date to readable format
 */
export function formatDate(date) {
  if (typeof date === "string") {
    date = new Date(date);
  }
  return new Intl.DateTimeFormat("id-ID", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/**
 * Validate file format
 */
export function isValidFileFormat(filename, allowedFormats) {
  const ext = filename.split(".").pop().toLowerCase();
  return allowedFormats.includes(ext);
}

/**
 * Get file extension
 */
export function getFileExtension(filename) {
  return filename.split(".").pop().toLowerCase();
}

/**
 * Truncate text to specified length
 */
export function truncateText(text, length = 100) {
  if (text.length <= length) return text;
  return text.substring(0, length) + "...";
}

/**
 * Sanitize filename
 */
export function sanitizeFilename(filename) {
  return filename
    .replace(/[^a-zA-Z0-9.-]/g, "_")
    .replace(/_+/g, "_")
    .trim();
}

/**
 * Generate unique ID
 */
export function generateId() {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Format score/percentage
 */
export function formatScore(score, decimals = 1) {
  return `${Number(score).toFixed(decimals)}%`;
}

/**
 * Get color based on score
 */
export function getScoreColor(score) {
  if (score >= 80) return "#10b981"; // green
  if (score >= 60) return "#f59e0b"; // amber
  if (score >= 40) return "#f97316"; // orange
  return "#ef4444"; // red
}

/**
 * Format criterion name for display
 */
export function formatCriterionName(criterion) {
  const names = {
    content: "Content",
    accuracy: "Accuracy",
    structure: "Structure",
    visuals: "Visuals",
    citations: "Citations",
    originality: "Originality",
  };
  return names[criterion] || criterion;
}

/**
 * Get initials from name
 */
export function getInitials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

/**
 * Check if API URL is accessible
 */
export async function isApiAccessible(url) {
  try {
    const response = await fetch(url, { method: "HEAD" });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Retry async function with exponential backoff
 */
export async function retryAsync(fn, retries = 3, delay = 1000) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise((resolve) =>
        setTimeout(resolve, delay * Math.pow(2, i))
      );
    }
  }
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 */
export function throttle(func, limit) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
