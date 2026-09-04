"""Generate a simple vector-free Q1 browser icon as PNG/ICO via a PAM image.

This is a build-time helper; the generated assets are committed to the repo so
Windows builds do not need Python drawing libraries.
"""
import struct

SIZE = 256


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def inside_round_rect(x, y, w, h, r):
    if x < 0 or y < 0 or x >= w or y >= h:
        return False
    dx = min(x, w - 1 - x)
    dy = min(y, h - 1 - y)
    if dx >= r or dy >= r:
        return True
    cx = r
    cy = r
    if dx < r:
        cx = r - dx
    if dy < r:
        cy = r - dy
    return (cx - r) ** 2 + (cy - r) ** 2 <= r * r


def make_pixels():
    w = h = SIZE
    c1 = (27, 110, 243)
    c2 = (0, 180, 216)
    px = bytearray()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (2 * SIZE)
            rgb = lerp_color(c1, c2, t)
            alpha = 255
            if not inside_round_rect(x + 0.5, y + 0.5, w, h, 48):
                alpha = 0
            # White "Q" as a ring
            cx, cy = 98, 126
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 42 <= dist <= 62:
                rgb = (255, 255, 255)
            # Q tail: a slanted rounded rectangle
            tx = 116 + (y - 136) * 0.55 if y > 136 else 0
            if 126 <= y <= 174 and 108 <= x <= 148:
                if 108 <= x + (y - 136) * 0.55 <= 148:
                    rgb = (255, 255, 255)
            # White "1"
            if 72 <= y <= 184 and 172 <= x <= 196:
                rgb = (255, 255, 255)
            if 56 <= y <= 86 and 168 <= x <= 184:
                dx = (x - 176) / 12.0
                dy = (y - 86) / 18.0
                if abs(dx) <= dy:
                    rgb = (255, 255, 255)
            # Yellow AI sparkle badge
            if (x - 200) ** 2 + (y - 62) ** 2 <= 22 ** 2:
                rgb = (255, 214, 10)
            # Check mark inside the badge
            if (x - 200) ** 2 + (y - 62) ** 2 <= 22 ** 2:
                sx, sy = x - 200 + 62, y - 62  # placeholder not used
            # Small white check
            if 188 <= x <= 212 and 52 <= y <= 72:
                d1 = abs((y - 72) - 0.7 * (x - 188))
                d2 = abs((y - 52) - (-0.9) * (x - 212))
                if 195 <= x <= 212 and 52 <= y <= 72 and d2 <= 3:
                    rgb = (255, 255, 255)
                if 188 <= x <= 198 and 58 <= y <= 72 and d1 <= 3:
                    rgb = (255, 255, 255)
            px += bytes(rgb) + bytes([alpha])
    return bytes(px)


def write_pam(path):
    data = make_pixels()
    header = (
        b"P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
        % (SIZE, SIZE)
    )
    with open(path, "wb") as fh:
        fh.write(header + data)


if __name__ == "__main__":
    write_pam("assets/icon.pam")
    print("wrote assets/icon.pam")
