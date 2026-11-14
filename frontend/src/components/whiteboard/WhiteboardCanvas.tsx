
import type { Scene } from "../../types/visualAction";
import SceneRenderer from "./engine/SceneRenderer";

interface WhiteboardCanvasProps {
  scene: Scene;
  activeDrawing?: {
    objectId: string;
    progress: number;
  } | null;
  viewBox?: { x: number; y: number; width: number; height: number };
}

export default function WhiteboardCanvas({
  scene,
  activeDrawing = null,
  viewBox = { x: 0, y: 0, width: 2000, height: 1400 },
}: WhiteboardCanvasProps) {
  return (
    <div className="whiteboard-canvas">
      <SceneRenderer
        scene={scene}
        width={viewBox.width}
        height={viewBox.height}
        viewBox={viewBox}
        activeDrawing={activeDrawing}
      />
    </div>
  );
}
