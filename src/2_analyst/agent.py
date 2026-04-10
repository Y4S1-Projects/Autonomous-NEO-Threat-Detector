"""
Agent 2 — Trajectory Analyst Node for LangGraph Pipeline.

This module defines the LangGraph node function for the Trajectory Analyst
agent. It extracts numerical data from the raw API JSON, computes
kinetic energy via the physics engine tool, and writes computed
results back into the shared NEOState.

Agent Persona:
    A deterministic physics computation engine. Extracts raw values,
    applies first-principles mathematics, and passes results downstream.
    Never guesses or estimates — only computes from given data.
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Ensure project root is on the path for cross-module imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from state import NEOState

# Relative import from the same directory
from .tools import calculate_kinetic_energy


def run_analyst_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Trajectory Analyst.

    Extracts numerical data from the raw API JSON and passes it
    into the deterministic physics engine.

    Args:
        state: The current NEOState with ``raw_api_data`` populated.

    Returns:
        NEOState: The updated state with ``physics_results`` populated.
    """
    logging.info("Agent 2 (Trajectory Analyst) activated.")
    agent_start = datetime.now(timezone.utc)

    raw_data = state.get("raw_api_data", {})

    # Defensive check: Ensure Agent 1 didn't pass an error
    if not raw_data or "error" in raw_data:
        logging.error("Analyst aborted: Invalid raw data received.")
        state["physics_results"] = {"error": "Missing telemetry data."}
        state["errors"].append("Agent 2: Missing upstream telemetry data.")
        state["execution_metadata"]["agent_2_analyst"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_upstream",
        }
        return state

    diameter = raw_data.get("estimated_diameter_meters")
    velocity = raw_data.get("relative_velocity_kms")

    if diameter is None or velocity is None:
        state["physics_results"] = {"error": "Missing dimensional data."}
        state["errors"].append("Agent 2: Missing diameter or velocity data.")
        state["execution_metadata"]["agent_2_analyst"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_missing_fields",
        }
        return state

    # Execute the custom tool
    logging.info(f"Agent 2 parsing: Diameter={diameter}m, Velocity={velocity}km/s")
    physics_output = calculate_kinetic_energy(diameter, velocity)

    # Update the Global State clipboard
    state["physics_results"] = physics_output

    if "error" in physics_output:
        state["errors"].append("Agent 2: Physics calculation failed.")

    agent_end = datetime.now(timezone.utc)
    state["execution_metadata"]["agent_2_analyst"] = {
        "start": agent_start.isoformat(),
        "end": agent_end.isoformat(),
        "duration_seconds": (agent_end - agent_start).total_seconds(),
        "status": "error" if "error" in physics_output else "success",
    }

    logging.info("Agent 2 finished. State updated.")
    return state
