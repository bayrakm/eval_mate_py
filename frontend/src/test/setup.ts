import "@testing-library/jest-dom";

// Mock window APIs
Object.defineProperty(window, "URL", {
  value: {
    createObjectURL: vi.fn(() => "mocked-url"),
    revokeObjectURL: vi.fn(),
  },
});

// Mock process.env for Next.js
Object.defineProperty(process, "env", {
  value: {
    NEXT_PUBLIC_API_BASE_URL: "http://localhost:8000",
  },
});