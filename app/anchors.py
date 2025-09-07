from typing import Dict, Any, List
from app.schemas import AnchorPlan, AnchorAction, GraphBundle, ExecutionReport, ExecutionEvent
from app.adapters import shodan_adapter, censys_adapter

def _merge(a: GraphBundle, b: GraphBundle) -> GraphBundle:
    ei = {e.id: e for e in a.entities}
    for e in b.entities: ei[e.id] = e
    ri = {(r.src, r.rel, r.dst): r for r in a.edges}
    for r in b.edges: ri[(r.src, r.rel, r.dst)] = r
    from app.schemas import Entity, Edge
    return GraphBundle(entities=list(ei.values()), edges=list(ri.values()))

ANCHORS: Dict[str, AnchorPlan] = {
    "Eternal Flame — ignite": AnchorPlan(
        name="Eternal Flame — ignite",
        description="Rapid enrichment for a single asset.",
        intent="enrichment",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"burst"}
    ),
    "Indigo Pulse 47193": AnchorPlan(
        name="Indigo Pulse 47193",
        description="Heartbeat check for changes.",
        intent="validation",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"pulse","diff":True}
    ),
    "Return, Elyra": AnchorPlan(
        name="Return, Elyra",
        description="Resume and refresh core pivots.",
        intent="exploration",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"resume"}
    ),
    "Overflow": AnchorPlan(
        name="Overflow",
        description="Go wide—related discovery.",
        intent="exploration",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"wide","throttle":0.5}
    ),
    "Pillar of Strength": AnchorPlan(
        name="Pillar of Strength",
        description="Cross-source validation + confidence.",
        intent="validation",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"verified","confidence":"source_overlap"}
    ),
    "Truth Be Told": AnchorPlan(
        name="Truth Be Told",
        description="Emit only corroborated facts.",
        intent="validation",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"corroborated","require_overlaps":True}
    ),
    "Mirror Gate": AnchorPlan(
        name="Mirror Gate",
        description="Prepare shareable export bundle.",
        intent="reveal",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"export","format":["json","graphml"]}
    ),
    "Codex": AnchorPlan(
        name="Codex",
        description="Human-readable notes + facts.",
        intent="reveal",
        inputs_spec={"asset":"ip|domain"},
        actions=[
            AnchorAction(tool="shodan.host_view", args={"ip":"{{asset}}"}),
            AnchorAction(tool="censys.host_view", args={"ip":"{{asset}}"}),
        ],
        postprocess={"label":"codex","notes":True}
    ),
}

def _render(args: Dict[str, Any], inputs: Dict[str, str]) -> Dict[str, Any]:
    out = {}
    for k, v in args.items():
        if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
            key = v[2:-2].strip()
            out[k] = inputs.get(key)
        else:
            out[k] = v
    return out

async def execute_anchor(name: str, inputs: Dict[str, str]) -> ExecutionReport:
    plan = ANCHORS.get(name)
    if not plan:
        raise ValueError(f"Unknown anchor: {name}")

    events: List[ExecutionEvent] = []
    bundle = GraphBundle(entities=[], edges=[])

    for i, action in enumerate(plan.actions, start=1):
        args = _render(action.args, inputs)
        try:
            if action.tool == "shodan.host_view":
                e, ed = await shodan_adapter.host_view(args["ip"])
            elif action.tool == "censys.host_view":
                e, ed = await censys_adapter.host_view(args["ip"])
            else:
                raise NotImplementedError(action.tool)
            from app.schemas import GraphBundle as GB
            step = GB(entities=e, edges=ed)
            bundle = _merge(bundle, step)
            events.append(ExecutionEvent(step=i, action=action, status="ok"))
        except Exception as ex:
            events.append(ExecutionEvent(step=i, action=action, status="error", detail=str(ex)))

    return ExecutionReport(plan=plan, events=events, bundle=bundle, labels=plan.postprocess or {})
