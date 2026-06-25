"""Tests for the starters package (Phase 13.3) — deterministic, offline scaffolds."""

import pytest
from starters import get_starter, list_starters


def test_list_includes_empty_and_fastapi():
    ids = {s.id for s in list_starters()}
    assert {"empty", "fastapi-saas"} <= ids


def test_get_starter_is_deterministic():
    assert get_starter("fastapi-saas") == get_starter("fastapi-saas")


def test_fastapi_starter_has_expected_files():
    files = get_starter("fastapi-saas")
    for expected in (
        "app/main.py",
        "app/security.py",
        "tests/test_app.py",
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
    ):
        assert expected in files
    assert "jwt" in files["app/security.py"].lower()


def test_empty_starter_is_minimal():
    assert set(get_starter("empty")) == {"README.md"}


def test_unknown_starter_raises():
    with pytest.raises(KeyError):
        get_starter("nope")
