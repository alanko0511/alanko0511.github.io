# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A GitHub Pages **user site** (`alanko0511.github.io`) used to publish standalone HTML files publicly. There is no build step, no framework, no package manager, and no tests. Every file under the repo is served as-is from the `main` branch root.

- A file at `tools/compound-observatory.html` is reachable at `https://alanko0511.github.io/tools/compound-observatory.html`.
- Pushing to `main` deploys. There is no CI/build — GitHub Pages serves the committed files directly.

## Conventions for HTML artifacts

Each HTML file is a **fully self-contained single page**: inline `<style>` and a single inline `<script>`, no bundler and no local dependencies. The only external resources are CDN links (e.g. Google Fonts via `<link>`). Keep new files in this style so they work when opened directly (`open tools/<file>.html`) and when served by Pages — no relative asset paths to break.

- Organize artifacts into topical subdirectories (e.g. `tools/`) rather than the repo root.
- Vanilla JS only unless a CDN ES module (`https://esm.sh/...`) is explicitly warranted; there is no local `node_modules`.

## Working in this repo

- Preview locally by opening the file in a browser (`open tools/<file>.html`) — no server needed since everything is inlined.
- To publish: commit and push to `main`.
