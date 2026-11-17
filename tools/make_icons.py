"""Write the PNG icons in icons/ (no third-party libraries). Run: python tools/make_icons.py"""
import pathlib
import struct
import zlib

BG, FG = (37, 99, 235), (255, 255, 255)


def png(size, safe):
    # safe = fraction of the canvas the artwork may use (maskable icons need a safe zone)
    pix = [[BG] * size for _ in range(size)]
    m = size * (1 - safe) / 2
    span = size * safe
    heights = [0.35, 0.6, 0.45, 0.8]
    bw, gap = span * 0.16, span * 0.08
    x0 = m + (span - (4 * bw + 3 * gap)) / 2
    for i, h in enumerate(heights):
        xa, xb = int(x0 + i * (bw + gap)), int(x0 + i * (bw + gap) + bw)
        ya, yb = int(m + span * (0.9 - 0.8 * h)), int(m + span * 0.9)
        for y in range(ya, yb):
            for x in range(xa, xb):
                pix[y][x] = FG
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pix)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


out = pathlib.Path(__file__).resolve().parent.parent / "icons"
out.mkdir(exist_ok=True)
for name, size, safe in [("icon-192", 192, 0.9), ("icon-512", 512, 0.9),
                         ("icon-maskable-512", 512, 0.6), ("apple-touch-icon", 180, 0.9)]:
    (out / f"{name}.png").write_bytes(png(size, safe))
