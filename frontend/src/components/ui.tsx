import type { ReactNode } from "react";

/** Editorial section kicker: small uppercase label. */
export function Kicker({ children }: { children: ReactNode }) {
  return <span className="kicker">{children}</span>;
}

/** Card header: kicker on the left, actions on the right. */
export function CardHead({
  label,
  hint,
  actions,
}: {
  label: string;
  hint?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="card-head">
      <Kicker>{label}</Kicker>
      {hint && <span className="hint card-head-hint">{hint}</span>}
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}
