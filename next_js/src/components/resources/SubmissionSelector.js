"use client";

import { useEffect, useState, useCallback } from "react";
import { Select, Stack, Paper, Text, Loader, Button } from "@mantine/core";
import { IconRefresh } from "@tabler/icons-react";

export function SubmissionSelector({
  selectedSubmission,
  rubricId,
  questionId,
  onSelect,
  onLoad,
  onGet,
}) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(selectedSubmission?.id || null);

  const loadSubmissions = useCallback(async () => {
    if (!rubricId || !questionId || !onLoad || typeof onLoad !== "function") {
      setSubmissions([]);
      return;
    }

    try {
      setLoading(true);
      const data = await onLoad({
        rubric_id: rubricId,
        question_id: questionId,
      });
      if (Array.isArray(data)) {
        setSubmissions(data);
      } else {
        console.warn("Expected array but got:", typeof data);
        setSubmissions([]);
      }
    } catch (error) {
      console.warn("Failed to load submissions:", error);
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  }, [rubricId, questionId, onLoad]);

  useEffect(() => {
    if (rubricId && questionId) {
      loadSubmissions();
    } else {
      setSubmissions([]);
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rubricId, questionId]);

  useEffect(() => {
    if (selectedSubmission) {
      setSelectedId(selectedSubmission.id);
    }
  }, [selectedSubmission]);

  const handleSelect = async (value) => {
    if (!value || !onGet || typeof onGet !== "function") return;
    setSelectedId(value);
    try {
      const submission = await onGet(value);
      if (onSelect && typeof onSelect === "function") {
        onSelect(submission);
      }
    } catch (error) {
      console.warn("Failed to get submission:", error);
    }
  };

  if (!rubricId || !questionId) {
    return (
      <Paper p="md" withBorder radius="md" bg="gray.0">
        <Text size="sm" c="dimmed" ta="center">
          Pilih rubric dan question terlebih dahulu
        </Text>
      </Paper>
    );
  }

  const submissionOptions = submissions.map((s) => ({
    value: s.id,
    label: `${s.student_handle} (${s.id.substring(0, 8)}...)`,
  }));

  return (
    <Stack gap="sm">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Text size="sm" fw={600}>
          Pilih Submission
        </Text>
        <Button
          variant="subtle"
          size="xs"
          onClick={loadSubmissions}
          leftSection={<IconRefresh size={14} />}
        >
          Refresh
        </Button>
      </div>

      {loading ? (
        <Loader size="sm" />
      ) : (
        <Select
          placeholder="Pilih submission..."
          value={selectedId}
          onChange={handleSelect}
          data={submissionOptions}
          searchable
          clearable
        />
      )}

      {selectedSubmission && (
        <Paper p="xs" withBorder radius="sm" bg="orange.0">
          <Text size="xs" fw={600} c="orange.7">
            Selected: {selectedSubmission.student_handle}
          </Text>
        </Paper>
      )}
    </Stack>
  );
}
