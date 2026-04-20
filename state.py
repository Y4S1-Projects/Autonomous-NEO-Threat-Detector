"""
Global State Management for the Autonomous NEO Threat Detector Pipeline.

This module defines the shared NEOState TypedDict that flows sequentially
through the LangGraph pipeline. Each agent reads the fields it needs and
writes ONLY to its designated output fields, ensuring zero context loss
between handoffs.

Architecture:
    User Input → Fetcher → Analyst → Assessor → Modeler → END

State Preservation Strategy:
    LangGraph passes this dictionary by reference through each node.
    Each node function receives the full state and returns the full state
    with its assigned fields updated. Fields written by upstream agents
    are preserved immutably by downstream agents.

Observability:
    The `errors` list accumulates any warnings or failures from each agent
    without halting the pipeline. The `execution_metadata` dict records
    timestamps and durations for each agent's execution, enabling
    post-run performance analysis via the system log.
"""

from typing import TypedDict, Optional, List, Dict, Any


class NEOState(TypedDict):
    """
    The Global State dictionary passed sequentially through the LangGraph
    pipeline. Each agent reads from this state and updates its specific
    assigned fields. No agent may overwrite another agent's output fields.

    Attributes:
        target_date: The user-specified date to query for NEO data
                     (format: 'YYYY-MM-DD'). Set at pipeline initiation.

        raw_api_data: Sanitized JSON from the NASA NeoWs API containing
                      asteroid name, diameter, and velocity.
                      Written by: Agent 1 (Telemetry Fetcher).

        asteroid_name: The human-readable designation of the target NEO
                       extracted from the API response.
                       Written by: Agent 1 (Telemetry Fetcher).

        physics_results: Computed mass (kg) and kinetic energy (Joules)
                         derived from first-principles physics calculations.
                         Written by: Agent 2 (Trajectory Analyst).

        threat_level: Classification label assigned by the RAG assessor.
                      One of: 'LOW', 'MODERATE', 'HIGH', or 'UNKNOWN'.
                      Written by: Agent 3 (Semantic RAG Assessor).

        blast_radius_km: The estimated theoretical blast radius in km,
                         retrieved from the historical impact database.
                         Written by: Agent 3 (Semantic RAG Assessor).

        historical_match_context: Natural-language description of the
                                  closest historical impact event retrieved
                                  from the ChromaDB vector database via RAG.
                                  Written by: Agent 3 (Semantic RAG Assessor).

        final_map_path: Absolute file path to the generated interactive
                        Folium HTML map file (simulation_latest.html).
                        Written by: Agent 4 (Geospatial Synthesizer).

        errors: Accumulated list of non-fatal error/warning messages
                from any agent in the pipeline. Allows the system to
                degrade gracefully without losing upstream context.
                Written by: Any agent encountering a recoverable error.

        execution_metadata: Dictionary recording per-agent execution
                            timestamps, durations, and status codes for
                            observability and AgentOps compliance.
                            Written by: Each agent upon activation.
    """

    # ── User Input ──────────────────────────────────────────────────────
    target_date: str
    asteroid_index: int

    # ── Agent 1: Telemetry Fetcher ──────────────────────────────────────
    raw_api_data: Optional[Dict[str, Any]]
    asteroid_name: Optional[str]

    # ── Agent 2: Trajectory Analyst ─────────────────────────────────────
    physics_results: Optional[Dict[str, float]]

    # ── Agent 3: Semantic RAG Assessor ──────────────────────────────────
    threat_level: Optional[str]
    blast_radius_km: Optional[float]
    historical_match_context: Optional[str]

    # ── Agent 4: Geospatial Synthesizer ─────────────────────────────────
    final_map_path: Optional[str]
    estimated_affected_population: Optional[int]

    # ── Cross-Cutting Observability ─────────────────────────────────────
    errors: List[str]
    execution_metadata: Dict[str, Any]
