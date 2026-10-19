# AGENTS.md: standing rules for AI agents working on Tola

Read this file first in every session. Then read the docs the prompt names.

## Project

Tola is a Django web app for online verification of weighing and measuring instruments. Source of truth for scope is `docs/01-PRD.md`, for schema and flow `docs/02-ARCHITECTURE.md`, for visuals `docs/03-DESIGN-SYSTEM.md`. If a prompt conflicts with those, stop and ask rather than guessing.

## Stack (do not change without asking)

Python 3.12, Django 5.2 LTS, SQLite, `django-htmx`, ReportLab, `qrcode[pil]`, WhiteNoise, `python-decouple`. Hand-written CSS with custom properties. GSAP, ScrollTrigger and Lenis from a CDN. No Tailwind, Bootstrap, React or Node build step. No new dependencies without saying why.

## Engineering rules

1. Work on the current stage only. Do not build features from later stages.
2. Never fetch a user-owned object by bare `pk`. Use a scoped queryset and `get_object_or_404`.
3. Status changes only through `verification.services.transition()`. Never assign `request.status` in a view.
4. Wrap multi-step writes in `transaction.atomic`.
5. Public pages identify certificates by `token` (UUID4), never by primary key, and never expose owner contact details.
6. Use class-based views and mixins for CRUD. Keep views thin; put logic in services or model methods.
7. Add tests alongside every feature. Run `python manage.py check` and `python manage.py test` before saying a stage is done and report the real output.
8. Use `select_related` and `prefetch_related` on list views.
9. Keep secrets in `.env`. Never commit `.env`, databases or `__pycache__`.
10. Make the smallest change that satisfies the request. Do not rewrite files that are not part of the task. Do not remove existing tests to make a run pass.
11. If a library, API or setting is uncertain, say so instead of inventing it.

## Design rules

1. Use only the tokens in `static/css/tokens.css`. No new colours, no shadows, no gradients, no icon libraries.
2. Headlines are weight 300. Never bold a headline.
3. Fonts: Inter Tight, Instrument Serif (italic accents only), Geist Mono (data and labels).
4. Mobile first. Check 390, 768 and 1440 px.
5. All motion wrapped in `prefers-reduced-motion: no-preference`, and the site must work with JavaScript disabled.
6. Status is always conveyed with a word and a dot, never colour alone.
7. Meet WCAG AA contrast and keep visible focus rings.

## Git rules

- One branch per stage, small commits, conventional messages (`feat:`, `fix:`, `test:`, `chore:`).
- Do not rewrite history on `main`.
- Show a short summary of changed files at the end of each stage.

## Communication

Be concise. State what changed, what was verified, and anything uncertain. Do not claim a check passed unless you ran it.
