Weekly Workout Plan Generation — Google ADK Tech Spec
Overview

This document defines the new architecture for weekly workout plan generation using Google ADK, replacing the current single-pass LLM approach.

The new system follows a multi-agent, tool-driven RAG pipeline that:

Separates planning, retrieval, and selection concerns

Uses embeddings for semantic workout retrieval

Produces explainable, balanced, and goal-aligned weekly plans

Is fully traceable via Opik

This design is intended to be implemented incrementally using tools like Cursor IDE.

Current State (Context)
Existing Behavior

All workouts are fetched from Firestore (no vector search)

A single LLM prompt:

Sees the full workout list

Selects workouts

Generates the weekly plan in one step

Limitations

No semantic retrieval

Poor scalability beyond small libraries

Weak enforcement of variety and constraints

LLM overloaded with multiple responsibilities

Target Architecture (Proposed)

The new system breaks plan generation into distinct agents and tools, orchestrated via a Sequential ADK Agent, inspired by:

https://gist.githubusercontent.com/vincentkoc/638f11fcb00d0351473be5a8705d4c08/raw/a2ca4d974b717ba20928f3045fd2b2d739a51b1c/recipe_agent.py

High-Level Flow
User Goal
   ↓
Agent 1: Weekly Plan Skeleton
   ↓
Tool: Daily Retrieval Query Generator
   ↓
Tool: Firebase Vector Search (per day)
   ↓
Agent 2: Workout Selection & Plan Assembly
   ↓
Final Weekly Plan (JSON + Natural Language Notes)


Each step is independently testable and Opik-traced.

Agent & Tool Specifications
Agent 1 — Weekly Plan Skeleton Generator
Role

Expert Fitness Coach / Trainer

Responsibility

Create a high-level weekly training structure based on the user’s goal and analysis results.

This agent does not select specific workouts.

Inputs

user_goal (e.g., "lean", "muscle", "general fitness")

analysis_results (output of /analyse, e.g. fitness level, constraints)

Output (JSON Only)
{
  "weekly_intent": "Lean fat loss with balanced recovery",
  "days": [
    {
      "day": 1,
      "day_name": "Monday",
      "workout_type": "Strength",
      "primary_focus": ["Full Body"],
      "duration_range": "30-45",
      "equipment": ["Dumbbells"]
    }
  ]
}

Prompt (Agent 1)

System Role
You are an expert fitness coach designing a structured weekly training plan.

Instructions

Output a 7-day structure (Monday–Sunday)

Define workout intent per day, not specific workouts

Balance intensity and recovery

Avoid repeating the same primary focus on consecutive days

Include 1–2 rest or active recovery days if appropriate

Do NOT reference specific workouts or IDs

Opik

Agent name: weekly-plan-skeleton-agent

Tags: ["weekly-plan", "skeleton", "fitness-coach"]

Tool 1 — Daily Retrieval Query Generator
Type

Deterministic Tool (No LLM Creativity)

Responsibility

Convert each day’s plan into a semantic retrieval query aligned with the embedding schema.

Input

Single day object from Agent 1.

Output (Text for Embedding)
Workout type: Strength
Primary focus: Legs, Glutes
Difficulty: Intermediate
Duration: 30–45 minutes
Impact: Moderate
Equipment: Dumbbells

Notes

This query must follow the same structured format as workout embeddings

No marketing language

No trainer or program references

Opik

Tool name: daily-retrieval-query-builder

Tags: ["retrieval", "embedding-query"]

Tool 2 — Firebase Vector Search (Per Day)
Type

Retrieval Tool

Responsibility

Retrieve top-K workout candidates for each day using vector similarity.

Inputs

Query embedding (from Tool 1)

Metadata filters:

Difficulty range

Duration bounds

Equipment availability

Output
[
  {
    "id": "workout_id",
    "display_title": "30 Min Dumbbell Legs",
    "difficulty": "Intermediate",
    "difficulty_score": 5,
    "focus": ["Legs", "Glutes"]
  }
]

Notes

Embeddings represent training intent, not descriptions

Hard constraints are enforced before similarity scoring

Opik

Tool name: firebase-workout-vector-search

Tags: ["vector-search", "firebase"]

Agent 2 — Workout Selection & Plan Assembly
Role

Head Coach & Plan Assembler

Responsibility

From retrieved candidates:

Select 1 workout per day

Ensure weekly balance and variety

Avoid repeating the same focus on consecutive days

Add human-readable reasoning

Inputs

Weekly skeleton (Agent 1)

Retrieved workout candidates (per day)

Output (Final JSON)
- MUST have same structure as for existing /generate-plan response

Sample response
{
    "status": "exists",
    "plan": {
        "generated_at": "2026-02-08T12:34:26.181264",
        "schedule": [
            {
                "workout_id": "8twRGtpr48w",
                "day": 1,
                "notes": "High-intensity full body workout to kickstart the week with calorie burn and muscle engagement.",
                "is_rest": false,
                "day_name": "Monday",
                "activity": "60 Min Full Body HIIT Workout",
                "workout_details": {
                    "equipments": [],
                    "display_title": "60 Min Full Body HIIT Workout",
                    "difficulty_score": 7,
                    "difficulty": "Advanced",
                    "title": "60 Minute Full Body HIIT Workout | Summertime Fine 3.0 - Day 34",
                    "playlist_id": "PLE5lGVrS3V9ch3kAxWpqwDMkoNg6bal-3",
                    "id": "8twRGtpr48w",
                    "duration_mins": 62,
                    "focus": [
                        "Full Body",
                        "HIIT",
                        "Cardio"
                    ],
                    "difficulty_reason": [
                        "60+ minute duration",
                        "HIIT intervals"
                    ],
                    "description": "From program: 60 Minute Workouts. 60 Minute Full Body HIIT Workout | Summertime Fine 3.0 - Day 34 - Welcome to DAY 34 OF Summertime Fine 3.0! Please subscribe to the channel at the link here! www.yout...",
                    "url": "https://www.youtube.com/watch?v=8twRGtpr48w",
                    "thumbnail": "https://i.ytimg.com/vi/8twRGtpr48w/hqdefault.jpg",
                    "trainer": "Sydney Cummings"
                }
            },
            {
                "workout_id": "GFvqGKqaYgE",
                "day": 2,
                "notes": "Targets upper body and core for strength and definition.",
                "is_rest": false,
                "day_name": "Tuesday",
                "activity": "40 Min Arms and Abs Bootcamp",
                "workout_details": {
                    "equipments": [],
                    "display_title": "40 Min Arms and Abs Bootcamp",
                    "difficulty_score": 6,
                    "difficulty": "Intermediate",
                    "title": "Strong and Sculpted Arms and Abs Bootcamp Workout | PRIME - Day 2",
                    "playlist_id": "PLE5lGVrS3V9em94a4J2f6TaWVt0-HY0cS",
                    "id": "GFvqGKqaYgE",
                    "duration_mins": 44,
                    "focus": [
                        "Core",
                        "Abs",
                        "Upper Body",
                        "Arms"
                    ],
                    "difficulty_reason": [
                        "45+ minute duration",
                        "Supersets",
                        "Three rounds per exercise"
                    ],
                    "description": "From program: PRIME. Strong and Sculpted Arms and Abs Bootcamp Workout | PRIME - Day 2 - Are you ready to get lean arms and strong abs? Let's challenge your body with PRIME's 40-minute Uppe...",
                    "url": "https://www.youtube.com/watch?v=GFvqGKqaYgE",
                    "thumbnail": "https://i.ytimg.com/vi/GFvqGKqaYgE/hqdefault.jpg",
                    "trainer": "Sydney Cummings"
                }
            },
            {
                "workout_id": "MqAcQeDGysg",
                "day": 3,
                "notes": "Intense leg workout to build lower body strength and muscle.",
                "is_rest": false,
                "day_name": "Wednesday",
                "activity": "60 Min Legs Workout",
                "workout_details": {
                    "equipments": [],
                    "display_title": "60 Min Legs Workout",
                    "difficulty_score": 7,
                    "difficulty": "Advanced",
                    "title": "60 Minute Legs Workout | Summertime Fine 2.0 - Day 68",
                    "playlist_id": "PLE5lGVrS3V9ch3kAxWpqwDMkoNg6bal-3",
                    "id": "MqAcQeDGysg",
                    "duration_mins": 65,
                    "focus": [
                        "Legs",
                        "Glutes"
                    ],
                    "difficulty_reason": [
                        "60+ minute duration",
                        "Body weight only"
                    ],
                    "description": "From program: 60 Minute Workouts. 60 Minute Legs Workout | Summertime Fine 2.0 - Day 68 - Welcome to your workout!! PLEASE CLICK HERE and subscribe! We are on the road to 1 million! https://...",
                    "url": "https://www.youtube.com/watch?v=MqAcQeDGysg",
                    "thumbnail": "https://i.ytimg.com/vi/MqAcQeDGysg/hqdefault.jpg",
                    "trainer": "Sydney Cummings"
                }
            },
            {
                "workout_id": "CR4X4XwlA_c",
                "day": 4,
                "notes": "Shorter HIIT session to maintain intensity without overtraining.",
                "is_rest": false,
                "day_name": "Thursday",
                "activity": "30 Min HIIT Full Body",
                "workout_details": {
                    "equipments": [],
                    "display_title": "30 Min HIIT Full Body",
                    "difficulty_score": 6,
                    "difficulty": "Intermediate",
                    "title": "30 Minute FAT-BURNING HIIT WORKOUT! 🔥Burn 450 Calories 🔥Sydney Cummings",
                    "playlist_id": "PLE5lGVrS3V9cb7OHogkQFzjH1Gzdb4iaT",
                    "id": "CR4X4XwlA_c",
                    "duration_mins": 32,
                    "focus": [
                        "HIIT",
                        "Cardio"
                    ],
                    "difficulty_reason": [
                        "30+ minute duration",
                        "HIIT intervals",
                        "Body weight only"
                    ],
                    "description": "From program: Full Body Workouts. 30 Minute FAT-BURNING HIIT WORKOUT! 🔥Burn 450 Calories 🔥Sydney Cummings - This total body workout may be my new favorite workout! I loved all the exercises today because they...",
                    "url": "https://www.youtube.com/watch?v=CR4X4XwlA_c",
                    "thumbnail": "https://i.ytimg.com/vi/CR4X4XwlA_c/hqdefault.jpg",
                    "trainer": "Sydney Cummings"
                }
            },
            {
                "workout_id": "46cYfOOwNc4",
                "day": 5,
                "notes": "Focuses on back, biceps, and core for balanced strength and definition.",
                "is_rest": false,
                "day_name": "Friday",
                "activity": "44 Min Dumbbell Back, Biceps, Core",
                "workout_details": {
                    "equipments": [
                        "Dumbbells",
                        "Yoga Mat",
                        "Yoga Block"
                    ],
                    "display_title": "44 Min Dumbbell Back, Biceps, Core",
                    "difficulty_score": 6,
                    "difficulty": "Intermediate",
                    "title": "FUNDAMENTAL Back, Biceps and Core Workout - Dumbbells | EPIC III Day 6",
                    "playlist_id": "PLamoA-6M6N6HBIJX2EGNlxtaRBYHGkTRX",
                    "id": "46cYfOOwNc4",
                    "duration_mins": 44,
                    "focus": [
                        "Core",
                        "Abs"
                    ],
                    "difficulty_reason": [
                        "45+ minute duration",
                        "Dumbbells",
                        "Core strengthening exercises"
                    ],
                    "description": "From program: CG-Back/Bicep. FUNDAMENTAL Back, Biceps and Core Workout - Dumbbells | EPIC III Day 6 - The back, biceps and core will be targeted in this workout with dumbbells and bodyweight with unilat...",
                    "url": "https://www.youtube.com/watch?v=46cYfOOwNc4",
                    "thumbnail": "https://i.ytimg.com/vi/46cYfOOwNc4/hqdefault.jpg",
                    "trainer": "Caroline Girvan"
                }
            },
            {
                "workout_id": "SxX-4qB7Vf8",
                "day": 6,
                "notes": "Maximize calorie burn and cardiovascular fitness with a high-intensity HIIT workout.",
                "is_rest": false,
                "day_name": "Saturday",
                "activity": "40 Minute All Out HIIT",
                "workout_details": {
                    "equipments": [],
                    "display_title": "40 Minute All Out HIIT",
                    "difficulty_score": 7,
                    "difficulty": "Advanced",
                    "title": "GRAND FINALE WORKOUT - 40 Minute All Out HIIT!",
                    "playlist_id": "PLE5lGVrS3V9erP7lssSatLqgCVA2-ZGvh",
                    "id": "SxX-4qB7Vf8",
                    "duration_mins": 44,
                    "focus": [
                        "HIIT",
                        "Cardio"
                    ],
                    "difficulty_reason": [
                        "45+ minute duration",
                        "HIIT intervals"
                    ],
                    "description": "From program: BOLD. GRAND FINALE WORKOUT - 40 Minute All Out HIIT! - It's the final workout of the BOLD program-we've made it! Let this be a celebration of all you have ...",
                    "url": "https://www.youtube.com/watch?v=SxX-4qB7Vf8",
                    "thumbnail": "https://i.ytimg.com/vi/SxX-4qB7Vf8/hqdefault.jpg",
                    "trainer": "Sydney Cummings"
                }
            },
            {
                "day": 7,
                "notes": "Allows the body to recover and rebuild after a week of intense training. Focus on stretching and light activity.",
                "workout_id": null,
                "day_name": "Sunday",
                "activity": "Rest Day",
                "is_rest": true
            }
        ],
        "weekly_focus": "This week focuses on high-intensity interval training (HIIT) and strength training to maximize fat loss and muscle definition, aligning with the client's goal to get 'shredded'. The schedule incorporates full-body workouts with targeted sessions for upper body, core, and legs to ensure balanced development and recovery."
    }
}

Prompt (Agent 2)

System Role
You are a senior fitness coach finalizing a weekly workout plan.

Instructions

Select exactly one workout per non-rest day

Prefer variety across the week

Avoid same primary focus on back-to-back days

Use rest days strategically

Explain the reasoning for each selection

Output JSON only

Opik

Agent name: weekly-plan-assembler-agent

Tags: ["weekly-plan", "selection", "assembly"]

Sequential Agent Orchestration

A Sequential ADK Agent orchestrates:

weekly-plan-skeleton-agent

daily-retrieval-query-builder (per day)

firebase-workout-vector-search (per day)

weekly-plan-assembler-agent

Each step:

Passes structured outputs forward

Is individually traceable in Opik

Can be debugged or replaced independently