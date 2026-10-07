export default function WorkingCard({ label }: { label?: string }) {
  return (
    <div className="working card" aria-live="polite">
      <span className="spinner" />
      <span>{label ?? "Analyzing the image — extracting Visual DNA and writing the prompt…"}</span>
    </div>
  );
}
