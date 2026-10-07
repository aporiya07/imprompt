import { useCallback, useEffect, useState } from "react";
import { Moon, ScanSearch, Sun } from "lucide-react";
import CreativeDirectionCard from "./components/CreativeDirectionCard";
import DnaViewer from "./components/DnaViewer";
import Dropzone from "./components/Dropzone";
import ErrorBanner from "./components/ErrorBanner";
import HistoryPanel from "./components/HistoryPanel";
import NegativeCard from "./components/NegativeCard";
import PromptCard from "./components/PromptCard";
import QualityCard from "./components/QualityCard";
import ReferencePanel from "./components/ReferencePanel";
import RefinePanel from "./components/RefinePanel";
import ShotsList from "./components/ShotsList";
import VersionList from "./components/VersionList";
import WorkingCard from "./components/WorkingCard";
import { api, DEFAULT_MODELS } from "./services/api";
import { errorCodeOf, friendlyMessage, requestIdOf } from "./services/errors";
import type {
  CreativeIntent,
  HistoryItem,
  Mode,
  PromptQuality,
  PromptVersion,
  PromptVersionSource,
  ShotResult,
  TargetModel,
  UploadedImage,
  VisualDNA,
} from "./types";
import { MODE_LABELS } from "./types";
import { clearHistory, deleteHistoryItem, loadHistory, saveHistoryItem } from "./utils/history";
import { loadImageFile, thumbnailOf } from "./utils/image";

type Busy = "analyzing" | "regenerating" | "refining" | null;

interface BannerAction {
  label: string;
  run: () => void;
}

function newVersion(
  source: PromptVersionSource,
  prompt: string,
  negative: string | null,
  extra: Partial<PromptVersion> = {}
): PromptVersion {
  return { id: crypto.randomUUID(), source, ts: Date.now(), prompt, negative, ...extra };
}

export default function App() {
  const [theme, setTheme] = useState<"dark" | "light">(
    () => (localStorage.getItem("ipa.theme") as "dark" | "light") ?? "dark"
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("ipa.theme", theme);
  }, [theme]);

  const [image, setImage] = useState<UploadedImage | null>(null);
  const [mode, setMode] = useState<Mode>("recreate");
  const [models, setModels] = useState<TargetModel[]>(DEFAULT_MODELS);
  const [targetModel, setTargetModel] = useState("generic");
  const [instruction, setInstruction] = useState("");
  const [phase, setPhase] = useState<"setup" | "result">("setup");
  const [busy, setBusy] = useState<Busy>(null);
  const [urlBusy, setUrlBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | undefined>(undefined);
  const [errorRequestId, setErrorRequestId] = useState<string | undefined>(undefined);
  const [errorAction, setErrorAction] = useState<BannerAction | null>(null);
  const [dna, setDna] = useState<VisualDNA | null>(null);
  const [intent, setIntent] = useState<CreativeIntent | null>(null);
  const [shots, setShots] = useState<ShotResult[]>([]);
  const [layout, setLayout] = useState<string | null>(null);
  const [quality, setQuality] = useState<PromptQuality | null>(null);
  const [prompt, setPrompt] = useState("");
  const [negative, setNegative] = useState<string | null>(null);
  const [supportsNegative, setSupportsNegative] = useState(true);
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [activeVersionId, setActiveVersionId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>(() => loadHistory());

  useEffect(() => {
    api.models().then(setModels);
  }, []);

  const currentModel = models.find((m) => m.id === targetModel);
  const currentModelName = currentModel?.name ?? targetModel;
  const charLimit = currentModel?.soft_char_limit ?? null;

  function reportError(e: unknown) {
    setError(friendlyMessage(e));
    setErrorCode(errorCodeOf(e));
    setErrorRequestId(requestIdOf(e));
    setErrorAction(null);
  }

  function clearError() {
    setError(null);
    setErrorCode(undefined);
    setErrorRequestId(undefined);
    setErrorAction(null);
  }

  function adoptImage(img: UploadedImage) {
    setImage(img);
    setDna(null);
    setIntent(null);
    setShots([]);
    setLayout(null);
    setQuality(null);
    setPrompt("");
    setNegative(null);
    setVersions([]);
    setActiveVersionId(null);
    setPhase("setup");
  }

  async function onFile(file: File) {
    clearError();
    try {
      adoptImage(await loadImageFile(file));
    } catch (e) {
      reportError(e);
    }
  }

  async function onFetchUrl(url: string) {
    setUrlBusy(true);
    clearError();
    try {
      const fetched = await api.fetchImage(url);
      const name = decodeURIComponent(url.split("/").pop()?.split("?")[0] || "image-from-url").slice(0, 80);
      adoptImage({ dataUrl: fetched.image, width: fetched.width, height: fetched.height, name, size: 0 });
    } catch (e) {
      reportError(e);
    } finally {
      setUrlBusy(false);
    }
  }

  function reset() {
    setImage(null);
    adoptImage({
      dataUrl: "",
      width: 0,
      height: 0,
      name: "",
      size: 0,
    });
    setImage(null);
    clearError();
    setPhase("setup");
  }

  async function persistHistory(d: VisualDNA, p: string, neg: string | null) {
    if (!image) return;
    const item: HistoryItem = {
      id: crypto.randomUUID(),
      ts: Date.now(),
      mode,
      targetModel,
      name: image.name,
      thumbnail: await thumbnailOf(image.dataUrl),
      dna: d,
      intent: intent ?? undefined,
      prompt: p,
      negative: neg,
      instruction: mode === "modify" ? instruction.trim() : undefined,
    };
    setHistory(saveHistoryItem(item));
  }

  const analyze = useCallback(async () => {
    if (!image) return;
    setBusy("analyzing");
    clearError();
    try {
      const data = await api.analyze({
        image: image.dataUrl,
        mode,
        target_model: targetModel,
        instruction: mode === "modify" ? instruction.trim() : undefined,
        generate_prompt: true,
      });
      setDna(data.visual_dna);
      setIntent(data.creative_intent);
      setShots(data.shots ?? []);
      setLayout(data.layout_description ?? null);
      setQuality(data.prompt_quality ?? null);
      setPrompt(data.prompt ?? "");
      setNegative(data.negative_prompt);
      setPhase("result");
      if (data.prompt_error) {
        setError(`The image was analyzed, but prompt generation failed: ${data.prompt_error.message}`);
        setErrorCode(data.prompt_error.code);
        setErrorAction({ label: "Retry prompt", run: () => void regenerate() });
      } else {
        const v = newVersion("analyze", data.prompt ?? "", data.negative_prompt, { targetModel: currentModelName });
        setVersions([v]);
        setActiveVersionId(v.id);
        await persistHistory(data.visual_dna, data.prompt ?? "", data.negative_prompt);
      }
    } catch (e) {
      reportError(e);
    } finally {
      setBusy(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image, mode, targetModel, instruction, currentModelName, intent]);

  async function regenerate(modelId?: string) {
    if (!dna) return;
    const target = modelId ?? targetModel;
    setBusy("regenerating");
    clearError();
    try {
      const data = await api.generatePrompt({
        visual_dna: dna,
        creative_intent: intent ?? undefined,
        mode,
        target_model: target,
        instruction: mode === "modify" ? instruction.trim() : undefined,
      });
      setPrompt(data.prompt);
      setNegative(data.negative_prompt);
      setQuality(data.quality ?? null);
      const v = newVersion("regenerate", data.prompt, data.negative_prompt, {
        targetModel: models.find((m) => m.id === target)?.name ?? target,
      });
      setVersions((vs) => [...vs, v]);
      setActiveVersionId(v.id);
    } catch (e) {
      reportError(e);
    } finally {
      setBusy(null);
    }
  }

  function onModelChange(id: string) {
    setTargetModel(id);
    const m = models.find((m) => m.id === id);
    setSupportsNegative(m?.supports_negative ?? true);
    if (dna && phase === "result") void regenerate(id);
  }

  async function refine(text: string) {
    if (!dna || !prompt) return;
    setBusy("refining");
    clearError();
    try {
      const data = await api.refinePrompt({
        visual_dna: dna,
        creative_intent: intent ?? undefined,
        current_prompt: prompt,
        instruction: text,
        mode,
        target_model: targetModel,
      });
      setPrompt(data.prompt);
      setNegative(data.negative_prompt);
      setQuality(data.quality ?? null);
      const v = newVersion("refine", data.prompt, data.negative_prompt, {
        instruction: text,
        keep: data.keep,
        change: data.change,
      });
      setVersions((vs) => [...vs, v]);
      setActiveVersionId(v.id);
    } catch (e) {
      reportError(e);
    } finally {
      setBusy(null);
    }
  }

  function applyEdit(newPrompt: string) {
    const v = newVersion("edit", newPrompt, negative);
    setPrompt(newPrompt);
    setVersions((vs) => [...vs, v]);
    setActiveVersionId(v.id);
  }

  function restoreVersion(v: PromptVersion) {
    setPrompt(v.prompt);
    setNegative(v.negative);
    setActiveVersionId(v.id);
  }

  function restore(item: HistoryItem) {
    setImage({ dataUrl: item.thumbnail, width: 0, height: 0, name: item.name, size: 0 });
    setMode(item.mode);
    setTargetModel(item.targetModel);
    setDna(item.dna);
    setIntent(item.intent ?? null);
    setShots([]);
    setLayout(null);
    setQuality(null);
    setPrompt(item.prompt);
    setNegative(item.negative);
    setSupportsNegative(models.find((m) => m.id === item.targetModel)?.supports_negative ?? true);
    if (item.instruction) setInstruction(item.instruction);
    const v = newVersion("analyze", item.prompt, item.negative, { targetModel: item.targetModel });
    setVersions([v]);
    setActiveVersionId(v.id);
    setPhase("result");
    clearError();
  }

  const refineEntries = versions
    .filter((v) => v.source === "refine")
    .map((v) => ({ instruction: v.instruction ?? "", keep: v.keep ?? [], change: v.change ?? [] }));

  const isCollage = shots.length > 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          VISURA
          <span className="brand-descriptor">visual reverse engineering</span>
        </div>
        <div className="topbar-actions">
          {phase === "result" && (
            <button className="btn ghost small" onClick={reset}>
              New image
            </button>
          )}
          <button
            className="btn ghost small icon-btn"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          >
            {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </header>

      {error && (
        <ErrorBanner
          message={error}
          onDismiss={clearError}
          actionLabel={errorAction?.label}
          onAction={errorAction ? () => errorAction.run() : undefined}
          code={errorCode}
          requestId={errorRequestId}
        />
      )}

      {phase === "setup" ? (
        <main className="setup">
          <h1 className="hero-title">
            Reverse-engineer the visual logic of any reference <em>into a generation-ready prompt</em>.
          </h1>
          <p className="hero-sub">
            Subjects, composition, lighting, color and mood, extracted as structured Visual DNA and rebuilt
            for your target model.
          </p>

          <Dropzone
            image={image}
            onFile={(f) => void onFile(f)}
            onFetchUrl={(u) => void onFetchUrl(u)}
            disabled={busy !== null || urlBusy}
            fetchingUrl={urlBusy}
          />

          <div className="controls card">
            <div className="controls-grid">
              <label className="field">
                <span className="field-label">Target model</span>
                <select value={targetModel} onChange={(e) => onModelChange(e.target.value)}>
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Reference intent</span>
                <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
                  {(Object.keys(MODE_LABELS) as Mode[]).map((m) => (
                    <option key={m} value={m}>
                      {MODE_LABELS[m]}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {mode === "modify" && (
              <textarea
                className="instruction"
                rows={2}
                placeholder="Describe the change, e.g. “Replace the background with a futuristic laboratory.”"
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
              />
            )}
          </div>

          <button
            className="btn primary big"
            disabled={!image || busy !== null || (mode === "modify" && !instruction.trim())}
            onClick={() => void analyze()}
          >
            <ScanSearch className="btn-icon" />
            {busy === "analyzing" ? "Analyzing…" : "Analyze reference"}
          </button>

          {busy === "analyzing" && <WorkingCard />}

          <HistoryPanel
            items={history}
            onRestore={restore}
            onDelete={(id) => setHistory(deleteHistoryItem(id))}
            onClear={() => setHistory(clearHistory())}
          />
        </main>
      ) : (
        <main className="result">
          <div className="result-grid">
            <aside className="result-left">
              <ReferencePanel image={image} onFile={(f) => void onFile(f)} disabled={busy !== null} />
              {dna && <DnaViewer dna={dna} />}
            </aside>
            <section className="result-right">
              {busy === "regenerating" && (
                <WorkingCard label={`Adapting the prompt for ${currentModelName}`} />
              )}
              <PromptCard
                prompt={prompt}
                modelName={currentModelName}
                busy={busy !== null}
                charLimit={charLimit}
                label={isCollage ? "Master creative direction" : "Prompt"}
                onRegenerate={() => void regenerate()}
                onEdit={applyEdit}
              />
              <QualityCard quality={quality} />
              {supportsNegative && negative && <NegativeCard negative={negative} />}
              {!supportsNegative && negative && (
                <p className="hint negative-note">
                  Note: {currentModelName} has no separate negative prompt; avoidances are already phrased inside
                  the prompt.
                </p>
              )}
              <CreativeDirectionCard intent={intent} />
              <ShotsList shots={shots} layout={layout} />
              <RefinePanel busy={busy === "refining"} log={refineEntries} onRefine={(t) => void refine(t)} />
              <VersionList versions={versions} activeId={activeVersionId} onRestore={restoreVersion} />
              <HistoryPanel
                items={history}
                onRestore={restore}
                onDelete={(id) => setHistory(deleteHistoryItem(id))}
                onClear={() => setHistory(clearHistory())}
              />
            </section>
          </div>
        </main>
      )}

      <footer className="footer">VISURA · v0.2</footer>
    </div>
  );
}
