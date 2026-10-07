export type Mode =
  | "recreate"
  | "create_similar"
  | "extract_style"
  | "extract_composition"
  | "extract_lighting"
  | "extract_color"
  | "extract_pose"
  | "modify";

export const MODE_LABELS: Record<Mode, string> = {
  recreate: "Recreate",
  create_similar: "Create Similar",
  extract_style: "Extract Style",
  extract_composition: "Extract Composition",
  extract_lighting: "Extract Lighting",
  extract_color: "Extract Color",
  extract_pose: "Extract Pose",
  modify: "Modify",
};

// ---------- Visual DNA v2 ----------

export type ConfidenceLevel = "high" | "medium" | "low" | "uncertain";
export type ElementImportance = "essential" | "supporting" | "incidental" | "uncertain";

export interface ReferenceMeta {
  reference_type: string;
  reference_type_confidence: ConfidenceLevel;
  layout_description: string;
  overall_description: string;
  analysis_confidence: number;
  [k: string]: unknown;
}

export interface SubjectRecord {
  label: string;
  type: string;
  count: number;
  description: string;
  age_category: string;
  gender_presentation: string;
  clothing: string;
  accessories: string[];
  pose: string;
  body_orientation: string;
  facial_expression: string;
  gaze_direction: string;
  position_in_frame: string;
  relative_scale: string;
  distinguishing_characteristics: string[];
  interactions: string[];
  confidence: ConfidenceLevel;
  [k: string]: unknown;
}

export interface Swatch {
  name: string;
  hex: string;
  role: string;
}

export interface VisualDNA {
  schema_version: number;
  reference: ReferenceMeta;
  subjects: SubjectRecord[];
  environment: Record<string, unknown> & { objects?: string[]; spatial_relationships?: string[] };
  composition: Record<string, unknown>;
  camera: Record<string, unknown>;
  lighting: Record<string, unknown>;
  color: {
    dominant: Swatch[];
    secondary: Swatch[];
    accent: Swatch[];
    palette_description?: string;
    warm_cool_balance?: string;
    [k: string]: unknown;
  };
  style: Record<string, unknown>;
  mood: { description?: string; emotional_tone?: string[]; [k: string]: unknown };
  materials: Array<Record<string, unknown>>;
  typography: {
    present: boolean;
    text_content?: string[];
    graphics?: string[];
    [k: string]: unknown;
  };
  relationships: Array<{ subject?: string; relation?: string; object?: string; description?: string }>;
  elements: Array<{ description: string; importance: ElementImportance; reason?: string }>;
  interpretation: {
    creative_reading?: string;
    photographic_intent?: string;
    target_emotion?: string;
    notes?: string[];
    [k: string]: unknown;
  };
  uncertainty: string[];
  technical: { aspect_ratio?: string; orientation?: string; image_quality?: string; [k: string]: unknown };
  [k: string]: unknown;
}

export interface CreativeIntent {
  primary_goal: string;
  aesthetic_direction: string;
  photographic_direction: string;
  composition_strategy: string;
  lighting_strategy: string;
  color_strategy: string;
  subject_strategy: string;
  environment_strategy: string;
  emotional_direction: string;
  preserve: string[];
  flexible: string[];
  confidence: ConfidenceLevel;
  [k: string]: unknown;
}

export interface PromptQuality {
  score: number;
  warnings: string[];
  strengths: string[];
  [k: string]: unknown;
}

export interface ShotResult {
  index: number;
  title: string;
  prompt: string;
  negative_prompt: string | null;
  quality: PromptQuality | null;
}

// ---------- API envelope ----------

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: ApiErrorBody | null;
}

export interface AnalyzeData {
  reference_type: string;
  layout_description: string | null;
  visual_dna: VisualDNA;
  creative_intent: CreativeIntent;
  prompt: string | null;
  negative_prompt: string | null;
  prompt_error: { code: string; message: string } | null;
  prompt_quality: PromptQuality | null;
  shots: ShotResult[];
}

export interface GeneratePromptData {
  prompt: string;
  negative_prompt: string | null;
  quality: PromptQuality | null;
}

export interface RefineData extends GeneratePromptData {
  keep: string[];
  change: string[];
}

export interface FetchedImageData {
  image: string;
  width: number;
  height: number;
}

export interface TargetModel {
  id: string;
  name: string;
  supports_negative: boolean;
  soft_char_limit?: number | null;
}

export interface UploadedImage {
  dataUrl: string;
  width: number;
  height: number;
  name: string;
  size: number;
}

export type PromptVersionSource = "analyze" | "regenerate" | "refine" | "edit";

export interface PromptVersion {
  id: string;
  source: PromptVersionSource;
  ts: number;
  prompt: string;
  negative: string | null;
  targetModel?: string;
  instruction?: string;
  keep?: string[];
  change?: string[];
}

export interface HistoryItem {
  id: string;
  ts: number;
  mode: Mode;
  targetModel: string;
  name: string;
  thumbnail: string;
  dna: VisualDNA;
  intent?: CreativeIntent;
  prompt: string;
  negative: string | null;
  instruction?: string;
}

export interface RefineEntry {
  instruction: string;
  keep: string[];
  change: string[];
}
