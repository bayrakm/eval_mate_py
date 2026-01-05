export function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

export function formatDate(date) {
  if (typeof date === "string") {
    date = new Date(date);
  }
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function isValidFileFormat(filename, allowedFormats) {
  const ext = filename.split(".").pop().toLowerCase();
  return allowedFormats.includes(ext);
}

export function getFileExtension(filename) {
  return filename.split(".").pop().toLowerCase();
}

export function truncateText(text, length = 100) {
  if (text.length <= length) return text;
  return text.substring(0, length) + "...";
}

export function sanitizeFilename(filename) {
  return filename
    .replace(/[^a-zA-Z0-9.-]/g, "_")
    .replace(/_+/g, "_")
    .trim();
}

export function generateId() {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function formatScore(score, decimals = 1) {
  return `${Number(score).toFixed(decimals)}%`;
}

export function getScoreColor(score) {
  if (score >= 80) return "#10b981"; // green
  if (score >= 60) return "#f59e0b"; // amber
  if (score >= 40) return "#f97316"; // orange
  return "#ef4444"; // red
}

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

export function getInitials(name) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export async function isApiAccessible(url) {
  try {
    const response = await fetch(url, { method: "HEAD" });
    return response.ok;
  } catch {
    return false;
  }
}

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

/**
 * Parse narrative content into structured items with titles and descriptions
 * Handles both bullet points (- **Title:** description) and numbered format (1. **Title:** description)
 */
export function parseNarrativeContent(content) {
  if (!content || typeof content !== "string") {
    return [];
  }

  const items = [];
  
  // Split by bullet points with optional leading spaces
  // Pattern: \n followed by optional spaces, then - or number
  const parts = content.split(/\n\s*(?=[-•]|\d+\.)/);

  parts.forEach((part) => {
    const trimmed = part.trim();
    if (!trimmed) return;

    // Remove leading bullet or number
    const cleaned = trimmed.replace(/^([-•]|\d+\.)\s*/, "").trim();

    // Extract title from **Title:** pattern
    // Title is bold text followed by colon, rest is description
    const titleMatch = cleaned.match(/^\*\*([^*]+)\*\*:\s*([\s\S]*)$/);

    if (titleMatch) {
      const title = titleMatch[1].trim();
      const description = titleMatch[2].trim();
      
      items.push({
        title,
        description,
      });
    } else if (cleaned) {
      // If no title pattern found, treat entire part as description
      items.push({
        title: null,
        description: cleaned,
      });
    }
  });

  return items;
}
