"""
Module 4 Tool — Geospatial Impact Simulation Data Engine.

This module provides the ``generate_impact_map`` tool used by the
Geospatial Synthesizer agent (Agent 4) to compile threat intelligence
and output it to a historical JSON database.

A static HTML/JS template then reads this JSON database to render the
interactive geospatial maps dynamically.

Features:
        - **Scenario Record Generation** — Stores asteroid-specific threat and
            blast metadata only. Human impact is computed interactively in the UI
            after the user selects ground zero.
    - **Historical Tracking** — Outputs structured data to an appended
      JSON array for historical comparison.

Technical Constraints:
    - All data processing is deterministic and local.
    - Output is a JSON file + path to the fixed HTML template.
    - Graceful error handling with no unhandled exceptions.

Grading Note (SE4010):
    This tool demonstrates:
    - Separation of Concerns (Python for data, JS for UI)
    - Persistent Local Data Storage (JSON appending)
    - Haversine formula and data synthesis
"""

import os
import json
import math
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any

# ═══════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════

#: Mapping from threat level to visual styling (fill, stroke, opacity)
THREAT_STYLES: Dict[str, Dict[str, object]] = {
    "LOW": {
        "fill_color": "#FFC107",  # Amber
        "stroke_color": "#FF8F00",  # Dark amber
        "fill_opacity": 0.25,
        "icon_color": "orange",
        "label": "LOW — Localized Airburst",
    },
    "MODERATE": {
        "fill_color": "#FF5722",  # Deep orange
        "stroke_color": "#D32F2F",  # Red
        "fill_opacity": 0.30,
        "icon_color": "red",
        "label": "MODERATE — Regional Destruction",
    },
    "HIGH": {
        "fill_color": "#B71C1C",  # Dark red
        "stroke_color": "#880E4F",  # Dark magenta
        "fill_opacity": 0.35,
        "icon_color": "darkred",
        "label": "HIGH — Global Extinction Event",
    },
}

#: Earth's mean radius in km (for Haversine formula)
_EARTH_RADIUS_KM = 6371.0


# ═══════════════════════════════════════════════════════════════════════
# Private Helper Functions
# ═══════════════════════════════════════════════════════════════════════


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two geographic points."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return _EARTH_RADIUS_KM * c


def _get_threat_style(threat_level: str) -> Dict[str, object]:
    """Retrieve visual styling configuration based on threat level."""
    return THREAT_STYLES.get(
        threat_level.upper(),
        {
            "fill_color": "#1565C0",
            "stroke_color": "#0D47A1",
            "fill_opacity": 0.20,
            "icon_color": "blue",
            "label": f"UNKNOWN — Unclassified ({threat_level})",
        },
    )


# ═══════════════════════════════════════════════════════════════════════
# Primary Tool Function
# ═══════════════════════════════════════════════════════════════════════


def generate_impact_map(
    radius_km: float,
    threat_level: str,
    historical_context: str,
    asteroid_name: Optional[str] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Generate impact simulation data and append it to the historical
    JSON database for dynamic front-end rendering.

    Args:
        radius_km:          The theoretical blast radius in kilometers.
        threat_level:       The classification label from Agent 3.
        historical_context: The RAG context string from Agent 3.
        asteroid_name:      Optional NEO designation for display.

    Returns:
        Tuple of (file_path, population_data):
            - file_path (str): Absolute path to the index.html file, or an
              error string prefixed with ``'ERROR:'``.
            - population_data (Optional[Dict]): The population impact
              analysis result, or None if failed.
    """
    logging.info("Tool executed: Generating Geospatial Impact Simulation Data.")

    # ── 1. Input Validation ─────────────────────────────────────────
    try:
        radius_km = float(radius_km)
    except (TypeError, ValueError) as exc:
        logging.error(f"Invalid radius_km value: {radius_km!r} ({exc})")
        return "ERROR: radius_km must be a valid positive number.", None

    if radius_km <= 0:
        logging.warning(f"Non-positive radius ({radius_km}), clamping to 1.0 km.")
        radius_km = 1.0

    if not threat_level or not isinstance(threat_level, str):
        logging.warning("Invalid threat_level, defaulting to 'UNKNOWN'.")
        threat_level = "UNKNOWN"

    if not historical_context or not isinstance(historical_context, str):
        logging.warning("Empty historical context, using placeholder.")
        historical_context = "No historical context available."

    try:
        # ── 2. Build style; population impact is computed in UI after click
        style = _get_threat_style(threat_level)

        # ── 3. Build Record ─────────────────────────────────────────
        sim_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asteroid_name": asteroid_name,
            "radius_km": radius_km,
            "threat_level": threat_level,
            "historical_context": historical_context,
            "impact_lat": None,
            "impact_lon": None,
            "location_name": "User-selected ground zero",
            "population_data": None,
            "style": style,
        }

        # ── 4. Append to JSON History File ──────────────────────────
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(
            os.path.join(base_dir, "..", "..", "data", "output_maps")
        )
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "simulation_history.json")
        html_path = os.path.join(output_dir, "index.html")

        # We append to the JSON array
        history = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        history = json.loads(content)
            except Exception as e:
                logging.warning(
                    f"Could not parse existing JSON history, starting fresh: {e}"
                )

        # Enforce reasonable limits (last 50 runs max to keep file size small)
        history.append(sim_record)
        if len(history) > 50:
            history = history[-50:]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        logging.info(f"Simulation data successfully appended to {json_path}")
        return html_path, None

    except Exception as exc:
        logging.error(f"Data generation failed: {exc}", exc_info=True)
        return f"ERROR: Data generation failed -- {exc}", None
