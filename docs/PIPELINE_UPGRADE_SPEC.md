You are working on my existing project:

C:\AP\itp

This is an AI visual reverse-engineering application.

IMPORTANT:
We are NOT building the node-based workflow editor yet.
The node-based/n8n/ComfyUI-style idea is archived for a future V2.

For now, your ONLY goal is to make the current image → visual understanding → prompt pipeline significantly better and more reliable.

Do not redesign the whole application unnecessarily.
Do not replace working architecture just because you prefer another stack.
Do not add unrelated features.
Work incrementally and validate every phase.

============================================================
PROJECT CONTEXT
============================================================

Current stack:

Backend:
- Python
- FastAPI
- Pydantic v2
- uv
- Gemini vision provider
- OpenAI prompt optimization provider

Frontend:
- React
- TypeScript
- Vite

Current pipeline concept:

Reference Image
      ↓
Image Validation / Processing
      ↓
Gemini Vision Analysis
      ↓
Visual DNA
      ↓
OpenAI Prompt Optimization
      ↓
Model-specific Prompt Adapter
      ↓
Final Prompt

Current supported target models include:
- Generic
- Gemini / Nano Banana
- GPT Image
- FLUX
- Midjourney
- Stable Diffusion

The existing project already has:
- image validation
- magic-byte detection
- image size limits
- image normalization/downscaling
- Gemini vision analysis
- Visual DNA validation/normalization
- OpenAI prompt optimization
- model-specific prompt adapters
- analyze/generate/refine APIs
- frontend upload UI
- prompt results
- Visual DNA display
- refine workflow
- history
- tests

FIRST ACTION:
Inspect the entire existing repository before changing anything.

Read:
- README
- backend structure
- frontend structure
- Pydantic models
- API routes
- services
- providers
- prompts
- adapters
- tests
- frontend components
- configuration/environment handling

Create an internal understanding of the existing architecture.

Do NOT immediately start coding.

============================================================
PRODUCT DIRECTION
============================================================

The product is NOT supposed to be a generic image captioning tool.

The core product idea is:

"Reverse-engineer the visual logic of an image and convert it into a controllable generation recipe."

The system should answer:

1. What is actually visible?
2. What visual elements are important?
3. What makes the image aesthetically work?
4. Which elements are essential versus incidental?
5. How is the image composed?
6. How was it photographed/rendered?
7. What lighting is being used?
8. What style and mood are being communicated?
9. How should another image model reproduce the visual result?
10. How should the prompt change depending on the target model?

For example:

A weak system says:

"A romantic couple standing on a beach at sunset."

A strong system understands:

- two-person romantic composition
- full/medium body framing
- golden-hour backlight
- warm orange/cream palette
- shallow depth of field
- cinematic editorial photography
- ocean background
- intimate body language
- specific wardrobe
- environmental separation
- negative space
- camera perspective
- subject/background relationship
- photographic intent

The goal is VISUAL REVERSE ENGINEERING, not caption generation.

============================================================
OVERALL IMPLEMENTATION PLAN
============================================================

Implement the following phases IN ORDER.

Do not skip directly to Phase 4.

After each phase:
1. run backend tests
2. run frontend type checking/build
3. fix regressions
4. report exactly what changed
5. only then continue

============================================================
PHASE 0 — FULL CODEBASE AUDIT
============================================================

Before modifying code:

Inspect the repository.

Identify:

A. Current request/response contracts
B. Current Visual DNA schema
C. Current Gemini analysis prompt
D. Current OpenAI optimization prompt
E. Current model adapters
F. Current refine implementation
G. Current frontend data flow
H. Existing tests
I. Existing API envelope implementation
J. Any contract inconsistencies
K. Any duplicated logic
L. Any places where information is lost between stages

Create a short internal audit.

Then identify the minimum files that need modification.

IMPORTANT:
Do not rewrite unrelated code.

============================================================
PHASE 1 — REDESIGN VISUAL DNA
============================================================

The biggest priority is improving Visual DNA.

The current Visual DNA must become rich enough to represent how an image actually works.

Design a strongly typed Pydantic v2 schema.

Do not use unstructured dictionaries where a typed model is appropriate.

The Visual DNA should contain, where applicable:

------------------------------------------------------------
1. REFERENCE METADATA
------------------------------------------------------------

reference_type:
- single_image
- collage
- moodboard
- screenshot
- photograph
- illustration
- advertisement
- product_image
- unknown

analysis_confidence

overall_description

------------------------------------------------------------
2. SUBJECT
------------------------------------------------------------

subjects[]

For each subject capture:

- type
- count
- approximate age category if visually relevant
- gender presentation only when visually evident/relevant
- clothing
- accessories
- pose
- body orientation
- facial expression
- gaze direction
- position in frame
- relative scale
- distinguishing visual characteristics
- interaction with other subjects

DO NOT invent identity or attributes that cannot be observed.

Use uncertainty where appropriate.

------------------------------------------------------------
3. ENVIRONMENT
------------------------------------------------------------

Capture:

- location type
- indoor/outdoor
- foreground
- middle ground
- background
- environmental objects
- architecture
- landscape
- weather
- time of day
- season if visually inferable
- atmosphere
- spatial relationships

------------------------------------------------------------
4. COMPOSITION
------------------------------------------------------------

This is extremely important.

Capture:

- shot type
- framing
- camera angle
- viewpoint
- subject placement
- rule of thirds / centered / symmetrical / asymmetric
- negative space
- foreground/background relationship
- depth
- leading lines
- visual hierarchy
- cropping
- orientation
- aspect ratio
- subject scale
- visual balance
- perspective

Do NOT simply output generic terms like "well composed."

Describe the actual composition.

------------------------------------------------------------
5. CAMERA / PHOTOGRAPHY
------------------------------------------------------------

When visually inferable:

- camera perspective
- apparent focal length category
- wide/normal/telephoto appearance
- depth of field
- focus plane
- background blur
- motion blur
- shutter-like visual characteristics
- perspective compression
- lens distortion
- image sharpness
- photographic realism

IMPORTANT:

Never claim an exact camera, lens, aperture, ISO, shutter speed, etc. unless it is explicitly known.

Use approximate categories such as:

"telephoto-like compression"

instead of:

"85mm f/1.4 lens"

unless there is actual evidence.

------------------------------------------------------------
6. LIGHTING
------------------------------------------------------------

Capture:

- lighting type
- key light direction
- fill level
- backlight/rim light
- hard/soft light
- natural/artificial
- light temperature
- highlights
- shadows
- contrast
- exposure characteristics
- atmospheric lighting
- golden hour / blue hour / daylight / studio etc.
- practical lights if visible

Lighting should be described in a way useful for image generation.

------------------------------------------------------------
7. COLOR
------------------------------------------------------------

Capture:

- dominant colors
- secondary colors
- accent colors
- approximate palette
- warm/cool balance
- saturation
- contrast
- brightness
- color grading
- tonal characteristics

Where possible represent palette as structured values.

------------------------------------------------------------
8. STYLE
------------------------------------------------------------

Capture:

- photography style
- editorial style
- visual genre
- artistic direction
- realism level
- cinematic characteristics
- fashion/editorial characteristics
- commercial characteristics
- cultural aesthetic when visually evident
- texture
- grain
- rendering characteristics
- post-processing characteristics

Avoid meaningless labels.

Instead of:

"beautiful"

prefer:

"soft cinematic editorial photography with warm golden-hour grading and restrained contrast."

------------------------------------------------------------
9. MOOD / EMOTION
------------------------------------------------------------

Capture:

- emotional tone
- atmosphere
- intimacy
- energy
- sophistication
- calmness
- drama
- romance
- nostalgia
- etc.

Use observable visual evidence where possible.

------------------------------------------------------------
10. MATERIALS / TEXTURES
------------------------------------------------------------

Capture:

- fabric
- skin appearance
- metal
- glass
- wood
- stone
- water
- foliage
- architectural surfaces
- texture characteristics

------------------------------------------------------------
11. TYPOGRAPHY / GRAPHICS
------------------------------------------------------------

If the image contains text:

- visible text
- text position
- typography style
- approximate hierarchy
- graphic elements
- logos if visible
- layout

Do not hallucinate unreadable text.

------------------------------------------------------------
12. VISUAL RELATIONSHIPS
------------------------------------------------------------

This is extremely important.

Represent relationships such as:

- subject A facing subject B
- subject standing behind object
- person holding object
- person positioned beside object
- foreground object partially occluding subject
- light source behind subject
- background architecture framing subject

The system must understand spatial relationships, not just list objects.

------------------------------------------------------------
13. ESSENTIAL VS INCIDENTAL
------------------------------------------------------------

Every important visual element should be classified approximately as:

- essential
- supporting
- incidental
- uncertain

Example:

essential:
- golden-hour backlight
- beach environment
- intimate couple composition

supporting:
- warm cream wardrobe
- shallow depth of field

incidental:
- small rock
- tiny background object

This is critical for recreation.

============================================================
PHASE 2 — OBSERVATION VS INTERPRETATION
============================================================

Create a distinction between:

OBSERVATION

and

INTERPRETATION / CREATIVE INTENT.

Example:

Observation:
"Two people are standing near the shoreline."

Interpretation:
"Romantic editorial pre-wedding photography emphasizing intimacy and warmth."

Do not allow interpretation to overwrite observation.

The pipeline should conceptually be:

IMAGE
 ↓
OBSERVATION
 ↓
VISUAL DNA
 ↓
CREATIVE INTENT
 ↓
GENERATION INSTRUCTIONS

Add appropriate typed models if necessary.

Use confidence levels.

Possible confidence:

- high
- medium
- low

The model must be allowed to say:

"uncertain"

instead of hallucinating.

============================================================
PHASE 3 — IMPROVE GEMINI VISION ANALYSIS
============================================================

Rewrite/improve the Gemini vision analysis prompt.

The prompt should explicitly tell Gemini:

You are a visual reverse-engineering system.

Do NOT write a generic caption.

Analyze the image as a professional:
- photographer
- art director
- cinematographer
- fashion/editorial director
- image-generation prompt engineer

The analysis must focus on reproducible visual information.

Gemini must:

1. identify subjects
2. understand spatial relationships
3. analyze composition
4. analyze camera perspective
5. analyze lighting
6. analyze color
7. analyze environment
8. analyze wardrobe/materials
9. analyze mood
10. analyze style
11. identify important visual motifs
12. distinguish essential from incidental elements
13. record uncertainty
14. avoid unsupported technical claims

Require strict JSON matching the Pydantic schema.

Do not let the model return prose around the JSON.

Implement:
- JSON parsing
- validation
- normalization
- retry
- repair only when necessary
- final validation

If repair is performed, never silently accept an invalid structure.

============================================================
PHASE 4 — CREATIVE INTENT LAYER
============================================================

Add a layer between Visual DNA and Prompt Generation.

Create something like:

CreativeIntent

It should summarize:

- primary visual objective
- aesthetic direction
- photographic direction
- composition strategy
- lighting strategy
- color strategy
- subject strategy
- environment strategy
- emotional direction
- essential elements
- elements that can change
- elements that should remain stable

Example:

{
  "primary_goal": "Recreate the visual language of a romantic cinematic beach pre-wedding photograph",
  "preserve": [
    "golden-hour backlighting",
    "intimate couple composition",
    "warm cinematic color grading",
    "shallow depth of field"
  ],
  "flexible": [
    "background details",
    "minor environmental objects"
  ]
}

This layer should be useful when the user later provides a different person/product.

============================================================
PHASE 5 — MAKE THE PROMPT GENERATOR MUCH BETTER
============================================================

The OpenAI prompt optimizer should NOT simply rewrite the Visual DNA into a long paragraph.

It should construct a generation-ready instruction.

Prompt structure should generally follow:

1. Primary objective
2. Subject
3. Subject appearance
4. Pose/action
5. Environment
6. Composition
7. Camera perspective
8. Lighting
9. Color
10. Style
11. Materials/textures
12. Mood
13. Important spatial relationships
14. Quality/rendering instructions
15. Constraints
16. Negative prompt where supported

But:

DO NOT blindly include every field.

The prompt should prioritize high-confidence, visually important information.

Avoid unnecessary verbosity.

Avoid contradictory instructions.

Avoid hallucinated technical details.

Avoid generic filler such as:

"masterpiece"
"best quality"
"8k"
"ultra detailed"

unless they actually help the selected model.

============================================================
PHASE 6 — MODEL-SPECIFIC PROMPT ADAPTERS
============================================================

Audit all existing adapters.

Each model should receive a prompt optimized for its actual interaction style.

Do not simply change the model name.

Maintain a common internal representation:

Visual DNA
+
Creative Intent
+
User Instruction

Then:

Model Adapter

produces:

Target-specific PromptResult.

At minimum maintain adapters for:

- Generic
- Gemini / Nano Banana
- GPT Image
- FLUX
- Midjourney
- Stable Diffusion

Each adapter should define:

- prompt structure
- instruction style
- reference-image language
- negative prompt behavior
- parameter requirements
- model-specific limitations
- image editing vs generation behavior

Do not invent unsupported model capabilities.

Keep model-specific behavior isolated from the core analysis engine.

============================================================
PHASE 7 — REFERENCE-AWARE PROMPTING
============================================================

Introduce the concept of reference intent.

The system should be able to distinguish:

- recreate
- create_similar
- extract_style
- extract_composition
- extract_lighting
- extract_color
- extract_pose
- modify

For now, preserve compatibility with the existing API.

If necessary introduce a typed enum.

For example:

RECREATE

means:

"Try to preserve the visual structure and important characteristics of the reference."

CREATE_SIMILAR

means:

"Use the visual language but create a new composition."

EXTRACT_STYLE

means:

"Do not reproduce the exact scene; extract the aesthetic language."

MODIFY

means:

"Preserve the reference unless explicitly instructed to change something."

This distinction must influence prompt generation.

============================================================
PHASE 8 — COLLAGE / MOODBOARD DETECTION
============================================================

This is a HIGH PRIORITY feature because many of my target images will come from Pinterest.

Do NOT treat a 3x3 Pinterest collage as one photographic scene.

The system should detect whether the input is likely:

- single image
- collage
- moodboard
- screenshot containing multiple images

Add:

reference_type

and appropriate confidence.

For a collage/moodboard:

1. detect panels
2. identify approximate panel boundaries
3. analyze individual panels
4. produce per-panel Visual DNA
5. identify recurring characteristics
6. generate a GLOBAL CREATIVE DNA

For example:

9 images might contain:

Panel 1 → close-up portrait
Panel 2 → couple walking
Panel 3 → sitting pose
Panel 4 → flower detail
Panel 5 → sunset
...

The system should identify common patterns:

- warm golden-hour lighting
- beach environment
- romantic editorial photography
- red/cream wardrobe
- intimate couple posing
- shallow depth of field
- warm color palette

Then produce:

GLOBAL CREATIVE DNA

plus:

PANEL SHOT DNA

Do not simply average all panels together.

============================================================
PHASE 9 — COLLAGE OUTPUT
============================================================

For a collage, the output should conceptually look like:

GLOBAL CREATIVE DIRECTION

- overall aesthetic
- color palette
- lighting
- mood
- photography style
- wardrobe direction
- environment
- recurring motifs
- composition patterns

SHOT 01

- shot type
- pose
- composition
- lighting
- prompt

SHOT 02

...

SHOT 09

...

This will eventually allow a user to upload a Pinterest moodboard and create an entire photoshoot concept.

Do not build the full photoshoot UI yet.

First build the backend data model and pipeline.

============================================================
PHASE 10 — REFINE PIPELINE
============================================================

Improve:

POST /api/refine-prompt

The refine process should understand:

CURRENT PROMPT
+
REFERENCE VISUAL DNA
+
CURRENT INSTRUCTION
+
KEEP
+
CHANGE

Example:

KEEP:
- couple identity
- wardrobe
- sunset
- beach
- composition

CHANGE:
- make pose more intimate
- move camera closer
- stronger golden-hour lighting

The system should generate a new prompt without destroying the requested preserved elements.

It should not simply append the new instruction to the previous prompt.

It should regenerate the prompt coherently.

============================================================
PHASE 11 — ADD PROMPT DIAGNOSTICS
============================================================

Before returning a generated prompt, validate it.

Create a prompt quality validator.

Check for:

- missing subject
- missing primary objective
- contradictions
- excessive repetition
- unsupported technical claims
- vague language
- hallucinated details
- missing reference instructions
- unnecessary filler
- model-incompatible instructions

Return structured diagnostics internally and expose useful information to the frontend where appropriate.

Example:

prompt_quality:

score: 87

warnings:
[
  "Camera focal length is inferred rather than known."
]

strengths:
[
  "Strong composition description",
  "Clear lighting direction",
  "Good subject/environment separation"
]

Do not make the score meaningless.

Use deterministic heuristics where possible.

============================================================
PHASE 12 — PRESERVE STRICT API CONTRACTS
============================================================

Do NOT introduce contract drift.

All API responses must use the strict envelope already defined for this project.

Success:

{
  "success": true,
  "data": {...},
  "error": null
}

Error:

{
  "success": false,
  "data": null,
  "error": {
    "code": "...",
    "message": "...",
    "details": [],
    "request_id": "..."
  }
}

Use Pydantic models.

Do not return arbitrary dictionaries from routes.

Do not use Any unnecessarily.

All endpoints must have explicit response models.

Validate both success and error envelopes.

Maintain request IDs.

============================================================
PHASE 13 — FRONTEND IMPROVEMENTS
============================================================

Do not redesign the frontend completely.

Improve the current UX to expose the stronger pipeline.

For a single image, display:

REFERENCE

VISUAL UNDERSTANDING

CREATIVE DIRECTION

GENERATED PROMPT

NEGATIVE PROMPT

MODEL

QUALITY / WARNINGS

For Visual DNA:

Do not dump a giant JSON object directly to the user.

Present useful sections:

- Subject
- Composition
- Camera
- Lighting
- Color
- Style
- Environment
- Mood
- Important Elements
- Uncertainty

Keep raw JSON available for debugging/developer use.

============================================================
PHASE 14 — COLLAGE UI
============================================================

If the backend detects a collage:

Show:

"Detected: 9-panel moodboard"

Then:

GLOBAL CREATIVE DNA

followed by:

Shot 01
Shot 02
Shot 03
...

Each shot should be expandable.

Each shot should have:

- thumbnail if available
- visual summary
- composition
- lighting
- style
- prompt

Do not build an overly complex UI.

The priority is correctness and usefulness.

============================================================
PHASE 15 — TEST DATA / BENCHMARK
============================================================

Create a proper evaluation suite.

Use representative images for:

1. portrait
2. couple
3. fashion editorial
4. product advertisement
5. architecture
6. food
7. landscape
8. interior
9. cinematic image
10. Pinterest collage
11. 3x3 moodboard
12. image with text
13. low-light image
14. complex composition
15. image containing multiple people

For every case evaluate:

- subject accuracy
- composition accuracy
- lighting accuracy
- color accuracy
- style accuracy
- spatial relationship accuracy
- uncertainty handling
- prompt usefulness
- hallucination rate

The goal is not just:

"Does the JSON validate?"

The goal is:

"Does the generated prompt actually help another image model reproduce the important visual characteristics?"

============================================================
PHASE 16 — TEST GENERATION QUALITY
============================================================

Where API keys are available, create an optional integration benchmark.

Pipeline:

Reference
→ Analyze
→ Generate Prompt
→ Generate Image
→ Compare

Do NOT make external generation mandatory for unit tests.

Unit tests must remain deterministic and affordable.

Create separate:

- unit tests
- contract tests
- integration tests
- optional live AI tests

Never make the full test suite depend on paid APIs.

============================================================
PHASE 17 — CACHING / COST CONTROL
============================================================

Do not unnecessarily call models multiple times.

Where appropriate:

cache:

- normalized image hash
- Visual DNA
- creative intent
- generated prompt

Use stable cache keys.

Do not store raw images in logs.

Never log API keys.

Never log full private image contents.

============================================================
PHASE 18 — OBSERVABILITY
============================================================

Every pipeline execution should have:

request_id
analysis latency
prompt latency
total latency
provider
model
success/failure
validation status

Do not log sensitive image contents.

Make failures diagnosable.

Example:

REQUEST
 ↓
IMAGE VALIDATION
 ↓
VISION ANALYSIS
 ↓
DNA VALIDATION
 ↓
CREATIVE INTENT
 ↓
PROMPT GENERATION
 ↓
PROMPT VALIDATION
 ↓
RESPONSE

If something fails, we should know exactly which stage failed.

============================================================
PHASE 19 — DO NOT BUILD THESE YET
============================================================

Explicitly DO NOT implement:

- node-based canvas
- React Flow / XYFlow
- workflow builder
- n8n-like editor
- visual programming
- workflow marketplace
- complex user accounts
- team collaboration
- billing
- Chrome extension
- Pinterest browser extension
- model marketplace
- complicated job queue
- microservices
- Kubernetes
- distributed architecture

Those are future considerations.

The current goal is making the intelligence pipeline excellent.

============================================================
PHASE 20 — ARCHITECTURE PRINCIPLE
============================================================

Keep the system modular so that later it CAN become node-based.

The internal architecture should naturally allow:

Image Input
→ Vision Analyzer
→ Visual DNA
→ Creative Intent
→ Prompt Builder
→ Model Adapter
→ Generation
→ Evaluation
→ Refinement

Each stage should have a clean typed input/output contract.

DO NOT implement a node graph.

Just keep the services modular.

Later these services can become nodes.

============================================================
PHASE 21 — FINAL PIPELINE
============================================================

The desired architecture after this work is:

                    ┌──────────────────────┐
                    │     Reference       │
                    │       Image         │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ Image Preprocessor  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Image Type/        │
                    │ Collage Detection   │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   Vision Analysis   │
                    │      Gemini         │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Visual DNA       │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Creative Intent    │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ Prompt Construction │
                    │      OpenAI         │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ Prompt Validator    │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Model Adapter      │
                    └──────────┬───────────┘
                               ↓
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
      Gemini               GPT Image             FLUX
          ↓                    ↓                    ↓
      Prompt               Prompt                Prompt


For refinement:

Reference
    ↓
Visual DNA
    ↓
Current Prompt
    ↓
Keep / Change Instruction
    ↓
Prompt Reconstructor
    ↓
Prompt Validator
    ↓
New Prompt


For a moodboard:

Pinterest / Reference Collage
          ↓
     Collage Detection
          ↓
      Panel Detection
          ↓
   ┌──────┼──────┐
   ↓      ↓      ↓
Panel 1 Panel 2 ... Panel N
   ↓      ↓      ↓
Visual DNA per panel
          ↓
Cross-panel analysis
          ↓
GLOBAL CREATIVE DNA
          +
SHOT-SPECIFIC DNA
          ↓
Master Creative Direction
          +
Shot Prompts

============================================================
IMPLEMENTATION RULES
============================================================

RULE 1:
Inspect before modifying.

RULE 2:
Do not rewrite working code unnecessarily.

RULE 3:
Do not change the technology stack unless there is a concrete technical reason.

RULE 4:
Use Pydantic models for contracts.

RULE 5:
No arbitrary dict-based data flow when a typed model is appropriate.

RULE 6:
Do not hallucinate visual details.

RULE 7:
Represent uncertainty explicitly.

RULE 8:
Separate observation from interpretation.

RULE 9:
Do not confuse image captioning with visual reverse engineering.

RULE 10:
Do not optimize prompts for length.
Optimize for visual controllability.

RULE 11:
Do not hardcode Pinterest-specific assumptions into the core engine.

RULE 12:
Pinterest is a SOURCE/USE CASE.
The underlying visual intelligence engine should remain generic.

RULE 13:
Do not introduce the node system yet.

RULE 14:
Do not break existing API compatibility unnecessarily.

RULE 15:
Every meaningful change must have tests.

RULE 16:
Run tests after each phase.

RULE 17:
If a test fails because of your change, fix it before proceeding.

RULE 18:
Do not silently remove existing functionality.

RULE 19:
Do not use paid APIs in unit tests.

RULE 20:
Do not expose API keys or private image data in logs.

============================================================
DELIVERABLES
============================================================

At the end of the implementation, provide:

1. Architecture changes
2. Files changed
3. New Pydantic models
4. Visual DNA improvements
5. Gemini analysis improvements
6. Creative Intent implementation
7. Prompt generation improvements
8. Model adapter improvements
9. Collage/moodboard support
10. Refinement improvements
11. Prompt validation
12. Frontend changes
13. Tests added
14. Existing tests status
15. Frontend build/type-check status
16. Any live API tests performed
17. Remaining limitations
18. Recommended next step

============================================================
IMPORTANT EXECUTION INSTRUCTION
============================================================

DO NOT attempt to implement everything blindly in one pass.

Work in this exact order:

PHASE 0
Audit repository

↓

PHASE 1
Visual DNA

↓

PHASE 2
Observation / Interpretation

↓

PHASE 3
Gemini analysis

↓

PHASE 4
Creative Intent

↓

PHASE 5
Prompt generation

↓

PHASE 6
Model adapters

↓

PHASE 7
Reference modes

↓

PHASE 8
Collage detection

↓

PHASE 9
Collage output

↓

PHASE 10
Refinement

↓

PHASE 11
Prompt diagnostics

↓

PHASE 12
API contracts

↓

PHASE 13
Frontend

↓

PHASE 14
Collage UI

↓

PHASE 15
Benchmark

↓

PHASE 16
Optional live evaluation

↓

PHASE 17
Caching

↓

PHASE 18
Observability

At each stage:

- inspect existing implementation
- implement only that stage
- run relevant tests
- fix failures
- verify no regressions
- continue

If you discover that an existing implementation already satisfies a requirement, DO NOT duplicate it. Improve it only where necessary.

============================================================
SUCCESS CRITERIA
============================================================

The final system should be able to take a Pinterest-style reference image and answer:

"What makes this image look like this?"

not merely:

"What is in this image?"

For example, for a romantic beach couple reference, the system should understand things such as:

- subject relationship
- pose
- framing
- camera perspective
- environmental context
- golden-hour lighting
- color palette
- wardrobe
- depth of field
- background separation
- editorial photography language
- emotional tone
- composition
- spatial relationships
- important vs incidental details

Then it should turn that understanding into a generation-ready prompt.

The ultimate test is:

REFERENCE IMAGE
        ↓
UNDERSTANDING
        ↓
PROMPT
        ↓
IMAGE GENERATION

The generated image should preserve the important visual characteristics of the reference while allowing the user to replace the subject or modify selected elements.

That is the product.

Start with PHASE 0.

Do not code before auditing the repository.