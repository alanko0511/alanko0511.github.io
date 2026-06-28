#!/usr/bin/env -S uv run --quiet --with markdown-it-py python
"""
Render a plan's markdown to a styled HTML file and open it.

Two input modes:
  1. Hook mode (no args): reads the PreToolUse JSON payload from stdin and
     pulls `.tool_input.plan` (what ExitPlanMode is being called with).
  2. File mode (one arg): reads a .md file directly. Handy for testing.

Conversion is a pure, deterministic CommonMark -> HTML render via markdown-it-py.
It only maps markup (**bold** -> <strong>, ``` fences -> <pre><code>, lists ->
<ul>/<ol>, etc.). It never rewords, reorders, or drops content, so the text is
verbatim by construction.

CommonMark (markdown-it-py) is used rather than python-markdown specifically so a
list may interrupt a paragraph with no blank line between them -- which plans do
constantly (e.g. "Rewrite foo.tsx:" immediately followed by "- ..." bullets).
python-markdown folds those into one paragraph blob; CommonMark renders the list.
"""

import hashlib
import html
import json
import os
import subprocess
import sys
import tempfile

from markdown_it import MarkdownIt


def get_source_markdown() -> tuple[str, str]:
    """Return (markdown_text, slug). Slug is used for a stable filename."""
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            text = f.read()
        slug = os.path.splitext(os.path.basename(path))[0]
        return text, slug

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)  # nothing to do; don't block the tool call
    payload = json.loads(raw)
    text = (payload.get("tool_input") or {}).get("plan") or ""
    if not text.strip():
        sys.exit(0)
    slug = "plan-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return text, slug


# Editorial direction: serif body for comfortable reading, sans headings,
# warm off-white, deep-green accent, wide (960px) measure.
TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<title>__TITLE__</title>
<style>
  :root{ --ink:#23211c; --muted:#6f6a60; --accent:#2f6b4f; --line:#e7e3da;
         --paper:#fbfaf7; --codebg:#f3f1ea; }
  *{ box-sizing:border-box; }
  body{ margin:0; background:var(--paper); color:var(--ink);
        font:400 18px/1.72 "Source Serif 4",Georgia,serif;
        -webkit-font-smoothing:antialiased; }
  main{ max-width:960px; margin:0 auto; padding:4.5rem 2.5rem 6rem; }
  h1,h2,h3,h4{ font-family:"Hanken Grotesk",sans-serif;
        letter-spacing:-.01em; line-height:1.22; color:#1c1a15; }
  h1{ font-size:2.4rem; font-weight:700; letter-spacing:-.025em;
      margin:0 0 1.6rem; }
  h2{ font-size:1.35rem; font-weight:600; margin:3rem 0 1rem;
      padding-bottom:.45rem; border-bottom:1px solid var(--line); }
  h3{ font-size:1.05rem; font-weight:600; margin:2rem 0 .5rem;
      color:var(--accent); }
  p,li{ color:#2f2c25; }
  a{ color:var(--accent); text-underline-offset:3px;
     text-decoration-thickness:1px; }
  strong{ font-weight:600; color:#1c1a15; }
  code{ font:500 .82em "IBM Plex Mono",monospace; background:var(--codebg);
        color:#5a4f3a; padding:.1em .4em; border-radius:4px; }
  pre{ background:var(--codebg); border:none; border-left:3px solid var(--accent);
       border-radius:0 6px 6px 0; padding:1.1rem 1.3rem; overflow-x:auto;
       line-height:1.5; }
  pre code{ background:none; padding:0; color:#3d3527; font-size:.8rem; }
  ul,ol{ padding-left:1.5rem; } li{ margin:.4rem 0; padding-left:.2rem; }
  ol li::marker{ color:var(--accent); font-family:"Hanken Grotesk";
       font-weight:600; }
  blockquote{ margin:1rem 0; padding-left:1rem; border-left:3px solid var(--line);
       color:var(--muted); }
  table{ border-collapse:collapse; width:100%; margin:1rem 0; }
  th,td{ border:1px solid var(--line); padding:.45rem .7rem; text-align:left; }
  th{ background:var(--codebg); font-family:"Hanken Grotesk"; }
  hr{ border:none; border-top:1px solid var(--line); margin:2.6rem 0; }
  @media(max-width:680px){ body{ font-size:17px; } main{ padding:3rem 1.3rem; } }
</style></head><body><main>
__BODY__
</main></body></html>
"""


def main() -> None:
    text, slug = get_source_markdown()

    md = MarkdownIt("commonmark").enable(["table", "strikethrough"])
    body = md.render(text)

    # Title = first H1 if present, else the slug.
    title = slug
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    out_html = TEMPLATE.replace("__TITLE__", html.escape(title)).replace(
        "__BODY__", body
    )

    out_path = os.path.join(tempfile.gettempdir(), f"{slug}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    subprocess.run(["open", out_path], check=False)
    print(out_path)


if __name__ == "__main__":
    main()
