import { useCallback, useEffect, useReducer, useRef } from "react";
import { api, isAbortError } from "../services/api";
import { AppError, errorCodeOf, friendlyMessage, requestIdOf } from "../services/errors";
import type {
  CreativeIntent,
  HistoryItem,
  Mode,
  PanelInfo,
  PromptQuality,
  PromptVersion,
  PromptVersionSource,
  ShotResult,
  TargetModel,
  UploadedImage,
  VisualDNA,
} from "../types";
import { HISTORY_SCHEMA_VERSION, saveHistoryItem } from "../utils/history";
import { newId } from "../utils/id";
import { thumbnailOf } from "../utils/image";

export type Busy = "analyzing" | "regenerating" | "refining" | "validating" | null;
export type Phase = "setup" | "result";
export type AnalysisStatus = "idle" | "uploading" | "analyzing" | "analyzed" | "refining" | "error";

export interface BannerAction {
  label: string;
  run: () => void;
}

export interface AnalysisState {
  status: AnalysisStatus;
  image: UploadedImage | null;
  mode: Mode;
  targetModel: string;
  instruction: string;
  phase: Phase;
  busy: Busy;
  urlBusy: boolean;
  error: string | null;
  errorCode?: string;
  errorRequestId?: string;
  errorAction: BannerAction | null;
  dna: VisualDNA | null;
  intent: CreativeIntent | null;
  shots: ShotResult[];
  panels: PanelInfo[];
  layout: string | null;
  quality: PromptQuality | null;
  prompt: string;
  negative: string | null;
  versions: PromptVersion[];
  activeVersionId: string | null;
}

type Action =
  | { type: "IMAGE_ADOPTED"; image: UploadedImage }
  | { type: "RESET" }
  | { type: "SET_MODE"; mode: Mode }
  | { type: "SET_INSTRUCTION"; instruction: string }
  | { type: "MODEL_CHANGED"; targetModel: string }
  | { type: "URL_BUSY"; busy: boolean }
  | { type: "CLEAR_ERROR" }
  | { type: "SET_ERROR"; error: string; code?: string; requestId?: string; action?: BannerAction | null }
  | { type: "ANALYSIS_STARTED" }
  | {
      type: "ANALYSIS_SUCCEEDED";
      dna: VisualDNA;
      intent: CreativeIntent;
      shots: ShotResult[];
      panels: PanelInfo[];
      layout: string | null;
      quality: PromptQuality | null;
      prompt: string;
      negative: string | null;
      versions: PromptVersion[];
      activeVersionId: string | null;
      promptError?: { message: string; code: string; retry: BannerAction } | null;
    }
  | { type: "ANALYSIS_FAILED"; error: string; code?: string; requestId?: string }
  | {
      type: "PROMPT_REGENERATED";
      prompt: string;
      negative: string | null;
      quality: PromptQuality | null;
      version: PromptVersion;
    }
  | {
      type: "PROMPT_REFINED";
      prompt: string;
      negative: string | null;
      quality: PromptQuality | null;
      version: PromptVersion;
    }
  | { type: "PROMPT_EDITED"; prompt: string; version: PromptVersion }
  | { type: "PROMPT_VALIDATED"; quality: PromptQuality | null }
  | { type: "BUSY"; busy: Busy }
  | { type: "VERSION_RESTORED"; version: PromptVersion }
  | { type: "HISTORY_RESTORED"; item: HistoryItem; version: PromptVersion };

function newVersion(
  source: PromptVersionSource,
  prompt: string,
  negative: string | null,
  extra: Partial<PromptVersion> = {}
): PromptVersion {
  return { id: newId(), source, ts: Date.now(), prompt, negative, ...extra };
}

export const initialAnalysisState: AnalysisState = {
  status: "idle",
  image: null,
  mode: "recreate",
  targetModel: "generic",
  instruction: "",
  phase: "setup",
  busy: null,
  urlBusy: false,
  error: null,
  errorCode: undefined,
  errorRequestId: undefined,
  errorAction: null,
  dna: null,
  intent: null,
  shots: [],
  panels: [],
  layout: null,
  quality: null,
  prompt: "",
  negative: null,
  versions: [],
  activeVersionId: null,
};

function clearAnalysisFields(state: AnalysisState): AnalysisState {
  return {
    ...state,
    dna: null,
    intent: null,
    shots: [],
    panels: [],
    layout: null,
    quality: null,
    prompt: "",
    negative: null,
    versions: [],
    activeVersionId: null,
    phase: "setup",
    status: "idle",
    busy: null,
  };
}

export function analysisReducer(state: AnalysisState, action: Action): AnalysisState {
  switch (action.type) {
    case "IMAGE_ADOPTED":
      return clearAnalysisFields({ ...state, image: action.image, error: null, errorAction: null });
    case "RESET":
      return { ...initialAnalysisState, mode: state.mode, targetModel: state.targetModel, instruction: "" };
    case "SET_MODE":
      return { ...state, mode: action.mode };
    case "SET_INSTRUCTION":
      return { ...state, instruction: action.instruction };
    case "MODEL_CHANGED":
      return { ...state, targetModel: action.targetModel };
    case "URL_BUSY":
      return { ...state, urlBusy: action.busy };
    case "CLEAR_ERROR":
      return { ...state, error: null, errorCode: undefined, errorRequestId: undefined, errorAction: null };
    case "SET_ERROR":
      return {
        ...state,
        error: action.error,
        errorCode: action.code,
        errorRequestId: action.requestId,
        errorAction: action.action ?? null,
        status: "error",
      };
    case "ANALYSIS_STARTED":
      return {
        ...state,
        busy: "analyzing",
        status: "analyzing",
        error: null,
        errorCode: undefined,
        errorRequestId: undefined,
        errorAction: null,
      };
    case "ANALYSIS_SUCCEEDED":
      return {
        ...state,
        busy: null,
        status: action.promptError ? "error" : "analyzed",
        phase: "result",
        dna: action.dna,
        intent: action.intent,
        shots: action.shots,
        panels: action.panels,
        layout: action.layout,
        quality: action.quality,
        prompt: action.prompt,
        negative: action.negative,
        versions: action.versions,
        activeVersionId: action.activeVersionId,
        error: action.promptError?.message ?? null,
        errorCode: action.promptError?.code,
        errorAction: action.promptError?.retry ?? null,
      };
    case "ANALYSIS_FAILED":
      return {
        ...state,
        busy: null,
        status: "error",
        error: action.error,
        errorCode: action.code,
        errorRequestId: action.requestId,
        errorAction: null,
      };
    case "BUSY":
      return { ...state, busy: action.busy };
    case "PROMPT_REGENERATED":
      return {
        ...state,
        busy: null,
        status: "analyzed",
        prompt: action.prompt,
        negative: action.negative,
        quality: action.quality,
        versions: [...state.versions, action.version],
        activeVersionId: action.version.id,
        error: null,
        errorAction: null,
      };
    case "PROMPT_REFINED":
      return {
        ...state,
        busy: null,
        status: "analyzed",
        prompt: action.prompt,
        negative: action.negative,
        quality: action.quality,
        versions: [...state.versions, action.version],
        activeVersionId: action.version.id,
      };
    case "PROMPT_EDITED":
      return {
        ...state,
        prompt: action.prompt,
        versions: [...state.versions, action.version],
        activeVersionId: action.version.id,
      };
    case "PROMPT_VALIDATED":
      return { ...state, busy: null, quality: action.quality };
    case "VERSION_RESTORED":
      return {
        ...state,
        prompt: action.version.prompt,
        negative: action.version.negative,
        activeVersionId: action.version.id,
      };
    case "HISTORY_RESTORED":
      return {
        ...state,
        image: {
          dataUrl: action.item.thumbnail,
          width: 0,
          height: 0,
          name: action.item.name,
          size: 0,
        },
        mode: action.item.mode,
        targetModel: action.item.targetModel,
        instruction: action.item.instruction ?? "",
        dna: action.item.dna,
        intent: action.item.intent ?? null,
        shots: action.item.shots ?? [],
        panels: action.item.panels ?? [],
        layout: action.item.layout ?? null,
        quality: action.item.quality ?? null,
        prompt: action.item.prompt,
        negative: action.item.negative,
        versions: action.item.versions?.length ? action.item.versions : [action.version],
        activeVersionId: action.version.id,
        phase: "result",
        status: "analyzed",
        busy: null,
        error: null,
        errorAction: null,
      };
    default:
      return state;
  }
}

export interface UseAnalysisOptions {
  models: TargetModel[];
  onHistorySaved: (items: HistoryItem[]) => void;
}

export function useAnalysis({ models, onHistorySaved }: UseAnalysisOptions) {
  const [state, dispatch] = useReducer(analysisReducer, initialAnalysisState);
  const analyzeCtrl = useRef<AbortController | null>(null);
  const generateCtrl = useRef<AbortController | null>(null);
  const refineCtrl = useRef<AbortController | null>(null);
  const fetchCtrl = useRef<AbortController | null>(null);
  const validateCtrl = useRef<AbortController | null>(null);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    return () => {
      analyzeCtrl.current?.abort();
      generateCtrl.current?.abort();
      refineCtrl.current?.abort();
      fetchCtrl.current?.abort();
      validateCtrl.current?.abort();
    };
  }, []);

  const modelName = useCallback(
    (id: string) => models.find((m) => m.id === id)?.name ?? id,
    [models]
  );

  const supportsNegative = models.find((m) => m.id === state.targetModel)?.supports_negative ?? true;

  const persistHistory = useCallback(
    async (args: {
      dna: VisualDNA;
      creativeIntent: CreativeIntent | null | undefined;
      prompt: string;
      negative: string | null;
      image: UploadedImage;
      mode: Mode;
      targetModel: string;
      instruction: string;
      quality: PromptQuality | null;
      shots: ShotResult[];
      layout: string | null;
      panels: PanelInfo[];
      versions?: PromptVersion[];
    }) => {
      const item: HistoryItem = {
        historySchemaVersion: HISTORY_SCHEMA_VERSION,
        id: newId(),
        ts: Date.now(),
        mode: args.mode,
        targetModel: args.targetModel,
        name: args.image.name,
        thumbnail: await thumbnailOf(args.image.dataUrl),
        dna: args.dna,
        intent: args.creativeIntent ?? undefined,
        prompt: args.prompt,
        negative: args.negative,
        instruction: args.mode === "modify" ? args.instruction.trim() : undefined,
        quality: args.quality,
        shots: args.shots,
        layout: args.layout,
        panels: args.panels,
        versions: args.versions,
      };
      onHistorySaved(saveHistoryItem(item));
    },
    [onHistorySaved]
  );

  const regeneratePrompt = useCallback(
    async (args: {
      dna: VisualDNA;
      creativeIntent: CreativeIntent | null | undefined;
      selectedModel: string;
      mode: Mode;
      instruction: string;
    }) => {
      generateCtrl.current?.abort();
      const ctrl = new AbortController();
      generateCtrl.current = ctrl;
      dispatch({ type: "BUSY", busy: "regenerating" });
      dispatch({ type: "CLEAR_ERROR" });
      try {
        const data = await api.generatePrompt(
          {
            visual_dna: args.dna,
            creative_intent: args.creativeIntent ?? undefined,
            mode: args.mode,
            target_model: args.selectedModel,
            instruction: args.mode === "modify" ? args.instruction.trim() : undefined,
          },
          { signal: ctrl.signal }
        );
        const version = newVersion("regenerate", data.prompt, data.negative_prompt, {
          targetModel: modelName(args.selectedModel),
        });
        dispatch({
          type: "PROMPT_REGENERATED",
          prompt: data.prompt,
          negative: data.negative_prompt,
          quality: data.quality ?? null,
          version,
        });
      } catch (e) {
        if (isAbortError(e)) return;
        dispatch({
          type: "SET_ERROR",
          error: friendlyMessage(e),
          code: errorCodeOf(e),
          requestId: requestIdOf(e),
        });
        dispatch({ type: "BUSY", busy: null });
      }
    },
    [modelName]
  );

  const analyze = useCallback(async () => {
    const s = stateRef.current;
    if (!s.image) return;
    analyzeCtrl.current?.abort();
    const ctrl = new AbortController();
    analyzeCtrl.current = ctrl;
    dispatch({ type: "ANALYSIS_STARTED" });
    try {
      const data = await api.analyze(
        {
          image: s.image.dataUrl,
          mode: s.mode,
          target_model: s.targetModel,
          instruction: s.mode === "modify" ? s.instruction.trim() : undefined,
          generate_prompt: true,
        },
        { signal: ctrl.signal }
      );
      const dna = data.visual_dna;
      const intent = data.creative_intent;
      const shots = data.shots ?? [];
      const panels = data.panels ?? [];
      const layout = data.layout_description ?? null;
      const quality = data.prompt_quality ?? null;
      const prompt = data.prompt ?? "";
      const negative = data.negative_prompt;
      const version = newVersion("analyze", prompt, negative, {
        targetModel: modelName(s.targetModel),
      });

      let promptError: { message: string; code: string; retry: BannerAction } | null = null;
      if (data.prompt_error) {
        promptError = {
          message: `The image was analyzed, but prompt generation failed: ${data.prompt_error.message}`,
          code: data.prompt_error.code,
          retry: {
            label: "Retry prompt",
            run: () => {
              void regeneratePrompt({
                dna,
                creativeIntent: intent,
                selectedModel: stateRef.current.targetModel,
                mode: stateRef.current.mode,
                instruction: stateRef.current.instruction,
              });
            },
          },
        };
      }

      dispatch({
        type: "ANALYSIS_SUCCEEDED",
        dna,
        intent,
        shots,
        panels,
        layout,
        quality,
        prompt,
        negative,
        versions: promptError ? [] : [version],
        activeVersionId: promptError ? null : version.id,
        promptError,
      });

      if (!data.prompt_error && s.image) {
        await persistHistory({
          dna,
          creativeIntent: intent,
          prompt,
          negative,
          image: s.image,
          mode: s.mode,
          targetModel: s.targetModel,
          instruction: s.instruction,
          quality,
          shots,
          layout,
          panels,
          versions: [version],
        });
      }
    } catch (e) {
      if (isAbortError(e)) return;
      dispatch({
        type: "ANALYSIS_FAILED",
        error: friendlyMessage(e),
        code: errorCodeOf(e),
        requestId: requestIdOf(e),
      });
    }
  }, [modelName, persistHistory, regeneratePrompt]);

  const onModelChange = useCallback(
    (id: string) => {
      const s = stateRef.current;
      dispatch({ type: "MODEL_CHANGED", targetModel: id });
      if (s.dna && s.phase === "result") {
        void regeneratePrompt({
          dna: s.dna,
          creativeIntent: s.intent,
          selectedModel: id,
          mode: s.mode,
          instruction: s.instruction,
        });
      }
    },
    [regeneratePrompt]
  );

  const refine = useCallback(async (text: string) => {
    const s = stateRef.current;
    if (!s.dna || !s.prompt) return;
    refineCtrl.current?.abort();
    const ctrl = new AbortController();
    refineCtrl.current = ctrl;
    dispatch({ type: "BUSY", busy: "refining" });
    dispatch({ type: "CLEAR_ERROR" });
    try {
      const data = await api.refinePrompt(
        {
          visual_dna: s.dna,
          creative_intent: s.intent ?? undefined,
          current_prompt: s.prompt,
          instruction: text,
          mode: s.mode,
          target_model: s.targetModel,
        },
        { signal: ctrl.signal }
      );
      const version = newVersion("refine", data.prompt, data.negative_prompt, {
        instruction: text,
        keep: data.keep,
        change: data.change,
      });
      dispatch({
        type: "PROMPT_REFINED",
        prompt: data.prompt,
        negative: data.negative_prompt,
        quality: data.quality ?? null,
        version,
      });
    } catch (e) {
      if (isAbortError(e)) return;
      dispatch({
        type: "SET_ERROR",
        error: friendlyMessage(e),
        code: errorCodeOf(e),
        requestId: requestIdOf(e),
      });
      dispatch({ type: "BUSY", busy: null });
    }
  }, []);

  const applyEdit = useCallback(async (newPrompt: string) => {
    const s = stateRef.current;
    const version = newVersion("edit", newPrompt, s.negative);
    dispatch({ type: "PROMPT_EDITED", prompt: newPrompt, version });
    validateCtrl.current?.abort();
    const ctrl = new AbortController();
    validateCtrl.current = ctrl;
    dispatch({ type: "BUSY", busy: "validating" });
    try {
      const data = await api.validatePrompt(
        { prompt: newPrompt, model: s.targetModel, visual_dna: s.dna ?? undefined },
        { signal: ctrl.signal }
      );
      dispatch({ type: "PROMPT_VALIDATED", quality: data.quality ?? null });
    } catch (e) {
      if (isAbortError(e)) return;
      dispatch({ type: "BUSY", busy: null });
      // Soft-fail: edit is kept; validation is best-effort.
      if (!(e instanceof AppError)) {
        dispatch({
          type: "SET_ERROR",
          error: friendlyMessage(e),
          code: errorCodeOf(e),
          requestId: requestIdOf(e),
        });
      }
    }
  }, []);

  const fetchUrl = useCallback(async (url: string, adopt: (img: UploadedImage) => void, name: string) => {
    fetchCtrl.current?.abort();
    const ctrl = new AbortController();
    fetchCtrl.current = ctrl;
    dispatch({ type: "URL_BUSY", busy: true });
    dispatch({ type: "CLEAR_ERROR" });
    try {
      const fetched = await api.fetchImage(url, { signal: ctrl.signal });
      adopt({
        dataUrl: fetched.image,
        width: fetched.width,
        height: fetched.height,
        name,
        size: 0,
      });
    } catch (e) {
      if (isAbortError(e)) return;
      dispatch({
        type: "SET_ERROR",
        error: friendlyMessage(e),
        code: errorCodeOf(e),
        requestId: requestIdOf(e),
      });
    } finally {
      dispatch({ type: "URL_BUSY", busy: false });
    }
  }, []);

  return {
    state,
    dispatch,
    supportsNegative,
    analyze,
    regeneratePrompt,
    onModelChange,
    refine,
    applyEdit,
    fetchUrl,
    modelName,
  };
}
