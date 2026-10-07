import type { PromptQuality } from "../types";

export default function QualityCard({ quality }: { quality: PromptQuality | null }) {
  if (!quality || (quality.warnings.length === 0 && quality.strengths.length === 0)) return null;
  const tone = quality.score >= 85 ? "good" : quality.score >= 60 ? "ok" : "poor";
  return (
    <section className="card quality-card">
      <div className="quality-head">
        <span className={`quality-score ${tone}`}>{quality.score}</span>
        <span className="hint">deterministic prompt quality — warnings are advisory</span>
      </div>
      {quality.warnings.length > 0 && (
        <ul className="quality-list warnings">
          {quality.warnings.map((w, i) => (
            <li key={i}>⚠ {w}</li>
          ))}
        </ul>
      )}
      {quality.strengths.length > 0 && (
        <ul className="quality-list strengths">
          {quality.strengths.map((s, i) => (
            <li key={i}>✓ {s}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
