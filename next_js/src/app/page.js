"use client";

import { useState, useCallback, useMemo } from "react";
import {
  Container,
  Grid,
  Stack,
  Paper,
  Title,
  Text,
  Divider,
  Group,
  Badge,
  Button,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useAppState } from "../hooks/useAppState";
import { AppLayout } from "../components/layout/AppLayout";
import { UploadRubric } from "../components/upload/UploadRubric";
import { UploadQuestion } from "../components/upload/UploadQuestion";
import { UploadSubmission } from "../components/upload/UploadSubmission";
import { ActionButtons } from "../components/actions/ActionButtons";
import { MessageList } from "../components/display/MessageList";
import { ResultsPanel } from "../components/display/ResultsPanel";
import { ProgressIndicator } from "../components/display/ProgressIndicator";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import * as api from "../lib/apiClient";
import { LOADING_STATES } from "../lib/constants";
import { signOut, useSession } from "next-auth/react";
import { IconLogout } from "@tabler/icons-react";

export default function HomePage() {
  const {
    state,
    setState,
    addMessage,
    setLoading,
    setProgress,
    clearProgress,
    resetSelections,
  } = useAppState();

  const { data: session } = useSession();

  const handleRubricUpload = useCallback(
    async (file) => {
      const startTime = Date.now();
      const minDuration = 800;

      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(`Uploading rubric: ${file.name}`, "user");

        setProgress({
          type: "upload",
          value: 0,
          label: `Uploading ${file.name}...`,
          target: "rubric",
        });

        const response = await api.uploadRubric(file, {});

        const elapsed = Date.now() - startTime;
        if (elapsed < minDuration) {
          await new Promise((resolve) =>
            setTimeout(resolve, minDuration - elapsed)
          );
        }

        setProgress({
          type: "upload",
          value: 100,
          label: `Upload complete!`,
          target: "rubric",
        });

        await new Promise((resolve) => setTimeout(resolve, 300));

        const rubric = await api.getRubric(response.meta.id);

        setState((prev) => ({
          ...prev,
          selectedRubric: rubric,
          selectedQuestion: null,
          selectedSubmission: null,
          fusion: null,
          result: null,
        }));

        clearProgress();
        addMessage(
          `✅ Rubric uploaded successfully: ${rubric.assignment} (${
            rubric.items?.length || 0
          } items)`
        );
        notifications.show({
          title: "Success",
          message: "Rubric uploaded successfully",
          color: "green",
        });
      } catch (error) {
        clearProgress();
        const message = error.message || "Failed to upload rubric";
        addMessage(`❌ ${message}`);
        notifications.show({
          title: "Error",
          message,
          color: "red",
        });
      } finally {
        setLoading(LOADING_STATES.IDLE);
      }
    },
    [addMessage, setLoading, setState, setProgress, clearProgress]
  );

  const handleQuestionUpload = useCallback(
    async (file, title) => {
      if (!state.selectedRubric) {
        addMessage("❌ Please select a rubric first");
        notifications.show({
          title: "Warning",
          message: "Please select a rubric first",
          color: "orange",
        });
        return;
      }

      const startTime = Date.now();
      const minDuration = 800;

      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(`Uploading question: ${file.name}`, "user");

        setProgress({
          type: "upload",
          value: 0,
          label: `Uploading ${file.name}...`,
          target: "question",
        });

        const response = await api.uploadQuestion(file, {
          rubric_id: state.selectedRubric.id,
          title: title,
        });

        const elapsed = Date.now() - startTime;
        if (elapsed < minDuration) {
          await new Promise((resolve) =>
            setTimeout(resolve, minDuration - elapsed)
          );
        }

        setProgress({
          type: "upload",
          value: 100,
          label: `Upload complete!`,
          target: "question",
        });

        await new Promise((resolve) => setTimeout(resolve, 300));

        const question = await api.getQuestion(response.meta.id);

        setState((prev) => ({
          ...prev,
          selectedQuestion: question,
          selectedSubmission: null,
          fusion: null,
          result: null,
        }));

        clearProgress();
        addMessage(`✅ Question uploaded successfully: ${question.title}`);
        notifications.show({
          title: "Success",
          message: "Question uploaded successfully",
          color: "green",
        });
      } catch (error) {
        clearProgress();
        const message = error.message || "Failed to upload question";
        addMessage(`❌ ${message}`);
        notifications.show({
          title: "Error",
          message,
          color: "red",
        });
      } finally {
        setLoading(LOADING_STATES.IDLE);
      }
    },
    [
      state.selectedRubric,
      addMessage,
      setLoading,
      setState,
      setProgress,
      clearProgress,
    ]
  );

  const handleSubmissionUpload = useCallback(
    async (file, studentHandle) => {
      if (!state.selectedRubric || !state.selectedQuestion) {
        addMessage("❌ Please select a rubric and question first");
        notifications.show({
          title: "Warning",
          message: "Please select a rubric and question first",
          color: "orange",
        });
        return;
      }

      const startTime = Date.now();
      const minDuration = 800;

      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(
          `Uploading submission for ${studentHandle}: ${file.name}`,
          "user"
        );

        setProgress({
          type: "upload",
          value: 0,
          label: `Uploading ${file.name}...`,
          target: "submission",
        });

        const response = await api.uploadSubmission(file, {
          rubric_id: state.selectedRubric.id,
          question_id: state.selectedQuestion.id,
          student_handle: studentHandle,
        });

        const elapsed = Date.now() - startTime;
        if (elapsed < minDuration) {
          await new Promise((resolve) =>
            setTimeout(resolve, minDuration - elapsed)
          );
        }

        setProgress({
          type: "upload",
          value: 100,
          label: `Upload complete!`,
          target: "submission",
        });

        await new Promise((resolve) => setTimeout(resolve, 300));

        const submission = await api.getSubmission(response.meta.id);

        setState((prev) => ({
          ...prev,
          selectedSubmission: submission,
          fusion: null,
          result: null,
        }));

        clearProgress();
        addMessage(
          `✅ Submission uploaded successfully for ${submission.student_handle}`
        );
        notifications.show({
          title: "Success",
          message: "Submission uploaded successfully",
          color: "green",
        });
      } catch (error) {
        clearProgress();
        const message = error.message || "Failed to upload submission";
        addMessage(`❌ ${message}`);
        notifications.show({
          title: "Error",
          message,
          color: "red",
        });
      } finally {
        setLoading(LOADING_STATES.IDLE);
      }
    },
    [
      state.selectedRubric,
      state.selectedQuestion,
      addMessage,
      setLoading,
      setState,
      setProgress,
      clearProgress,
    ]
  );

  const handleRubricSelect = useCallback(
    (rubric) => {
      setState((prev) => ({
        ...prev,
        selectedRubric: rubric,
        selectedQuestion: null,
        selectedSubmission: null,
        fusion: null,
        result: null,
      }));
      addMessage(
        `Selected rubric: ${rubric.assignment} (${
          rubric.items?.length || 0
        } items)`
      );
    },
    [addMessage, setState]
  );

  const handleQuestionSelect = useCallback(
    (question) => {
      setState((prev) => ({
        ...prev,
        selectedQuestion: question,
        selectedSubmission: null,
        fusion: null,
        result: null,
      }));
      addMessage(`Selected question: ${question.title}`);
    },
    [addMessage, setState]
  );

  const handleSubmissionSelect = useCallback(
    (submission) => {
      setState((prev) => ({
        ...prev,
        selectedSubmission: submission,
        fusion: null,
        result: null,
      }));
      addMessage(`Selected submission from: ${submission.student_handle}`);
    },
    [addMessage, setState]
  );

  const handleEvaluate = useCallback(async () => {
    if (
      !state.selectedRubric ||
      !state.selectedQuestion ||
      !state.selectedSubmission
    ) {
      addMessage("❌ Please select a rubric, question, and submission first");
      notifications.show({
        title: "Warning",
        message: "Please select all required resources",
        color: "orange",
      });
      return;
    }

    let progressInterval = null;
    const startTime = Date.now();
    try {
      // Step 1: Build Fusion if not already built
      if (!state.fusion) {
        setLoading(LOADING_STATES.BUILDING);
        addMessage("Building fusion context...", "user");

        let progressValue = 0;
        setProgress({
          type: "building",
          value: 0,
          label: "Building fusion context...",
        });

        progressInterval = setInterval(() => {
          progressValue = Math.min(progressValue + 2, 85);
          setProgress({
            type: "building",
            value: progressValue,
            label: "Processing documents and building context...",
          });
        }, 400);

        const fusion = await api.buildFusion(
          state.selectedRubric.id,
          state.selectedQuestion.id,
          state.selectedSubmission.id
        );

        const buildDuration = Date.now() - startTime;
        const minBuildDuration = 3000; // 3 seconds minimum

        if (progressInterval) {
          clearInterval(progressInterval);
          progressInterval = null;
        }

        setProgress({
          type: "building",
          value: 100,
          label: "Fusion context built successfully!",
        });

        setState((prev) => ({
          ...prev,
          fusion,
          result: null,
        }));

        addMessage(
          `✅ Fusion context built! Token estimate: ${fusion.token_estimate}, Visual count: ${fusion.visual_count}`
        );

        // Ensure minimum duration for visual feedback
        if (buildDuration < minBuildDuration) {
          await new Promise((resolve) =>
            setTimeout(resolve, minBuildDuration - buildDuration)
          );
        }

        // Wait additional 2 seconds before proceeding to evaluation
        await new Promise((resolve) => setTimeout(resolve, 2000));
        clearProgress();
      }

      // Step 2: Run Evaluation
      setLoading(LOADING_STATES.EVALUATING);
      addMessage("Running LLM evaluation...", "user");

      let progressValue = 0;
      setProgress({
        type: "evaluating",
        value: 0,
        label: "Running LLM evaluation...",
      });

      progressInterval = setInterval(() => {
        progressValue = Math.min(progressValue + 3, 90);
        setProgress({
          type: "evaluating",
          value: progressValue,
          label: "Analyzing submission and generating feedback...",
        });
      }, 300);

      // Get the current fusion state (either from step 1 or existing state)
      const currentFusion =
        state.fusion ||
        (await api.buildFusion(
          state.selectedRubric.id,
          state.selectedQuestion.id,
          state.selectedSubmission.id
        ));

      const result = (await api.evaluate(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      )) || {
        total: 0,
        items: [],
        overall_feedback: "Evaluation completed",
      };

      if (progressInterval) {
        clearInterval(progressInterval);
      }

      setProgress({
        type: "evaluating",
        value: 100,
        label: "Evaluation complete!",
      });

      setState((prev) => ({
        ...prev,
        result,
      }));

      setTimeout(() => clearProgress(), 500);

      // Handle both narrative and structured formats
      const isNarrative =
        result.narrative_evaluation || result.narrative_strengths;
      if (isNarrative) {
        addMessage(`✅ Evaluation complete! Narrative feedback generated.`);
        notifications.show({
          title: "Success",
          message: "Evaluation complete! Feedback generated.",
          color: "green",
        });
      } else {
        addMessage(
          `✅ Evaluation complete! Total score: ${
            result.total?.toFixed(1) || "N/A"
          }/100 (${result.items?.length || 0} items graded)`
        );
        notifications.show({
          title: "Success",
          message: `Evaluation complete! Score: ${
            result.total?.toFixed(1) || "N/A"
          }/100`,
          color: "green",
        });
      }
    } catch (error) {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      clearProgress();
      const message = error.message || "Failed to run evaluation";
      addMessage(`❌ ${message}`);
      notifications.show({
        title: "Error",
        message,
        color: "red",
      });
    } finally {
      setLoading(LOADING_STATES.IDLE);
    }
  }, [
    state.selectedRubric,
    state.selectedQuestion,
    state.selectedSubmission,
    state.fusion,
    addMessage,
    setLoading,
    setState,
    setProgress,
    clearProgress,
  ]);

  const rubricId = state.selectedRubric?.id;
  const questionId = state.selectedQuestion?.id;

  const canUploadQuestion = Boolean(rubricId);
  const canUploadSubmission = Boolean(rubricId && questionId);
  const canEvaluate = Boolean(
    rubricId && questionId && state.selectedSubmission?.id
  );

  return (
    <ProtectedRoute>
      <AppLayout sidebarContent={null}>
        <Container size="xl" p="md" style={{ margin: "0 auto" }}>
          <Grid gutter="md">
            <Grid.Col span={{ base: 12, lg: 8 }}>
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div>
                    <Title order={2} c="orange.7" mb="xs">
                      EvalMate
                    </Title>
                    <Text size="sm" c="dimmed">
                      Intelligent Student Assignment Feedback System
                    </Text>
                  </div>
                  <Stack gap={4} align="flex-end">
                    <Text size="xs" c="dimmed">
                      {session?.user?.email || "demo@example.com"}
                    </Text>
                    <Button
                      size="xs"
                      variant="light"
                      color="orange"
                      leftSection={<IconLogout size={14} />}
                      onClick={() => signOut({ callbackUrl: "/login" })}
                    >
                      Sign Out
                    </Button>
                  </Stack>
                </Group>

                <Divider />

                <Stack gap="lg">
                  <div>
                    <Group gap="xs" mb="md">
                      <Badge size="lg" variant="filled" color="orange">
                        Step 1
                      </Badge>
                      <Text size="sm" fw={600} c="dimmed">
                        Upload Resources
                      </Text>
                    </Group>
                    <Stack gap="md">
                      <UploadRubric
                        onUpload={handleRubricUpload}
                        loading={state.loading === LOADING_STATES.UPLOADING}
                        isCompleted={!!state.selectedRubric}
                        progress={
                          state.progress?.type === "upload" &&
                          state.progress?.target === "rubric" &&
                          state.loading === LOADING_STATES.UPLOADING
                            ? state.progress
                            : null
                        }
                      />

                      <UploadQuestion
                        onUpload={handleQuestionUpload}
                        loading={state.loading === LOADING_STATES.UPLOADING}
                        disabled={!canUploadQuestion}
                        isCompleted={!!state.selectedQuestion}
                        progress={
                          state.progress?.type === "upload" &&
                          state.progress?.target === "question" &&
                          state.loading === LOADING_STATES.UPLOADING
                            ? state.progress
                            : null
                        }
                      />

                      <UploadSubmission
                        onUpload={handleSubmissionUpload}
                        loading={state.loading === LOADING_STATES.UPLOADING}
                        disabled={!canUploadSubmission}
                        isCompleted={!!state.selectedSubmission}
                        completedSubmission={state.selectedSubmission}
                        progress={
                          state.progress?.type === "upload" &&
                          state.progress?.target === "submission" &&
                          state.loading === LOADING_STATES.UPLOADING
                            ? state.progress
                            : null
                        }
                      />
                    </Stack>
                  </div>

                  <Divider />

                  <div>
                    <Group gap="xs" mb="md">
                      <Badge size="lg" variant="filled" color="orange">
                        Step 2
                      </Badge>
                      <Text size="sm" fw={600} c="dimmed">
                        Evaluate
                      </Text>
                    </Group>
                    <Stack gap="md">
                      <ActionButtons
                        onEvaluate={handleEvaluate}
                        canEvaluate={canEvaluate}
                        loading={state.loading}
                      />
                      {(state.progress?.type === "building" ||
                        state.progress?.type === "evaluating") && (
                        <ProgressIndicator progress={state.progress} />
                      )}
                    </Stack>
                  </div>

                  <Divider />
                  <div>
                    <ResultsPanel
                      result={state.result}
                      selectedRubric={state.selectedRubric}
                    />
                  </div>
                </Stack>
              </Stack>
            </Grid.Col>

            <Grid.Col
              span={{ base: 12, lg: 4 }}
              className="sticky-results-panel"
            >
              <Group gap="xs" mb="md">
                <Text size="sm" fw={600}>
                  Messages
                </Text>
              </Group>
              <MessageList messages={state.messages} />
            </Grid.Col>
          </Grid>
        </Container>
      </AppLayout>
    </ProtectedRoute>
  );
}
