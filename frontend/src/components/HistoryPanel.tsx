import type { HistoryItem } from "../types";
import { MODE_LABELS } from "../types";

interface Props {
  items: HistoryItem[];
  onRestore: (item: HistoryItem) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
}

export default function HistoryPanel({ items, onRestore, onDelete, onClear }: Props) {
  if (items.length === 0) return null;
  return (
    <section className="card history">
      <div className="card-head">
        <h2>Recent</h2>
        <button className="btn ghost small" onClick={onClear}>
          Clear
        </button>
      </div>
      <div className="history-list">
        {items.map((item) => (
          <div key={item.id} className="history-item" onClick={() => onRestore(item)} role="button" tabIndex={0}>
            {item.thumbnail ? (
              <img src={item.thumbnail} alt="" className="history-thumb" />
            ) : (
              <span className="history-thumb placeholder" />
            )}
            <span className="history-meta">
              <span className="history-line1">
                {MODE_LABELS[item.mode]} · {item.targetModel}
              </span>
              <span className="history-line2">{item.prompt.slice(0, 90)}…</span>
              <span className="history-line3">{new Date(item.ts).toLocaleString()}</span>
            </span>
            <span
              className="history-delete"
              role="button"
              aria-label="Delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(item.id);
              }}
            >
              ×
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
