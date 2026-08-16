# Product Context: Password Recovery & Change (AUTH-03)

## Corporate Context & Vision
HealthCore operates a cross-border healthcare network consisting of 12 clinical clinics spanning the US and the UK. Managed via our internal department HealthCore Digital, this platform must handle sensitive patient portals safely while conforming strictly to both HIPAA and UK GDPR regulatory guidelines. Account security and reliable credential operations directly impact corporate compliance, operations, and patient protection.

## Problem Statement
The baseline authentication system lets users register, log in, and manage profiles, but has no mechanism for forgotten passwords or active session updates. Under production security compliance standards audited by Claire Whitfield's team, the platform requires absolute protection against automated account enumeration attacks and credential replay exploits.

## Grading & Technical Evaluation Criteria (AUTH-03)
To successfully pass the automated evaluation suite, our implementation guarantees:
* **Leaking Prevention:** The platform completely strips away diagnostic data on public lookups. Registered and missing accounts mirror each other precisely across the HTTP boundary.
* **Token Expiration Windows:** Expiration properties are treated as hard boundaries. A token is un-executable the instant it crosses its validity timeline.
* **Functional Dispatch Tracking:** Core infrastructure evaluations test real email dispatches containing functional links whenever triggered by an existing address.
* **Component-Level Context Loops:** Broken or stale tokens seamlessly prompt users to restart the journey without requiring manual address bar entries.

## Core Security Safeguards
To comply with the explicit security requirements of ticket AUTH-03:
1. **Anti-Replay Mechanism:** Tokens are strictly single-use. Once an account recovery is completed, that token is immediately blacklisted or invalidated. It can never be used twice.
2. **Data Leakage Mitigation:** The request flow completely hides whether an email exists in our database. It provides an identical success confirmation to every applicant to block user discovery attempts.
3. **Zero Codebase Exposure:** Third-party communication API keys must live exclusively in host machine environment configurations. Hardcoded parameters are prohibited from entering source control.

## Infrastructure Strategy
To send out reset links without custom DNS domain blocks during development, the system integrates with either **Resend** or **SendGrid (Twilio)**. These transactional services provide sandboxed single-sender verification workflows. To maintain security, infrastructure API keys must never be hardcoded and must stay completely isolated inside environment variables.
