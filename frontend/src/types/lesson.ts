
import type {
  Scene,
  VisualAction,
} from "./visualAction";

// A question used during lesson practice.

export interface PracticeQuestion {
  question: string;
  answer: string;
  explanation: string;
}

// One synchronized explanation-and-visual segment inside a teaching step.
export interface TeachingEvent {
  id: string;
  explanation: string;
  visual_actions: VisualAction[];
  expected_scene: Scene;
  duration: number;
}

// One teaching step in a lesson.

export interface TeachingStep {
  id: string;
  explanation: string;
  equations: string[];
  visual_actions: VisualAction[];
  teaching_events: TeachingEvent[];
  expected_scene: Scene;
  duration: number;
}

// Complete generated lesson.

export interface Lesson {
  id: string;
  title: string;
  subject: string;
  difficulty: string;
  objectives: string[];
  initial_scene: Scene;
  steps: TeachingStep[];
  practice_questions: PracticeQuestion[];
  version: number;
}

// Request sent to POST /lessons/generate.

export interface LessonGenerationRequest {
  question: string;
  subject?: string | null;
  difficulty?: string;
  conversation_id?: number | null;
}

// Response from POST /lessons/generate.

export interface LessonGenerationResponse {
  success: boolean;
  lesson: Lesson;
  message: string;
}

// Metadata returned by GET /lessons.

export interface LessonSummary {
  id: string;
  conversation_id: number | null;
  title: string;
  subject: string;
  difficulty: string;
  version: number;
  created_at: string;
  updated_at: string;
}

// Response from GET /lessons/{id}.

export interface SavedLessonResponse {
  id: string;
  conversation_id: number | null;
  title: string;
  subject: string;
  difficulty: string;
  version: number;
  created_at: string;
  updated_at: string;
  lesson: Lesson;
}
