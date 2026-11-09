
import type {
  VisualAction,
  Scene,
  EasingType,
} from "../../../types/visualAction";

import { SceneManager } from "./SceneManager";
import { AnimationEngine } from "./AnimationEngine";

export interface ActionExecutionOptions {
  onActionStart?: (action: VisualAction, index: number) => void;

  onActionProgress?: (
    action: VisualAction,
    index: number,
    progress: number
  ) => void;

  onActionComplete?: (
    action: VisualAction,
    index: number,
    scene: Scene
  ) => void;

  onError?: (error: Error, action: VisualAction) => void;
}

export class ActionExecutor {
  private sceneManager: SceneManager;
  private animationEngine: AnimationEngine;

  private cancelled = false;
  private executionId = 0;
  private sequencePaused = false;
  private resumeSequence: (() => void) | null = null;

  constructor(sceneManager: SceneManager) {
    this.sceneManager = sceneManager;
    this.animationEngine = new AnimationEngine();
  }

  cancel(): void {
    this.cancelled = true;
    this.executionId++;
    this.sequencePaused = false;
    this.resumeSequence?.();
    this.resumeSequence = null;
    this.animationEngine.cancel();
  }

  reset(): void {
    this.cancel();

    this.cancelled = false;
  }

  pause(): void {
    this.sequencePaused = true;
    this.animationEngine.pause();
  }

  resume(): void {
    this.sequencePaused = false;
    this.animationEngine.resume();
    this.resumeSequence?.();
    this.resumeSequence = null;
  }

  private async waitWhilePaused(executionId: number): Promise<void> {
    while (this.sequencePaused && !this.cancelled && executionId === this.executionId) {
      await new Promise<void>((resolve) => {
        this.resumeSequence = resolve;
      });
    }
  }

  isRunning(): boolean {
    return this.animationEngine.isRunning();
  }

  isPaused(): boolean {
    return this.animationEngine.isPaused();
  }

  async executeSequence(
    actions: VisualAction[],
    playbackSpeed = 1,
    options: ActionExecutionOptions = {}
  ): Promise<void> {
    if (!Number.isFinite(playbackSpeed) || playbackSpeed <= 0) {
      throw new Error("Playback speed must be greater than zero.");
    }

    // Start a new sequence without clearing a lesson-wide pause request.
    // A caller starting a fresh lesson must call cancel() explicitly first.
    this.cancelled = false;
    this.executionId++;

    const currentExecutionId = this.executionId;

    const orderedActions = [...actions].sort(
      (a, b) => a.order - b.order
    );

    for (let index = 0; index < orderedActions.length; index++) {
      await this.waitWhilePaused(currentExecutionId);

      if (
        this.cancelled ||
        currentExecutionId !== this.executionId
      ) {
        return;
      }

      const action = orderedActions[index];

      try {
        options.onActionStart?.(action, index);

        // Apply the scene change first.
        // DrawingRenderer will use progress to reveal it.
        this.sceneManager.applyAction(action);

        const durationMs =
          (action.duration * 1000) / playbackSpeed;

        const easing = action.easing as EasingType;

        // Animate this action before starting the next one.
        await this.animationEngine.animate(
          durationMs,
          (progress) => {
            if (
              this.cancelled ||
              currentExecutionId !== this.executionId
            ) {
              return;
            }

            options.onActionProgress?.(
              action,
              index,
              progress
            );
          },
          easing
        );

        if (
          this.cancelled ||
          currentExecutionId !== this.executionId
        ) {
          return;
        }

        options.onActionComplete?.(
          action,
          index,
          this.sceneManager.getScene()
        );
      } catch (error) {
        const executionError =
          error instanceof Error
            ? error
            : new Error(String(error));

        options.onError?.(executionError, action);

        throw executionError;
      }
    }
  }
}
