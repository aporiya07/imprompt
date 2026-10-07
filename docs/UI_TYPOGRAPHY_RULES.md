============================================================
STRICT TYPOGRAPHY + VISUAL LANGUAGE RULES
============================================================

These are NON-NEGOTIABLE project-wide rules.

They apply to:

- UI text
- headings
- labels
- buttons
- tooltips
- empty states
- loading states
- error messages
- toast messages
- component copy
- frontend source comments where applicable
- documentation generated as part of the frontend
- visual decorations
- icons
- status indicators

============================================================
RULE 1 — NEVER USE EM DASH
============================================================

DO NOT use the em dash character:

—

Anywhere in the product.

This is a strict rule.

Use alternatives:

- commas
- periods
- colons
- parentheses
- semicolons
- line breaks

Examples:

BAD:
"Visual DNA — extracted from your reference"

GOOD:
"Visual DNA: extracted from your reference"

BAD:
"Reference image — Creative Direction — Prompt"

GOOD:
"Reference image → Creative Direction → Prompt"

Also search the entire frontend source after implementation for:

—

and remove every occurrence.

============================================================
RULE 2 — NO EMOJI IN THE UI
============================================================

DO NOT use emoji anywhere in the product UI.

This includes:

- buttons
- headings
- empty states
- notifications
- status messages
- navigation
- cards
- loading states
- tooltips
- onboarding
- decorative elements

NEVER use emoji as icons.

Examples of prohibited UI:

"Analyze ✨"
"Upload 📷"
"AI Magic ✨"
"Success 🎉"
"Generate 🚀"
"Creative 🎨"

Do not replace emoji with Unicode symbols either when a proper visual/icon system is more appropriate.

============================================================
RULE 3 — USE VECTOR ICONS AND VISUAL REPRESENTATIONS
============================================================

Instead of emoji, use proper vector-based visual elements.

Preferred icon system:

Lucide Icons

Use SVG/vector icons consistently.

Examples:

Upload:
Upload icon

Image:
Image icon

Analyze:
Scan / ScanSearch icon

Prompt:
FileText / TextCursorInput

Copy:
Copy icon

Refine:
Wand2 / RefreshCw where semantically appropriate

Settings:
Settings icon

History:
History icon

Warning:
TriangleAlert

Error:
CircleAlert

Success:
CircleCheck

Information:
Info

Do not randomly select icons.

Choose icons based on semantic meaning.

Icons should generally be:

16px to 20px

with occasional 24px icons for prominent actions.

Do not use huge decorative icons.

============================================================
RULE 4 — USE VISUAL REPRESENTATION INSTEAD OF DECORATION
============================================================

When information can be communicated visually, use an intentional visual representation.

Examples:

Instead of:

"Essential 🔥"

Use:

small accent indicator
+
"Essential"

Instead of:

"High confidence ⭐⭐⭐⭐⭐"

Use:

Confidence
High

with a subtle confidence indicator.

Instead of:

"Lighting ☀️"

Use:

Lighting

with a Lucide vector icon if useful.

Instead of:

"9 images 🖼️"

Use:

Image icon
9 panels

Instead of:

"AI is thinking..."

Use:

a restrained progress indicator and:

"Reading visual structure"

The interface should communicate through:

- typography
- spacing
- iconography
- dividers
- grids
- progress indicators
- image thumbnails
- swatches
- charts where genuinely useful
- vector graphics
- structured metadata

rather than decorative emoji.

============================================================
RULE 5 — NO GENERIC AI SPARKLES
============================================================

Do NOT use:

- sparkle icons as decoration
- multiple sparkle icons
- magic wand decoration everywhere
- glowing stars
- AI brain icons
- robot icons
- circuit-board decorations
- neural-network illustrations
- floating particles
- artificial intelligence imagery

A single semantic icon may be used when it genuinely represents an action.

Do not use sparkle icons as a visual shorthand for "AI".

The product should communicate intelligence through its functionality and visual hierarchy, not AI clichés.

============================================================
RULE 6 — NO AI-SLOP VISUAL PATTERNS
============================================================

STRICTLY AVOID:

- purple-to-blue gradients
- pink-to-purple gradients
- rainbow gradients
- neon accents
- glowing borders
- glassmorphism everywhere
- excessive backdrop blur
- floating gradient blobs
- animated gradient backgrounds
- giant glowing CTA buttons
- excessive pill components
- excessive rounded cards
- giant shadows
- decorative 3D blobs
- generic AI illustrations
- robot illustrations
- stock "AI" imagery
- unnecessary dashboard charts
- fake statistics
- fake activity indicators
- fake model confidence visualizations
- meaningless progress bars
- decorative orbit diagrams
- random dots
- random geometric decorations
- excessive noise textures
- excessive grain
- decorative code snippets
- giant "AI POWERED" labels

Every visual element must have a reason to exist.

============================================================
RULE 7 — USE DATA VISUALIZATION WHEN APPROPRIATE
============================================================

When the product needs to communicate structured visual information, use proper visual systems.

For example:

COLOR PALETTE

Instead of:

"Warm beige, orange, cream"

Show:

[■■■■] #E8D8C3
[■■■■] #C9784A
[■■■■] #8A6A52

Use actual color swatches.

For confidence:

Confidence
High

Use a restrained indicator.

For image composition:

Use the actual image with overlays where useful.

For collage:

Use a contact sheet.

For relationships:

Use clean directional/vector connectors only when they genuinely clarify relationships.

For shot lists:

Use thumbnails.

For Visual DNA:

Use structured sections.

For model capabilities:

Use compact comparison rows rather than decorative cards.

============================================================
RULE 8 — VECTOR VISUAL LANGUAGE
============================================================

Establish a consistent vector language throughout the application.

Use:

- SVG icons
- thin/medium strokes
- consistent stroke width
- restrained geometry
- simple shapes
- semantic symbols

Recommended icon stroke:

approximately 1.5px to 2px.

Do not mix:

- filled emoji-style icons
- 3D icons
- colorful cartoon icons
- outlined Lucide icons
- random icon libraries

Use one coherent icon family.

============================================================
RULE 9 — ICONS MUST HAVE SEMANTIC PURPOSE
============================================================

Before adding an icon, ask:

"Does this icon improve comprehension or interaction?"

If NO:

Do not add it.

Do not put an icon beside every heading just to make the UI look interesting.

Text hierarchy and spacing are often enough.

============================================================
RULE 10 — DO NOT OVERUSE PILLS
============================================================

Pills should be reserved for:

- tags
- selected states
- compact metadata
- filters
- status labels

Do NOT turn every piece of text into a pill.

Bad:

[Subject]
[Composition]
[Lighting]
[Camera]
[Style]
[Color]

Better:

SUBJECT

Content...

COMPOSITION

Content...

============================================================
RULE 11 — VISUAL HIERARCHY OVER DECORATION
============================================================

If a section looks empty, do NOT immediately add:

- gradients
- icons
- illustrations
- decorative lines
- shapes
- shadows

First improve:

- typography
- spacing
- alignment
- grouping
- image scale
- whitespace
- content hierarchy

Whitespace is an intentional design element.

============================================================
RULE 12 — USE EDITORIAL VISUAL DEVICES
============================================================

The product can use sophisticated editorial devices instead of AI decoration.

Examples:

- thin rules
- section numbering
- small uppercase labels
- editorial captions
- image metadata
- contact-sheet layouts
- asymmetric grids
- typographic hierarchy
- restrained color accents
- image annotations
- swatches
- subtle dividers
- margin notes
- compact metadata

Use these sparingly.

The goal is sophistication, not visual noise.

============================================================
RULE 13 — SECTION LABELS
============================================================

Use small labels where useful.

Example:

01
REFERENCE

02
VISUAL UNDERSTANDING

03
CREATIVE DIRECTION

04
PROMPT

05
REFINEMENT

This can create a strong editorial structure.

Do not use numbering everywhere.

Use it where it improves navigation.

============================================================
RULE 14 — NO DECORATIVE TEXT
============================================================

Do not add copy purely to make the interface appear sophisticated.

Avoid phrases such as:

"Powered by next-generation AI"

"Unlock your creativity"

"Where ideas become reality"

"AI-powered visual intelligence"

unless the copy has an actual product purpose.

The UI should be concise and functional.

============================================================
RULE 15 — NO FAKE TECHNICAL AESTHETIC
============================================================

Do not add:

- fake terminal windows
- fake code
- fake system logs
- fake model metrics
- fake latency displays
- fake neural network diagrams
- fake technical graphs

unless that information is actually generated by the application and useful to the user.

The product should feel technically sophisticated without pretending to expose technical information it does not actually have.

============================================================
RULE 16 — REAL INFORMATION SHOULD LOOK REAL
============================================================

When displaying technical information, use actual values from the application.

Examples:

Model:
Gemini 2.5 Flash

Latency:
1.42s

Request:
abc123

Confidence:
High

Do not fabricate:

"99.8% visual accuracy"

"AI confidence 98%"

"10x faster"

unless those metrics genuinely exist and are measured.

============================================================
RULE 17 — ANIMATION MUST NEVER LOOK LIKE AI MAGIC
============================================================

Animation should communicate:

- state
- progress
- transition
- hierarchy
- interaction

Animation should NOT communicate:

"AI magic is happening."

Avoid:

- glowing pulses
- sparkles
- orbiting particles
- animated gradients
- morphing blobs
- floating particles
- excessive shimmer
- dramatic reveal animations

Preferred:

- opacity transition
- subtle translate
- height transition
- progress indicator
- content reveal
- button state transition
- image crossfade

============================================================
RULE 18 — NO TYPEWRITER EFFECT FOR NORMAL UI
============================================================

Do not use typewriter animations for:

- headings
- normal content
- prompts
- analysis
- buttons
- status messages

Generated content should appear normally.

Use transitions only when they improve comprehension.

============================================================
RULE 19 — LOADING VISUALS
============================================================

Use restrained loading indicators.

Preferred:

small spinner
progress bar
skeleton
subtle pulse
stage indicator

Example:

ANALYZING REFERENCE

01  Composition
02  Lighting
03  Color
04  Visual style

But do not pretend each stage is complete unless the backend actually reports that stage.

No fake progress.

============================================================
RULE 20 — IMAGE-FIRST VISUAL LANGUAGE
============================================================

The application's strongest visual elements should be real user/reference images.

Use images instead of decorative illustrations whenever the image itself can communicate the concept.

For example:

Moodboard:
actual reference thumbnails

Color:
actual extracted swatches

Composition:
actual reference image

Shot list:
actual generated/reference thumbnails

Visual relationships:
actual image + restrained annotation

This reinforces the product's identity as a visual intelligence tool.

============================================================
RULE 21 — DO NOT USE EM DASH IN GENERATED COPY
============================================================

This must also apply to dynamically generated frontend copy.

Before displaying any generated text from the frontend, sanitize or validate if necessary.

The character:

—

must never appear.

If generated content contains an em dash, replace it with an appropriate alternative such as:

", "
": "
". "
" → "

Do not blindly replace every em dash with a hyphen.

Choose the correct punctuation for the sentence.

============================================================
RULE 22 — FINAL AUTOMATED CHECK
============================================================

Before declaring the design update complete, search the entire frontend codebase for:

1. Em dash:
—

2. Emoji Unicode ranges

3. Sparkle characters

4. Common AI decorative patterns

5. Hardcoded colors

6. Inconsistent icon imports

7. Duplicate CSS tokens

8. Random border-radius values

9. Random spacing values

10. Excessive gradients

11. Excessive box shadows

12. Excessive backdrop-filter usage

Fix every violation that is part of the UI.

============================================================
FINAL DESIGN STANDARD
============================================================

The final interface should communicate:

VISUAL INTELLIGENCE

through:

real imagery
typography
editorial hierarchy
structured information
vector iconography
color systems
contact sheets
swatches
composition
spacing
subtle motion

NOT through:

emoji
sparkles
gradients
glows
robots
AI clichés
decorative noise

The product should look like it was designed intentionally by a strong product designer and art director.

It should feel closer to a professional creative instrument than a generic AI application.

============================================================
FINAL QA QUESTION
============================================================

Before finishing, ask yourself:

"If I remove the logo and product name, does this still look like a distinctive visual intelligence tool?"

If the answer is no:

keep refining the design system.

Do not add decoration to solve the problem.

Improve:

typography
spacing
layout
image treatment
hierarchy
color
iconography
interaction design

until the identity is strong enough to stand on its own.