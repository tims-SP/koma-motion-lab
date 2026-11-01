"""Shared palette + reusable anime feature builders for KomaMotion P0 design SVGs.
Identity source: identity_spec.json (palette + asymmetric features).
All drawings are hand-authored cel-style vector art (no 3D shading, no raster).
"""
import os

OUT = "/root/koma-p0-designs/design"
os.makedirs(OUT, exist_ok=True)

# --- palette (identity_spec.json) ---
SKIN    = "#FFE9E1"
SKIN_SH = "#F6D3CB"
SKIN_LN = "#D8A79C"
HAIR    = "#C27A98"
HAIR_SH = "#8C5574"
HAIR_LT = "#DC9FB6"
HAIR_HL = "#EAB9C8"
IRIS    = "#B65A8C"
IRIS_DK = "#7E3A61"
IRIS_LT = "#D981AE"
PUPIL   = "#3A2233"
LINE    = "#5A3A4E"
LASH    = "#3B2333"
JACKET  = "#3B3A51"
JACKET_DK = "#2A293B"
JACKET_LT = "#4C4B66"
SHIRT   = "#FFFFFF"
SHIRT_SH= "#E7E1E6"
BOW     = "#8C3A54"
BOW_DK  = "#6B2A3E"
GOLD    = "#D4AF37"
GOLD_LT = "#F0DB92"
GOLD_DK = "#9A7A20"
BLUSH   = "#F3A9A2"
WHITE   = "#FFFFFF"


def svg_open(w, h, vb):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" width="%d" height="%d">\n'
            % (vb, w, h))


def write_svg(name, body):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


def eye_group(cx, cy, cid, flip=1, sx=1.0, tag="eye", lid=True):
    """Anime eye: white sclera, layered pink-violet iris, pupil, highlights,
    heavy tapered upper lash with outer flick, lower lash accent, lid crease.
    flip=1 -> outer corner at +x (character's LEFT eye on screen-right).
    flip=-1 -> mirrored (character's RIGHT eye).  sx -> horizontal squash."""
    ap    = "M-37-4C-32-26-14-36 4-33C24-30 34-18 37 2C30 22 12 30-6 27C-22 24-33 12-37-4Z"
    lash  = "M-40-10C-35-34-14-44 6-40C26-37 37-24 41-2L36 4C32-17 22-28 6-31C-12-34-28-26-33-6Z"
    flick = "M38-6C45-12 51-20 55-28C51-16 48-8 44 0Z"
    t = "translate(%s,%s) scale(%s,1)" % (cx, cy, flip * sx)
    s  = '<g id="%s" transform="%s">\n' % (tag, t)
    s += '  <clipPath id="%s"><path d="%s"/></clipPath>\n' % (cid, ap)
    if lid:
        s += ('  <path d="M-44-12C-40-40-10-52 22-44C40-40 46-20 44 14C36 34 6 40-16 30C-36 20-46 2-44-12Z"'
              ' fill="%s" stroke="none"/>\n' % SKIN)
    s += '  <path d="%s" fill="%s" stroke="%s" stroke-width="2"/>\n' % (ap, WHITE, LINE)
    s += '  <g clip-path="url(#%s)">\n' % cid
    s += '    <ellipse cx="2" cy="-3" rx="19.5" ry="25" fill="%s"/>\n' % IRIS_DK
    s += '    <ellipse cx="2" cy="1" rx="17.5" ry="21.5" fill="%s"/>\n' % IRIS
    s += '    <ellipse cx="2" cy="12" rx="14" ry="9" fill="%s" opacity="0.9"/>\n' % IRIS_LT
    s += '    <ellipse cx="2" cy="0" rx="5.5" ry="12.5" fill="%s"/>\n' % PUPIL
    s += '    <path d="M-13 12C-6 20 10 20 16 11" fill="none" stroke="#FBD6E6" stroke-width="2.6" stroke-linecap="round"/>\n'
    s += '    <circle cx="-6" cy="-11" r="6.2" fill="%s"/>\n' % WHITE
    s += '    <circle cx="9" cy="11" r="3" fill="%s" opacity="0.9"/>\n' % WHITE
    s += '    <circle cx="-11" cy="4" r="2" fill="%s" opacity="0.7"/>\n' % WHITE
    s += '  </g>\n'
    s += '  <path d="%s" fill="%s" stroke="%s" stroke-width="1" stroke-linejoin="round"/>\n' % (lash, LASH, LASH)
    s += '  <path d="%s" fill="%s"/>\n' % (flick, LASH)
    s += '  <path d="M-33 13C-20 29 8 35 29 21" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round"/>\n' % LASH
    s += '  <path d="M-27 25L-34 32M-17 29L-22 37" stroke="%s" stroke-width="1.8" stroke-linecap="round"/>\n' % LASH
    s += '  <path d="M-30-22C-16-42 14-47 33-31" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity="0.85"/>\n' % SKIN_LN
    s += '</g>\n'
    return s


def hairpin_group(x, y, rot=0, scale=1.0, tag="gold-hairpin"):
    """Two close staggered crossed gold barrettes (cross motif)."""
    s  = '<g id="%s" transform="translate(%s,%s) rotate(%s) scale(%s)">\n' % (tag, x, y, rot, scale)
    s += '  <rect x="-23" y="-4" width="46" height="8" rx="4" fill="%s" stroke="%s" stroke-width="1.4" transform="rotate(-34)"/>\n' % (GOLD, GOLD_DK)
    s += '  <rect x="-22" y="-4" width="46" height="8" rx="4" fill="%s" stroke="%s" stroke-width="1.4" transform="rotate(32)"/>\n' % (GOLD_LT, GOLD_DK)
    s += '  <rect x="-19" y="-2.4" width="30" height="2.4" rx="1.2" fill="#F7E6A8" transform="rotate(-34)"/>\n'
    s += '  <rect x="-17" y="-2.4" width="26" height="2.2" rx="1.1" fill="#FBF0C4" transform="rotate(32)"/>\n'
    s += '</g>\n'
    return s


def ahoge_group(x, y, scale=1.0, rot=0, tag="ahoge"):
    """Single crown strand that curves toward screen-left in the front view."""
    s  = '<g id="%s" transform="translate(%s,%s) rotate(%s) scale(%s)">\n' % (tag, x, y, rot, scale)
    s += ('  <path d="M0 0C-4-24-20-42-42-50C-62-57-76-67-80-81C-82-89-74-93-68-87C-62-79-52-73-38-67C-14-57 2-41 8-19C11-7 8 0 0 0Z"'
          ' fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M-6-16C-18-30-32-38-46-43C-58-47-68-55-74-64C-68-52-56-46-42-40C-24-32-12-24-6-16Z" fill="%s" opacity=".85"/>\n' % HAIR_SH
    s += '</g>\n'
    return s


def brow_group(cx, cy, flip=1, tag="brow"):
    s  = '<g id="%s" transform="translate(%s,%s) scale(%s,1)">\n' % (tag, cx, cy, flip)
    s += '  <path d="M-34 4C-24-6-4-10 16-4C26-1 32 2 36 5" fill="none" stroke="%s" stroke-width="4.4" stroke-linecap="round"/>\n' % HAIR_SH
    s += '  <path d="M-30 0C-18-9 0-12 18-6" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round" opacity=".7"/>\n' % HAIR
    s += '</g>\n'
    return s


def mouth_closed(cx, cy, scale=1.0, tag="mouth-closed"):
    s  = '<g id="%s" transform="translate(%s,%s) scale(%s)">\n' % (tag, cx, cy, scale)
    s += '  <path d="M-24 0C-14-6 14-6 24-2C16 7-8 8-24 0Z" fill="#E7A8A0" stroke="#A65A62" stroke-width="2.4" stroke-linejoin="round"/>\n'
    s += '  <path d="M-22 0C-10 4 10 4 22-1" fill="none" stroke="#A65A62" stroke-width="2"/>\n'
    s += '  <path d="M-12 8C-4 12 6 12 12 8" fill="none" stroke="#F0C4BC" stroke-width="2.4" stroke-linecap="round"/>\n'
    s += '</g>\n'
    return s


def mouth_open(cx, cy, scale=1.0, tag="mouth-open"):
    s  = '<g id="%s" transform="translate(%s,%s) scale(%s)">\n' % (tag, cx, cy, scale)
    s += '  <path d="M-26-2C-16-9 16-9 26-2C24 14 14 26 0 26C-14 26-24 14-26-2Z" fill="#8C3A54" stroke="#5A3A4E" stroke-width="2.6"/>\n'
    s += '  <path d="M-22 0C-12-6 12-6 22 0C18 8 8 12 0 12C-8 12-18 8-22 0Z" fill="#C25A72" opacity=".95"/>\n'
    s += '  <path d="M-13 12C-6 22 8 22 13 12C6 16-6 16-13 12Z" fill="#E9A0AE" opacity=".9"/>\n'
    s += '  <path d="M-16-4C-10-9 10-9 16-4C8-1-8-1-16-4Z" fill="#FFFFFF"/>\n'
    s += '  <path d="M-26-2C-16-9 16-9 26-2" fill="none" stroke="#5A3A4E" stroke-width="2.6" stroke-linecap="round"/>\n'
    s += '</g>\n'
    return s
