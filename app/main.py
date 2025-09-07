from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.graph import make_graph
from app.orchestrator import investigate_ip, list_anchors, run_anchor

load_dotenv()

app = FastAPI()
graph = make_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/anchors")
async def anchors_catalog():
    return await list_anchors()

@app.post("/invoke/anchor/{name}")
async def invoke_anchor(name: str, asset: str):
    try:
        report = await run_anchor(name, asset)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    if report.bundle:
        graph.upsert(report.bundle.entities, report.bundle.edges)
    return report.model_dump()

@app.get("/investigate/ip/{ip}")
async def investigate_ip_route(ip: str):
    bundle = await investigate_ip(ip)
    graph.upsert(bundle.entities, bundle.edges)
    return bundle.model_dump()
