import { Fragment } from "react";
import type { CreativeIntent } from "../types";
import { CardHead } from "./ui";

function StrategyRows({ intent }: { intent: CreativeIntent }) {
  const rows: Array<[string, string]> = (
    [
      ["Aesthetic", intent.aesthetic_direction],
      ["Photography", intent.photographic_direction],
      ["Composition", intent.composition_strategy],
      ["Lighting", intent.lighting_strategy],
      ["Color", intent.color_strategy],
      ["Subjects", intent.subject_strategy],
      ["Environment", intent.environment_strategy],
      ["Emotion", intent.emotional_direction],
    ] as Array<[string, string]>
  ).filter(([, v]) => v && v.trim() !== "");
  if (rows.length === 0) return null;
  return (
    <dl className="kv">
      {rows.map(([k, v]) => (
        <Fragment key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </Fragment>
      ))}
    </dl>
  );
}

export default function CreativeDirectionCard({ intent }: { intent: CreativeIntent | null }) {
  if (!intent || (!intent.primary_goal && intent.preserve.length === 0)) return null;
  return (
    <section className="card direction-card">
      <CardHead label="Creative direction" hint={`${intent.confidence} confidence`} />
      {intent.primary_goal && <p className="direction-goal">{intent.primary_goal}</p>}
      <StrategyRows intent={intent} />
      {(intent.preserve.length > 0 || intent.flexible.length > 0) && (
        <div className="direction-lists">
          {intent.preserve.length > 0 && (
            <div>
              <span className="field-label">Must preserve</span>
              <div className="chips">
                {intent.preserve.map((p, i) => (
                  <span key={i} className="chip chip-essential">
                    <span className="importance-dot" />
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}
          {intent.flexible.length > 0 && (
            <div>
              <span className="field-label">Can change</span>
              <div className="chips">
                {intent.flexible.map((f, i) => (
                  <span key={i} className="chip chip-incidental">
                    <span className="importance-dot" />
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
