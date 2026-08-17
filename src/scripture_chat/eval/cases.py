from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from scripture_chat.domain.identifiers import CanonicalReference
from scripture_chat.domain.models import Identifier, SearchFilters, StrictModel


class EvidenceJudgment(StrictModel):
    reference: str
    grade: int = Field(ge=0, le=3)

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        reference = CanonicalReference.parse(value)
        if reference.end_verse is not None:
            raise ValueError("judgments must identify one passage")
        return value


class EvaluationCase(StrictModel):
    case_id: Identifier
    schema_version: int = Field(default=1, ge=1)
    split: Literal["development", "locked"]
    query: Annotated[
        str,
        StringConstraints(min_length=1, max_length=512, strip_whitespace=True),
    ]
    filters: SearchFilters | None = None
    curator_rationale: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    non_authoritative_notes: Annotated[
        str,
        StringConstraints(max_length=4000),
    ] = ""
    judgments: list[EvidenceJudgment] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_judgments(self) -> EvaluationCase:
        references = [judgment.reference for judgment in self.judgments]
        if len(references) != len(set(references)):
            raise ValueError("judgment references must be unique within a case")
        return self


def load_cases(path: Path) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                cases.append(EvaluationCase.model_validate_json(line))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid evaluation case at line {line_number}") from exc
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("evaluation case identifiers must be unique")
    return cases
