"use client";

import { useState, useEffect } from "react";
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

export function UploadSubmission({
  onUpload,
  loading,
  disabled,
  isCompleted = false,
  completedSubmission = null,
}) {
  const [studentHandle, setStudentHandle] = useState("");
  const [file, setFile] = useState(null);

  const textInputDisabled = disabled || loading || isCompleted;
  const fileInputDisabled = disabled || loading || isCompleted;

  // Auto-upload when file and studentHandle are ready
  useEffect(() => {
    if (file && studentHandle.trim() && !isCompleted) {
      onUpload(file, studentHandle.trim());
      setStudentHandle("");
      setFile(null);
    }
  }, [file, studentHandle, onUpload, isCompleted]);

  const handleFileChange = (newFile) => {
    setFile(newFile);
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
              Upload Submission
            </Text>
            <Text size="xs" c="dimmed">
              Upload student submission
            </Text>
            {isCompleted && completedSubmission && (
              <Text size="xs" c="green.7" mt={4} fw={500}>
                ✓ Uploaded: {completedSubmission.student_handle}
              </Text>
            )}
          </div>
          {isCompleted && (
            <Badge color="green" leftSection={<IconCheck size={12} />}>
              Completed
            </Badge>
          )}
        </Group>

        <TextInput
          placeholder={
            disabled
              ? "Please select a rubric and question first"
              : "Student handle/ID"
          }
          value={studentHandle}
          onChange={(e) => setStudentHandle(e.target.value)}
          disabled={textInputDisabled}
          size="md"
          required
        />

        <FileInput
          leftSection={<IconFileText size={18} />}
          placeholder="Select submission file"
          accept={FILE_TYPES.SUBMISSION.accept}
          onChange={handleFileChange}
          disabled={fileInputDisabled}
          value={file}
          size="md"
        />
      </Stack>
    </Paper>
  );
}
