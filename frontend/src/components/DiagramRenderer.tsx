import { useId, useEffect, useState } from "react";

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

type Props = {
  elements?: DiagramElement[];
  description?: string;
  animated?: boolean;
};

export default function DiagramRenderer({
  elements = [],
  description,
  animated = false,
}: Props) {
  const markerId = `arrow-${useId().replace(/:/g, "")}`;
  const [visibleCount, setVisibleCount] = useState(
    animated ? 0 : elements.length,
  );

  useEffect(() => {
    if (!animated) {
      setVisibleCount(elements.length);
      return;
    }

    setVisibleCount(0);

    let current = 0;

    const interval = window.setInterval(() => {
      current += 1;
      setVisibleCount(current);

      if (current >= elements.length) {
        window.clearInterval(interval);
      }
    }, 450);

    return () => window.clearInterval(interval);
  }, [animated, elements]);

  if (elements.length === 0) {
    return (
      <div className="lesson-visual">
        <strong>Visual description</strong>
        <p>{description || "No drawing instructions available."}</p>
      </div>
    );
  }

  const displayedElements = elements.slice(0, visibleCount);

  return (
    <div className="diagram-container">
      <svg
        viewBox="0 0 700 400"
        role="img"
        aria-label={description || "Lesson diagram"}
        className="ai-diagram"
      >
        <defs>
          <marker
            id={markerId}
            markerWidth="10"
            markerHeight="10"
            refX="8"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0 0 L0 6 L9 3 Z" fill="context-stroke" />
          </marker>
        </defs>

        {displayedElements.map((element, index) => {
          const color = element.color || "#2563eb";
          const strokeWidth = element.strokeWidth || 3;
          const dashed = element.dashed ? "7 5" : undefined;

          switch (element.type.toLowerCase()) {
            case "rectangle":
              return (
                <g key={index} className="drawing-element">
                  <rect
                    x={element.x}
                    y={element.y}
                    width={element.width}
                    height={element.height}
                    fill={`${color}20`}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashed}
                    rx="6"
                  />
                  {element.label && (
                    <text
                      x={element.x + element.width / 2}
                      y={element.y + element.height / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#1e293b"
                      fontSize="15"
                    >
                      {element.label}
                    </text>
                  )}
                </g>
              );

            case "circle":
              return (
                <g key={index} className="drawing-element">
                  <circle
                    cx={element.x}
                    cy={element.y}
                    r={element.width || 30}
                    fill={`${color}20`}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashed}
                  />
                  {element.label && (
                    <text
                      x={element.x}
                      y={element.y + (element.width || 30) + 20}
                      textAnchor="middle"
                      fill="#1e293b"
                      fontSize="15"
                    >
                      {element.label}
                    </text>
                  )}
                </g>
              );

            case "ellipse":
              return (
                <g key={index} className="drawing-element">
                  <ellipse
                    cx={element.x}
                    cy={element.y}
                    rx={element.width || 40}
                    ry={element.height || 25}
                    fill={`${color}20`}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashed}
                  />
                  {element.label && (
                    <text
                      x={element.x}
                      y={element.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#1e293b"
                      fontSize="14"
                    >
                      {element.label}
                    </text>
                  )}
                </g>
              );

            case "line":
            case "arrow":
              return (
                <g key={index} className="drawing-element">
                  <line
                    x1={element.x}
                    y1={element.y}
                    x2={element.x2}
                    y2={element.y2}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashed}
                    markerEnd={
                      element.type.toLowerCase() === "arrow"
                        ? `url(#${markerId})`
                        : undefined
                    }
                  />
                  {element.label && (
                    <text
                      x={
                        element.x2 >= element.x ? element.x - 8 : element.x + 8
                      }
                      y={element.y - 14}
                      textAnchor={element.x2 >= element.x ? "end" : "start"}
                      fill="#1e293b"
                      fontSize="14"
                      fontWeight="600"
                    >
                      {element.label}
                    </text>
                  )}
                </g>
              );

            case "polygon":
              return (
                <g key={index} className="drawing-element">
                  <polygon
                    points={
                      element.points ||
                      `${element.x},${element.y} ${element.x + element.width},${element.y} ${element.x + element.width / 2},${element.y - element.height}`
                    }
                    fill={`${color}20`}
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={dashed}
                  />
                  {element.label && (
                    <text
                      x={element.x + element.width / 2}
                      y={element.y - element.height / 3}
                      textAnchor="middle"
                      fill="#1e293b"
                      fontSize="14"
                    >
                      {element.label}
                    </text>
                  )}
                </g>
              );

            case "text":
              return (
                <text
                  key={index}
                  className="drawing-element"
                  x={element.x}
                  y={element.y}
                  fill={color}
                  fontSize={element.width || 18}
                >
                  {element.label}
                </text>
              );

            default:
              return null;
          }
        })}
      </svg>

      {animated && (
        <p className="drawing-progress">
          Drawing: {visibleCount} / {elements.length} elements
        </p>
      )}
    </div>
  );
}
