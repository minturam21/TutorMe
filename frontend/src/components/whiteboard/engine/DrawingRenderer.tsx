
import { useId } from "react";
import type { SceneObject } from "../../../types/visualAction";

interface DrawingRendererProps {
  object: SceneObject;
  progress: number;
}

function getNumber(
  properties: Record<string, unknown>,
  key: string,
  fallback = 0
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

function getPoints(value: unknown): [number, number][] {
  if (!Array.isArray(value)) return [];

  return value.filter(
    (point): point is [number, number] =>
      Array.isArray(point) &&
      point.length === 2 &&
      typeof point[0] === "number" &&
      typeof point[1] === "number" &&
      Number.isFinite(point[0]) &&
      Number.isFinite(point[1])
  );
}

function createDefaultPolygonPoints(
  width: number,
  height: number
): [number, number][] {
  return [
    [width * 0.25, 0],
    [width * 0.75, 0],
    [width, height * 0.5],
    [width * 0.75, height],
    [width * 0.25, height],
    [0, height * 0.5],
  ];
}

export default function DrawingRenderer({
  object,
  progress,
}: DrawingRendererProps) {
  const markerId = useId().replace(/:/g, "");

  const p = object.properties;

  const amount = Math.max(0, Math.min(1, progress));

  const x = getNumber(p, "x");
  const y = getNumber(p, "y");
  const width = getNumber(p, "width", 100);
  const height = getNumber(p, "height", 60);

  const stroke = getString(p, "stroke", "#2563eb");
  const fill = getString(p, "fill", "transparent");
  const color = getString(p, "color", "#1e293b");
  const strokeWidth = getNumber(p, "stroke_width", 4);

  const angle = getNumber(p, "angle");
  const scaleX = getNumber(p, "scale_x", 1);
  const scaleY = getNumber(p, "scale_y", 1);

  const highlight = getString(p, "highlight_color", "");

  const transform = [
    `translate(${x} ${y})`,
    `rotate(${angle} ${width / 2} ${height / 2})`,
    `scale(${scaleX} ${scaleY})`,
  ].join(" ");

  const animatedStroke = {
    stroke,
    strokeWidth,
    strokeDasharray: 1,
    strokeDashoffset: 1 - amount,
    strokeLinejoin: "round" as const,
    strokeLinecap: "round" as const,
  };

  const animatedFill = {
    fill,
    fillOpacity: amount,
  };

  let drawing;

  switch (object.type) {
    case "rectangle":
      drawing = (
        <rect
          x={0}
          y={0}
          width={width}
          height={height}
          pathLength={1}
          {...animatedStroke}
          {...animatedFill}
        />
      );
      break;

    case "circle":
      drawing = (
        <circle
          cx={width / 2}
          cy={height / 2}
          r={Math.min(width, height) / 2}
          pathLength={1}
          {...animatedStroke}
          {...animatedFill}
        />
      );
      break;

    case "ellipse":
      drawing = (
        <ellipse
          cx={width / 2}
          cy={height / 2}
          rx={width / 2}
          ry={height / 2}
          pathLength={1}
          {...animatedStroke}
          {...animatedFill}
        />
      );
      break;

    case "line":
    case "arrow": {
      const startX = getNumber(p, "start_x");
      const startY = getNumber(p, "start_y");
      const endX = getNumber(p, "end_x");
      const endY = getNumber(p, "end_y");

      drawing = (
        <>
          {object.type === "arrow" && (
            <defs>
              <marker
                id={markerId}
                markerWidth="12"
                markerHeight="12"
                refX="10"
                refY="6"
                orient="auto"
                markerUnits="strokeWidth"
              >
                <path
                  d="M 0 0 L 12 6 L 0 12 z"
                  fill={stroke}
                />
              </marker>
            </defs>
          )}

          <line
            x1={startX}
            y1={startY}
            x2={endX}
            y2={endY}
            pathLength={1}
            {...animatedStroke}
            markerEnd={
              object.type === "arrow" && amount >= 1
                ? `url(#${markerId})`
                : undefined
            }
          />
        </>
      );
      break;
    }

    case "polygon": {
      const suppliedPoints = getPoints(p.points);

      const points =
        suppliedPoints.length >= 3
          ? suppliedPoints
          : createDefaultPolygonPoints(width, height);

      drawing = (
        <polygon
          points={points.map(([px, py]) => `${px},${py}`).join(" ")}
          pathLength={1}
          {...animatedStroke}
          {...animatedFill}
        />
      );
      break;
    }

    case "path": {
      const points = getPoints(p.points);

      const pathData = points
        .map(([px, py], index) =>
          `${index === 0 ? "M" : "L"} ${px} ${py}`
        )
        .join(" ");

      drawing = (
        <path
          d={`${pathData}${p.closed === true ? " Z" : ""}`}
          pathLength={1}
          {...animatedStroke}
          fill={p.closed === true ? fill : "none"}
          fillOpacity={amount}
        />
      );
      break;
    }

    case "text": {
      const text = getString(p, "text", "");
      const fontSize = getNumber(p, "font_size", 32);

      drawing = (
        <text
          x={0}
          y={0}
          fill={color}
          fontSize={fontSize}
          fontFamily="Arial, sans-serif"
          opacity={amount}
        >
          {text}
        </text>
      );
      break;
    }

    case "equation": {
      const equation = getString(p, "equation", "");

      drawing = (
        <text
          x={0}
          y={0}
          fill={color}
          fontSize={36}
          fontFamily="serif"
          opacity={amount}
        >
          {equation}
        </text>
      );
      break;
    }

    default:
      return null;
  }

  return (
    <g
      transform={transform}
      opacity={amount === 0 ? 0 : 1}
      style={
        highlight
          ? { filter: `drop-shadow(0 0 8px ${highlight})` }
          : undefined
      }
    >
      {drawing}

      {typeof p.label === "string" && amount > 0 && (
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize={24}
          opacity={amount}
        >
          {p.label}
        </text>
      )}
    </g>
  );
}
