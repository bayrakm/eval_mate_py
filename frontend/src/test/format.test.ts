import { describe, it, expect } from "vitest";
import { evalResultToCSV, formatScore, formatTokens } from "@/lib/format";
import type { EvalResult } from "@/lib/types";

describe("Format utilities", () => {
  describe("evalResultToCSV", () => {
    it("should convert EvalResult to CSV format", () => {
      const result: EvalResult = {
        submission_id: "sub1",
        rubric_id: "rub1", 
        total: 85.5,
        items: [
          {
            rubric_item_id: "item1",
            score: 90,
            justification: "Excellent work",
            evidence_block_ids: ["block1", "block2"]
          },
          {
            rubric_item_id: "item2", 
            score: 80,
            justification: "Good effort, with \"quotes\"",
            evidence_block_ids: ["block3"]
          }
        ],
        overall_feedback: "Great submission",
        metadata: {}
      };

      const csv = evalResultToCSV(result);
      const lines = csv.split("\n");
      
      expect(lines[0]).toBe("rubric_item_id,score,justification");
      expect(lines[1]).toBe('"item1",90,"Excellent work"');
      expect(lines[2]).toBe('"item2",80,"Good effort, with ""quotes"""');
    });
  });

  describe("formatScore", () => {
    it("should format scores to one decimal place", () => {
      expect(formatScore(85)).toBe("85.0/100");
      expect(formatScore(92.7)).toBe("92.7/100");
    });
  });

  describe("formatTokens", () => {
    it("should format token counts", () => {
      expect(formatTokens(500)).toBe("500 tokens");
      expect(formatTokens(1500)).toBe("1.5k tokens");
      expect(formatTokens(2000)).toBe("2.0k tokens");
    });
  });
});