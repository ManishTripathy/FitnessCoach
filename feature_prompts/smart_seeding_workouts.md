Workout Difficulty & Metadata Enrichment (LLM-Assisted)

This document defines additional metadata fields to be generated during workout seeding.
These fields are inferred using an LLM-assisted classifier based on YouTube video metadata (title, description, duration, tags if available).

The goal is to provide:

Explainable workout difficulty

Structured equipment data

A clean, user-friendly workout title for frontend display

1. Additional Document Fields

Each workout document should include the following new fields:

{
  "display_title": "20 Min HIIT Full Body",
  "difficulty": "Intermediate",
  "difficulty_score": 4,
  "difficulty_reason": ["HIIT workout", "30+ minute duration"],
  "equipments": ["Dumbbells"]
}

2. Field Definitions & Inference Logic
2.1 display_title

Type: string
Required: Yes

Purpose:
A short, clean, frontend-friendly title that summarizes the workout.
This is not the original YouTube title.

Inference Guidelines (LLM):

Max ~5–7 words

Remove:

Trainer name

Emojis

Marketing phrases (“You won’t believe”, “Brutal”, etc.)

Episode numbers

Keep:

Duration (rounded minutes)

Workout type

Primary focus

Examples:

"20 Min HIIT Full Body"

"45 Min Strength Upper Body"

"15 Min Low Impact Core"

"30 Min Dumbbell Legs"

2.2 difficulty

Type: string
Allowed Values: "Beginner" | "Intermediate" | "Advanced"
Required: Yes

Purpose:
Human-readable difficulty level derived from difficulty_score.

Inference Rules:

Based on final difficulty_score (see below)

Must be consistent with the score range

2.3 difficulty_score

Type: number (integer)
Range: 0 – 10
Required: Yes

Purpose:
A normalized numeric representation of workout difficulty used for ranking, filtering, and personalization.

Inference Signals (LLM should consider all that apply):

A. Duration

Shorter workouts → lower difficulty

Longer workouts → higher difficulty

B. Intensity Indicators

Keywords or phrases indicating high exertion, e.g.:

HIIT

Intense

No Rest

Burn

Tabata

AMRAP

EMOM

C. Impact Level

High impact (jumping, plyometrics) → increases difficulty

Low impact → reduces difficulty

D. Pace & Structure

Circuits with minimal rest

Timed intervals

Density-based workouts

E. Load & Resistance

Bodyweight only → neutral baseline

External resistance → increases difficulty

⚠️ Explicitly excluded:

Trainer reputation

Program or series name heuristics

2.4 difficulty_reason

Type: array<string>
Required: Yes

Purpose:
Explain why a workout was classified at a given difficulty.
Used for debugging, analytics, and potential UI explanations.

Rules:

2–4 short, human-readable reasons

Each reason should map to a concrete signal

No vague language

Examples:

[
  "HIIT workout",
  "Minimal rest intervals",
  "30+ minute duration"
]

[
  "Low impact movements",
  "Short duration workout"
]

2.5 equipments

Type: array<string>
Required: Yes (can be empty)

Purpose:
Explicit list of equipment required for the workout.

Inference Guidelines (LLM):

Infer from title and description

Normalize naming (singular, title case)

Common Values:

"Dumbbells"

"Kettlebell"

"Barbell"

"Resistance Bands"

"Yoga Mat"

"Bench"

"None" → do not include, use empty array instead

Examples:

"equipments": []

"equipments": ["Dumbbells", "Bench"]

3. Difficulty Score → Difficulty Label Mapping
Difficulty Score	Difficulty Label
0 – 2	Beginner
3 – 6	Intermediate
7 – 10	Advanced
4. Design Principles

Explainable: Every difficulty decision must be justifiable

Deterministic-ish: Similar inputs should yield similar scores

Frontend-friendly: Clean titles and normalized fields

Future-proof: Score allows later personalization or re-bucketing

5. Non-Goals

No personalized difficulty (user fitness level not considered)

No trainer-based or program-based assumptions

No reliance on YouTube engagement metrics