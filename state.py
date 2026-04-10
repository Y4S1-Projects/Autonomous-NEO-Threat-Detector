from typing import TypedDict, Optional


class NEOState(TypedDict):
    """
    The Global State dictionary passed sequentially through the LangGraph pipeline.
    Each agent reads from this state and updates its specific assigned fields.
    """

    # Initiated by the user
    target_date: str

    # Updated by Member 1 (Telemetry Fetcher)
    raw_api_data: Optional[dict]

    # Updated by Member 2 (Trajectory Analyst)
    physics_results: Optional[dict]

    # Updated by Member 3 (Semantic RAG Assessor)
    threat_level: Optional[str]
    blast_radius_km: Optional[float]
    historical_match_context: Optional[str]

    # Updated by Member 4 (Geospatial Synthesizer)
    final_map_path: Optional[str]
