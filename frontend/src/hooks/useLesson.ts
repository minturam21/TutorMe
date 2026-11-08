
import { useState } from "react";

import { lessonApi } from "../services/lessonApi";

import type {
  Lesson,
  LessonGenerationRequest,
} from "../types/lesson";

interface UseLessonReturn {
  lesson: Lesson | null;
  loading: boolean;
  error: string | null;
  generateLesson: (
    request: LessonGenerationRequest
  ) => Promise<Lesson | null>;
  clearLesson: () => void;
}

export function useLesson(): UseLessonReturn {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generateLesson(
    request: LessonGenerationRequest
  ): Promise<Lesson | null> {
    setLoading(true);
    setError(null);

    try {
      const response = await lessonApi.generate(request);

      if (!response.success || !response.lesson) {
        throw new Error(
          response.message || "Lesson generation failed."
        );
      }

      setLesson(response.lesson);
      return response.lesson;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred.";

      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }

  function clearLesson(): void {
    setLesson(null);
    setError(null);
  }

  return {
    lesson,
    loading,
    error,
    generateLesson,
    clearLesson,
  };
}
