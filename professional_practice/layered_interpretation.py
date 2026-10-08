"""Layered Interpretation — shared engineer-decomposition baseline.
Wing: code | Topic: layered-interpretation | Updated: 2026-09-14 19:40
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


def order_layer_chunks(items: Sequence[Mapping]) -> list:
    """Return a build order where host/base layers precede their dependents.

    Each item carries ``item_id`` and ``hosted_on`` (ids of the layers or
    semantic hosts it depends on, e.g. foreground wall hosted on background
    slab). The order guarantees a background chunk commits before any chunk
    that covers or depends on it, so Feature-based Chunk Streaming can never
    schedule a 3D foreground before its layout base exists.

    Raises ``ValueError`` on duplicate ids, unknown hosts, self-hosting, or
    dependency cycles — all fail closed instead of silently dropping a layer.
    """
    if isinstance(items,(str,bytes)) or not isinstance(items,Sequence):
        raise ValueError('items must be a sequence')
    hosts: dict = {}
    for i,item in enumerate(items):
        if not isinstance(item,Mapping):
            raise ValueError('items must be mappings')
        item_id=item.get('item_id')
        if not isinstance(item_id,str) or not item_id:
            raise ValueError(f'items[{i}].item_id must be a non-empty string')
        if item_id in hosts:
            raise ValueError(f'duplicate item_id: {item_id}')
        hosted_on=item.get('hosted_on',[])
        if isinstance(hosted_on,(str,bytes)) or not isinstance(hosted_on,Sequence):
            raise ValueError(f'{item_id}: hosted_on must be a sequence')
        for dep in hosted_on:
            if not isinstance(dep,str) or not dep:
                raise ValueError(f'{item_id}: hosted_on entries must be non-empty strings')
            if dep==item_id:
                raise ValueError(f'{item_id}: self-hosting is not allowed')
        hosts[item_id]=list(dict.fromkeys(hosted_on))
    for item_id,deps in hosts.items():
        for dep in deps:
            if dep not in hosts:
                raise ValueError(f'{item_id}: unknown host: {dep}')
    order: list = []
    done=set()
    remaining=dict(hosts)
    while remaining:
        ready=sorted(item_id for item_id,deps in remaining.items() if all(d in done for d in deps))
        if not ready:
            cycle=sorted(remaining)
            raise ValueError(f'host dependency cycle: {", ".join(cycle)}')
        for item_id in ready:
            order.append(item_id)
            done.add(item_id)
            del remaining[item_id]
    return order
