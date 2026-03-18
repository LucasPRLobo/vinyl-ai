"""Natural language query API routes."""

import json

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.graph.connection import get_neo4j_driver
from app.services.research import nl_to_cypher, synthesize_query_response
from app.dependencies import get_user_id

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    group_id: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    cypher: str
    raw_results: list[dict]


@router.post("/", response_model=QueryResponse)
def query_graph(req: QueryRequest, uid: str = Depends(get_user_id)):
    try:
        cypher = nl_to_cypher(req.question, group_id=req.group_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate query: {e}")

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            params = {"user_id": uid}
            if req.group_id:
                params["group_id"] = req.group_id
            result = session.run(cypher, **params)
            records = [record.data() for record in result]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query execution failed. Generated Cypher may be invalid: {e}",
        )

    if not records:
        return QueryResponse(
            question=req.question,
            answer="No results found for that question. Try rephrasing or adding more records.",
            cypher=cypher,
            raw_results=[],
        )

    try:
        answer = synthesize_query_response(
            req.question, json.dumps(records, indent=2, default=str)
        )
    except Exception:
        answer = json.dumps(records, indent=2, default=str)

    return QueryResponse(
        question=req.question,
        answer=answer,
        cypher=cypher,
        raw_results=records,
    )
