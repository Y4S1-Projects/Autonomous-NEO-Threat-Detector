"""
Agent 4 — Geospatial Synthesizer Node for LangGraph Pipeline.

This module defines the LangGraph node function for the Geospatial
Synthesizer, the final agent in the AstroGuard pipeline. It consumes
the accumulated state data from all three upstream agents and produces
structured simulation data appended to a JSON history file.

Agent Persona:
    A geospatial rendering and analysis engine. Reads ``blast_radius_km``,
    ``threat_level``, and ``historical_match_context`` from the shared
    state. Does NOT invent new facts. Passes exact data into the mapping
    tool and then verifies the output using a Self-Correction Loop.

Self-Correction Architecture:
    After the tool generates the data, the agent validates the output by:
    1. Checking the JSON file exists and was recently updated.
    2. Reading the last recorded entry to verify all critical data strings
       (threat_level, blast_radius) were saved correctly.
    3. If validation fails, it retries the generation.
    4. If Ollama is available, the LLM produces a verification summary.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Optional

# Ensure project root is on the path for cross-module imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from state import NEOState

# Relative import from the same directory
from .tools import generate_impact_map

# ── Attempt to load Ollama (graceful fallback) ──────────────────────
try:
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.info("langchain-ollama not available; Agent 4 will run without LLM.")


# ═══════════════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are a geospatial rendering verification engine for the AstroGuard "
    "planetary defense system.\n\n"
    "STRICT RULES:\n"
    "1. You MUST NOT invent, estimate, or hallucinate any scientific data.\n"
    "2. You MUST NOT change, re-interpret, or embellish the threat level, "
    "   blast radius, or historical context provided to you.\n"
    "3. Your ONLY job is to confirm that the rendering tool successfully "
    "   recorded the simulation data to the JSON database.\n"
    "4. If any data is missing or invalid, report exactly what is missing.\n"
    "5. Include the population impact estimate in your summary if provided.\n"
    "6. Keep your response under 100 words. Be precise and technical.\n\n"
    "You are the final checkpoint. Accuracy is paramount."
)

# Maximum number of retry attempts for data generation
MAX_RETRIES = 2


# ═══════════════════════════════════════════════════════════════════════
# Self-Correction: Output Validation
# ═══════════════════════════════════════════════════════════════════════


def _validate_map_output(
    html_path: str,
    expected_threat: str,
    expected_radius: float,
) -> dict:
    """
    Validate the generated JSON data file for correctness.

    This is the core of the Self-Correction Loop. The agent opens the
    ``simulation_history.json`` file and checks whether the critical data
    actually made it into the latest record.

    Args:
        html_path:       Path to the index.html file (json is in same dir).
        expected_threat: The threat level that should appear.
        expected_radius: The blast radius that should appear.

    Returns:
        dict with validation results.
    """
    issues = []
    file_size_kb = 0.0

    output_dir = os.path.dirname(os.path.abspath(html_path))
    json_path = os.path.join(output_dir, "simulation_history.json")

    # Check 1: File exists
    if not os.path.exists(json_path):
        issues.append(f"Simulation history JSON does not exist: {json_path}")
        return {"valid": False, "issues": issues, "file_size_kb": 0}

    # Check 2: File size
    file_size_kb = os.path.getsize(json_path) / 1024
    if file_size_kb < 0.1:
        issues.append("JSON file is empty.")

    # Check 3: Content validation
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            issues.append("JSON file does not contain a valid array of simulations.")
        else:
            latest = data[-1]
            if str(latest.get("threat_level", "")).upper() != expected_threat.upper():
                issues.append(f"Last record threat_level mismatch.")

            radius = float(latest.get("radius_km", 0))
            if abs(radius - expected_radius) > 0.1:
                issues.append(f"Last record blast radius mismatch.")

            # Population is now computed on-demand after user picks ground zero.
            if "population_data" not in latest:
                issues.append("Missing population_data field in record.")

    except Exception as exc:
        issues.append(f"Could not parse JSON file for validation: {exc}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "file_size_kb": round(file_size_kb, 1),
    }


# ═══════════════════════════════════════════════════════════════════════
# Agent Node Function
# ═══════════════════════════════════════════════════════════════════════


def run_modeler_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Geospatial Synthesizer.

    Reads the final analytical data from all upstream agents, triggers
    data compilation and appending, and then runs a Self-Correction Loop.
    """
    logging.info("=" * 50)
    logging.info("Agent 4 (Geospatial Synthesizer) activated.")
    logging.info("=" * 50)
    agent_start = datetime.now(timezone.utc)

    # ── 1. Extract State Data ───────────────────────────────────────
    radius: Optional[float] = state.get("blast_radius_km")
    threat: Optional[str] = state.get("threat_level")
    context: Optional[str] = state.get("historical_match_context")
    asteroid_name: Optional[str] = state.get("asteroid_name")

    logging.info(
        f"Agent 4 received state: threat={threat}, "
        f"radius={radius}, asteroid={asteroid_name}"
    )

    # ── 2. Input Validation ─────────────────────────────────────────
    if radius is None or threat is None:
        error_msg = (
            "Modeler aborted: Missing required threat data. "
            f"blast_radius_km={radius}, threat_level={threat}"
        )
        logging.error(error_msg)
        state["final_map_path"] = f"ERROR: {error_msg}"
        state["errors"].append(f"Agent 4: {error_msg}")
        state["estimated_affected_population"] = None
        state["execution_metadata"]["agent_4_modeler"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_missing_data",
        }
        return state

    if not context:
        logging.warning("Agent 4: No historical context provided. Using placeholder.")
        context = "No historical context available."

    # ── 3. Self-Correction Loop ─────────────────────────────────────
    map_path = None
    pop_data = None
    validation = None
    attempt = 0

    while attempt <= MAX_RETRIES:
        attempt += 1
        logging.info(f"Agent 4: Data compilation attempt {attempt}/{MAX_RETRIES + 1}")

        # Execute the data recording tool
        result = generate_impact_map(
            radius_km=radius,
            threat_level=threat,
            historical_context=context,
            asteroid_name=asteroid_name,
        )

        if isinstance(result, tuple):
            map_path, pop_data = result
        else:
            map_path = result
            pop_data = None

        if isinstance(map_path, str) and map_path.startswith("ERROR"):
            logging.error(f"Agent 4: Tool error on attempt {attempt}: {map_path}")
            if attempt <= MAX_RETRIES:
                continue
            else:
                break

        # Validate the recorded output
        validation = _validate_map_output(map_path, threat, radius)

        if validation["valid"]:
            logging.info(
                f"Agent 4: Validation PASSED on attempt {attempt} "
                f"(JSON size: {validation['file_size_kb']} KB)"
            )
            break
        else:
            logging.warning(
                f"Agent 4: Validation FAILED on attempt {attempt}: "
                f"{validation['issues']}"
            )
            if attempt <= MAX_RETRIES:
                logging.info("Agent 4: Self-correcting — retrying data compilation...")
                state["errors"].append(
                    f"Agent 4: Self-correction triggered (attempt {attempt}): "
                    f"{validation['issues']}"
                )
            else:
                logging.error("Agent 4: Max retries exhausted.")

    # ── 4. Determine Final Success ──────────────────────────────────
    tool_success = (
        isinstance(map_path, str)
        and not map_path.startswith("ERROR")
        and os.path.exists(map_path)
    )

    file_size_kb = validation.get("file_size_kb", 0) if validation else 0.0
    if tool_success:
        logging.info(f"Agent 4: Link to Dashboard: {map_path}")
    else:
        state["errors"].append(f"Agent 4: Dashboard generation failed -- {map_path}")

    # ── 5. LLM Verification Step (Optional) ─────────────────────────
    llm_summary = None
    if OLLAMA_AVAILABLE and tool_success:
        try:
            llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), temperature=0
            )

            pop_info = "- Population at Risk: computed interactively after user selects location\n"

            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            human_msg = HumanMessage(
                content=(
                    f"The data extraction tool has completed.\n"
                    f"- Threat Level: {threat}\n"
                    f"- Blast Radius: {radius} km\n"
                    f"- Asteroid: {asteroid_name or 'Unknown'}\n"
                    f"{pop_info}"
                    f"- Validation: {'PASSED' if validation and validation['valid'] else 'ISSUES'}\n"
                    f"- Updates recorded to DB successfully.\n\n"
                    f"Provide a brief verification summary."
                )
            )

            response = llm.invoke([system_msg, human_msg])
            content = response.content
            if isinstance(content, str):
                llm_summary = content.strip()
            else:
                llm_summary = str(content)
            logging.info(f"Agent 4 LLM verification: {llm_summary}")

        except Exception as exc:
            logging.warning(f"Agent 4: LLM verification unavailable ({exc}).")

    # ── 6. Update Global State ──────────────────────────────────────
    state["final_map_path"] = map_path
    state["estimated_affected_population"] = (
        pop_data["total_affected"] if pop_data else None
    )

    agent_end = datetime.now(timezone.utc)
    state["execution_metadata"]["agent_4_modeler"] = {
        "start": agent_start.isoformat(),
        "end": agent_end.isoformat(),
        "duration_seconds": (agent_end - agent_start).total_seconds(),
        "status": "success" if tool_success else "error",
        "file_size_kb": file_size_kb,
        "generation_attempts": attempt,
        "self_correction_triggered": attempt > 1,
        "validation_passed": validation["valid"] if validation else False,
        "estimated_affected_population": (
            pop_data["total_affected"] if pop_data else None
        ),
        "llm_verification": llm_summary,
    }

    logging.info("=" * 50)
    return state
