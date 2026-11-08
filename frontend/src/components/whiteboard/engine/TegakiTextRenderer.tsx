import { TegakiRenderer } from "tegaki/react";
import caveat from "tegaki/fonts/caveat";
import { variationPlugin } from "tegaki";
import type { SceneObject } from "../../../types/visualAction";

interface TegakiTextRendererProps {
  object: SceneObject;
  progress: number;
}

const handwritingPlugins = [variationPlugin({ amount: 1 })];

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

  return (
    <g
      transform={transform}
      style={
        highlight
          ? { filter: `drop-shadow(0 0 8px ${highlight})` }
          : undefined
      }
    >
      <foreignObject
        x={0}
        y={-fontSize}
        width={width}
        height={height}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            color,
            overflow: "hidden",
          }}
        >
          <TegakiRenderer
            font={caveat}
            time={{
              mode: "controlled",
              value: amount,
              unit: "progress",
            }}
            plugins={handwritingPlugins}
            seed={getSeed(object.id)}
            style={{
              width: "100%",
              height: "100%",
              fontSize,
              lineHeight: 1.4,
              color,
              whiteSpace: "pre-wrap",
              margin: 0,
            }}
          >
            {text}
          </TegakiRenderer>
        </div>
      </foreignObject>
    </g>
  );
}