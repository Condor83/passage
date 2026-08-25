from passage.domain.models import (
    ExternalChapterReferenceTarget,
    ExternalReferenceTarget,
    InternalChapterReferenceTarget,
    InternalReferenceTarget,
    ReferenceTarget,
)


def reference_target_key(target: ReferenceTarget) -> str:
    if isinstance(target, (InternalChapterReferenceTarget, ExternalChapterReferenceTarget)):
        suffix = f"-{target.end_chapter}" if target.end_chapter is not None else ""
        return f"{target.work}/{target.book}/{target.chapter}{suffix}"
    suffix = f"-{target.end_verse}" if target.end_verse is not None else ""
    return f"{target.work}/{target.book}/{target.chapter}/{target.verse}{suffix}"


def is_internal_reference_target(target: ReferenceTarget) -> bool:
    return isinstance(target, (InternalReferenceTarget, InternalChapterReferenceTarget))


def is_external_reference_target(target: ReferenceTarget) -> bool:
    return isinstance(target, (ExternalReferenceTarget, ExternalChapterReferenceTarget))
