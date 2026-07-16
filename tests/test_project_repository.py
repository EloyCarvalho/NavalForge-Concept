from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db import Base
from backend.app.repository import (
    RevisionConflictError,
    create_project,
    delete_project,
    get_project_revision,
    list_project_revisions,
    next_revision,
    save_project_revision,
    upsert_project,
)
from navalforge_core.models import Project
from scripts.seed_examples import service_7m


class TestProjectRevisionRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.project = Project.model_validate(service_7m()).model_copy(
            update={"project_id": "NF-TEST-REVISION"}
        )

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_revision_labels_increment(self) -> None:
        self.assertEqual(next_revision("P1"), "P2")
        self.assertEqual(next_revision("r9"), "R10")
        self.assertEqual(next_revision("draft"), "P2")

    def test_create_and_save_preserve_immutable_history(self) -> None:
        record, first_snapshot = create_project(self.session, self.project)
        self.assertEqual(record.revision, "P1")
        self.assertEqual(first_snapshot.revision, "P1")

        changed = self.project.model_copy(update={"name": "Projeto alterado"})
        record, second_snapshot, revised = save_project_revision(
            self.session,
            changed,
            expected_revision="P1",
            change_summary="Nome atualizado",
        )
        self.assertEqual(record.revision, "P2")
        self.assertEqual(revised.revision, "P2")
        self.assertTrue(all(requirement.revision == "P2" for requirement in revised.requirements))

        history = list_project_revisions(self.session, self.project.project_id)
        self.assertEqual({item.revision for item in history}, {"P1", "P2"})
        historical = get_project_revision(
            self.session,
            self.project.project_id,
            first_snapshot.revision_id,
        )
        self.assertIsNotNone(historical)
        assert historical is not None
        self.assertEqual(historical.project_data["name"], self.project.name)
        self.assertEqual(second_snapshot.change_summary, "Nome atualizado")

    def test_stale_revision_is_rejected(self) -> None:
        create_project(self.session, self.project)
        with self.assertRaises(RevisionConflictError):
            save_project_revision(
                self.session,
                self.project,
                expected_revision="P0",
            )

    def test_legacy_project_gets_baseline_snapshot_on_first_save(self) -> None:
        upsert_project(self.session, self.project)
        _, _, revised = save_project_revision(
            self.session,
            self.project,
            expected_revision="P1",
        )
        history = list_project_revisions(self.session, self.project.project_id)
        self.assertEqual(revised.revision, "P2")
        self.assertEqual({item.revision for item in history}, {"P1", "P2"})

    def test_delete_removes_project_and_history(self) -> None:
        create_project(self.session, self.project)
        self.assertTrue(delete_project(self.session, self.project.project_id))
        self.assertFalse(delete_project(self.session, self.project.project_id))
        self.assertEqual(list_project_revisions(self.session, self.project.project_id), [])


if __name__ == "__main__":
    unittest.main()
