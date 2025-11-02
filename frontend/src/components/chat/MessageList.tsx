"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";
import { formatDate } from "@/lib/format";

interface MessageListProps {
  messages: ChatMessage[];
  className?: string;
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <div className={cn("flex flex-col space-y-4 p-4", className)}>
      {messages.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">
          <p>Welcome to EvalMate!</p>
          <p className="text-sm mt-2">Upload a rubric, question, and submission to get started.</p>
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
    </div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === "user";
  const isSystem = message.type === "system";

  return (
    <div
      className={cn(
        "flex",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <Card
        className={cn(
          "max-w-[80%] min-w-[200px]",
          isUser
            ? "bg-primary text-primary-foreground"
            : isSystem
            ? "bg-muted"
            : "bg-card"
        )}
      >
        <CardContent className="p-3">
          <div className="space-y-1">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            <p
              className={cn(
                "text-xs opacity-70",
                isUser ? "text-right" : "text-left"
              )}
            >
              {formatDate(message.timestamp)}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}