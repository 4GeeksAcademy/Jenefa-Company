# Technical Specifications: AUTH-02 — Frontend Authentication & Protected Views

## 1. Overview & Scope
This specification outlines the technical implementation of client-side JSON Web Token (JWT) management, route protection mechanics, and state workflows across HealthCore Digital's Next.js applications. It guarantees strict isolation of administrative and clinical functions across our 12 cross-border facilities while leaving the public marketing portal completely uninhibited.

### Application Boundaries
*   **Protected Next.js Targets**: All operational, clinical management, and administrative dashboards within the monorepo workspace.
*   **Excluded Targets (Milestone 1)**: The public website is entirely unaffected—no token evaluation, interception, or evaluation checks are allowed.

---

## 2. Token Lifecycle Management

### 2.1 Storage Configuration
*   **Mechanism**: Browser `localStorage`.
*   **Key Name**: `hc_auth_token`.
*   **Persistency**: Maintained continuously across active browser sessions until explicitly terminated via logout or invalidation hooks.

### 2.2 Dynamic Request Interception
*   **Inbound Preparation**: For every outbound request made to protected API routes, the application must read the token from `localStorage`.
*   **Header Format**: `Authorization: Bearer <token>`
*   **Absence Handling**: If the token is absent, the header signature must not be generated.

### 2.3 Automatic Session Revocation (401 Response)
*   **401 Trigger**: If any protected API call returns an HTTP status of `401`, the client must:
    1. Clear the session (`hc_auth_token`) completely from `localStorage`.
    2. Force an immediate redirect back to the `/login` view.

---

## 3. Core Authentication & Profile Views

### 3.1 Authentication Views

#### 1. `/login` (Sign-In Interface)
*   **Input Fields**: Email and password credentials form.
*   **Successful Execution**: Write the returned JWT token to `localStorage` and route the user cleanly to the primary authenticated entry view.
*   **Failure Execution**: Capture errors and display a clear, user-facing error message.

#### 2. `/register` (User Onboarding Interface)
*   **Input Fields**: Standard credential fields alongside optional profile fields.
*   **Successful Execution Sequence**:
    1. Issue a `POST /users` request with credentials and profile metrics.
    2. Upon success, immediately chain a `POST /auth/login` request with those same credentials.
    3. Store the resulting authentication token into `localStorage` and redirect to the dashboard view.
*   **Failure Execution**: Catch and display explicit, field-level validation errors.

### 3.2 Account Management View (`/account/profile`)
*   **Data Resolution**: Fetches the authenticated user metrics from the backend schema using the token in the header.
*   **Rendered Attributes**:
    *   **Email Field**: Resolved from the core `User` model entity.
    *   **Name & Contact Data**: Resolved from the linked `Profile` model entity.
*   **Profile Modifications**: Allows real-time modification of name and contact fields by transmitting data over a `PUT /profiles/me` endpoint with the token attached in the request header.
*   **Explicit Session Termination (Logout)**: Completely removes the token from `localStorage` followed by an instant client redirect to the `/login` page.

---

## 4. Route Guard Architecture

### 4.1 Client-Side Enforcement
Because Next.js server-side middleware cannot access browser-level `localStorage`, route protection must utilize a clean client-side mechanism (such as a shared custom layout guard or a dedicated hook).

```tsx
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AppRouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isVerified, setIsVerified] = useState<boolean>(false);

  useEffect(() => {
    const token = localStorage.getItem('hc_auth_token');
    if (!token) {
      router.replace('/login');
    } else {
      isVerified(true);
    }
  }, [router]);

  if (!isVerified) {
    return <div className="loading-state">Verifying session token safety layer...</div>;
  }

  return <>{children}</>;
}
```

### 4.2 Security Constraints
*   **Zero-Flash Rule**: Component trees must render a secure loading state until the presence of a token is checked. Under no circumstances should unauthenticated users see a layout flash of sensitive, protected administrative data.

---

## 5. Evaluation Verification Framework
To guarantee acceptance during final delivery reviews, the frontend implementation must pass the following structural checks:
1.  **Form Pipeline**: Login and registration forms work end-to-end, writing the token to `localStorage` immediately upon successful network resolution.
2.  **Route Protection**: Protected views instantly intercept unauthenticated traffic and force a redirect to `/login` when there is no valid token in storage.
3.  **Public Isolation**: The public website (Milestone 1) continues to work completely without any authentication checks or redirects.
4.  **Data Isolation Rules**: The profile view displays the email from the `User` model and the name/contact fields from the linked `Profile` model, with successful patch updates executed via `PUT /profiles/me`.
5.  **Clean Eviction**: Logout routines remove the token and redirect correctly.
6.  **Intercept Eviction**: Any intercepted `401` response from a protected API path instantly clears the session data and redirects the browser back to `/login`.
