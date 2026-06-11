from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data.mock_cases import MOCK_CASES, get_case_summaries
from engine.rules import execute_test_plan
from schemas.gutachten import CaseSummary, Gutachten
from schemas.verdict import TestPlanResult

app = FastAPI(
    title="Autocomply API",
    description=(
        "RegTech platform for vehicle homologation (Einzelabnahme). "
        "One Gutachten in, one auditable verdict out."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "autocomply-api"}


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases():
    """Return the 5 archetypal reference cases for frontend selection."""
    return get_case_summaries()


@app.get("/api/cases/{case_id}", response_model=Gutachten)
def get_case(case_id: str):
    """Return full Gutachten JSON for a specific mock case."""
    if case_id not in MOCK_CASES:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return MOCK_CASES[case_id]


@app.post("/api/analyze", response_model=TestPlanResult)
def analyze_gutachten(gutachten: Gutachten):
    """
    Accept a structured Gutachten JSON and return a full deterministic test plan result.
    No generative inference — rules engine only.
    """
    return execute_test_plan(gutachten)
