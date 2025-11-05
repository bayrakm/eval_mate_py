"use client";

import { Paper, Stack, Title, Text, Divider, ScrollArea } from "@mantine/core";
import { ScoreCard } from "./ScoreCard";
import { formatScore } from "../../lib/utils";

export function ResultsPanel({ result, selectedRubric }) {
  if (!result) {
    return (
      <Paper p="xl" withBorder radius="md" style={{ height: "100%" }}>
        <Text size="sm" c="dimmed" ta="center">
          Hasil evaluasi akan muncul di sini
        </Text>
      </Paper>
    );
  }

  return (
    <ScrollArea h="100%">
      <Paper p="lg" withBorder radius="md" style={{ height: "100%" }}>
        <Stack gap="md">
          <div>
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb="xs">
              Total Score
            </Text>
            <Title order={1} c="orange.7">
              {formatScore(result.total)} / 100
            </Title>
          </div>

          <Divider />

          {result.overall_feedback && (
            <Stack gap="xs">
              <Text size="sm" fw={600}>
                Overall Feedback
              </Text>
              <Text size="sm" c="dimmed">
                {result.overall_feedback}
              </Text>
            </Stack>
          )}

          {result.items && result.items.length > 0 && (
            <>
              <Divider />
              <Stack gap="md">
                <Text size="sm" fw={600}>
                  Item Scores ({result.items.length})
                </Text>
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
    </ScrollArea>
  );
}
