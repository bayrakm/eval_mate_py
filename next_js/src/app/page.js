"use client";

import { useState, useCallback, useMemo } from "react";
import { Container, Grid, Stack, Paper, Title, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useAppState } from "../hooks/useAppState";
import { AppLayout } from "../components/layout/AppLayout";
import { Sidebar } from "../components/layout/Sidebar";
import { UploadRubric } from "../components/upload/UploadRubric";
import { UploadQuestion } from "../components/upload/UploadQuestion";
import { UploadSubmission } from "../components/upload/UploadSubmission";
import { ActionButtons } from "../components/actions/ActionButtons";
import { MessageList } from "../components/display/MessageList";
import { ResultsPanel } from "../components/display/ResultsPanel";
import * as api from "../lib/apiClient";
import { LOADING_STATES } from "../lib/constants";

export default function HomePage() {
  const { state, setState, addMessage, setLoading, resetSelections } =
    useAppState();

  // Upload handlers
  const handleRubricUpload = useCallback(
    async (file) => {
      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(`Uploading rubric: ${file.name}`, "user");

        const response = await api.uploadRubric(file);
        const rubric = await api.getRubric(response.meta.id);

        console.log("🔍 Uploaded Rubric:", {
          id: rubric.id,
          hasId: !!rubric.id,
          type: typeof rubric.id,
          keys: Object.keys(rubric),
        });

        setState((prev) => ({
          ...prev,
          selectedRubric: rubric,
          selectedQuestion: null,
          selectedSubmission: null,
          fusion: null,
          result: null,
        }));

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
    [addMessage, setLoading, setState]
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

      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(`Uploading question: ${file.name}`, "user");

        const response = await api.uploadQuestion(
          state.selectedRubric.id,
          file,
          title
        );
        const question = await api.getQuestion(response.meta.id);

        console.log("🔍 Uploaded Question:", {
          id: question.id,
          hasId: !!question.id,
          keys: Object.keys(question),
        });

        setState((prev) => {
          console.log("🔍 Setting question - prev state:", {
            hasRubric: !!prev.selectedRubric,
            rubricId: prev.selectedRubric?.id,
          });
          return {
            ...prev,
            selectedQuestion: question,
            selectedSubmission: null,
            fusion: null,
            result: null,
          };
        });

        addMessage(`✅ Question uploaded successfully: ${question.title}`);
        notifications.show({
          title: "Success",
          message: "Question uploaded successfully",
          color: "green",
        });
      } catch (error) {
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
    [state.selectedRubric, addMessage, setLoading, setState]
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

      try {
        setLoading(LOADING_STATES.UPLOADING);
        addMessage(
          `Uploading submission for ${studentHandle}: ${file.name}`,
          "user"
        );

        const response = await api.uploadSubmission(
          state.selectedRubric.id,
          state.selectedQuestion.id,
          studentHandle,
          file
        );
        console.log("Upload response:", response);
        const submission = await api.getSubmission(response.meta.id);
        console.log("Submission from API:", submission);
        console.log("Submission ID:", submission?.id);
        console.log(
          "Submission keys:",
          submission ? Object.keys(submission) : "null"
        );

        setState((prev) => ({
          ...prev,
          selectedSubmission: submission,
          fusion: null,
          result: null,
        }));

        addMessage(
          `✅ Submission uploaded successfully for ${submission.student_handle}`
        );
        notifications.show({
          title: "Success",
          message: "Submission uploaded successfully",
          color: "green",
        });
      } catch (error) {
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
    ]
  );

  // Resource selection handlers
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

  // Fusion and evaluation handlers
  const handleBuildFusion = useCallback(async () => {
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

    try {
      setLoading(LOADING_STATES.BUILDING);
      addMessage("Building fusion context...", "user");

      const fusion = await api.buildFusion(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      );

      setState((prev) => ({
        ...prev,
        fusion,
        result: null,
      }));

      addMessage(
        `✅ Fusion context built successfully! Token estimate: ${fusion.token_estimate}, Visual count: ${fusion.visual_count}`
      );
      notifications.show({
        title: "Success",
        message: "Fusion context built successfully",
        color: "green",
      });
    } catch (error) {
      const message = error.message || "Failed to build fusion context";
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
    addMessage,
    setLoading,
    setState,
  ]);

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

    if (!state.fusion) {
      addMessage("❌ Please build fusion context first");
      notifications.show({
        title: "Warning",
        message: "Please build fusion context first",
        color: "orange",
      });
      return;
    }

    try {
      setLoading(LOADING_STATES.EVALUATING);
      addMessage("Running LLM evaluation...", "user");

      const result = await api.evaluate(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      );

      setState((prev) => ({
        ...prev,
        result,
      }));

      addMessage(
        `✅ Evaluation complete! Total score: ${result.total.toFixed(1)}/100 (${
          result.items?.length || 0
        } items graded)`
      );
      notifications.show({
        title: "Success",
        message: `Evaluation complete! Score: ${result.total.toFixed(1)}/100`,
        color: "green",
      });
    } catch (error) {
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
  ]);

  // Capability checks - langsung hitung, tidak pakai useMemo untuk debugging
  const rubricId = state.selectedRubric?.id;
  const questionId = state.selectedQuestion?.id;

  const canUploadQuestion = Boolean(rubricId);
  const canUploadSubmission = Boolean(rubricId && questionId);
  const canBuildFusion = Boolean(
    rubricId && questionId && state.selectedSubmission?.id
  );
  const canEvaluate = Boolean(state.fusion?.id);

  // Log setiap render
  console.log("=== RENDER DEBUG ===");
  console.log("State:", {
    rubric: state.selectedRubric
      ? { id: state.selectedRubric.id, type: typeof state.selectedRubric.id }
      : null,
    question: state.selectedQuestion
      ? {
          id: state.selectedQuestion.id,
          type: typeof state.selectedQuestion.id,
        }
      : null,
  });
  console.log("IDs:", { rubricId, questionId });
  console.log("Capabilities:", {
    canUploadQuestion,
    canUploadSubmission,
    canBuildFusion,
    canEvaluate,
  });
  console.log("===================");

  return (
    <AppLayout
      sidebarContent={
        <Sidebar
          selectedRubric={state.selectedRubric}
          selectedQuestion={state.selectedQuestion}
          selectedSubmission={state.selectedSubmission}
          onRubricSelect={handleRubricSelect}
          onQuestionSelect={handleQuestionSelect}
          onSubmissionSelect={handleSubmissionSelect}
          onLoadRubrics={api.listRubrics}
          onLoadQuestions={api.listQuestions}
          onLoadSubmissions={api.listSubmissions}
          onGetRubric={api.getRubric}
          onGetQuestion={api.getQuestion}
          onGetSubmission={api.getSubmission}
        />
      }
    >
      <Container fluid p="md">
        <Grid gutter="md">
          {/* Main Content Area */}
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Stack gap="md">
              <div>
                <Title order={2} c="orange.7" mb="xs">
                  EvalMate
                </Title>
                <Text size="sm" c="dimmed">
                  Intelligent Student Assignment Feedback System
                </Text>
              </div>

              {/* Upload Sections */}
              <Stack gap="md">
                {/* Debug Panel */}
                <Paper p="sm" withBorder bg="yellow.0">
                  <Text size="xs" fw={700} mb="xs">
                    🔍 DEBUG INFO:
                  </Text>
                  <Text size="xs">
                    Rubric ID: {state.selectedRubric?.id || "❌ null"}
                  </Text>
                  <Text size="xs">
                    Question ID: {state.selectedQuestion?.id || "❌ null"}
                  </Text>
                  <Text size="xs">
                    Submission ID: {state.selectedSubmission?.id || "❌ null"}
                  </Text>
                  <Text
                    size="xs"
                    fw={600}
                    c={canUploadSubmission ? "green" : "red"}
                  >
                    Can Upload Submission:{" "}
                    {canUploadSubmission ? "✅ TRUE" : "❌ FALSE"}
                  </Text>
                  <Text size="xs" fw={600} c={canBuildFusion ? "green" : "red"}>
                    Can Build Fusion: {canBuildFusion ? "✅ TRUE" : "❌ FALSE"}
                  </Text>
                  <Text size="xs" fw={600} c={canEvaluate ? "green" : "red"}>
                    Can Evaluate: {canEvaluate ? "✅ TRUE" : "❌ FALSE"}
                  </Text>
                  <Text size="xs">
                    Loading state: {state.loading || "idle"}
                  </Text>
                </Paper>

                <UploadRubric
                  onUpload={handleRubricUpload}
                  loading={state.loading === LOADING_STATES.UPLOADING}
                />

                <UploadQuestion
                  onUpload={handleQuestionUpload}
                  loading={state.loading === LOADING_STATES.UPLOADING}
                  disabled={!canUploadQuestion}
                />

                <UploadSubmission
                  onUpload={handleSubmissionUpload}
                  loading={state.loading === LOADING_STATES.UPLOADING}
                  disabled={!canUploadSubmission}
                />
              </Stack>

              {/* Action Buttons */}
              <ActionButtons
                onBuildFusion={handleBuildFusion}
                onEvaluate={handleEvaluate}
                canBuildFusion={canBuildFusion}
                canEvaluate={canEvaluate}
                loading={state.loading}
              />

              {/* Messages */}
              <div>
                <Text size="sm" fw={600} mb="sm">
                  Messages
                </Text>
                <MessageList messages={state.messages} />
              </div>
            </Stack>
          </Grid.Col>

          {/* Results Panel */}
          <Grid.Col span={{ base: 12, md: 4 }}>
            <ResultsPanel
              result={state.result}
              selectedRubric={state.selectedRubric}
            />
          </Grid.Col>
        </Grid>
      </Container>
    </AppLayout>
  );
}
