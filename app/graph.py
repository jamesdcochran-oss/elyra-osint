import os
from typing import List
from app.schemas import Entity, Edge

class NoOpGraph:
    def upsert(self, entities: List[Entity], edges: List[Edge]):
        return

def make_graph():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    if not (uri and user and pwd):
        return NoOpGraph()
    try:
        from neo4j import GraphDatabase
    except Exception:
        return NoOpGraph()

    class Graph:
        def __init__(self, uri, user, pwd):
            self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
        def upsert(self, entities: List[Entity], edges: List[Edge]):
            q_entity = """UNWIND $rows AS r
            MERGE (n:Entity {id:r.id}) SET n.type=r.type, n += r.props"""
            q_edge = """UNWIND $rows AS r
            MATCH (a:Entity {id:r.src}),(b:Entity {id:r.dst})
            MERGE (a)-[e:REL {rel:r.rel}]->(b) SET e += r.props"""
            with self.driver.session() as s:
                s.run(q_entity, rows=[e.model_dump() for e in entities])
                s.run(q_edge, rows=[e.model_dump() for e in edges])
    return Graph(uri, user, pwd)
