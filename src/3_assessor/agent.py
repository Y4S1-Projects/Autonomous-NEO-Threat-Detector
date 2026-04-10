"""
Agent 3 — Semantic RAG Assessor Node for LangGraph Pipeline.

This module defines the LangGraph node function for the Semantic RAG
Assessor. It reads kinetic energy data from the physics results,
queries a local ChromaDB vector database for historical impact context,
and classifies the threat level.

Agent Persona:
    An AI memory retrieval specialist. Queries the historical impact
    database using semantic search and returns the closest factual
    match. Never fabricates historical data — only recalls from the
    embedded corpus.
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
from .tools import query_vector_memory


def run_rag_assessor_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Semantic RAG Assessor.

    Reads the kinetic energy, queries the local Vector Database,
    and appends the historical memory and threat level to the state.

    Args:
        state: The current NEOState with ``physics_results`` populated.

    Returns:
        NEOState: The updated state with ``threat_level``,
                  ``blast_radius_km``, and ``historical_match_context``.
    """
    logging.info("Agent 3 (RAG Assessor) activated.")
    agent_start = datetime.now(timezone.utc)

    physics_data = state.get("physics_results", {})

    if not physics_data or "error" in physics_data:
        logging.error("RAG Assessor aborted: Missing physics data.")
        state["threat_level"] = "UNKNOWN"
        state["historical_match_context"] = "Data missing due to upstream failure."
        state["errors"].append("Agent 3: Missing upstream physics data.")
        state["execution_metadata"]["agent_3_assessor"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_upstream",
        }
        return state

    energy = physics_data.get("kinetic_energy_joules")

    if energy is None:
        state["threat_level"] = "UNKNOWN"
        state["errors"].append("Agent 3: Missing kinetic energy value.")
        state["execution_metadata"]["agent_3_assessor"] = {
            "start": agent_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "status": "error_missing_energy",
        }
        return state

    # Execute the RAG Tool
    logging.info(f"Agent 3 querying memory for energy: {energy:e} Joules")
    rag_results = query_vector_memory(energy)

    # Update the Global State clipboard with the 3 new facts
    state["threat_level"] = rag_results["threat_level"]
    state["blast_radius_km"] = rag_results["blast_radius_km"]
    state["historical_match_context"] = rag_results["historical_match_context"]

    agent_end = datetime.now(timezone.utc)
    state["execution_metadata"]["agent_3_assessor"] = {
        "start": agent_start.isoformat(),
        "end": agent_end.isoformat(),
        "duration_seconds": (agent_end - agent_start).total_seconds(),
        "status": "success",
    }

    logging.info(
        f"Agent 3 finished. Threat classified as: {rag_results['threat_level']}"
    )
    return state
