---
name: receipt-printer
description: |
  Use this skill any time the user wants a physical paper copy of something to come out of the small thermal/receipt printer in their room or home. Trigger on casual phrasings like "print this", "print me a ___", "print out", "spit out", "throw it on the printer", or "print X on the receipt/thermal printer" — where X is a note, memo, reminder, message, label, sign, sticker, grocery/to-do/shopping list, QR code, or any short text (English or Chinese). If the request is for real paper coming out of a machine, this skill applies — that's the whole job. The hardware is a V320L 80mm ESC/POS printer at 192.168.2.250:9100; also use this to find, debug, or reconfigure it on the network.

  Do NOT trigger for digital-only actions: saving notes/todos in an app, exporting to PDF, scanning, screenshots ("print screen"), or programming output like Python print()/console.log.
metadata:
  model: V320L
  printer-ip: 192.168.2.250
  printer-port: "9100"
  command-set: ESC/POS
compatibility: Requires Python 3 and network access to 192.168.2.250:9100 on the local LAN.
---

# Receipt Printer (V320L)

A personal 80mm thermal printer used for **notes, memos, lists, and reminders** (despite
the "receipt printer" hardware label, it's not used for retail receipts). Print to it over
the LAN using ESC/POS commands.

> [!IMPORTANT]
> **Confirm before sending.** Printing is a physical, irreversible side effect — paper
> comes out of a machine in the user's space. Before you actually send a job, show the user
> a short preview of what you're about to print (the text/layout) and get a clear go-ahead.
> Build the job and preview it with `python scripts/print.py --dry-run "..."` (renders the
> exact content + byte count, sends nothing). Only send once they confirm.
> If the user has clearly opted out of confirmation for this request ("just print it",
> "don't ask, print N copies"), honor that and skip the prompt — the goal is no *surprise*
> printing, not friction for someone who knows what they want.

## At a glance

- **Where:** `192.168.2.250`, TCP port **`9100`** (raw / JetDirect). Static IP, DHCP off.
- **Model:** V320L — generic 80mm Xprinter/Zjiang-family clone. **ESC/POS** command set.
- **Has:** auto-cutter, beeper, cash-drawer kick, 2D barcodes (QR/PDF417/DataMatrix).
- **Print width:** **48 chars/line** (Font A, default) · **64 chars/line** (Font B, small).

## How to print (preferred: Python)

Open a TCP socket to `192.168.2.250:9100`, send ESC/POS bytes, close. One job per
connection. Use the bundled helper — `scripts/print.py` — either as a CLI or a module:

```bash
# Step 1 — preview WITHOUT sending (show this to the user, get the go-ahead)
python scripts/print.py --dry-run "Hello from Claude"

# Step 2 — actually print once confirmed (auto-initializes + feeds + cuts)
python scripts/print.py "Hello from Claude"

# Other options: center, no cut, read piped text, Chinese
echo "ticket #42" | python scripts/print.py --center --no-cut -
python scripts/print.py --gbk "你好世界"
```

```python
# Module: full control
from print import send, init, align, size, bold, text, feed, cut, ESC, GS
send(b"".join([
    init(),
    align(1), size(0x11), text("MY STORE\n"), size(0x00),
    align(0),
    text(f"{'Coffee':<40}{'$4.50':>8}\n"),   # pad columns to 48 wide
    bold(True), text(f"{'TOTAL':<40}{'$4.50':>8}\n"), bold(False),
    feed(4), cut(),
]))
```

Quick no-Python smoke test:
```bash
printf '\x1b@Hello\n\n\n\x1dV\x42\x00' | nc 192.168.2.250 9100
```

## Critical rules (read before printing)

1. **ASCII is safe; everything else is not.** The printer's default code page is **GBK
   (Chinese)**. Plain ASCII (letters, digits, ``!@#$%^&*()_+-=[]{}|;:,.<>/?~` ``) prints
   perfectly. **Non-ASCII sent as UTF-8 turns into random Chinese** (e.g. `café` → `caf茅`),
   and emoji never works. Default to ASCII: `s.encode("ascii", "replace")`.
2. **To print Chinese**, encode the text as **GBK** (`s.encode("gbk")`) — it works with no
   setup because GBK is the default page. **Both Simplified and Traditional render** — the
   font ROM includes the GBK-extended traditional glyphs (verified on paper). **Default to
   Traditional Chinese** when the user asks to print Chinese (unless they say Simplified). For
   Latin accents / € / £, you must select a Latin code page first (`ESC t n`); see
   `references/REFERENCE.md`.
3. **Always feed before cutting** (`feed(3+)` then `cut()`). The blade sits above the head,
   so the last ~3 lines are lost otherwise.
4. **Lines hard-wrap at 48 (Font A) / 64 (Font B)** and break mid-word. Pad/truncate your
   own lines for clean columns: `f"{name:<40}{price:>8}"`.

## Keep it plain by default

Default to **plain text**: just the content, left-aligned, using blank lines and simple
spacing/column padding for readability. Notes and memos are meant to be unfussy, and heavy styling
(double-size, bold, inverted text, separator rules, centered banners) is easy to overdo and
makes output look cluttered. So reach for the formatting commands below **only when the user
asks** ("make the title big", "add a divider line", "center it") or the content genuinely
calls for it. Plain spacing and alignment are always fine; decorative styling is opt-in.
When in doubt, less is better.

## ESC/POS essentials (verified on this unit)

| Action | Bytes | Helper |
|---|---|---|
| Initialize (always first) | `1B 40` | `init()` |
| Align (0 L / 1 C / 2 R) | `1B 61 n` | `align(n)` |
| Size (`00` normal, `11` 2x, `01` tall, `10` wide) | `1D 21 n` | `size(n)` |
| Bold on/off | `1B 45 n` | `bold(b)` |
| Underline on/off | `1B 2D n` | `underline(b)` |
| Invert (white-on-black) | `1D 42 n` | `invert(b)` |
| Small font (B) on/off | `1B 4D n` | `font_b(b)` |
| Feed n lines | `1B 64 n` | `feed(n)` |
| **Partial cut** (feed + cut) | `1D 56 42 00` | `cut()` |
| Full cut | `1D 56 00` | — |

For QR codes, barcodes, raster logos, cash-drawer kick, the full debug playbook, network
discovery, and reconfiguring the printer's IP, see **[references/REFERENCE.md](references/REFERENCE.md)**.

## If the printer can't be reached

`192.168.2.250` is a static IP we set. If it stops responding it likely reset to its
factory default `192.168.123.100` (DHCP disabled), which is off this LAN. Recovery and
the network-reconfig commands are in **[references/REFERENCE.md](references/REFERENCE.md)** (§"Network"). Quick check:

```bash
ping -c2 192.168.2.250 && nc -z -w2 192.168.2.250 9100 && echo OK
```
