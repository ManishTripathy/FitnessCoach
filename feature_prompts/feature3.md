Feature 3: Decide – User Choice or AI-Suggested Path

Overview

This feature represents the decision-making core of the AI Fitness Transformation Agent. At this stage, the user moves from exploration to commitment by choosing how their fitness path is selected:
	•	User-led decision: The user manually selects one of the previously generated physique paths
	•	AI-assisted decision: The user asks the AI to suggest a realistic path based on their current body and generated options

This feature does not generate new images. It reasons over existing assets and provides guidance.

⸻

Business Goal

The primary business goal of this feature is to:
	•	Reduce decision paralysis for users who feel unsure
	•	Build trust by offering realistic, time-bound guidance
	•	Position the AI as a coach, not just a generator
	•	Convert visual motivation into an actionable commitment

This feature ensures users do not abandon the journey due to uncertainty.

⸻

User Options

Option A: User Proceeds Manually
	•	User clicks on one of the three generated images:
	•	Lean & Toned
	•	Athletic Build
	•	Muscle Gain
	•	This selection indicates the chosen transformation path
	•	No AI reasoning is required

⸻

Option B: AI Suggests a Path
	•	User clicks “Ask AI to Suggest”
	•	The system sends the following to the AI:
	•	User-uploaded original image
	•	Three generated physique images
	•	AI evaluates all inputs and provides a text-only recommendation

⸻

AI Suggestion Behavior

When AI suggestion is requested, the system:

Inputs to AI
	•	Original uploaded image (current state)
	•	Generated images:
	•	Lean & Toned
	•	Athletic Build
	•	Muscle Gain

⸻

AI Output (Text Only)

The AI returns a structured, realistic assessment:
	•	Estimated time required for each physique option (e.g., N months)
	•	High-level effort comparison (e.g., consistency, intensity)
	•	A recommended short-term achievable goal

Example output structure:
	•	Lean & Toned: ~3–4 months with moderate consistency
	•	Athletic Build: ~6–8 months with strength-focused training
	•	Muscle Gain: ~9–12 months with progressive overload

AI Recommendation:

Based on your current body and realistic timelines, focusing on Lean & Toned first is the most achievable short-term goal.

⚠️ No medical, nutritional, or health guarantees are made.

⸻

Decision Finalization
	•	After either:
	•	Manual selection, or
	•	AI suggestion acceptance

The chosen path is saved as the user’s committed fitness direction.

⸻

Persistence

When a path is finalized:
	•	Selected fitness path is saved against userId
	•	Decision timestamp is recorded
	•	Feature 3 is marked as completed

This decision is immutable unless reset in a future feature.

⸻

Data Storage

Firestore / Database

Stores:
	•	userId
	•	Selected path:
	•	lean_toned | athletic_build | muscle_gain
	•	Decision source:
	•	user_selected | ai_suggested
	•	AI recommendation text (if applicable)
	•	Timestamp

⸻

Technical Architecture

Frontend
	•	Displays three generated images as selectable cards
	•	Provides Ask AI to Suggest option
	•	Shows AI recommendation clearly before confirmation

⸻

Backend / AI Integration
	•	Gemini Multimodal / Reasoning Model:
	•	Consumes original image + generated images
	•	Produces comparative, time-based reasoning

No image generation models are invoked in this feature.

⸻

Explicit Constraints
	•	❌ No new image generation
	•	❌ No workout plans
	•	❌ No nutrition guidance
	•	❌ No guarantees or medical advice

⸻

Success Criteria
	•	User selects a path manually or via AI suggestion
	•	AI provides realistic, understandable timelines
	•	Final decision is persisted
	•	User progresses to planning phase

⸻

This feature completes the decision phase and sets the foundation for workout planning in the next feature.