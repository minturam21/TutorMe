
import { useEffect, useRef, useState } from "react";

import type { Lesson } from "../../types/lesson";
import type { Scene, VisualAction } from "../../types/visualAction";

import { SceneManager } from "./engine/SceneManager";
import { ActionExecutor } from "./engine/ActionExecutor";
import WhiteboardCanvas from "./WhiteboardCanvas";

interface StructuredLessonWhiteboardProps {
  lesson: Lesson;
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

            if (
              CREATION_ACTIONS.has(action.type) &&
              action.target_id
            ) {
              setActiveDrawing({
                objectId: action.target_id,
                progress,
              });
            }
          },

          onActionComplete: (action: VisualAction) => {
            setScene(manager.getScene());

            if (
              CREATION_ACTIONS.has(action.type) &&
              action.target_id
            ) {
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
        <div>
          <h2>{lesson.title}</h2>
          <p>
            Step {activeStepIndex + 1} of {lesson.steps.length}
          </p>
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
            <h3>What this step means</h3>
            <p>{activeStep.explanation}</p>
          </div>
        )}

        {activeStep.equations.length > 0 && (
          <div className="structured-whiteboard-equations">
            <h3>Equations</h3>
            {activeStep.equations.map((equation, index) => (
              <div key={`${activeStep.id}-${index}`}>
                {equation}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
