"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
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
  Modal,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconMessage } from "@tabler/icons-react";
import { useAppState } from "../hooks/useAppState";
import { AppLayout } from "../components/layout/AppLayout";
import { UploadRubric } from "../components/upload/UploadRubric";
import { UploadQuestion } from "../components/upload/UploadQuestion";
import { UploadSubmission } from "../components/upload/UploadSubmission";
import { ActionButtons } from "../components/actions/ActionButtons";
import { MessageList } from "../components/display/MessageList";
import { ResultsPanel } from "../components/display/ResultsPanel";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import ChatInterface from "../components/chat/ChatInterface";
import * as api from "../lib/apiClient";
import { LOADING_STATES } from "../lib/constants";
import { useSession } from "next-auth/react";

export default function HomePage() {
  const [showChatModal, setShowChatModal] = useState(false);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);

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

  const processUploadQueue = useCallback(async () => {
    if (isProcessingQueue || uploadQueue.length === 0) return;
    
    setIsProcessingQueue(true);
    const queue = [...uploadQueue];
    
    for (const uploadItem of queue) {
      const { type, file, params, handler } = uploadItem;
      
      if (type === 'rubric') {
        await handler(file);
      } else if (type === 'question') {
        if (state.selectedRubric) {
          await handler(file, params.title, state.selectedRubric.id);
        }
      } else if (type === 'submission') {
        if (state.selectedRubric && state.selectedQuestion) {
          await handler(file, params.studentHandle, state.selectedRubric.id, state.selectedQuestion.id);
        }
      }
      
      setUploadQueue(prev => prev.slice(1));
    }
    
    setIsProcessingQueue(false);
  }, [uploadQueue, isProcessingQueue, state.selectedRubric, state.selectedQuestion]);

  useEffect(() => {
    processUploadQueue();
  }, [uploadQueue, state.selectedRubric, state.selectedQuestion, processUploadQueue]);

  const handleNewEvaluation = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedRubric: null,
      selectedQuestion: null,
      selectedSubmission: null,
      fusion: null,
      result: null,
      evalId: null,
      messages: [],
      loading: "idle",
      progress: null,
    }));
    addMessage("🆕 Started a new evaluation. Please upload your resources.");
    notifications.show({
      title: "New Evaluation",
      message: "Ready to start a new evaluation. Upload your resources!",
      color: "blue",
    });
  }, [setState, addMessage]);

  const handleRubricUpload = useCallback(
    async (file) => {
      setUploadQueue(prev => [{
        type: 'rubric',
        file,
        params: {},
        handler: async (uploadFile) => {
          try {
            setLoading(LOADING_STATES.UPLOADING);
            addMessage(`Uploading rubric: ${uploadFile.name}`, "user");

            setProgress({
              type: "upload",
              value: 0,
              label: `Uploading ${uploadFile.name}...`,
              target: "rubric",
            });

            const response = await api.uploadRubric(uploadFile, {}, (progress) => {
              setProgress({
                type: "upload",
                value: progress,
                label: `Uploading ${uploadFile.name}... ${progress}%`,
                target: "rubric",
              });
            });

            const rubric = await api.getRubric(response.meta.id);

            setState((prev) => ({
              ...prev,
              selectedRubric: rubric,
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
        }
      }]);
    },
    [addMessage, setLoading, setState, setProgress, clearProgress]
  );

  const handleQuestionUpload = useCallback(
    async (file, title) => {
      setUploadQueue(prev => [...prev, {
        type: 'question',
        file,
        params: { title },
        handler: async (uploadFile, uploadTitle, currentRubricId) => {
          try {
            setLoading(LOADING_STATES.UPLOADING);
            addMessage(`Uploading question: ${uploadFile.name}`, "user");

            setProgress({
              type: "upload",
              value: 0,
              label: `Uploading ${uploadFile.name}...`,
              target: "question",
            });

            const response = await api.uploadQuestion(uploadFile, {
              rubric_id: currentRubricId,
              title: uploadTitle,
            }, (progress) => {
              setProgress({
                type: "upload",
                value: progress,
                label: `Uploading ${uploadFile.name}... ${progress}%`,
                target: "question",
              });
            });

            const question = await api.getQuestion(response.meta.id);

            setState((prev) => ({
              ...prev,
              selectedQuestion: question,
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
        }
      }]);
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
      setUploadQueue(prev => [...prev, {
        type: 'submission',
        file,
        params: { studentHandle },
        handler: async (uploadFile, uploadStudentHandle, currentRubricId, currentQuestionId) => {
          try {
            setLoading(LOADING_STATES.UPLOADING);
            addMessage(
              `Uploading submission for ${uploadStudentHandle}: ${uploadFile.name}`,
              "user"
            );

            setProgress({
              type: "upload",
              value: 0,
              label: `Uploading ${uploadFile.name}...`,
              target: "submission",
            });

            const response = await api.uploadSubmission(uploadFile, {
              rubric_id: currentRubricId,
              question_id: currentQuestionId,
              student_handle: uploadStudentHandle,
            }, (progress) => {
              setProgress({
                type: "upload",
                value: progress,
                label: `Uploading ${uploadFile.name}... ${progress}%`,
                target: "submission",
              });
            });

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
        }
      }]);
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

      const evaluationResponse = (await api.evaluate(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      )) || {
        eval_id: null,
        result: {
          total: 0,
          items: [],
          overall_feedback: "Evaluation completed",
        },
      };

      const evalId = evaluationResponse.eval_id;
      const result = evaluationResponse.result;

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
        evalId,
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

  const canUploadQuestion = true;
  const canUploadSubmission = true;
  const canEvaluate = Boolean(
    rubricId && questionId && state.selectedSubmission?.id
  );

  return (
    <ProtectedRoute>
      <AppLayout sidebarContent={null} onNewEvaluation={handleNewEvaluation}>
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
                      {session?.user?.email || "user@example.com"}
                    </Text>
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
                        loading={
                          state.loading === LOADING_STATES.UPLOADING &&
                          state.progress?.target === "rubric"
                        }
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
                        loading={
                          state.loading === LOADING_STATES.UPLOADING &&
                          state.progress?.target === "question"
                        }
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
                        loading={
                          state.loading === LOADING_STATES.UPLOADING &&
                          state.progress?.target === "submission"
                        }
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
                    </Stack>
                  </div>

                  <Divider />
                  <div>
                    <ResultsPanel
                      result={state.result}
                      selectedRubric={state.selectedRubric}
                      onOpenChat={() => setShowChatModal(true)}
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
                  Activity Log
                </Text>
              </Group>
              <MessageList messages={state.messages} />
            </Grid.Col>
          </Grid>
        </Container>

        <Modal
          opened={showChatModal}
          onClose={() => setShowChatModal(false)}
          title="Chat About Your Evaluation"
          size="lg"
          centered
          styles={{
            content: { maxHeight: "80vh" },
          }}
        >
          <ChatInterface
            evalData={
              state.result && state.evalId
                ? {
                    eval_id: state.evalId,
                    rubric_id: state.selectedRubric?.id,
                    question_id: state.selectedQuestion?.id,
                    submission_id: state.selectedSubmission?.id,
                  }
                : null
            }
            onClose={() => setShowChatModal(false)}
          />
        </Modal>
      </AppLayout>
    </ProtectedRoute>
  );
}
