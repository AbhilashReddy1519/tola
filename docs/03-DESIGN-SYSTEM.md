# 3. Design System

## 3.1 Honest expectations

Awwwards winners are built by teams over weeks, with custom WebGL, bespoke illustration and a motion designer. You will not match that in two days across an entire application, and trying to will leave you with a half-working project.

The strategy that works: **spend the polish budget on three surfaces** (landing page, owner dashboard, certificate plus public verify page) and make every other page inherit the same tokens so it feels like one system. Awwwards jurors score Design, Usability, Creativity and Content; restraint and typography carry a minimalist site on the first two without needing heavy tech.

## 3.2 References

I could only read published descriptions of these sites, not view them in a browser. Treat the numbers below as a starting point and **open both sites yourself and tune by eye.**

### Primary reference: Awwwards.com itself

A published style analysis of the Awwwards site describes it as a Swiss editorial gallery wall: oversized type, full-bleed photography and a single black floating rail for navigation. Details noted there:

- Near-monochrome palette, ink `#222222` on a warm pale-gray canvas, with one sparse orange accent.
- **Inter Tight** for everything, from 9 px metadata up to a display size around 127 px at **weight 300**, so large type whispers rather than shouts.
- Flat, rectangular components with about 8 px radii, pill buttons that read like labels, and a floating dark tab bar.

Source: [Refero style reference for Awwwards](https://styles.refero.design/style/a77a7289-3438-46ba-8194-214739e47514).

### Secondary reference: PP Fragment

A typography showcase site by Locomotive for Pangram Pangram. Its case study says the minimalist design keeps the focus on the typefaces themselves. It won Site of the Day and a Developer award on Awwwards. Study how it uses space and type as the only decoration.

Source: [Locomotive case study](https://locomotive.ca/en/work/pp-fragment).

### What we borrow and what we leave

| Borrow | Leave |
|---|---|
| Huge light-weight display type | Heavy WebGL or 3D |
| Warm neutral canvas, ink text, one accent | Full-bleed photography (we have no photos to shoot) |
| Floating dark navigation rail | Custom cursor on touch devices |
| Hairline rules and flat surfaces instead of shadows | Gradients, glassmorphism, drop shadows |
| Small mono metadata labels | Decorative illustration |

## 3.3 Typography

All three families are free on Google Fonts and available under open licences.

| Role | Font | Use |
|---|---|---|
| Display and UI | **Inter Tight** (variable) | Headlines at weight 300, body at 400, UI at 500 |
| Accent | **Instrument Serif** (italic) | One emphasised word per headline, used sparingly |
| Data | **Geist Mono** | Certificate numbers, serials, readings, small uppercase labels |

Why this trio: Inter Tight matches the reference and is tighter and more editorial than plain Inter. Instrument Serif adds a human, editorial note that makes a technical product feel crafted. Geist Mono gives numbers a calm, precise look, which suits a metrology product. Instrument Serif and Geist Mono both appear in current Google Fonts roundups for 2026, and a geometric-sans roundup suggests pairing Instrument Serif and Geist Mono with modern grotesques.

**Loading:** use `<link rel="preconnect">` and Google Fonts with `display=swap`. For better performance and offline demos, self-host the files from `static/fonts/` and preload the two used on the landing page.

**Fallback stack:** `"Inter Tight", "Inter", system-ui, -apple-system, "Segoe UI", sans-serif`.

### Type scale

| Token | Size | Weight | Tracking | Line height | Use |
|---|---|---|---|---|---|
| `--fs-display` | `clamp(3.5rem, 11vw, 10rem)` | 300 | -0.045em | 0.92 | Landing hero |
| `--fs-h1` | `clamp(2.5rem, 6vw, 5rem)` | 300 | -0.035em | 1.0 | Page titles |
| `--fs-h2` | `clamp(1.75rem, 3.2vw, 2.75rem)` | 300 | -0.025em | 1.1 | Section titles |
| `--fs-h3` | `1.25rem` | 500 | -0.01em | 1.3 | Card titles |
| `--fs-body` | `1.0625rem` (17 px) | 400 | -0.005em | 1.55 | Paragraphs |
| `--fs-small` | `0.875rem` | 400 | 0 | 1.5 | Table cells, help text |
| `--fs-label` | `0.6875rem` (11 px) | 500 | +0.08em, uppercase | 1.2 | Mono metadata |

Rules: never use bold for headlines (weight 300 is the signature), never centre long text, limit body measure to about 62 characters.

## 3.4 Colour

One neutral family, one accent, and semantic colours that are used only for status.

```css
:root {
  --canvas:   #EDECE8;  /* warm pale gray, page background */
  --surface:  #F6F5F2;  /* raised panels */
  --ink:      #222222;  /* text, filled buttons, nav rail */
  --ink-soft: #5E5E5A;  /* secondary text, 5.6:1 on canvas */
  --rule:     #CFCDC6;  /* hairlines */
  --accent:   #FF5A1F;  /* single accent: links on hover, focus ring, key marks */

  --ok:       #2F6B4F;  /* Valid */
  --warn:     #A86A00;  /* Expiring soon */
  --bad:      #B3261E;  /* Failed, Expired, Revoked */
}
```

Check contrast with a tool before finalising. Accent orange on the pale canvas is for marks and large text, not small body text. Status is always shown with a **word and a dot**, never colour alone.

## 3.5 Layout and spacing

- 12-column grid, 8 px base unit, outer margin `clamp(16px, 4vw, 48px)`, max content width 1440 px.
- Generous vertical rhythm: sections separated by `clamp(96px, 14vw, 200px)`.
- Content aligns hard-left to the grid. Asymmetry is the editorial signal; avoid centred hero blocks.
- Hairline `1px solid var(--rule)` separates rows and sections. No box shadows anywhere.
- Radii: `8px` for inputs and cards, `999px` for buttons and chips.

## 3.6 Components

| Component | Spec |
|---|---|
| **Nav rail** | Fixed, floating pill at bottom centre on mobile and top centre on desktop, `--ink` background, 14 px text in `--canvas`. Contains wordmark, 3 links, a filled *Log in* chip. Hides on scroll down, returns on scroll up. |
| **Button, primary** | Pill, `--ink` fill, `--canvas` text, 48 px tall. Hover: background slides to `--accent` with a 400 ms ease. |
| **Button, secondary** | Pill, 1 px `--ink` outline, same height. Hover: fills with ink. |
| **Input** | Bottom border only, 56 px tall, label floats above in the mono label style, focus draws a 2 px `--accent` underline from left. |
| **Table row** | Hairline separators, 72 px tall, hover shifts the row 8 px right and reveals an arrow. Click target is the whole row. |
| **Status chip** | Mono label, 8 px dot in the semantic colour, word beside it. |
| **Stat block** | Giant number in weight 300, mono label beneath. |
| **Timeline** | Vertical hairline with dots, event text in small size, timestamp in mono. |
| **Empty state** | One sentence in the h2 style and one pill button. No illustration. |
| **Toast** | Slides in from bottom, ink background, auto-dismiss after 4 s. |

## 3.7 Motion

Motion should feel like paper being drawn, not like a demo reel. Slow, eased and purposeful.

- **Easing:** `cubic-bezier(0.22, 1, 0.36, 1)` for entrances, durations 500 to 800 ms. Hover transitions 250 to 400 ms.
- **Smooth scroll:** Lenis at default settings. Disabled for `prefers-reduced-motion` and for the inspector form.
- **Hero reveal:** headline split by line, each line translates up from a clipped mask, 90 ms stagger.
- **Scroll reveals:** sections fade and rise 24 px once, triggered at 80 percent viewport height.
- **Counters:** stat numbers count up once when visible.
- **Link hover:** underline wipes in from the left.
- **Page transitions:** CSS View Transitions for same-document navigation as progressive enhancement, plain navigation as fallback.
- **Reduced motion:** wrap all of it in `@media (prefers-reduced-motion: no-preference)`; everything else renders in its final state.

## 3.8 Page layouts

### Landing (`/`)
1. **Hero.** Display headline: *Every scale, <em>verified.</em>* with the italic word in Instrument Serif. A mono label row beneath: `LEGAL METROLOGY / DIGITAL VERIFICATION / EST. 2026`. A short paragraph at columns 8 to 11 and two buttons.
2. **Index.** A hairline-separated list of the three roles (Owner, Inspector, Public) with large numerals `01`, `02`, `03`.
3. **How it works.** Four steps in a sticky left title, right column scrolling through large numbered statements: Register, Request, Inspect, Certify.
4. **Live ledger.** Three giant counters (instruments verified, certificates active, average days to certify) fed from real database counts.
5. **Verify strip.** A single oversized input, *Enter a certificate number*, sending users to `/verify/`.
6. **Footer.** A wordmark `Tola` at 20vw, cropped by the viewport edge.

### Owner dashboard
- Greeting at h1 size: *Good morning, Ramesh.*
- Three stat blocks: Valid, Expiring in 30 days, Overdue.
- Instruments as a hairline table with status chips and a *Request verification* action on hover.
- Right rail: next three deadlines in mono.

### Inspector queue and inspection form
- Queue as large rows: instrument, business, preferred date.
- Inspection form full-screen, one section at a time (Zero, Accuracy, Repeatability, Eccentricity). Each reading row shows live error and a pass or fail dot as the user types (HTMX). Sticky bottom bar: *Result so far: PASS* and a *Submit inspection* button.

### Certificate (PDF) and public verify page
- **PDF:** A4 portrait. Top left mono label `CERTIFICATE OF VERIFICATION`. Certificate number at display size in Geist Mono. Two-column key facts table. QR bottom right at 35 mm with its URL in mono beneath. Hairline frame, no ornaments.
- **Verify page:** the state word (**VALID**, **EXPIRED**, **REVOKED**) at display size in the semantic colour, details underneath in a two-column mono list. This is the page a customer sees on a phone, so make it unmissable.

## 3.9 Accessibility checklist

- [ ] Text contrast at least 4.5:1, large text at least 3:1
- [ ] Visible 2 px focus ring in `--accent` with 2 px offset on every interactive element
- [ ] All motion off under `prefers-reduced-motion`
- [ ] Forms have real `<label>` elements and error text linked with `aria-describedby`
- [ ] Status never conveyed by colour alone
- [ ] Tap targets at least 44 px
- [ ] One `<h1>` per page, headings in order
- [ ] Nav rail usable by keyboard and does not trap focus

## 3.10 Pre-submission design checklist

- [ ] Only three font families loaded, and only the weights actually used
- [ ] No page uses a default browser button or Bootstrap look
- [ ] Every page has the same margins and the same nav rail
- [ ] Empty, loading and error states exist for lists and forms
- [ ] 390 px, 768 px and 1440 px widths checked
- [ ] Lighthouse accessibility 95 or higher, performance 90 or higher on landing
- [ ] Certificate PDF opened and the QR scanned from a real phone
