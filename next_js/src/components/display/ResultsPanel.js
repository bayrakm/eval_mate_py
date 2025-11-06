"use client";

import { Paper, Stack, Title, Text, Divider, Center } from "@mantine/core";
import { IconClipboardCheck } from "@tabler/icons-react";
import { ScoreCard } from "./ScoreCard";
import { formatScore } from "../../lib/utils";

export function ResultsPanel({ result, selectedRubric }) {
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
        <div>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb="xs">
            Total Score
          </Text>
          <Title order={1} c="orange.7">
            {formatScore(result.total)} / 100
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
                  (ri) => ri.id === item.rubric_item_id
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
