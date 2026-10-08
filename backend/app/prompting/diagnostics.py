"""Deterministic prompt-quality heuristics (spec Phase 11).

No LLM calls: pure pattern checks so the score is stable and explainable.
Every warning is actionable; strengths note what the prompt does well.
"""
import re

from app.models.dna import VisualDNA
from app.models.quality import PromptQuality
from app.prompting.adapters.base import PromptTarget

FILLER = re.compile(
    r"\b(masterpiece|best quality|top quality|8k|4k|ultra detailed|highly detailed|"
    r"award[- ]winning|stunning|gorgeous|amazing|incredible|breathtaking)\b",
    re.IGNORECASE,
)
TECH_CLAIM = re.compile(r"\b(\d{2,3}\s?mm\b|\bf/[12](\.\d)?\b|\bISO\s?\d{3,5}\b|\b1/\d{3,4}\s?s\b)", re.IGNORECASE)
VAGUE = re.compile(r"\b(nice|beautiful|good looking|well composed|very aesthetic|lovely)\b", re.IGNORECASE)
SPATIAL = re.compile(
    r"\b(behind|beside|in front of|above|below|left of|right of|framed by|occlu\w+|next to)\b", re.IGNORECASE
)
LIGHTING_WORDS = re.compile(
    r"\b(backlight\w*|rim light|golden hour|blue hour|soft light|hard light|key light|"
    r"window light|studio light|side light|overcast)\b",
    re.IGNORECASE,
)
COMPOSITION_WORDS = re.compile(
    r"\b(rule of thirds|negative space|leading lines?|symmetr\w+|asymmetric\w*|centered|"
    r"off[- ]center|close[- ]?up|wide shot|medium shot|full[- ]body|waist[- ]up|portrait orientation)\b",
    re.IGNORECASE,
)
MATERIAL_WORDS = re.compile(
    r"\b(fabric|silk|leather|metal|glass|wood|stone|knit|denim|satin|linen|wool|"
    r"skin|texture|matte|glossy|reflect\w+)\b",
    re.IGNORECASE,
)


def validate_prompt(
    prompt: str, negative: str | None, target: PromptTarget, dna: VisualDNA
) -> PromptQuality:
    score = 100
    warnings: list[str] = []
    strengths: list[str] = []
    text = prompt.strip()

    if not text:
        return PromptQuality(score=0, warnings=["Prompt is empty."], strengths=[])

    if len(text) < 60:
        warnings.append("Prompt is very thin: important visual information is likely missing.")
        score -= 25

    fillers = sorted({m.group(0).lower() for m in FILLER.finditer(text)})
    if fillers:
        warnings.append(f"Filler words that add little control: {', '.join(fillers)}")
        score -= 6 * len(fillers)

    claims = sorted({m.group(0) for m in TECH_CLAIM.finditer(text)})
    if claims:
        warnings.append(f"Unsupported technical claims (no evidence in the analysis): {', '.join(claims)}")
        score -= 10

    vague = sorted({m.group(0).lower() for m in VAGUE.finditer(text)})
    if vague:
        warnings.append(f"Vague language: {', '.join(vague)}")
        score -= 5 * len(vague)

    words = re.findall(r"[a-z']+", text.lower())
    shingles = [" ".join(words[i : i + 5]) for i in range(len(words) - 4)]
    seen: set[str] = set()
    repeated: set[str] = set()
    for shingle in shingles:
        if shingle in seen:
            repeated.add(shingle)
        seen.add(shingle)
    if repeated:
        warnings.append("Contains repeated phrases: tighten the wording so every clause earns its place.")
        score -= 6

    subject_terms: list[str] = []
    stopwords = {"with", "that", "this", "from", "into", "over", "near", "wearing", "while", "also"}
    for subject in dna.subjects[:3]:
        subject_terms.extend(
            term
            for term in re.findall(r"[a-z']{4,}", (subject.description + " " + subject.clothing).lower())
            if term not in stopwords
        )
    if subject_terms and not any(term in text.lower() for term in subject_terms):
        warnings.append("The analyzed subject does not appear to be described in the prompt.")
        score -= 15

    if negative:
        neg_fillers = sorted({m.group(0).lower() for m in FILLER.finditer(negative)})
        if neg_fillers:
            warnings.append(f"Negative prompt contains filler terms: {', '.join(neg_fillers)}")
            score -= 4
        if len(negative.split(",")) > 12:
            warnings.append("Negative prompt is a long boilerplate list: keep it specific to this image.")
            score -= 4

    if target.soft_char_limit and len(text) > target.soft_char_limit:
        warnings.append(f"Prompt exceeds the ~{target.soft_char_limit}-character comfort zone for {target.name}.")
        score -= 5

    prompt_temps: set[str] = set()
    if re.search(r"\bwarm\b", text, re.IGNORECASE):
        prompt_temps.add("warm")
    if re.search(r"\bcool\b", text, re.IGNORECASE):
        prompt_temps.add("cool")
    if len(prompt_temps) == 2:
        # Split lighting ("warm highlights, cool shadows") is a legitimate deliberate
        # choice; only flag when the two terms are not presented as an intentional pair.
        paired = bool(re.search(r"\bwarm\b[^.!?]{0,60}\bcool\b|\bcool\b[^.!?]{0,60}\bwarm\b", text, re.IGNORECASE))
        dna_temp = dna.color.warm_cool_balance.lower()
        if not paired and dna_temp in ("warm", "cool"):
            warnings.append(
                "Possible color-temperature contradiction: the analysis calls the image "
                f"'{dna.color.warm_cool_balance}'."
            )
            score -= 4

    if LIGHTING_WORDS.search(text):
        strengths.append("Concrete lighting direction present")
    if COMPOSITION_WORDS.search(text):
        strengths.append("Composition is described, not implied")
    if SPATIAL.search(text):
        strengths.append("Spatial relationships are explicit")
    if MATERIAL_WORDS.search(text):
        strengths.append("Materials/textures are specified")

    return PromptQuality(score=max(0, min(100, score)), warnings=warnings, strengths=strengths)
