"use client";

import { Paper, Stack, Text, FileInput, Group, Badge, Loader } from "@mantine/core";
import { IconFileText, IconCheck } from "@tabler/icons-react";
import { useState, useEffect } from "react";
import { FILE_TYPES } from "../../lib/constants";
import { ProgressIndicator } from "../display/ProgressIndicator";

export function UploadRubric({
  onUpload,
  loading,
  isCompleted = false,
  progress = null,
}) {
  const [file, setFile] = useState(null);

  useEffect(() => {
    if (!isCompleted) {
      setFile(null);
    }
  }, [isCompleted]);

  const handleFileChange = (newFile) => {
    setFile(newFile);
    if (newFile) {
      onUpload(newFile);
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
              Upload Rubric
            </Text>
            <Text size="xs" c="dimmed">
              Upload rubric file for evaluation
            </Text>
          </div>
          {isCompleted && (
            <Badge color="green" leftSection={<IconCheck size={12} />}>
              Completed
            </Badge>
          )}
        </Group>

        <FileInput
          leftSection={<IconFileText size={18} />}
          placeholder="Select rubric file"
          accept={FILE_TYPES.RUBRIC.accept}
          onChange={handleFileChange}
          disabled={loading || isCompleted}
          value={file}
          size="md"
        />

        {loading && (
          <Group mt="xs">
            <Loader type="dots" color="orange" size="sm" />
            <Text size="sm" c="dimmed">
              Uploading rubric file...
            </Text>
          </Group>
        )}
      </Stack>
    </Paper>
  );
}
