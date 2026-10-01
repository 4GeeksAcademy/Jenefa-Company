# Product Context: Real-Time Bidirectional Support Chat (HealthCore Digital)

## 1. Problem Statement & User Friction
* **The Perceived Latency Issue:** Within HealthCore's patient and operational ecosystem, users currently send support messages and wait in silence for the complete response block to generate, creating an experience that feels sluggish and detached.
* **The "Wrong Path" Obstacle:** If a support agent references the wrong market context (e.g., confusing US EHR data with UK platforms or HIPAA rules with UK GDPR guidelines), the user cannot correct it until the entire incorrect turn finishes rendering.
* **The Core Objective:** Shift the interface from an asynchronous request/response loop into a live, real-time conversation matching natural human interaction flow.

## 2. User Experience & Lifecycle
* **Live Token Streaming:** Users observe a continuous, word-by-word typing effect as responses generate.
* **Immediate Mid-Response Interruption:** Users can transmit a correction or new question mid-stream via an interrupt control.
* **Non-Destructive Interruption Representation:** Interrupted messages are preserved, visually marked as `interrupted`, and followed by a new conversational turn representing the redirected input.
* **Operational Visibility:** Support supervisors can inspect the ongoing session stream without degrading performance or triggering redundant backend executions.

## 3. Scope Boundaries & Constraints
### In-Scope
* Replacing the uni-directional SSE or HTTP loop with full-duplex WebSocket connections within the HealthCore Digital estate.
* Token-by-token streaming UI components.
* True runtime task abortion on user interruption.
* Reconnection safety nets protecting the conversation thread state across international network boundaries.

### Out-of-Scope
* Adjusting the inner reasoning logic, tools, or memory of the existing HealthCore support agent.
* Modifying underlying clinic EHR integration layers or data routers.
* Constructing parallel delivery applications or standalone folders outside the established architecture.

## 4. Organizational & Regulatory Alignment
* **Division:** HealthCore Digital.
* **Executive Sponsor:** Dr. Sandra Okonkwo (CEO), demanding precise, evidence-driven technology executions.
* **Compliance Gatekeepers:** Claire Whitfield (Compliance & Data Governance), enforcing strict data flow separation under HIPAA (US) and UK GDPR (UK).
