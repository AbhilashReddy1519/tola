# 4. Antigravity Build Plan

Paste prompts one stage at a time. Each stage ends with a check you run yourself and a commit. Do not move on until the check passes.

## 4.0 Ground rules

- **One stage per session.** Long mixed prompts produce sprawling diffs you cannot review.
- **Always point the agent at the docs.** Every prompt below starts by naming the files to read. This keeps the schema and design from drifting.
- **Branch per stage:** `git switch -c stage-3-requests`, merge to `main` when the check passes.
- **Read the diff before committing.** Pick two functions per stage and explain them aloud. That is your viva prep.
- **If you hit a wall for more than 20 minutes,** restore the last commit and re-prompt with a narrower request instead of layering fixes.
- **If your Antigravity build lets you run agents in parallel,** the safest split is stage 4 (backend) alongside stage 6 (design layer). Keep them on separate branches and avoid touching the same files.
- `AGENTS.md` at the repo root holds standing rules. If Antigravity offers workspace rules or custom instructions, paste its contents there as well. The exact setting name may differ by version.

## 4.1 Time plan

| Block | Stages | Target |
|---|---|---|
| Day 1 morning | 0, 1, 2 | Auth, roles, tokens, base layout |
| Day 1 afternoon | 3, 4 | Instruments, requests, assignment, inspection |
| Day 1 evening | 5 | Certificates, PDF, QR, public verify |
| Day 2 morning | 6, 7 | Landing and dashboards design plus motion |
| Day 2 afternoon | 8, 9 | Tests, seed data, reminders |
| Day 2 evening | 10 | Polish, screenshots, viva rehearsal |

If you only have one day, drop stage 7's advanced motion, stage 9's reminders and all stretch items.

---

## Stage 0: Bootstrap

**Satisfies:** foundation.

```
Read AGENTS.md, docs/01-PRD.md and docs/02-ARCHITECTURE.md fully before writing code.

Set up the Django project in the current directory (the repo root already has docs and README):
- Project package named `tola`, apps: accounts, registry, verification, certificates, site_pages.
- Python 3.12, Django 5.2 LTS. Use requirements.txt as given and add anything missing.
- Configure python-decouple with a .env and .env.example, WhiteNoise, templates dir at /templates, static at /static.
- Set AUTH_USER_MODEL = "accounts.User" BEFORE the first migration.
- Do not create models yet beyond the custom User (fields in the architecture doc).
- Add a placeholder landing view at "/" that renders templates/base.html.

When done, run `python manage.py check` and `python manage.py migrate` and show me the output. Do not run the dev server unless needed.
```

**Check:** `python manage.py check` reports no issues, `runserver` shows a blank landing page.
**Commit:** `chore: bootstrap django project and custom user`

## Stage 1: Auth and roles

**Satisfies:** O1, FR-1, FR-2.

```
Read docs/02-ARCHITECTURE.md sections 2.2, 2.6 and 2.7.

Implement in `accounts`:
- Login, logout and owner self-registration (role forced to OWNER; users cannot choose their role).
- `RoleRequiredMixin` in accounts/mixins.py that takes `allowed_roles` and returns 403 for wrong roles and redirects anonymous users to login.
- `/app/` view that redirects to a role-specific dashboard URL (stub pages saying "Owner dashboard", "Inspector queue", "Admin console").
- A management command `create_demo_users` creating one admin, one inspector and two owners with printed credentials.
- Register User in Django admin with the role column visible.

Write tests: owner cannot open the inspector URL, anonymous user is redirected, registration cannot set role to ADMIN by posting extra fields.
Run the tests and show me the results.
```

**Check:** log in as each demo user and land on the right stub.
**Commit:** `feat(accounts): auth, roles, role mixin, demo users`

## Stage 2: Design tokens and base layout

**Satisfies:** design foundation.

```
Read docs/03-DESIGN-SYSTEM.md fully. This stage is CSS and templates only; no new models.

Create:
- static/css/tokens.css with every CSS custom property from sections 3.3 to 3.5.
- static/css/base.css: reset, typography classes (.display, .h1, .h2, .h3, .body, .small, .label), grid helpers, focus-visible ring, reduced-motion handling.
- static/css/components.css: nav rail, buttons (primary and secondary), inputs with bottom border and floating mono labels, table rows, status chip, stat block, timeline, empty state, toast. Follow the component table in section 3.6 exactly.
- templates/base.html loading Google Fonts (Inter Tight, Instrument Serif italic, Geist Mono) with preconnect and display=swap, linking the three CSS files, containing the nav rail and a content block. Include a Django messages block rendered as toasts.
- A hidden route /styleguide/ (DEBUG only) that shows every component and type size so I can review them.

No Bootstrap, no Tailwind, no external CSS frameworks. No shadows. Do not use bold for headlines.
```

**Check:** open `/styleguide/` at 390 px and 1440 px. Compare against the reference sites side by side and adjust tokens by eye.
**Commit:** `feat(ui): design tokens, base styles, components, styleguide`

## Stage 3: Registry (business and instruments)

**Satisfies:** O2, O3, O4, FR-3, FR-4.

```
Read docs/02-ARCHITECTURE.md section 2.3 (Business, Instrument).

Implement in `registry`:
- Models exactly as specified, with the UniqueConstraint on (business, serial_no) and a validator that max_capacity > 0.
- Owner-only class-based views: instrument list, create, detail, edit; business create and edit (an owner has one business for the MVP).
- Every queryset must be scoped to request.user's business. Fetching by pk without scoping is a bug; use get_object_or_404 on the scoped queryset.
- Derived status properties `current_certificate`, `status` and `days_to_expiry` on Instrument. The certificates app does not exist yet, so write them to tolerate its absence and add TODO markers.
- Templates using the components from stage 2. Include an empty state.
- Register models in admin.

Tests: owner A gets 404 for owner B's instrument URL; serial uniqueness per business; capacity validation.
```

**Check:** two owners cannot see each other's data by changing the URL.
**Commit:** `feat(registry): business and instrument CRUD with scoping`

## Stage 4: Verification workflow

**Satisfies:** O5, O6, I1 to I4, A1, FR-5 to FR-7, FR-11.

```
Read docs/02-ARCHITECTURE.md sections 2.3 to 2.5, 2.7 and 2.11.

Implement in `verification`:
- Models VerificationRequest, Inspection, TestReading, StatusEvent as specified.
- verification/services.py with `transition(request, to_status, actor, note="")`. It must validate against an ALLOWED_TRANSITIONS dict, wrap in transaction.atomic, save, and create a StatusEvent. No view may assign `.status` directly.
- verification/rules.py with the permitted-error lookup as a single table, a function `mpe_for(load, e, accuracy_class)` and `evaluate_reading(...)`. Add a comment that the table is a simplified OIML R 76-1 class III initial-verification set to be confirmed.
- Owner views: create request for one of their own instruments, list, detail with timeline from StatusEvent.
- Admin views: list open requests and an assign form. Assigning calls transition(). Only users with role INSPECTOR can be assigned.
- Inspector views: queue (assigned to me only) and the inspection form. Use HTMX so adding a reading row and recalculating error and pass or fail happens live via partial templates. The server remains the source of truth: recompute everything on submit.
- Submitting the inspection creates Inspection and TestReadings, computes the result, and calls transition() to PASSED or FAILED.

Tests: every allowed and disallowed transition; MPE at the 500e, 2000e, 10000e boundaries; zero_ok False forces FAIL; an inspector cannot open an unassigned request (404); an owner cannot request verification for someone else's instrument.
```

**Check:** run the demo flow through to PASSED and FAILED once each and read the timeline.
**Commit:** `feat(verification): requests, assignment, inspection, rules, audit log`

## Stage 5: Certificates, PDF, QR, public verify

**Satisfies:** O7, A3, P1, P2, FR-8 to FR-10.

```
Read docs/02-ARCHITECTURE.md sections 2.3 (Certificate), 2.8 and docs/03-DESIGN-SYSTEM.md section 3.8 (certificate and verify page).

Implement in `certificates`:
- Certificate model as specified. Number format TOLA-<year>-<6 digit sequence> generated safely inside a transaction. `token` is a UUID4, unique, and is the only public identifier. `state` property returns VALID, EXPIRED or REVOKED.
- Issue the certificate inside the same transaction as the PASSED transition and then transition the request to CERTIFIED. A failed inspection must never create a certificate.
- PDF view using ReportLab following the certificate layout in the design doc. Register Inter Tight and Geist Mono TTFs from static/fonts/ (download them or tell me which files to add; do not silently fall back to Helvetica). QR via qrcode pointing to SITE_URL + /v/<token>/.
- Owner of the instrument or admin may download the PDF. Everyone else gets 404.
- Public pages: /v/<token>/ and /verify/ (manual number lookup). Show the state word at display size in the semantic colour. No login required. Do not leak owner email or phone; show business name, instrument category and serial, issue and expiry dates.
- Admin revoke view with a reason; revoked certificates show REVOKED.
- Wire Instrument.current_certificate and status to the real model; remove the TODOs from stage 3.

Tests: certificate issued on pass only, unique numbers, token lookup, expired and revoked states, permission on PDF download.
```

**Check:** download a PDF, scan the QR with your phone, see VALID. Revoke it and refresh to see REVOKED.
**Commit:** `feat(certificates): issue, pdf, qr, public verification, revoke`

## Stage 6: Landing page and dashboards (design pass)

**Satisfies:** design goals in PRD 1.2.

```
Read docs/03-DESIGN-SYSTEM.md sections 3.2 to 3.8 carefully. Reference sites are Awwwards.com (Swiss editorial, Inter Tight weight 300, ink on warm gray, one orange accent) and PP Fragment (type as the only decoration).

Build, in this order, one page at a time and show me a summary after each:
1. Landing page exactly as section 3.8: hero with the italic Instrument Serif word, index of roles, how-it-works with sticky title, live ledger counters from real database counts, verify strip, cropped footer wordmark.
2. Owner dashboard: greeting, three stat blocks, hairline instrument table, deadlines rail.
3. Inspector queue and inspection form restyled per the design doc, keeping all HTMX behaviour.
4. Admin console list and assign pages.
5. Public verify page.

Constraints: reuse the components from stage 2, add no new colours, no shadows, no gradients, no icon libraries. Mobile first. Do not add motion yet.
```

**Check:** compare 390, 768 and 1440 px against section 3.10.
**Commit:** `feat(ui): landing page and role dashboards`

## Stage 7: Motion

**Satisfies:** design goals.

```
Read docs/03-DESIGN-SYSTEM.md section 3.7.

Add static/js/motion.js using GSAP, ScrollTrigger and Lenis loaded from a CDN with defer. Implement ONLY these behaviours:
- Hero headline line-mask reveal with 90 ms stagger.
- Section reveals (fade and rise 24 px, once).
- Stat counters counting up once when visible.
- Nav rail hides on scroll down and returns on scroll up.
- Underline wipe on links and the button fill transition (CSS only).
- Lenis smooth scroll on public pages only, not on the inspection form.

Everything must be inside a prefers-reduced-motion: no-preference check, and the page must be fully usable with JavaScript disabled (content visible by default, JS adds the animation classes). Do not animate layout properties; use transform and opacity only. Keep total JS under 20 KB excluding the CDN libraries.
```

**Check:** toggle reduced motion in your OS, throttle CPU in devtools, and verify there is no layout shift.
**Commit:** `feat(ui): scroll and entrance motion`

## Stage 8: Tests and hardening

```
Run the full test suite and report coverage gaps against docs/02-ARCHITECTURE.md section 2.11. Add the missing tests only; do not refactor application code. Then:
- Add `python manage.py check --deploy` and fix any warnings that apply to a production configuration via environment variables (not by weakening settings).
- Confirm every view that takes a pk uses a scoped queryset.
- Add select_related and prefetch_related to list views and show me the query counts with django.test.utils.CaptureQueriesContext for the instrument list and the admin request list.
```

**Check:** `python manage.py test` is green.
**Commit:** `test: coverage for rules, permissions, certificates; query optimisation`

## Stage 9: Seed data and reminders

**Satisfies:** O8, FR-12, FR-14.

```
Implement `python manage.py seed_demo`: one admin, two inspectors, five owners with realistic Indian shop names, 25 instruments with varied categories and capacities, requests in every status, and certificates in states VALID (several), EXPIRING (within 30 days), EXPIRED and REVOKED. It must be idempotent and print credentials.
Implement `python manage.py send_expiry_reminders` that emails owners whose certificates expire in exactly 30 and 7 days, using Django's email backend (console backend in development). Add tests.
```

**Check:** run `seed_demo` on a fresh database and click through every role.
**Commit:** `feat: demo seed and expiry reminders`

## Stage 10: Polish and handover

```
Final pass, no new features:
1. Lighthouse-style review of the landing page: fix anything below 90 performance or 95 accessibility.
2. Add 404 and 500 templates in the design language.
3. Update README with real screenshots paths, setup steps verified from a clean clone, and demo logins.
4. Remove dead code, unused imports and debug prints.
5. Write docs/CHANGELOG.md summarising what was built per stage.
```

**Check:** clone the repo into a new folder, follow the README exactly, and run the demo script from PRD 1.8.
**Commit:** `chore: final polish and docs`

---

## 4.2 Prompts for when things go wrong

| Problem | Prompt |
|---|---|
| Agent rewrote too much | `Revert to the last commit. Re-do only <specific change> and touch no other files.` |
| Visual output looks generic | `Compare templates/<page>.html against docs/03-DESIGN-SYSTEM.md 3.5 and 3.6. List every deviation, then fix them. No new colours or shadows.` |
| Query count too high | `Show the SQL queries for <view>. Fix N+1 with select_related or prefetch_related and show before and after counts.` |
| Migration conflict | `Show me the migration plan with makemigrations --dry-run before creating anything. Do not delete existing migrations.` |
| You do not understand a block | `Explain lines X to Y as if I must defend them in a viva. Include what breaks if I remove them.` |

## 4.3 Definition of done

- [ ] Full demo script (PRD 1.8) runs without a hiccup
- [ ] `python manage.py test` passes
- [ ] No secrets in git history
- [ ] README works from a clean clone
- [ ] Design checklist (3.10) ticked
- [ ] You can answer every question in docs/05-VIVA-PREP.md
