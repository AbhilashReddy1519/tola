# Tola

**Every scale, verified.**

Tola is an online verification system for weighing and measuring instruments. Shop owners register their instruments, request verification, and receive a tamper-evident certificate with a QR code. Inspectors record test readings on site and the system decides pass or fail against permitted error limits. Anyone can scan a certificate and confirm it is genuine.

> The name: a *tola* is a traditional Indian unit of weight, about 11.66 g, historically used to weigh gold and silver. Short, memorable, and exactly on topic.

Built for the Django assignment problem statement: *Development of an Online Verification System for Weighing and Measuring Instruments.*

---

## Documentation

| # | Document | What it answers |
|---|---|---|
| 1 | [Product requirements](docs/01-PRD.md) | Who is it for, what must it do, what is in the MVP |
| 2 | [Architecture and data model](docs/02-ARCHITECTURE.md) | Stack, models, status flow, URLs, permissions |
| 3 | [Design system](docs/03-DESIGN-SYSTEM.md) | Awwwards references, fonts, tokens, motion, page layouts |
| 4 | [Antigravity build plan](docs/04-ANTIGRAVITY-PLAN.md) | Stage-by-stage prompts with checks and commit points |
| 5 | [Viva prep](docs/05-VIVA-PREP.md) | Questions an evaluator is likely to ask |
| - | [AGENTS.md](AGENTS.md) | Rules the AI agent must follow while building |

Start with the Antigravity plan. It links to everything else.

## Stack at a glance

Django 5.2 LTS, SQLite in development, HTMX for interactivity, hand-written CSS with design tokens (no Node build step), GSAP and Lenis for motion, ReportLab and `qrcode` for certificates.

## Roles

| Role | Can do |
|---|---|
| Business owner | Register business and instruments, request verification, download certificates |
| Inspector | See assigned requests, record test readings, submit result |
| Admin | Assign inspectors, revoke certificates, view all activity |
| Public (no login) | Verify a certificate by QR or number |

## Quick start (once built)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Demo logins are created by `seed_demo` and listed in the command output.

## Repository layout (target)

```
tola-verify/
  AGENTS.md
  README.md
  docs/
  manage.py
  tola/            # project settings, urls
  accounts/        # custom User with role
  registry/        # Business, Instrument
  verification/    # VerificationRequest, Inspection, TestReading
  certificates/    # Certificate, PDF, QR, public verify
  site_pages/      # landing, errors
  templates/
  static/          # css, js, fonts
```

## Git

Create the remote repo and push:

```bash
gh repo create tola-verify --private --source=. --remote=origin --push
```

Or create an empty repo on GitHub in the browser and run:

```bash
git remote add origin https://github.com/<your-username>/tola-verify.git
git branch -M main
git push -u origin main
```
