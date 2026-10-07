import type { CreativeIntent } from "../types";

function StrategyRows({ intent }: { intent: CreativeIntent }) {
  const rows: Array<[string, string]> = [
    ["Aesthetic", intent.aesthetic_direction],
    ["Photography", intent.photographic_direction],
    ["Composition", intent.composition_strategy],
    ["Lighting", intent.lighting_strategy],
    ["Color", intent.color_strategy],
    ["Subjects", intent.subject_strategy],
    ["Environment", intent.environment_strategy],
    ["Emotion", intent.emotional_direction],
  ].filter(([, v]) => v && v.trim() !== "") as Array<[string, string]>;
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

import { Fragment } from "react";

export default function CreativeDirectionCard({ intent }: { intent: CreativeIntent | null }) {
  if (!intent || (!intent.primary_goal && intent.preserve.length === 0)) return null;
  return (
    <section className="card direction-card">
      <div className="card-head">
        <h2>Creative Direction</h2>
        <span className="hint">{intent.confidence} confidence</span>
      </div>
      {intent.primary_goal && <p className="direction-goal">{intent.primary_goal}</p>}
      <StrategyRows intent={intent} />
      {(intent.preserve.length > 0 || intent.flexible.length > 0) && (
        <div className="direction-lists">
          {intent.preserve.length > 0 && (
            <div>
              <div className="hint">must preserve</div>
              <div className="chips">
                {intent.preserve.map((p, i) => (
                  <span key={i} className="chip chip-essential">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}
          {intent.flexible.length > 0 && (
            <div>
              <div className="hint">can change</div>
              <div className="chips">
                {intent.flexible.map((f, i) => (
                  <span key={i} className="chip chip-incidental">
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
