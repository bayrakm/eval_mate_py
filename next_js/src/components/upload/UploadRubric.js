"use client";

import { Paper, Stack, Text, FileInput, Group, Badge } from "@mantine/core";
import { IconFileText, IconCheck } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";
import { ProgressIndicator } from "../display/ProgressIndicator";

export function UploadRubric({
  onUpload,
  loading,
  isCompleted = false,
  progress = null,
}) {
  const handleFileChange = (file) => {
    if (file) {
      onUpload(file);
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
          size="md"
        />

        {progress && progress.type === "upload" && (
          <ProgressIndicator progress={progress} />
        )}
      </Stack>
    </Paper>
  );
}
