"use client";

import {
  Paper,
  Stack,
  Title,
  Text,
  Divider,
  Center,
  Box,
  Button,
  Group,
} from "@mantine/core";
import { IconClipboardCheck, IconMessage } from "@tabler/icons-react";
import { ScoreCard } from "./ScoreCard";
import { formatScore } from "../../lib/utils";
import { NarrativeSection } from "./NarrativeSection";

export function ResultsPanel({ result, selectedRubric, onOpenChat }) {
  if (!result) {
    return (
      <Paper
        p="xl"
        withBorder
        radius="md"
        style={{ height: "100%", minHeight: 400 }}
      >
        <Center style={{ height: "100%", flexDirection: "column", gap: 16 }}>
          <IconClipboardCheck size={48} color="var(--mantine-color-gray-4)" />
          <Text size="sm" c="dimmed" ta="center">
            Evaluation results will appear here
          </Text>
          <Text size="xs" c="dimmed" ta="center">
            Upload resources and run evaluation to see results
          </Text>
        </Center>
      </Paper>
    );
  }

  // Check if this is narrative format or structured format
  const isNarrative = result.narrative_evaluation || result.narrative_strengths;

  if (isNarrative) {
    // NARRATIVE FORMAT - Display as panels
    return (
      <Paper
        p="lg"
        withBorder
        radius="md"
        style={{
          maxHeight: "calc(100vh - 200px)",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Stack gap="md">
          <Title order={3}>Evaluation Results</Title>

          {result.narrative_evaluation && (
            <Box>
              <Text
                size="xs"
                c="dimmed"
                tt="uppercase"
                fw={600}
                mb="xs"
                ta="center"
              >
                📋 Evaluation
              </Text>
              <NarrativeSection content={result.narrative_evaluation} />
            </Box>
          )}

          {result.narrative_strengths && (
            <>
              <Divider />
              <Box>
                <Text
                  size="xs"
                  c="dimmed"
                  tt="uppercase"
                  fw={600}
                  mb="xs"
                  ta="center"
                >
                  ✅ Strengths
                </Text>
                <NarrativeSection content={result.narrative_strengths} />
              </Box>
            </>
          )}

          {result.narrative_gaps && (
            <>
              <Divider />
              <Box>
                <Text
                  size="xs"
                  c="dimmed"
                  tt="uppercase"
                  fw={600}
                  mb="xs"
                  ta="center"
                >
                  ⚠️ Gaps & Areas for Improvement
                </Text>
                <NarrativeSection content={result.narrative_gaps} />
              </Box>
            </>
          )}

          {result.narrative_guidance && (
            <>
              <Divider />
              <Box>
                <Text
                  size="xs"
                  c="dimmed"
                  tt="uppercase"
                  fw={600}
                  mb="xs"
                  ta="center"
                >
                  💡 Guidance for Improvement
                </Text>
                <NarrativeSection content={result.narrative_guidance} />
              </Box>
            </>
          )}
        </Stack>
      </Paper>
    );
  }

  // STRUCTURED FORMAT - Display as before (backward compatibility)
  return (
    <Paper
      p="lg"
      withBorder
      radius="md"
      style={{
        maxHeight: "calc(100vh - 200px)",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Stack gap="md">
        <Title order={3}>Evaluation Results</Title>

        <div>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb="xs">
            Total Score
          </Text>
          <Title order={1} c="orange.7">
            {result.total ? formatScore(result.total) : "N/A"} / 100
          </Title>
        </div>

        {result.items && result.items.length > 0 && (
          <>
            <Divider />
            <Stack gap="md">
              {result.items.length > 1 && (
                <Text size="sm" fw={600}>
                  Item Scores ({result.items.length})
                </Text>
              )}
              {result.items.map((item, idx) => {
                const rubricItem = selectedRubric?.items?.find(
                  (ri) => ri.id === item.rubric_item_id,
                );
                return (
                  <ScoreCard key={idx} item={item} rubricItem={rubricItem} />
                );
              })}
            </Stack>
          </>
        )}
      </Stack>
    </Paper>
  );
}
