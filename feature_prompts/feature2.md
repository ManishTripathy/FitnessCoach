Feature 2: Decide – Persist Progress & Continue

Overview

This feature represents the Decide step of the AI Fitness Transformation Agent. The purpose of this step is not to introduce new AI generation, but to lock in the user’s progress from Feature 1 and allow them to safely continue their journey later.

This feature ensures continuity: once the user decides to continue, their uploaded image and generated images are persisted and restored across sessions.

⸻

Business Goal

The primary business goal of this feature is to:
	•	Prevent user frustration caused by lost progress
	•	Increase trust by making the experience feel reliable and stateful
	•	Encourage commitment by turning exploration into a deliberate decision
	•	Enable multi-session journeys instead of single-session demos

This feature converts curiosity into intent by saving progress explicitly.

⸻

User Flow
	1.	User completes Feature 1 (image upload + analysis + generated images)
	2.	User reviews the body analysis and generated future physique images
	3.	User clicks the Continue button
	4.	Application saves the current state against the user account
	5.	User may log out or close the app
	6.	Upon logging back in, the user resumes from this saved state

⸻

Functional Requirements

Continue Action
	•	A single Continue button is displayed
	•	Clicking Continue triggers persistence of the current state
	•	No new AI generation occurs in this feature

⸻

Persistence Behavior

When the user clicks Continue, the system must save:
	•	Reference to the original uploaded image
	•	References to the three generated physique images:
	•	Lean & Toned
	•	Athletic Build
	•	Muscle Gain
	•	AI-generated body analysis text
	•	Feature completion status (Feature 2 completed)

This data is associated with the authenticated userId.

⸻

Session Restoration

When a user logs in:
	•	System checks if Feature 2 is completed
	•	If completed:
	•	Previously uploaded image is loaded
	•	Previously generated images are displayed
	•	No regeneration is allowed
	•	User continues from this saved state

⸻

Explicit Constraints
	•	❌ No image regeneration
	•	❌ No fitness goal selection
	•	❌ No workout planning
	•	❌ No AI model calls

This feature is strictly about decision and persistence, not generation.

⸻

Data Storage

Firebase Storage
	•	Images are already stored during Feature 1
	•	Feature 2 does not upload new images
	•	Only confirms and references existing stored assets

Storage paths remain unchanged:

/users/{userId}/observe/original.jpg
/users/{userId}/observe/generated/lean.png
/users/{userId}/observe/generated/athletic.png
/users/{userId}/observe/generated/muscle.png


⸻

Firestore / Database

Stores:
	•	userId
	•	URLs for:
	•	Original image
	•	Generated images
	•	Body analysis text
	•	Feature state:
	•	observeCompleted: true
	•	decideCompleted: true
	•	Timestamp of continuation

⸻

Technical Architecture

Frontend
	•	Displays previously generated images and analysis
	•	Continue button with loading and success states
	•	No regeneration controls shown

⸻

Backend
	•	Validates authenticated user session
	•	Writes feature completion state to database
	•	Ensures idempotency (multiple clicks do not duplicate data)

⸻

Authentication
	•	Firebase Authentication required
	•	All persistence tied to authenticated userId

⸻

Out of Scope
	•	Selecting a fitness goal
	•	Modifying generated images
	•	Re-running AI models
	•	User input beyond clicking Continue

⸻

Success Criteria
	•	User clicks Continue and data is persisted
	•	User logs out and logs back in successfully
	•	Uploaded image and generated images are restored
	•	User resumes without data loss or regeneration

⸻

This feature completes the Decide phase and prepares the system for the next phase: Goal Selection & Planning.