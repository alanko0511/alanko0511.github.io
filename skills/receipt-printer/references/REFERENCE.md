# Receipt Printer — Technical Reference

Deep reference for the V320L 80mm thermal printer. The main [SKILL.md](../SKILL.md) covers
everyday printing; this file holds the full command set, encoding details, debugging, and
network reconfiguration. Load it when you need more than basic text printing.

## Device facts

| | |
|---|---|
| Model | V320L — generic 80mm Xprinter/Zjiang-family clone |
| Command set | ESC/POS (Epson standard) |
| Interfaces | USB + LAN (10/100M Ethernet); we use LAN |
| Current IP | **`192.168.2.250`** (static, DHCP disabled) |
| Print port | **`9100`** (raw / JetDirect) |
| Subnet / gateway | `255.255.255.0` / `192.168.123.1` (stale; harmless for same-subnet printing) |
| MAC | `00:61:7B:6B:49:5A` |
| Firmware | `7.004PAOG` |
| Factory-default IP | `192.168.123.100` (what it reverts to on reset) |
| Features | auto-cutter, beeper, cash-drawer kick (24V), QR/PDF417/DataMatrix, 200 mm/s |
| Print geometry | ~576 dot width; 48 chars/line Font A, 64 chars/line Font B (48-col divider verified on paper) |

## Encoding (the #1 gotcha)

**The printer's default code page is GBK (Chinese GB2312/GB18030).** Verified: `é`
(UTF-8 `c3 a9`) prints as the Chinese char `茅`, exactly what `bytes([0xc3,0xa9]).decode("gbk")`
yields. Consequences:

- **ASCII** (incl. all punctuation/symbols) → prints perfectly.
- **Non-ASCII as UTF-8** → multibyte bytes reinterpreted as GBK double-byte → wrong Chinese
  (`café`→`caf茅`, `£`→`拢`, `¥`→`楼`, `°`→`掳`, `½`→`陆`).
- **Emoji / 3-byte UTF-8** (`€ • →`) → garbage, and can desync the byte stream.
- **Chinese works for free**: `text.encode("gbk")` (e.g. `你好` → `c4 e3 ba c3`).
  Verified on paper: `谢谢惠顾 欢迎再来` sent via GBK printed as clean Chinese (no FS& Kanji-mode
  switch needed — direct GBK bytes are enough since GBK is already the default page).
- **Traditional Chinese works too** (not just Simplified). GBK is a superset that encodes
  traditional characters, and this unit's font ROM has the glyphs — verified on paper:
  `哈囉，世界！` and the traditional-only probe `體 灣 學 龍 國` all rendered clean (these differ
  from their simplified forms 啰/体/湾/学/龙/国). So `s.encode("gbk")` covers both scripts; no
  Big5 needed (and Big5 is not supported anyway). Note "Hello World" itself is `你好，世界` —
  glyph-identical in both scripts (Han unification), so it's not a distinct traditional test.

To print **Latin accents / € / £**, select a Latin code page first with `ESC t n`, then
encode bytes to match that page. The `n`→codepage map varies on these clones — trial a
couple and keep what renders `é`/`£` right:

```python
# ESC t n  selects code page n. Try n=0 (CP437), n=16 (CP1252/WPC1252), n=2 (CP850).
send(ESC + b"@" + ESC + b"t" + bytes([16]) + "café £5 50°".encode("cp1252", "replace")
     + b"\n" + feed() + cut())
```

(`ESC` = `0x1B`, `GS` = `0x1D` throughout.)

## Full ESC/POS command set

### Verified working
| Action | Bytes | Notes |
|---|---|---|
| Initialize | `1B 40` | Always start with this; resets modes |
| Align | `1B 61 n` | n = 0 left / 1 center / 2 right |
| Character size | `1D 21 n` | `00` normal, `11` double w+h, `01` double height, `10` double width |
| Bold | `1B 45 n` | n = 1 / 0 |
| Underline | `1B 2D n` | n = 1 / 0 |
| Invert (white/black) | `1D 42 n` | n = 1 / 0 |
| Font A / B | `1B 4D n` | 0 = Font A (48 cols), 1 = Font B (64 cols) |
| Default line spacing | `1B 32` | |
| Set line spacing | `1B 33 n` | n dots |
| Feed n lines | `1B 64 n` | **always feed before cutting** |
| Partial cut | `1D 56 42 00` | feed + cut (recommended) |
| Full cut | `1D 56 00` | |
| Select code page | `1B 74 n` | see Encoding above |

### Not yet tested on this unit (standard ESC/POS — try when needed)
| Feature | Command | Notes |
|---|---|---|
| QR code | `GS ( k` = `1D 28 6B ...` | store data (fn 80) then print (fn 81); set size with fn 67 |
| Barcode | `GS k` = `1D 6B m ...` | Code128 = m 73; set height `1D 68 n`, width `1D 77 n` |
| Raster image / logo | `GS v 0` = `1D 76 30 m xL xH yL yH <data>` | convert PNG → 1-bit dithered, row-major bitmap |
| Cash-drawer kick | `ESC p m t1 t2` = `1B 70 00 19 FA` | pin 2 pulse; clicks even with no drawer attached |
| Beep | vendor-specific on clones | test before relying on it |

#### QR helper sketch
```python
def qr(data: bytes, module=6, ecc=49):  # ecc: 48=L 49=M 50=Q 51=H
    store = b"\x1d(k" + (len(data)+3).to_bytes(2,"little") + b"\x31\x50\x30" + data
    size  = b"\x1d(k\x03\x00\x31\x43" + bytes([module])
    err   = b"\x1d(k\x03\x00\x31\x45" + bytes([ecc])
    prnt  = b"\x1d(k\x03\x00\x31\x51\x30"
    return size + err + store + prnt
# send(b"".join([init(), align(1), qr(b"https://example.com"), feed(4), cut()]))
```

## Debugging

### Self-test / config page (ground truth)
Power **off** → **hold FEED** → power **on**, keep holding ~2s → release. Prints firmware
version, interface, **MAC, IP, subnet, gateway, DHCP state**, and feature flags. Works
regardless of network config — the definitive way to learn the current IP.

### Open ports / protocol notes
- Only **9100** (raw ESC/POS) and **80** are open. **Port 80's web server is a dead stub** —
  it accepts the TCP connection but never returns an HTTP response. No usable web UI.
- No LPR/515, no IPP/631, no telnet/23.
- 9100 is one-job-per-connection: open, send the whole job, close.

## Network

### Find it on the LAN
These ship with **DHCP disabled** and static default **`192.168.123.100`**, so on a normal
`192.168.2.x` LAN they're invisible. Sweep, then probe the raw-print port:

```bash
# 1) ping-sweep to populate ARP
for i in $(seq 1 254); do ping -c1 -W200 192.168.2.$i >/dev/null 2>&1 & done; wait
# 2) probe TCP 9100 (the fingerprint of an ESC/POS net printer)
for ip in $(arp -an | grep -oE '192\.168\.2\.[0-9]+'); do
  nc -z -G2 -w2 $ip 9100 2>/dev/null && echo "$ip 9100 OPEN"; done
# 3) or find the printer by MAC
arp -an | grep -i 00:61:7b:6b:49:5a
```

### Reach a printer stuck on the 192.168.123.x default
Give your Mac a temporary 2nd IP in that subnet (same physical LAN = reachable):
```bash
sudo ifconfig en8 alias 192.168.123.50 255.255.255.0    # en8 = active wired iface; check via: route -n get default
ping 192.168.123.100 && nc -z -w2 192.168.123.100 9100  # now reachable
sudo ifconfig en8 -alias 192.168.123.50                 # remove when done
```

### Change the printer's IP (how we put it on the LAN)
Official Xprinter/Zjiang set-IP command, sent over 9100 to the printer's **current** IP:

```
1F 1B 1F 91 00 49 50  <ip1> <ip2> <ip3> <ip4>      (49 50 = ASCII "IP")
```
```python
import socket
cmd = bytes([0x1F,0x1B,0x1F,0x91,0x00,0x49,0x50, 192,168,2,250])  # -> 192.168.2.250
s = socket.create_connection(("192.168.123.100", 9100), timeout=5)  # send to CURRENT ip
s.sendall(cmd); s.close()
```
- Printer **beeps** on accept (we observed **two beeps** = accepted + network restart).
- **Applies immediately, no power-cycle needed** (observed). Verify: `ping`/`nc 9100` on the
  new IP, or a fresh self-test.
- Pick a static IP **outside the router's DHCP pool** (e.g. `.250`) to avoid lease collisions.

Other documented net commands (reverse-engineered; vary by firmware — the IP-only command
above is the most reliable):

| Purpose | Bytes |
|---|---|
| Set IP (alt code) | `1F 1B 1F 22` + ip(4) |
| Set subnet mask | `1F 1B 1F B0` + mask(4) |
| Set gateway | `1F 1B 1F B1` + gw(4) |
| Set IP + mask + gateway | `1F 1B 1F B2` + ip(4) + mask(4) + gw(4) |
| Set WiFi (wifi models only) | `1F 1B 1F B3` (ssid/key) / `B4` (all) |

### You can't brick it (recovery)
These commands only rewrite **network settings in NVRAM** — never firmware, the print
mechanism, or the bootloader. Worst case the IP lands somewhere unexpected; recover by:
self-test print → read the actual IP → re-add a matching Mac alias (above) → retry.

## Quick reference card
```
IP:PORT   192.168.2.250:9100   (raw ESC/POS)
Self-test FEED + power-on, hold ~2s
Find it   ping-sweep + probe TCP 9100; ARP MAC 00:61:7b:6b:49:5a
Set IP    1F 1B 1F 91 00 49 50 + <4 ip bytes>   (beeps, applies live)
Encoding  default page = GBK; ASCII safe; Chinese via .encode('gbk'); accents need ESC t n
Width     48 chars (Font A) / 64 (Font B); hard-wrap, breaks mid-word
Cut       feed first, then 1D 56 42 00 (partial)
```
