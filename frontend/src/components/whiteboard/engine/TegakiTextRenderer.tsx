import { TegakiRenderer } from "tegaki/react";
import { computeTimeline, variationPlugin } from "tegaki";
import caveat from "tegaki/fonts/caveat";
import notoSansMath from "../../../assets/tegaki/noto-sans-math/bundle";
import playpenSans from "../../../assets/tegaki/playpen-sans/bundle";
import { customMathGlyphData } from "../../../assets/tegaki/customMathGlyphs";

const customMathFont = {
  ...playpenSans,
  glyphData: {
    ...playpenSans.glyphData,
    ...customMathGlyphData,
  },
  // Disable Playpen's old glyph-ID map so Tegaki uses our custom character paths.
  glyphDataById: undefined,
} as unknown as typeof playpenSans;
import type { SceneObject } from "../../../types/visualAction";

interface TegakiTextRendererProps {
  object: SceneObject;
  progress: number;
}

type FontBundle =
  | typeof caveat
  | typeof notoSansMath
  | typeof playpenSans
  | typeof customMathFont;

type FontKind =
  | "caveat"
  | "playpen"
  | "custom-math"
  | "math"
  | "superscript"
  | "subscript"
  | "unsupported";

interface TextRun {
  text: string;
  renderText: string;
  font: FontBundle;
  kind: FontKind;
  duration: number;
}

const handwritingPlugins = [variationPlugin({ amount: 1 })];
const caveatCharacters = new Set(Object.keys(caveat.glyphData));
const mathCharacters = new Set(Object.keys(notoSansMath.glyphData));
const playpenCharacters = new Set(Object.keys(playpenSans.glyphData));
const customMathCharacters = new Set(Object.keys(customMathGlyphData));

// Unicode script digits reuse Caveat's existing handwritten digit glyphs.
const superscriptDigits: Record<string, string> = {
  "⁰": "0",
  "¹": "1",
  "²": "2",
  "³": "3",
  "⁴": "4",
  "⁵": "5",
  "⁶": "6",
  "⁷": "7",
  "⁸": "8",
  "⁹": "9",
};

const subscriptDigits: Record<string, string> = {
  "₀": "0",
  "₁": "1",
  "₂": "2",
  "₃": "3",
  "₄": "4",
  "₅": "5",
  "₆": "6",
  "₇": "7",
  "₈": "8",
  "₉": "9",
};

const SCRIPT_GLYPH_SCALE = 0.65;

function getNumber(
  properties: Record<string, unknown>,
  key: string,
  fallback: number
): number {
  const value = properties[key];

  return typeof value === "number" && Number.isFinite(value)
    ? value
    : fallback;
}

function getString(
  properties: Record<string, unknown>,
  key: string,
  fallback: string
): string {
  const value = properties[key];

  return typeof value === "string" ? value : fallback;
}

// Gives each text object a repeatable variation seed.
function getSeed(id: string): number {
  let seed = 0;

  for (let i = 0; i < id.length; i++) {
    seed = (seed * 31 + id.charCodeAt(i)) >>> 0;
  }

  return seed;
}

function getFontKind(character: string): FontKind {
  if (character in superscriptDigits) return "superscript";
  if (character in subscriptDigits) return "subscript";

  // Whitespace has layout but no visible glyph stroke; keep it with Latin runs.
  if (/^\s+$/u.test(character) || caveatCharacters.has(character)) {
    return "caveat";
  }

  if (playpenCharacters.has(character)) return "playpen";

  if (customMathCharacters.has(character)) return "custom-math";

  if (mathCharacters.has(character)) {
    return "math";
  }

  return "unsupported";
}

function getRenderableCharacter(character: string): string {
  return superscriptDigits[character] ?? subscriptDigits[character] ?? character;
}

function splitTextIntoRuns(text: string): TextRun[] {
  const runs: Array<{ text: string; renderText: string; kind: FontKind }> = [];

  for (const character of text) {
    const kind = getFontKind(character);
    const renderCharacter = getRenderableCharacter(character);
    const lastRun = runs[runs.length - 1];

    if (lastRun?.kind === kind) {
      lastRun.text += character;
      lastRun.renderText += renderCharacter;
    } else {
      runs.push({ text: character, renderText: renderCharacter, kind });
    }
  }

  return runs.map((run) => {
    const font =
      run.kind === "playpen"
        ? playpenSans
        : run.kind === "custom-math"
          ? customMathFont
          : run.kind === "math"
            ? notoSansMath
            : caveat;
    const duration =
      run.kind === "unsupported"
        ? 0
        : computeTimeline(run.renderText, font).totalDuration;

    return { ...run, font, duration };
  });
}

export default function TegakiTextRenderer({
  object,
  progress,
}: TegakiTextRendererProps) {
  const p = object.properties;

  const text = getString(p, "text", "");
  const x = getNumber(p, "x", 0);
  const y = getNumber(p, "y", 0);

  const fontSize = getNumber(p, "font_size", 32);
  const width = getNumber(p, "width", 900);
  const height = getNumber(p, "height", Math.max(100, fontSize * 2.5));

  const color = getString(p, "color", "#1e293b");
  const angle = getNumber(p, "angle", 0);
  const scaleX = getNumber(p, "scale_x", 1);
  const scaleY = getNumber(p, "scale_y", 1);

  const highlight = getString(p, "highlight_color", "");
  const amount = Math.max(0, Math.min(1, progress));

  const transform = [
    `translate(${x} ${y})`,
    `rotate(${angle} ${width / 2} ${height / 2})`,
    `scale(${scaleX} ${scaleY})`,
  ].join(" ");

  if (!text.trim()) return null;

  const runs = splitTextIntoRuns(text);
  const totalDuration = runs.reduce((total, run) => total + run.duration, 0);
  let elapsed = 0;

  const renderedRuns = runs.map((run, index) => {
    if (run.kind === "unsupported") {
      console.warn(
        `[TutorMe] No Tegaki stroke data for character(s): ${JSON.stringify(run.text)}. Add these characters to a Tegaki font bundle before using them in lesson content.`
      );

      return (
        <span
          key={`unsupported-${index}`}
          aria-label={`Unsupported handwriting character: ${run.text}`}
          style={{ display: "none" }}
        />
      );
    }

    const start = elapsed;
    elapsed += run.duration;

    const localProgress =
      run.duration <= 0 || totalDuration <= 0
        ? amount
        : Math.max(
            0,
            Math.min(1, (amount * totalDuration - start) / run.duration)
          );

    return (
      <span
        key={`${run.kind}-${index}`}
        style={{
          display: "inline-block",
          whiteSpace: "pre-wrap",
          verticalAlign:
            run.kind === "superscript"
              ? "super"
              : run.kind === "subscript"
                ? "sub"
                : "baseline",
        }}
      >
        <TegakiRenderer
          font={run.font}
          time={{
            mode: "controlled",
            value: localProgress,
            unit: "progress",
          }}
          plugins={handwritingPlugins}
          seed={getSeed(`${object.id}-${index}`)}
          style={{
            display: "inline-block",
            width: "max-content",
            maxWidth: "100%",
            fontSize:
              run.kind === "superscript" || run.kind === "subscript"
                ? fontSize * SCRIPT_GLYPH_SCALE
                : fontSize,
            lineHeight: 1.4,
            color,
            whiteSpace: "pre-wrap",
            margin: 0,
          }}
        >
          {run.renderText}
        </TegakiRenderer>
      </span>
    );
  });

  return (
    <g
      transform={transform}
      style={
        highlight
          ? { filter: `drop-shadow(0 0 8px ${highlight})` }
          : undefined
      }
    >
      <foreignObject x={0} y={-fontSize} width={width} height={height}>
        <div
          style={{
            width: "100%",
            height: "100%",
            color,
            overflow: "hidden",
            whiteSpace: "pre-wrap",
          }}
        >
          {renderedRuns}
        </div>
      </foreignObject>
    </g>
  );
}



