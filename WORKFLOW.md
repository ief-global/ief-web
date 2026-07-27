# IEF Website — Development & Deployment Workflow

How code moves from an edit to the live site. Canonical, committed doc — if
`PROJECT-COWORK-INSTRUCTIONS.md` or a chat session disagrees with this file, this file wins.
(History: an earlier `.gitignore` rule ignored `WORKFLOW*.md`, which is why this file went
missing from the repo. That rule is removed; keep this file tracked.)

## Source of truth

The laptop folder `E:\COWORK\PROJECTS\IEF\WEB` is the working clone of `ief-global/ief-web`.
Both Claude environments operate on this same folder:

- **Claude Code (native Windows) — PRIMARY.** Everything that touches the pipeline:
  building (`compile_site.py`), local preview, `git` commit/push, promoting
  `develop` → `main`, checking CI. GitHub Desktop is the manual fallback for review/commit.
- **Claude Cowork (Linux sandbox) — edits and planning only.** It reads/edits files over the
  Windows mount but must never run `git`, `wrangler`, `gh`, or a build it trusts (see
  Gotchas). Cowork hands off via `IEF-HANDOFF.md` (git-ignored).

## Branches

- `develop` — integration branch. Push ⇒ CI deploys preview: **https://develop.ief-site.pages.dev**
- `main` — production. Merge ⇒ CI deploys **https://ief-global.org**

Work on `develop`. Promote only after the preview validates.

## The loop

1. **Edit** source under `html/` (Cowork or Code). Bilingual parity: EN and TA together.
   `html/parts/` partials propagate to every page. New pages must be added to
   `compile_site.py`'s page list.
2. **Build + preview (Code):** `PYTHONUTF8=1 python html/compile_site.py`, then
   `cd dist && python -m http.server 8080` → http://localhost:8080/en/.
3. **Commit + push `develop` (Code or GitHub Desktop).** Review the diff first —
   especially Tamil files (see Gotchas).
4. **CI deploys** (`.github/workflows/deploy.yml`): builds and publishes to Cloudflare
   Pages. Production only deploys while the Pages project stays **git-connected** with
   Production branch = `main` (native Cloudflare auto-deploys are disabled; CI is the path).
5. **Validate on preview**, both `/en/` and `/ta/`, desktop + a real phone.
6. **Promote:** merge `develop` → `main`, push (deploys production). Then **fast-forward
   `develop`**: switch to `develop`, merge `main` into it, push — so both branches read
   `0 ahead, 0 behind`. Do this after every promotion.

## Media (images / assets)

Media lives in `html/assets/` and is committed. `compile_site.py` copies it to
`dist/assets/`. If the image set grows large (e.g. per-school photos plus gallery growth),
the plan is Cloudflare R2 — tracked in `docs/BLUEPRINT-schools-and-donate.md`.

## Gotchas (hard-won — don't relearn these)

- **Never run `git` from the Cowork sandbox.** Git writes over the Windows mount fail and
  leave a stale `.git/index.lock` that blocks GitHub Desktop/Code. If that happens: delete
  `.git\index.lock` and retry.
- **Sandbox reads truncate multibyte files** (Tamil, em-dashes, emoji). A Tamil file can
  look cut off from the sandbox while being complete on disk. Trust host-side reads and the
  git diff, not a sandbox compile. After Cowork edits Tamil files, verify the diff in Code
  before committing.
- **`compile_site.py` paths derive from `__file__`, never `~`** (CI runs as `/home/runner`).
  Don't regress this.
- **A malformed Alpine `x-data` silently kills all Alpine on the page.** If interactivity
  dies, check `x-data` syntax first.
- **Cloudflare/`gh` auth is an API token from `.env` / Actions secrets — never OAuth,
  never committed.**
- **`wrangler.toml` is the source of truth** for the Pages project (`name = ief-site`,
  output `./dist`) — don't hand-edit those fields in the dashboard.

## Local files not in the repo

`IEF-HANDOFF.md` (Cowork→Code session handoffs) and `PROJECT-*.md` (project-instruction
scratch) are git-ignored working notes. Everything else — including `WORKFLOW.md`, `docs/`,
and `html/data/*.json` — is committed.
