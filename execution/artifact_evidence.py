"""Artifact Evidence — hash-bound identity and stale-evidence checks.
Wing: code | Topic: artifact-evidence | Updated: 2026-09-12 14:47
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Mapping, Sequence

_SHA256_RE=re.compile(r'^[a-f0-9]{64}$')

def _sha(value: str, name: str) -> str:
    if not isinstance(value,str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f'{name} must be lowercase sha256')
    return value

def artifact_manifest(*,run_id:str,artifact_id:str,sha256:str,source_hashes:Sequence[str],versions:Mapping[str,str],reopened:bool) -> dict:
    if not run_id or not artifact_id:
        raise ValueError('run_id and artifact_id are required')
    if not isinstance(reopened,bool):
        raise ValueError('reopened must be bool')
    return {
        'run_id':run_id,
        'artifact_id':artifact_id,
        'artifact_sha256':_sha(sha256,'sha256'),
        'source_hashes':[_sha(x,'source_hash') for x in source_hashes],
        'versions':dict(versions),
        'reopened':reopened,
    }

def evidence_is_stale(evidence: Mapping, *, current_artifact_sha256: str) -> bool:
    current=_sha(current_artifact_sha256,'current_artifact_sha256')
    recorded=evidence.get('artifact_sha256')
    if recorded is None:
        return True
    return _sha(recorded,'artifact_sha256') != current


def sha256_file(path: str | Path) -> str:
    """Hash one stable file for engine-neutral artifact identity evidence."""
    p=Path(path)
    if not p.is_file():
        raise ValueError('artifact path must be an existing file')
    digest=hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
