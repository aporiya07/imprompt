export const THEME_KEY = "imprompt.theme";
const LEGACY_THEME_KEYS = ["visura.theme", "ipa.theme"] as const;

export type Theme = "dark" | "light";

export function readStoredTheme(): Theme | null {
  const primary = localStorage.getItem(THEME_KEY);
  if (primary === "dark" || primary === "light") return primary;
  for (const key of LEGACY_THEME_KEYS) {
    const v = localStorage.getItem(key);
    if (v === "dark" || v === "light") return v;
  }
  return null;
}

export function resolveInitialTheme(): Theme {
  return readStoredTheme() ?? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
}

export function persistTheme(theme: Theme): void {
  localStorage.setItem(THEME_KEY, theme);
  for (const key of LEGACY_THEME_KEYS) {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  }
}
