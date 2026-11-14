#!/usr/bin/env python3
"""Inventory verified native source coverage by semantic part across the front-to-back arc."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'private-assets'
OUT = ROOT / 'evidence' / 'p15-117-source-coverage-qa.json'
REQUIRED = [0, 45, 90, 135, 180]
SOURCES = [(0, 'p1-front/parts.json'), (45, 'p2-views/parts.json'), (90, 'p2-views/parts.json')]

def audit():
    rows = {}
    roles = set()
    for angle, manifest_rel in SOURCES:
        manifest = ASSETS / manifest_rel
        data = json.loads(manifest.read_text())
        assert data['characterId'] == 'p0_character_001'
        entries = [entry for entry in data['parts'] if entry['yawDeg'] == angle]
        assert len(entries) == 13, (angle, len(entries))
        view = {}
        for entry in entries:
            role = entry['semanticId']
            assert role not in view
            path = ASSETS / entry['path']
            exists = path.is_file()
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if exists else None
            expected = entry.get('sha256') or entry.get('frameSha256')
            view[role] = {
                'exists': exists, 'hashVerified': bool(exists and (not expected or digest == expected)),
                'alphaInspection': 'see p15-20-canonical-source-views/qa.json',
                'manifest': manifest_rel,
            }
            roles.add(role)
        rows[str(angle)] = view
    for angle in REQUIRED:
        rows.setdefault(str(angle), {})
    # Supplemental view paintings are recorded separately: a single RGBA frame is not a 13-part source manifest.
    supplements = {}
    for angle, rel in [(52.5, 'p15-93-yaw0525/yaw0525-native.png'),
                       (75, 'p15-92-yaw075/yaw075-native.png')]:
        path = ASSETS / rel
        supplements[str(angle)] = {'path': rel, 'exists': path.is_file(),
                                   'classification': 'single-view raster; part decomposition not verified'}
    blockers = [angle for angle in REQUIRED if not rows[str(angle)]]
    invalid = [{'angle': angle, 'role': role} for angle, view in rows.items()
               for role, check in view.items() if not check['hashVerified']]
    result = {
        'schema': 'KOMA_P15_117_SOURCE_COVERAGE_V1', 'characterId': 'p0_character_001',
        'scope': 'canonical-source-manifest coverage from 0 to 180 degrees',
        'requiredCheckpointAngles': REQUIRED, 'semanticRoles': sorted(roles),
        'perAngleSourceParts': rows, 'supplementarySingleViewPaintings': supplements,
        'verifiedCompleteManifestAngles': [a for a in REQUIRED if len(rows[str(a)]) == len(roles) and
                                          all(x['hashVerified'] for x in rows[str(a)].values())],
        'missingCanonicalManifestAngles': blockers, 'invalidSourceParts': invalid,
        'outcome': 'CANONICAL_180_SOURCE_COVERAGE_INCOMPLETE' if blockers or invalid else 'CANONICAL_180_SOURCE_COVERAGE_VERIFIED',
        'acceptance': {'fullYawVisualAccepted': False, 'nativeSourcePixelIntegrity': not invalid},
        'next': 'Acquire and verify independent 135/180-degree P0 semantic art and underpaint before promising 180/360-degree source-correct rotation.'
    }
    return result

if __name__ == '__main__':
    result = audit()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'outcome': result['outcome'], 'verified': result['verifiedCompleteManifestAngles'],
                      'missing': result['missingCanonicalManifestAngles'], 'invalid': result['invalidSourceParts']}))
