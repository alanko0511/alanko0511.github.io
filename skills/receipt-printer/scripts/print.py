#!/usr/bin/env python3
"""Print to the V320L 80mm thermal receipt printer over the LAN (ESC/POS).

Usable two ways:

  CLI:
    python print.py --dry-run "Hello world"   # preview only; sends nothing (use to confirm first)
    python print.py "Hello world"
    echo "ticket #42" | python print.py --center --no-cut -
    python print.py --gbk "你好世界"          # Chinese (printer's default code page is GBK)

Printing is a physical side effect: preview with --dry-run and get the user's OK before
sending a real job (unless they've said to just print it).

  Module:
    from print import send, init, align, size, bold, text, feed, cut
    send(b"".join([init(), align(1), text("HI\n"), feed(4), cut()]))

Notes / gotchas (verified against real printouts):
  * Default code page is GBK (Chinese). ASCII prints clean; UTF-8 non-ASCII garbles into
    Chinese; emoji never works. Use text() for ASCII, or --gbk / chinese() for Chinese.
  * Width: 48 chars/line (Font A) or 64 (Font B). Lines hard-wrap and break mid-word.
  * Always feed before cutting or the last ~3 lines are lost.
"""
import argparse
import socket
import sys

PRINTER_IP = "192.168.2.250"
PRINTER_PORT = 9100

ESC = b"\x1b"
GS = b"\x1d"


# --- transport ---
def send(payload: bytes, ip: str = PRINTER_IP, port: int = PRINTER_PORT, timeout: float = 5.0):
    """Open a socket, send raw ESC/POS bytes, close. One job per connection."""
    s = socket.create_connection((ip, port), timeout=timeout)
    try:
        s.sendall(payload)
    finally:
        s.close()


# --- building blocks ---
def init():            return ESC + b"@"                         # reset to defaults
def text(s):           return s.encode("ascii", "replace")       # ASCII-safe; unknowns -> '?'
def chinese(s):        return s.encode("gbk")                    # GBK is the printer's default page
def align(n):          return ESC + b"a" + bytes([n])            # 0 left, 1 center, 2 right
def size(n):           return GS + b"!" + bytes([n])             # 0x00 normal, 0x11 2x, 0x01 tall, 0x10 wide
def bold(on):          return ESC + b"E" + (b"\x01" if on else b"\x00")
def underline(on):     return ESC + b"-" + (b"\x01" if on else b"\x00")
def invert(on):        return GS + b"B" + (b"\x01" if on else b"\x00")   # white-on-black
def font_b(on):        return ESC + b"M" + (b"\x01" if on else b"\x00")  # small font (64 cols)
def feed(n=4):         return ESC + b"d" + bytes([n])            # feed n lines
def cut():             return GS + b"V" + b"\x42" + b"\x00"      # partial cut (feed + cut)
def cut_full():        return GS + b"V" + b"\x00"                # full cut


def render(body: str, *, center=False, gbk=False, do_cut=True, feed_lines=4) -> bytes:
    """Build a simple text job. body is printed verbatim (add your own \\n)."""
    encode = chinese if gbk else text
    parts = [init()]
    if center:
        parts.append(align(1))
    parts.append(encode(body))
    if not body.endswith("\n"):
        parts.append(b"\n")
    parts.append(feed(feed_lines))
    if do_cut:
        parts.append(cut())
    return b"".join(parts)


def main(argv=None):
    p = argparse.ArgumentParser(description="Print text to the V320L receipt printer.")
    p.add_argument("text", help="Text to print, or '-' to read stdin.")
    p.add_argument("--center", action="store_true", help="Center-align the text.")
    p.add_argument("--gbk", action="store_true", help="Encode as GBK (for Chinese).")
    p.add_argument("--no-cut", dest="cut", action="store_false", help="Do not cut after printing.")
    p.add_argument("--feed", type=int, default=4, help="Lines to feed before cut (default 4).")
    p.add_argument("--dry-run", action="store_true",
                   help="Build and preview the job but DO NOT send it (use to confirm before printing).")
    p.add_argument("--ip", default=PRINTER_IP)
    p.add_argument("--port", type=int, default=PRINTER_PORT)
    args = p.parse_args(argv)

    body = sys.stdin.read() if args.text == "-" else args.text
    job = render(body, center=args.center, gbk=args.gbk, do_cut=args.cut, feed_lines=args.feed)

    if args.dry_run:
        print(f"[DRY RUN] Would send {len(job)} bytes to {args.ip}:{args.port}. Nothing was printed.")
        print("--- preview (text that will print) " + "-" * 12)
        print(body if body.endswith("\n") else body + "\n", end="")
        print("-" * 47)
        return

    send(job, ip=args.ip, port=args.port)
    print(f"Sent {len(job)} bytes to {args.ip}:{args.port}")


if __name__ == "__main__":
    main()
