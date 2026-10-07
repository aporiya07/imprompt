import type { PromptVersion, PromptVersionSource } from "../types";

interface Props {
  versions: PromptVersion[];
  activeId: string | null;
  onRestore: (version: PromptVersion) => void;
}

const SOURCE_LABELS: Record<PromptVersionSource, string> = {
  analyze: "Analyzed",
  regenerate: "Regenerated",
  refine: "Refined",
  edit: "Edited by hand",
};

function describe(v: PromptVersion): string {
  if (v.source === "regenerate" && v.targetModel) return `for ${v.targetModel}`;
  if (v.source === "refine" && v.instruction) return `“${v.instruction.slice(0, 70)}”`;
  if (v.source === "analyze" && v.targetModel) return `with ${v.targetModel}`;
  return "";
}

export default function VersionList({ versions, activeId, onRestore }: Props) {
  if (versions.length === 0) return null;
  return (
    <section className="card version-card">
      <div className="card-head">
        <h2>Prompt Versions</h2>
        <span className="hint">click to restore</span>
      </div>
      <div className="version-list">
        {versions
          .slice()
          .reverse()
          .map((v) => (
            <div
              key={v.id}
              className={`version-row${v.id === activeId ? " active" : ""}`}
              onClick={() => onRestore(v)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter") onRestore(v);
              }}
            >
              <div className="version-top">
                <span className="version-label">{SOURCE_LABELS[v.source]}</span>
                <span className="version-when">{describe(v)}</span>
                <span className="version-time">{new Date(v.ts).toLocaleTimeString()}</span>
              </div>
              <div className="version-snippet">{v.prompt.slice(0, 90)}{v.prompt.length > 90 ? "…" : ""}</div>
            </div>
          ))}
      </div>
    </section>
  );
}
