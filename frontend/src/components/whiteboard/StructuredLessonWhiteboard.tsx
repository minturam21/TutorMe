import { useEffect, useRef, useState } from "react";

import type { Lesson, TeachingEvent } from "../../types/lesson";
import type { Scene, SceneObject, VisualAction } from "../../types/visualAction";

import { SceneManager } from "./engine/SceneManager";
import { ActionExecutor } from "./engine/ActionExecutor";
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
  id,
  text,
  fontSize = 32,
  minHeight = 76,
  progress = 1,
}: HandwrittenTextLineProps) {
  if (!text.trim()) return null;

  const estimatedLines = text.split("\n").reduce(
    (count, line) => count + Math.max(1, Math.ceil(line.length / 90)),
    0
  );
  const height = Math.max(minHeight, estimatedLines * fontSize * 1.6 + 20);
  const object: SceneObject = {
    id,
    type: "text",
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

const CREATION_ACTIONS = new Set([
  "create_object", "draw_shape", "draw_line", "draw_arrow", "draw_path",
  "write_text", "write_equation",
]);

export default function StructuredLessonWhiteboard({ lesson }: StructuredLessonWhiteboardProps) {
  const managerRef = useRef<SceneManager | null>(null);
  const executorRef = useRef<ActionExecutor | null>(null);
  const runIdRef = useRef(0);

  if (!managerRef.current) managerRef.current = new SceneManager(lesson.initial_scene);
  if (!executorRef.current) executorRef.current = new ActionExecutor(managerRef.current);

  const [scene, setScene] = useState<Scene>(() => managerRef.current!.getScene());
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [activeEvent, setActiveEvent] = useState<TeachingEvent | null>(null);
  const [explanationProgress, setExplanationProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [activeDrawing, setActiveDrawing] = useState<{ objectId: string; progress: number } | null>(null);
  const activeStep = lesson.steps[activeStepIndex];

  useEffect(() => {
    const manager = managerRef.current!;
    const executor = executorRef.current!;
    runIdRef.current++;
    executor.cancel();
    manager.loadScene(lesson.initial_scene);
    setScene(manager.getScene());
    setActiveStepIndex(0);
    setActiveEvent(null);
    setExplanationProgress(0);
    setIsPlaying(false);
    setIsPaused(false);
    setActiveDrawing(null);
    return () => { runIdRef.current++; executor.cancel(); };
  }, [lesson.id]);

  function loadStep(index: number) {
    if (index < 0 || index >= lesson.steps.length) return;
    runIdRef.current++;
    executorRef.current!.cancel();
    const startingScene = index === 0 ? lesson.initial_scene : lesson.steps[index - 1].expected_scene;
    managerRef.current!.loadScene(startingScene);
    setScene(managerRef.current!.getScene());
    setActiveStepIndex(index);
    setActiveEvent(null);
    setExplanationProgress(0);
    setIsPlaying(false);
    setIsPaused(false);
    setActiveDrawing(null);
  }

  async function playLesson() {
    if (isPlaying || isPaused) return;
    const runId = ++runIdRef.current;
    const executor = executorRef.current!;
    const manager = managerRef.current!;
    executor.cancel();
    manager.loadScene(lesson.initial_scene);
    setScene(manager.getScene());
    setActiveStepIndex(0);
    setActiveEvent(null);
    setExplanationProgress(0);
    setActiveDrawing(null);
    setIsPlaying(true);

    try {
      for (let stepIndex = 0; stepIndex < lesson.steps.length; stepIndex++) {
        if (runId !== runIdRef.current) return;
        const step = lesson.steps[stepIndex];
        setActiveStepIndex(stepIndex);
        const events = step.teaching_events ?? [];
        for (const event of events) {
          if (runId !== runIdRef.current) return;
          const actions = [...event.visual_actions].sort((a, b) => a.order - b.order);
          const totalDuration = actions.reduce((sum, action) => sum + action.duration, 0);
          const preceding = new Map<string, number>();
          let elapsed = 0;
          for (const action of actions) {
            preceding.set(action.id, elapsed);
            elapsed += action.duration;
          }
          setActiveEvent(event);
          setExplanationProgress(0);
          await executor.executeSequence(actions, playbackSpeed, {
            onActionProgress: (action: VisualAction, _index, progress) => {
              if (runId !== runIdRef.current) return;
              setScene(manager.getScene());
              const eventProgress = totalDuration > 0
                ? ((preceding.get(action.id) ?? 0) + action.duration * progress) / totalDuration
                : progress;
              setExplanationProgress(Math.max(0, Math.min(1, eventProgress)));
              if (CREATION_ACTIONS.has(action.type) && action.target_id) {
                setActiveDrawing({ objectId: action.target_id, progress });
              }
            },
            onActionComplete: (action: VisualAction) => {
              if (runId !== runIdRef.current) return;
              setScene(manager.getScene());
              if (CREATION_ACTIONS.has(action.type) && action.target_id) setActiveDrawing(null);
            },
            onError: (error: Error) => console.error("Whiteboard event action failed:", error),
          });
          if (runId !== runIdRef.current) return;
          setExplanationProgress(1);
          setScene(manager.getScene());
          setActiveDrawing(null);
        }
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

  function restartLesson() {
    runIdRef.current++;
    executorRef.current!.cancel();
    managerRef.current!.loadScene(lesson.initial_scene);
    setScene(managerRef.current!.getScene());
    setActiveStepIndex(0);
    setActiveEvent(null);
    setExplanationProgress(0);
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
        <WhiteboardCanvas scene={scene} activeDrawing={activeDrawing} />
      </div>
      {activeEvent && (
        <section className="structured-whiteboard-content" aria-live="polite">
          <HandwrittenTextLine id={`event-${activeEvent.id}-explanation`}
            text={activeEvent.explanation} fontSize={28} minHeight={120}
            progress={explanationProgress} />
        </section>
      )}
      <div className="structured-whiteboard-controls">
        {isPlaying ? <button onClick={pauseLesson}>Pause</button>
          : isPaused ? <button onClick={resumeLesson}>Resume</button>
          : <button onClick={playLesson}>Play lesson</button>}
        <button onClick={restartLesson} disabled={!isPlaying && !isPaused && activeStepIndex === 0 && !activeEvent}>
          Restart
        </button>
        <select value={playbackSpeed} onChange={(event) => setPlaybackSpeed(Number(event.target.value))}
          aria-label="Playback speed" disabled={isPlaying || isPaused}>
          <option value={0.5}>0.5x</option><option value={1}>1x</option>
          <option value={1.5}>1.5x</option><option value={2}>2x</option>
        </select>
      </div>
    </div>
  );
}
