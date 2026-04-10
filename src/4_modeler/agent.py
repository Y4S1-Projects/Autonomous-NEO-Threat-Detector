import logging
from state import NEOState
from src.member_4_modeler.tools import generate_impact_map


def run_modeler_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Geospatial Synthesizer.
    Reads the final analytical data from the state and triggers
    the mapping tool to create the visual artifact.
    """
    logging.info("Agent 4 (Geospatial Synthesizer) activated.")

    radius = state.get("blast_radius_km")
    threat = state.get("threat_level")
    context = state.get("historical_match_context")

    # Defensive programming: Ensure we have data to map
    if radius is None or threat is None:
        logging.error("Modeler aborted: Missing threat data.")
        state["final_map_path"] = "Failed to generate map due to missing upstream data."
        return state

    # Execute the rendering tool
    logging.info(f"Agent 4 mapping {threat} threat with {radius}km radius.")
    map_path = generate_impact_map(radius, threat, context)

    # Update the Global State with the final file location
    state["final_map_path"] = map_path

    logging.info("Agent 4 finished. Pipeline complete.")
    return state
