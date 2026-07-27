from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse

from coa_workbench import __version__
from coa_workbench.planner import MAX_RAID_SLOTS, RaidFormat
from coa_workbench.storage import PlanNotFoundError, PlanRepository
from coa_workbench.web.catalog import catalog_payload
from coa_workbench.web.models import PlanPreviewRequest, PlanPreviewResponse, build_plan_preview
from coa_workbench.web.ui import INDEX_HTML

logger = logging.getLogger("uvicorn.error")


def create_app(
    database_path: Path = Path("data/warehouse/coa.duckdb"),
    migrations_dir: Path = Path("migrations"),
) -> FastAPI:
    app = FastAPI(
        title="CoA Raid Intelligence",
        version=__version__,
        description="Local-first raid planning application",
    )
    repository = PlanRepository(database_path, migrations_dir)

    @app.middleware("http")
    async def request_diagnostics(request: Request, call_next):
        request_id = uuid4().hex[:8]
        started = perf_counter()
        logger.info(
            "request.start id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request.error id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        duration_ms = (perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request.end id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

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
        return {
            "formats": [item.value for item in RaidFormat],
            "max_slots": MAX_RAID_SLOTS,
            "fixed_sizes": {"10": 10, "25": 25, "40": 40},
        }

    @app.get("/api/catalog/class-specs")
    def class_specs() -> dict[str, object]:
        payload = catalog_payload()
        logger.info(
            "catalog.loaded entries=%s classes=%s",
            payload["entry_count"],
            len(payload["classes"]),
        )
        return payload

    @app.post("/api/plans/preview", response_model=PlanPreviewResponse)
    def preview(payload: PlanPreviewRequest) -> PlanPreviewResponse:
        result = build_plan_preview(payload)
        if result.validation_errors:
            logger.warning(
                "plan.preview.validation plan_id=%s errors=%s",
                result.plan_id,
                result.validation_errors,
            )
        return result

    @app.get("/api/plans")
    def list_plans() -> dict[str, object]:
        try:
            plans = repository.list()
        except Exception as exc:
            logger.exception("plans.list.failed database=%s", database_path)
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Не удалось получить список планов",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc
        logger.info("plans.list.success count=%s database=%s", len(plans), database_path)
        return {"plans": plans}

    @app.get("/api/plans/{plan_id}")
    def get_plan(plan_id: str) -> dict[str, object]:
        logger.info("plan.load.start plan_id=%s", plan_id)
        try:
            plan = repository.get(plan_id)
        except PlanNotFoundError as exc:
            logger.warning("plan.load.not_found plan_id=%s", plan_id)
            raise HTTPException(status_code=404, detail="Plan not found") from exc
        except Exception as exc:
            logger.exception("plan.load.failed plan_id=%s", plan_id)
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Не удалось открыть план",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc
        logger.info("plan.load.success plan_id=%s slots=%s", plan_id, len(plan["slots"]))
        return plan

    @app.post("/api/plans")
    def save_plan(payload: PlanPreviewRequest) -> dict[str, str]:
        preview_result = build_plan_preview(payload)
        action = "updated" if preview_result.plan_id else "created"
        logger.info(
            "plan.save.start action=%s plan_id=%s name=%r format=%s target=%s filled=%s",
            action,
            preview_result.plan_id,
            preview_result.plan_name,
            preview_result.raid_format.value,
            preview_result.target_size,
            preview_result.filled_slots,
        )
        if preview_result.validation_errors:
            logger.warning(
                "plan.save.rejected action=%s plan_id=%s errors=%s",
                action,
                preview_result.plan_id,
                preview_result.validation_errors,
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "План не сохранён: исправьте ошибки проверки",
                    "validation_errors": preview_result.validation_errors,
                },
            )
        try:
            plan_id = repository.save(preview_result.model_dump(mode="json"))
        except Exception as exc:
            logger.exception(
                "plan.save.failed action=%s plan_id=%s name=%r database=%s",
                action,
                preview_result.plan_id,
                preview_result.plan_name,
                database_path,
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Не удалось сохранить план",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc
        logger.info(
            "plan.save.success action=%s plan_id=%s name=%r",
            action,
            plan_id,
            preview_result.plan_name,
        )
        return {"plan_id": plan_id, "status": "saved", "action": action}

    @app.delete("/api/plans/{plan_id}", status_code=204)
    def delete_plan(plan_id: str) -> Response:
        logger.info("plan.delete.start plan_id=%s", plan_id)
        try:
            repository.delete(plan_id)
        except PlanNotFoundError as exc:
            logger.warning("plan.delete.not_found plan_id=%s", plan_id)
            raise HTTPException(status_code=404, detail="Plan not found") from exc
        except Exception as exc:
            logger.exception("plan.delete.failed plan_id=%s", plan_id)
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Не удалось удалить план",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc
        logger.info("plan.delete.success plan_id=%s", plan_id)
        return Response(status_code=204)

    return app


app = create_app()
