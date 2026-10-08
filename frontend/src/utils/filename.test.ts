import { describe, expect, it } from "vitest";
import { safeFilenameFromUrl } from "./filename";

describe("safeFilenameFromUrl", () => {
  it("decodes valid percent encoding", () => {
    expect(safeFilenameFromUrl("https://cdn.example/photo%20name.jpg")).toBe("photo name.jpg");
  });

  it("falls back on malformed percent encoding without throwing", () => {
    expect(() => safeFilenameFromUrl("https://cdn.example/photo%GGname.jpg")).not.toThrow();
    const name = safeFilenameFromUrl("https://cdn.example/photo%GGname.jpg");
    expect(name).toBe("photo%GGname.jpg");
  });
});
