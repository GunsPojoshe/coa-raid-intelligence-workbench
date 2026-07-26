from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import HTMLResponse

from coa_workbench import __version__
from coa_workbench.planner import MAX_RAID_SLOTS, RaidFormat
from coa_workbench.storage import PlanNotFoundError, PlanRepository
from coa_workbench.web.catalog import catalog_payload
from coa_workbench.web.models import PlanPreviewRequest, PlanPreviewResponse, build_plan_preview
from coa_workbench.web.ui import INDEX_HTML


def create_app(
    database_path: Path = Path("data/warehouse/coa.duckdb"),
    migrations_dir: Path = Path("migrations"),
) -> FastAPI:
    app = FastAPI(title="CoA Raid Intelligence", version=__version__, description="Local-first raid planning application")
    repository = PlanRepository(database_path, migrations_dir)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return INDEX_HTML

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "mode": "localhost"}

    @app.get("/api/formats")
    def formats() -> dict[str, object]:
        return {"formats": [item.value for item in RaidFormat], "max_slots": MAX_RAID_SLOTS, "fixed_sizes": {"10": 10, "25": 25, "40": 40}}

    @app.get("/api/catalog/class-specs")
    def class_specs() -> dict[str, object]:
        return catalog_payload()

    @app.post("/api/plans/preview", response_model=PlanPreviewResponse)
    def preview(payload: PlanPreviewRequest) -> PlanPreviewResponse:
        return build_plan_preview(payload)

    @app.get("/api/plans")
    def list_plans() -> dict[str, object]:
        return {"plans": repository.list()}

    @app.get("/api/plans/{plan_id}")
    def get_plan(plan_id: str) -> dict[str, object]:
        try:
            return repository.get(plan_id)
        except PlanNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Plan not found") from exc

    @app.post("/api/plans")
    def save_plan(payload: PlanPreviewRequest) -> dict[str, str]:
        preview_result = build_plan_preview(payload)
        plan_id = repository.save(preview_result.model_dump(mode="json"))
        return {"plan_id": plan_id, "status": "saved"}

    @app.delete("/api/plans/{plan_id}", status_code=204)
    def delete_plan(plan_id: str) -> Response:
        try:
            repository.delete(plan_id)
        except PlanNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Plan not found") from exc
        return Response(status_code=204)

    return app


app = create_app()
