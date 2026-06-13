# The Cabinet

A small, growing collection of self-contained web tools — each one a single HTML page built to do one thing precisely.

**Live at → [alanko0511.github.io](https://alanko0511.github.io/)**

## What this is

This is my GitHub Pages site: a place to publish little interactive instruments and share them with a plain link. The landing page is a catalogue — open it to browse whatever's currently in the cabinet.

Each tool is intentionally a **single, dependency-free HTML file**: inline styles and script, no build step, no framework, no package install. You can open any of them straight from disk in a browser, or send someone the one file and it just works.

> **Heads up:** everything here is AI-generated. These are quick, vibe-coded tools made to scratch a specific itch — not hand-crafted, not audited, not production software. Use them as-is and at your own discretion. Yes, including this heads up. And this sentence pointing out that the heads up wrote itself. It's turtles all the way down.

## How it's built

- **AI-generated.** The pages are produced with an AI coding agent, then committed as-is. Expect rough edges.
- **Static deploy.** Pushing to `main` deploys — GitHub Pages serves the files directly, no CI or bundler.
- **Self-contained pages.** New tools live as standalone HTML (under `tools/`) and only ever reach out to a CDN for fonts.
- **A catalogue, not a framework.** `index.html` lists every page; it's the front door to the collection as it grows.

## License

[MIT](LICENSE) © Alan Ko
