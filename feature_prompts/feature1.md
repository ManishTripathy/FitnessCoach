Feature 1: Observe – User Login, Image Upload & AI Body Analysis

Overview

This feature represents the Observe step of the AI Fitness Transformation Agent. It establishes the user’s starting point by collecting a photo, analyzing the body visually, and generating future physique options. This feature intentionally stops before goal selection, which will be handled in the next phase.

⸻

Business Goal

The primary business goal of this feature is to:
	•	Create a strong first impression using AI-powered visual feedback
	•	Help users understand their current physique without overwhelming them
	•	Increase user commitment by showing visually compelling future possibilities
	•	Persist user progress so they can safely return without restarting

This feature is designed to maximize activation and motivation, which are critical for user retention in fitness applications.

⸻

User Flow
	1.	User logs in to the web application
	2.	User uploads a front-facing body image
	3.	AI analyzes the uploaded image and generates:
	•	A textual body analysis
	•	Three future physique images
	4.	User views the analysis and generated images
	5.	User may regenerate the future images if desired
	6.	User clicks Continue to persist the results and move forward later

At this stage, the user does not select a fitness goal.

⸻

Functional Requirements

Authentication
	•	Users must be authenticated before uploading images
	•	Authentication will be handled using Firebase Authentication
	•	Supported login methods (initial):
	•	Email + Password


⸻

Image Upload
	•	User uploads a single front-facing image
	•	Basic client-side validation:
	•	Image file only (JPG / PNG)
	•	Max size limit enforced
	•	Uploaded image is stored in Firebase Storage under the user’s ID

⸻

AI Body Analysis (Text)

After upload, the system generates a textual body analysis, such as:
	•	Overall body type classification (e.g., lean, average, overfat)
	•	General observations (non-medical, non-judgmental)
	•	Neutral and motivational tone

⚠️ No health claims, BMI, or medical advice are generated.

⸻

Future Physique Image Generation

Using the uploaded image as a reference, the system generates three future physique images:
	1.	Lean & Toned
	2.	Athletic Build
	3.	Muscle Gain

	•	Images are generated using the Nana Banana image generation model
	•	Generated images visually resemble the user while clearly indicating a future transformation
	•	Each image is labeled clearly

⸻

Regeneration Behavior
	•	User may regenerate the three future images
	•	Regeneration replaces the previously generated images
	•	Only the latest generated set is retained unless the user clicks Continue

⸻

Persistence on Continue

When the user clicks Continue:
	•	The following data is permanently saved against the userId:
	•	Original uploaded image
	•	AI-generated body analysis text
	•	Final selected set of three generated images
	•	Data persistence ensures:
	•	User can log out
	•	Log back in later
	•	Resume exactly from this stage

⸻

Data Storage

Firebase Storage
	•	Stores:
	•	Original uploaded user image
	•	Generated future physique images
	•	Storage structure example:

/users/{userId}/observe/original.jpg
/users/{userId}/observe/generated/lean.png
/users/{userId}/observe/generated/athletic.png
/users/{userId}/observe/generated/muscle.png



⸻

Firestore / Database
	•	Stores metadata and analysis results:
	•	User ID
	•	Image URLs
	•	Body analysis text
	•	Timestamp
	•	Completion status of Feature 1

⸻

Technical Architecture

Frontend
	•	Responsive web application
	•	Image upload UI with preview
	•	Loading states for analysis and generation
	•	Clear regeneration and continue actions

⸻

Backend / AI Integration
	•	Gemini Vision (or equivalent):
	•	Analyze the uploaded image
	•	Generate textual body analysis
	•	Nana Banana Image Generation Model:
	•	Generate three future physique images using the uploaded photo as reference

⸻

Authentication
	•	Firebase Authentication
	•	User session required before image upload

⸻

Storage & Persistence
	•	Firebase Storage for image assets
	•	Firestore (or equivalent) for structured user progress data

⸻

Out of Scope (Explicitly Not Included)
	•	Fitness goal selection
	•	Workout generation
	•	Exercise tracking
	•	Nutrition, calories, or macros
	•	Medical or health diagnostics

⸻

Success Criteria
	•	User successfully logs in and uploads an image
	•	AI analysis text is generated and displayed
	•	Three future physique images are generated
	•	User can regenerate images
	•	User progress persists across logout/login

⸻

This feature completes the Observe phase and prepares the user for goal selection in the next feature.