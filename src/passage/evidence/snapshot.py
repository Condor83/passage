from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from passage.db.contracts import (
    AcceptedSnapshot,
    ControlState,
    EvidenceRepository,
    RepositorySessionFactory,
)
from passage.domain.errors import (
    ConfigUnavailableError,
    CorpusUnavailableError,
    VersionUnavailableError,
)

if TYPE_CHECKING:
    from passage.domain.models import SnapshotSelector


@dataclass(slots=True)
class PinnedSnapshot:
    accepted: AcceptedSnapshot
    config: dict[str, object]
    repository: EvidenceRepository

    @property
    def corpus_version(self) -> str:
        return self.accepted.corpus_version

    @property
    def retrieval_config(self) -> str:
        return self.accepted.retrieval_config

    def __enter__(self) -> PinnedSnapshot:
        return self

    def __exit__(self, *_: object) -> None:
        self.repository.close()


class SnapshotManager:
    def __init__(
        self,
        control: ControlState,
        repository_factory: RepositorySessionFactory,
    ) -> None:
        self.control = control
        self.repository_factory = repository_factory

    def pin(self, selector: SnapshotSelector) -> PinnedSnapshot:
        if selector.corpus_version is None:
            active = self.control.get_active()
            if active is None:
                raise CorpusUnavailableError()
            corpus_version = active.corpus_version
            retrieval_config = active.retrieval_config
        else:
            corpus_version = selector.corpus_version
            if selector.retrieval_config is None:
                raise ConfigUnavailableError("retrieval configuration is required")
            retrieval_config = selector.retrieval_config

        accepted = self.control.get_accepted(corpus_version)
        if accepted is None:
            raise VersionUnavailableError(corpus_version)
        if retrieval_config is None or accepted.retrieval_config != retrieval_config:
            raise ConfigUnavailableError("selected corpus/configuration pair is unavailable")
        config = self.control.get_config(retrieval_config)
        if config is None:
            raise ConfigUnavailableError("selected retrieval configuration is unavailable")
        repository = self.repository_factory(corpus_version, retrieval_config)
        return PinnedSnapshot(
            accepted=accepted,
            config=config,
            repository=repository,
        )
