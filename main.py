import logging
from langgraph.graph import StateGraph, END
from state import NEOState

# Set up Observability Logging (Required for 10% AgentOps grade)
logging.basicConfig(
    filename="logs/system_run.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# TODO: Import the agent nodes once the team builds them
# from src.member_1_fetcher.agent import run_fetcher_agent
# from src.member_2_analyst.agent import run_analyst_agent
# from src.member_3_assessor.agent import run_rag_assessor_agent
# from src.member_4_modeler.agent import run_modeler_agent


def build_pipeline():
    """Builds and compiles the sequential Multi-Agent pipeline."""
    logging.info("Initializing AstroGuard MAS Pipeline...")

    # Initialize the graph with our strict typed state
    workflow = StateGraph(NEOState)

    # 1. Add the Nodes (The Agents)
    # workflow.add_node("telemetry_fetcher", run_fetcher_agent)
    # workflow.add_node("trajectory_analyst", run_analyst_agent)
    # workflow.add_node("rag_assessor", run_rag_assessor_agent)
    # workflow.add_node("geospatial_modeler", run_modeler_agent)

    # 2. Define the Edges (The strict sequential data flow)
    # workflow.add_edge("telemetry_fetcher", "trajectory_analyst")
    # workflow.add_edge("trajectory_analyst", "rag_assessor")
    # workflow.add_edge("rag_assessor", "geospatial_modeler")
    # workflow.add_edge("geospatial_modeler", END)

    # 3. Set the Entry Point
    # workflow.set_entry_point("telemetry_fetcher")

    # Compile the graph
    app = workflow.compile()
    return app


if __name__ == "__main__":
    print("AstroGuard MAS Pipeline Scaffold Ready.")
    # Example trigger once agents are built:
    # app = build_pipeline()
    # initial_state = {"target_date": "2026-04-12"}
    # result = app.invoke(initial_state)
    # print(f"Execution complete. Map saved to: {result.get('final_map_path')}")
