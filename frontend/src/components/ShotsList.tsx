import { useEffect, useState } from "react";
import { Check, Copy, TriangleAlert } from "lucide-react";
import type { PanelInfo, ShotResult } from "../types";
import { cropPanelThumb } from "../utils/image";
import { CardHead } from "./ui";

interface Props {
  shots: ShotResult[];
  layout: string | null;
  referenceUrl?: string | null;
  panels?: PanelInfo[];
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* ignore */
  }
}

export default function ShotsList({ shots, layout, referenceUrl = null, panels = [] }: Props) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [thumbs, setThumbs] = useState<Record<number, string>>({});

  useEffect(() => {
    let cancelled = false;
    if (!referenceUrl || panels.length === 0) {
      queueMicrotask(() => {
        if (!cancelled) setThumbs({});
      });
      return () => {
        cancelled = true;
      };
    }
    void (async () => {
      const next: Record<number, string> = {};
      await Promise.all(
        panels.map(async (panel) => {
          if (!panel.bounds) return;
          const thumb = await cropPanelThumb(referenceUrl, panel.bounds);
          if (thumb) next[panel.index] = thumb;
        })
      );
      if (!cancelled) setThumbs(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [referenceUrl, panels]);

  if (shots.length === 0) return null;

  async function onCopy(shot: ShotResult) {
    await copyText(shot.prompt);
    setCopiedIndex(shot.index);
    setTimeout(() => setCopiedIndex(null), 1500);
  }

  return (
    <section className="card shots-card">
      <CardHead label="Shot list" hint={layout ? layout : `${shots.length} panels`} />
      <div className="shots-grid">
        {shots.map((shot) => (
          <details key={shot.index} className="shot-item">
            <summary>
              <span className="shot-thumb">
                {thumbs[shot.index] ? (
                  <img src={thumbs[shot.index]} alt="" />
                ) : (
                  <span className="shot-num">{String(shot.index).padStart(2, "0")}</span>
                )}
              </span>
              <span className="shot-meta">
                <span className="shot-index">Shot {String(shot.index).padStart(2, "0")}</span>
                <span className="shot-title">{shot.title || "Untitled panel"}</span>
                {shot.quality && (
                  <span
                    className={`shot-score ${shot.quality.score >= 85 ? "good" : shot.quality.score >= 60 ? "ok" : "poor"}`}
                  >
                    quality {shot.quality.score}
                  </span>
                )}
              </span>
            </summary>
            <div className="shot-body">
              <p className="prompt-text">{shot.prompt}</p>
              {shot.negative_prompt && <p className="negative-text">negative: {shot.negative_prompt}</p>}
              {shot.quality && shot.quality.warnings.length > 0 && (
                <ul className="quality-list warnings">
                  {shot.quality.warnings.map((w, i) => (
                    <li key={i}>
                      <TriangleAlert />
                      {w}
                    </li>
                  ))}
                </ul>
              )}
              <div className="refine-row">
                <span className="hint mono">{shot.prompt.length} chars</span>
                <button className="btn primary small" onClick={() => void onCopy(shot)}>
                  {copiedIndex === shot.index ? <Check className="btn-icon" /> : <Copy className="btn-icon" />}
                  {copiedIndex === shot.index ? "Copied" : "Copy prompt"}
                </button>
              </div>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
