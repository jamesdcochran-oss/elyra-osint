from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Service(BaseModel):
    ip: str
    port: int
    proto: str
    banner: Optional[dict] = None
    product: Optional[str] = None

class Vulnerability(BaseModel):
    cve: str
    severity: Optional[str] = None
    source: str

class Entity(BaseModel):
    type: str
    id: str
    props: Dict[str, Any] = Field(default_factory=dict)

class Edge(BaseModel):
    src: str
    dst: str
    rel: str
    props: Dict[str, Any] = Field(default_factory=dict)

class GraphBundle(BaseModel):
    entities: List[Entity]
    edges: List[Edge]

class AnchorAction(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    capture_as: Optional[str] = None

class AnchorPlan(BaseModel):
    name: str
    description: str
    intent: str
    inputs_spec: Dict[str, str]
    actions: List[AnchorAction]
    postprocess: Optional[Dict[str, Any]] = None

class ExecutionEvent(BaseModel):
    step: int
    action: AnchorAction
    status: str
    detail: Optional[str] = None

class ExecutionReport(BaseModel):
    plan: AnchorPlan
    events: List[ExecutionEvent] = Field(default_factory=list)
    bundle: Optional[GraphBundle] = None
    labels: Dict[str, Any] = Field(default_factory=dict)
