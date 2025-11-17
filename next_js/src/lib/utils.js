export const formatDate = (value) => {
  if (!value) {
    return "";
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
};

export const formatScore = (value, digits = 1) => {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return (0).toFixed(digits);
  }
  return numeric.toFixed(digits);
};
