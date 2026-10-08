# Collage and moodboard analysis

Collage handling is produced by the same vision analysis call, but the resulting `CollageAnalysis` preserves panel-specific shot records alongside global creative DNA.

```mermaid
flowchart LR
    A["Moodboard / contact sheet"]
    B["Vision analysis<br/>reference type + layout"]
    C["Per-panel records<br/>title · bounds · summary<br/>shot type · pose · composition<br/>lighting · palette · wardrobe · environment"]
    D["GlobalCreativeDNA<br/>recurring palette · lighting<br/>wardrobe · environment<br/>style · motifs · composition patterns"]
    E["Master creative direction<br/>shared visual system"]
    F["Shot-specific prompts<br/>one complete prompt per panel"]
    G["Prompt quality<br/>per-shot diagnostics"]

    A --> B
    B --> C
    B --> D
    D --> E
    C --> F
    D --> F
    E --> F
    F --> G

    X["Continuity across shots<br/>same subjects · wardrobe family<br/>palette · location family · lighting language"]
    Y["Variation per shot<br/>framing · pose · gaze · orientation<br/>interaction · viewpoint · scale"]
    X -.-> E
    Y -.-> F

    classDef input fill:#f4efe8,stroke:#6b6258,color:#28231f
    classDef analysis fill:#e8f0f2,stroke:#42636b,color:#1f3034
    classDef output fill:#e8f1e7,stroke:#557653,color:#253724
    class A input
    class B,C,D analysis
    class E,F,G output
    class X,Y input
```
