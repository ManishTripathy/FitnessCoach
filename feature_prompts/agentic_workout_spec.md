# Agentic Workout Interaction Spec (Feature F4)

## Overview

This document defines the initial agentic interaction flow for the AI
fitness coach. The system starts when a user sends a message from a
specific workout chat. The agent must classify intent and route the
message to the correct tool.

For the current scope, only the following features are to be implemented:

1.  Intent Detection & Routing
2.  Adaptive Workout Adjustment
3.  Opik integration


Other intents exist in the architecture but are out of scope for this
implementation.

------------------------------------------------------------------------

## To be Implemented Features

### 1. Intent Detection & Routing

**Description**

When a user sends a message from a workout chat head, the system
classifies the message into a coaching intent and routes it to the
appropriate agent tool.

The classifier operates on:

-   User message
-   Current workout context (day index, workout metadata)
-   Weekly plan snapshot

**Supported Intent (Current Scope)**

-   `ADJUST_WORKOUT`: User requests changes to the workout (shorter
    duration, easier intensity, or modification).

**Other Intents (Defined but Not Implemented Yet)**

-   Motivation & accountability
-   Weekly progress review
-   Workout explanation

These intents are recognized conceptually but are not routed to active
tools in this version.

------------------------------------------------------------------------

### 2. Adaptive Workout Adjustment

**Description**

When the intent is classified as `ADJUST_WORKOUT`, the Adaptive
Adjustment Tool updates the selected workout while preserving weekly
balance.

The agent must:

-   Modify only the affected day
-   Ensure muscle group distribution and intensity balance are preserved
-   Avoid overloading adjacent days

**Inputs**

-   Current weekly plan
-   Selected workout (day index)
-   User message
-   Adjustment constraints (e.g., time or difficulty)

**Outputs**

-   Updated workout for the selected day
-   Updated weekly plan structure
-   Short explanation of the adjustment
-   UI summary of changes

------------------------------------------------------------------------

## Interaction Flow

1.  User opens chat from a specific workout.
2.  User sends a message requesting a change.
3.  Intent classifier detects `ADJUST_WORKOUT`.
4.  Adaptive Adjustment Tool generates an updated plan.
5.  UI displays a summary of what changed.
6.  User can accept or continue chatting.

------------------------------------------------------------------------

## Example User Messages

### Example 1

**User:** "I only have 20 minutes today."

**Agent Action:**

-   Shortens Day 5 workout
-   Keeps overall weekly intensity balanced

**UI Summary Example:**

> Day 5 workout shortened to a 20‑minute session. Weekly intensity
> balance preserved.

------------------------------------------------------------------------

### Example 2

**User:** "This is too hard for today."

**Agent Action:**

-   Replaces workout with lower‑intensity alternative
-   Ensures adjacent days remain balanced

**UI Summary Example:**

> Day 3 switched to a lower‑intensity workout. Weekly balance
> maintained.

------------------------------------------------------------------------

## UI Requirements

After adjustment, the UI must show:

-   Highlighted updated workout
-   A concise change summary
-   Confirmation that weekly balance is preserved

No workout swapping between days is implemented in this version.

------------------------------------------------------------------------

## Non‑Goals (Current Version)

-   Workout swapping across days
-   Multi‑agent coordination
-   Long‑term coaching memory
-   Weekly progress analytics
-   Motivation coaching flows

These are reserved for future iterations.

------------------------------------------------------------------------

## Architecture Summary

    User Message
       ↓
    Intent Classifier
       ↓
    Adaptive Workout Adjustment Tool
       ↓
    Updated Weekly Plan + UI Summary

This architecture establishes the foundation for future agentic
extensions.
