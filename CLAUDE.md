# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A GitHub Pages **user site** (`alanko0511.github.io`) used to publish standalone HTML files publicly. There is no build step, no framework, no package manager, and no tests. Every file under the repo is served as-is from the `main` branch root.

- A file at `tools/compound-observatory.html` is reachable at `https://alanko0511.github.io/tools/compound-observatory.html`.
- `index.html` at the repo root is the landing page (`https://alanko0511.github.io/`) — a catalogue listing every published page.
- Pushing to `main` deploys. There is no CI/build — GitHub Pages serves the committed files directly.

## ⚠️ Keep the index in sync

`index.html` renders its catalogue from a single `const TOOLS = [...]` array near the bottom of the file. **Whenever you add, remove, rename, or move a page, edit that array in the same change** — add/update/delete the entry's `name`, `href` (relative to repo root), `blurb`, and `tag`. Nothing else needs touching. A new page that isn't in `TOOLS` is unreachable from the landing page.

## ⬅ Every page gets a "back to The Cabinet" nav

Every published page (anything reachable from `index.html`) **must include a back-nav link to the landing page** as the first element inside the page wrapper. This is the shared convention — match it exactly so navigation feels consistent. The markup:

```html
<a class="backlink" href="../">← The Cabinet</a>
```

And the styles (already present in `skills/index.html` and `tools/compound-observatory.html` — copy them into the new page's `<style>`):

```css
.backlink {
  font-family: "Spline Sans Mono", monospace;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 26px;
  transition: color 0.3s ease, gap 0.3s ease;
}
.backlink:hover { color: var(--gold); gap: 12px; }
```

- `href` points at the **site root** — use `../` for a page one directory deep (e.g. `tools/`, `skills/`); adjust the relative depth if a page is nested deeper.
- Pages built with the `.reveal` entrance animation (see `skills/index.html`) should give the backlink a `class="backlink reveal"` and an early `style="animation-delay: 0.02s"`.

## Shared visual system ("The Cabinet" aesthetic)

New pages should adopt the same look as the existing pages unless asked otherwise: the dark-parchment palette (`--ink`, `--parch`, `--gold`, `--teal` CSS variables), the **Fraunces** serif for titles + **Spline Sans** / **Spline Sans Mono** for body and labels (loaded via the same Google Fonts `<link>`), the fixed film-grain `body::after` overlay, and the gold eyebrow + italic-gold title treatment. Copy the `:root` variables and base styles from `index.html` or `skills/index.html` as a starting point.

## Conventions for HTML artifacts

Each HTML file is a **fully self-contained single page**: inline `<style>` and a single inline `<script>`, no bundler and no local dependencies. The only external resources are CDN links (e.g. Google Fonts via `<link>`). Keep new files in this style so they work when opened directly (`open tools/<file>.html`) and when served by Pages — no relative asset paths to break.

- Organize artifacts into topical subdirectories (e.g. `tools/`) rather than the repo root.
- Vanilla JS only unless a CDN ES module (`https://esm.sh/...`) is explicitly warranted; there is no local `node_modules`.

## Working in this repo

- Preview locally by opening the file in a browser (`open tools/<file>.html`) — no server needed since everything is inlined.
- To publish: commit and push to `main`.
