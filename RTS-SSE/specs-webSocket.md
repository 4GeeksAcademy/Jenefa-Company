# Technical Specifications: Bidirectional WebSocket Streaming & Abort Mechanics

## 1. System Architecture & Event Protocols
+------------------+                   +----------------------+                   +---------------------+
|   Chat Client    | <--- WebSockets ->| WebSocket Controller | <--- Pub/Sub ----> |   Agent Producer    |
|   (uis/ layer)   |   (Full-Duplex)   | (services/ layer)    |  (Producer/Cons.) | (LangGraph Runtime) |
+------------------+                   +----------------------+                   +---------------------+

### Protocol Requirements
* **Transport Mechanism:** State-bound, persistent bidirectional WebSockets.
* **Decoupled Architecture:** Event production must be isolated from consumption using a structured producer/consumer or pub/sub pattern to support multi-client syncing without duplicating agent invocations.
* **Data Field Isolation:** Strictly utilize naming disciplines matching HealthCore's Part 2 `CONTEXT.md` file. Do not mix Part 1 RFP/SSE payloads.

### Contract Payloads
* `token_chunk`: Explicit text data fragment emitted iteratively during active generation.
* `interrupt`: Structural payload fired from client telling backend to abort the stream.
* `generation_interrupted`: Backend confirmation acknowledging execution drop.
* `generation_completed`: Boundary marker signifying graceful text completion.

## 2. Backend Architecture (`services/`)
### Authentication & Handshake
* **Token Verification:** Restrict endpoint access using the same JWT enforced by HealthCore's Backoffice API.
* **Ingress Transport:** Transmit the token explicitly through a query parameter (e.g., `?token=...`) or within the initial application authentication frame.
* **Rejection:** Drop unauthenticated connection attempts prior to handling any chat domain events to satisfy Claire Whitfield's data governance standards.
* **Session Binding:** Force inclusion of `session_id` and/or LangGraph `thread_id` inside the handshake URL parameter to lock connections directly to active database records.

### Execution Control & Stream Interruption
* **True Runtime Abortion:** Interruption calls must terminate the active background task or model stream natively.
* **HITL Disconnection:** Do not substitute LangGraph human-in-the-loop `interrupt()` mechanics for a network stream abort signal.
* **State Preservation:** Append an `interrupted` flag status on partial database frames. Never delete or overwrite the disrupted turn.

## 3. Frontend Implementation (`uis/`)
### Interface Behaviors
* **Typing Interface:** Append text chunks directly to the UI view model immediately upon arrival.
* **Asynchronous Inputs:** Unlock text input textboxes and send triggers during active generation frames.
* **State Interlocking:** Flag active target messages visually as broken turns immediately upon triggering interrupts.

### Fault Tolerance & Connection Resiliency
* **Stateful Rehydration:** Reconnect using progressive backoff strategies if socket dropouts occur across US/UK paths.
* **Context Preservation:** Provide identical `session_id` or `thread_id` elements during retry attempts to pull existing checkpoints and history logs.

## 4. Testing Protocols (`tests/`)
* **Contract Compliance:** Build unit test fixtures checking serialization patterns for `token_chunk`, `interrupt`, `generation_interrupted`, and `generation_completed`.
* **Flow Interruption Test:** Verify that mid-response signals kill downstream execution loops, mark states accurately, and accept new inputs.
* **Reconnection Thread Test:** Validate that connection failures followed by session retries rehydrate historical conversations cleanly rather than spawning blank screens.