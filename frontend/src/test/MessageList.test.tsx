import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "@/components/chat/MessageList";
import type { ChatMessage } from "@/lib/types";

// Mock the format utility
vi.mock("@/lib/format", () => ({
  formatDate: (date: Date) => date.toISOString(),
}));

describe("MessageList", () => {
  it("renders welcome message when no messages", () => {
    render(<MessageList messages={[]} />);
    expect(screen.getByText("Welcome to EvalMate!")).toBeInTheDocument();
  });

  it("renders messages correctly", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        type: "user",
        content: "Hello",
        timestamp: new Date("2023-01-01"),
      },
      {
        id: "2", 
        type: "assistant",
        content: "Hi there!",
        timestamp: new Date("2023-01-01"),
      },
    ];

    render(<MessageList messages={messages} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
  });
});