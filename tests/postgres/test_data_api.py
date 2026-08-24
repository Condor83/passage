from __future__ import annotations

import tomllib
import uuid
from pathlib import Path

import httpx
import pytest

from tests.postgres.conftest import LocalSupabaseStack


def _authenticated_token(stack: LocalSupabaseStack) -> str:
    token = uuid.uuid4().hex
    response = httpx.post(
        f"{stack.api_url}/auth/v1/signup",
        headers={"apikey": stack.anon_key},
        json={
            "email": f"u3-{token}@example.test",
            "password": f"Synthetic-{token}!",
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        pytest.fail("local Supabase Auth did not issue a synthetic access token")
    return access_token


def _api_headers(stack: LocalSupabaseStack, token: str) -> dict[str, str]:
    return {
        "apikey": stack.anon_key,
        "authorization": f"Bearer {token}",
    }


def test_passage_schema_is_absent_from_data_api_configuration() -> None:
    config = tomllib.loads(Path("supabase/config.toml").read_text(encoding="utf-8"))

    assert "passage" not in config["api"]["schemas"]
    assert "passage" not in config["api"]["extra_search_path"]


def test_rest_cannot_select_passage_schema_as_anon_or_authenticated(
    local_supabase_stack: LocalSupabaseStack,
) -> None:
    authenticated = _authenticated_token(local_supabase_stack)

    for token in (
        local_supabase_stack.anon_key,
        authenticated,
        local_supabase_stack.service_role_key,
    ):
        response = httpx.get(
            f"{local_supabase_stack.api_url}/rest/v1/passage_versions",
            headers={
                **_api_headers(local_supabase_stack, token),
                "accept-profile": "passage",
            },
            params={"select": "*"},
            timeout=10,
        )
        assert response.status_code == 406
        assert response.json()["code"] == "PGRST106"


def test_graphql_has_no_passage_collection_for_anon_or_authenticated(
    local_supabase_stack: LocalSupabaseStack,
) -> None:
    authenticated = _authenticated_token(local_supabase_stack)
    query = {"query": "query { passageVersionsCollection { edges { node { corpusVersion } } } }"}

    for token in (
        local_supabase_stack.anon_key,
        authenticated,
        local_supabase_stack.service_role_key,
    ):
        response = httpx.post(
            f"{local_supabase_stack.api_url}/graphql/v1",
            headers=_api_headers(local_supabase_stack, token),
            json=query,
            timeout=10,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("data") in (None, {})
        assert payload.get("errors")
