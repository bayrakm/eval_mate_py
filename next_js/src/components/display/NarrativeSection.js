"use client";

import { Stack, Box, Text } from "@mantine/core";
import { parseNarrativeContent } from "../../lib/utils";

export function NarrativeSection({ content }) {
  if (!content) {
    return null;
  }

  const items = parseNarrativeContent(content);

  if (items.length === 0) {
    return (
      <Text size="sm" style={{ lineHeight: 1.7, color: "var(--mantine-color-gray-7)" }}>
        {content}
      </Text>
    );
  }

  return (
    <Stack gap="lg">
      {items.map((item, idx) => (
        <Box key={idx}>
          {item.title && (
            <Text
              size="sm"
              fw={500}
              style={{
                marginBottom: 4,
                color: "var(--mantine-color-gray-8)",
                fontSize: "0.85rem",
              }}
            >
              {idx + 1}. {item.title}
            </Text>
          )}
          <Text
            size="sm"
            style={{
              lineHeight: 1.55,
              textAlign: "justify",
              color: "var(--mantine-color-gray-7)",
              fontSize: "0.8rem",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word",
            }}
          >
            {item.description}
          </Text>
        </Box>
      ))}
    </Stack>
  );
}
