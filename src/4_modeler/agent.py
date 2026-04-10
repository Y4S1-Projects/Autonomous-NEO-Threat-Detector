"""
Agent 4 — Geospatial Synthesizer Node for LangGraph Pipeline.

This module defines the LangGraph node function for the Geospatial
Synthesizer, the final agent in the AstroGuard pipeline. It consumes
the accumulated state data from all three upstream agents and produces
an interactive Folium HTML map as the pipeline's visual artifact.

Agent Persona:
    A geospatial rendering engine. Reads the ``blast_radius_km``,
    ``threat_level``, and ``historical_match_context`` from the
    shared state. Does NOT invent new facts, estimate values, or
    reinterpret upstream data. Passes the exact data into the
    mapping tool to generate the final output.

LLM Integration Strategy:
    The local SLM (Ollama/phi3) is used in a verification role:
    after the deterministic tool generates the map, the LLM
    produces a brief, factual summary of what was rendered.
    If Ollama is unavailable, the agent degrades gracefully
    and only uses the deterministic tool.
"""

import os
import sys
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
    "3. Your ONLY job is to confirm that the rendering tool produced a valid "
    "   output file and provide a brief, factual summary.\n"
    "4. If any data is missing or invalid, report exactly what is missing.\n"
    "5. Keep your response under 100 words. Be precise and technical.\n\n"
    "You are the final checkpoint. Accuracy is paramount."
)


# ═══════════════════════════════════════════════════════════════════════
# Agent Node Function
# ═══════════════════════════════════════════════════════════════════════


def run_modeler_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Geospatial Synthesizer.

    Reads the final analytical data from all upstream agents in the
    state, validates the data, triggers the mapping tool to create
    the visual artifact, and optionally uses the local LLM to verify
    the output.

    **Workflow:**

    1. Extract ``blast_radius_km``, ``threat_level``, and
       ``historical_match_context`` from the shared NEOState.
    2. Validate that all required fields are present and reasonable.
    3. Invoke ``generate_impact_map()`` to render the Folium HTML map.
    4. (If Ollama available) Ask the LLM to verify and summarize
       the rendered output.
    5. Update ``final_map_path`` in the state and record execution
       metadata for observability.

    Args:
        state: The current NEOState with upstream fields populated
               by agents 1–3.

    Returns:
        NEOState: The final state with ``final_map_path`` populated.
                  On failure, ``final_map_path`` contains an error
                  description and the error is appended to
                  ``state['errors']``.
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
        state["execution_metadata"]["agent_4_modeler"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_missing_data",
        }
        return state

    # Warn but don't abort on missing context
    if not context:
        logging.warning("Agent 4: No historical context provided. Using placeholder.")
        context = (
            "No historical context available. Upstream RAG retrieval may have failed."
        )

    # ── 3. Execute the Rendering Tool ───────────────────────────────
    logging.info(
        f"Agent 4 rendering map: {threat} threat, "
        f"{radius} km radius, asteroid={asteroid_name}"
    )

    map_path = generate_impact_map(
        radius_km=radius,
        threat_level=threat,
        historical_context=context,
        asteroid_name=asteroid_name,
    )

    # ── 4. Validate Tool Output ─────────────────────────────────────
    tool_success = (
        isinstance(map_path, str)
        and not map_path.startswith("ERROR")
        and os.path.exists(map_path)
    )

    if tool_success:
        logging.info(f"Agent 4: Map file generated successfully at {map_path}")
        file_size_kb = os.path.getsize(map_path) / 1024
        logging.info(f"Agent 4: File size = {file_size_kb:.1f} KB")
    else:
        logging.error(f"Agent 4: Map generation failed. Result: {map_path}")
        state["errors"].append(f"Agent 4: Map generation failed — {map_path}")

    # ── 5. LLM Verification Step (Optional) ─────────────────────────
    llm_summary = None
    if OLLAMA_AVAILABLE and tool_success:
        try:
            llm = ChatOllama(model="phi3", temperature=0)

            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            human_msg = HumanMessage(
                content=(
                    f"The mapping tool has completed. Here is the rendering report:\n"
                    f"- Threat Level: {threat}\n"
                    f"- Blast Radius: {radius} km\n"
                    f"- Asteroid: {asteroid_name or 'Unknown'}\n"
                    f"- Historical Context: {context[:200]}\n"
                    f"- Output File: {map_path}\n"
                    f"- File Size: {file_size_kb:.1f} KB\n\n"
                    f"Provide a brief verification summary."
                )
            )

            response = llm.invoke([system_msg, human_msg])
            llm_summary = response.content.strip()
            logging.info(f"Agent 4 LLM verification: {llm_summary}")

        except Exception as exc:
            logging.warning(
                f"Agent 4: LLM verification unavailable ({exc}). "
                "Continuing with tool output only."
            )

    # ── 6. Update Global State ──────────────────────────────────────
    state["final_map_path"] = map_path

    agent_end = datetime.now(timezone.utc)
    state["execution_metadata"]["agent_4_modeler"] = {
        "start": agent_start.isoformat(),
        "end": agent_end.isoformat(),
        "duration_seconds": (agent_end - agent_start).total_seconds(),
        "status": "success" if tool_success else "error",
        "file_size_kb": round(file_size_kb, 1) if tool_success else None,
        "llm_verification": llm_summary,
    }

    logging.info("Agent 4 finished. Pipeline complete.")
    logging.info("=" * 50)
    return state
