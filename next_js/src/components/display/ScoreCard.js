"use client";

import {
  Paper,
  Stack,
  Text,
  Progress,
  Divider,
  Badge,
  Accordion,
} from "@mantine/core";
import { formatScore } from "../../lib/utils";

export function ScoreCard({ item, rubricItem }) {
  const score = item.score || 0;
  const maxScore = 100;
  const percentage = (score / maxScore) * 100;

  const hasComprehensiveFeedback =
    item.evidence ||
    item.evaluation ||
    item.completeness_percentage !== undefined ||
    item.strengths ||
    item.gaps ||
    item.guidance ||
    item.significance;

  return (
    <Stack gap="sm">
      {item.justification && !hasComprehensiveFeedback && (
        <div>
          <Text size="xs" fw={600} c="dimmed" mb="xs">
            Justification:
          </Text>
          <Text size="xs" c="gray.7" style={{ whiteSpace: "pre-wrap" }}>
            {item.justification}
          </Text>
        </div>
      )}

      {hasComprehensiveFeedback && (
        <Accordion variant="separated" radius="md" defaultValue="feedback">
          <Accordion.Item value="feedback">
            <Accordion.Control>
              <Text size="sm" fw={600}>
                📋 Detailed Feedback
              </Text>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs" mt="xs">
                {item.evidence && item.evidence.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#f0f9ff" }}
                  >
                    <Text size="xs" fw={600} c="blue.7" mb={4} ta="center">
                      📎 Evidence:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.evidence}
                    </Text>
                  </Paper>
                )}

                {item.evaluation && item.evaluation.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#fef3f2" }}
                  >
                    <Text size="xs" fw={600} c="blue.7" mb={4} ta="center">
                      🔍 Evaluation:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.evaluation}
                    </Text>
                  </Paper>
                )}

                {item.strengths && item.strengths.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#f0fdf4" }}
                  >
                    <Text size="xs" fw={600} c="green.7" mb={4} ta="center">
                      ✅ Strengths:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.strengths}
                    </Text>
                  </Paper>
                )}

                {item.gaps && item.gaps.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#fff7ed" }}
                  >
                    <Text size="xs" fw={600} c="red.7" mb={4} ta="center">
                      ⚠️ Gaps & Weaknesses:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.gaps}
                    </Text>
                  </Paper>
                )}

                {item.guidance && item.guidance.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#fefce8" }}
                  >
                    <Text size="xs" fw={600} c="orange.7" mb={4} ta="center">
                      💡 Guidance for Improvement:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.guidance}
                    </Text>
                  </Paper>
                )}

                {item.significance && item.significance.trim() && (
                  <Paper
                    p="sm"
                    withBorder
                    radius="sm"
                    style={{ backgroundColor: "#faf5ff" }}
                  >
                    <Text size="xs" fw={600} c="violet.7" mb={4} ta="center">
                      🎯 Significance:
                    </Text>
                    <Text
                      size="xs"
                      c="gray.8"
                      style={{ whiteSpace: "pre-wrap" }}
                    >
                      {item.significance}
                    </Text>
                  </Paper>
                )}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}
    </Stack>
  );
}
