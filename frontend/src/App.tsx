import { useEffect, useState } from "react";
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
import { useAnalysis } from "./hooks/useAnalysis";
import { api, DEFAULT_MODELS } from "./services/api";
import type { HistoryItem, Mode, PromptVersion, TargetModel, UploadedImage } from "./types";
import { MODE_LABELS } from "./types";
import { APP_VERSION } from "./version";
import { safeFilenameFromUrl } from "./utils/filename";
import { clearHistory, deleteHistoryItem, loadHistory } from "./utils/history";
import { loadImageFile } from "./utils/image";
import { persistTheme, resolveInitialTheme, type Theme } from "./utils/theme";
import { errorCodeOf, friendlyMessage, requestIdOf } from "./services/errors";

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme());
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    persistTheme(theme);
  }, [theme]);

  const [models, setModels] = useState<TargetModel[]>(DEFAULT_MODELS);
  const [history, setHistory] = useState<HistoryItem[]>(() => loadHistory());

  const {
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
  } = useAnalysis({ models, onHistorySaved: setHistory });

  useEffect(() => {
    api.models().then(setModels);
  }, []);

  const {
    image,
    mode,
    targetModel,
    instruction,
    phase,
    busy,
    urlBusy,
    error,
    errorCode,
    errorRequestId,
    errorAction,
    dna,
    intent,
    shots,
    panels,
    layout,
    quality,
    prompt,
    negative,
    versions,
    activeVersionId,
  } = state;

  const currentModelName = modelName(targetModel);
  const charLimit = models.find((m) => m.id === targetModel)?.soft_char_limit ?? null;

  function adoptImage(img: UploadedImage) {
    dispatch({ type: "IMAGE_ADOPTED", image: img });
  }

  async function onFile(file: File) {
    dispatch({ type: "CLEAR_ERROR" });
    try {
      adoptImage(await loadImageFile(file));
    } catch (e) {
      dispatch({
        type: "SET_ERROR",
        error: friendlyMessage(e),
        code: errorCodeOf(e),
        requestId: requestIdOf(e),
      });
    }
  }

  async function onFetchUrl(url: string) {
    await fetchUrl(url, adoptImage, safeFilenameFromUrl(url));
  }

  function reset() {
    dispatch({ type: "RESET" });
  }

  function restoreVersion(v: PromptVersion) {
    dispatch({ type: "VERSION_RESTORED", version: v });
  }

  function restore(item: HistoryItem) {
    const version: PromptVersion = item.versions?.[0] ?? {
      id: item.id,
      source: "analyze",
      ts: item.ts,
      prompt: item.prompt,
      negative: item.negative,
      targetModel: item.targetModel,
    };
    dispatch({ type: "HISTORY_RESTORED", item, version });
  }

  const refineEntries = versions
    .filter((v) => v.source === "refine")
    .map((v) => ({ instruction: v.instruction ?? "", keep: v.keep ?? [], change: v.change ?? [] }));

  const isCollage = shots.length > 0;
  const modelSelect = (
    <label className="field">
      <span className="field-label">Target model</span>
      <select value={targetModel} onChange={(e) => onModelChange(e.target.value)} disabled={busy !== null}>
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          ImPrompt
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
          onDismiss={() => dispatch({ type: "CLEAR_ERROR" })}
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
              {modelSelect}
              <label className="field">
                <span className="field-label">Reference intent</span>
                <select value={mode} onChange={(e) => dispatch({ type: "SET_MODE", mode: e.target.value as Mode })}>
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
                onChange={(e) => dispatch({ type: "SET_INSTRUCTION", instruction: e.target.value })}
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
              <div className="controls card result-model">
                <div className="controls-grid">{modelSelect}</div>
                <p className="hint">Changing the model rebuilds the prompt from existing Visual DNA. Vision is not re-run.</p>
              </div>
              {(busy === "regenerating" || busy === "validating") && (
                <WorkingCard
                  label={
                    busy === "validating"
                      ? "Revalidating edited prompt"
                      : `Adapting the prompt for ${currentModelName}`
                  }
                />
              )}
              <PromptCard
                prompt={prompt}
                modelName={currentModelName}
                busy={busy !== null}
                charLimit={charLimit}
                label={isCollage ? "Master creative direction" : "Prompt"}
                onRegenerate={() => {
                  if (!dna) return;
                  void regeneratePrompt({
                    dna,
                    creativeIntent: intent,
                    selectedModel: targetModel,
                    mode,
                    instruction,
                  });
                }}
                onEdit={(p) => void applyEdit(p)}
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
              <ShotsList
                shots={shots}
                layout={layout}
                referenceUrl={image?.dataUrl ?? null}
                panels={panels}
              />
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

      <footer className="footer">ImPrompt · v{APP_VERSION}</footer>
    </div>
  );
}
