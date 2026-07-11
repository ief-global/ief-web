---
name: school-cards
description: >
  Convert TTKP school information (a thaitamilkalvippani.org page link, the
  TTKP_Schools_list_15.pdf, or raw details Saran pastes) into a record in
  html/data/schools.json and render it as a modern bilingual card on
  en/schools.html + ta/schools.html. Use whenever Saran adds a school, updates
  school details (students, staff, chairman, social links), asks to build or
  restyle the Schools (பள்ளிகள்) page, or provides new school photos.
---

<!-- INSTALL (Claude Code, one time): copy this folder to .claude/skills/ so it
     auto-triggers:  cp -r docs/skills/school-cards .claude/skills/school-cards
     (Cowork cannot write .claude/ — that's why it lives here.) -->

# School Cards — data-to-card pipeline

The Schools page is **data-driven**: cards are generated at build time from
`html/data/schools.json`. Never hand-edit card HTML in `en/schools.html` /
`ta/schools.html` — edit the JSON (content) or the card template (style) and
rebuild. Full design rationale: `docs/BLUEPRINT-schools-and-donate.md`.

## Prerequisites (read first)

1. `CLAUDE.md` — build/deploy rules. Key ones: edit `html/` never `dist/`,
   bilingual parity, run `python html/compile_site.py` (with `PYTHONUTF8=1` on
   Windows), new pages must be ADDED to the compiler's hardcoded page list.
2. `html/data/schools.json` — current data. `null` = pending, skip at render.

## Workflow A — add or update a school record

1. **Get the source.** One of:
   - A TTKP page URL (e.g. `https://thaitamilkalvippani.org/singanur_tirupur.htm`) — fetch it.
   - Raw text/PDF from Saran.
2. **Map fields** with this table (TTKP pages are Tamil; keep Tamil verbatim,
   translate to English for `_en` fields — flag transliterations for Saran's
   review, never invent facts):

   | TTKP page heading | JSON field |
   |---|---|
   | Page title / hero name | `name_ta` (+ translate → `name_en`) |
   | முகவரி | `address_ta` / `address_en` |
   | தொடங்கிய ஆண்டு | `year_started` (integer) |
   | நிறுவனர் மற்றும் பொறுப்பாளர் | `chairman_ta` / `chairman_en` |
   | தொடர்புக்கு (தொலைபேசி / மின்னஞ்சல்) | `phone`, `email` |
   | மாணவர் எண்ணிக்கை (ஆண்கள்/பெண்கள்/மொத்தம்) | `students.boys/girls/total` |
   | ஆசிரியர்கள்... எண்ணிக்கை | `staff.teachers/part_time/support` (+ compute `total`) |
   | (not on TTKP pages) | `social.*`, `donate.ref` — ask Saran |

3. **Slug**: lowercase place name, hyphenated (`vallalar-nagar`). `donate.ref`
   must be `school-<slug>`.
4. **Validate** after editing:
   `python -c "import json; json.load(open('html/data/schools.json', encoding='utf-8'))"`
   and check the record count.

## Workflow B — school photo pipeline

Target: `html/assets/schools/<slug>.webp`, **1200px wide, quality ~80, aim
< 120 KB** (16:10-ish crop; the card crops with `object-cover` anyway).

1. Download the school photo from the TTKP page (e.g.
   `wp-content/uploads/2017/palliyin-pattiyal/<name>.png`) or use the image
   Saran supplies. TTKP is IEF's partner org, but confirm with Saran that image
   reuse is approved before shipping.
2. Convert: `python -c "from PIL import Image; im=Image.open('in.png'); im.thumbnail((1200,10000)); im.save('html/assets/schools/<slug>.webp','WEBP',quality=80)"`
   (or `cwebp -q 80 -resize 1200 0`).
3. Missing photo → the generator must fall back to the branded gradient
   (`hero-gradient`), never a broken `<img>`.

## Workflow C — render the cards (generator contract)

`compile_site.py` gains one pre-pass: a marker in the source page is replaced
by generated cards before SSI includes are resolved.

Marker (one per page):

```html
<!--#school-cards lang="en"-->      <!-- in en/schools.html -->
<!--#school-cards lang="ta"-->      <!-- in ta/schools.html -->
```

Generator rules:

- Read `html/data/schools.json`; for each school render the card template
  below, picking `_en` or `_ta` fields by `lang`.
- **Null handling:** omit the entire row/element for any null field. A card
  with only name + address + donate button must still look complete.
- Donate URL: `<shared_stripe_link>?client_reference_id=<donate.ref>` (link
  read from `_meta.shared_stripe_link`).
- Social icons render only for non-null links.
- Escape nothing in Tamil strings; files are UTF-8 end-to-end.
- Keep implementation small (~40 lines): token filling with `{{field}}`, and
  conditional blocks `{{#field}}...{{/field}}` stripped when the field is null.

## Card template (reference design)

Grid wrapper: `grid gap-8 md:grid-cols-2 xl:grid-cols-3`. Each card — photo as
shadowed background, text/social/donate as the focus:

```html
<article class="group relative rounded-3xl overflow-hidden shadow-xl bg-slate-900 flex flex-col min-h-[30rem]">
  <!-- background image, darkened so text carries the card -->
  <img src="{{photo}}" alt="{{name}} — {{place}}" loading="lazy"
       class="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-70 group-hover:scale-105 transition duration-700">
  <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-slate-900/20"></div>

  <div class="relative flex flex-col justify-end flex-1 p-6 text-white">
    {{#year_started}}
    <span class="self-start text-[11px] font-bold uppercase tracking-widest bg-blue-500/90 rounded-full px-3 py-1 mb-3">
      EST. {{year_started}}</span>
    {{/year_started}}

    <h3 class="text-xl font-black leading-snug mb-1">{{name}}</h3>
    <p class="text-sm text-blue-200 font-semibold mb-3">{{place}}</p>

    {{#students_total}}
    <div class="flex gap-4 text-xs mb-3">
      <span class="bg-white/10 rounded-lg px-2.5 py-1.5"><strong>{{students_total}}</strong> STUDENTS_LABEL</span>
      <span class="bg-white/10 rounded-lg px-2.5 py-1.5"><strong>{{staff_total}}</strong> STAFF_LABEL</span>
    </div>
    {{/students_total}}

    <p class="text-xs text-slate-300 leading-relaxed mb-1">{{address}}</p>
    {{#phone}}<a href="tel:{{phone}}" class="text-xs text-slate-300 hover:text-white">{{phone}}</a>{{/phone}}
    {{#chairman}}<p class="text-xs text-slate-400 mt-1">CHAIRMAN_LABEL: {{chairman}}</p>{{/chairman}}

    <div class="flex items-center justify-between mt-5 pt-4 border-t border-white/15">
      <div class="flex gap-3">
        <!-- one inline SVG per non-null social link (YouTube / Facebook / Instagram),
             w-5 h-5, text-slate-300 hover:text-white, aria-label set -->
      </div>
      <a href="{{donate_url}}" target="_blank" rel="noopener"
         class="bg-amber-400 text-slate-950 text-sm font-black rounded-xl px-5 py-2.5 hover:bg-amber-300 active:scale-[0.98] transition shadow-lg">
        DONATE_LABEL</a>
    </div>
  </div>
</article>
```

Labels by lang: STUDENTS_LABEL = `Students` / `மாணவர்கள்` · STAFF_LABEL =
`Staff` / `பணியாளர்கள்` · CHAIRMAN_LABEL = `Chairman` / `தாளாளர்` ·
DONATE_LABEL = `Donate to this school` / `இப்பள்ளிக்கு நன்கொடை`.

## Page + site wiring checklist (first build only)

- [ ] Create `en/schools.html` + `ta/schools.html` (copy head/nav/footer
      chrome from `en/gallery.html` / `ta/gallery.html`; keep the shared body
      font rule and favicon block; page `<title>`: `IEF | Our Schools` /
      `IEF | எங்கள் பள்ளிகள்`).
- [ ] Add both pages to `compile_site.py`'s page list (it is hardcoded).
- [ ] Nav: add `Schools` / `பள்ளிகள்` to `parts/nav-en.html` + `parts/nav-ta.html`.
- [ ] Home teaser: small section on `en/index.html` + `ta/index.html` — heading,
      one line ("15 Tamil-medium schools across Tamil Nadu"), 3 sample cards or
      a photo strip, and a "View all schools →" link to `/en/schools.html` /
      `/ta/schools.html`.
- [ ] Footer quick-links: add Schools to `parts/footer-en.html` / `footer-ta.html`.

## Verification (every change)

1. `PYTHONUTF8=1 python html/compile_site.py` — zero missing-component warnings.
2. Preview `dist/` on :8080 — check **both** `/en/schools.html` and
   `/ta/schools.html`: card count = JSON record count, no literal `null` or
   `{{` anywhere, Tamil renders in Noto Sans Tamil, lazy images load.
3. Click one donate button → Stripe page opens; URL carries
   `client_reference_id`.
4. Mobile viewport (375px): single-column cards, donate button ≥ 44px tall.
5. Tamil copy: flag anything machine-translated for Saran's native review.

## Guardrails

- Cowork sandbox: do NOT run git; large Tamil file writes can truncate — after
  any JSON edit from Cowork, re-validate with the JSON check above.
- Never edit `dist/`. Never invent school facts — null until Saran confirms.
- Bilingual parity is mandatory: EN and TA pages ship together in one commit.
