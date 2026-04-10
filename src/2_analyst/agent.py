import logging
from state import NEOState
from src.member_2_analyst.tools import calculate_kinetic_energy


def run_analyst_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Trajectory Analyst.
    Extracts numerical data from the raw API JSON and passes it
    into the deterministic physics engine.
    """
    logging.info("Agent 2 (Trajectory Analyst) activated.")

    raw_data = state.get("raw_api_data", {})

    # Defensive check: Ensure Agent 1 didn't pass an error
    if not raw_data or "error" in raw_data:
        logging.error("Analyst aborted: Invalid raw data received.")
        state["physics_results"] = {"error": "Missing telemetry data."}
        return state

    diameter = raw_data.get("estimated_diameter_meters")
    velocity = raw_data.get("relative_velocity_kms")

    if diameter is None or velocity is None:
        state["physics_results"] = {"error": "Missing dimensional data."}
        return state

    # Execute the custom tool
    logging.info(f"Agent 2 parsing: Diameter={diameter}m, Velocity={velocity}km/s")
    physics_output = calculate_kinetic_energy(diameter, velocity)

    # Update the Global State clipboard
    state["physics_results"] = physics_output

    logging.info("Agent 2 finished. State updated.")
    return state
