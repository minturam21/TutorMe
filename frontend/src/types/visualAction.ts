
export type VisualActionType =
  | "create_object"
  | "draw_shape"
  | "draw_line"
  | "draw_arrow"
  | "draw_path"
  | "write_text"
  | "write_equation"
  | "move_object"
  | "rotate_object"
  | "transform_object"
  | "highlight_object"
  | "erase_object"
  | "wait";

export type EasingType =
  | "linear"
  | "ease_in"
  | "ease_out"
  | "ease_in_out";

export type CanvasX = number;
export type CanvasY = number;

export type ObjectType =
  | "rectangle"
  | "circle"
  | "ellipse"
  | "line"
  | "arrow"
  | "polygon"
  | "text";

export type ShapeType =
  | "rectangle"
  | "circle"
  | "ellipse"
  | "polygon";

// Parameters for each supported action.

export interface CreateObjectParameters {
  object_type: ObjectType;
  x: CanvasX;
  y: CanvasY;
  width: number;
  height: number;
}

export interface DrawShapeParameters {
  shape: ShapeType;
  x: CanvasX;
  y: CanvasY;
  width: number;
  height: number;
  label?: string | null;
}

export interface DrawLineParameters {
  start_x: CanvasX;
  start_y: CanvasY;
  end_x: CanvasX;
  end_y: CanvasY;
}

export interface DrawPathParameters {
  points: [CanvasX, CanvasY][];
  closed: boolean;
}

export interface WriteTextParameters {
  text: string;
  x: CanvasX;
  y: CanvasY;
}

export interface WriteEquationParameters {
  equation: string;
  x: CanvasX;
  y: CanvasY;
}

export interface MoveObjectParameters {
  x: CanvasX;
  y: CanvasY;
}

export interface RotateObjectParameters {
  angle: number;
}

export interface TransformObjectParameters {
  scale_x: number;
  scale_y: number;
}

export interface HighlightObjectParameters {
  color: string;
}

export type EraseObjectParameters = Record<string, never>;
export type WaitParameters = Record<string, never>;

// Shared action metadata.

interface VisualActionBase<T extends VisualActionType, P> {
  id: string;
  type: T;
  target_id?: string | null;
  parameters: P;
  duration: number;
  easing: EasingType;
  order: number;
}

// Discriminated union: action type determines its parameters.

export type VisualAction =
  | VisualActionBase<"create_object", CreateObjectParameters>
  | VisualActionBase<"draw_shape", DrawShapeParameters>
  | VisualActionBase<"draw_line", DrawLineParameters>
  | VisualActionBase<"draw_arrow", DrawLineParameters>
  | VisualActionBase<"draw_path", DrawPathParameters>
  | VisualActionBase<"write_text", WriteTextParameters>
  | VisualActionBase<"write_equation", WriteEquationParameters>
  | VisualActionBase<"move_object", MoveObjectParameters>
  | VisualActionBase<"rotate_object", RotateObjectParameters>
  | VisualActionBase<"transform_object", TransformObjectParameters>
  | VisualActionBase<"highlight_object", HighlightObjectParameters>
  | VisualActionBase<"erase_object", EraseObjectParameters>
  | VisualActionBase<"wait", WaitParameters>;

// Scene objects represent the current whiteboard state.

export interface SceneObject {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface Scene {
  objects: SceneObject[];
}
