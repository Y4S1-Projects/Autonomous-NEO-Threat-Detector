"""
AstroGuard Multi-Agent System — Main Pipeline Orchestrator.

This is the entry point for the Autonomous NEO Threat Detector. It
constructs and executes a sequential LangGraph pipeline that passes
a shared NEOState through four specialized AI agents:

    1. Telemetry Fetcher  → Retrieves live NASA NEO data
    2. Trajectory Analyst  → Computes impact physics
    3. RAG Assessor        → Queries ChromaDB for historical context
    4. Geospatial Modeler  → Renders an interactive Folium map

Usage:
    python main.py                     # Uses default date (today)
    python main.py 2026-04-12          # Uses a specific target date
    python main.py --date 2026-04-12   # Named argument form

Observability:
    All agent activations, tool executions, state transitions, and
    errors are logged to both ``logs/system_run.log`` (persistent)
    and the console (ephemeral) via structured Python logging.
"""

import os
import sys
import logging
import argparse
import importlib
from datetime import datetime, timezone
from typing import Dict, Any

# ── Ensure project root is on sys.path ──────────────────────────────────
# This allows all modules to import `state` and `src.*` regardless
# of the current working directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from langgraph.graph import StateGraph, END  # noqa: E402
from state import NEOState  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════
# Observability: Structured Logging Configuration
# ═══════════════════════════════════════════════════════════════════════


def _configure_logging() -> logging.Logger:
    """
    Set up dual-output logging for AgentOps compliance.

    Creates two handlers:
      • **File handler** — appends structured records to
        ``logs/system_run.log`` for post-run analysis.
      • **Console handler** — emits formatted output to ``stdout``
        for live monitoring during pipeline execution.

    Returns:
        logging.Logger: The configured root logger instance.
    """
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on re-import
    if not logger.handlers:
        # File handler — persistent record
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "system_run.log"),
            mode="a",
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)

        # Console handler — live feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(console_handler)

    return logger


logger = _configure_logging()


# ═══════════════════════════════════════════════════════════════════════
# Dynamic Module Imports (handles numeric-prefix directories)
# ═══════════════════════════════════════════════════════════════════════


def _import_agent_function(module_dir: str, module_file: str, func_name: str):
    """
    Dynamically imports an agent's node function from a directory whose
    name begins with a digit (e.g., ``src/1_fetcher``).

    Standard Python ``import`` syntax does not support module names
    starting with numbers. This helper uses :mod:`importlib` to
    resolve the path at runtime.

    Args:
        module_dir:  Relative sub-directory under ``src/``
                     (e.g., ``'1_fetcher'``).
        module_file: Python file inside that directory
                     (e.g., ``'agent'``).
        func_name:   The callable to extract from the module
                     (e.g., ``'run_fetcher_agent'``).

    Returns:
        The imported callable, ready to be used as a LangGraph node.

    Raises:
        ImportError: If the module or function cannot be found.
    """
    module_path = os.path.join(PROJECT_ROOT, "src", module_dir, f"{module_file}.py")
    spec = importlib.util.spec_from_file_location(
        f"src.{module_dir}.{module_file}", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, func_name)


# Import each agent's LangGraph node function
try:
    run_fetcher_agent = _import_agent_function(
        "1_fetcher", "agent", "run_fetcher_agent"
    )
    run_analyst_agent = _import_agent_function(
        "2_analyst", "agent", "run_analyst_agent"
    )
    run_rag_assessor_agent = _import_agent_function(
        "3_assessor", "agent", "run_rag_assessor_agent"
    )
    run_modeler_agent = _import_agent_function(
        "4_modeler", "agent", "run_modeler_agent"
    )
    ALL_AGENTS_LOADED = True
    logger.info("All 4 agent modules loaded successfully.")
except (ImportError, FileNotFoundError, AttributeError) as exc:
    ALL_AGENTS_LOADED = False
    logger.warning(f"Agent import failed ({exc}). Pipeline will run in demo mode.")


# ═══════════════════════════════════════════════════════════════════════
# LangGraph Pipeline Construction
# ═══════════════════════════════════════════════════════════════════════


def build_pipeline() -> Any:
    """
    Constructs and compiles the sequential Multi-Agent pipeline.

    The pipeline enforces a strict linear data flow::

        Telemetry Fetcher → Trajectory Analyst → RAG Assessor → Geospatial Modeler → END

    Each node receives the full :class:`NEOState` and updates only
    its own designated fields, preserving upstream context.

    Returns:
        The compiled LangGraph application, ready for ``.invoke()``.

    Raises:
        RuntimeError: If agent modules failed to load.
    """
    if not ALL_AGENTS_LOADED:
        raise RuntimeError(
            "Cannot build pipeline — one or more agent modules failed to import. "
            "Check the logs for details."
        )

    logger.info("═" * 60)
    logger.info("Initializing AstroGuard MAS Pipeline...")
    logger.info("═" * 60)

    # Initialize the graph with the strict typed state
    workflow = StateGraph(NEOState)

    # ── 1. Add the Agent Nodes ──────────────────────────────────────
    workflow.add_node("telemetry_fetcher", run_fetcher_agent)
    workflow.add_node("trajectory_analyst", run_analyst_agent)
    workflow.add_node("rag_assessor", run_rag_assessor_agent)
    workflow.add_node("geospatial_modeler", run_modeler_agent)

    # ── 2. Define Sequential Edges (strict data-flow order) ─────────
    workflow.add_edge("telemetry_fetcher", "trajectory_analyst")
    workflow.add_edge("trajectory_analyst", "rag_assessor")
    workflow.add_edge("rag_assessor", "geospatial_modeler")
    workflow.add_edge("geospatial_modeler", END)

    # ── 3. Set the Entry Point ──────────────────────────────────────
    workflow.set_entry_point("telemetry_fetcher")

    # Compile the graph into an executable application
    app = workflow.compile()
    logger.info("Pipeline compiled successfully. Ready for invocation.")
    return app


# ═══════════════════════════════════════════════════════════════════════
# Pipeline Execution
# ═══════════════════════════════════════════════════════════════════════


def run_pipeline(target_date: str) -> Dict[str, Any]:
    """
    Executes the full AstroGuard pipeline for a given target date.

    Creates a clean initial :class:`NEOState`, invokes the compiled
    LangGraph application, and returns the final state containing
    all agent outputs.

    Args:
        target_date: The date to query in ``'YYYY-MM-DD'`` format.

    Returns:
        Dict[str, Any]: The completed NEOState with all fields populated.
    """
    logger.info(f"Pipeline triggered for target date: {target_date}")

    # Build the pipeline
    app = build_pipeline()

    # Create the initial empty state
    initial_state: NEOState = {
        "target_date": target_date,
        "raw_api_data": None,
        "asteroid_name": None,
        "physics_results": None,
        "threat_level": None,
        "blast_radius_km": None,
        "historical_match_context": None,
        "final_map_path": None,
        "errors": [],
        "execution_metadata": {
            "pipeline_start": datetime.now(timezone.utc).isoformat(),
            "pipeline_status": "RUNNING",
        },
    }

    logger.info("Initial state created. Invoking pipeline...")
    logger.info("-" * 60)

    # Execute the full pipeline
    start_time = datetime.now(timezone.utc)
    try:
        result = app.invoke(initial_state)
        result["execution_metadata"]["pipeline_status"] = "COMPLETED"
    except Exception as exc:
        logger.error(f"Pipeline execution failed: {exc}")
        initial_state["errors"].append(f"Pipeline failure: {exc}")
        initial_state["execution_metadata"]["pipeline_status"] = "FAILED"
        result = initial_state

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    result["execution_metadata"]["pipeline_end"] = end_time.isoformat()
    result["execution_metadata"]["duration_seconds"] = duration

    # ── Final Summary ───────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Target Date    : {result.get('target_date')}")
    logger.info(f"  Asteroid       : {result.get('asteroid_name', 'N/A')}")
    logger.info(f"  Threat Level   : {result.get('threat_level', 'N/A')}")
    logger.info(f"  Blast Radius   : {result.get('blast_radius_km', 'N/A')} km")
    logger.info(f"  Map Output     : {result.get('final_map_path', 'N/A')}")
    logger.info(f"  Duration       : {duration:.2f}s")
    logger.info(f"  Errors         : {len(result.get('errors', []))}")
    if result.get("errors"):
        for err in result["errors"]:
            logger.warning(f"    ⚠ {err}")
    logger.info("=" * 60)

    return result


# ═══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the pipeline."""
    parser = argparse.ArgumentParser(
        prog="AstroGuard MAS",
        description=(
            "Autonomous NEO Threat Assessment Pipeline — "
            "A multi-agent system for planetary defense analysis."
        ),
    )
    parser.add_argument(
        "date",
        nargs="?",
        default=None,
        help="Target date in YYYY-MM-DD format (default: today).",
    )
    parser.add_argument(
        "--date",
        "-d",
        dest="named_date",
        default=None,
        help="Target date (alternative named argument).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Resolve the target date from positional or named arg
    target = args.named_date or args.date or datetime.now().strftime("%Y-%m-%d")

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        🛡️  AstroGuard — NEO Threat Detector  🛡️        ║")
    print("║     Multi-Agent Planetary Defense Analysis System       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"  Target Date: {target}")
    print()

    if not ALL_AGENTS_LOADED:
        print("⚠️  Some agent modules could not be imported.")
        print("   Ensure all dependencies are installed:")
        print("     pip install -r requirements.txt")
        print("   And that Ollama is running:")
        print("     ollama run phi3")
        sys.exit(1)

    result = run_pipeline(target)

    map_path = result.get("final_map_path")
    if map_path and os.path.exists(str(map_path)):
        print(f"\n✅ Success! Open the interactive map:")
        print(f"   {map_path}\n")
    else:
        print(f"\n❌ Pipeline completed with issues. Check logs/system_run.log\n")
