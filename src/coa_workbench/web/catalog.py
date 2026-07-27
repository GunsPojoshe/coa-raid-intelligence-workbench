from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files


@dataclass(frozen=True, slots=True)
class ClassSpec:
    class_code: str
    class_name: str
    spec_code: str
    spec_name: str
    role: str


def load_class_specs() -> tuple[ClassSpec, ...]:
    resource = files("coa_workbench.web").joinpath("data/class_specs.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    return tuple(ClassSpec(**entry) for entry in payload["entries"])


CLASS_SPECS = load_class_specs()
CLASS_SPEC_BY_CODE = {(entry.class_code, entry.spec_code): entry for entry in CLASS_SPECS}


def catalog_payload() -> dict[str, object]:
    classes: dict[str, dict[str, object]] = {}
    for entry in CLASS_SPECS:
        current = classes.setdefault(
            entry.class_code,
            {"code": entry.class_code, "name": entry.class_name, "specs": []},
        )
        current["specs"].append(
            {"code": entry.spec_code, "name": entry.spec_name, "role": entry.role}
        )
    return {"schema_version": 1, "classes": list(classes.values()), "entry_count": len(CLASS_SPECS)}


def resolve_role(class_code: str, spec_code: str) -> str | None:
    entry = CLASS_SPEC_BY_CODE.get((class_code.strip(), spec_code.strip()))
    return entry.role if entry else None
