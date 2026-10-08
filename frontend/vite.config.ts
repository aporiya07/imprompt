import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf-8")) as { version: string };

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, root, "");
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || "http://localhost:8000";
  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_APP_VERSION": JSON.stringify(pkg.version),
    },
    server: {
      port: 5173,
      proxy: {
        "/api": proxyTarget,
      },
    },
  };
});
