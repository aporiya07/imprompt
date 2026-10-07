import type { HistoryItem } from "../types";

const KEY = "ipa.history.v1";
const MAX_ITEMS = 12;

export function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as HistoryItem[]) : [];
  } catch {
    return [];
  }
}

export function saveHistoryItem(item: HistoryItem): HistoryItem[] {
  const next = [item, ...loadHistory()].slice(0, MAX_ITEMS);
  persist(next);
  return next;
}

export function deleteHistoryItem(id: string): HistoryItem[] {
  const next = loadHistory().filter((i) => i.id !== id);
  persist(next);
  return next;
}

export function clearHistory(): HistoryItem[] {
  localStorage.removeItem(KEY);
  return [];
}

function persist(items: HistoryItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    // Storage full — retry without thumbnails.
    try {
      localStorage.setItem(KEY, JSON.stringify(items.map((i) => ({ ...i, thumbnail: "" }))));
    } catch {
      /* give up silently */
    }
  }
}
