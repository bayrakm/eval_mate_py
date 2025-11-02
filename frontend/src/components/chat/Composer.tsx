"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Upload, Play, FileText, HelpCircle, User } from "lucide-react";
import type { LoadingState } from "@/lib/types";

interface ComposerProps {
  loading: LoadingState;
  onRubricUpload: (file: File) => void;
  onQuestionUpload: (file: File, title?: string) => void;
  onSubmissionUpload: (file: File, studentHandle: string) => void;
  onBuildFusion: () => void;
  onEvaluate: () => void;
  canUploadQuestion: boolean;
  canUploadSubmission: boolean;
  canBuildFusion: boolean;
  canEvaluate: boolean;
}

export function Composer({
  loading,
  onRubricUpload,
  onQuestionUpload,
  onSubmissionUpload,
  onBuildFusion,
  onEvaluate,
  canUploadQuestion,
  canUploadSubmission,
  canBuildFusion,
  canEvaluate,
}: ComposerProps) {
  const [studentHandle, setStudentHandle] = useState("");
  const [questionTitle, setQuestionTitle] = useState("");

  const handleFileUpload = (
    event: React.ChangeEvent<HTMLInputElement>,
    type: "rubric" | "question" | "submission"
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    switch (type) {
      case "rubric":
        onRubricUpload(file);
        break;
      case "question":
        if (canUploadQuestion) {
          onQuestionUpload(file, questionTitle || undefined);
          setQuestionTitle("");
        }
        break;
      case "submission":
        if (canUploadSubmission && studentHandle.trim()) {
          onSubmissionUpload(file, studentHandle.trim());
          setStudentHandle("");
        }
        break;
    }
    
    // Reset the input
    event.target.value = "";
  };

  const isUploading = loading === "uploading";
  const isBuilding = loading === "building";
  const isEvaluating = loading === "evaluating";
  const isLoading = loading !== "idle";

  return (
    <Card className="border-t">
      <div className="p-4 space-y-4">
        {/* Upload Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Rubric Upload */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium">
              <FileText className="w-4 h-4 mr-2" />
              Upload Rubric
            </label>
            <div className="relative">
              <Input
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={(e) => handleFileUpload(e, "rubric")}
                disabled={isLoading}
                className="file:mr-2 file:rounded file:border-0 file:bg-primary file:text-primary-foreground file:hover:bg-primary/90"
              />
            </div>
          </div>

          {/* Question Upload */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium">
              <HelpCircle className="w-4 h-4 mr-2" />
              Upload Question
            </label>
            <div className="space-y-2">
              <Input
                type="text"
                placeholder="Question title (optional)"
                value={questionTitle}
                onChange={(e) => setQuestionTitle(e.target.value)}
                disabled={!canUploadQuestion || isLoading}
              />
              <Input
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={(e) => handleFileUpload(e, "question")}
                disabled={!canUploadQuestion || isLoading}
                className="file:mr-2 file:rounded file:border-0 file:bg-primary file:text-primary-foreground file:hover:bg-primary/90"
              />
            </div>
          </div>

          {/* Submission Upload */}
          <div className="space-y-2">
            <label className="flex items-center text-sm font-medium">
              <User className="w-4 h-4 mr-2" />
              Upload Submission
            </label>
            <div className="space-y-2">
              <Input
                type="text"
                placeholder="Student handle/ID"
                value={studentHandle}
                onChange={(e) => setStudentHandle(e.target.value)}
                disabled={!canUploadSubmission || isLoading}
              />
              <Input
                type="file"
                accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
                onChange={(e) => handleFileUpload(e, "submission")}
                disabled={!canUploadSubmission || !studentHandle.trim() || isLoading}
                className="file:mr-2 file:rounded file:border-0 file:bg-primary file:text-primary-foreground file:hover:bg-primary/90"
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 justify-center">
          <Button
            onClick={onBuildFusion}
            disabled={!canBuildFusion || isLoading}
            variant="secondary"
          >
            {isBuilding ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Building Fusion...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Build Fusion
              </>
            )}
          </Button>

          <Button
            onClick={onEvaluate}
            disabled={!canEvaluate || isLoading}
          >
            {isEvaluating ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Evaluating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Evaluation
              </>
            )}
          </Button>
        </div>

        {/* Loading Status */}
        {isLoading && (
          <div className="text-center text-sm text-muted-foreground">
            {loading === "uploading" && "Uploading file..."}
            {loading === "building" && "Building fusion context..."}
            {loading === "evaluating" && "Running LLM evaluation..."}
          </div>
        )}
      </div>
    </Card>
  );
}