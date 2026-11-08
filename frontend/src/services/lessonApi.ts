import { apiClient } from "./apiClient";

import type {
  LessonGenerationRequest,
  LessonGenerationResponse,
  LessonSummary,
  SavedLessonResponse,
} from "../types/lesson";

export const lessonApi = {
  // Generate a new AI lesson.
  generate(
    request: LessonGenerationRequest
  ): Promise<LessonGenerationResponse> {
    return apiClient.post<LessonGenerationResponse>(
      "/lessons/generate",
      request
    );
  },

  // Get all lessons, optionally filtered by conversation.
  getAll(conversationId?: number): Promise<LessonSummary[]> {
    const query =
      conversationId === undefined
        ? ""
        : `?conversation_id=${conversationId}`;

    return apiClient.get<LessonSummary[]>(`/lessons${query}`);
  },

  // Get one complete saved lesson.
  getById(lessonId: string): Promise<SavedLessonResponse> {
    return apiClient.get<SavedLessonResponse>(
      `/lessons/${encodeURIComponent(lessonId)}`
    );
  },

  // Delete a saved lesson.
  delete(lessonId: string): Promise<void> {
    return apiClient.delete(
      `/lessons/${encodeURIComponent(lessonId)}`
    );
  },
};