import type { HistoryItem } from "../types";

const KEY = "imprompt.history.v1";
const LEGACY_KEYS = ["visura.history.v1", "ipa.history.v1"] as const;
const MAX_ITEMS = 12;
export const HISTORY_SCHEMA_VERSION = 1;

function isObject(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

/** Validate a history entry; malformed/old shapes are rejected. */
export function isValidHistoryItem(raw: unknown): raw is HistoryItem {
  if (!isObject(raw)) return false;
  if (typeof raw.id !== "string" || typeof raw.ts !== "number") return false;
  if (typeof raw.mode !== "string" || typeof raw.targetModel !== "string") return false;
  if (typeof raw.name !== "string" || typeof raw.thumbnail !== "string") return false;
  if (typeof raw.prompt !== "string") return false;
  if (!isObject(raw.dna)) return false;
  if (raw.negative !== null && typeof raw.negative !== "string") return false;
  const ver = raw.historySchemaVersion;
  if (ver !== undefined && ver !== HISTORY_SCHEMA_VERSION) {
    // Accept legacy items that lack the version field (pre-v1) if core fields are present.
    if (typeof ver !== "number") return false;
  }
  return true;
}

function normalizeItem(raw: HistoryItem): HistoryItem {
  return {
    ...raw,
    historySchemaVersion: HISTORY_SCHEMA_VERSION,
    shots: raw.shots ?? [],
    panels: raw.panels ?? [],
  };
}

function readRawList(): unknown[] {
  const keys = [KEY, ...LEGACY_KEYS];
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      /* try next key */
    }
  }
  return [];
}

export function loadHistory(): HistoryItem[] {
  const items = readRawList()
    .filter(isValidHistoryItem)
    .map(normalizeItem)
    .slice(0, MAX_ITEMS);
  if (items.length > 0) {
    persist(items);
    for (const key of LEGACY_KEYS) {
      try {
        localStorage.removeItem(key);
      } catch {
        /* ignore */
      }
    }
  }
  return items;
}

export function saveHistoryItem(item: HistoryItem): HistoryItem[] {
  const normalized = normalizeItem({ ...item, historySchemaVersion: HISTORY_SCHEMA_VERSION });
  const next = [normalized, ...loadHistory().filter((i) => i.id !== normalized.id)].slice(0, MAX_ITEMS);
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
  for (const key of LEGACY_KEYS) {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  }
  return [];
}

function persist(items: HistoryItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    try {
      localStorage.setItem(KEY, JSON.stringify(items.map((i) => ({ ...i, thumbnail: "" }))));
    } catch {
      /* give up silently */
    }
  }
}
