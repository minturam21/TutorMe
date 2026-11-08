import { useEffect, useState } from "react";
import { TegakiRenderer } from "tegaki/react";
import caveat from "tegaki/fonts/caveat";
import { variationPlugin } from "tegaki";

export default function TegakiTest() {
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (!playing || duration <= 0) return;

    let frame = 0;
    const startTime = performance.now() - progress * duration * 1000;

    function animate(now: number) {
      const next = Math.min((now - startTime) / (duration * 1000), 1);

      setProgress(next);

      if (next >= 1) {
        setPlaying(false);
        setPaused(false);
        return;
      }

      frame = requestAnimationFrame(animate);
    }

    frame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(frame);
  }, [playing, duration]);

  function play() {
    setProgress(0);
    setPaused(false);
    setPlaying(true);
  }

  function pause() {
    setPlaying(false);
    setPaused(true);
  }

  function resume() {
    if (paused && progress < 1) {
      setPaused(false);
      setPlaying(true);
    }
  }

  function restart() {
    setPlaying(false);
    setPaused(false);
    setProgress(0);
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>SVG Handwriting Integration Test</h2>

      <svg
        viewBox="0 0 2000 500"
        width="100%"
        style={{
          display: "block",
          background: "#fff",
          border: "1px solid #ddd",
          borderRadius: 12,
        }}
      >
        <line
          x1="100"
          y1="400"
          x2="1900"
          y2="400"
          stroke="#ddd"
          strokeWidth="2"
        />

        <foreignObject x="150" y="80" width="1500" height="280">
          <div
            style={{
              width: "100%",
              height: "100%",
              color: "#222",
            }}
          >
            <TegakiRenderer
              font={caveat}
              time={{
                mode: "controlled",
                value: progress,
                unit: "progress",
              }}
              onChangeTimeline={(timeline) => {
                setDuration(timeline.totalDuration);
              }}
              plugins={[variationPlugin({ amount: 1 })]}
              seed={42}
              style={{
                width: "100%",
                height: "100%",
                fontSize: 64,
                lineHeight: 1.4,
                color: "#222",
              }}
            >
              Newton's Second Law F = ma Force = Mass × Acceleration
            </TegakiRenderer>
          </div>
        </foreignObject>
      </svg>

      <p>
        Progress: {(progress * 100).toFixed(0)}%{" | "}
        Duration: {duration.toFixed(2)} seconds
      </p>

      <input
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={progress}
        onChange={(event) => {
          setPlaying(false);
          setPaused(false);
          setProgress(Number(event.target.value));
        }}
        style={{ width: "100%" }}
      />

      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <button onClick={play} disabled={playing || duration <= 0}>
          Play
        </button>

        <button onClick={pause} disabled={!playing}>
          Pause
        </button>

        <button onClick={resume} disabled={!paused}>
          Resume
        </button>

        <button onClick={restart}>Restart</button>
      </div>
    </div>
  );
}
