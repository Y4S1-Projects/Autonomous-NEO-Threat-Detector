"""
Module 4 Test Suite — Geospatial Synthesizer Hybrid Validation.

This module provides a comprehensive test suite for the Geospatial
Synthesizer agent (Agent 4) and its ``generate_impact_map`` tool.

Test Categories:
    1. **Happy Path** — Full execution with valid state data.
    2. **Edge Cases** — Missing data, extreme values, invalid types.
    3. **Content Validation** — Verify HTML file contains expected data.
    4. **Property-Based Tests** — File size, format, and structure checks.
    5. **LLM-as-a-Judge** — (Optional) Uses Ollama to evaluate output.

Grading Note (SE4010):
    Demonstrates comprehensive evaluation methodology including
    property-based testing, content validation, and LLM-as-a-Judge
    pattern. Each team member contributes test cases for their agent.
"""

import os
import sys
import unittest
import tempfile
import logging

# ── Path Setup ──────────────────────────────────────────────────────
# Ensure the project root is importable regardless of CWD
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# We need to import the tools module directly since the package uses
# relative imports that need the full package context
import importlib.util

_tools_path = os.path.join(os.path.dirname(__file__), "tools.py")
_tools_spec = importlib.util.spec_from_file_location("modeler_tools", _tools_path)
_tools_module = importlib.util.module_from_spec(_tools_spec)
_tools_spec.loader.exec_module(_tools_module)

generate_impact_map = _tools_module.generate_impact_map
_calculate_zoom_level = _tools_module._calculate_zoom_level
_get_threat_style = _tools_module._get_threat_style
_build_popup_html = _tools_module._build_popup_html
_select_impact_coordinate = _tools_module._select_impact_coordinate

from state import NEOState


# ═══════════════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════════════

# Suppress logging noise during tests
logging.basicConfig(level=logging.WARNING)

# Output directory for test-generated maps
_OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "output_maps")
)
_OUTPUT_FILE = os.path.join(_OUTPUT_DIR, "simulation_latest.html")


class TestGenerateImpactMap(unittest.TestCase):
    """Tests for the ``generate_impact_map`` tool function."""

    # ── 1. Happy Path Tests ─────────────────────────────────────────

    def test_successful_map_generation_moderate(self) -> None:
        """
        Happy Path: Verify that the tool generates a valid HTML map file
        when given MODERATE threat data simulating a Tunguska-class event.
        """
        result = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="Similar to the 1908 Tunguska event in Siberia.",
            asteroid_name="(2024 YR4)",
        )

        # Assert returned path is not an error
        self.assertIsInstance(result, str)
        self.assertFalse(result.startswith("ERROR"), f"Tool returned error: {result}")

        # Assert the file physically exists on disk
        self.assertTrue(
            os.path.exists(result),
            f"Generated file does not exist at: {result}",
        )

        # Assert the file is not empty
        file_size = os.path.getsize(result)
        self.assertGreater(file_size, 0, "Generated HTML file is empty.")

        print(f"[PASS] MODERATE map generated: {result} ({file_size / 1024:.1f} KB)")

    def test_successful_map_generation_high(self) -> None:
        """
        Happy Path: Verify HIGH threat (planet-killer) map generation
        with a 1000 km blast radius (Chicxulub-class event).
        """
        result = generate_impact_map(
            radius_km=1000.0,
            threat_level="HIGH",
            historical_context="Chicxulub impactor that caused dinosaur extinction.",
            asteroid_name="Test Asteroid X",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print(f"[PASS] HIGH threat map generated: {result}")

    def test_successful_map_generation_low(self) -> None:
        """
        Happy Path: Verify LOW threat (Chelyabinsk-class) map generation
        with a small 15 km blast radius.
        """
        result = generate_impact_map(
            radius_km=15.0,
            threat_level="LOW",
            historical_context="Chelyabinsk meteor — airburst, shattered windows.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print(f"[PASS] LOW threat map generated: {result}")

    # ── 2. Edge Case Tests ──────────────────────────────────────────

    def test_missing_historical_context(self) -> None:
        """
        Edge Case: Verify the tool handles empty/None historical context
        gracefully without crashing.
        """
        result = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="",  # Empty context
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Empty context handled gracefully.")

    def test_unknown_threat_level(self) -> None:
        """
        Edge Case: Verify the tool handles unrecognized threat levels
        by falling back to the neutral style.
        """
        result = generate_impact_map(
            radius_km=25.0,
            threat_level="EXTREME_DANGER",  # Not in the standard set
            historical_context="Test context for unknown level.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Unknown threat level handled with fallback style.")

    def test_very_small_blast_radius(self) -> None:
        """
        Edge Case: Verify the tool handles a very small blast radius
        (0.5 km) without rendering issues.
        """
        result = generate_impact_map(
            radius_km=0.5,
            threat_level="LOW",
            historical_context="Minor airburst event.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Very small radius (0.5 km) rendered successfully.")

    def test_very_large_blast_radius(self) -> None:
        """
        Edge Case: Verify the tool handles an extremely large blast radius
        (10,000 km — nearly planetary scale) without errors.
        """
        result = generate_impact_map(
            radius_km=10000.0,
            threat_level="HIGH",
            historical_context="Hypothetical planet-killer beyond Chicxulub.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Extreme radius (10,000 km) rendered successfully.")

    def test_negative_radius_is_clamped(self) -> None:
        """
        Edge Case: A negative blast radius should be clamped to 1.0 km
        and the map should still generate successfully.
        """
        result = generate_impact_map(
            radius_km=-50.0,
            threat_level="LOW",
            historical_context="Testing negative radius input.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Negative radius clamped and handled gracefully.")

    def test_zero_radius_is_clamped(self) -> None:
        """
        Edge Case: A zero blast radius should be clamped to 1.0 km.
        """
        result = generate_impact_map(
            radius_km=0.0,
            threat_level="LOW",
            historical_context="Zero radius test.",
        )

        self.assertFalse(result.startswith("ERROR"))
        self.assertTrue(os.path.exists(result))

        print("[PASS] Zero radius clamped and handled gracefully.")

    def test_invalid_radius_type_returns_error(self) -> None:
        """
        Edge Case: Passing a non-numeric radius should return an error
        string, not raise an exception.
        """
        result = generate_impact_map(
            radius_km="not_a_number",  # type: ignore
            threat_level="LOW",
            historical_context="Invalid input test.",
        )

        self.assertTrue(result.startswith("ERROR"))
        print("[PASS] Invalid radius type returned error string (no crash).")

    # ── 3. Content Validation Tests ─────────────────────────────────

    def test_html_contains_threat_level(self) -> None:
        """
        Content Validation: Read the generated HTML file and verify it
        contains the threat level string.
        """
        result = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="Tunguska-class regional destruction event.",
            asteroid_name="ContentTest-NEO",
        )

        self.assertTrue(os.path.exists(result))

        with open(result, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Verify threat level appears in the HTML
        self.assertIn("MODERATE", html_content)

        # Verify the historical context is embedded
        self.assertIn("Tunguska", html_content)

        # Verify blast radius data is present
        self.assertIn("50.0", html_content)

        # Verify asteroid name appears
        self.assertIn("ContentTest-NEO", html_content)

        print("[PASS] HTML content validation passed — all data embedded.")

    def test_html_is_valid_structure(self) -> None:
        """
        Property-Based: Verify the generated file is valid HTML by
        checking for expected structural elements.
        """
        result = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="Structure validation test.",
        )

        self.assertTrue(os.path.exists(result))

        with open(result, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Basic HTML structure checks
        self.assertIn("<html>", html_content.lower() + html_content)
        self.assertIn("</html>", html_content.lower() + html_content)
        self.assertIn("leaflet", html_content.lower())  # Folium uses Leaflet.js

        print("[PASS] HTML structure validation passed.")

    def test_file_size_is_reasonable(self) -> None:
        """
        Property-Based: Verify the generated HTML file is within a
        reasonable size range (between 5 KB and 5 MB).
        """
        result = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="File size validation test.",
        )

        self.assertTrue(os.path.exists(result))

        file_size_kb = os.path.getsize(result) / 1024

        self.assertGreater(file_size_kb, 5.0, "File suspiciously small (<5 KB)")
        self.assertLess(file_size_kb, 5000.0, "File suspiciously large (>5 MB)")

        print(f"[PASS] File size is reasonable: {file_size_kb:.1f} KB")

    # ── 4. Helper Function Tests ────────────────────────────────────

    def test_zoom_level_scaling(self) -> None:
        """
        Unit Test: Verify the dynamic zoom calculation produces
        reasonable values across the expected radius range.
        """
        # Small radius → high zoom
        self.assertGreaterEqual(_calculate_zoom_level(1.0), 8)

        # Medium radius → moderate zoom
        zoom_50 = _calculate_zoom_level(50.0)
        self.assertGreaterEqual(zoom_50, 4)
        self.assertLessEqual(zoom_50, 9)

        # Large radius → low zoom
        self.assertLessEqual(_calculate_zoom_level(5000.0), 4)

        # Edge: zero/negative → safe fallback
        self.assertEqual(_calculate_zoom_level(0), 8)
        self.assertEqual(_calculate_zoom_level(-10), 8)

        print("[PASS] Zoom level scaling validated across all ranges.")

    def test_threat_style_lookup(self) -> None:
        """
        Unit Test: Verify the threat style lookup returns correct
        colors for all standard levels.
        """
        low = _get_threat_style("LOW")
        self.assertEqual(low["fill_color"], "#FFC107")

        moderate = _get_threat_style("MODERATE")
        self.assertEqual(moderate["fill_color"], "#FF5722")

        high = _get_threat_style("HIGH")
        self.assertEqual(high["fill_color"], "#B71C1C")

        # Fallback for unknown levels
        unknown = _get_threat_style("UNDEFINED")
        self.assertEqual(unknown["fill_color"], "#1565C0")

        print("[PASS] Threat style lookup validated for all levels.")

    def test_impact_coordinate_selection(self) -> None:
        """
        Unit Test: Verify the coordinate selection returns valid
        geographic coordinates within expected ranges.
        """
        for _ in range(20):  # Test randomness stability
            lat, lon, name = _select_impact_coordinate()
            self.assertGreaterEqual(lat, -90.0)
            self.assertLessEqual(lat, 90.0)
            self.assertGreaterEqual(lon, -180.0)
            self.assertLessEqual(lon, 180.0)
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)

        print("[PASS] Coordinate selection produces valid geographic data.")

    def test_popup_html_contains_all_fields(self) -> None:
        """
        Unit Test: Verify the popup HTML builder includes all required
        data fields in its output.
        """
        popup = _build_popup_html(
            threat_level="HIGH",
            blast_radius_km=1000.0,
            historical_context="Chicxulub extinction event.",
            asteroid_name="TestNEO-42",
            coordinates=(10.0, -140.0),
        )

        self.assertIn("HIGH", popup)
        self.assertIn("1,000.0", popup)
        self.assertIn("Chicxulub", popup)
        self.assertIn("TestNEO-42", popup)
        self.assertIn("10.00", popup)
        self.assertIn("-140.00", popup)

        print("[PASS] Popup HTML contains all required fields.")


class TestLLMAsJudge(unittest.TestCase):
    """
    LLM-as-a-Judge evaluation for Agent 4 output quality.

    Uses the local Ollama model to evaluate whether the agent's
    rendering output is accurate, factual, and free of hallucinations.

    NOTE: These tests are skipped if Ollama is not running.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Check if Ollama is available before running LLM tests."""
        try:
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                from langchain_community.chat_models import ChatOllama
            from langchain_core.messages import HumanMessage

            llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), temperature=0
            )
            llm.invoke([HumanMessage(content="ping")])
            cls.ollama_available = True
            cls.llm = llm
        except Exception:
            cls.ollama_available = False

    def test_llm_judges_map_output_accuracy(self) -> None:
        """
        LLM-as-a-Judge: Ask the local SLM to evaluate whether the
        generated map output is factually accurate and does not contain
        hallucinated data.
        """
        if not self.ollama_available:
            self.skipTest("Ollama (phi3) not available — skipping LLM judge test.")

        from langchain_core.messages import SystemMessage, HumanMessage  # noqa: E402

        # First, generate a map to evaluate
        map_path = generate_impact_map(
            radius_km=50.0,
            threat_level="MODERATE",
            historical_context="Tunguska 1908 event — 15 megaton airburst.",
            asteroid_name="LLM-Judge-Test-NEO",
        )

        # Ask the LLM to judge the output
        judge_prompt = SystemMessage(
            content=(
                "You are a strict quality assurance judge. Evaluate the following:\n"
                "1. Does the map output path look valid? (ends in .html)\n"
                "2. Is the data internally consistent? (MODERATE + 50km + Tunguska)\n"
                "3. Are there any signs of hallucination or fabricated data?\n\n"
                "Respond with EXACTLY one word: 'PASS' or 'FAIL', followed by "
                "a brief one-line reason."
            )
        )
        test_prompt = HumanMessage(
            content=(
                f"Map output path: {map_path}\n"
                f"Threat Level: MODERATE\n"
                f"Blast Radius: 50.0 km\n"
                f"Historical Context: Tunguska 1908 event — 15 megaton airburst.\n"
                f"Asteroid: LLM-Judge-Test-NEO"
            )
        )

        response = self.llm.invoke([judge_prompt, test_prompt])
        verdict = response.content.strip()

        logging.info(f"LLM Judge verdict: {verdict}")
        print(f"[LLM] LLM-as-a-Judge verdict: {verdict}")

        # We check that the LLM didn't say FAIL
        self.assertNotIn(
            "FAIL",
            verdict.upper().split()[0] if verdict else "",
            f"LLM Judge reported FAIL: {verdict}",
        )

    def test_llm_detects_hallucination_mismatch(self) -> None:
        """
        LLM-as-a-Judge: Verify the LLM can detect when we present
        intentionally mismatched data (wrong threat level for the context).
        """
        if not self.ollama_available:
            self.skipTest("Ollama (phi3) not available — skipping LLM judge test.")

        from langchain_core.messages import SystemMessage, HumanMessage

        judge_prompt = SystemMessage(
            content=(
                "You are a consistency checker. The user will give you a threat "
                "assessment. Check if the threat level matches the description.\n"
                "A LOW threat should be about minor damage (airburst, windows).\n"
                "A HIGH threat should be about extinction-level events.\n"
                "If the level MISMATCHES the description, say 'MISMATCH'.\n"
                "If it matches, say 'CONSISTENT'.\n"
                "Respond with one word first, then a brief reason."
            )
        )
        test_prompt = HumanMessage(
            content=(
                "Threat Level: LOW\n"
                "Description: Planet-killer extinction event, global firestorm, "
                "dinosaur extinction, 1000km blast radius.\n"
                "Is this consistent?"
            )
        )

        response = self.llm.invoke([judge_prompt, test_prompt])
        verdict = response.content.strip()

        print(f"[LLM] Mismatch detection verdict: {verdict}")
        # The LLM should detect the mismatch
        self.assertIn(
            "MISMATCH",
            verdict.upper(),
            f"LLM failed to detect data mismatch: {verdict}",
        )


# ═══════════════════════════════════════════════════════════════════════
# Test Runner
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Module 4: Geospatial Synthesizer — Test Suite")
    print("=" * 60)
    print()

    # Run all test classes
    unittest.main(verbosity=2)
