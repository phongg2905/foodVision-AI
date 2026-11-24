"""Knowledge Base Coverage (20/20 YOLO Classes) & Postgres Personalization Parity Tests (TV1)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.database import (  # noqa: E402
    InMemoryCatalogRepository,
    PostgresCatalogRepository,
)
from app.core.seed_fixtures import (  # noqa: E402
    ING_NGHE,
    ING_SA,
    ING_THIT_GA_SONG,
    REC_GA_HAP_SA,
    REC_GA_KHO_SA_NGHE,
    REC_GA_XAO_SA_OT,
)
from app.intelligence.personalization import (  # noqa: E402
    PersonalizationFeedback,
    RecipeFeatureInput,
    extract_recipe_feature_vector,
)


# THUẬT TOÁN: Kiểm chứng Phủ 20/20 Lớp YOLO trong Cơ sở Tri thức Công thức (`seed_fixtures.py`)
# Cơ chế: Duyệt toàn bộ 20 nhãn hoạt động của mô hình YOLO v1 và xác minh mỗi nhãn đều xuất hiện
#         trong ít nhất 1 công thức đã xuất bản (`status == 'published'`).
# Complexity: Time O(R * I_r), Space O(K).
def test_all_20_yolo_classes_have_published_recipes_in_seed_kb(
    repo: InMemoryCatalogRepository,
) -> None:
    active_model = repo.get_active_ai_model()
    assert active_model is not None
    assert len(active_model.labels_by_index) == 20

    used_ingredient_ids: set[str] = set()
    for recipe in repo.get_all_published_recipes():
        for ri in recipe.ingredients:
            used_ingredient_ids.add(ri.ingredient_id)

    missing_classes = [
        f"{idx}:{lbl.class_name}"
        for idx, lbl in sorted(active_model.labels_by_index.items())
        if lbl.ingredient_id not in used_ingredient_ids
    ]
    assert missing_classes == [], f"YOLO classes without any published recipe: {missing_classes}"


# THUẬT TOÁN: Kiểm chứng Luồng End-to-End Kịch bản Bảo vệ "1 con gà + 1 củ sả + dị ứng nghệ"
# Cơ chế: Gửi `POST /api/v1/recommendations` với thịt gà + sả và danh sách dị ứng nghệ tươi;
#         xác minh món `Gà kho sả nghệ` bị chặn cứng (`BLOCKED`), `Gà hấp sả` xếp hạng đầu (`READY`),
#         và `Gà xào sả ớt` hiển thị ở nhóm thiếu nguyên liệu (`missing`).
# Complexity: Time O(R), Space O(R).
def test_chicken_lemongrass_turmeric_allergy_demo_scenario(client: TestClient) -> None:
    res_search_sa = client.get("/api/v1/ingredients?q=cu sa")
    assert res_search_sa.status_code == 200
    assert res_search_sa.json()["items"][0]["id"] == ING_SA

    res_search_nghe = client.get("/api/v1/ingredients?q=nghe")
    assert res_search_nghe.status_code == 200
    assert res_search_nghe.json()["items"][0]["id"] == ING_NGHE

    res = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_THIT_GA_SONG, ING_SA],
            "allergic_ingredient_ids": [ING_NGHE],
            "include_missing": True,
            "limit": 20,
        },
    )
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    by_id = {it["recipe"]["id"]: it for it in items}

    assert REC_GA_KHO_SA_NGHE not in by_id
    assert REC_GA_HAP_SA in by_id
    assert REC_GA_XAO_SA_OT in by_id
    assert items[0]["recipe"]["id"] == REC_GA_HAP_SA
    assert items[0]["availability"] == "ready"
    assert items[0]["reasoning_status"] == "READY"
    assert by_id[REC_GA_XAO_SA_OT]["availability"] == "missing"


# THUẬT TOÁN: Kiểm chứng Tương đương `PostgresCatalogRepository.personalization_engine` (Mocked Psycopg)
# Cơ chế: Giả lập bảng `user_preferences` trong bộ nhớ qua cursor giả, kiểm tra chuỗi đọc/ghi/đặt lại
#         trọng số Hồi quy Logistic 18 chiều và bộ lọc chống phát lại cũ hơn (`ADR-012`).
# Complexity: Time O(d), Space O(d).
def test_postgres_catalog_repository_personalization_engine_parity() -> None:
    store: dict[str, dict[str, Any]] = {}

    class _FakeCursor:
        def __init__(self) -> None:
            self._row: dict[str, Any] | None = None

        def __enter__(self) -> "_FakeCursor":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
            sql_norm = " ".join(sql.split()).upper()
            if sql_norm.startswith("SELECT LR_WEIGHTS"):
                uid = str(params[0])
                self._row = store.get(uid)
            elif sql_norm.startswith("INSERT INTO PUBLIC.USER_PREFERENCES"):
                uid = str(params[0])
                raw_weights = getattr(params[1], "obj", params[1])
                if len(params) == 4:
                    fb_count = int(params[2])
                    ver = str(params[3])
                else:
                    fb_count = 0
                    ver = str(params[2])
                now_ts = datetime.now(timezone.utc)
                store[uid] = {
                    "lr_weights": list(raw_weights),
                    "feedback_count": fb_count,
                    "lr_model_version": ver,
                    "updated_at": now_ts,
                }
                self._row = {"updated_at": now_ts}

        def fetchone(self) -> dict[str, Any] | None:
            return self._row

    class _FakeConn:
        def __enter__(self) -> "_FakeConn":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def cursor(self) -> _FakeCursor:
            return _FakeCursor()

        def commit(self) -> None:
            return None

    pg_repo = PostgresCatalogRepository("postgresql://user:pass@localhost:5432/postgres")
    pg_repo._connect = lambda: _FakeConn()  # type: ignore[method-assign]

    engine = pg_repo.personalization_engine
    assert engine is not None

    uid = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    rid = UUID("22222222-2222-4222-8222-222222222209")
    feat = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="steam",
            total_minutes=30,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
        ),
        config=engine.config,
    )
    res = engine.update_from_feedback(
        uid,
        feat,
        PersonalizationFeedback(uid, rid, rating=5, updated_at=datetime(2026, 11, 23, 1, 0, tzinfo=timezone.utc)),
    )
    assert res.model_state_update is not None
    assert res.model_state_update.applied is True
    assert store[str(uid)]["feedback_count"] == 1
    assert len(store[str(uid)]["lr_weights"]) == 18

    reset_upd = engine.reset_user_personalization(uid)
    assert reset_upd.applied is True
    assert store[str(uid)]["feedback_count"] == 0
    assert store[str(uid)]["lr_weights"] == []
