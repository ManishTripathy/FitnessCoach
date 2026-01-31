# Feature 1: Observe - Implementation Plan

## 1. Overview
This feature implements the "Observe" phase where users log in, upload a body image, receiving an AI-based body analysis, and view generated future physique potentials.

## 2. Architecture & Tech Stack
- **Frontend**: React + Vite + DaisyUI
  - Firebase SDK for Client-side Auth and Storage.
- **Backend**: FastAPI
  - Firebase Admin SDK for Token Verification and Firestore operations.
  - Google Gen AI SDK (Gemini) for Body Analysis.
  - *Image Generation Model* (Nana Banana) for Physique Generation.
- **Database**: Firestore (User data, Analysis results).
- **Storage**: Firebase Storage (User images, Generated images).

## 3. Implementation Phases

### Phase 1: Authentication & Setup
**Goal**: Secure the app and allow user identification.
1.  **Frontend**:
    -   Install `firebase` SDK.
    -   Initialize Firebase App (using env vars).
    -   Create `AuthProvider` context.
    -   Build `Login` page using DaisyUI (Email/Password).
2.  **Backend**:
    -   Create `deps.py` for verifying Firebase ID Tokens in FastAPI routes.
    -   Protect `api/v1/*` routes.

### Phase 2: Image Upload (Frontend -> Firebase Storage)
**Goal**: Get the user's image into the cloud.
1.  **Frontend**:
    -   Create `ImageUpload` component.
    -   Validate file type (JPG/PNG) and size.
    -   Upload to path: `/users/{userId}/observe/original.jpg`.
    -   Get Download URL.

### Phase 3: AI Body Analysis (Backend)
**Goal**: Analyze the user's current physique.
1.  **Backend**:
    -   Endpoint: `POST /api/v1/observe/analyze`
    -   Input: `image_url`
    -   Logic:
        -   Download/Stream image to Gemini Vision.
        -   Prompt: "Analyze body type, general observations, neutral tone. No medical advice."
    -   Output: JSON with analysis text.

### Phase 4: Future Physique Generation (Backend)
**Goal**: Generate motivational future images.
1.  **Backend**:
    -   Endpoint: `POST /api/v1/observe/generate`
    -   Input: `image_url`, `current_analysis`
    -   Logic:
        -   Call Image Generation Service (Nana Banana / Placeholder).
        -   Generate 3 variants: Lean & Toned, Athletic Build, Muscle Gain.
        -   Upload generated images to Firebase Storage (if model returns raw bytes) or save URLs.
    -   Output: List of 3 image URLs.

### Phase 5: Persistence & UI Integration
**Goal**: Save progress and allow resuming.
1.  **Firestore Schema**:
    ```json
    users/{userId}
    {
      "observe": {
        "original_image_url": "...",
        "analysis_text": "...",
        "generated_images": [
           { "type": "lean", "url": "..." },
           { "type": "athletic", "url": "..." },
           { "type": "muscle", "url": "..." }
        ],
        "status": "completed", // or "in_progress"
        "timestamp": "..."
      }
    }
    ```
2.  **Frontend**:
    -   Display Analysis Text and Images in a nice DaisyUI layout.
    -   "Regenerate" button (calls Generation API again).
    -   "Continue" button (Saves state to Firestore via Backend endpoint `POST /api/v1/observe/complete`).

## 4. Key Questions / Clarifications
-   **Nana Banana Model**: Need to confirm specific API details or SDK for this image generation model. Will use a placeholder or standard Gemini/Imagen if specific details aren't available immediately.
-   **Storage Rules**: Need to configure Firebase Storage rules to allow authenticated read/write for own paths.

## 5. Execution Order
1.  Frontend Auth & UI Shell.
2.  Backend Auth Middleware.
3.  Image Upload Logic.
4.  Backend Analysis Endpoint (Gemini).
5.  Backend Generation Endpoint.
6.  Wiring it all together.
