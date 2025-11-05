"use client";

import { useState } from "react";
import { Paper, Stack, Text, FileInput, TextInput } from "@mantine/core";
import { IconFileText } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";

export function UploadQuestion({ onUpload, loading, disabled }) {
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
    <Paper p="md" withBorder radius="md" shadow="sm">
      <Stack gap="sm">
        <div>
          <Text size="sm" fw={600} c="orange.7">
            Upload Question
          </Text>
          <Text size="xs" c="dimmed">
            Upload file question/tugas
          </Text>
        </div>

        <TextInput
          placeholder="Judul question (opsional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={disabled || loading}
          size="md"
        />

        <FileInput
          leftSection={<IconFileText size={18} />}
          placeholder="Pilih file question"
          accept={FILE_TYPES.QUESTION.accept}
          onChange={handleFileChange}
          disabled={disabled || loading}
          value={file}
          size="md"
        />
      </Stack>
    </Paper>
  );
}
