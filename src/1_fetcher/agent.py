import logging
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from state import NEOState
from src.member_1_fetcher.tools import fetch_nasa_neo_data


def run_fetcher_agent(state: NEOState) -> NEOState:
    """
    The LangGraph Node function for the Telemetry Fetcher.
    It reads the target_date from the state, triggers the tool,
    and updates the raw_api_data field.
    """
    logging.info("Agent 1 (Telemetry Fetcher) activated.")
    target_date = state["target_date"]

    # 1. Initialize the local LLM via Ollama
    # Ensure your whole team uses the exact same model name here!
    llm = ChatOllama(model="phi3", temperature=0)

    # 2. Define the Agent's strict persona
    system_prompt = SystemMessage(
        content=(
            "You are a strict data retrieval engineer for planetary defense. "
            "Your only job is to use your tools to fetch data. Do not analyze it."
        )
    )

    # NOTE: While advanced LangGraph setups use LLM tool-calling (bind_tools),
    # local SLMs sometimes struggle with JSON routing. To guarantee 100% stability
    # for the assignment, we can deterministically call the tool in Python
    # and pass the result back to the state.

    human_prompt = HumanMessage(content=f"Fetch the NEO data for {target_date}.")

    # Execute the custom tool
    logging.info("Agent 1 calling tool: fetch_nasa_neo_data")
    tool_result = fetch_nasa_neo_data(target_date)

    # Update the Global State clipboard with the new data
    state["raw_api_data"] = tool_result

    logging.info("Agent 1 finished. State updated.")
    return state
