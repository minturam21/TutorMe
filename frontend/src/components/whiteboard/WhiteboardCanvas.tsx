
import type { Scene } from "../../types/visualAction";
import SceneRenderer from "./engine/SceneRenderer";

interface WhiteboardCanvasProps {
  scene: Scene;
  activeDrawing?: {
    objectId: string;
    progress: number;
  } | null;
}

export default function WhiteboardCanvas({
  scene,
  activeDrawing = null,
}: WhiteboardCanvasProps) {
  return (
    <div className="whiteboard-canvas">
      <SceneRenderer
        scene={scene}
        width={2000}
        height={1400}
        activeDrawing={activeDrawing}
      />
    </div>
  );
}
