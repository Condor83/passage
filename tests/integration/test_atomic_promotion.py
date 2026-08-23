from pathlib import Path

import pytest

from passage.db.builder import BuildFault, CorpusBuilder
from passage.db.control import ControlStore
from passage.db.repository import CorpusRepository
from tests.integration.test_corpus_build import approval, sample_corpus


@pytest.mark.parametrize(
    "stage",
    [
        "after_commit",
        "after_checkpoint",
        "after_close",
        "after_reconcile",
        "after_file_fsync",
        "after_rename",
        "after_registration",
    ],
)
def test_failed_replacement_never_changes_active_snapshot(tmp_path: Path, stage: str) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        builder = CorpusBuilder(root, control)
        original = builder.build(sample_corpus(), approval(), "b" * 64)
        control.activate(original.corpus_version, original.retrieval_config)

        with pytest.raises(BuildFault):
            builder.build(
                sample_corpus("Replacement text"),
                approval("c" * 64),
                "d" * 64,
                fault_at=stage,
            )
        assert control.accepted_count() == 1
        assert control.latest_accepted() == control.get_accepted(original.corpus_version)
        rejected = control.connection.execute(
            """SELECT state, error_code FROM build_attempts
               WHERE state = 'rejected'"""
        ).fetchall()
        assert [(row["state"], row["error_code"]) for row in rejected] == [
            ("rejected", "injected_fault")
        ]

    with ControlStore(root) as reopened:
        active = reopened.get_active()
        assert active is not None
        assert active.corpus_version == original.corpus_version
        assert active.retrieval_config == original.retrieval_config
        with CorpusRepository.open(reopened) as repository:
            assert repository.get_passage("bofm/1-ne/1/2").text == "Second verse"


def test_invalid_activation_keeps_prior_pair(tmp_path: Path) -> None:
    root = tmp_path / "private"
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(sample_corpus(), approval(), "b" * 64)
        control.activate(published.corpus_version, published.retrieval_config)

        with pytest.raises(ValueError, match="compatible accepted"):
            control.activate(published.corpus_version, "missing-config")

        assert control.get_active().retrieval_config == published.retrieval_config
