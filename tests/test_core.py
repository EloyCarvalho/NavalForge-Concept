from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from navalforge_core.equilibrium import solve_equilibrium
from navalforge_core.evaluator import avaliar_projeto, evaluate_project, evaluate_single
from navalforge_core.geometry import mesh_payload
from navalforge_core.hydrostatics import calculate_hydrostatics
from navalforge_core.models import Geometry, Project
from navalforge_core.propulsion import load_engine_database, match_engines
from navalforge_core.reports import generate_report_bundle
from navalforge_core.requirements import verify_requirements
from navalforge_core.resistance import calculate_resistance_point
from navalforge_core.stability import calculate_stability
from navalforge_core.structure import preliminary_structure
from navalforge_core.tanks import tank_analysis
from navalforge_core.units import hp_to_kw, knots_to_m_s, kw_to_hp
from navalforge_core.variants import generate_and_select_variants
from navalforge_core.weights import calculate_weights
from scripts.seed_examples import patrol_10m, rescue_12m, service_7m


def project_7m() -> Project:
    return Project.model_validate(service_7m())


class TestModelsAndUnits(unittest.TestCase):
    def test_knots_conversion(self) -> None:
        self.assertAlmostEqual(knots_to_m_s(10), 5.14444, places=5)

    def test_power_round_trip(self) -> None:
        self.assertAlmostEqual(kw_to_hp(hp_to_kw(300)), 300.0, places=8)

    def test_geometry_rejects_lwl_above_loa(self) -> None:
        raw = service_7m()["geometry"]
        raw["lwl_m"] = 7.5
        with self.assertRaises(ValidationError):
            Geometry.model_validate(raw)

    def test_three_projects_validate(self) -> None:
        for factory in (service_7m, patrol_10m, rescue_12m):
            project = Project.model_validate(factory())
            self.assertTrue(5.0 <= project.geometry.loa_m <= 15.0)


class TestWeightsHydrostaticsAndEquilibrium(unittest.TestCase):
    def test_weight_centres_are_finite_and_symmetric(self) -> None:
        summary = calculate_weights(project_7m())
        self.assertGreater(summary.total_kg, 2000)
        self.assertAlmostEqual(summary.tcg_m, 0.0, places=7)
        self.assertGreater(summary.confidence, 0.5)

    def test_volume_increases_with_draft(self) -> None:
        geometry = project_7m().geometry
        shallow = calculate_hydrostatics(geometry, 0.35)
        deep = calculate_hydrostatics(geometry, 0.55)
        self.assertGreater(deep.volume_m3, shallow.volume_m3)
        self.assertGreater(deep.waterplane_area_m2, 0.0)

    def test_equilibrium_conserves_weight_and_buoyancy(self) -> None:
        project = project_7m()
        weights = calculate_weights(project)
        hydro = solve_equilibrium(project.geometry, weights.total_kg, weights.lcg_m)
        self.assertTrue(hydro.converged)
        self.assertLess(abs(hydro.residual_mass_kg), 2.0)
        self.assertLess(abs(hydro.residual_lcg_m), 0.01)

    def test_free_surface_only_for_partial_tank(self) -> None:
        project = project_7m()
        weights = calculate_weights(project)
        partial = tank_analysis(project, weights.total_kg)
        self.assertGreater(partial["combined_gm_correction_m"], 0.0)
        project.loading_conditions[0].tank_fills["T7-FUEL"] = 1.0
        full = tank_analysis(project, weights.total_kg)
        self.assertEqual(full["combined_gm_correction_m"], 0.0)


class TestEngineeringModules(unittest.TestCase):
    def setUp(self) -> None:
        self.project = project_7m()
        self.weights = calculate_weights(self.project)
        self.hydro = solve_equilibrium(
            self.project.geometry, self.weights.total_kg, self.weights.lcg_m
        )

    def test_gm_identity(self) -> None:
        stability = calculate_stability(self.project, self.weights, self.hydro)
        expected = (
            self.hydro.kb_m
            + self.hydro.bmt_m
            - self.weights.vcg_m
            - stability["free_surface_correction_m"]
        )
        self.assertAlmostEqual(stability["gm_corrected_m"], expected, places=10)

    def test_downflooding_point_limits_curve(self) -> None:
        stability = calculate_stability(self.project, self.weights, self.hydro)
        self.assertLessEqual(stability["downflooding_angle_deg"], 60.0)
        self.assertGreater(len(stability["gz_curve"]), 10)

    def test_resistance_power_rises_with_speed(self) -> None:
        low = calculate_resistance_point(self.project, self.weights, self.hydro, 15)
        high = calculate_resistance_point(self.project, self.weights, self.hydro, 34)
        self.assertGreater(high["effective_power_kw"], low["effective_power_kw"])
        self.assertGreater(high["froude_number"], low["froude_number"])

    def test_engine_matching_respects_installation(self) -> None:
        engines = load_engine_database()
        matches = match_engines(self.project, 105.0, engines)
        self.assertTrue(matches)
        self.assertTrue(all(item["compatibility"] == "compatible" for item in matches))

    def test_preliminary_structure_has_six_elements(self) -> None:
        structure = preliminary_structure(self.project, self.weights, self.hydro)
        self.assertEqual(len(structure["elements"]), 6)
        for element in structure["elements"]:
            self.assertGreaterEqual(
                element["adopted_commercial_thickness_mm"],
                element["calculated_thickness_mm"],
            )

    def test_mesh_uses_native_y_up_coordinates(self) -> None:
        payload = mesh_payload(self.project.geometry)
        vertices = payload["vertices"]
        y_values = [vertex[1] for vertex in vertices]
        z_values = [vertex[2] for vertex in vertices]
        self.assertGreater(max(y_values) - min(y_values), 1.0)
        self.assertGreater(max(z_values) - min(z_values), 1.5)
        self.assertGreaterEqual(min(y_values), 0.0)


class TestRequirementsPipelineAndReports(unittest.TestCase):
    def test_mandatory_failure_cannot_be_hidden(self) -> None:
        project = project_7m()
        project.requirements[1].value = 90
        check = verify_requirements(project, {"max_speed_kn": 34})
        self.assertFalse(check["mandatory_gate_passed"])
        self.assertIn("NÃO CONFORME", check["status"])

    def test_single_evaluation_has_traceability(self) -> None:
        result = evaluate_single(project_7m())
        self.assertIn("displacement", result.traceability)
        self.assertIn("calculation_id", result.traceability["displacement"])
        self.assertIn("algorithm_version", result.traceability["displacement"])

    def test_variants_use_same_pipeline_and_select_three(self) -> None:
        variants, selected = generate_and_select_variants(project_7m())
        self.assertEqual(len(variants), 9)
        ids = {
            selected["eco"].get("variant_id"),
            selected["balanced"].get("variant_id"),
            selected["performance"].get("variant_id"),
        }
        self.assertEqual(len(ids), 3)

    def test_public_portuguese_entry_point_is_json_serializable(self) -> None:
        result = avaliar_projeto(service_7m())
        self.assertEqual(result["project_id"], "NF-DEMO-SERVICE-7M")
        json.dumps(result)

    def test_all_demo_projects_pass_mandatory_gate(self) -> None:
        for factory in (service_7m, patrol_10m, rescue_12m):
            result = evaluate_single(Project.model_validate(factory()))
            self.assertTrue(result.requirements["mandatory_gate_passed"], factory.__name__)

    def test_full_evaluation_has_nine_variants(self) -> None:
        result = evaluate_project(project_7m(), include_variants=True)
        self.assertEqual(len(result.variants), 9)
        self.assertIn("eco", result.selected_alternatives)

    def test_report_bundle_contains_five_nonempty_files(self) -> None:
        project = project_7m()
        result = evaluate_project(project, include_variants=True)
        with tempfile.TemporaryDirectory() as directory:
            paths = generate_report_bundle(project, result, Path(directory))
            self.assertEqual({path.suffix for path in paths}, {".pdf", ".docx", ".xlsx", ".csv", ".json"})
            self.assertTrue(all(path.stat().st_size > 100 for path in paths))


if __name__ == "__main__":
    unittest.main()
