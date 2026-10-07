import { useState } from "react";
import type { RefineEntry } from "../types";

interface Props {
  busy: boolean;
  log: RefineEntry[];
  onRefine: (instruction: string) => void;
}

export default function RefinePanel({ busy, log, onRefine }: Props) {
  const [text, setText] = useState("");

  function submit() {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    onRefine(trimmed);
    setText("");
  }

  return (
    <section className="card refine">
      <h2>Refine Prompt</h2>
      <textarea
        value={text}
        rows={3}
        placeholder="Tell the AI what to change — e.g. “Keep everything but change the lighting to sunset.”"
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
        }}
      />
      <div className="refine-row">
        <span className="hint">Ctrl/⌘ + Enter to apply</span>
        <button className="btn primary" disabled={busy || !text.trim()} onClick={submit}>
          {busy ? "Revising…" : "Apply Changes"}
        </button>
      </div>
      {log.length > 0 && (
        <div className="refine-log">
          {log
            .slice()
            .reverse()
            .map((entry, i) => (
              <div key={i} className="refine-entry">
                <div className="refine-instr">“{entry.instruction}”</div>
                <div className="chips">
                  {entry.change.map((c, j) => (
                    <span key={`c${j}`} className="chip change">
                      changed: {c}
                    </span>
                  ))}
                  {entry.keep.map((k, j) => (
                    <span key={`k${j}`} className="chip keep">
                      kept: {k}
                    </span>
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}
    </section>
  );
}
