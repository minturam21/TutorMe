import type { Lesson } from "../../../types/lesson";
import type { VisualAction } from "../../../types/visualAction";

/** A single action placed on the lesson-wide playback clock. */
export interface TimelineEntry {
  stepIndex: number;
  eventIndex: number;
  actionIndex: number;
  eventId: string;
  action: VisualAction;
  start: number;
  end: number;
  duration: number;
}

export interface TimelinePosition {
  entryIndex: number;
  entry: TimelineEntry | null;
  time: number;
  progress: number;
  totalDuration: number;
}

/**
 * Flattens the nested lesson structure into one deterministic clock.
 * Action order is local to its teaching event; timeline order follows
 * the lesson's step/event order and then each event's action order.
 */
export function buildLessonTimeline(lesson: Lesson): TimelineEntry[] {
  const entries: TimelineEntry[] = [];
  let cursor = 0;

  lesson.steps.forEach((step, stepIndex) => {
    (step.teaching_events ?? []).forEach((event, eventIndex) => {
      const actions = [...event.visual_actions].sort(
        (a, b) => a.order - b.order
      );

      actions.forEach((action, actionIndex) => {
        const duration = Number.isFinite(action.duration)
          ? Math.max(0, action.duration)
          : 0;

        entries.push({
          stepIndex,
          eventIndex,
          actionIndex,
          eventId: event.id,
          action,
          start: cursor,
          end: cursor + duration,
          duration,
        });
        cursor += duration;
      });
    });
  });

  return entries;
}

/** Resolves a clock time to the action that owns it and its local progress. */
export function locateTimelinePosition(
  entries: TimelineEntry[],
  requestedTime: number
): TimelinePosition {
  const totalDuration = entries.length > 0 ? entries[entries.length - 1].end : 0;
  const time = Number.isFinite(requestedTime)
    ? Math.max(0, Math.min(totalDuration, requestedTime))
    : 0;

  if (entries.length === 0) {
    return { entryIndex: -1, entry: null, time: 0, progress: 0, totalDuration };
  }

  // At an exact boundary, select the next positive-duration action so
  // seeking to that timestamp starts at the beginning of the next action.
  let entryIndex = entries.findIndex(
    (entry) => entry.duration > 0 && time < entry.end
  );

  if (entryIndex < 0) {
    entryIndex = entries.length - 1;
  }

  const entry = entries[entryIndex];
  const progress = entry.duration > 0
    ? Math.max(0, Math.min(1, (time - entry.start) / entry.duration))
    : 1;

  return { entryIndex, entry, time, progress, totalDuration };
}
