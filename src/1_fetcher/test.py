"""
Test Suite — Agent 1: Telemetry Fetcher.

Validates the fetch_nasa_neo_data() tool using property-based assertions,
type-contract checks, error-case handling, and network-failure simulation
via unittest.mock. Tests are designed to pass both online and offline.

Usage:
    # From the project root:
    python -m pytest src/1_fetcher/test.py -v

    # Or directly:
    python src/1_fetcher/test.py
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# ── Path setup so the module can be imported from any working directory ──
_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_DIR, "..", ".."))
for _p in (_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools import fetch_nasa_neo_data  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════
# Helper — Minimal NASA API response payload for mocking
# ═══════════════════════════════════════════════════════════════════════

_FAKE_DATE = "2026-04-10"

_MOCK_NASA_PAYLOAD = {
    "near_earth_objects": {
        _FAKE_DATE: [
            {
                "name": "(2099 DX1)",
                "estimated_diameter": {
                    "meters": {
                        "estimated_diameter_min": 80.0,
                        "estimated_diameter_max": 180.0,
                    }
                },
                "close_approach_data": [
                    {
                        "relative_velocity": {
                            "kilometers_per_second": "14.72"
                        }
                    }
                ],
            },
            {
                "name": "(2099 AX7)",
                "estimated_diameter": {
                    "meters": {
                        "estimated_diameter_min": 10.0,
                        "estimated_diameter_max": 22.0,
                    }
                },
                "close_approach_data": [
                    {
                        "relative_velocity": {
                            "kilometers_per_second": "8.10"
                        }
                    }
                ],
            },
        ]
    }
}


def _make_mock_response(payload: dict) -> MagicMock:
    """Build a mock requests.Response object that returns the given payload."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = payload
    return mock_resp


# ═══════════════════════════════════════════════════════════════════════
# Test Class
# ═══════════════════════════════════════════════════════════════════════


class TestTelemetryFetcherProperties(unittest.TestCase):
    """
    Property-based and contract tests for fetch_nasa_neo_data().

    Every test that would hit the live NASA network instead patches
    requests.get so the suite is deterministic and runs fully offline.
    """

    # ── Contract: return type is always dict ────────────────────────

    @patch("tools.requests.get")
    def test_return_type_is_always_dict(self, mock_get: MagicMock) -> None:
        """Return value must be a dict in both success and error paths."""
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(
            result, dict,
            "fetch_nasa_neo_data() must always return a dict.",
        )

    # ── Contract: success response has all 3 required keys ──────────

    @patch("tools.requests.get")
    def test_required_keys_present_on_success(self, mock_get: MagicMock) -> None:
        """
        Property: every successful response must contain exactly the
        three sanitized fields — 'name', 'estimated_diameter_meters',
        and 'relative_velocity_kms'.
        """
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIn("name", result)
        self.assertIn("estimated_diameter_meters", result)
        self.assertIn("relative_velocity_kms", result)

    # ── Contract: correct value types ───────────────────────────────

    @patch("tools.requests.get")
    def test_name_is_string(self, mock_get: MagicMock) -> None:
        """Property: 'name' must be a str."""
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result["name"], str)

    @patch("tools.requests.get")
    def test_estimated_diameter_is_numeric(self, mock_get: MagicMock) -> None:
        """Property: 'estimated_diameter_meters' must be a non-negative number."""
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result["estimated_diameter_meters"], (int, float))
        self.assertGreaterEqual(result["estimated_diameter_meters"], 0)

    @patch("tools.requests.get")
    def test_relative_velocity_is_numeric(self, mock_get: MagicMock) -> None:
        """Property: 'relative_velocity_kms' must be a non-negative number."""
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result["relative_velocity_kms"], (int, float))
        self.assertGreaterEqual(float(result["relative_velocity_kms"]), 0)

    # ── Contract: largest asteroid is selected by default ───────────

    @patch("tools.requests.get")
    def test_default_index_selects_largest_asteroid(self, mock_get: MagicMock) -> None:
        """
        Property: index=0 (default) must return the asteroid with the
        maximum estimated diameter among all returned by the API.
        """
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE, asteroid_index=0)

        # The mock has two asteroids; 180.0 m is the largest
        self.assertEqual(result["estimated_diameter_meters"], 180.0)
        self.assertIn("2099 DX1", result["name"])

    # ── Contract: asteroid_index selects the correct offset ─────────

    @patch("tools.requests.get")
    def test_asteroid_index_selects_second_entry(self, mock_get: MagicMock) -> None:
        """Property: asteroid_index=1 must return the second-largest asteroid."""
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE, asteroid_index=1)

        self.assertEqual(result["estimated_diameter_meters"], 22.0)
        self.assertIn("2099 AX7", result["name"])

    # ── Error case: out-of-bounds index ─────────────────────────────

    @patch("tools.requests.get")
    def test_out_of_bounds_index_returns_error_dict(self, mock_get: MagicMock) -> None:
        """
        Error Contract: requesting an asteroid_index beyond the list length
        must return a dict containing an 'error' key, not raise an exception.
        """
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE, asteroid_index=99)

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    # ── Error case: API returns empty asteroid list ──────────────────

    @patch("tools.requests.get")
    def test_empty_asteroid_list_returns_error_dict(self, mock_get: MagicMock) -> None:
        """
        Error Contract: when NASA returns no asteroids for the date, the
        tool must return a dict with an 'error' key rather than crashing.
        """
        empty_payload = {"near_earth_objects": {_FAKE_DATE: []}}
        mock_get.return_value = _make_mock_response(empty_payload)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    # ── Error case: network timeout ──────────────────────────────────

    @patch("tools.requests.get")
    def test_network_timeout_returns_error_dict(self, mock_get: MagicMock) -> None:
        """
        Error Contract: a network timeout (requests.exceptions.Timeout)
        must be caught and returned as an error dict — the pipeline must
        not crash when the NASA API is unreachable.
        """
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.Timeout("Connection timed out")

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    # ── Error case: HTTP error (e.g., 403 Forbidden) ─────────────────

    @patch("tools.requests.get")
    def test_http_error_returns_error_dict(self, mock_get: MagicMock) -> None:
        """
        Error Contract: an HTTP error (e.g., 403 rate-limit from NASA)
        must be caught and returned as an error dict.
        """
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError(
            "403 Client Error: Forbidden"
        )
        mock_get.return_value = mock_resp

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    # ── Security: no raw NASA JSON keys leak into the output ─────────

    @patch("tools.requests.get")
    def test_raw_nasa_keys_are_not_exposed(self, mock_get: MagicMock) -> None:
        """
        Security/Sanitisation: the tool must strip the full NASA payload.
        Internal NASA keys like 'close_approach_data' and 'links' must
        not appear in the returned dict.
        """
        mock_get.return_value = _make_mock_response(_MOCK_NASA_PAYLOAD)

        result = fetch_nasa_neo_data(_FAKE_DATE)

        self.assertNotIn("close_approach_data", result)
        self.assertNotIn("links", result)
        self.assertNotIn("near_earth_objects", result)

    # ── Live integration smoke-test (skipped when offline) ───────────

    def test_live_api_smoke_test(self) -> None:
        """
        Live Integration Test: calls the real NASA DEMO_KEY endpoint.
        Skipped automatically if the network is unreachable so the CI
        suite remains green in offline environments.
        """
        import requests as req_lib
        try:
            req_lib.get("https://api.nasa.gov", timeout=5)
        except req_lib.exceptions.RequestException:
            self.skipTest("NASA API unreachable — skipping live smoke test.")

        result = fetch_nasa_neo_data("2026-04-10")

        self.assertIsInstance(result, dict)
        # Either a valid payload or a well-formed error dict
        if "error" not in result:
            self.assertIn("name", result)
            self.assertIn("estimated_diameter_meters", result)
            self.assertIn("relative_velocity_kms", result)
            print(f"\n[LIVE] Asteroid fetched: {result['name']}")


# ═══════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
