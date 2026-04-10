from typing import TypedDict, Optional

class NEOState(TypedDict):
    target_date: str
    raw_api_data: Optional[dict]
    physics_results: Optional[dict]
    threat_level: Optional[str]
    blast_radius_km: Optional[float]
    historical_match_context: Optional[str]
    final_map_path: Optional[str]
