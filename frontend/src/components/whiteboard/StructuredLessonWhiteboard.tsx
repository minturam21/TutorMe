import { useEffect, useRef, useState } from "react";

import type { Lesson } from "../../types/lesson";
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
  height?: number;
}

function HandwrittenTextLine({
  id,
  text,
  fontSize = 32,
  height = 76,
}: HandwrittenTextLineProps) {
  if (!text.trim()) return null;

  const object: SceneObject = {
    id,
    type: "text",
    properties: {
      text,
      x: 24,
      y: fontSize + 8,
      width: 1900,
      height: height - 12,
      font_size: fontSize,
      color: "#1e293b",
    },
  };

  return (
    <svg
      viewBox={`0 0 2000 ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label={text}
      style={{ display: "block", overflow: "hidden" }}
    >
      <TegakiTextRenderer object={object} progress={1} />
    </svg>
  );
}

const CREATION_ACTIONS = new Set([
  "create_object",
  "draw_shape",
  "draw_line",
  "draw_arrow",
  "draw_path",
  "write_text",
  "write_equation",
]);

export default function StructuredLessonWhiteboard({
  lesson,
}: StructuredLessonWhiteboardProps) {
  const managerRef = useRef<SceneManager | null>(null);
  const executorRef = useRef<ActionExecutor | null>(null);

  if (!managerRef.current) {
    managerRef.current = new SceneManager(lesson.initial_scene);
  }

  if (!executorRef.current) {
    executorRef.current = new ActionExecutor(managerRef.current);
  }

  const [scene, setScene] = useState<Scene>(() =>
    managerRef.current!.getScene()
  );

  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  const [activeDrawing, setActiveDrawing] = useState<{
    objectId: string;
    progress: number;
  } | null>(null);

  const activeStep = lesson.steps[activeStepIndex];

  useEffect(() => {
    const manager = managerRef.current!;
    const executor = executorRef.current!;

    executor.cancel();
    manager.loadScene(lesson.initial_scene);

    setScene(manager.getScene());
    setActiveStepIndex(0);
    setIsPlaying(false);
    setIsPaused(false);
    setActiveDrawing(null);

    return () => {
      executor.cancel();
    };
  }, [lesson.id]);

  function getStepStartingScene(index: number): Scene {
    if (index === 0) {
      return lesson.initial_scene;
    }

    return lesson.steps[index - 1].expected_scene;
  }

  function loadStep(index: number) {
    if (index < 0 || index >= lesson.steps.length) return;

    const executor = executorRef.current!;
    const manager = managerRef.current!;

    executor.cancel();
    manager.loadScene(getStepStartingScene(index));

    setScene(manager.getScene());
    setActiveStepIndex(index);
    setIsPlaying(false);
    setIsPaused(false);
    setActiveDrawing(null);
  }

  async function playStep() {
    if (!activeStep || isPlaying) return;

    const executor = executorRef.current!;
    const manager = managerRef.current!;

    executor.cancel();
    manager.loadScene(getStepStartingScene(activeStepIndex));

    setScene(manager.getScene());
    setActiveDrawing(null);
    setIsPlaying(true);
    setIsPaused(false);

    try {
      await executor.executeSequence(
        activeStep.visual_actions,
        playbackSpeed,
        {
          onActionProgress: (action: VisualAction, _index, progress) => {
            setScene(manager.getScene());

            if (CREATION_ACTIONS.has(action.type) && action.target_id) {
              setActiveDrawing({
                objectId: action.target_id,
                progress,
              });
            }
          },

          onActionComplete: (action: VisualAction) => {
            setScene(manager.getScene());

            if (CREATION_ACTIONS.has(action.type) && action.target_id) {
              setActiveDrawing(null);
            }
          },

          onError: (error: Error) => {
            console.error("Whiteboard action failed:", error);
            setActiveDrawing(null);
          },
        }
      );
    } catch (error) {
      console.error("Whiteboard playback failed:", error);
    } finally {
      setScene(manager.getScene());
      setActiveDrawing(null);
      setIsPlaying(false);
      setIsPaused(false);
    }
  }

  function pauseStep() {
    executorRef.current?.pause();
    setIsPlaying(false);
    setIsPaused(true);
  }

  function resumeStep() {
    executorRef.current?.resume();
    setIsPlaying(true);
    setIsPaused(false);
  }

  if (!activeStep) {
    return <div>No teaching steps are available.</div>;
  }

  return (
    <div className="structured-whiteboard">
      <div className="structured-whiteboard-header">
        <div style={{ width: "100%" }}>
          <HandwrittenTextLine
            id={`lesson-${lesson.id}-title`}
            text={lesson.title}
            fontSize={48}
            height={100}
          />
          <HandwrittenTextLine
            id={`lesson-${lesson.id}-step-${activeStep.id}`}
            text={`Step ${activeStepIndex + 1} of ${lesson.steps.length}`}
            fontSize={28}
            height={64}
          />
        </div>
      </div>

      <div className="structured-whiteboard-canvas">
        <WhiteboardCanvas
          scene={scene}
          activeDrawing={activeDrawing}
        />
      </div>

      <div className="structured-whiteboard-controls">
        <button
          onClick={() => loadStep(activeStepIndex - 1)}
          disabled={activeStepIndex === 0}
        >
          Previous
        </button>

        {isPlaying ? (
          <button onClick={pauseStep}>Pause</button>
        ) : isPaused ? (
          <button onClick={resumeStep}>Resume</button>
        ) : (
          <button onClick={playStep}>Play step</button>
        )}

        <button
          onClick={() => loadStep(activeStepIndex + 1)}
          disabled={activeStepIndex === lesson.steps.length - 1}
        >
          Next
        </button>

        <select
          value={playbackSpeed}
          onChange={(event) =>
            setPlaybackSpeed(Number(event.target.value))
          }
          aria-label="Playback speed"
          disabled={isPlaying || isPaused}
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>

      <section className="structured-whiteboard-content">
        {activeStep.explanation.trim() && (
          <div className="structured-whiteboard-explanation">
            <HandwrittenTextLine
              id={`step-${activeStep.id}-explanation-heading`}
              text="What this step means"
              fontSize={30}
              height={72}
            />
            <HandwrittenTextLine
              id={`step-${activeStep.id}-explanation`}
              text={activeStep.explanation}
              fontSize={28}
              height={180}
            />
          </div>
        )}

        {activeStep.equations.length > 0 && (
          <div className="structured-whiteboard-equations">
            <HandwrittenTextLine
              id={`step-${activeStep.id}-equations-heading`}
              text="Equations"
              fontSize={30}
              height={72}
            />
            {activeStep.equations.map((equation, index) => (
              <HandwrittenTextLine
                key={`${activeStep.id}-equation-${index}`}
                id={`step-${activeStep.id}-equation-${index}`}
                text={equation}
                fontSize={34}
                height={82}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
