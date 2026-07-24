from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from coa_workbench.planner.formats import RaidFormat, resolve_target_size


class RoleLimit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int | None = Field(default=None, ge=0, le=40)
    max: int | None = Field(default=None, ge=0, le=40)

    @model_validator(mode="after")
    def validate_order(self) -> "RoleLimit":
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("role limit min cannot exceed max")
        return self


class RaidProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    status: Literal["legacy_baseline", "draft_unapproved", "approved"]
    raid_format: RaidFormat
    target_size: int | None = Field(default=None, ge=1, le=40)
    target_size_source: Literal["fixed", "user_input"] = "fixed"
    allowed_size_range: tuple[int, int] | None = None
    role_limits: dict[str, RoleLimit] = Field(default_factory=dict)
    class_limit: int | None = Field(default=None, ge=1, le=40)
    spec_limit: int | None = Field(default=None, ge=1, le=40)
    capability_policy: str = "confirmed_or_manual"
    source_note: str | None = None

    @model_validator(mode="after")
    def validate_format(self) -> "RaidProfile":
        if self.raid_format is RaidFormat.FLEX:
            if self.target_size_source != "user_input":
                raise ValueError("FLEX profile must use target_size_source=user_input")
            if self.allowed_size_range is None:
                raise ValueError("FLEX profile requires allowed_size_range")
            lo, hi = self.allowed_size_range
            if not 1 <= lo <= hi <= 40:
                raise ValueError("invalid FLEX allowed_size_range")
        else:
            resolved = resolve_target_size(self.raid_format, self.target_size)
            if self.target_size != resolved:
                raise ValueError("fixed format has an invalid target_size")
        return self


class RaidProfilesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    raid_profiles: list[RaidProfile]


def load_raid_profiles(path: Path) -> RaidProfilesConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return RaidProfilesConfig.model_validate(payload)
