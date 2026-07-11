# Blueprint — Schools page, Donate-modal revamp, Modernization roadmap

**Author:** Claude Fable 5 (design/architecture pass, 2026-07-10)
**Implementers:** Claude Opus / Sonnet in **Claude Code (native Windows)** — Cowork is
content/planning only (no git, no build verification; see `PROJECT-COWORK-INSTRUCTIONS.md`).
**Decisions below were confirmed with Saran on 2026-07-10** — do not re-litigate them;
ask him only where a ❓ marks an open item.

Read in this order before touching anything: `CLAUDE.md` → this file →
`docs/skills/school-cards/SKILL.md` → `html/data/schools.json`.

---

## 0. Confirmed decisions (from Saran)

| Topic | Decision |
|---|---|
| Schools placement | New `en/schools.html` + `ta/schools.html` **plus** a small teaser section on both home pages |
| Data model | `html/data/schools.json` + build-time card generator in `compile_site.py` |
| Per-school donations | **One shared Stripe payment link** with `?client_reference_id=school-<slug>` per card (no per-school links for now) |
| Card images | Reuse TTKP site photos → WebP in `html/assets/schools/` (❓ confirm reuse permission with Saran before production deploy) |
| Donate revamp scope | Redesign `parts/donate-modal.html` only (no dedicated /donate page yet) |
| Stripe ACH split | Not available — one combined link; nudge ACH via hierarchy + copy, cannot enforce |
| Modernization in scope | Tailwind CDN→CLI, generalized data-driven engine, SEO/meta/a11y pass; **Astro = evaluation ADR only**, not a migration |

## 1. Current-state assessment (why these designs)

What's healthy: tiny surface (8 pages), zero-backend static output, clean SSI-include
chrome sharing, CI deploy with preview branch, bilingual structure already disciplined.
Keep all of that — every design below stays inside HTML + Tailwind + Alpine + Python
compiler + Cloudflare Pages.

What's creaking (each maps to a fix in this blueprint):

1. **Content duplicated across en/ and ta/** (gallery arrays, leadership, stats live in
   two page files). Every edit is a two-file edit; drift is the failure mode. → §4
   data-driven engine; schools start life data-driven so they never inherit the problem.
2. **Tailwind CDN at runtime** (~300 KB script, browser JIT, console warning, styling
   flashes on slow connections). Fine for dev, wrong for production. → §4 Phase A.
3. **`compile_site.py` hardcoded page list** — silent gotcha for every new page. The
   schools work touches this file anyway; convert the list to a loop over a PAGES
   constant while there (5-minute refactor, keeps behavior identical).
4. **No SEO/meta layer** — no OG tags, no sitemap, no hreflang EN⇄TA, no structured
   data. A nonprofit lives on shared links and search. → §4 Phase C.
5. **Donate modal fights donor psychology** — one combined button treats 2.9%-fee cards
   and 0.8%-fee ACH identically; the Zelle QR assumes a second device (donor is often
   *on* their phone). → §3.
6. Housekeeping: `WORKFLOW.md` is referenced by `PROJECT-COWORK-INSTRUCTIONS.md` and
   `CLAUDE.md`-adjacent docs but **does not exist at repo root** (only inside a stale
   `.claude/worktrees/` copy). Restore or re-point. Also: the README structure section
   is stale (already flagged in CLAUDE.md).

## 2. Feature 1 — Schools (பள்ளிகள்) page

Everything an implementer needs is in **`docs/skills/school-cards/SKILL.md`**
(install to `.claude/skills/` per the note at its top). Summary of the architecture:

```
html/data/schools.json      ← single source of truth (15 records seeded; Singanur complete)
        │  (build time)
compile_site.py pre-pass    ← replaces <!--#school-cards lang="…"--> with rendered cards
        │
en/schools.html, ta/schools.html   ← page chrome + marker (never hand-edit cards)
html/assets/schools/<slug>.webp    ← image pipeline output
```

Why build-time rather than Alpine-runtime: content is indexable without JS, no
double-maintenance in two page files, and the pattern generalizes (§4 Phase B). It also
costs nothing new — it's ~40 lines added to the existing compiler.

Data status: all 15 schools are seeded from `TTKP_Schools_list_15.pdf` with Tamil
names/addresses. Only Singanur has year/chairman/strength populated (scraped from its
TTKP page). **First implementation task: fetch the remaining `ttkp_url` pages and fill
the null fields** (Workflow A of the skill). `social.*` and Perur's URL need Saran. ❓

Definition of done (Phase 1):
- [ ] Generator implemented in `compile_site.py` + pages added to its page list.
- [ ] `en/schools.html` + `ta/schools.html` render 15 cards each; no `null`/`{{` leaks.
- [ ] Nav + footer links, home-page teaser section — both languages.
- [ ] All available TTKP data scraped into JSON; pending fields listed for Saran.
- [ ] Images converted per pipeline; gradient fallback works for missing ones.
- [ ] Donate buttons carry `client_reference_id`; verified visible in Stripe dashboard
      metadata on a test donation. ❓ Saran to confirm attribution appears as expected.
- [ ] Verification checklist in the skill passes; deployed to develop preview; Saran
      approves Tamil copy; promoted to main (then fast-forward develop).

## 3. Feature 2 — Donate modal revamp (`html/parts/donate-modal.html`)

Goals: (a) nudge **ACH over card** on the shared Stripe link, (b) make **Zelle work on
one device**, (c) make fee impact transparent — donors respond to "more reaches
students," and IEF keeps more of each gift.

Constraint: one combined Stripe link — we cannot force method order at checkout. The
nudge is therefore visual hierarchy + microcopy.

### Layout spec (top → bottom inside the existing modal shell)

1. **Header** — keep current title/blurb.
2. **Fee-impact strip** — three tiny columns (Zelle · Bank/ACH · Card) showing
   "of $100, reaches students": **$100 · ~$99 · ~$97**. One line under it:
   "Bank transfer and Zelle keep processing fees near zero."
   ⚠️ Verify Saran's actual Stripe rates (nonprofit pricing differs: card ~2.2%+30¢,
   ACH 0.8% cap $5) before hardcoding numbers; round conservatively, never overstate —
   501(c)(3) accuracy rule.
3. **Primary button (unchanged link, upgraded copy)** — the existing Stripe link,
   styled as today's primary. Label: `Donate — Bank (ACH) or Card`. Directly beneath,
   a persistent tip line with a small bank icon:
   EN: *"Tip: choose **US bank account** at checkout — lowest fees, more of your gift
   reaches students."*
   TA: *"குறிப்பு: செலுத்தும்போது **US bank account** தேர்வு செய்யுங்கள் — கட்டணம்
   குறைவு, உங்கள் நன்கொடையில் அதிகம் மாணவர்களுக்குச் சேரும்."* (native review ❓)
4. **Zelle block — device-aware, no second device required.** Replace the QR-first
   layout:
   - **Mobile (`md:hidden`):** big button `Pay with Zelle` using the existing
     `enroll.zellepay.com` deep link (opens bank-app chooser on the phone) + a
     `Copy email` button (`navigator.clipboard.writeText`, Alpine `$data` toast
     "Copied ✓") for donors who prefer pasting into their banking app.
   - **Desktop (`hidden md:flex`):** QR (unchanged asset) + caption "Scan with your
     phone's banking app" + the same copy-email button + the deep-link as a text link.
   - Zelle = $0 fees; badge it `No fees` in both languages.
5. **Trust footer** — one line: "IEF is a 501(c)(3); donations are tax-deductible to
   the extent allowed by law. EIN available on request." ❓ Saran: confirm exact
   wording/EIN display preference.

Implementation notes: CSS breakpoints (`md:`) for device-awareness — no UA sniffing.
Keep everything in the single include file; both languages via the existing
`lang === 'en' ? … : …` pattern. Modal is shared chrome — one edit propagates to all 8
(soon 10) pages.

Definition of done (Phase 2):
- [ ] New hierarchy renders in both languages, mobile and desktop.
- [ ] Zelle deep link verified on a real phone (Android + iOS if possible); copy-email
      works over HTTPS (preview URL is fine; localhost clipboard needs `http://localhost`).
- [ ] Fee numbers verified against Saran's Stripe dashboard.
- [ ] Modal open/close/`@click.away` behavior unchanged on every page.
- [ ] Rollback: single-file revert of `parts/donate-modal.html` + rebuild.

## 4. Modernization roadmap (approved scope)

Do these as separate commits/PRs after Phases 1–2, in this order:

### Phase A — Tailwind CDN → CLI (~half day, low risk)
1. `npm init -y` + `tailwindcss` as the only devDependency; `tailwind.config.js` with
   `content: ["html/**/*.html", "html/data/*.json"]` (JSON included so generated-card
   classes are seen) and a `safelist` for any class only produced by the generator.
2. Input CSS with the three `@tailwind` layers + the current inline custom CSS
   (`hero-gradient`, scrollbar, countUp) moved into it.
3. Build step: `npx tailwindcss -i … -o dist/assets/site.css --minify` invoked from
   `compile_site.py` (subprocess) so the one-command build stays true; CI adds a
   `setup-node` step before the Python build.
4. Swap the CDN `<script>` for `<link rel="stylesheet" href="/assets/site.css">` in all
   page heads (this is per-page — heads are not shared chrome).
   **Risk:** missed dynamic classes → safelist; **verify** by diffing rendered pages
   visually on preview before promoting. **Rollback:** restore CDN script tag.

### Phase B — Generalize the data-driven engine (~1 day)
Promote the schools generator into a generic pass: `<!--#data:TEMPLATE src=… lang=…-->`
so `photoItems`/`videoItems` (gallery), leadership cards, and stats also come from
`html/data/*.json`. Result: EN/TA content parity becomes automatic (one JSON, two
rendered languages) — this kills failure mode #1 permanently. Migrate one content type
per commit; gallery first (highest churn — see memory: home reel vs gallery archive).

### Phase C — SEO / meta / a11y pass (~half day)
- OG + Twitter meta on every page (per-language titles/descriptions).
- `sitemap.xml` + `robots.txt` emitted by `compile_site.py`.
- `<link rel="alternate" hreflang="en|ta">` pairs on every page (also fixes language
  discovery); canonical tags.
- JSON-LD: `NGO` (org, on index) + `School` (one per schools.json record — generator
  emits it with the cards; free win from the data model).
- A11y sweep: alt text audit, focus states on modal, color-contrast check on the new
  fee strip, `aria-label`s on icon-only links.

### Phase D — Astro: evaluation only (ADR, ~half-day spike)
Saran wants Astro considered **later in the lifecycle**. Do not migrate now. Write
`docs/ADR-001-astro.md` after Phases A–C, answering: what Astro buys over the (by then)
data-driven Python pipeline — content collections with schema validation (schools.json
would get typed), built-in i18n routing, `astro:assets` image optimization, zero-JS
default that matches this site's philosophy; what it costs — Node build chain replaces
a 150-line readable Python script, CI change, re-learning cost for a one-person org.
**Trigger criteria to adopt:** page count > ~15, a third JSON-driven content type, or
per-school detail pages get approved. If triggers aren't met, staying on the compiler
is the right call — record that.

### Effort summary

| Work | Estimate (Claude Code session time) |
|---|---|
| Phase 1 Schools page (incl. scraping + images) | 1–1.5 days |
| Phase 2 Donate modal | 0.5 day |
| Phase A Tailwind CLI | 0.5 day |
| Phase B Data engine generalization | 1 day |
| Phase C SEO/a11y | 0.5 day |
| Phase D Astro ADR | 0.5 day |

## 5. Standing rules for implementers (Opus/Sonnet)

1. **Environment:** all git/build/preview/deploy in Claude Code on the Windows laptop.
   Never run git from Cowork. `PYTHONUTF8=1` for builds on Windows.
2. **Loop:** edit `html/` → build → preview :8080 → commit/push `develop` → validate
   https://develop.ief-site.pages.dev → promote to `main` → **fast-forward `develop`**
   (see `PROJECT-COWORK-INSTRUCTIONS.md` §Promotion).
3. **One phase = one PR/commit series.** Ship Phase 1 fully before Phase 2; never mix
   modernization phases with feature phases in one commit.
4. **Bilingual parity is a merge blocker.** EN and TA changes land together.
5. **Tamil copy:** produce real Tamil, mark anything machine-generated for Saran's
   native review before promoting to main. Never ship English placeholders in `ta/`.
6. **Money-related copy** (fees, tax deductibility) must be verified with Saran before
   production — 501(c)(3) accuracy requirement.
7. When you change build behavior, update `CLAUDE.md` (and restore/point `WORKFLOW.md`)
   in the same commit — repo docs are the single source of truth.

## 6. Open items for Saran (tracked ❓)

1. TTKP image reuse — written OK from TTKP.
2. Social media links per school (YouTube/Facebook/Instagram) — or drop icons for v1.
3. Perur school: TTKP page URL (not in their nav) or data directly.
4. Actual Stripe fee rates (nonprofit pricing?) for the fee strip.
5. Tax-deductibility line wording / EIN display.
6. Native-speaker review of new Tamil copy (cards, modal, teaser).
7. `WORKFLOW.md` missing at repo root — restore it or update references.
