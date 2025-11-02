"use client";

import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import type { ChatMessage, LoadingState } from "@/lib/types";

interface ChatShellProps {
  messages: ChatMessage[];
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

export function ChatShell({
  messages,
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
}: ChatShellProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>
      
      {/* Composer Area */}
      <div className="flex-shrink-0">
        <Composer
          loading={loading}
          onRubricUpload={onRubricUpload}
          onQuestionUpload={onQuestionUpload}
          onSubmissionUpload={onSubmissionUpload}
          onBuildFusion={onBuildFusion}
          onEvaluate={onEvaluate}
          canUploadQuestion={canUploadQuestion}
          canUploadSubmission={canUploadSubmission}
          canBuildFusion={canBuildFusion}
          canEvaluate={canEvaluate}
        />
      </div>
    </div>
  );
}