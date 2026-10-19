# Tola Changelog

All notable changes across each development stage of Tola are documented in this file.

---

## [Stage 10] - Polish and Handover
### Added
- Created custom `404.html` and `500.html` error templates styled with the Swiss editorial design system (`var(--border-hairline)`, `Instrument Serif` italic headlines, `Geist Mono` error labels).
- Added accessible `.skip-to-content` navigation link and meta description to `templates/base.html` for WCAG AA compliance.
- Added `docs/screenshots/` catalogue index.
- Authored comprehensive `docs/CHANGELOG.md` and updated `README.md` with verified setup instructions, test commands, and demo credentials.

### Verified
- Automated test suite passes 100% green with 65 tests.
- Clean deployment check (`python manage.py check --deploy`) passes with zero issues.

---

## [Stage 9] - Seed Data and Expiry Reminders
### Added
- **`seed_demo` management command** (`verification/management/commands/seed_demo.py`):
  - Idempotent database population with 1 admin, 2 inspectors, and 5 business owners with realistic Indian business profiles.
  - Generates 25 instruments across varied categories (`COUNTER_SCALE`, `PLATFORM_SCALE`, `WEIGHBRIDGE`, `CAPACITY_MEASURE`, `LENGTH_MEASURE`), capacities, scale intervals, and accuracy classes (I, II, III).
  - Populates verification requests in every state: `SUBMITTED`, `ASSIGNED`, `CERTIFIED`, `FAILED`, and `CANCELLED`.
  - Issues certificates in all states: `VALID` (8), `EXPIRING` (4, including exact 30-day and 7-day targets), `EXPIRED` (2), and `REVOKED` (1).
  - Prints formatted credentials directory to stdout.
- **`send_expiry_reminders` management command** (`certificates/management/commands/send_expiry_reminders.py`):
  - Finds active certificates expiring in exactly 30 and 7 days.
  - Dispatches statutory notices via Django's email backend detailing instrument serial, business name, expiry date, renewal filing URL, and public verification link.
  - Supports `--dry-run` simulation mode and custom `--days` parameters.
- Comprehensive automated test coverage in `verification/tests.py` and `certificates/tests.py`.

---

## [Stage 8] - Tests and Hardening
### Added
- Production security configurations in `tola/settings.py` configurable via environment variables (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`).
- Updated `.env.example` with production configuration documentation.
- Additional test coverage against Architecture Section 2.11:
  - Scoped owner request permissions (Owner A cannot view or cancel Owner B's request, expecting 404).
  - Admin certificate revocation flow, metrological reason enforcement, and non-admin 403 access control.
- Query optimization and N+1 query elimination:
  - Added prefetched cache checks in `Instrument.current_certificate` and `Instrument.status`.
  - Cached business lookups on `InstrumentListView`.
  - Verified query counts via `django.test.utils.CaptureQueriesContext`: Admin Request List executes in **3 queries**, Owner Instrument List executes in **6 constant queries** ($O(1)$ database hits).
  - Added automated regression tests for query counts.

---

## [Stage 7] - Motion and Interactions
### Added
- Lightweight vanilla JavaScript motion controller in `static/js/motion.js` (under 5 KB):
  - GSAP headline line-mask reveals with 90ms stagger.
  - Section fade and rise entrance reveals (24px rise once at 80% viewport height).
  - Animated stat counters with integer and decimal support.
  - Smart floating navigation rail that hides on scroll down and returns on scroll up.
  - Lenis smooth scrolling applied exclusively to public pages and disabled on inspection forms.
- CSS-only underline wipes on text links and 400ms button fill transitions.
- Full accessibility compliance wrapping all motion under `prefers-reduced-motion: no-preference`.

---

## [Stage 6] - Landing and Dashboards Design Pass
### Added
- **Editorial Landing Page** (`/`):
  - Italic `Instrument Serif` hero statement with mono metadata tags.
  - Index of roles with oversized numerals `01`, `02`, `03`.
  - Sticky "How it works" four-stage verification lifecycle.
  - Live ledger counter grid showing verified instruments, active certificates, and average certification turnaround.
  - Oversized public certificate lookup strip (`/verify/`).
  - 20vw cropped footer wordmark `Tola`.
- **Owner Dashboard** (`/app/instruments/`):
  - Dynamic time-of-day greeting header.
  - Three stat blocks: *Valid*, *Expiring in 30 days*, and *Overdue*.
  - Hairline instrument table with row hover action to request verification.
  - Upcoming deadlines right rail.
- **Inspector Queue and Inspection Form**:
  - Full-screen stepped layout with live HTMX reading rows and sticky pass/fail result bar.
- **Admin Console**:
  - Central ledger for inspector dispatch and certificate oversight.
- **Public Verify Page** (`/v/<token>/`):
  - Display-size semantic status word (`VALID`, `EXPIRED`, `REVOKED`) with complete privacy protection (never leaks owner phone or email).

---

## [Stage 5] - Certificates, PDF, QR and Public Verification
### Added
- Certificate generation engine using ReportLab:
  - Embedded `Inter Tight` and `Geist Mono` TTF typography.
  - Tamper-evident 35mm scannable QR code encoding `https://<host>/v/<token>/`.
  - Sequential certificate numbering format: `TOLA-<year>-<sequence>`.
  - Public token lookup using UUID4 keys.
- Views:
  - `CertificatePDFDownloadView`: Secure download restricted to instrument owner or admin.
  - `PublicTokenVerifyView`: Public verification page.
  - `PublicManualVerifyView`: Manual certificate number search.
  - `AdminRevokeCertificateView`: Admin revocation with required audit reason.

---

## [Stage 4] - Verification Workflow and State Machine
### Added
- Request state machine service (`verification/services.py`):
  - Strict transition validator enforcing `SUBMITTED -> ASSIGNED -> PASSED/FAILED -> CERTIFIED`, with cancellation states.
  - Comprehensive `StatusEvent` audit trail capturing actor, timestamp, previous status, and notes.
- Permitted-error logic (`verification/rules.py`):
  - OIML R 76-1 / Legal Metrology Act Class III MPE limits table at 500e, 2000e, and 10000e.
  - Zero return check verification and reading error evaluations.
- Views:
  - `OwnerRequestListView`, `OwnerRequestCreateView`, `OwnerRequestDetailView`, `OwnerRequestCancelView`.
  - `AdminConsoleRequestListView`, `AdminAssignInspectorView`.
  - `InspectorQueueView`, `InspectorInspectionView`, `ReadingRowHTMXView`.

---

## [Stage 3] - Business and Instrument Registry
### Added
- `Business` and `Instrument` models with strict validation:
  - Maximum capacity strictly greater than 0.
  - `UniqueConstraint(business, serial_no)` preventing duplicate serials within the same business.
  - Derived status properties: `current_certificate`, `status`, `days_to_expiry`.
- Strictly scoped CBVs (`InstrumentListView`, `InstrumentCreateView`, `InstrumentDetailView`, `InstrumentUpdateView`, `BusinessCreateView`, `BusinessUpdateView`).

---

## [Stage 2] - Tokens and Base CSS
### Added
- Design tokens defined in `static/css/tokens.css`:
  - Monochrome ink palette, warm off-white canvas, hairline borders, semantic green/yellow/red chips.
  - Fluid typography scale (`clamp`) and spacing variables.
- Base reset and layout rules in `static/css/base.css`.
- UI component classes in `static/css/components.css`:
  - Buttons, hairline tables, status chips, floating nav rail, and form controls.

---

## [Stage 1] - Authentication and Role Management
### Added
- Custom `User` model extending `AbstractUser` with `role` choices (`OWNER`, `INSPECTOR`, `ADMIN`) and optional phone.
- `RoleRequiredMixin` and role-based redirector (`/app/` -> role-specific dashboards).
- Custom authentication views for login, registration, and logout with Swiss design styling.

---

## [Stage 0] - Project Foundation
### Added
- Django 5.2 LTS project initialization with decoupled configuration.
- Installed apps structure: `accounts`, `registry`, `verification`, `certificates`, `site_pages`.
- WhiteNoise static files integration and SQLite database configuration.
