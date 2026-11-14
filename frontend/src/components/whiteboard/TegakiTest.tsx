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
  {
    id: "hybrid-script-digits",
    type: "text",
    properties: { text: "Powers and indices: x² + y³; H₂O; CO₂; a₁ + a₂", x: 60, y: 570, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
  {
    id: "hybrid-custom-arrows",
    type: "text",
    properties: { text: "Custom arrows and relations: \u2190 \u2192 \u2194 \u21D2 \u21D4 \u2213 \u2261 \u2207", x: 60, y: 690, width: 1800, height: 120, font_size: 54, color: "#222222" },
  },
  {
    id: "hybrid-custom-math",
    type: "text",
    properties: { text: "Custom math: \u222C \u222E \u221B \u221C \u221D \u2234 \u2235 \u2208 \u2209 \u2282 \u2286 \u222A \u2229 \u2227 \u2228", x: 60, y: 810, width: 1800, height: 120, font_size: 54, color: "#222222" },
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
    <main style={{ padding: 16, color: "#222", background: "#f3f0e8", minHeight: "100vh", overflowY: "auto" }}>
      <h2> TutorMe — Hybrid Tegaki Renderer Test</h2>
      <p>Latin characters use Caveat. Greek characters use Playpen Sans. Custom mathematical symbols use the TutorMe handwriting glyph bundle.</p>
      <svg viewBox="0 0 2000 960" width="100%" style={{ display: "block", height: "min(68vh, 680px)", background: "#fffdf7", border: "1px solid #ccc", borderRadius: 12 }}>
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



