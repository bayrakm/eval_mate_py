"use client";

import { Progress, Text, Paper, Stack, Group } from "@mantine/core";
import { IconUpload, IconBlocks, IconCheck } from "@tabler/icons-react";

export function ProgressIndicator({ progress }) {
  if (!progress || progress.value === null) {
    return null;
  }

  const getIcon = () => {
    switch (progress.type) {
      case "upload":
        return <IconUpload size={16} />;
      case "building":
        return <IconBlocks size={16} />;
      case "evaluating":
        return <IconCheck size={16} />;
      default:
        return null;
    }
  };

  const getColor = () => {
    switch (progress.type) {
      case "upload":
        return "blue";
      case "building":
        return "orange";
      case "evaluating":
        return "violet";
      default:
        return "blue";
    }
  };

  return (
    <Paper p="sm" withBorder radius="md" bg="gray.0">
      <Stack gap="xs">
        <Group gap="xs" justify="space-between">
          <Group gap="xs">
            {getIcon()}
            <Text size="sm" fw={500}>
              {progress.label || "Processing..."}
            </Text>
          </Group>
          <Text size="sm" fw={600} c={`${getColor()}.7`}>
            {progress.value}%
          </Text>
        </Group>
        <Progress
          value={progress.value}
          color={getColor()}
          size="md"
          radius="md"
          animated
          striped={progress.value < 100}
        />
      </Stack>
    </Paper>
  );
}
