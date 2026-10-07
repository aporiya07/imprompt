export default function WorkingCard({ label }: { label?: string }) {
  return (
    <div className="working card" aria-live="polite">
      <span className="spinner" />
      <div>
        <div className="working-kicker">Analyzing reference</div>
        <div>{label ?? "Reading visual structure: composition, lighting, color, style"}</div>
      </div>
    </div>
  );
}
