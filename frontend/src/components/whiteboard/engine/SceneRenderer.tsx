import type { Scene, SceneObject } from "../../../types/visualAction";
import DrawingRenderer from "./DrawingRenderer";
import TegakiTextRenderer from "./TegakiTextRenderer";

interface SceneRendererProps {
  scene: Scene;
  width?: number;
  height?: number;
  activeDrawing?: {
    objectId: string;
    progress: number;
  } | null;
  viewBox?: { x: number; y: number; width: number; height: number };
}

function toHandwrittenTextObject(object: SceneObject): SceneObject {
  const properties = object.properties;
  const text =
    object.type === "equation" ? properties.equation : properties.text;

  return {
    ...object,
    type: "text",
    properties: {
      ...properties,
      text: typeof text === "string" ? text : "",
      font_size:
        typeof properties.font_size === "number"
          ? properties.font_size
          : object.type === "equation"
            ? 36
            : 32,
    },
  };
}

export default function SceneRenderer({
  scene,
  width = 2000,
  height = 1400,
  activeDrawing = null,
  viewBox,
}: SceneRendererProps) {
  return (
    <svg
      viewBox={viewBox ? `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}` : `0 0 ${width} ${height}` }
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Interactive lesson whiteboard"
    >
      <defs>
        <marker
          id="scene-arrowhead"
          markerWidth="12"
          markerHeight="12"
          refX="10"
          refY="6"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M 0 0 L 12 6 L 0 12 z" fill="context-stroke" />
        </marker>
      </defs>

      {scene.objects.map((object: SceneObject) => {
        const isBeingDrawn = activeDrawing?.objectId === object.id;
        const progress = isBeingDrawn
          ? (activeDrawing?.progress ?? 0)
          : 1;

        return (
          <g key={object.id}>
            {object.type === "text" || object.type === "equation" ? (
              <TegakiTextRenderer
                object={toHandwrittenTextObject(object)}
                progress={progress}
              />
            ) : (
              <DrawingRenderer object={object} progress={progress} />
            )}
          </g>
        );
      })}
    </svg>
  );
}
