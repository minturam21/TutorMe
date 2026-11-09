import { useEffect, useMemo, useRef, useState } from "react";

import type { Lesson, TeachingEvent } from "../../types/lesson";
import type { Scene, SceneObject, VisualAction } from "../../types/visualAction";

import { SceneManager } from "./engine/SceneManager";
import { ActionExecutor } from "./engine/ActionExecutor";
import {
  buildLessonTimeline,
  locateTimelinePosition,
  reconstructTimelineScene,
} from "./engine/LessonTimeline";
import TegakiTextRenderer from "./engine/TegakiTextRenderer";
import WhiteboardCanvas from "./WhiteboardCanvas";

interface StructuredLessonWhiteboardProps {
  lesson: Lesson;
}

interface HandwrittenTextLineProps {
  id: string;
  text: string;
  fontSize?: number;
  minHeight?: number;
  progress?: number;
}

function HandwrittenTextLine({
  id, text, fontSize = 32, minHeight = 76, progress = 1,
}: HandwrittenTextLineProps) {
  if (!text.trim()) return null;
  const estimatedLines = text.split("\n").reduce(
    (count, line) => count + Math.max(1, Math.ceil(line.length / 90)), 0
  );
  const height = Math.max(minHeight, estimatedLines * fontSize * 1.6 + 20);
  const object: SceneObject = {
    id, type: "text",
    properties: {
      text, x: 24, y: fontSize + 8, width: 1900,
      height: height - 12, font_size: fontSize, color: "#1e293b",
    },
  };
  return (
    <svg viewBox={`0 0 2000 ${height}`} width="100%" height={height}
      role="img" aria-label={text} style={{ display: "block", overflow: "hidden" }}>
      <TegakiTextRenderer object={object} progress={progress} />
    </svg>
  );
}

interface CanvasViewBox { x: number; y: number; width: number; height: number; }

function calculateLessonViewBox(lesson: Lesson): CanvasViewBox {
  const bounds = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity };
  const include = (x: number, y: number, width: number, height: number) => {
    if (![x, y, width, height].every(Number.isFinite)) return;
    bounds.minX = Math.min(bounds.minX, x);
    bounds.minY = Math.min(bounds.minY, y);
    bounds.maxX = Math.max(bounds.maxX, x + Math.max(0, width));
    bounds.maxY = Math.max(bounds.maxY, y + Math.max(0, height));
  };
  const scenes = [lesson.initial_scene, ...lesson.steps.flatMap(step => [
    step.expected_scene,
    ...(step.teaching_events ?? []).map(event => event.expected_scene),
  ])];
  for (const scene of scenes) {
    for (const object of scene.objects ?? []) {
      const p = object.properties;
      const x = typeof p.x === "number" ? p.x : 0;
      const y = typeof p.y === "number" ? p.y : 0;
      const width = typeof p.width === "number" ? p.width : 900;
      const height = typeof p.height === "number" ? p.height : 120;
      if (object.type === "line" || object.type === "arrow") {
        const x1 = typeof p.start_x === "number" ? p.start_x : x;
        const y1 = typeof p.start_y === "number" ? p.start_y : y;
        const x2 = typeof p.end_x === "number" ? p.end_x : x;
        const y2 = typeof p.end_y === "number" ? p.end_y : y;
        include(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1));
      } else include(x, y, width, height);
    }
  }
  if (!Number.isFinite(bounds.minX)) return { x: 0, y: 0, width: 2000, height: 1400 };
  const contentWidth = Math.max(1, bounds.maxX - bounds.minX);
  const contentHeight = Math.max(1, bounds.maxY - bounds.minY);
  const padding = Math.max(48, Math.max(contentWidth, contentHeight) * 0.08);
  return { x: bounds.minX - padding, y: bounds.minY - padding,
    width: contentWidth + padding * 2, height: contentHeight + padding * 2 };
}

const CREATION_ACTIONS = new Set([
  "create_object", "draw_shape", "draw_line", "draw_arrow", "draw_path",
  "write_text", "write_equation",
]);

export default function StructuredLessonWhiteboard({ lesson }: StructuredLessonWhiteboardProps) {
  const managerRef = useRef<SceneManager | null>(null);
  const executorRef = useRef<ActionExecutor | null>(null);
  const runIdRef = useRef(0);
  const cursorRef = useRef(0);

  if (!managerRef.current) managerRef.current = new SceneManager(lesson.initial_scene);
  if (!executorRef.current) executorRef.current = new ActionExecutor(managerRef.current);

  const timeline = useMemo(() => buildLessonTimeline(lesson), [lesson]);
  const totalDuration = timeline.length ? timeline[timeline.length - 1].end : 0;
  const viewBox = useMemo(() => calculateLessonViewBox(lesson), [lesson]);

  const [scene, setScene] = useState<Scene>(() => managerRef.current!.getScene());
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [activeEvent, setActiveEvent] = useState<TeachingEvent | null>(null);
  const [explanationProgress, setExplanationProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeDrawing, setActiveDrawing] = useState<{ objectId: string; progress: number } | null>(null);
  const activeStep = lesson.steps[activeStepIndex];

  function findEvent(stepIndex: number, eventId: string): TeachingEvent | null {
    return lesson.steps[stepIndex]?.teaching_events?.find((event) => event.id === eventId) ?? null;
  }

  function updateEventProgress(entryIndex: number, progress: number) {
    const entry = timeline[entryIndex];
    if (!entry) return;
    const eventEntries = timeline.filter(
      (candidate) => candidate.stepIndex === entry.stepIndex && candidate.eventId === entry.eventId
    );
    const eventStart = eventEntries[0]?.start ?? entry.start;
    const eventEnd = eventEntries[eventEntries.length - 1]?.end ?? entry.end;
    const eventDuration = eventEnd - eventStart;
    const elapsed = entry.start - eventStart + entry.duration * progress;
    setExplanationProgress(eventDuration > 0 ? Math.max(0, Math.min(1, elapsed / eventDuration)) : 1);
    setActiveEvent(findEvent(entry.stepIndex, entry.eventId));
    setActiveStepIndex(entry.stepIndex);
  }

  useEffect(() => {
    const manager = managerRef.current!;
    const executor = executorRef.current!;
    runIdRef.current++;
    executor.cancel();
    manager.loadScene(lesson.initial_scene);
    cursorRef.current = 0;
    setScene(manager.getScene());
    setActiveStepIndex(0);
    setActiveEvent(null);
    setExplanationProgress(0);
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentTime(0);
    setActiveDrawing(null);
    return () => { runIdRef.current++; executor.cancel(); };
  }, [lesson.id]);

  async function playFromCursor() {
    if (isPlaying || isPaused || timeline.length === 0) return;
    const runId = ++runIdRef.current;
    const executor = executorRef.current!;
    const manager = managerRef.current!;
    const position = locateTimelinePosition(timeline, cursorRef.current);
    if (!position.entry) return;

    executor.cancel();
    setIsPlaying(true);
    let first = true;

    try {
      for (let index = position.entryIndex; index < timeline.length; index++) {
        if (runId !== runIdRef.current) return;
        const entry = timeline[index];
        const startProgress = first ? position.progress : 0;
        const alreadyApplied = first && startProgress > 0;
        first = false;

        setActiveStepIndex(entry.stepIndex);
        setActiveEvent(findEvent(entry.stepIndex, entry.eventId));
        updateEventProgress(index, startProgress);

        await executor.executeSequence([entry.action], playbackSpeed, {
          initialProgress: startProgress,
          firstActionAlreadyApplied: alreadyApplied,
          onActionProgress: (action: VisualAction, _actionIndex, progress) => {
            if (runId !== runIdRef.current) return;
            setScene(manager.getScene());
            updateEventProgress(index, progress);
            const elapsed = entry.start + entry.duration * progress;
            cursorRef.current = elapsed;
            setCurrentTime(elapsed);
            if (CREATION_ACTIONS.has(action.type) && action.target_id) {
              setActiveDrawing({ objectId: action.target_id, progress });
            }
          },
          onActionComplete: (action: VisualAction) => {
            if (runId !== runIdRef.current) return;
            setScene(manager.getScene());
            cursorRef.current = entry.end;
            setCurrentTime(entry.end);
            updateEventProgress(index, 1);
            if (CREATION_ACTIONS.has(action.type) && action.target_id) setActiveDrawing(null);
          },
          onError: (error: Error) => console.error("Whiteboard timeline action failed:", error),
        });

        if (runId !== runIdRef.current) return;
        cursorRef.current = entry.end;
        setCurrentTime(entry.end);
      }
    } catch (error) {
      console.error("Lesson playback failed:", error);
    } finally {
      if (runId === runIdRef.current) {
        setScene(manager.getScene());
        setActiveDrawing(null);
        setIsPlaying(false);
        setIsPaused(false);
      }
    }
  }

  function playLesson() {
    if (isPlaying || isPaused) return;
    if (cursorRef.current >= totalDuration) restartLesson();
    void playFromCursor();
  }

  function pauseLesson() {
    executorRef.current?.pause();
    setIsPlaying(false);
    setIsPaused(true);
  }

  function resumeLesson() {
    executorRef.current?.resume();
    setIsPlaying(true);
    setIsPaused(false);
  }

  function seekLesson(value: number) {
    runIdRef.current++;
    executorRef.current!.cancel();
    const manager = managerRef.current!;
    const reconstructed = reconstructTimelineScene(manager, lesson.initial_scene, timeline, value);
    cursorRef.current = reconstructed.position.time;
    setCurrentTime(reconstructed.position.time);
    setScene(manager.getScene());
    setIsPlaying(false);
    setIsPaused(false);

    const entry = reconstructed.position.entry;
    if (!entry) {
      setActiveStepIndex(0);
      setActiveEvent(null);
      setExplanationProgress(0);
      setActiveDrawing(null);
      return;
    }

    setActiveStepIndex(entry.stepIndex);
    setActiveEvent(findEvent(entry.stepIndex, entry.eventId));
    updateEventProgress(reconstructed.position.entryIndex, reconstructed.position.progress);
    if (reconstructed.activeAction && CREATION_ACTIONS.has(reconstructed.activeAction.type)
      && reconstructed.activeAction.target_id) {
      setActiveDrawing({
        objectId: reconstructed.activeAction.target_id,
        progress: reconstructed.position.progress,
      });
    } else {
      setActiveDrawing(null);
    }
  }

  function restartLesson() {
    runIdRef.current++;
    executorRef.current!.cancel();
    managerRef.current!.loadScene(lesson.initial_scene);
    cursorRef.current = 0;
    setScene(managerRef.current!.getScene());
    setActiveStepIndex(0);
    setActiveEvent(null);
    setExplanationProgress(0);
    setCurrentTime(0);
    setActiveDrawing(null);
    setIsPlaying(false);
    setIsPaused(false);
  }

  if (!activeStep) return <div>No teaching steps are available.</div>;

  return (
    <div className="structured-whiteboard">
      <div className="structured-whiteboard-header">
        <div style={{ width: "100%" }}>
          <HandwrittenTextLine id={`lesson-${lesson.id}-title`} text={lesson.title} fontSize={48} minHeight={100} />
          <HandwrittenTextLine id={`lesson-${lesson.id}-step-${activeStep.id}`}
            text={`Step ${activeStepIndex + 1} of ${lesson.steps.length}`} fontSize={28} minHeight={64} />
        </div>
      </div>
      <div className="structured-whiteboard-canvas">
        <WhiteboardCanvas scene={scene} activeDrawing={activeDrawing} viewBox={viewBox} />
      </div>      <div className="structured-whiteboard-controls">
        {isPlaying ? <button onClick={pauseLesson}>Pause</button>
          : isPaused ? <button onClick={resumeLesson}>Resume</button>
          : <button onClick={playLesson}>Play lesson</button>}
        <button onClick={restartLesson} disabled={currentTime === 0 && !isPlaying && !isPaused}>Restart</button>
        <label>
          <span>Seek</span>
          <input type="range" min={0} max={totalDuration || 1} step={0.01}
            value={Math.min(currentTime, totalDuration)}
            onChange={(event) => seekLesson(Number(event.target.value))}
            aria-label="Seek lesson timeline" disabled={totalDuration <= 0} />
        </label>
        <span>{currentTime.toFixed(1)}s / {totalDuration.toFixed(1)}s</span>
        <select value={playbackSpeed} onChange={(event) => setPlaybackSpeed(Number(event.target.value))}
          aria-label="Playback speed" disabled={isPlaying || isPaused}>
          <option value={0.5}>0.5x</option><option value={1}>1x</option>
          <option value={1.5}>1.5x</option><option value={2}>2x</option>
        </select>
      </div>
      {activeEvent && (
        <section className="structured-whiteboard-content" aria-live="polite">
          <HandwrittenTextLine id={`event-${activeEvent.id}-explanation`}
            text={activeEvent.explanation} fontSize={28} minHeight={120}
            progress={explanationProgress} />
        </section>
      )}

    </div>
  );
}
