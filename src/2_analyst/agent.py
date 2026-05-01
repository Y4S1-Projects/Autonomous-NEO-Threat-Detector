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

# Attempt to load Ollama (graceful fallback if not installed)
try:
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def run_analyst_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Trajectory Analyst.

    Leverages an LLM agent capable of invoking the calculate_kinetic_energy
    tool to parse and act on telemetry data.

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

    physics_output = {}

    # ── Agentic Framework Implementation (LLM + Tool Calling) ───────
    if OLLAMA_AVAILABLE:
        try:
            llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), temperature=0.0
            )
            # Bind the custom physics tool to the LLM
            llm_with_tools = llm.bind_tools([calculate_kinetic_energy])

            system_msg = SystemMessage(
                content=(
                    "You are a highly analytical Trajectory Physics Engine.\n"
                    "Your responsibility is to compute the mass and kinetic energy of an incoming asteroid.\n"
                    "You MUST use your provided tool 'calculate_kinetic_energy' to calculate these values.\n"
                    "Never guess or make up values. Execute the tool given the diameter and velocity."
                )
            )

            human_msg = HumanMessage(
                content=f"An incoming asteroid has a diameter of {diameter} meters and is traveling at {velocity} km/s. Calculate its kinetic properties."
            )

            logging.info("Agent 2 (LLM): Reasoning about incoming trajectory data...")
            ai_msg = llm_with_tools.invoke([system_msg, human_msg])

            # Check if LLM successfully decided to use the tool
            if ai_msg.tool_calls:
                logging.info(
                    f"Agent 2 (LLM) chose to execute tool: {ai_msg.tool_calls[0]['name']}"
                )
                tool_args = ai_msg.tool_calls[0]["args"]
                # Invoke the Langchain tool wrapper natively
                physics_output = calculate_kinetic_energy.invoke(tool_args)
            else:
                logging.warning(
                    "Agent 2 (LLM) failed to invoke the tool. Falling back to direct execution."
                )
                physics_output = calculate_kinetic_energy.invoke(
                    {"diameter_meters": float(diameter), "velocity_kms": float(velocity)}
                )

        except Exception as e:
            logging.error(f"Agent 2 LLM failed ({e}), fallback to manual execution.")
            physics_output = calculate_kinetic_energy.invoke(
                {"diameter_meters": float(diameter), "velocity_kms": float(velocity)}
            )
    else:
        logging.info("Agent 2: Ollama not available, bypassing LLM logic.")
        physics_output = calculate_kinetic_energy.invoke(
            {"diameter_meters": float(diameter), "velocity_kms": float(velocity)}
        )

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
