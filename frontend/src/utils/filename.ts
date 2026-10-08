/** Decode a URL path segment for display; never throw on malformed percent encoding. */
export function safeFilenameFromUrl(url: string, fallback = "image"): string {
  const raw = url.split("/").pop()?.split("?")[0] || fallback;
  try {
    return decodeURIComponent(raw).slice(0, 80) || fallback;
  } catch {
    return raw.slice(0, 80) || fallback;
  }
}
