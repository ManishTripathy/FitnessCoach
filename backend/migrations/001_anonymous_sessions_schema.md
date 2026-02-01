# Database Schema Migration: Anonymous Sessions

## Collection: `anonymous_sessions`

This collection stores temporary session data for unauthenticated users.

### Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | String (UUID) | Unique identifier for the session (Document ID) |
| `uploaded_photo_url` | String (URL) | Public URL of the uploaded photo in Firebase Storage |
| `storage_path` | String | Internal storage path (e.g., `anonymous/{session_id}/image.jpg`) |
| `analysis_results` | Map | JSON object containing body analysis data (optional, added after analysis) |
| `created_at` | String (ISO 8601) | Timestamp of creation |
| `expires_at` | String (ISO 8601) | Expiration timestamp (7 days from creation) |
| `user_id` | String | (Added upon migration) Linked authenticated user ID |
| `migrated_at` | String (ISO 8601) | (Added upon migration) Timestamp of migration |

### TTL (Time-To-Live) Policy

- **Application Level**: The API checks `expires_at` on access. If `current_time > expires_at`, the session is treated as 404 and deleted.
- **Database Level (Optional)**: A Firestore TTL policy can be configured on the `expires_at` field to automatically delete documents.

### Migration Logic

When a user authenticates:
1. The frontend calls `/api/anonymous/migrate` with the `session_id`.
2. The backend copies the session document to `users/{uid}/scans/{session_id}`.
3. The original document in `anonymous_sessions` is deleted.
