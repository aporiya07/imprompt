# ImPrompt system architecture

This is the repository-level view: the frontend calls the FastAPI routes, while the backend coordinates image handling, analysis, prompting, providers, and deterministic safeguards.

```mermaid
flowchart TB
    UI["React + TypeScript frontend<br/>upload · URL input · DNA viewer<br/>prompt · refinement · history"]
    API["FastAPI application<br/>strict API envelopes · request IDs"]
    ANALYSIS_API["Analysis routes<br/>/api/analyze · /api/fetch-image"]
    PROMPT_API["Prompt routes<br/>generate · refine · validate<br/>models · health"]
    MEDIA["Image handling<br/>base64 decode · magic-byte validation<br/>pixel/byte limits · EXIF · JPEG normalization"]
    FETCH["URL fetcher<br/>public HTTP(S) validation<br/>redirect checks · streaming limits"]
    VISION["Analysis stage<br/>vision provider executor"]
    DNA["Visual DNA + Creative Intent<br/>typed Pydantic artifacts"]
    COLLAGE["CollageAnalysis<br/>panel records + global DNA"]
    PROMPT["Prompting<br/>PromptSpec · templates<br/>collage generation · refinement"]
    ADAPTERS["Model adapters<br/>Gemini · OpenAI · FLUX<br/>Midjourney · Stable Diffusion · Generic"]
    PROVIDERS["Provider registry<br/>Gemini / OpenAI SDK wrappers<br/>retry · validation · fallback"]
    CACHE["In-process analysis cache<br/>TTL + in-flight deduplication"]
    DIAG["Deterministic diagnostics<br/>quality · visual coverage"]
    OBS["Observability<br/>request/stage logging"]

    UI --> API
    API --> ANALYSIS_API
    API --> PROMPT_API
    ANALYSIS_API --> MEDIA
    ANALYSIS_API --> FETCH
    MEDIA --> VISION
    FETCH --> MEDIA
    VISION --> DNA
    VISION --> CACHE
    DNA --> COLLAGE
    DNA --> PROMPT
    COLLAGE --> PROMPT
    PROMPT_API --> PROMPT
    PROMPT --> ADAPTERS
    ADAPTERS --> PROVIDERS
    PROVIDERS --> DIAG
    ADAPTERS --> DIAG
    API -.-> OBS
    VISION -.-> OBS
    PROMPT -.-> OBS

    classDef client fill:#f4efe8,stroke:#6b6258,color:#28231f
    classDef boundary fill:#e8f0f2,stroke:#42636b,color:#1f3034
    classDef core fill:#f0e9f7,stroke:#725789,color:#30243a
    classDef support fill:#f4f0df,stroke:#8a7742,color:#3d351d
    class UI client
    class API,ANALYSIS_API,PROMPT_API boundary
    class MEDIA,FETCH,VISION,DNA,COLLAGE,PROMPT,ADAPTERS,PROVIDERS core
    class CACHE,DIAG,OBS support
```
