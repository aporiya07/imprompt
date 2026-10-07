import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { CardHead } from "./ui";

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
      <CardHead
        label="Negative prompt"
        actions={
          <button className="btn ghost small" onClick={() => void onCopy()}>
            {copied ? <Check className="btn-icon" /> : <Copy className="btn-icon" />}
            {copied ? "Copied" : "Copy"}
          </button>
        }
      />
      <p className="negative-text">{negative}</p>
    </section>
  );
}
