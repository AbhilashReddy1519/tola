# 1. Product Requirements: Tola

## 1.1 Problem

Businesses that sell by weight or measure (grocers, jewellers, fuel stations, weighbridge operators) must have their instruments verified and stamped periodically so customers are not short-changed. In India this sits under the Legal Metrology Act, 2009 and its rules.

The paper process has predictable pain points:

- Owners do not know when verification expires until an inspector turns up.
- Requests, inspector visits and results live in registers and phone calls, so nothing is traceable.
- A sticker or paper certificate is easy to copy, and a customer cannot check it.
- The controller's office cannot see which instruments are overdue.

> Confirm fee amounts, validity periods and test procedures with your faculty or the official portal. Tola keeps these configurable so nothing is hard-coded to a guess.

## 1.2 Goals and non-goals

**Goals**

1. Take one instrument through the full cycle online: register, request, assign, inspect, certify.
2. Issue certificates that anyone can verify through a public page.
3. Warn owners before certificates expire.
4. Keep an audit trail of every status change.
5. Present a design that looks deliberate and premium, not like a default Bootstrap form.

**Non-goals (say these out loud in the viva)**

- Real payment gateway (a mock fee field is enough).
- Integration with government systems.
- Hardware or IoT readings.
- Native mobile app (the site is responsive).

## 1.3 Users

| Persona | Context | Main need |
|---|---|---|
| **Business owner** (Ramesh, runs a grain shop) | Phone-first, limited patience | Know what is due and get a certificate without visiting an office |
| **Inspector** | On site with a phone or tablet | Fast data entry, clear pass or fail, no arithmetic by hand |
| **Admin** (controller's office) | Desktop | Assign work, spot overdue instruments, revoke bad certificates |
| **Public verifier** (customer, auditor) | Scans a QR | One glance: valid, expired or revoked |

## 1.4 User stories

IDs are used in the Antigravity plan so each stage can point at what it satisfies.

**Owner**
- O1: Register and log in as a business owner.
- O2: Create a business profile.
- O3: Add instruments with category, make, model, serial number, capacity and accuracy class.
- O4: See each instrument's status: *Unverified, Pending, Valid, Expiring soon, Expired, Failed, Revoked*.
- O5: Request verification for an instrument and choose a preferred date.
- O6: Follow the request through its stages with a timeline.
- O7: Download the certificate as PDF.
- O8: Receive reminders 30 and 7 days before expiry.

**Inspector**
- I1: See my assigned requests, ordered by preferred date.
- I2: Open a request and record zero check, accuracy readings, repeatability and eccentricity.
- I3: See live pass or fail per reading as I type, computed against permitted error.
- I4: Submit the inspection with remarks. A pass issues a certificate automatically.

**Admin**
- A1: See all open requests and assign each to an inspector.
- A2: See instruments expiring in the next 30 days.
- A3: Revoke a certificate with a reason.
- A4: Manage users and categories through the Django admin.

**Public**
- P1: Open `/v/<token>/` from a QR code and see the certificate status with instrument and business details.
- P2: Enter a certificate number manually to verify it.

## 1.5 Functional requirements

| ID | Requirement | Stories |
|---|---|---|
| FR-1 | Custom user model with a `role` field; owners can self-register, inspectors and admins are created by admin | O1, A4 |
| FR-2 | Role-based access on every view; querysets are scoped so users only see their own data | all |
| FR-3 | CRUD for Business and Instrument with validation (serial unique per business, capacity > 0) | O2, O3 |
| FR-4 | Derived instrument status computed from latest certificate and open request | O4 |
| FR-5 | Verification request with a defined state machine (see architecture doc) | O5, O6 |
| FR-6 | Admin assignment screen | A1 |
| FR-7 | Inspection form with dynamic readings and server-side pass or fail against a permitted-error table | I2, I3, I4 |
| FR-8 | Certificate created automatically on pass: unique number, issue date, valid-until, random public token | I4 |
| FR-9 | Certificate PDF with QR code pointing at the public verify URL | O7 |
| FR-10 | Public verify page showing Valid, Expired or Revoked with no login | P1, P2 |
| FR-11 | Audit log of every status transition with actor and timestamp | O6 |
| FR-12 | Management command that emails or logs reminders for expiring certificates | O8 |
| FR-13 | Admin dashboard with counts and an expiring-soon list | A2 |
| FR-14 | Seed command that builds a realistic demo dataset | demo |

## 1.6 Non-functional requirements

- **Security:** CSRF on all forms, `LoginRequiredMixin` plus role checks, object-level scoping to prevent one owner opening another's records by editing the URL, unguessable public tokens (UUID4), no secrets in the repo.
- **Accessibility:** WCAG AA contrast, visible focus states, semantic HTML, full keyboard use, and all motion disabled under `prefers-reduced-motion`.
- **Responsive:** designed mobile first; inspector form works one-handed at 390 px wide.
- **Performance:** no N+1 queries on list pages (`select_related`), fonts preloaded, no layout shift, Lighthouse performance 90 or higher on landing.
- **Testability:** automated tests for the state machine, pass or fail calculation, permission scoping and certificate verification.

## 1.7 MVP scope

Cut lines are drawn so something demonstrable exists at the end of every phase.

| Phase | Time (approx.) | Delivers | Done when |
|---|---|---|---|
| **MVP-0: Foundation** | 1.5 h | Project, custom user, roles, tokens CSS, base layout, landing page v1 | You can log in as each role and see a role dashboard |
| **MVP-1: Core workflow** | 4 h | Business, Instrument, VerificationRequest, assignment, Inspection with readings | A request goes from submitted to passed or failed end to end |
| **MVP-2: Trust layer** | 3 h | Certificate, PDF, QR, public verify page, audit log | Scanning the QR on a downloaded PDF opens the verify page showing *Valid* |
| **MVP-3: Polish** | 5 h | Motion, final landing, empty states, error pages, responsive pass | Passes the design checklist in doc 3 |
| **MVP-4: Hardening** | 2.5 h | Tests, seed data, reminders command, README screenshots | `python manage.py test` is green and the demo script runs clean |
| **Stretch** | if time | JSON verify API, CSV export, dark mode, charts on admin dashboard | Only after MVP-4 |

**Cut first if time runs out:** dark mode, charts, JSON API, reminders email (keep the command, print to console), custom admin console (use Django admin).

**Never cut:** the state machine, permission scoping, the public verify page, tests for the pass or fail logic.

## 1.8 Demo script (5 minutes)

1. Landing page: scroll once to show motion and typography.
2. Log in as owner, add a counter scale, request verification.
3. Log in as admin, assign the inspector.
4. Log in as inspector, enter readings, watch pass or fail update, submit.
5. Back as owner, open the certificate PDF, scan the QR with a phone.
6. Public page shows *Valid*. Log in as admin, revoke the certificate, refresh: it shows *Revoked*.

## 1.9 Risks

| Risk | Mitigation |
|---|---|
| AI-generated code you cannot explain | Read each stage's diff and use doc 5 to rehearse |
| Domain rules (permitted error) are wrong | Keep them in one lookup table, labelled as simplified, and confirm with faculty |
| Over-investing in visuals | Polish only landing, dashboard and certificate. Everything else inherits tokens |
| PDF library install pain on Windows | ReportLab is pure pip; avoid WeasyPrint |
