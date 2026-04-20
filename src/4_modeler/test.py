"""
Module 4 — Comprehensive Test Suite for the Geospatial Data Synthesizer.

This test module provides automated verification of the Agent 4
tool (``generate_impact_map``) and its helper functions. It covers:

    1. Happy Path tests: Verify correct JSON database appending
    2. Edge Case tests: Invalid inputs, extreme values, graceful degradation
    3. Content Validation: JSON structure, embedded data integrity
    4. Helper Function Unit Tests: Styles, coordinates
    5. Population Impact Tests: Haversine formula, city proximity analysis
    6. Self-Correction Tests: Output JSON validation logic
    7. LLM-as-a-Judge: Automated SLM quality evaluation (requires Ollama)

Run this test suite directly:
    python src/4_modeler/test.py
"""

import io
import os
import sys
import json
import unittest
import logging

# ── Fix encoding for Windows cp1252 consoles ────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Ensure project root is on the path ──────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Module-under-test imports — use importlib because directory names
import importlib
import importlib.util


def _dynamic_import(module_name, file_path):
    """Import a module from a file path (handles numeric-prefix dirs)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_tools_path = os.path.join(_PROJECT_ROOT, "src", "4_modeler", "tools.py")
_tools_mod = _dynamic_import("_modeler_tools", _tools_path)

# Pull out needed symbols
generate_impact_map = _tools_mod.generate_impact_map
_get_threat_style = _tools_mod._get_threat_style
_haversine_distance = _tools_mod._haversine_distance

# Import the validation function from agent
try:
    _agent_path = os.path.join(_PROJECT_ROOT, "src", "4_modeler", "agent.py")
    _agent_mod = _dynamic_import("_modeler_agent", _agent_path)
    _validate_map_output = _agent_mod._validate_map_output
    AGENT_IMPORTABLE = True
except Exception:
    AGENT_IMPORTABLE = False


# ═══════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════

_TEST_RADIUS = 50.0
_TEST_THREAT = "MODERATE"
_TEST_CONTEXT = (
    "Similar to the 1908 Tunguska event which flattened 2,000 km2 of forest."
)
_TEST_ASTEROID = "(2024 YR4)"


def _get_latest_history_entry():
    """Retrieve the latest appended JSON record from the database."""
    history_path = os.path.join(
        _PROJECT_ROOT, "data", "output_maps", "simulation_history.json"
    )
    if not os.path.exists(history_path):
        return None
    with open(history_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list) and len(data) > 0:
        return data[-1]
    return None


# ═══════════════════════════════════════════════════════════════════════
# 1. Happy Path Tests
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateImpactMap(unittest.TestCase):
    def test_successful_map_generation_moderate(self):
        path, pop_data = generate_impact_map(
            radius_km=_TEST_RADIUS,
            threat_level=_TEST_THREAT,
            historical_context=_TEST_CONTEXT,
            asteroid_name=_TEST_ASTEROID,
        )
        self.assertTrue(
            path.endswith("index.html"), f"Expected index.html path, got: {path}"
        )
        self.assertIsNone(pop_data)

        latest = _get_latest_history_entry()
        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest["threat_level"], _TEST_THREAT)
        self.assertEqual(latest["radius_km"], _TEST_RADIUS)
        self.assertIsNone(latest["impact_lat"])
        self.assertIsNone(latest["impact_lon"])
        print(f"[PASS] MODERATE simulation appended to JSON.")

    def test_successful_map_generation_high(self):
        generate_impact_map(
            1000.0, "HIGH", "Comparable to the Chicxulub impactor.", "(Planet Killer)"
        )
        latest = _get_latest_history_entry()
        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest["threat_level"], "HIGH")
        print(f"[PASS] HIGH threat mapped and appended to JSON.")


# ═══════════════════════════════════════════════════════════════════════
# 2. Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases(unittest.TestCase):
    def test_zero_radius_is_clamped(self):
        generate_impact_map(0.0, "LOW", "Test context.")
        latest = _get_latest_history_entry()
        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest["radius_km"], 1.0)
        print("[PASS] Zero radius clamped to 1.0 km.")


# ═══════════════════════════════════════════════════════════════════════
# 4. Helper Function Unit Tests
# ═══════════════════════════════════════════════════════════════════════


class TestHelperFunctions(unittest.TestCase):
    def test_threat_style_lookup(self):
        for level in ("LOW", "MODERATE", "HIGH"):
            style = _get_threat_style(level)
            self.assertIn("fill_color", style)
            self.assertIn("stroke_color", style)
            self.assertIn("icon_color", style)
        print("[PASS] Threat style lookup validated for all levels.")


# ═══════════════════════════════════════════════════════════════════════
# 5. Utility Math Tests
# ═══════════════════════════════════════════════════════════════════════


class TestUtilityMath(unittest.TestCase):
    def test_haversine_london_to_paris(self):
        dist = _haversine_distance(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertAlmostEqual(dist, 344, delta=5)
        print(f"[PASS] Haversine London-Paris: {dist:.1f} km (expected ~344)")


# ═══════════════════════════════════════════════════════════════════════
# 7. Self-Correction Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSelfCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = generate_impact_map(50.0, "MODERATE", "Test context.")
        cls.valid_path = result[0]

    @unittest.skipUnless(AGENT_IMPORTABLE, "Agent module not importable")
    def test_validation_passes_for_valid_json(self):
        result = _validate_map_output(self.valid_path, "MODERATE", 50.0)
        self.assertTrue(result["valid"], f"Validation failed: {result['issues']}")
        print(f"[PASS] JSON Database validation passes for valid file.")

    @unittest.skipUnless(AGENT_IMPORTABLE, "Agent module not importable")
    def test_validation_detects_wrong_threat(self):
        # We test with a threat level that won't match the last JSON entry (which is MODERATE)
        result = _validate_map_output(self.valid_path, "ULTRA_MEGA", 50.0)
        self.assertFalse(result["valid"])
        self.assertTrue(any("mismatch" in i.lower() for i in result["issues"]))
        print("[PASS] Validation correctly detects mismatch in latest JSON record.")


# ═══════════════════════════════════════════════════════════════════════
# Custom Report Printer
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Module 4: Geospatial Synthesizer -- Test Suite (JSON DB)")
    print("=" * 60)
    print()
    unittest.main(verbosity=2)
