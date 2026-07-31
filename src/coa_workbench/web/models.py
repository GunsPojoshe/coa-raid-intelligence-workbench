from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from coa_workbench.planner import MAX_RAID_SLOTS, RaidFormat, active_slot_flags, resolve_target_size
from coa_workbench.web.catalog import resolve_role
from coa_workbench.web.trusted_effects import analyze_composition


class RaidSlotInput(BaseModel):
    slot_no: int = Field(ge=1, le=MAX_RAID_SLOTS)
    player_name: str = Field(default="", max_length=80)
    class_code: str = Field(default="", max_length=80)
    spec_code: str = Field(default="", max_length=80)
    role: str = Field(default="", max_length=40)
    locked: bool = False


class PlanPreviewRequest(BaseModel):
    plan_id: str | None = None
    plan_name: str = Field(default="Новый план", max_length=120)
    raid_date: str | None = None
    boss_id: str = Field(default="", max_length=120)
    raid_format: RaidFormat = RaidFormat.TWENTY_FIVE
    target_size: int | None = Field(default=None, ge=1, le=MAX_RAID_SLOTS)
    slots: list[RaidSlotInput] = Field(default_factory=list, max_length=MAX_RAID_SLOTS)

    @model_validator(mode="after")
    def validate_plan(self) -> "PlanPreviewRequest":
        numbers = [slot.slot_no for slot in self.slots]
        if len(numbers) != len(set(numbers)):
            raise ValueError("номера слотов не должны повторяться")
        names = [slot.player_name.strip().casefold() for slot in self.slots if slot.player_name.strip()]
        if len(names) != len(set(names)):
            raise ValueError("один игрок не может занимать несколько слотов")
        resolve_target_size(self.raid_format, self.target_size)
        return self

    def resolved_target_size(self) -> int:
        return resolve_target_size(self.raid_format, self.target_size)


class SlotPreview(BaseModel):
    slot_no: int
    active: bool
    player_name: str = ""
    class_code: str = ""
    spec_code: str = ""
    role: str = ""
    locked: bool = False


class PlanPreviewResponse(BaseModel):
    plan_id: str | None = None
    plan_name: str
    raid_date: str | None = None
    boss_id: str = ""
    raid_format: RaidFormat
    target_size: int
    filled_slots: int
    remaining_slots: int
    role_counts: dict[str, int]
    validation_errors: list[str]
    slots: list[SlotPreview]
    coverage: dict[str, Any]
    recommendations: list[dict[str, Any]]
    scoring: dict[str, Any]


def build_plan_preview(payload: PlanPreviewRequest) -> PlanPreviewResponse:
    target_size = payload.resolved_target_size()
    supplied = {slot.slot_no: slot for slot in payload.slots}
    result_slots: list[SlotPreview] = []
    role_counts: dict[str, int] = {}
    errors: list[str] = []

    for slot_no, active in enumerate(active_slot_flags(target_size), start=1):
        source = supplied.get(slot_no)
        class_code = source.class_code.strip() if source else ""
        spec_code = source.spec_code.strip() if source else ""
        derived_role = resolve_role(class_code, spec_code) if class_code and spec_code else None
        role = derived_role or (source.role.strip() if source else "")
        preview = SlotPreview(
            slot_no=slot_no,
            active=active,
            player_name=source.player_name.strip() if source else "",
            class_code=class_code,
            spec_code=spec_code,
            role=role,
            locked=source.locked if source else False,
        )
        result_slots.append(preview)
        if active and preview.player_name and preview.role:
            role_counts[preview.role] = role_counts.get(preview.role, 0) + 1
        if not active and preview.player_name:
            errors.append(f"Слот {slot_no} неактивен для размера рейда {target_size}")
        if active and preview.player_name and (not preview.class_code or not preview.spec_code):
            errors.append(
                f"Слот {slot_no}: для заполненного игрока выберите класс и специализацию"
            )
        if active and preview.player_name and preview.class_code and preview.spec_code and not derived_role:
            errors.append(f"Слот {slot_no}: неизвестная пара класса и специализации")

    analytics = analyze_composition(result_slots, top_n=3)
    filled_slots = sum(1 for slot in result_slots if slot.active and slot.player_name)
    return PlanPreviewResponse(
        plan_id=payload.plan_id,
        plan_name=payload.plan_name.strip() or "Новый план",
        raid_date=payload.raid_date,
        boss_id=payload.boss_id.strip(),
        raid_format=payload.raid_format,
        target_size=target_size,
        filled_slots=filled_slots,
        remaining_slots=target_size - filled_slots,
        role_counts=dict(sorted(role_counts.items())),
        validation_errors=errors,
        slots=result_slots,
        coverage=analytics["coverage"],
        recommendations=analytics["recommendations"],
        scoring=analytics["scoring"],
    )
