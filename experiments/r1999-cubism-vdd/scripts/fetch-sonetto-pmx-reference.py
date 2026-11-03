#!/usr/bin/env python3
"""Download a publicly downloadable Sonetto PMX reference with BowlRoll's normal form.

Downloads stay local; never upload or redistribute PMX, textures or included
ReadMe. Only derived 3D render screenshots may be published with author credit.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import urllib.parse
import urllib.request
import http.cookiejar
import zipfile
from pathlib import Path, PurePosixPath

PAGE = "https://bowlroll.net/file/315881"
CHECK = "https://bowlroll.net/api/file/315881/download-check"
EXPECTED_ID = "315881"


def download(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    cookiejar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/134.0"}

    with opener.open(urllib.request.Request(PAGE, headers=headers), timeout=35) as response:
        landing = response.read().decode("utf-8")
    match = re.search(r'data-csrf_token="([^"]+)"', landing)
    if not match:
        raise RuntimeError("Public download form has no CSRF token")
    csrf = html.unescape(match.group(1))
    payload = urllib.parse.urlencode({
        "download_key": "bowlroll_download_control_mischievous",
        "csrf_token": csrf,
    }).encode()
    request = urllib.request.Request(
        CHECK, data=payload, headers={**headers,
          "Origin": "https://bowlroll.net", "Referer": PAGE,
          "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with opener.open(request, timeout=35) as response:
        authorization = json.loads(response.read())
    if authorization.get("status") != "success":
        raise RuntimeError("Creator's public file distribution is not available")
    target = authorization.get("url", "")
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme != "https" or parsed.hostname != "bowlroll.net" or        not parsed.path.startswith(f"/file/{EXPECTED_ID}/download-execution/"):
        raise RuntimeError("Unexpected download URL origin")

    name = "Sonetto_Basic_PDp1.1v.zip"
    dest = outdir / name
    digest = hashlib.sha256()
    total = 0
    with opener.open(urllib.request.Request(target, headers=headers), timeout=65) as response,          dest.open("wb") as f:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > 75 * 1024 * 1024:
                raise RuntimeError("ZIP exceeds expected 75 MB safety bound")
            f.write(chunk)
            digest.update(chunk)
    with zipfile.ZipFile(dest) as archive:
        entries = archive.infolist()
        if not entries or not any(i.filename.endswith("_Sonetto_Basic.pmx") for i in entries):
            raise ValueError("PMX not present")
        if not any(i.filename == "ReadMe/ReadMe_EN.txt" for i in entries):
            raise ValueError("Creator's English license not present")
        license_text = archive.read("ReadMe/ReadMe_EN.txt").decode("utf-8-sig")
        if not all(x in license_text for x in [
           "editing this data", "redistribution and commercial use",
           "WTHN_Ross", "BLUEPOCH"]):
            raise RuntimeError("License requires review; expected terms changed")
        for item in entries:
            key = PurePosixPath(item.filename)
            if key.is_absolute() or ".." in key.parts or item.file_size > 100 * 1024 * 1024:
                raise ValueError("Unsafe archive entry")
        archive.extractall(outdir / "extracted")

    report = {"schema": "R1999-SONETTO-PMX-SOURCE-V1",
        "provider": "BowlRoll", "sourcePage": PAGE, "creator": "WTHN_Ross",
        "copyright": "BLUEPOCH / Reverse: 1999",
        "distribution": "private_noncommercial_structural_reference",
        "renderImagePublication": "permitted_with_creator_credit",
        "modelRedistribution": "prohibited",
        "assetPartsReuse": "prohibited",
        "zipSha256": digest.hexdigest(), "bytes": total, "entryCount": len(entries),
        "model": "[Reverse1999]_Sonetto_Basic.pmx",
        "readmeReviewed": True}
    (outdir / "source-audit.json").write_text(json.dumps(report, indent=2)+"\n")
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    report = download(args.output_dir.resolve())
    print(json.dumps(report))


if __name__ == "__main__":
    main()
