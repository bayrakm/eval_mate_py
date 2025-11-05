"use client";

import { useState, useEffect } from "react";
import { Paper, Stack, Text, FileInput, TextInput } from "@mantine/core";
import { IconFileText } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";

export function UploadSubmission({ onUpload, loading, disabled }) {
  const [studentHandle, setStudentHandle] = useState("");
  const [file, setFile] = useState(null);

  // Debug info
  const textInputDisabled = disabled || loading;
  const fileInputDisabled = disabled || loading; // FileInput hanya disabled jika disabled prop atau loading

  // Auto-upload ketika file dan studentHandle sudah ada
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
            Upload jawaban siswa
          </Text>
        </div>

        {/* Debug Info */}
        <Paper p="xs" withBorder bg="blue.0">
          <Text size="xs" fw={700} mb="xs">
            🔍 UPLOAD SUBMISSION DEBUG:
          </Text>
          <Text size="xs">
            disabled prop: {disabled ? "❌ TRUE" : "✅ FALSE"}
          </Text>
          <Text size="xs">loading: {loading ? "⏳ TRUE" : "✅ FALSE"}</Text>
          <Text size="xs">
            studentHandle: "{studentHandle}" (length: {studentHandle.length})
          </Text>
          <Text size="xs">file: {file ? `✅ ${file.name}` : "❌ null"}</Text>
          <Text size="xs">
            TextInput disabled: {textInputDisabled ? "❌ TRUE" : "✅ FALSE"}
          </Text>
          <Text size="xs" fw={600} c={fileInputDisabled ? "red" : "green"}>
            FileInput disabled: {fileInputDisabled ? "❌ TRUE" : "✅ FALSE"}
          </Text>
          <Text size="xs" c={file && studentHandle.trim() ? "green" : "orange"}>
            Ready to upload: {file && studentHandle.trim() ? "✅ YES" : "⏳ NO"}
          </Text>
        </Paper>

        <TextInput
          placeholder={
            disabled
              ? "Pilih rubric dan question terlebih dahulu"
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
          placeholder="Pilih file submission"
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
