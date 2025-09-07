from typing import List
from app.schemas import GraphBundle, Entity, Edge
from app.adapters import shodan_adapter, censys_adapter
from app.anchors import execute_anchor, ANCHORS

async def investigate_ip(ip: str) -> GraphBundle:
    ents: List[Entity] = []
    edges: List[Edge] = []
    for fn in (shodan_adapter.host_view, censys_adapter.host_view):
        try:
            e, ed = await fn(ip)
            ents.extend(e); edges.extend(ed)
        except Exception:
            pass
    return GraphBundle(entities=_dedupe_e(ents), edges=_dedupe_r(edges))

async def list_anchors():
    return [{"name": k, "intent": v.intent, "description": v.description, "inputs": v.inputs_spec}
            for k, v in ANCHORS.items()]

async def run_anchor(name: str, asset: str):
    return await execute_anchor(name, {"asset": asset})

def _dedupe_e(items: List[Entity]) -> List[Entity]:
    seen, out = set(), []
    for it in items:
        if it.id not in seen:
            out.append(it); seen.add(it.id)
    return out

def _dedupe_r(items: List[Edge]) -> List[Edge]:
    seen, out = set(), []
    for it in items:
        key = (it.src, it.rel, it.dst)
        if key not in seen:
            out.append(it); seen.add(key)
    return out
