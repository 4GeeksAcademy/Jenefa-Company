#  Context: Secure Authentication & Route Protection (AUTH-01)

## Strategic Objective
HealthCore Digital is transitioning its central API from an open, perimeter-less network to a zero-trust architecture. As a multi-jurisdictional company operating under HIPAA (US) and UK GDPR (UK), protecting patient, clinical, and operational data endpoints is a strict legal and security requirement. 

This project implements a stateless JSON Web Token (JWT) authentication layer. No route exposing or modifying sensitive data shall be reachable without a valid session. This security layer ensures that downstream high-stakes AI applications—such as clinical note parsing, automated billing analysis, and no-show predictions—operate on top of a completely secure data access foundation.

## User Personas & Roles
*   **Anonymous Client / External Vector**: Any unauthenticated client trying to access endpoints. Must be completely blocked from sensitive resources.
*   **User**: Standard clinical, operational, or administrative staff account. Has access to personal profile records and generic non-administrative routes.
*   **Manager**: Department head or regional overseer. Inherits standard access with elevated reading permissions.
*   **Admin**: System administrator (e.g., Executive Leadership, central tech team). Can manage global credentials, modify core resource roles, and run full administrative diagnostics.

## Scope Boundaries

### In Scope
*   **Stateless Token Auth**: Authentic sessions managed entirely via cryptographically signed JWT strings. Session-based or cookie-based state storage is explicitly forbidden.
*   **Decoupled Schema Storage**: Maintaining a dual-database architecture where `User` and `Profile` collections reside strictly within TinyDB. Other database tables (e.g., inventory, clinic operational records handled in Postgres/Supabase/SQLModel) are strictly banned from storing user entities; they must refer only to the TinyDB user `id` stored as a `user_uuid` string field.
*   **Comprehensive Core Route Hardening**: Forcing validation across all user management resources, personal profiles, and at least 5 cross-functional business routes outside the auth modules.
*   **Granular Failure Codes**: Discerning and returning distinct HTTP error states for unauthenticated requests (`401 Unauthorized`) vs. resource ownership violations (`403 Forbidden`).

### Out of Scope (Deferred to Future Tasks)
*   Frontend client integration updating (Frontend requests may break temporarily until an upcoming token header injection pipeline is deployed).
*   Automatic account locking due to repetitive failed password attempts.
*   Password reset flows using out-of-band communication tokens (SMS/Email).
