from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from coa_workbench import __version__
from coa_workbench.planner import MAX_RAID_SLOTS, RaidFormat
from coa_workbench.web.models import PlanPreviewRequest, PlanPreviewResponse, build_plan_preview
from coa_workbench.web.ui import INDEX_HTML


def create_app() -> FastAPI:
    app = FastAPI(
        title="CoA Raid Intelligence",
        version=__version__,
        description="Local-first raid planning application",
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return INDEX_HTML

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "mode": "localhost"}

    @app.get("/api/formats")
    def formats() -> dict[str, object]:
        return {
            "formats": [item.value for item in RaidFormat],
            "max_slots": MAX_RAID_SLOTS,
            "fixed_sizes": {"10": 10, "25": 25, "40": 40},
        }

    @app.post("/api/plans/preview", response_model=PlanPreviewResponse)
    def preview(payload: PlanPreviewRequest) -> PlanPreviewResponse:
        return build_plan_preview(payload)

    return app


app = create_app()
