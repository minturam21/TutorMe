
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

  constructor(sceneManager: SceneManager) {
    this.sceneManager = sceneManager;
    this.animationEngine = new AnimationEngine();
  }

  cancel(): void {
    this.cancelled = true;
    this.executionId++;

    this.animationEngine.cancel();
  }

  reset(): void {
    this.cancel();

    this.cancelled = false;
  }

  pause(): void {
    this.animationEngine.pause();
  }

  resume(): void {
    this.animationEngine.resume();
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

    // Stop any previous execution before starting another.
    this.cancel();

    this.cancelled = false;

    const currentExecutionId = this.executionId;

    const orderedActions = [...actions].sort(
      (a, b) => a.order - b.order
    );

    for (let index = 0; index < orderedActions.length; index++) {
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
