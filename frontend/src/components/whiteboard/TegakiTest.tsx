import { useEffect, useState } from "react";
import TegakiTextRenderer from "./engine/TegakiTextRenderer";
import type { SceneObject } from "../../types/visualAction";

const samples: SceneObject[] = [
  {
    id: "hybrid-latin",
    type: "text",
    properties: { text: "Newton's Second Law: Force = Mass × Acceleration", x: 60, y: 90, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
  {
    id: "hybrid-greek",
    type: "text",
    properties: { text: "Greek: α β γ θ λ π Ω", x: 60, y: 210, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
  {
    id: "hybrid-math",
    type: "text",
    properties: { text: "Operators: ± × ÷ → ∞ ≠ ≤ ≥ ∑ ∫ √ ∂ ∇", x: 60, y: 330, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
  {
    id: "hybrid-mixed",
    type: "text",
    properties: { text: "Mixed: F = ma; π ≈ 3.14; √x", x: 60, y: 450, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
];

export default function TegakiTest() {
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;

    let frame = 0;
    const start = performance.now() - progress * 12000;

    const animate = (now: number) => {
      const next = Math.min((now - start) / 12000, 1);
      setProgress(next);
      if (next >= 1) {
        setPlaying(false);
        return;
      }
      frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [playing]);

  return (
    <main style={{ padding: 24, color: "#222", background: "#f3f0e8", minHeight: "100vh" }}>
      <h2> TutorMe — Hybrid Tegaki Renderer Test</h2>
      <p>Latin characters use Caveat. Supported Greek and mathematical glyphs use the custom Noto Sans Math bundle.</p>
      <svg viewBox="0 0 2000 560" width="100%" style={{ display: "block", background: "#fffdf7", border: "1px solid #ccc", borderRadius: 12 }}>
        {samples.map((object) => (
          <TegakiTextRenderer key={object.id} object={object} progress={progress} />
        ))}
      </svg>
      <p>Progress: {(progress * 100).toFixed(0)}%</p>
      <input aria-label="Handwriting progress" type="range" min={0} max={1} step={0.01} value={progress} onChange={(event) => { setPlaying(false); setProgress(Number(event.target.value)); }} style={{ width: "100%" }} />
      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <button onClick={() => { setProgress(0); setPlaying(true); }}>Play</button>
        <button onClick={() => setPlaying(false)}>Pause</button>
        <button onClick={() => { setPlaying(false); setProgress(0); }}>Restart</button>
        <button onClick={() => { setPlaying(false); setProgress(1); }}>Skip to End</button>
      </div>
    </main>
  );
}
