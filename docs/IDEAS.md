# Idea Archive

## Node-based workflow canvas (n8n / ComfyUI style) — ARCHIVED 2026-10-07

**Status:** shelved after research; revisit when the linear app has proven usage.

### The idea

A drag-and-drop node editor for the image→prompt workflow, connected by paths:

- **Reference image nodes** — style references to recreate (Pinterest or any image URL)
- **User image nodes** — multiple identity references (the user and other people) to keep faces consistent
- **Prompt nodes** — user prompt + parameters
- **Visual model nodes** — pick the target image model
- **Final output node**

Fully dynamic: drag & drop, path connections, re-wiring.

### Why it was shelved

1. **Crowded category.** Generic "node canvas for AI models" is now occupied by Weavy, Krea Nodes, FLORA, Freepik — and Figma Weave (Figma's own entry). ComfyUI owns the pro/open-source end. A small standalone build can't win on canvas features.
2. **Scope.** A robust free-form graph engine (caching, cycles, typing, scheduler, save/load) is 5–10× the current MVP effort.
3. **Validation order.** The linear product just shipped; the graph should be phase 2 gated on real usage, not a parallel rebuild.

### What the research validated (keep these when reviving)

- The interaction model is proven: React Flow (xyflow, MIT) is the standard — n8n and Dify are built on it.
- Identity nodes are technically real: Nano Banana Pro takes up to 14 reference images with 5-person identity consistency; Nano Banana 2 / Flux-family take ~5.
- **The differentiated wedge:** none of the node canvases do prompt reverse-engineering (Visual DNA → model-specific prompt). Fusing that with identity consistency is the unique angle.
- Pinterest: don't integrate — ToS prohibits scraping and hotlinking is unreliable. Use a URL-paste node that fetches server-side once. (The linear precursor of this — `/api/fetch-image` — already ships in v1.1.)

### Recommended shape when revived

- **Constrained DAG, not free-form:** typed edges (`image`, `identity[]`, `DNA`, `prompt`), no cycles. ~90% of the value, ~30% of the engineering.
- Node types: Reference Image (upload/URL), Identity Image (multi), Prompt, Analyze (DNA), Visual Model (existing adapters), Output.
- React Flow frontend; FastAPI workflow runner with topological execution, **per-node result caching keyed by input hash** (cost control), SSE per-node progress.
- Out of scope for v1: loops, subgraphs, video, custom code nodes.

### Revival triggers

- The linear app gets consistent real usage and users ask for multi-reference / branching.
- A competitor ships prompt-DNA features (move faster) or the identity-consistency workflow proves demand.
