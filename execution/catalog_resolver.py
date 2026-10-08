"""Catalog Resolver — bind semantic engineering assets to verified native registry evidence.
Wing: code | Topic: catalog-resolution | Updated: 2026-09-12 20:22
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_VALID_CAPABILITY_RESULTS=frozenset({'pass','fail','unknown','blocked','not_applicable'})
_VALID_NATIVE_STATES=frozenset({'unresolved','resolved','blocked'})
_SHA256_RE=re.compile(r'^[a-f0-9]{64}$')


def _nonempty_string(value, name: str) -> str:
    if not isinstance(value,str) or not value:
        raise ValueError(f'{name} must be a non-empty string')
    return value


def _string_sequence(value, name: str) -> list[str]:
    if isinstance(value,(str,bytes)) or not isinstance(value,Sequence):
        raise ValueError(f'{name} must be a sequence')
    result=list(value)
    if any(not isinstance(item,str) or not item for item in result):
        raise ValueError(f'{name} must contain non-empty strings')
    if len(result)!=len(set(result)):
        raise ValueError(f'{name} must not contain duplicates')
    return result


def _runtime_fact(value: Mapping) -> tuple[str,list[str]]:
    if not isinstance(value,Mapping):
        raise ValueError('runtime_capability must be a mapping')
    result=value.get('result','unknown')
    if result not in _VALID_CAPABILITY_RESULTS:
        raise ValueError(f'invalid runtime capability result: {result}')
    reasons=value.get('reason_codes',[])
    if not isinstance(reasons,list) or any(not isinstance(reason,str) or not reason for reason in reasons):
        raise ValueError('runtime capability reason_codes must be a list of non-empty strings')
    return result,list(reasons)


def resolve_catalog_assets(
    catalog: Mapping,
    *,
    software_id: str,
    required_asset_ids: Sequence[str],
    registry_evidence: Mapping[str,Mapping],
    runtime_capability: Mapping,
) -> dict:
    """Resolve required semantic assets against exact native mapping + registry evidence.

    This helper deliberately does not decide proxy/custom substitution. It only proves
    the strong `resolved` path: semantic asset exists, catalog mapping is resolved,
    runtime library capability is released, and current registry key/hash/version match.
    """
    if not isinstance(catalog,Mapping):
        raise ValueError('catalog must be a mapping')
    software_id=_nonempty_string(software_id,'software_id')
    required=_string_sequence(required_asset_ids,'required_asset_ids')
    if not isinstance(registry_evidence,Mapping):
        raise ValueError('registry_evidence must be a mapping')

    assets=catalog.get('assets')
    if isinstance(assets,(str,bytes)) or not isinstance(assets,Sequence):
        raise ValueError('catalog.assets must be a sequence')
    by_id={}
    for index,asset in enumerate(assets):
        if not isinstance(asset,Mapping):
            raise ValueError('catalog assets must be mappings')
        asset_id=_nonempty_string(asset.get('asset_id'),f'assets[{index}].asset_id')
        if asset_id in by_id:
            raise ValueError(f'duplicate catalog asset_id: {asset_id}')
        by_id[asset_id]=asset

    capability_result,capability_reasons=_runtime_fact(runtime_capability)
    blockers=[]
    if capability_result!='pass':
        blockers.append(f'native_library_capability_not_released:{software_id}:{capability_result}')
        blockers.extend(capability_reasons)

    resolved=[]
    resolved_native=[]
    for asset_id in required:
        asset=by_id.get(asset_id)
        if asset is None:
            blockers.append(f'catalog_asset_missing:{asset_id}')
            continue
        native_mappings=asset.get('native_mappings',{})
        if not isinstance(native_mappings,Mapping):
            raise ValueError(f'{asset_id}: native_mappings must be a mapping')
        mapping=native_mappings.get(software_id)
        if mapping is None:
            blockers.append(f'native_mapping_missing:{asset_id}:{software_id}')
            continue
        if not isinstance(mapping,Mapping):
            raise ValueError(f'{asset_id}:{software_id}: native mapping must be a mapping')
        state=mapping.get('state')
        if state not in _VALID_NATIVE_STATES:
            raise ValueError(f'{asset_id}:{software_id}: invalid native mapping state: {state}')
        if state=='unresolved':
            blockers.append(f'native_mapping_unresolved:{asset_id}:{software_id}')
            continue
        if state=='blocked':
            blockers.append(f'native_mapping_blocked:{asset_id}:{software_id}')
            reason=mapping.get('reason')
            if reason is not None:
                blockers.append(f'native_mapping_reason:{asset_id}:{reason}')
            continue

        asset_key=_nonempty_string(mapping.get('asset_key'),f'{asset_id}:{software_id}.asset_key')
        expected_hash=_nonempty_string(mapping.get('sha256'),f'{asset_id}:{software_id}.sha256')
        if not _SHA256_RE.fullmatch(expected_hash):
            raise ValueError(f'{asset_id}:{software_id}: sha256 must be lowercase 64-hex')
        expected_version=_nonempty_string(mapping.get('native_version'),f'{asset_id}:{software_id}.native_version')
        observed=registry_evidence.get(asset_key)
        if observed is None:
            blockers.append(f'native_registry_evidence_missing:{asset_id}')
            continue
        if not isinstance(observed,Mapping):
            raise ValueError(f'{asset_id}: registry evidence must be a mapping')
        available=observed.get('available')
        if not isinstance(available,bool):
            raise ValueError(f'{asset_id}: registry available must be bool')
        if not available:
            blockers.append(f'native_registry_asset_unavailable:{asset_id}')
            continue
        observed_hash=_nonempty_string(observed.get('sha256'),f'{asset_id}.registry.sha256')
        observed_version=_nonempty_string(observed.get('native_version'),f'{asset_id}.registry.native_version')
        if observed_hash!=expected_hash:
            blockers.append(f'native_registry_hash_mismatch:{asset_id}')
            continue
        if observed_version!=expected_version:
            blockers.append(f'native_registry_version_mismatch:{asset_id}')
            continue
        resolved.append(asset_id)
        resolved_native.append({
            'asset_id':asset_id,
            'asset_key':asset_key,
            'sha256':expected_hash,
            'native_version':expected_version,
        })

    blockers=list(dict.fromkeys(blockers))
    return {
        'state':'blocked' if blockers else 'resolved',
        'reason_codes':blockers,
        'software_id':software_id,
        'required_asset_ids':required,
        'resolved_asset_ids':resolved,
        'resolved_native_assets':resolved_native,
    }
