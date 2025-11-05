"use client";

import { useEffect, useState, useCallback } from "react";
import { Select, Stack, Paper, Text, Loader, Button } from "@mantine/core";
import { IconRefresh } from "@tabler/icons-react";

export function QuestionSelector({
  selectedQuestion,
  rubricId,
  onSelect,
  onLoad,
  onGet,
}) {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(selectedQuestion?.id || null);

  const loadQuestions = useCallback(async () => {
    if (!rubricId || !onLoad || typeof onLoad !== "function") {
      setQuestions([]);
      return;
    }

    try {
      setLoading(true);
      const data = await onLoad(rubricId);
      if (Array.isArray(data)) {
        setQuestions(data);
      } else {
        setQuestions([]);
      }
    } catch (error) {
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  }, [rubricId, onLoad]);

  useEffect(() => {
    if (rubricId) {
      loadQuestions();
    } else {
      setQuestions([]);
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rubricId]);

  useEffect(() => {
    if (selectedQuestion) {
      setSelectedId(selectedQuestion.id);
    }
  }, [selectedQuestion]);

  const handleSelect = async (value) => {
    if (!value || !onGet || typeof onGet !== "function") return;
    setSelectedId(value);
    try {
      const question = await onGet(value);
      if (onSelect && typeof onSelect === "function") {
        onSelect(question);
      }
    } catch (error) {
      // Failed to get question
    }
  };

  if (!rubricId) {
    return (
      <Paper p="md" withBorder radius="md" bg="gray.0">
        <Text size="sm" c="dimmed" ta="center">
          Please select a rubric first
        </Text>
      </Paper>
    );
  }

  const questionOptions = questions.map((q) => ({
    value: q.id,
    label: q.title || `Question ${q.id}`,
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
          Select Question
        </Text>
        <Button
          variant="subtle"
          size="xs"
          onClick={loadQuestions}
          leftSection={<IconRefresh size={14} />}
        >
          Refresh
        </Button>
      </div>

      {loading ? (
        <Loader size="sm" />
      ) : (
        <Select
          placeholder="Select question..."
          value={selectedId}
          onChange={handleSelect}
          data={questionOptions}
          searchable
          clearable
        />
      )}

      {selectedQuestion && (
        <Paper p="xs" withBorder radius="sm" bg="orange.0">
          <Text size="xs" fw={600} c="orange.7">
            Selected: {selectedQuestion.title}
          </Text>
        </Paper>
      )}
    </Stack>
  );
}
