
import type {
  Scene,
  SceneObject,
  VisualAction,
  CreateObjectParameters,
  DrawShapeParameters,
  DrawLineParameters,
  DrawPathParameters,
  WriteTextParameters,
  WriteEquationParameters,
  MoveObjectParameters,
  RotateObjectParameters,
  TransformObjectParameters,
  HighlightObjectParameters,
} from "../../../types/visualAction";

export class SceneManager {
  private objects = new Map<string, SceneObject>();

  constructor(initialScene?: Scene) {
    if (initialScene) {
      this.loadScene(initialScene);
    }
  }

  loadScene(scene: Scene): void {
    this.objects.clear();

    for (const object of scene.objects) {
      this.objects.set(object.id, structuredClone(object));
    }
  }

  getScene(): Scene {
    return {
      objects: Array.from(this.objects.values()).map((object) =>
        structuredClone(object)
      ),
    };
  }

  getObject(id: string): SceneObject | undefined {
    const object = this.objects.get(id);
    return object ? structuredClone(object) : undefined;
  }

  hasObject(id: string): boolean {
    return this.objects.has(id);
  }

  clear(): void {
    this.objects.clear();
  }

  applyAction(action: VisualAction): void {
    const targetId = action.target_id;

    switch (action.type) {
      case "wait":
        return;

      case "create_object": {
        const p = action.parameters as CreateObjectParameters;

        this.createObject(targetId, p.object_type, {
          x: p.x,
          y: p.y,
          width: p.width,
          height: p.height,
        });
        return;
      }

      case "draw_shape": {
        const p = action.parameters as DrawShapeParameters;

        this.createObject(targetId, p.shape, {
          x: p.x,
          y: p.y,
          width: p.width,
          height: p.height,
          ...(p.label !== undefined ? { label: p.label } : {}),
        });
        return;
      }

      case "draw_line": {
        const p = action.parameters as DrawLineParameters;
        this.createObject(targetId, "line", { ...p });
        return;
      }

      case "draw_arrow": {
        const p = action.parameters as DrawLineParameters;
        this.createObject(targetId, "arrow", { ...p });
        return;
      }

      case "draw_path": {
        const p = action.parameters as DrawPathParameters;
        this.createObject(targetId, "path", { ...p });
        return;
      }

      case "write_text": {
        const p = action.parameters as WriteTextParameters;
        this.createObject(targetId, "text", { ...p });
        return;
      }

      case "write_equation": {
        const p = action.parameters as WriteEquationParameters;
        this.createObject(targetId, "equation", { ...p });
        return;
      }

      case "move_object": {
        const id = this.requireTarget(targetId);
        const p = action.parameters as MoveObjectParameters;
        const object = this.requireObject(id);

        object.properties.x = p.x;
        object.properties.y = p.y;
        return;
      }

      case "rotate_object": {
        const id = this.requireTarget(targetId);
        const p = action.parameters as RotateObjectParameters;
        const object = this.requireObject(id);

        object.properties.angle = p.angle;
        return;
      }

      case "transform_object": {
        const id = this.requireTarget(targetId);
        const p = action.parameters as TransformObjectParameters;
        const object = this.requireObject(id);

        object.properties.scale_x = p.scale_x;
        object.properties.scale_y = p.scale_y;
        return;
      }

      case "highlight_object": {
        const id = this.requireTarget(targetId);
        const p = action.parameters as HighlightObjectParameters;
        const object = this.requireObject(id);

        object.properties.highlight_color = p.color;
        return;
      }

      case "erase_object": {
        const id = this.requireTarget(targetId);
        this.requireObject(id);
        this.objects.delete(id);
        return;
      }

      default: {
        const unsupportedAction: never = action;
        throw new Error(
          `Unsupported action: ${JSON.stringify(unsupportedAction)}`
        );
      }
    }
  }

  private requireTarget(
    targetId: string | null | undefined
  ): string {
    if (!targetId) {
      throw new Error("This action requires a target_id.");
    }

    return targetId;
  }

  private requireObject(id: string): SceneObject {
    const object = this.objects.get(id);

    if (!object) {
      throw new Error(`Object "${id}" does not exist.`);
    }

    return object;
  }

  private createObject(
    targetId: string | null | undefined,
    type: string,
    properties: Record<string, unknown>
  ): void {
    if (!targetId) {
      throw new Error("Creation action requires a target_id.");
    }

    if (this.objects.has(targetId)) {
      throw new Error(`Object "${targetId}" already exists.`);
    }

    const object: SceneObject = {
      id: targetId,
      type,
      properties: structuredClone(properties),
    };

    this.objects.set(targetId, object);
  }
}
