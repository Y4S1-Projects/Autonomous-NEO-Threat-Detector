import logging
from state import NEOState
from src.member_3_assessor.tools import query_vector_memory


def run_rag_assessor_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Semantic RAG Assessor.
    Reads the kinetic energy, queries the local Vector Database,
    and appends the historical memory and threat level to the state.
    """
    logging.info("Agent 3 (RAG Assessor) activated.")

    physics_data = state.get("physics_results", {})

    if not physics_data or "error" in physics_data:
        logging.error("RAG Assessor aborted: Missing physics data.")
        state["threat_level"] = "UNKNOWN"
        state["historical_match_context"] = "Data missing due to upstream failure."
        return state

    energy = physics_data.get("kinetic_energy_joules")

    if energy is None:
        state["threat_level"] = "UNKNOWN"
        return state

    # Execute the RAG Tool
    logging.info(f"Agent 3 querying memory for energy: {energy:e} Joules")
    rag_results = query_vector_memory(energy)

    # Update the Global State clipboard with the 3 new facts
    state["threat_level"] = rag_results["threat_level"]
    state["blast_radius_km"] = rag_results["blast_radius_km"]
    state["historical_match_context"] = rag_results["historical_match_context"]

    logging.info(
        f"Agent 3 finished. Threat classified as: {rag_results['threat_level']}"
    )
    return state
