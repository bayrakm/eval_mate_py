import { describe, it, expect, vi, beforeEach } from "vitest";
import axios, { AxiosError } from "axios";
import * as apiClient from "@/lib/apiClient";

// Mock axios
vi.mock("axios");
const mockedAxios = vi.mocked(axios);

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Error handling", () => {
    it("should handle API errors gracefully", async () => {
      const mockError = new AxiosError("Network Error");
      mockError.response = {
        data: { detail: "API Error" },
        status: 400,
        statusText: "Bad Request",
        headers: {},
        config: {} as any,
      };

      mockedAxios.get.mockRejectedValueOnce(mockError);

      try {
        await apiClient.listRubrics();
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe("API Error");
      }
    });
  });

  describe("listRubrics", () => {
    it("should return rubrics list", async () => {
      const mockResponse = {
        data: {
          items: [
            { id: "1", course: "CS101", assignment: "Assignment 1", version: "1.0" }
          ],
          total: 1
        }
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await apiClient.listRubrics();
      expect(result).toEqual(mockResponse.data.items);
      expect(mockedAxios.get).toHaveBeenCalledWith("/rubrics");
    });
  });
});