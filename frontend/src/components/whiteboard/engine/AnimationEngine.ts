
import type { EasingType } from "../../../types/visualAction";

type ProgressCallback = (progress: number) => void;

export class AnimationEngine {
  private frameId: number | null = null;
  private startTime = 0;
  private elapsedBeforePause = 0;
  private duration = 0;

  private paused = false;
  private running = false;

  private resolveAnimation: (() => void) | null = null;
  private rejectAnimation: ((error: Error) => void) | null = null;

  animate(
    durationMs: number,
    onProgress: ProgressCallback,
    easing: EasingType = "ease_in_out"
  ): Promise<void> {
    if (!Number.isFinite(durationMs) || durationMs < 0) {
      return Promise.reject(
        new Error("Animation duration must be a non-negative number.")
      );
    }

    this.cancel();

    this.duration = durationMs;
    this.elapsedBeforePause = 0;
    this.paused = false;
    this.running = true;

    this.currentCallback = onProgress;
    this.currentEasing = easing;

    return new Promise<void>((resolve, reject) => {
      this.resolveAnimation = resolve;
      this.rejectAnimation = reject;

      try {
        onProgress(0);

        if (durationMs === 0) {
          onProgress(1);
          this.finish();
          return;
        }

        this.startTime = performance.now();
        this.frameId = requestAnimationFrame((time) =>
          this.update(time, onProgress, easing)
        );
      } catch (error) {
        this.fail(error);
      }
    });
  }

  pause(): void {
    if (!this.running || this.paused) return;

    this.elapsedBeforePause += performance.now() - this.startTime;
    this.paused = true;

    if (this.frameId !== null) {
      cancelAnimationFrame(this.frameId);
      this.frameId = null;
    }
  }

  resume(): void {
    if (!this.running || !this.paused) return;

    this.paused = false;
    this.startTime = performance.now();

    this.frameId = requestAnimationFrame((time) => {
      this.updateCurrentAnimation(time);
    });
  }

  cancel(): void {
    if (!this.running) return;

    if (this.frameId !== null) {
      cancelAnimationFrame(this.frameId);
      this.frameId = null;
    }

    this.running = false;
    this.paused = false;

    const resolve = this.resolveAnimation;

    this.clearState();
    resolve?.();
  }

  isRunning(): boolean {
    return this.running;
  }

  isPaused(): boolean {
    return this.paused;
  }

  private update(
    time: number,
    onProgress: ProgressCallback,
    easing: EasingType
  ): void {
    if (!this.running || this.paused) return;

    try {
      const elapsed =
        this.elapsedBeforePause + (time - this.startTime);

      const rawProgress = Math.min(1, elapsed / this.duration);
      const easedProgress = this.applyEasing(rawProgress, easing);

      onProgress(easedProgress);

      if (rawProgress >= 1) {
        this.finish();
        return;
      }

      this.frameId = requestAnimationFrame((nextTime) =>
        this.update(nextTime, onProgress, easing)
      );
    } catch (error) {
      this.fail(error);
    }
  }

  private updateCurrentAnimation(time: number): void {
    // The active callback is stored when animate() starts.
    if (!this.running || this.paused) return;

    if (!this.currentCallback) return;

    this.update(
      time,
      this.currentCallback,
      this.currentEasing
    );
  }

  private currentCallback: ProgressCallback | null = null;
  private currentEasing: EasingType = "ease_in_out";

  private applyEasing(
    progress: number,
    easing: EasingType
  ): number {
    switch (easing) {
      case "linear":
        return progress;

      case "ease_in":
        return progress * progress;

      case "ease_out":
        return 1 - (1 - progress) * (1 - progress);

      case "ease_in_out":
      default:
        return progress < 0.5
          ? 2 * progress * progress
          : 1 - Math.pow(-2 * progress + 2, 2) / 2;
    }
  }

  private finish(): void {
    if (!this.running) return;

    const resolve = this.resolveAnimation;

    this.running = false;
    this.clearState();
    resolve?.();
  }

  private fail(error: unknown): void {
    if (!this.running) return;

    const reject = this.rejectAnimation;

    this.running = false;

    if (this.frameId !== null) {
      cancelAnimationFrame(this.frameId);
    }

    this.clearState();

    reject?.(
      error instanceof Error
        ? error
        : new Error(String(error))
    );
  }

  private clearState(): void {
    this.frameId = null;
    this.resolveAnimation = null;
    this.rejectAnimation = null;
    this.currentCallback = null;
    this.currentEasing = "ease_in_out";
    this.elapsedBeforePause = 0;
    this.duration = 0;
  }
}
