# Tola — Legal Metrology Verification System

> **Every scale, verified.**

Tola is a production-ready Django web application designed for the statutory verification of commercial weighing and measuring instruments under the **Legal Metrology Act, 2009** (Government of India).

Tola modernizes physical stamping registers into a transparent digital ledger. Business owners register commercial weighing instruments, file verification requests, track statutory inspections on an audit timeline, and receive tamper-evident digital certificates featuring scannable QR codes. Authorized legal metrology officers perform digital field inspections with automated tolerance evaluation against OIML R 76-1 / Class III maximum permissible error (MPE) standards. The public can verify any instrument's legal standing instantly without logging in.

---

## Visual Tour & Screenshots

Full visual walkthrough documentation is available in [`docs/screenshots/README.md`](docs/screenshots/README.md).

| View | Route | Description | Screenshot Reference |
|---|---|---|---|
| **Editorial Landing Page** | `/` | Swiss typography hero, role index, live ledger metrics, oversized verify strip | [`landing.png`](docs/screenshots/README.md) |
| **Owner Dashboard** | `/app/instruments/` | Business overview, three stat counters, hairline instrument table, upcoming deadlines rail | [`owner-dashboard.png`](docs/screenshots/README.md) |
| **Inspector Queue** | `/app/inspector/queue/` | Prioritized field assignments organized by preferred visit date | [`inspector-queue.png`](docs/screenshots/README.md) |
| **Stepped Inspection Form** | `/app/inspector/requests/<pk>/inspect/` | Zero-check, dynamic test readings with live HTMX tolerance indicators | [`inspector-form.png`](docs/screenshots/README.md) |
| **Public Verification Page** | `/v/<token>/` | Mobile-optimized certificate lookup displaying state word in semantic color | [`public-verify.png`](docs/screenshots/README.md) |
| **Admin Operations Desk** | `/app/console/requests/` | Central officer dispatch, filings oversight, and certificate revocation | [`admin-console.png`](docs/screenshots/README.md) |

---

## Documentation Index

| Document | Purpose |
|---|---|
| [Product Requirements Document](docs/01-PRD.md) | Problem statement, user personas, functional requirements, and 5-minute demo script |
| [Architecture & Data Model](docs/02-ARCHITECTURE.md) | Technical stack, ER diagram, state machine, URL map, permissions matrix, and permitted-error logic |
| [Design System](docs/03-DESIGN-SYSTEM.md) | Swiss editorial tokens, typography hierarchy, mobile-first layouts, and motion guidelines |
| [Antigravity Plan](docs/04-ANTIGRAVITY-PLAN.md) | Stage-by-stage implementation milestones, git commit rules, and criteria for completion |
| [Viva Preparation Guide](docs/05-VIVA-PREP.md) | Exhaustive defense guide covering architecture, metrology rules, database design, and security questions |
| [Changelog](docs/CHANGELOG.md) | Comprehensive stage-by-stage log of all features, optimizations, and tests built |
| [Standing Agent Rules](AGENTS.md) | Engineering and design constraints enforced throughout development |

---

## Stack & Architecture

- **Backend:** Python 3.12, Django 5.2 LTS, SQLite (development) / PostgreSQL (production-ready).
- **Frontend Interactivity:** `django-htmx` for dynamic inline tolerance checks and partial re-renders (zero Node/npm or single-page-app bloat).
- **Styling:** Pure custom CSS design tokens (`static/css/tokens.css`, `base.css`, `components.css`). No Bootstrap, Tailwind, or CSS preprocessors.
- **Typography:** Inter Tight (body, headlines at weight 300), Instrument Serif (italic accents), Geist Mono (data, labels, code).
- **Motion:** CDN-delivered GSAP 3.12, ScrollTrigger, and Lenis smooth scroll, strictly wrapped inside `prefers-reduced-motion: no-preference`.
- **Certificate Generation:** Pure Python ReportLab engine embedding official TTF fonts with 35mm high-contrast scannable QR stamps (`qrcode[pil]`).
- **Static Asset Serving:** WhiteNoise with compressed caching.
- **Environment & Security:** `python-decouple` reading `.env`.

---

## Quick Start (Clean Setup)

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/AbhilashReddy1519/tola.git
cd tola

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example configuration file:

```bash
# On Linux/macOS:
cp .env.example .env

# On Windows:
copy .env.example .env
```

*(Optional)* Review `.env` for customized port, verification fee, or validity duration.

### 4. Apply Migrations & Seed Demo Data

```bash
# Run database schema migrations
python manage.py migrate

# Seed complete demonstration dataset (idempotent)
python manage.py seed_demo
```

### 5. Run the Local Development Server

```bash
python manage.py runserver
```

Open your browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## Demo Credentials Directory

The `seed_demo` command creates a realistic Indian Legal Metrology ecosystem. All passwords are set to `AdminPassword123!`, `InspectorPassword123!`, or `OwnerPassword123!`:

| Role | Username | Password | User & Business Profile |
|---|---|---|---|
| **Admin** | `admin` | `AdminPassword123!` | Sanjay Verma — Controller of Legal Metrology |
| **Inspector** | `inspector_rajesh` | `InspectorPassword123!` | Rajesh Kumar — Authorized Field Officer |
| **Inspector** | `inspector_anita` | `InspectorPassword123!` | Anita Sharma — Authorized Field Officer |
| **Owner** | `owner_ramesh` | `OwnerPassword123!` | Ramesh Patel — Sri Lakshmi Kirana & General Stores (Grocery, Hyderabad) |
| **Owner** | `owner_priya` | `OwnerPassword123!` | Priya Sundaram — Sundaram Jewellers & Bullion Merchants (Jewellery, Warangal) |
| **Owner** | `owner_manpreet` | `OwnerPassword123!` | Manpreet Singh — Punjab Highway Weighbridge & Freight Terminal (Nizamabad) |
| **Owner** | `owner_fatima` | `OwnerPassword123!` | Fatima Begum — Deccan Oil Mills & Bulk Traders (Karimnagar) |
| **Owner** | `owner_vikram` | `OwnerPassword123!` | Vikram Desai — Desai Agro Provisions & Mandi Yard (Khammam) |

---

## Key Features & Workflows

### 1. Verification State Machine
All verification status updates are governed by `verification.services.transition()` inside atomic transactions:
```
SUBMITTED ──► ASSIGNED ──► PASSED ──► CERTIFIED (Certificate Issued)
    │             │           ▲
    ▼             ▼           └── FAILED
CANCELLED     CANCELLED
```
Every change automatically logs a historical audit record in `StatusEvent`.

### 2. Statutory Permitted-Error Rules (OIML R 76-1 / Class III)
Field test tolerance limits are evaluated based on multiples of verification scale interval $e$:
- $0 \le m \le 500e$: $\text{MPE} = \pm 0.5e$
- $500e < m \le 2000e$: $\text{MPE} = \pm 1.0e$
- $2000e < m \le 10000e$: $\text{MPE} = \pm 1.5e$

An inspection passes only if the physical zero-return check passes and all test readings fall strictly within statutory tolerance limits.

### 3. Expiry Reminder Dispatcher
Run statutory reminder notifications for certificates expiring in exactly 30 and 7 days:
```bash
# Dry run simulation
python manage.py send_expiry_reminders --dry-run

# Real execution (dispatches console emails in development)
python manage.py send_expiry_reminders
```

---

## Running Verification & Tests

To execute the test suite (65 passing unit & integration tests covering state machines, permissions, query optimization, certificates, and management commands):

```bash
# Run system check
python manage.py check

# Run full test suite
python manage.py test

# Verify production security configuration
python manage.py check --deploy
```

---

## License

Developed under academic coursework guidelines for the Django Web Development and Legal Metrology Digital Transformation assignment.
