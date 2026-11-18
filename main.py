#!/usr/bin/env python3
"""News image for 18 Nov 2026 — stdlib only, byte-level PNG."""
import struct, zlib, os, sys

W, H = 1024, 1024
ROW = W * 4  # bytes per row

# Pre-allocate canvas
canvas = bytearray(b'\x12\x12\x18\xff' * (W * H))

def rgba(r, g, b, a=255):
    return bytes([r, g, b, a])

def fill_rect(x1, y1, x2, y2, color):
    if x1 >= W or y1 >= H or x2 <= 0 or y2 <= 0:
        return
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    if x2 <= x1 or y2 <= y1:
        return
    span = (x2 - x1) * 4
    row_start = y1 * ROW + x1 * 4
    for y in range(y1, y2):
        off = row_start + (y - y1) * ROW
        canvas[off:off + span] = color * (x2 - x1)

def fill_circle(cx, cy, r, color):
    x1 = max(0, int(cx - r))
    y1 = max(0, int(cy - r))
    x2 = min(W, int(cx + r + 1))
    y2 = min(H, int(cy + r + 1))
    rr = r * r
    for y in range(y1, y2):
        dy = y - cy
        dx_limit = int((rr - dy*dy) ** 0.5)
        lx = max(0, int(cx) - dx_limit)
        rx = min(W, int(cx) + dx_limit + 1)
        if rx > lx:
            off = y * ROW + lx * 4
            canvas[off:off + (rx - lx) * 4] = color * (rx - lx)

# Colors
C_ACCENT = rgba(0, 229, 255)
C_WARN   = rgba(255, 140, 0)
C_ALERT  = rgba(255, 50, 50)
C_WHITE  = rgba(240, 240, 245)
C_GRAY   = rgba(100, 100, 115)
C_DARK   = rgba(30, 30, 40)
C_CARD   = rgba(40, 40, 55)
C_BANNER = rgba(10, 10, 20)
C_GREEN  = rgba(0, 255, 150)
C_PURPLE = rgba(180, 100, 255)
C_YELLOW = rgba(255, 200, 50)
C_BLUE   = rgba(100, 200, 255)

# ── Layout ──
fill_rect(0, 0, W, 80, C_BANNER)        # top strip
fill_rect(0, 78, W, 82, C_ACCENT)        # accent line
fill_rect(0, 0, 4, H, C_ACCENT)          # left stripe

# Date banner
fill_rect(30, 95, W - 30, 185, C_CARD)
fill_rect(30, 95, W - 30, 101, C_ACCENT)

# 6 news cards (2 col × 3 row)
card_w, card_h = 460, 175
gap_x, gap_y = 32, 30
start_x, start_y = 30, 210

cards = [
    (start_x, start_y, C_ACCENT,  "GLOBAL"),
    (start_x + card_w + gap_x, start_y, C_GREEN,  "TECH"),
    (start_x, start_y + card_h + gap_y, C_WARN,   "ENERGY"),
    (start_x + card_w + gap_x, start_y + card_h + gap_y, C_PURPLE, "POLICY"),
    (start_x, start_y + 2*(card_h + gap_y), C_YELLOW, "ECONOMY"),
    (start_x + card_w + gap_x, start_y + 2*(card_h + gap_y), C_BLUE,  "CLIMATE"),
]

for cx, cy, color, _label in cards:
    fill_rect(cx, cy, cx + card_w, cy + card_h, C_CARD)
    fill_rect(cx, cy, cx + card_w, cy + 6, color)
    # accent dot pattern inside card
    fill_circle(cx + 30, cy + 55, 10, color)
    fill_circle(cx + 65, cy + 55, 6, rgba(color[0], color[1], color[2], 120))
    fill_circle(cx + 88, cy + 55, 4, rgba(color[0], color[1], color[2], 80))
    # right-side dots
    for i in range(4):
        fill_circle(cx + card_w - 20, cy + 40 + i * 35, 4 + i % 2,
                    rgba(color[0], color[1], color[2], 130 - i * 30))

# Footer
fill_rect(0, H - 50, W, H, C_DARK)
fill_rect(0, H - 50, W, H - 46, C_GRAY)

# ── PNG encode ──
def chunk(ctype, data):
    c = ctype + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

sig = b"\x89PNG\r\n\x1a\n"
ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))

# Add filter byte 0 per row
filtered = b""
for row in range(H):
    filtered += b"\x00" + bytes(canvas[row * ROW:(row + 1) * ROW])

idat = chunk(b"IDAT", zlib.compress(filtered, 9))
iend = chunk(b"IEND", b"")
png = sig + ihdr + idat + iend

out = "/output/entry.png"
os.makedirs("/output", exist_ok=True)
with open(out, "wb") as f:
    f.write(png)

size_kb = len(png) / 1024
print(f"done: {out} ({size_kb:.1f}KB, {W}x{H})")

# Verify
assert len(png) < 1048576, f"Too large: {len(png)} > 1MB"
assert W <= 1024 and H <= 1024, "Size exceeds 1024x1024"