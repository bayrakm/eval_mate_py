import type { EvalResult } from "./types";

export const evalResultToCSV = (result: EvalResult): string => {
  const header = "rubric_item_id,score,justification\n";
  const rows = result.items.map(item => {
    const escapedJustification = (item.justification || "")
      .replace(/"/g, '""')
      .replace(/\n/g, ' ');
    return `"${item.rubric_item_id}",${item.score},"${escapedJustification}"`;
  }).join("\n");
  
  return header + rows + "\n";
};

export const download = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const downloadJSON = (data: any, filename: string): void => {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json"
  });
  download(blob, filename);
};

export const downloadCSV = (result: EvalResult, filename: string): void => {
  const csvContent = evalResultToCSV(result);
  const blob = new Blob([csvContent], { type: "text/csv" });
  download(blob, filename);
};

export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
};

export const formatScore = (score: number): string => {
  return `${score.toFixed(1)}/100`;
};

export const formatTokens = (tokens: number): string => {
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}k tokens`;
  }
  return `${tokens} tokens`;
};