#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate sample_fig.png with only the Python standard library.

This is a synthetic demo (no real data). It intentionally avoids fonts/CJK:
the goal is to prove the PNG can be embedded, not to replace Origin/Excel.

Usage: python3 make_sample_fig.py
"""
import struct
import zlib

W, H = 900, 520
buf = bytearray([255]) * (W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i + 3] = bytes(c)


def line(x0, y0, x1, y1, c, w=2):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for ox in range(-w // 2, w // 2 + 1):
            for oy in range(-w // 2, w // 2 + 1):
                px(x0 + ox, y0 + oy, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


L, R, T, B = 90, 860, 60, 460
line(L, T, L, B, (0, 0, 0), 2)
line(L, B, R, B, (0, 0, 0), 2)
for i in range(6):
    x = L + (R - L) * i // 5
    line(x, B, x, B + 8, (0, 0, 0), 1)
for i in range(5):
    y = B - (B - T) * i // 4
    line(L - 8, y, L, y, (0, 0, 0), 1)

prev = None
for i in range(41):
    x = L + (R - L) * i / 40
    y = B - (B - T) * (i / 40) ** 0.7
    if prev:
        line(int(prev[0]), int(prev[1]), int(x), int(y), (31, 78, 121), 3)
    prev = (x, y)

prev = None
for i in range(41):
    x = L + (R - L) * i / 40
    y = B - (B - T) * 0.75 * (i / 40) ** 0.9
    if prev:
        line(int(prev[0]), int(prev[1]), int(x), int(y), (197, 90, 17), 3)
    prev = (x, y)

# A small black bar as a visual title placeholder (no fonts).
for i in range(30):
    px(110 + i * 10, 85, (0, 0, 0))
    px(110 + i * 10, 86, (0, 0, 0))

raw = bytearray()
for y in range(H):
    raw.append(0)
    raw.extend(buf[y * W * 3:(y + 1) * W * 3])


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
       + chunk(b"IEND", b""))
with open("sample_fig.png", "wb") as f:
    f.write(png)
print("wrote sample_fig.png", len(png), "bytes")
