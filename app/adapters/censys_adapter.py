import os, httpx
from typing import Tuple, List
from app.schemas import Entity, Edge

API = "https://search.censys.io/api/v2"
UID = os.getenv("CENSYS_API_ID")
SEC = os.getenv("CENSYS_API_SECRET")

async def host_view(ip: str) -> Tuple[List[Entity], List[Edge]]:
    if not UID or not SEC:
        return [], []
    async with httpx.AsyncClient(timeout=30, auth=(UID, SEC)) as client:
        r = await client.get(f"{API}/hosts/{ip}")
        if r.status_code == 404:
            return [], []
        r.raise_for_status()
        data = r.json().get("result", {})

    ents, edges = [], []
    ip_id = f"ip:{ip}"
    ents.append(Entity(type="IpAddress", id=ip_id, props={"ip": ip}))
    for s in (data.get("services") or []):
        svc_id = f"svc:{ip}:{s.get('port')}/{s.get('service_name')}"
        ents.append(Entity(type="Service", id=svc_id, props=s))
        edges.append(Edge(src=ip_id, dst=svc_id, rel="EXPOSES", props={}))
    return ents, edges
