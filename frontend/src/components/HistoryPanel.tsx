import { X } from "lucide-react";
import type { HistoryItem } from "../types";
import { MODE_LABELS } from "../types";
import { CardHead } from "./ui";

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
      <CardHead
        label="History"
        actions={
          <button className="btn ghost small" onClick={onClear}>
            Clear
          </button>
        }
      />
      <div className="history-list">
        {items.map((item) => (
          <div
            key={item.id}
            className="history-item"
            onClick={() => onRestore(item)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter") onRestore(item);
            }}
          >
            {item.thumbnail ? (
              <img src={item.thumbnail} alt="" className="history-thumb" />
            ) : (
              <span className="history-thumb placeholder" />
            )}
            <span className="history-meta">
              <span className="history-line1">{MODE_LABELS[item.mode]}</span>
              <span className="history-line2">{item.prompt.slice(0, 90)}…</span>
              <span className="history-line3">{new Date(item.ts).toLocaleString()}</span>
            </span>
            <button
              className="history-delete"
              aria-label="Delete entry"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(item.id);
              }}
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
