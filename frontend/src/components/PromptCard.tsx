import { useState } from "react";
import { Check, Copy, PenLine, RefreshCw } from "lucide-react";
import { CardHead } from "./ui";

interface Props {
  prompt: string;
  modelName: string;
  busy: boolean;
  charLimit?: number | null;
  label?: string;
  onRegenerate: () => void;
  onEdit: (newPrompt: string) => void;
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
}

export default function PromptCard({
  prompt,
  modelName,
  busy,
  charLimit,
  label = "Prompt",
  onRegenerate,
  onEdit,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  async function onCopy() {
    if (!prompt) return;
    await copyText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function startEdit() {
    setDraft(prompt);
    setEditing(true);
  }

  function saveEdit() {
    const trimmed = draft.trim();
    setEditing(false);
    if (trimmed && trimmed !== prompt) onEdit(trimmed);
  }

  const overLimit = charLimit !== null && charLimit !== undefined && prompt.length > charLimit;

  return (
    <section className="card prompt-card">
      <CardHead
        label={label}
        actions={
          editing ? (
            <>
              <button className="btn ghost small" onClick={() => setEditing(false)}>
                Cancel
              </button>
              <button className="btn primary small" onClick={saveEdit} disabled={!draft.trim()}>
                Save
              </button>
            </>
          ) : (
            <>
              <button className="btn ghost small" onClick={startEdit} disabled={busy || !prompt}>
                <PenLine className="btn-icon" />
                Edit
              </button>
              <button className="btn ghost small" onClick={onRegenerate} disabled={busy}>
                <RefreshCw className="btn-icon" />
                Regenerate
              </button>
              <button className="btn primary small" onClick={() => void onCopy()} disabled={busy || !prompt}>
                {copied ? <Check className="btn-icon" /> : <Copy className="btn-icon" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </>
          )
        }
      />

      {editing ? (
        <div className="prompt-edit">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={8}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) saveEdit();
              if (e.key === "Escape") setEditing(false);
            }}
          />
          <div className="refine-row">
            <span className="hint mono">{draft.trim().length} characters · Esc cancels · Ctrl/⌘+Enter saves</span>
          </div>
        </div>
      ) : prompt ? (
        <p className="prompt-text">{prompt}</p>
      ) : (
        <p className="empty-note">No prompt yet: regenerate to write one.</p>
      )}

      {!editing && (
        <div className="prompt-foot">
          <span>
            written for <b>{modelName}</b>
          </span>
          <span className="mono">{prompt.length} chars</span>
          {overLimit && <span className="char-warn">over the ~{charLimit}-character comfort zone for {modelName}</span>}
        </div>
      )}
    </section>
  );
}
