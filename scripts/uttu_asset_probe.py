#!/usr/bin/env python3
"""Bounded, non-invasive compatibility probe for the public UTTU archive.

Metadata-only; does not download, store, or redistribute game model/texture assets.
HTML and JS are analyzed in RAM only. No scraping behind authentication.
"""
from __future__ import annotations
import collections
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib import request, parse, error, robotparser
import time

BASE = "https://uttu.merui.net"
PAGES = ("/", "/live2d-sandbox/", "/npcs/jailer/", "/profiles/fatutu/", "/about/")
OUT = Path(os.getenv("OUT_DIR", "out/uttu-asset-probe"))
OUT.mkdir(parents=True, exist_ok=True)
UA = "KomaMotionLab-CompatibilityProbe/0.1 (single-sample format metadata; GitHub Actions)"
MAX_HTML = 400_000
MAX_SCRIPT = 350_000
MAX_SCRIPTS = 8
TIMEOUT = 18
EXT = re.compile(r"(?i)(?:\\.moc3|\\.model3\\.json|\\.physics3\\.json|\\.motion3\\.json|\\.exp3\\.json|\\.cmo3|\\.can3|\\.skel|\\.atlas(?:\\.txt)?|\\.riv|\\.psd)")
FINDINGS = re.compile(r"(?i)(?:cubism|live2d|spine|model3|moc3|atlas|skel|rive|assets/|asseturl|resourceurl|cdn)")
ALLOWED_WEB_SCHEMES = ("https",)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.links = []
        self.meta = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "script" and d.get("src"):
            self.scripts.append(d["src"])
        if tag == "link" and d.get("href"):
            self.links.append(d["href"])
        if tag == "meta" and d.get("content") and (d.get("name") or d.get("property")):
            self.meta.append((d.get("name") or d.get("property"), d["content"][:120]))

def fetch(url, limit=MAX_HTML, method="GET"):
    u = parse.urlparse(url)
    if u.scheme not in ALLOWED_WEB_SCHEMES or not u.hostname:
        raise ValueError("Unsafe URL")
    req = request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/javascript,application/json;q=0.9,*/*;q=0.3"}, method=method)
    with request.urlopen(req, timeout=TIMEOUT) as resp:
        content = resp.read(limit + 1) if method == "GET" else b""
        return {
            "status": resp.status, "final_url": resp.geturl(),
            "content_type": resp.headers.get("content-type", ""),
            "content_length_header": resp.headers.get("content-length"),
            "truncated": len(content) > limit,
            "body": content[:limit],
        }

report = {
    "source": BASE,
    "purpose": "public-page resource-format probe; no game assets redistributed",
    "pages": [], "script_samples": [], "format_evidence": {},
    "rights": {
        "site_claim": "UTTU is an unofficial Reverse: 1999 fan archive; Bluepoch owns character/game assets (About page)",
        "game_asset_reuse_license": "NOT_ESTABLISHED",
        "rive_import": "NOT_ESTABLISHED",
    },
    "limits": {"pages": len(PAGES), "scripts_max": MAX_SCRIPTS, "max_script_bytes": MAX_SCRIPT},
}
all_scripts = []
patterns = collections.Counter()
url_candidates = []

for path in PAGES:
    url = BASE + path
    entry = {"page": path}
    try:
        r = fetch(url)
        text = r["body"].decode("utf-8", errors="replace")
        p = Parser()
        p.feed(text)
        entry.update({k:v for k,v in r.items() if k != "body"})
        entry["html_bytes_inspected"] = len(r["body"])
        entry["first_party_js_count"] = len(p.scripts)
        entry["script_hosts"] = dict(collections.Counter(parse.urlparse(parse.urljoin(url,s)).hostname for s in p.scripts))
        entry["sample_script_paths"] = [parse.urlparse(parse.urljoin(url,s)).path for s in p.scripts[:5]]
        entry["contains_live2d_keyword"] = bool(re.search("live2d|cubism", text, re.I))
        entry["contains_spine_keyword"] = bool(re.search("spine", text, re.I))
        entry["file_extensions_mentioned"] = sorted(set(m.group(0).lower() for m in EXT.finditer(text)))
        for m in EXT.finditer(text): patterns[m.group(0).lower()] += 1
        for u in p.scripts:
            absolute = parse.urljoin(url, u)
            if parse.urlparse(absolute).hostname == parse.urlparse(BASE).hostname:
                all_scripts.append(absolute)
        # Only same-domain, public paths in metadata output. No HTML/JS/texture bodies.
    except Exception as e:
        entry["error"] = str(e)[:250]
    report["pages"].append(entry)

seen = set()
for url in all_scripts:
    if len(report["script_samples"]) >= MAX_SCRIPTS:
        break
    if url in seen:
        continue
    seen.add(url)
    entry = {"script_path": parse.urlparse(url).path}
    try:
        r = fetch(url, MAX_SCRIPT)
        code = r["body"].decode("utf-8", errors="replace")
        entry["http_status"] = r["status"]
        entry["bytes_inspected"] = len(r["body"])
        entry["truncated"] = r["truncated"]
        entry["formats_mentioned"] = sorted(set(m.group(0).lower() for m in EXT.finditer(code)))
        entry["keywords"] = {kw:bool(re.search(kw, code, re.I)) for kw in ("live2d","cubism","spine","moc3","model3","skel","atlas","rive")}
        for m in EXT.finditer(code):
            patterns[m.group(0).lower()] += 1
        # URLs in script strings with distinctive model manifest suffix only.
        for m in re.finditer(r'[^\\s\\"\x27<>]{1,220}(?:\\.model3\\.json|\\.moc3|\\.skel|\\.atlas(?:\\.txt)?|\\.riv)',code,re.I):
            s = m.group(0).strip(');,')
            if len(s)<240: url_candidates.append(s)
    except Exception as e:
        entry["error"] = str(e)[:200]
    report["script_samples"].append(entry)

report["format_evidence"] = dict(patterns)
report["candidate_refs_count"] = len(url_candidates)
# Do not expose or archive recovered game resource file links from third-party bundles.
report["candidate_ref_types"] = sorted(set(m.group(0).lower() for s in url_candidates for m in EXT.finditer(s)))
report["conclusions"] = {
    "public_site_http_available": any(p.get("status")==200 for p in report["pages"]),
    "format_identifiable_from_page_metadata": bool(patterns),
    "direct_rive_reuse_confirmed": False,
    "reconstruction_or_original_asset_pipeline_needed": True,
    "model_binaries_downloaded": False,
    "visual_character_reproduction_tested": False,
}
file = OUT / "report.json"
file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
summary = ["# UTTU asset production compatibility probe", "",
           "Metadata-only public page inspection. No copyrighted game assets or original JS bundles are included in artifacts.", "",
           "| Page | HTTP | Text inspected | Live2D ref | Spine ref |", "|---|---:|---:|---|---|"]
for e in report["pages"]:
    summary.append(f'| {e["page"]} | {e.get("status",e.get("error","ERROR"))} | {e.get("html_bytes_inspected",0)} | {e.get("contains_live2d_keyword",False)} | {e.get("contains_spine_keyword",False)} |')
summary += ["", "## Script hosts", "", json.dumps([{"page":e["page"],"hosts":e.get("script_hosts",{}),"sample_paths":e.get("sample_script_paths",[])} for e in report["pages"]],ensure_ascii=False), "", "## Sampled JS", "", json.dumps(report["script_samples"],ensure_ascii=False)]
summary += ["", "## Format markers", "", json.dumps(report["format_evidence"], ensure_ascii=False),
            "", "## Conclusions", "",
            "- Official Rive importer compatibility has **not** been established.",
            "- UTTU is a third-party fan archive and does not grant downstream reuse of the game assets.",
            "- Site preview uses Live2D Cubism and Spine per UTTU's About page; original binding is not a native Rive format.",
            "- Do not commit game model binaries, textures, model manifests or source bundles into this public repository.",
            "- If a private original 2D asset is available, generate new Rive rigs from independently owned layers.",
            "", "## Raw report", "", "See report.json for status and aggregate format markers."]
(OUT / "summary.md").write_text("\n".join(summary) + "\n")
print((OUT / "summary.md").read_text())
