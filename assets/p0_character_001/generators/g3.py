"""Independent organ sheets (design drafts) + manifest.
Anatomical convention: character's LEFT = screen RIGHT in front view."""
from common import *
import json


def part_eye(path, flip, tag, label=""):
    s = svg_open(260, 220, "0 0 260 220")
    s += '<g id="%s">\n' % tag
    # eyelid / eye-socket skin shape (design-draft context)
    s += ('  <path d="M34 112C34 60 74 28 130 28C186 28 226 60 226 112C226 158 190 186 130 186'
          'C70 186 34 158 34 112Z" fill="%s" opacity=".55"/>\n' % SKIN)
    s += eye_group(130, 108, "clip-%s" % tag, flip=flip, tag="eye")
    # eyelid lines (upper lid crease + lower lid)
    s += '  <path d="M38 104C44 58 82 30 130 30C180 30 220 58 224 104" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>\n' % LINE
    s += '  <path d="M44 124C58 158 92 176 130 176C168 176 202 158 216 124" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>\n' % LINE
    s += '  <path d="M46 96C60 56 92 40 130 40C170 40 202 58 216 96" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" opacity=".7"/>\n' % SKIN_LN
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg(path, s)


def part_nose():
    s = svg_open(420, 260, "0 0 420 260")
    s += '<g id="nose-design">\n'
    # --- frontal nose ---
    s += '  <g id="nose-front">\n'
    s += '    <path d="M120 20C132 34 136 60 132 84C129 100 118 112 104 116" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round"/>\n' % SKIN_LN
    s += '    <path d="M126 26C136 42 140 66 136 88" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" opacity=".65"/>\n' % SKIN_SH
    s += '    <path d="M96 112C104 118 116 118 124 112" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round"/>\n' % SKIN_LN
    s += '    <ellipse cx="104" cy="74" rx="6" ry="4" fill="%s" transform="rotate(-12 104 74)"/>\n' % WHITE
    s += '    <path d="M92 122C104 128 122 128 134 120" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" opacity=".7"/>\n' % SKIN_SH
    s += '  </g>\n'
    # --- profile nose ---
    s += '  <g id="nose-profile" transform="translate(250,0)">\n'
    s += '    <path d="M40 22C46 50 54 78 68 96C76 106 86 112 100 114C88 110 80 102 76 92C68 74 60 48 56 22Z" fill="%s" opacity=".5"/>\n' % SKIN_SH
    s += '    <path d="M40 22C44 48 52 76 66 94C74 104 84 110 98 112" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>\n' % LINE
    s += '    <path d="M96 112C104 116 112 114 116 108" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round"/>\n' % LINE
    s += '    <path d="M92 104C98 106 106 104 110 98" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round"/>\n' % LINE
    s += '    <ellipse cx="84" cy="88" rx="6" ry="4" fill="%s" transform="rotate(34 84 88)"/>\n' % WHITE
    s += '    <path d="M100 118C110 122 120 124 128 122" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>\n' % SKIN_LN
    s += '  </g>\n'
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_nose.svg", s)


def part_mouth():
    s = svg_open(420, 260, "0 0 420 260")
    s += '<g id="mouth-design">\n'
    s += '  <g id="mouth-closed">\n'
    s += mouth_closed(120, 90, scale=1.6, tag="closed-lips")
    s += '    <path d="M62 150C88 162 152 162 178 150" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".7"/>\n' % SKIN_LN
    s += '  </g>\n'
    s += '  <g id="mouth-open" transform="translate(200,0)">\n'
    s += mouth_open(110, 92, scale=1.5, tag="open-mouth")
    s += '    <path d="M54 168C82 182 140 182 166 166" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".7"/>\n' % SKIN_LN
    s += '  </g>\n'
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_mouth.svg", s)


def part_ear(path, flip, tag):
    s = svg_open(220, 300, "0 0 220 300")
    s += '<g id="%s" transform="translate(110,150) scale(%s,1)">\n' % (tag, flip)
    # hidden ear root (tucks under hair / head silhouette)
    s += '  <path d="M-40-56C-14-70 22-68 44-52C60-40 66-18 64 6C62 34 52 58 34 70C16 82-10 80-26 66C-42 52-48 22-48-6C-48-30-46-46-40-56Z" fill="%s" opacity=".45"/>\n' % SKIN_SH
    # ear body
    s += ('  <path d="M-34-44C-12-56 18-54 36-38C52-24 58 2 56 26C54 52 42 76 22 88'
          'C6 96-12 90-22 76C-32 62-38 34-38 8C-38-14-38-34-34-44Z" '
          'fill="%s" stroke="%s" stroke-width="3.4" stroke-linejoin="round"/>\n' % (SKIN, LINE))
    # helix + antihelix + concha + tragus + lobe
    s += '  <path d="M-26-30C-8-40 16-36 28-22C40-8 42 14 36 34C30 54 18 70 4 76" fill="none" stroke="%s" stroke-width="2.8" stroke-linecap="round"/>\n' % SKIN_LN
    s += '  <path d="M-14-16C0-24 14-18 20-6C26 8 22 26 12 38" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".85"/>\n' % SKIN_LN
    s += '  <path d="M-20-2C-8-12 8-10 14 2C20 14 14 30 2 38C-8 44-20 38-22 26C-24 16-24 6-20-2Z" fill="%s" opacity=".85"/>\n' % SKIN_SH
    s += '  <path d="M-30 6C-22 0-12 4-10 14C-8 24-16 32-26 30C-32 28-34 16-30 6Z" fill="%s" stroke="%s" stroke-width="2.2" stroke-linejoin="round"/>\n' % (SKIN, LINE)
    s += '  <path d="M-4 66C6 74 18 70 24 58" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>\n' % SKIN_LN
    s += '  <path d="M-16 20C-8 26-2 38-4 50" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" opacity=".7"/>\n' % SKIN_LN
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg(path, s)


def part_hair_front():
    s = svg_open(420, 300, "0 0 420 300")
    s += '<g id="hair-front-bangs">\n'
    s += ('  <path d="M210 26C112 26 44 90 42 168C42 186 58 190 66 176C74 162 74 140 80 120'
          'C94 152 116 176 140 188C152 194 162 186 156 174C150 162 154 148 164 138C176 126 194 120 208 122'
          'C232 126 252 148 262 176C266 186 278 186 282 176C288 162 286 142 282 126C276 100 264 82 248 70'
          'C262 96 268 124 264 148C258 132 246 116 232 104C240 128 244 154 238 178C232 198 214 206 204 192'
          'C196 180 198 162 206 148C216 132 234 122 250 122C268 122 284 134 292 152C300 170 296 190 288 202'
          'C300 196 308 184 308 170C308 152 300 132 288 118C296 136 300 158 296 178C292 198 274 210 262 200'
          'C250 190 246 170 250 152C256 128 270 110 286 100C300 90 316 84 332 82C310 74 286 70 262 70'
          'C296 54 320 40 336 28C296 20 252 18 210 26Z" '
          'fill="%s" stroke="%s" stroke-width="3.4" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += '  <path d="M76 146C92 100 146 54 204 48C158 58 110 92 90 138C84 152 76 156 76 146Z" fill="%s" opacity=".9"/>\n' % HAIR_LT
    s += '  <path d="M96 174C118 132 168 96 226 86C182 96 136 124 110 162C102 174 94 180 96 174Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '  <path d="M232 104C244 132 248 164 240 190C252 176 256 142 244 112Z" fill="%s" opacity=".75"/>\n' % HAIR_SH
    s += '  <path d="M286 100C298 126 302 154 296 180C304 166 306 138 296 112Z" fill="%s" opacity=".75"/>\n' % HAIR_SH
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_hair_front.svg", s)


def part_hair_back():
    s = svg_open(420, 420, "0 0 420 420")
    s += '<g id="hair-back">\n'
    s += ('  <path d="M210 24C118 24 66 92 64 182C62 250 72 322 86 362C96 396 118 384 114 366'
          'C108 340 104 314 108 284C112 244 122 200 140 172C156 146 180 132 210 130C240 132 264 146 280 172'
          'C298 200 308 244 312 284C316 314 312 340 306 366C302 384 324 396 334 362C348 322 358 250 356 182'
          'C354 92 302 24 210 24Z" '
          'fill="%s" stroke="%s" stroke-width="3.6" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M100 214C96 278 92 340 104 374C114 348 116 300 120 262C124 232 132 202 146 182'
          'C126 188 108 198 100 214Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M320 214C324 278 328 340 316 374C306 348 304 300 300 262C296 232 288 202 274 182'
          'C294 188 312 198 320 214Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M186 232C176 274 176 330 188 366C196 388 214 392 218 372C206 340 202 296 208 258'
          'C212 232 226 210 242 198C220 194 196 208 186 232Z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>\n' % (HAIR_SH, LINE))
    s += '  <path d="M104 168C126 112 176 76 230 70C186 82 142 112 118 154C108 170 100 176 104 168Z" fill="%s" opacity=".85"/>\n' % HAIR_LT
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_hair_back.svg", s)


def part_hair_side_L():
    s = svg_open(320, 360, "0 0 320 360")
    s += '<g id="hair-side-anatomical-left">\n'
    s += ('  <path d="M226 30C166 24 122 62 110 122C100 174 106 236 122 282C130 306 150 314 160 304'
          'C170 294 164 276 156 262C144 240 140 206 144 170C148 130 158 96 178 78C196 62 214 54 230 52'
          'C246 50 258 42 256 30C250 22 238 24 226 30Z" '
          'fill="%s" stroke="%s" stroke-width="3.4" stroke-linejoin="round"/>\n' % (HAIR, LINE))
    s += ('  <path d="M232 56C198 60 168 84 154 122C144 150 140 184 142 214C136 180 142 140 158 110'
          'C176 74 204 56 232 56Z" fill="%s" opacity=".85"/>\n' % HAIR_LT)
    s += '  <path d="M116 178C110 224 118 268 136 296C128 262 128 218 136 186Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    s += '  <path d="M158 108C176 82 202 64 228 60C204 70 180 88 166 112Z" fill="%s" opacity=".8"/>\n' % HAIR_SH
    # fixed gold crossed hairpin on this same anatomical-left section
    s += hairpin_group(196, 96, rot=-24, scale=1.0, tag="gold-hairpin-fixed")
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_hair_side_L.svg", s)


def part_ahoge():
    s = svg_open(260, 200, "0 0 260 200")
    s += '<g id="ahoge">\n'
    s += ahoge_group(196, 172, scale=1.15, tag="ahoge-strand")
    s += '</g>\n'
    s += '</svg>\n'
    return write_svg("part_ahoge.svg", s)


def manifest():
    items = [
        ("design/view_000_front.svg", "viewYaw", 0, {"eyes": True, "nose": True, "mouth": True, "ears": True, "hair": True}),
        ("design/view_045_three_quarter_right.svg", "viewYaw", 45, {"eyes": True, "nose": True, "mouth": True, "ears": True, "hair": True}),
        ("design/view_090_profile_right.svg", "viewYaw", 90, {"eyes": True, "nose": True, "mouth": True, "ears": True, "hair": True}),
        ("design/view_180_back.svg", "viewYaw", 180, {"eyes": False, "nose": False, "mouth": False, "ears": False, "hair": True}),
        ("design/part_eye_L.svg", "partId", "eye_anatomical_left", {"eyes": True, "nose": False, "mouth": False, "ears": False, "hair": False}),
        ("design/part_eye_R.svg", "partId", "eye_anatomical_right", {"eyes": True, "nose": False, "mouth": False, "ears": False, "hair": False}),
        ("design/part_nose.svg", "partId", "nose", {"eyes": False, "nose": True, "mouth": False, "ears": False, "hair": False}),
        ("design/part_mouth.svg", "partId", "mouth", {"eyes": False, "nose": False, "mouth": True, "ears": False, "hair": False}),
        ("design/part_ear_L.svg", "partId", "ear_anatomical_left", {"eyes": False, "nose": False, "mouth": False, "ears": True, "hair": False}),
        ("design/part_ear_R.svg", "partId", "ear_anatomical_right", {"eyes": False, "nose": False, "mouth": False, "ears": True, "hair": False}),
        ("design/part_hair_front.svg", "partId", "hair_front_bangs", {"eyes": False, "nose": False, "mouth": False, "ears": False, "hair": True}),
        ("design/part_hair_back.svg", "partId", "hair_back", {"eyes": False, "nose": False, "mouth": False, "ears": False, "hair": True}),
        ("design/part_hair_side_L.svg", "partId", "hair_side_anatomical_left", {"eyes": False, "nose": False, "mouth": False, "ears": False, "hair": True}),
        ("design/part_ahoge.svg", "partId", "ahoge", {"eyes": False, "nose": False, "mouth": False, "ears": False, "hair": True}),
    ]
    out = {
        "schema_version": "1.0.0",
        "project": "KomaMotion",
        "asset_stage": "P0-1B",
        "character_id": "p0_character_001",
        "identity_review_status": "PROVISIONAL_DESIGN",
        "identity_review_note": ("Approved Hero binary is not available on this machine; all files are original "
                                 "vector interpretations of identity_spec.json and must NOT be claimed as "
                                 "pixel-level identity match. Layered group ids are kept for later transparent "
                                 "PNG regeneration."),
        "palette": {
            "hair_base": "#C27A98", "hair_shadow": "#8C5574", "iris": "#B65A8C",
            "skin": "#FFE9E1", "jacket": "#3B3A51", "shirt": "#FFFFFF",
            "bow": "#8C3A54", "hairpin_gold": "#D4AF37",
        },
        "asymmetry_rules": {
            "gold_cross_hairpin": "anatomical LEFT only; front view screen RIGHT; never mirrored",
            "ahoge": "single strand curving toward screen-left in the front view",
            "bangs": "asymmetric swept parting, not mirrored",
        },
        "files": [],
    }
    for path, key, val, parts in items:
        entry = {
            "path": path,
            "exists": True,
            "format": "svg_transparent_background",
            "identity_review_status": "PROVISIONAL_DESIGN",
        }
        if key == "viewYaw":
            entry["viewYaw"] = val
        else:
            entry["partId"] = val
        entry["parts_present"] = parts
        entry["has_eye"] = parts["eyes"]
        entry["has_nose"] = parts["nose"]
        entry["has_mouth"] = parts["mouth"]
        entry["has_ear"] = parts["ears"]
        entry["has_hair"] = parts["hair"]
        out["files"].append(entry)
    out["file_count"] = len(out["files"])
    p = "/root/koma-p0-designs/design/manifest.json"
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    return p


if __name__ == "__main__":
    print(part_eye("part_eye_L.svg", 1, "eye-anatomical-left"))
    print(part_eye("part_eye_R.svg", -1, "eye-anatomical-right"))
    print(part_nose())
    print(part_mouth())
    print(part_ear("part_ear_L.svg", 1, "ear-anatomical-left"))
    print(part_ear("part_ear_R.svg", -1, "ear-anatomical-right"))
    print(part_hair_front())
    print(part_hair_back())
    print(part_hair_side_L())
    print(part_ahoge())
    print(manifest())
