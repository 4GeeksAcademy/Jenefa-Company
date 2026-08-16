# Technical Specifications: Password Recovery & Change (AUTH-03)

## 1. Architectural System Architecture
The system establishes three distinct endpoints and their corresponding client interfaces to process self-service recoveries and authorized profile updates.

[Request Form]  ---> POST /auth/forgot-password ---> Creates Token & Emails Mobile Link[Email Context] ---> Form Route: /reset-password?token=[Reset Form]    ---> POST /auth/reset-password   ---> Validates, Hashes, Updates & Marks Used
---

## 2. Backend API Specifications & Evaluation Targets

### 2.1 Password Reset Initiation Request
* **Endpoint:** `POST /auth/forgot-password`
* **Authentication:** None (Public)
* **Payload Structure:**
  ```json
  {
    "email": "string"
  }
  ```
* **Processing Rules & Evaluation Metrics:**
  1. Parse request context to pull the `email` property.
  2. Query user records to check account existence.
  3. **Evaluation Target (No Information Leaked):** The endpoint **must return a HTTP 200 response even when the address is not registered**.
  4. **Evaluation Target (Real Email Dispatch):** If the email is registered in our database, the system must trigger a real email containing the functional reset link via the integrated transaction service.
  5. Structure the absolute reset link using the format: `https://<domain>/reset-password?token=<token>`. Tokens must expire reliably after their configured time window.
* **Response Status:** `200`

### 2.2 Complete Password Reset Operation
* **Endpoint:** `POST /auth/reset-password`
* **Authentication:** None (Public)
* **Payload Structure:**
  ```json
  {
    "token": "string",
    "new_password": "string"
  }
  ```
* **Processing Rules & Evaluation Metrics:**
  1. **Evaluation Target (Token Expiry Bounds):** The system must assert that a reset token **cannot be used after its configured expiry window has passed**.
  2. **Evaluation Target (Success Updates & Invalidation):** On success, the API must simultaneously update the database password hash **and invalidate the token**.
  3. **Evaluation Target (Error Handling):** The endpoint must explicitly **return a HTTP 400 response for expired or already-used tokens**.
  4. Cryptographically hash the validated `new_password` before storing.
* **Response Status:** `200` (Success) or `400` (Invalid, Expired, or Already-Used Tokens)

### 2.3 Profile Password Revision Request
* **Endpoint:** `POST /auth/change-password`
* **Authentication:** Mandated Session Token passed inside the standard `Authorization` header context.
* **Payload Structure:**
  ```json
  {
    "current_password": "string",
    "new_password": "string"
  }
  ```
* **Processing Rules & Evaluation Metrics:**
  1. Confirm authorization context headers are populated and intact.
  2. **Evaluation Target (Wrong Password Rejection):** The API must **reject a wrong current password with a HTTP 400 response**.
  3. Upon a valid password match, hash the `new_password` and update the user record database row.
* **Response Status:** `200` (Success) or `400` (Incorrect Current Password)

---

## 3. Frontend Component & Routing Layouts

### 3.1 Account Recovery Request Interface (`/forgot-password`)
* **Evaluation Target (Ubiquitous Message Display):** The form must **show a confirmation message after submission regardless of the result** (whether the address exists or not).
* **Interactive Behavior:**
  * Invokes the `POST /auth/forgot-password` endpoint upon client-side interaction.
  * The interface component must be explicitly disabled immediately following submission to prevent duplicate requests.
  * Exact display literal text: *"If that address is registered, you'll receive a link shortly"*

### 3.2 Recovery Completion Interface (`/reset-password`)
* **Evaluation Target (Success Pipeline):** The route must **read the token from the URL, submit the form payloads, and redirect to `/login` on success**.
* **Evaluation Target (Failure Pipeline):** If the token is invalid or expired, the UI must **show a clear error message with a visible link back to `/forgot-password`**.

### 3.3 Session Core Password Configuration Form (`/account/change-password`)
* **Evaluation Target (Input Validation & Feedback):** The interface must **validate that the new password and confirmation match**, invoke the API, and **show clear success or error feedback** depending on the network outcome.

### 3.4 Entry Gateway View Amendments (`/login`)
* **Evaluation Target (Link Visibility):** The `/login` page **must display a visible "Forgot your password?" link** that points correctly back to the `/forgot-password` interface page.

---

## 4. Environment Isolation & Configuration Documentation
* **Evaluation Target (No Hardcoded Secrets):** **No API keys can be hardcoded** anywhere in the codebase. All connection string secrets and mail tokens **must be loaded from environment variables exclusively**.
* **Deployment Documentation:** Developers must completely document the exact environment variables required by the email service inside the repository's root **`README`** or **`.env.example`** configuration blueprint.