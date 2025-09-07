import os, httpx
from typing import Tuple, List
from app.schemas import Entity, Edge

API = "https://api.shodan.io"
KEY = os.getenv("SHODAN_API_KEY")

async def host_view(ip: str) -> Tuple[List[Entity], List[Edge]]:
    if not KEY:
        return [], []
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API}/shodan/host/{ip}", params={"key": KEY})
        if r.status_code == 404:
            return [], []
        r.raise_for_status()
        data = r.json()

    ents, edges = [], []
    ip_id = f"ip:{ip}"
    ents.append(Entity(type="IpAddress", id=ip_id, props={"ip": ip}))

    for item in data.get("data", []):
        port = item.get("port")
        module = (item.get("_shodan") or {}).get("module", "")
        svc_id = f"svc:{ip}:{port}/{module}"
        ents.append(Entity(type="Service", id=svc_id, props={
            "ip": ip, "port": port, "proto": module, "banner": item
        }))
        edges.append(Edge(src=ip_id, dst=svc_id, rel="EXPOSES", props={}))

        for cve in (item.get("vulns") or {}):
            v_id = f"vuln:{cve}"
            ents.append(Entity(type="Vulnerability", id=v_id, props={"cve": cve, "source": "shodan"}))
            edges.append(Edge(src=svc_id, dst=v_id, rel="HAS_VULN", props={}))

    return ents, edges
