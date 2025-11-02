"use client";

import { useState, useCallback } from "react";
import { ChatShell } from "@/components/chat/ChatShell";
import { Picker } from "@/components/panels/Picker";
import { Summary } from "@/components/panels/Summary";
import { ScoreCard } from "@/components/panels/ScoreCard";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { 
  AppState, 
  ChatMessage, 
  LoadingState,
  RubricMeta,
  QuestionMeta,
  SubmissionMeta,
  Rubric,
  Question,
  Submission,
  FusionContext,
  EvalResult
} from "@/lib/types";
import * as api from "@/lib/apiClient";

export default function HomePage() {
  const [state, setState] = useState<AppState>({
    selectedRubric: null,
    selectedQuestion: null,
    selectedSubmission: null,
    fusion: null,
    result: null,
    messages: [],
    loading: "idle",
  });

  const addMessage = useCallback((content: string, type: ChatMessage["type"] = "assistant") => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
    };
    
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
    }));
  }, []);

  const setLoading = useCallback((loading: LoadingState) => {
    setState(prev => ({ ...prev, loading }));
  }, []);

  // File upload handlers
  const handleRubricUpload = useCallback(async (file: File) => {
    try {
      setLoading("uploading");
      addMessage(`Uploading rubric: ${file.name}`, "user");
      
      const response = await api.uploadRubric(file);
      const rubric = await api.getRubric(response.id);
      
      setState(prev => ({
        ...prev,
        selectedRubric: rubric,
        selectedQuestion: null,
        selectedSubmission: null,
        fusion: null,
        result: null,
      }));
      
      addMessage(`✅ Rubric uploaded successfully: ${rubric.assignment} (${rubric.items.length} items)`);
    } catch (error) {
      addMessage(`❌ Failed to upload rubric: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading("idle");
    }
  }, [addMessage, setLoading]);

  const handleQuestionUpload = useCallback(async (file: File, title?: string) => {
    if (!state.selectedRubric) {
      addMessage("❌ Please select a rubric first");
      return;
    }

    try {
      setLoading("uploading");
      addMessage(`Uploading question: ${file.name}`, "user");
      
      const response = await api.uploadQuestion(state.selectedRubric.id, file, title);
      const question = await api.getQuestion(response.id);
      
      setState(prev => ({
        ...prev,
        selectedQuestion: question,
        selectedSubmission: null,
        fusion: null,
        result: null,
      }));
      
      addMessage(`✅ Question uploaded successfully: ${question.title}`);
    } catch (error) {
      addMessage(`❌ Failed to upload question: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading("idle");
    }
  }, [state.selectedRubric, addMessage, setLoading]);

  const handleSubmissionUpload = useCallback(async (file: File, studentHandle: string) => {
    if (!state.selectedRubric || !state.selectedQuestion) {
      addMessage("❌ Please select a rubric and question first");
      return;
    }

    try {
      setLoading("uploading");
      addMessage(`Uploading submission for ${studentHandle}: ${file.name}`, "user");
      
      const response = await api.uploadSubmission(
        state.selectedRubric.id, 
        state.selectedQuestion.id, 
        studentHandle, 
        file
      );
      const submission = await api.getSubmission(response.id);
      
      setState(prev => ({
        ...prev,
        selectedSubmission: submission,
        fusion: null,
        result: null,
      }));
      
      addMessage(`✅ Submission uploaded successfully for ${submission.student_handle}`);
    } catch (error) {
      addMessage(`❌ Failed to upload submission: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading("idle");
    }
  }, [state.selectedRubric, state.selectedQuestion, addMessage, setLoading]);

  // Fusion and evaluation handlers
  const handleBuildFusion = useCallback(async () => {
    if (!state.selectedRubric || !state.selectedQuestion || !state.selectedSubmission) {
      addMessage("❌ Please select a rubric, question, and submission first");
      return;
    }

    try {
      setLoading("building");
      addMessage("Building fusion context...", "user");
      
      const fusion = await api.buildFusion(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      );
      
      setState(prev => ({
        ...prev,
        fusion,
        result: null,
      }));
      
      addMessage(`✅ Fusion context built successfully! Token estimate: ${fusion.token_estimate}, Visual count: ${fusion.visual_count}`);
    } catch (error) {
      addMessage(`❌ Failed to build fusion context: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading("idle");
    }
  }, [state.selectedRubric, state.selectedQuestion, state.selectedSubmission, addMessage, setLoading]);

  const handleEvaluate = useCallback(async () => {
    if (!state.selectedRubric || !state.selectedQuestion || !state.selectedSubmission) {
      addMessage("❌ Please select a rubric, question, and submission first");
      return;
    }

    try {
      setLoading("evaluating");
      addMessage("Running LLM evaluation...", "user");
      
      const result = await api.evaluate(
        state.selectedRubric.id,
        state.selectedQuestion.id,
        state.selectedSubmission.id
      );
      
      setState(prev => ({
        ...prev,
        result,
      }));
      
      addMessage(`✅ Evaluation complete! Total score: ${result.total.toFixed(1)}/100 (${result.items.length} items graded)`);
    } catch (error) {
      addMessage(`❌ Failed to run evaluation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading("idle");
    }
  }, [state.selectedRubric, state.selectedQuestion, state.selectedSubmission, addMessage, setLoading]);

  // Resource selection handlers
  const handleRubricSelect = useCallback((rubric: Rubric) => {
    setState(prev => ({
      ...prev,
      selectedRubric: rubric,
      selectedQuestion: null,
      selectedSubmission: null,
      fusion: null,
      result: null,
    }));
    addMessage(`Selected rubric: ${rubric.assignment} (${rubric.items.length} items)`);
  }, [addMessage]);

  const handleQuestionSelect = useCallback((question: Question) => {
    setState(prev => ({
      ...prev,
      selectedQuestion: question,
      selectedSubmission: null,
      fusion: null,
      result: null,
    }));
    addMessage(`Selected question: ${question.title}`);
  }, [addMessage]);

  const handleSubmissionSelect = useCallback((submission: Submission) => {
    setState(prev => ({
      ...prev,
      selectedSubmission: submission,
      fusion: null,
      result: null,
    }));
    addMessage(`Selected submission from: ${submission.student_handle}`);
  }, [addMessage]);

  // Capability checks
  const canUploadQuestion = Boolean(state.selectedRubric);
  const canUploadSubmission = Boolean(state.selectedRubric && state.selectedQuestion);
  const canBuildFusion = Boolean(state.selectedRubric && state.selectedQuestion && state.selectedSubmission);
  const canEvaluate = Boolean(state.fusion);

  return (
    <div className="h-screen flex bg-background">
      {/* Left Sidebar - Resource Picker */}
      <div className="w-80 border-r flex flex-col">
        <Picker
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
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Interface */}
        <div className="flex-1">
          <ChatShell
            messages={state.messages}
            loading={state.loading}
            onRubricUpload={handleRubricUpload}
            onQuestionUpload={handleQuestionUpload}
            onSubmissionUpload={handleSubmissionUpload}
            onBuildFusion={handleBuildFusion}
            onEvaluate={handleEvaluate}
            canUploadQuestion={canUploadQuestion}
            canUploadSubmission={canUploadSubmission}
            canBuildFusion={canBuildFusion}
            canEvaluate={canEvaluate}
          />
        </div>
      </div>

      {/* Right Sidebar - Summary and Results */}
      <div className="w-96 border-l flex flex-col">
        {/* Summary Panel */}
        <div className="flex-shrink-0">
          <Summary
            fusion={state.fusion}
            result={state.result}
          />
        </div>

        {/* Results Panel */}
        {state.result && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Evaluation Results</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Detailed scores for each rubric item:
                </p>
              </CardContent>
            </Card>
            
            {state.result.items.map((item) => {
              const rubricItem = state.selectedRubric?.items.find(ri => ri.id === item.rubric_item_id);
              return (
                <ScoreCard
                  key={item.rubric_item_id}
                  item={item}
                  rubricItem={rubricItem}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}