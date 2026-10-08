import { CircleCheck, TriangleAlert } from "lucide-react";
import type { PromptQuality } from "../types";
import { CardHead } from "./ui";

export default function QualityCard({ quality }: { quality: PromptQuality | null }) {
  if (
    !quality ||
    (quality.warnings.length === 0 &&
      quality.strengths.length === 0 &&
      quality.visual_coverage_score == null)
  ) {
    return null;
  }
  const tone = quality.score >= 85 ? "good" : quality.score >= 60 ? "ok" : "poor";
  return (
    <section className="card quality-card">
      <CardHead label="Prompt quality" />
      <div className="quality-head">
        <span className={`quality-score ${tone}`}>{quality.score}</span>
        <span className={`quality-bar ${tone}`} aria-hidden="true">
          <span className="quality-bar-fill" style={{ width: `${quality.score}%` }} />
        </span>
      </div>
      {typeof quality.visual_coverage_score === "number" && (
        <p className="quality-coverage">
          Visual coverage {quality.visual_coverage_score}
        </p>
      )}
      {quality.warnings.length > 0 && (
        <ul className="quality-list warnings">
          {quality.warnings.map((w, i) => (
            <li key={i}>
              <TriangleAlert />
              {w}
            </li>
          ))}
        </ul>
      )}
      {quality.strengths.length > 0 && (
        <ul className="quality-list strengths">
          {quality.strengths.map((s, i) => (
            <li key={i}>
              <CircleCheck />
              {s}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
