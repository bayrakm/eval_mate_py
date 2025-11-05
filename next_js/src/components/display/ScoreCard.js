"use client";

import { Paper, Stack, Text, Progress, Divider } from "@mantine/core";
import { formatScore } from "../../lib/utils";

export function ScoreCard({ item, rubricItem }) {
  const score = item.score || 0;
  const maxScore = 100;
  const percentage = (score / maxScore) * 100;

  return (
    <Paper p="md" withBorder radius="md" shadow="sm">
      <Stack gap="sm">
        <div>
          <Text size="sm" fw={600} c="orange.7">
            {rubricItem?.title || "Rubric Item"}
          </Text>
          {rubricItem?.description && (
            <Text size="xs" c="dimmed">
              {rubricItem.description}
            </Text>
          )}
        </div>

        <Divider />

        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: "8px",
            }}
          >
            <Text size="lg" fw={700} c="orange.7">
              {formatScore(score)}
            </Text>
            <Text size="sm" c="dimmed">
              / {maxScore}
            </Text>
          </div>

          <Progress
            value={percentage}
            color="orange"
            size="lg"
            radius="md"
            animated
          />
        </div>

        {item.justification && (
          <div>
            <Text size="xs" fw={600} c="dimmed" mb="xs">
              Justification:
            </Text>
            <Text size="xs" c="gray.7">
              {item.justification}
            </Text>
          </div>
        )}

        {item.evidence_block_ids && item.evidence_block_ids.length > 0 && (
          <div>
            <Text size="xs" fw={600} c="dimmed">
              Evidence: {item.evidence_block_ids.length} block(s)
            </Text>
          </div>
        )}
      </Stack>
    </Paper>
  );
}
