"use client";

import { useState } from "react";
import {
  Paper,
  Stack,
  Text,
  FileInput,
  TextInput,
  Group,
  Badge,
} from "@mantine/core";
import { IconFileText, IconCheck } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";

export function UploadQuestion({
  onUpload,
  loading,
  disabled,
  isCompleted = false,
}) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);

  const handleFileChange = (newFile) => {
    setFile(newFile);
    if (newFile) {
      onUpload(newFile, title || undefined);
      setTitle("");
      setFile(null);
    }
  };

  return (
    <Paper
      p="md"
      withBorder
      radius="md"
      shadow="sm"
      style={{
        borderColor: isCompleted ? "var(--mantine-color-green-5)" : undefined,
        backgroundColor: isCompleted
          ? "var(--mantine-color-green-0)"
          : undefined,
      }}
    >
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start">
          <div style={{ flex: 1 }}>
            <Text size="sm" fw={600} c="orange.7">
              Upload Question
            </Text>
            <Text size="xs" c="dimmed">
              Upload question/assignment file
            </Text>
          </div>
          {isCompleted && (
            <Badge color="green" leftSection={<IconCheck size={12} />}>
              Completed
            </Badge>
          )}
        </Group>

        <TextInput
          placeholder="Question title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={disabled || loading || isCompleted}
          size="md"
        />

        <FileInput
          leftSection={<IconFileText size={18} />}
          placeholder="Select question file"
          accept={FILE_TYPES.QUESTION.accept}
          onChange={handleFileChange}
          disabled={disabled || loading || isCompleted}
          value={file}
          size="md"
        />
      </Stack>
    </Paper>
  );
}
