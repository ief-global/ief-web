# IEF Global — Website

Official website for the **International Educational Foundation (IEF)**, a 501(c)(3) nonprofit organization dedicated to empowering K-12 students through native-language education.

🌐 **Live site:** [https://ief-global.org](https://ief-global.org)

> 📖 இந்த ஆவணம் தமிழிலும் கிடைக்கிறது — [README-ta.md](README-ta.md) (Tamil version).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Markup | HTML5 with SSI-style includes (compiled) |
| Styling | [Tailwind CSS](https://tailwindcss.com/) (CDN) |
| Interactivity | [Alpine.js](https://alpinejs.dev/) (CDN) |
| Build | Python compile script (`html/compile_site.py`) |
| CI/CD | [GitHub Actions](https://github.com/features/actions) (`.github/workflows/deploy.yml`) |
| Hosting | [Cloudflare Pages](https://pages.cloudflare.com/) |
| DNS | Cloudflare |

---

## Repository Structure

All site source lives under `html/`. The build script wipes and regenerates `dist/`
(generated output — gitignored, never edited by hand).

```
ief-web/
├── html/                    # ← SITE SOURCE (edit everything here)
│   ├── assets/              # Static assets (images, logos, QR codes), committed to git
│   │   ├── logo.webp
│   │   ├── hero-bg.webp
│   │   ├── picture-00.webp  # Community photos (picture-00 through picture-11)
│   │   ├── ...
│   │   ├── headshot-sm.webp # Board member headshots
│   │   └── zelle-qr.webp    # Donation QR code
│   │
│   ├── parts/               # Shared HTML components (SSI includes)
│   │   ├── nav-en.html      # English navigation bar
│   │   ├── nav-ta.html      # Tamil navigation bar
│   │   ├── donate-modal.html# Donation modal (Stripe + Zelle)
│   │   ├── footer-en.html   # English footer
│   │   └── footer-ta.html   # Tamil footer
│   │
│   ├── en/                  # English pages
│   │   ├── index.html
│   │   └── gallery.html
│   │
│   ├── ta/                  # Tamil pages
│   │   ├── index.html
│   │   └── gallery.html
│   │
│   ├── index.html           # Root language-redirect (→ /en or /ta)
│   └── compile_site.py      # SSI include compiler / build script
│
├── dist/                    # GENERATED OUTPUT — gitignored, do not edit
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions CI (build + deploy)
├── deploy.sh                # Manual local build/deploy helper
├── docker-compose.yml       # Optional nginx SSI dev preview (+ Tailscale sidecar)
├── nginx.conf
├── wrangler.toml            # Cloudflare Pages configuration
├── .gitignore
├── LICENSE
└── README.md
```

---

## Languages & Localization

The site is fully bilingual. Every page exists in two versions:

| Path | Language |
|---|---|
| `/en/` | English |
| `/ta/` | Tamil (தமிழ்) |

- Shared components (nav, footer, donate modal) live in `/parts/` and are compiled into each page at build time.
- The donate modal uses Alpine.js `lang` state (`'en'` or `'ta'`) to switch label text dynamically at runtime.
- Both language versions share one font stack — `'Noto Sans', 'Noto Sans Tamil', sans-serif` — so Latin text renders in **Noto Sans** and Tamil text in **Noto Sans Tamil**, two sibling families that harmonize by design. The rule lives on `body` in each page's `<style>` block, so sizing can be tuned in a single place.

---

## Local Development

### Prerequisites

- Python 3.x
- A local web server that supports static files (e.g. VS Code Live Server, `python -m http.server`, or similar)

### Setup

```bash
# Clone the repo
git clone https://github.com/ief-global/ief-web.git
cd ief-web

# Run the SSI compile step to resolve <!--#include virtual="..."--> directives.
# This wipes and regenerates dist/ and copies html/assets/ into dist/assets/.
# On Windows, use `python` if `python3` is not on PATH.
python3 html/compile_site.py

# Serve the compiled output locally
cd dist && python -m http.server 8080
# Then open http://localhost:8080/en/ in your browser
```

> **Note:** The raw source files use `<!--#include virtual="...">` directives for shared components. These are **not** processed by browsers directly — always run `html/compile_site.py` first to produce the final HTML before previewing or deploying.

---

## Build & Deployment

Deployment is handled by **GitHub Actions** (`.github/workflows/deploy.yml`), which builds
the site with `python3 html/compile_site.py` and deploys the resulting `dist/` to
**Cloudflare Pages**. Both the integration and production branches deploy automatically:

| Branch | Deploys to | URL |
|---|---|---|
| `develop` | Cloudflare **Preview** | `https://develop.ief-site.pages.dev` |
| `main` | Cloudflare **Production** | `https://ief-global.org` |

| CI Setting | Value |
|---|---|
| Trigger | Push to `develop` or `main` (plus manual `workflow_dispatch`) |
| Build command | `python3 html/compile_site.py` |
| Output directory | `dist/` |
| Cloudflare project | `ief-site` |
| Auth | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` (GitHub Actions secrets) |

Work on `develop`, validate the change on the preview URL, then merge `develop` into `main`
to promote it to production. See [WORKFLOW.md](WORKFLOW.md) for the full edit → commit →
deploy loop.

### Manual deploy (local)

For an out-of-band deploy, use the `deploy.sh` helper. It needs a local `.env` with
`CLOUDFLARE_*` credentials (gitignored). Cloudflare auth is an **API token**, not OAuth.

```bash
./deploy.sh           # build + deploy
./deploy.sh --build   # build only (regenerate dist/)
./deploy.sh --deploy  # deploy the existing dist/ without rebuilding
```

---

## Adding Content

### Adding a new photo

1. Convert your image to `.webp` format (use [Squoosh](https://squoosh.app/) or `cwebp` CLI for best results).
2. Name it sequentially: `picture-12.webp`, `picture-13.webp`, etc.
3. Place it in `html/assets/` (committed to git).
4. Add an entry to the `photoItems` array in **both** `html/en/gallery.html` and `html/ta/gallery.html`:

```js
// en/gallery.html
{ url: '/assets/picture-12.webp', title: 'Your English Caption' }

// ta/gallery.html
{ url: '/assets/picture-12.webp', title: 'உங்கள் தமிழ்த் தலைப்பு' }
```

5. If the photo should also appear on the home page, add it to `photoItems` in `html/en/index.html` and `html/ta/index.html` as well.

### Adding a new video

1. Upload the video to the [IEF YouTube channel](https://www.youtube.com/) and copy its video ID (the part after `?v=` in the URL).
2. Add an entry to `videoItems` in **both** the gallery files and the home page files:

```js
// en/gallery.html & en/index.html
{ type: 'video', url: 'YOUR_VIDEO_ID', title: 'Your English Title' }

// ta/gallery.html & ta/index.html
{ type: 'video', url: 'YOUR_VIDEO_ID', title: 'உங்கள் தமிழ் தலைப்பு' }
```

---

## Collaboration

Contributors are managed via GitHub repository access. Contact the repository admin to request access.

| Role | Permission level |
|---|---|
| Core developer | `Maintain` |
| Contributor | `Write` |
| Read-only reviewer | `Read` |

### Branching convention

```
main           ← production (auto-deploys to ief-global.org)
develop        ← integration branch (auto-deploys to the preview URL)
feature/<name> ← individual feature branches
fix/<name>     ← bug fix branches
```

Do day-to-day work on `develop` and validate on the preview URL. Promote to production by
merging `develop` into `main` (open a **Pull Request** and get at least one review) only
after the preview looks right.

---

## Organization Details

| Field | Value |
|---|---|
| Legal Name | International Educational Foundation, Inc. |
| Tax Status | 501(c)(3) Non-Profit, Tax-Exempt |
| EIN | 32-0103781 |
| General Contact | info@ief-global.org |
| Website Admin | admin@ief-global.org |

---

## License

This codebase is proprietary and maintained by the International Educational Foundation, Inc. All rights reserved. Content, images, and branding may not be reproduced without written permission.
