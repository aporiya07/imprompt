import { useState } from "react";
import type { ShotResult } from "../types";

interface Props {
  shots: ShotResult[];
  layout: string | null;
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* ignore */
  }
}

export default function ShotsList({ shots, layout }: Props) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  if (shots.length === 0) return null;

  async function onCopy(shot: ShotResult) {
    await copyText(shot.prompt);
    setCopiedIndex(shot.index);
    setTimeout(() => setCopiedIndex(null), 1500);
  }

  return (
    <section className="card shots-card">
      <div className="card-head">
        <h2>Shot List</h2>
        <span className="hint">{layout ? `Detected: ${layout}` : `${shots.length} shots`}</span>
      </div>
      <div className="shots-list">
        {shots.map((shot) => (
          <details key={shot.index} className="shot-item">
            <summary>
              <span className="shot-index">Shot {String(shot.index).padStart(2, "0")}</span>
              <span className="shot-title">{shot.title || "—"}</span>
              {shot.quality && (
                <span className={`shot-score ${shot.quality.score >= 85 ? "good" : shot.quality.score >= 60 ? "ok" : "poor"}`}>
                  {shot.quality.score}
                </span>
              )}
            </summary>
            <div className="shot-body">
              <p className="prompt-text">{shot.prompt}</p>
              {shot.negative_prompt && <p className="negative-text">negative: {shot.negative_prompt}</p>}
              {shot.quality && shot.quality.warnings.length > 0 && (
                <ul className="quality-list warnings">
                  {shot.quality.warnings.map((w, i) => (
                    <li key={i}>⚠ {w}</li>
                  ))}
                </ul>
              )}
              <div className="refine-row">
                <span className="hint">
                  {shot.prompt.length} characters
                </span>
                <button className="btn primary small" onClick={() => void onCopy(shot)}>
                  {copiedIndex === shot.index ? "Copied ✓" : "Copy Prompt"}
                </button>
              </div>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
