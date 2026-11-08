
import { useCallback, useEffect, useState } from "react";

import type { TeachingStep } from "../types/lesson";

interface UsePlaybackReturn {
  activeStepIndex: number;
  isPlaying: boolean;
  playbackSpeed: number;
  activeStep: TeachingStep | null;
  play: () => void;
  pause: () => void;
  togglePlayback: () => void;
  nextStep: () => void;
  previousStep: () => void;
  goToStep: (index: number) => void;
  setPlaybackSpeed: (speed: number) => void;
  resetPlayback: () => void;
}

export function usePlayback(
  steps: TeachingStep[]
): UsePlaybackReturn {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeedState] = useState(1);

  const activeStep = steps[activeStepIndex] ?? null;

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const play = useCallback(() => {
    if (steps.length === 0) return;

    setActiveStepIndex((current) =>
      current >= steps.length - 1 ? 0 : current
    );

    setIsPlaying(true);
  }, [steps.length]);

  const togglePlayback = useCallback(() => {
    if (steps.length === 0) return;

    setIsPlaying((current) => !current);
  }, [steps.length]);

  const nextStep = useCallback(() => {
    setIsPlaying(false);

    setActiveStepIndex((current) =>
      Math.min(current + 1, steps.length - 1)
    );
  }, [steps.length]);

  const previousStep = useCallback(() => {
    setIsPlaying(false);

    setActiveStepIndex((current) =>
      Math.max(current - 1, 0)
    );
  }, []);

  const goToStep = useCallback(
    (index: number) => {
      if (index < 0 || index >= steps.length) return;

      setIsPlaying(false);
      setActiveStepIndex(index);
    },
    [steps.length]
  );

  const updatePlaybackSpeed = useCallback((speed: number) => {
    if (!Number.isFinite(speed) || speed <= 0) return;

    setPlaybackSpeedState(Math.min(speed, 4));
  }, []);

  const resetPlayback = useCallback(() => {
    setIsPlaying(false);
    setActiveStepIndex(0);
  }, []);

  // Automatically advance through teaching steps.
  useEffect(() => {
    if (!isPlaying || !activeStep) return;

    const duration = Math.max(
      100,
      (activeStep.duration * 1000) / playbackSpeed
    );

    const timer = window.setTimeout(() => {
      if (activeStepIndex < steps.length - 1) {
        setActiveStepIndex((current) => current + 1);
      } else {
        setIsPlaying(false);
      }
    }, duration);

    return () => window.clearTimeout(timer);
  }, [
    isPlaying,
    activeStep,
    activeStepIndex,
    playbackSpeed,
    steps.length,
  ]);

  // Stop playback if the current index becomes invalid.
  useEffect(() => {
    if (steps.length === 0 || activeStepIndex >= steps.length) {
      setIsPlaying(false);
      setActiveStepIndex(0);
    }
  }, [steps.length, activeStepIndex]);

  return {
    activeStepIndex,
    isPlaying,
    playbackSpeed,
    activeStep,
    play,
    pause,
    togglePlayback,
    nextStep,
    previousStep,
    goToStep,
    setPlaybackSpeed: updatePlaybackSpeed,
    resetPlayback,
  };
}
