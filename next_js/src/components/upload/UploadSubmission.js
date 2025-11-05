"use client";

import { useState, useEffect } from "react";
import { Paper, Stack, Text, FileInput, TextInput } from "@mantine/core";
import { IconFileText } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";

export function UploadSubmission({ onUpload, loading, disabled }) {
  const [studentHandle, setStudentHandle] = useState("");
  const [file, setFile] = useState(null);

  const textInputDisabled = disabled || loading;
  const fileInputDisabled = disabled || loading;

  // Auto-upload when file and studentHandle are ready
  useEffect(() => {
    if (file && studentHandle.trim()) {
      onUpload(file, studentHandle.trim());
      setStudentHandle("");
      setFile(null);
    }
  }, [file, studentHandle, onUpload]);

  const handleFileChange = (newFile) => {
    setFile(newFile);
  };

  return (
    <Paper p="md" withBorder radius="md" shadow="sm">
      <Stack gap="sm">
        <div>
          <Text size="sm" fw={600} c="orange.7">
            Upload Submission
          </Text>
          <Text size="xs" c="dimmed">
            Upload student submission
          </Text>
        </div>

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
