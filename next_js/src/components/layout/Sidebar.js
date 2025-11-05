"use client";

import { useState, useEffect } from "react";
import { Tabs, Stack, Text, Paper, Divider } from "@mantine/core";
import { IconFileText, IconHelpCircle, IconUser } from "@tabler/icons-react";
import { RubricSelector } from "../resources/RubricSelector";
import { QuestionSelector } from "../resources/QuestionSelector";
import { SubmissionSelector } from "../resources/SubmissionSelector";

export function Sidebar({
  selectedRubric,
  selectedQuestion,
  selectedSubmission,
  onRubricSelect,
  onQuestionSelect,
  onSubmissionSelect,
  onLoadRubrics,
  onLoadQuestions,
  onLoadSubmissions,
  onGetRubric,
  onGetQuestion,
  onGetSubmission,
}) {
  const [activeTab, setActiveTab] = useState("rubrics");

  // Helper to check if resources are valid
  const hasRubric = Boolean(selectedRubric?.id);
  const hasQuestion = Boolean(selectedQuestion?.id);

  // Auto-switch tabs when resources are selected
  useEffect(() => {
    if (hasRubric && hasQuestion) {
      setActiveTab("submissions");
    } else if (hasRubric) {
      setActiveTab("questions");
    }
  }, [hasRubric, hasQuestion]);

  return (
    <Stack gap="md">
      <div>
        <Text size="lg" fw={700} c="orange.7" mb="xs">
          Resources
        </Text>
        <Text size="xs" c="dimmed">
          Select or upload resources for evaluation
        </Text>
      </div>

      <Divider />

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="rubrics" leftSection={<IconFileText size={16} />}>
            Rubrics
          </Tabs.Tab>
          <Tabs.Tab
            value="questions"
            leftSection={<IconHelpCircle size={16} />}
            disabled={!hasRubric}
          >
            Questions
          </Tabs.Tab>
          <Tabs.Tab
            value="submissions"
            leftSection={<IconUser size={16} />}
            disabled={!hasRubric || !hasQuestion}
          >
            Submissions
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="rubrics" pt="md">
          <RubricSelector
            selectedRubric={selectedRubric}
            onSelect={onRubricSelect}
            onLoad={onLoadRubrics}
            onGet={onGetRubric}
          />
        </Tabs.Panel>

        <Tabs.Panel value="questions" pt="md">
          <QuestionSelector
            selectedQuestion={selectedQuestion}
            rubricId={selectedRubric?.id}
            onSelect={onQuestionSelect}
            onLoad={onLoadQuestions}
            onGet={onGetQuestion}
          />
        </Tabs.Panel>

        <Tabs.Panel value="submissions" pt="md">
          <SubmissionSelector
            selectedSubmission={selectedSubmission}
            rubricId={selectedRubric?.id}
            questionId={selectedQuestion?.id}
            onSelect={onSubmissionSelect}
            onLoad={onLoadSubmissions}
            onGet={onGetSubmission}
          />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
