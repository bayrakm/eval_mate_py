"use client";

import { Group, Button, Stack, Card, Title, Text, Loader, Flex } from "@mantine/core";
import { IconArrowRight } from "@tabler/icons-react";
import { useState, useEffect } from "react";
import { LOADING_STATES } from "../../lib/constants";

const trivias = [
  "AI tutoring systems have shown to improve student learning outcomes by up to 30% compared to traditional methods.",
  "Generative AI can create personalized learning paths adapted to each student's pace, learning style, and preferences.",
  "AI-powered plagiarism detection tools can now identify content from large language models with 98% accuracy.",
  "Machine learning algorithms can predict student dropout risk with 85% accuracy by analyzing engagement patterns.",
  "AI code review systems can identify bugs and suggest improvements faster than human reviewers.",
  "Natural language processing enables AI to provide detailed, personalized feedback on student submissions in seconds.",
  "AI analytics dashboards help educators identify at-risk students and intervene before performance declines significantly.",
  "Large language models like GPT-4 can now understand and explain complex programming concepts in multiple languages.",
  "AI-powered educational platforms have reached over 1 billion learners worldwide in 2024.",
  "Real-time AI feedback during coding helps students learn from mistakes immediately rather than after submission.",
];

const shuffleArray = (array) => {
  const newArray = [...array];
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
};

export function ActionButtons({ onEvaluate, canEvaluate, loading }) {
  const [currentTrivia, setCurrentTrivia] = useState(0);
  const [triviasArray] = useState(() => shuffleArray(trivias));

  const isBuilding = loading === LOADING_STATES.BUILDING;
  const isEvaluating = loading === LOADING_STATES.EVALUATING;
  const isLoading = isBuilding || isEvaluating;

  const isEvaluateDisabled = !canEvaluate || isBuilding || isEvaluating;

  useEffect(() => {
    if (!isLoading) return;

    const interval = setInterval(() => {
      setCurrentTrivia((prev) => (prev + 1) % triviasArray.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [isLoading, triviasArray.length]);

  return (
    <Stack align="center" gap="md">
      <Group justify="center" gap="md">
        <Button
          leftSection={<IconArrowRight size={18} />}
          onClick={onEvaluate}
          disabled={isEvaluateDisabled}
          color="orange"
          size="lg"
        >
          Run Evaluation
        </Button>
      </Group>

      {isLoading && (
        <Card
          shadow="sm"
          padding="lg"
          radius="md"
          withBorder
          mt="md"
          w="100%"
          maw={500}
        >
          <Flex justify="center" align="center" gap="md" mb="md">
            <Loader type="dots" color="orange" size="lg" />
          </Flex>
          <Title order={6} ta="center" mb="md">
            While we&apos;re working, here are some AI facts:
          </Title>
          <Text size="sm" ta="center" style={{ minHeight: "60px" }}>
            &quot;{triviasArray[currentTrivia]}&quot;
          </Text>
        </Card>
      )}
    </Stack>
  );
}
