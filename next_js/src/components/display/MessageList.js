"use client";

import { Stack, Paper, Text, ScrollArea } from "@mantine/core";
import { formatDate } from "../../lib/utils";

export function MessageList({ messages }) {
  if (!messages || messages.length === 0) {
    return (
      <Paper p="xl" withBorder radius="md" style={{ textAlign: "center" }}>
        <Text size="sm" c="dimmed">
          No messages yet. Start by uploading resources or running evaluation.
        </Text>
      </Paper>
    );
  }

  return (
    <ScrollArea h={400} style={{ maxHeight: "60vh" }}>
      <Stack gap="xs">
        {messages.map((msg) => (
          <Paper
            key={msg.id}
            p="sm"
            withBorder
            radius="md"
            bg={msg.type === "user" ? "orange.0" : "gray.0"}
          >
            <Text size="sm" c={msg.type === "user" ? "orange.7" : "gray.7"}>
              {msg.content}
            </Text>
            {msg.timestamp && (
              <Text size="xs" c="dimmed" mt="xs">
                {formatDate(msg.timestamp)}
              </Text>
            )}
          </Paper>
        ))}
      </Stack>
    </ScrollArea>
  );
}
