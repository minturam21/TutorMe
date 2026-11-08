
import type { Scene, SceneObject } from "../../../types/visualAction";
import DrawingRenderer from "./DrawingRenderer";
import TegakiTextRenderer from "./TegakiTextRenderer";

interface SceneRendererProps {
  scene: Scene;
  width?: number;
  height?: number;

  // Identifies the object currently being drawn.
  activeDrawing?: {
    objectId: string;
    progress: number;
  } | null;
}

export default function SceneRenderer({
  scene,
  width = 2000,
  height = 1400,
  activeDrawing = null,
}: SceneRendererProps) {
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
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
            {object.type === "text" ? (
              <TegakiTextRenderer
                object={object}
                progress={progress}
              />
            ) : (
              <DrawingRenderer
                object={object}
                progress={progress}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}
