"""Shared pytest fixtures and canonical seed constants for Stage 1 & Stage 2 test suites."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.database import InMemoryCatalogRepository, get_catalog_repo
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_DAU_AN,
    ING_DAU_HU,
    ING_HANH_LA,
    ING_MUOI,
    ING_NUOC_MAM,
    ING_THIT_BA_CHI,
    ING_TRUNG_GA,
    REC_CANH_CA_CHUA_TRUNG,
    REC_DAU_HU_SOT_CA,
    REC_DRAFT,
    REC_THIT_KHO_TRUNG,
    REC_TRUNG_XAO_CA_CHUA,
)
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]

__all__ = [
    "ING_CA_CHUA",
    "ING_DAU_AN",
    "ING_DAU_HU",
    "ING_HANH_LA",
    "ING_MUOI",
    "ING_NUOC_MAM",
    "ING_THIT_BA_CHI",
    "ING_TRUNG_GA",
    "REC_CANH_CA_CHUA_TRUNG",
    "REC_DAU_HU_SOT_CA",
    "REC_DRAFT",
    "REC_THIT_KHO_TRUNG",
    "REC_TRUNG_XAO_CA_CHUA",
    "REPO_ROOT",
]


@pytest.fixture()
def repo() -> InMemoryCatalogRepository:
    """Fresh in-memory catalog repository seeded with deterministic test data."""
    return InMemoryCatalogRepository()


@pytest.fixture()
def client(repo: InMemoryCatalogRepository) -> TestClient:
    """FastAPI TestClient wired to the in-memory catalog repository fixture."""
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    return TestClient(app)

