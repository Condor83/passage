from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scripture_chat.config import AppConfig
from scripture_chat.db.builder import CorpusBuilder
from scripture_chat.db.control import ControlStore
from scripture_chat.domain.errors import ErrorCode, ScriptureChatError
from scripture_chat.domain.models import (
    ContextRequest,
    EvidenceSearchRequest,
    LexicalSearchRequest,
    PassageRequest,
    SnapshotRequest,
    SourceApproval,
    TraversalRequest,
)
from scripture_chat.evidence.service import EvidenceService
from scripture_chat.http.app import create_app
from scripture_chat.ingest.normalize import normalize_extraction
from scripture_chat.ingest.validation import StructureManifest
from tests.unit.ingest.test_validation import extraction


@pytest.fixture
def accepted_config(tmp_path: Path) -> AppConfig:
    root = tmp_path / "private"
    manifest = StructureManifest(
        schema_version=1,
        source={},
        books={"1-ne": [4], "2-ne": [2]},
    )
    corpus = normalize_extraction(
        extraction(
            [
                ("bofm/1-ne/1/1", "Faith hope and charity."),
                ("bofm/1-ne/1/2", "Faith is things hoped for."),
                ("bofm/1-ne/1/3", "Hope and charity endure."),
                ("bofm/1-ne/1/4", "Repent and remember."),
                ("bofm/2-ne/1/1", "A faithful witness speaks."),
                ("bofm/2-ne/1/2", "Faith and hope remain."),
            ],
            [
                ("bofm/1-ne/1/1", "bofm/1-ne/1/2"),
                ("bofm/1-ne/1/1", "bible/john/3/16"),
                ("bofm/1-ne/1/2", "bofm/1-ne/1/3"),
            ],
        ),
        manifest,
    )
    approval = SourceApproval(
        source_sha256="a" * 64,
        acquisition_url="https://example.test/source.epub",
        acquisition_date=date(2026, 8, 16),
        edition="Current Church edition",
    )
    with ControlStore(root) as control:
        published = CorpusBuilder(root, control).build(corpus, approval, "b" * 64)
        control.activate(published.corpus_version, published.retrieval_config)
    return AppConfig(private_root=root)


@pytest.fixture
def live_client(accepted_config: AppConfig) -> Iterator[tuple[Any, TestClient]]:
    app = create_app(accepted_config)
    with TestClient(app, base_url="http://localhost") as client:
        yield app, client


def test_all_six_routes_serialize_the_shared_service_responses(
    live_client: tuple[Any, TestClient],
    accepted_config: AppConfig,
) -> None:
    _, client = live_client
    with ControlStore(accepted_config.private_root) as control:
        service = EvidenceService(control)
        expected = {
            "corpus": service.get_corpus(SnapshotRequest()).model_dump(mode="json"),
            "passage": service.get_passage(PassageRequest(reference="bofm/1-ne/1/2")).model_dump(
                mode="json"
            ),
            "context": service.get_context(
                ContextRequest(reference="bofm/1-ne/1/3", before=2, after=1)
            ).model_dump(mode="json"),
            "lexical": service.search_lexical(
                LexicalSearchRequest(query="faith", limit=2)
            ).model_dump(mode="json"),
            "traversal": service.traverse_references(
                TraversalRequest(reference="bofm/1-ne/1/1", max_depth=2, max_nodes=2)
            ).model_dump(mode="json"),
            "evidence": service.search_evidence(
                EvidenceSearchRequest(query="faith charity")
            ).model_dump(mode="json"),
        }

    corpus = client.get("/v1/corpus")
    passage = client.get("/v1/passages/bofm/1-ne/1/2")
    context = client.get("/v1/passages/bofm/1-ne/1/3/context", params={"before": 2, "after": 1})
    lexical = client.post("/v1/search/lexical", json={"query": "faith", "limit": 2})
    traversal = client.post(
        "/v1/references/traverse",
        json={"reference": "bofm/1-ne/1/1", "max_depth": 2, "max_nodes": 2},
    )
    evidence = client.post("/v1/evidence/search", json={"query": "faith charity"})

    assert corpus.status_code == 200
    assert corpus.json() == expected["corpus"]
    assert passage.status_code == 200
    assert passage.json() == expected["passage"]
    assert context.status_code == 200
    assert context.json() == expected["context"]
    assert lexical.status_code == 200
    assert lexical.json() == expected["lexical"]
    assert traversal.status_code == 200
    assert traversal.json() == expected["traversal"]
    assert evidence.status_code == 200
    assert evidence.json() == expected["evidence"]


def test_slash_preserving_context_route_precedes_catch_all(
    live_client: tuple[Any, TestClient],
) -> None:
    app, client = live_client

    response = client.get("/v1/passages/bofm/1-ne/1/3/context")
    route_paths = list(app.openapi()["paths"])

    assert response.status_code == 200
    assert response.json()["applied"]["operation"] == "get_context"
    assert route_paths.index("/v1/passages/{reference}/context") < route_paths.index(
        "/v1/passages/{reference}"
    )


def test_empty_search_is_a_success(live_client: tuple[Any, TestClient]) -> None:
    _, client = live_client

    response = client.post("/v1/search/lexical", json={"query": "unfindable"})

    assert response.status_code == 200
    assert response.json()["records"] == []
    assert response.json()["completeness"]["truncated"] is False


def test_openapi_declares_all_paths_and_transport_models(accepted_config: AppConfig) -> None:
    schema = create_app(accepted_config).openapi()

    assert set(schema["paths"]) == {
        "/v1/corpus",
        "/v1/passages/{reference}/context",
        "/v1/passages/{reference}",
        "/v1/search/lexical",
        "/v1/references/traverse",
        "/v1/evidence/search",
    }
    assert {
        "CorpusMetadata",
        "EvidenceResponse",
        "TraversalResponse",
        "LexicalSearchRequest",
        "TraversalRequest",
        "EvidenceSearchRequest",
        "HttpErrorEnvelope",
        "HttpErrorDetail",
    } <= set(schema["components"]["schemas"])
    assert "CORSMiddleware" not in {
        middleware.cls.__name__ for middleware in create_app(accepted_config).user_middleware
    }


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (ErrorCode.INVALID_REFERENCE, 400),
        (ErrorCode.INVALID_QUERY, 400),
        (ErrorCode.LIMIT_EXCEEDED, 400),
        (ErrorCode.PASSAGE_NOT_FOUND, 404),
        (ErrorCode.VERSION_UNAVAILABLE, 404),
        (ErrorCode.CORPUS_UNAVAILABLE, 503),
        (ErrorCode.CONFIG_UNAVAILABLE, 409),
        (ErrorCode.INTERNAL_ERROR, 500),
    ],
)
def test_every_domain_error_has_a_stable_http_envelope(
    accepted_config: AppConfig,
    code: ErrorCode,
    status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(accepted_config)
    with TestClient(
        app,
        base_url="http://localhost",
        raise_server_exceptions=False,
    ) as client:

        def fail(_: SnapshotRequest) -> None:
            raise ScriptureChatError(code, "domain failure", {"kind": "synthetic"})

        monkeypatch.setattr(app.state.evidence_service, "get_corpus", fail)
        response = client.get("/v1/corpus")

    assert response.status_code == status
    assert response.json()["error"]["code"] == code.value
    if code is ErrorCode.INTERNAL_ERROR:
        assert response.json()["error"]["message"] == "internal server error"
        assert set(response.json()["error"]["detail"]) == {"incident_id"}
    else:
        assert response.json() == {
            "error": {
                "code": code.value,
                "message": "domain failure",
                "detail": {"kind": "synthetic"},
            }
        }


def test_validation_separates_caps_from_other_invalid_queries(
    live_client: tuple[Any, TestClient],
) -> None:
    _, client = live_client

    capped = client.post("/v1/search/lexical", json={"query": "faith", "limit": 101})
    invalid = client.post("/v1/search/lexical", json={"query": ""})
    empty_filter = client.post(
        "/v1/search/lexical",
        json={"query": "faith", "filters": {"books": []}},
    )

    assert capped.status_code == 400
    assert capped.json()["error"]["code"] == "limit_exceeded"
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "invalid_query"
    assert empty_filter.status_code == 400
    assert empty_filter.json()["error"]["code"] == "invalid_query"
    assert "input" not in str(capped.json())
    assert "input" not in str(invalid.json())


def test_absent_and_unavailable_selected_snapshots_map_without_rewriting(
    live_client: tuple[Any, TestClient],
) -> None:
    _, client = live_client
    metadata = client.get("/v1/corpus").json()
    absent = client.get("/v1/passages/bofm/1-ne/9/9")
    version = client.get(
        "/v1/corpus",
        params={"corpus_version": "missing", "retrieval_config": "missing"},
    )
    config = client.get(
        "/v1/corpus",
        params={
            "corpus_version": metadata["corpus_version"],
            "retrieval_config": "missing",
        },
    )

    assert absent.status_code == 404
    assert absent.json()["error"]["code"] == "passage_not_found"
    assert version.status_code == 404
    assert version.json()["error"]["code"] == "version_unavailable"
    assert config.status_code == 409
    assert config.json()["error"]["code"] == "config_unavailable"


def test_startup_fails_closed_without_an_active_snapshot_and_closes_store(tmp_path: Path) -> None:
    created: list[ControlStore] = []

    def create_control(root: Path) -> ControlStore:
        control = ControlStore(root)
        created.append(control)
        return control

    app = create_app(
        AppConfig(private_root=tmp_path / "empty-private"),
        control_store_factory=create_control,
    )

    with (
        pytest.raises(ScriptureChatError) as raised,
        TestClient(app, base_url="http://localhost"),
    ):
        pass

    assert raised.value.code is ErrorCode.CORPUS_UNAVAILABLE
    with pytest.raises(sqlite3.ProgrammingError):
        created[0].connection.execute("SELECT 1")


@pytest.mark.parametrize(
    "host",
    ["attacker.example", "127.0.0.1.attacker.example", "0.0.0.0", "[::]"],
)
def test_host_middleware_rejects_non_loopback_and_dns_rebinding_values(
    live_client: tuple[Any, TestClient],
    host: str,
) -> None:
    _, client = live_client

    response = client.get("/v1/corpus", headers={"host": host})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_query"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert host not in response.text


@pytest.mark.parametrize("host", ["localhost", "localhost:8765", "127.0.0.1:8765", "[::1]:8765"])
def test_host_middleware_accepts_configured_loopback_values_with_optional_ports(
    live_client: tuple[Any, TestClient],
    host: str,
) -> None:
    _, client = live_client

    response = client.get("/v1/corpus", headers={"host": host})

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"


def test_origin_middleware_requires_an_explicit_local_allowlist(
    live_client: tuple[Any, TestClient],
) -> None:
    _, client = live_client

    local = client.get("/v1/corpus", headers={"origin": "http://localhost"})
    hostile = client.get("/v1/corpus", headers={"origin": "https://attacker.example"})

    assert local.status_code == 200
    assert hostile.status_code == 403
    assert hostile.json()["error"]["code"] == "invalid_query"
    assert "access-control-allow-origin" not in local.headers
    assert "access-control-allow-origin" not in hostile.headers
    assert hostile.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("bind", ["0.0.0.0", "::", "192.0.2.10", "example.test"])
def test_app_factory_rejects_non_loopback_bind_even_if_config_validation_is_bypassed(
    tmp_path: Path,
    bind: str,
) -> None:
    config = AppConfig.model_construct(
        private_root=tmp_path / "private",
        host=bind,
        port=8765,
        allowed_hosts=("localhost",),
        allowed_origins=("http://localhost",),
    )

    with pytest.raises(ValueError, match="loopback"):
        create_app(config)


def test_unexpected_errors_return_only_an_opaque_incident_identifier(
    accepted_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(accepted_config)
    with TestClient(
        app,
        base_url="http://localhost",
        raise_server_exceptions=False,
    ) as client:

        def explode(_: SnapshotRequest) -> None:
            raise RuntimeError("private source text and query must never escape")

        monkeypatch.setattr(app.state.evidence_service, "get_corpus", explode)
        response = client.get("/v1/corpus")

    error = response.json()["error"]
    assert response.status_code == 500
    assert error["code"] == "internal_error"
    assert error["message"] == "internal server error"
    assert len(error["detail"]["incident_id"]) == 32
    assert "private source" not in response.text
    assert "query" not in response.text


def test_control_store_is_closed_after_normal_shutdown(accepted_config: AppConfig) -> None:
    app = create_app(accepted_config)

    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/v1/corpus").status_code == 200
        control = app.state.control_store

    with pytest.raises(sqlite3.ProgrammingError):
        control.connection.execute("SELECT 1")
