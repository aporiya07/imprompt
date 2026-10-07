import { Fragment } from "react";
import type { ElementImportance, SubjectRecord, Swatch, VisualDNA } from "../types";
import { CardHead } from "./ui";

function titleCase(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function rowsOf(obj: Record<string, unknown> | undefined | null): Array<[string, string]> {
  if (!obj) return [];
  return Object.entries(obj)
    .filter(([k, v]) => k !== "confidence" && typeof v === "string" && v.trim() !== "")
    .map(([k, v]) => [titleCase(k), v as string]);
}

function Kv({ rows }: { rows: Array<[string, string]> }) {
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

function Chips({ items, tone = "" }: { items: string[]; tone?: string }) {
  if (items.length === 0) return null;
  return (
    <div className="chips">
      {items.map((c, i) => (
        <span key={i} className={`chip ${tone}`.trim()}>
          {c}
        </span>
      ))}
    </div>
  );
}

function Section({ title, open = false, children }: { title: string; open?: boolean; children: React.ReactNode }) {
  return (
    <details className="dna-section" open={open}>
      <summary>{title}</summary>
      <div className="section-body">{children}</div>
    </details>
  );
}

const IMPORTANCE_DOT: Record<ElementImportance, string> = {
  essential: "chip-essential",
  supporting: "chip keep",
  incidental: "chip chip-incidental",
  uncertain: "chip chip-uncertain",
};

function SubjectCard({ subject }: { subject: SubjectRecord }) {
  return (
    <div className="subject-card">
      <div className="subject-head">
        <b>{subject.description || subject.label}</b>
        <span className="hint">
          {subject.type}
          {subject.count > 1 ? ` ×${subject.count}` : ""}
        </span>
      </div>
      <Kv rows={rowsOf(subject as unknown as Record<string, unknown>)} />
      <Chips items={[...subject.accessories, ...subject.distinguishing_characteristics]} />
      {subject.interactions.length > 0 && (
        <div className="subject-interactions">Interacts: {subject.interactions.join("; ")}</div>
      )}
    </div>
  );
}

function SwatchChips({ swatches }: { swatches: Swatch[] }) {
  if (swatches.length === 0) return null;
  return (
    <div className="chips">
      {swatches.map((s, i) => (
        <span key={i} className="chip swatch">
          {s.hex && <span className="swatch-dot" style={{ background: `#${s.hex.replace(/^#/, "")}` }} />}
          {s.name || s.hex}
          {s.hex && <span className="swatch-hex">#{s.hex.replace(/^#/, "").toUpperCase()}</span>}
          {s.role ? ` · ${s.role}` : ""}
        </span>
      ))}
    </div>
  );
}

export default function DnaViewer({ dna }: { dna: VisualDNA }) {
  const reference = dna.reference;
  const materials = (dna.materials ?? []).filter((m) => m && Object.keys(m).length > 0);
  const relationships = (dna.relationships ?? []).filter((r) => r && (r.description || r.relation));
  const elements = (dna.elements ?? []).filter((e) => e.description);

  return (
    <section className="card dna" data-testid="visual-dna">
      <CardHead
        label="Visual understanding"
        hint={`${reference.reference_type.replace(/_/g, " ")} · ${Math.round((reference.analysis_confidence || 0) * 100)}% confidence`}
      />
      {reference.overall_description && <p className="dna-overall">{reference.overall_description}</p>}
      {reference.layout_description && <p className="dna-layout">{reference.layout_description}</p>}

      {dna.subjects.length > 0 && (
        <Section title="Subjects" open>
          {dna.subjects.map((s, i) => (
            <SubjectCard key={s.label || i} subject={s} />
          ))}
        </Section>
      )}

      <Section title="Composition">
        <Kv rows={rowsOf(dna.composition)} />
      </Section>

      <Section title="Camera">
        <Kv rows={rowsOf(dna.camera)} />
      </Section>

      <Section title="Lighting">
        <Kv rows={rowsOf(dna.lighting)} />
      </Section>

      <Section title="Color">
        <SwatchChips swatches={dna.color.dominant} />
        <SwatchChips swatches={dna.color.secondary} />
        <SwatchChips swatches={dna.color.accent} />
        <Kv
          rows={rowsOf(dna.color as unknown as Record<string, unknown>).filter(
            ([k]) => !["Dominant", "Secondary", "Accent"].includes(k)
          )}
        />
      </Section>

      <Section title="Environment">
        <Kv rows={rowsOf(dna.environment)} />
        <Chips items={dna.environment?.objects ?? []} />
        {(dna.environment?.spatial_relationships ?? []).length > 0 && (
          <ul className="mat-list">
            {(dna.environment!.spatial_relationships as string[]).map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Style">
        <Kv rows={rowsOf(dna.style)} />
      </Section>

      <Section title="Mood">
        <Kv rows={rowsOf(dna.mood)} />
        <Chips items={dna.mood?.emotional_tone ?? []} />
      </Section>

      {materials.length > 0 && (
        <Section title="Materials">
          <ul className="mat-list">
            {materials.map((m, i) => (
              <li key={i}>{[m.object, m.material, m.texture, m.reflectivity, m.appearance].filter(Boolean).join(", ")}</li>
            ))}
          </ul>
        </Section>
      )}

      {dna.typography?.present && (
        <Section title="Typography" open>
          <Chips items={dna.typography.text_content ?? []} />
          <Chips items={dna.typography.graphics ?? []} />
          <Kv rows={rowsOf(dna.typography as unknown as Record<string, unknown>)} />
        </Section>
      )}

      {relationships.length > 0 && (
        <Section title="Relationships">
          <ul className="mat-list">
            {relationships.map((r, i) => {
              const chain = [r.subject, r.relation, r.object].filter(Boolean).join(" → ");
              return <li key={i}>{r.description ? `${chain ? chain + ": " : ""}${r.description}` : chain}</li>;
            })}
          </ul>
        </Section>
      )}

      {elements.length > 0 && (
        <Section title="Important elements" open>
          <div className="chips">
            {elements.map((e, i) => (
              <span key={i} className={`chip ${IMPORTANCE_DOT[e.importance] ?? ""}`} title={e.reason || e.importance}>
                <span className="importance-dot" />
                {e.description}
              </span>
            ))}
          </div>
          <div className="hint importance-legend">
            accent marker: essential, plain: supporting, faded: incidental, amber: uncertain
          </div>
        </Section>
      )}

      {dna.uncertainty.length > 0 && (
        <Section title="Uncertainty">
          <ul className="mat-list uncertainty-list">
            {dna.uncertainty.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Technical">
        <Kv rows={rowsOf(dna.technical)} />
      </Section>

      <details className="dna-section raw-json">
        <summary>Developer details</summary>
        <pre className="raw-json-body">{JSON.stringify(dna, null, 2)}</pre>
      </details>
    </section>
  );
}
