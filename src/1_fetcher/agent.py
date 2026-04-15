"""
Agent 1 — Telemetry Fetcher Node for LangGraph Pipeline.

This module defines the LangGraph node function for the Telemetry Fetcher
agent. It reads `target_date` from the shared NEOState, invokes the
NASA NeoWs API tool, and writes the sanitized telemetry data back.

Agent Persona:
    A strict data retrieval engineer for planetary defense.
    Fetches and sanitizes data — never analyzes or interprets it.
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
from .tools import fetch_nasa_neo_data

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


def run_fetcher_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Telemetry Fetcher.

    It reads the target_date from the state, triggers the NASA API tool,
    and updates the ``raw_api_data`` and ``asteroid_name`` fields.

    Args:
        state: The current NEOState passed from the pipeline entry point.

    Returns:
        NEOState: The updated state with ``raw_api_data`` populated.
    """
    logging.info("Agent 1 (Telemetry Fetcher) activated.")
    agent_start = datetime.now(timezone.utc)

    target_date = state["target_date"]

    # ── LLM Integration (verify intent, not generate data) ──────────
    if OLLAMA_AVAILABLE:
        try:
            llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), temperature=0
            )
            system_prompt = SystemMessage(
                content=(
                    "You are a strict data retrieval engineer for planetary defense. "
                    "Your only job is to use your tools to fetch data. Do not analyze it. "
                    "Do not hallucinate any data. Only report what the tool returns."
                )
            )
            human_prompt = HumanMessage(
                content=f"Fetch the NEO data for {target_date}."
            )
            # LLM acknowledges the task (not used for actual data retrieval)
            llm.invoke([system_prompt, human_prompt])
            logging.info("Agent 1 LLM acknowledged task.")
        except Exception as e:
            logging.warning(
                f"Agent 1 LLM unavailable ({e}), proceeding with direct tool call."
            )
    else:
        logging.info("Agent 1: Ollama not available, using direct tool execution.")

    # ── Execute the custom tool ─────────────────────────────────────
    logging.info("Agent 1 calling tool: fetch_nasa_neo_data")
    tool_result = fetch_nasa_neo_data(target_date)

    # ── Update the Global State ─────────────────────────────────────
    state["raw_api_data"] = tool_result
    state["asteroid_name"] = (
        tool_result.get("name") if isinstance(tool_result, dict) else None
    )

    if isinstance(tool_result, dict) and "error" in tool_result:
        state["errors"].append(f"Agent 1: {tool_result['error']}")

    # Record execution metadata
    agent_end = datetime.now(timezone.utc)
    state["execution_metadata"]["agent_1_fetcher"] = {
        "start": agent_start.isoformat(),
        "end": agent_end.isoformat(),
        "duration_seconds": (agent_end - agent_start).total_seconds(),
        "status": (
            "error"
            if (isinstance(tool_result, dict) and "error" in tool_result)
            else "success"
        ),
    }

    logging.info("Agent 1 finished. State updated.")
    return state
