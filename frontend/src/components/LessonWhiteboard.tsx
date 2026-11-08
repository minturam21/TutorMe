
import { useState, useEffect, useRef } from "react";
import DiagramRenderer from "./DiagramRenderer";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

type DiagramElement = {
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  x2: number;
  y2: number;
  label: string;
  color: string;
  points?: string;
  dashed?: boolean;
  strokeWidth?: number;
};

type Lesson = {
  title: string;
  subject: string;
  level: string;
  objectives: string[];
  steps: {
    title: string;
    explanation: string;
    equations: string[];
    visual: {
      type: string;
      description: string;
      elements?: DiagramElement[];
    };
    animation: {
      type: string;
      description: string;
    };
  }[];
  practice_questions: string[];
};

type Props = {
  lesson: Lesson;
};

export default function LessonWhiteboard({ lesson }: Props) {
  const [visibleSteps, setVisibleSteps] = useState<number[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const stepRefs = useRef<(HTMLElement | null)[]>([]);

  const totalSteps = lesson.steps.length;

  function revealStep(index: number) {
    const step = lesson.steps[index];

    if (step?.visual?.type !== "none") {
      setVisibleSteps((current) =>
        current.includes(index) ? current : [...current, index]
      );
    }
  }

  function nextStep() {
    setIsPlaying(false);

    setActiveStep((current) => {
      const next = Math.min(current + 1, totalSteps - 1);
      revealStep(next);
      return next;
    });
  }

  function previousStep() {
    setIsPlaying(false);

    setActiveStep((current) => {
      const previous = Math.max(current - 1, 0);
      return previous;
    });
  }

  function restartLesson() {
    setIsPlaying(false);
    setActiveStep(0);
    setVisibleSteps([]);
  }

  function togglePlayback() {
    if (activeStep >= totalSteps - 1 && !isPlaying) {
      setActiveStep(0);
      setVisibleSteps([]);
    }

    revealStep(activeStep >= totalSteps - 1 ? 0 : activeStep);
    setIsPlaying((current) => !current);
  }

  function toggleStep(index: number) {
    setVisibleSteps((current) =>
      current.includes(index)
        ? current.filter((item) => item !== index)
        : [...current, index]
    );
  }

  function revealAll() {
    setVisibleSteps(
      lesson.steps.map((step, index) =>
        step.visual?.type !== "none" ? index : -1
      ).filter((index) => index !== -1)
    );
    setIsPlaying(false);
  }

  useEffect(() => {
    if (!isPlaying) return;

    const timer = window.setInterval(() => {
      setActiveStep((current) => {
        if (current >= totalSteps - 1) {
          setIsPlaying(false);
          return current;
        }

        const next = current + 1;
        revealStep(next);
        return next;
      });
    }, 5000);

    return () => window.clearInterval(timer);
  }, [isPlaying, totalSteps]);

  useEffect(() => {
    stepRefs.current[activeStep]?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeStep]);

  return (
    <div className="whiteboard">
      <div className="whiteboard-header">
        <div>
          <h2>{lesson.title}</h2>
          <p>{lesson.subject} · {lesson.level} level</p>
        </div>

        <span className="board-status">AI Lesson</span>
      </div>

      <div className="whiteboard-stage">
        <section className="lesson-objectives">
          <h3>What you will learn</h3>

          <ul>
            {lesson.objectives.map((objective, index) => (
              <li key={index}>{objective}</li>
            ))}
          </ul>
        </section>

        <div className="lesson-playback">
          <div className="playback-progress">
            <div
              className="playback-progress-fill"
              style={{
                width: `${totalSteps > 0 ? ((activeStep + 1) / totalSteps) * 100 : 0}%`,
              }}
            />
          </div>

          <span className="playback-counter">
            Step {activeStep + 1} of {totalSteps}
          </span>

          <div className="playback-buttons">
            <button
              type="button"
              onClick={previousStep}
              disabled={activeStep === 0}
            >
              Previous
            </button>

            <button
              type="button"
              className="play-button"
              onClick={togglePlayback}
            >
              {isPlaying ? "Pause" : "Play"}
            </button>

            <button
              type="button"
              onClick={nextStep}
              disabled={activeStep === totalSteps - 1}
            >
              Next
            </button>

            <button type="button" onClick={restartLesson}>
              Restart
            </button>
          </div>
        </div>

        <button
          type="button"
          className="reveal-all-button"
          onClick={revealAll}
        >
          Reveal all diagrams
        </button>

        {lesson.steps.map((step, index) => {
          const isVisible = visibleSteps.includes(index);
          const isActive = activeStep === index;

          return (
            <section
              className={`ai-lesson-step ${isActive ? "active-lesson-step" : ""}`}
              key={index}
              ref={(element) => {
                stepRefs.current[index] = element;
              }}
            >
              <span className="step-label">STEP {index + 1}</span>

              <h2>{step.title}</h2>

              <div className="lesson-explanation">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {step.explanation}
                </ReactMarkdown>
              </div>

              {step.equations?.length > 0 && (
                <div className="physics-equation">
                  {step.equations.map((equation, equationIndex) => (
                    <div key={equationIndex}>
                      <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {`$$${equation}$$`}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>
              )}

              {step.visual?.type !== "none" && (
                <div className="lesson-visual">
                  <strong>Visual: {step.visual.type}</strong>

                  <div className={isVisible ? "diagram-revealed" : "diagram-hidden"}>
                    {isVisible && (
                      <DiagramRenderer
                        elements={step.visual.elements}
                        description={step.visual.description}
                        animated={true}
                      />
                    )}
                  </div>

                  <button
                    type="button"
                    className="reveal-diagram-button"
                    onClick={() => toggleStep(index)}
                  >
                    {isVisible ? "Hide diagram" : "Reveal diagram"}
                  </button>
                </div>
              )}

              {step.animation?.type !== "none" && (
                <div className="lesson-animation">
                  <strong>Animation instructions: {step.animation.type}</strong>
                  <p>{step.animation.description}</p>
                </div>
              )}
            </section>
          );
        })}

        <section className="lesson-practice">
          <h3>Test your understanding</h3>

          {lesson.practice_questions.map((question, index) => (
            <p key={index}>
              <strong>{index + 1}.</strong> {question}
            </p>
          ))}
        </section>
      </div>
    </div>
  );
}
