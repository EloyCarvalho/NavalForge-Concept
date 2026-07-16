from __future__ import annotations

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_session
from backend.app.main import app
from scripts.seed_examples import service_7m


class TestProjectRevisionApi(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)

        def override_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        self.client = TestClient(app)
        self.project = service_7m()
        self.project["project_id"] = "NF-API-REVISION-TEST"

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_create_update_history_and_conflict(self) -> None:
        created = self.client.post(
            "/api/v1/projects",
            json={"project": self.project, "change_summary": "Caso inicial"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["project"]["revision"], "P1")

        changed = created.json()["project"]
        changed["mission"]["target_range_nm"] = 95.0
        saved = self.client.post(
            f"/api/v1/projects/{changed['project_id']}/revisions",
            json={
                "project": changed,
                "expected_revision": "P1",
                "change_summary": "Alcance atualizado",
            },
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()["project"]["revision"], "P2")

        history = self.client.get(f"/api/v1/projects/{changed['project_id']}/revisions")
        self.assertEqual(history.status_code, 200)
        self.assertEqual({item["revision"] for item in history.json()}, {"P1", "P2"})

        stale = self.client.post(
            f"/api/v1/projects/{changed['project_id']}/revisions",
            json={
                "project": changed,
                "expected_revision": "P1",
                "change_summary": "Tentativa obsoleta",
            },
        )
        self.assertEqual(stale.status_code, 409)

        deleted = self.client.delete(f"/api/v1/projects/{changed['project_id']}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(
            self.client.get(f"/api/v1/projects/{changed['project_id']}").status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
