import { useState } from "react";

export default function NegativeCard({ negative }: { negative: string }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(negative);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <section className="card negative-card">
      <div className="card-head">
        <h2>Negative Prompt</h2>
        <button className="btn ghost small" onClick={() => void onCopy()}>
          {copied ? "Copied ✓" : "Copy"}
        </button>
      </div>
      <p className="negative-text">{negative}</p>
    </section>
  );
}
