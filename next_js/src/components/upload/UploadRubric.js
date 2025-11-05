"use client";

import { Paper, Stack, Text, FileInput } from "@mantine/core";
import { IconFileText } from "@tabler/icons-react";
import { FILE_TYPES } from "../../lib/constants";

export function UploadRubric({ onUpload, loading }) {
  const handleFileChange = (file) => {
    if (file) {
      onUpload(file);
    }
  };

  return (
    <Paper p="md" withBorder radius="md" shadow="sm">
      <Stack gap="sm">
        <div>
          <Text size="sm" fw={600} c="orange.7">
            Upload Rubric
          </Text>
          <Text size="xs" c="dimmed">
            Upload rubric file for evaluation
          </Text>
        </div>

        <FileInput
          leftSection={<IconFileText size={18} />}
          placeholder="Select rubric file"
          accept={FILE_TYPES.RUBRIC.accept}
          onChange={handleFileChange}
          disabled={loading}
          size="md"
        />
      </Stack>
    </Paper>
  );
}
