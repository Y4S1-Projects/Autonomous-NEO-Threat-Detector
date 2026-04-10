# Module 1: The Telemetry Fetcher 🛰️
**Owner:** [Student 1 Name]
**Role:** Data Engineer / Sensory Input

## Objective
Your goal is to act as the "eyes" of the AstroGuard system. The LLM cannot see the internet, so you must build the tool that safely connects to the NASA NeoWs API, authenticates, and retrieves the raw telemetry data for a specific date without crashing the system.

## Required Deliverables

### 1. `tools.py`
Write the function `fetch_nasa_neo_data(target_date: str) -> dict`.
* **Technique:** Use the `requests` Python library.
* **Constraint 1:** You must handle network failures gracefully. Include a `timeout=10` parameter in your request and wrap it in a `try/except` block.
* **Constraint 2:** Do not return the *entire* massive JSON. Parse it and return a clean dictionary containing only the asteroid's name, estimated diameter (meters), and relative velocity (km/s).
* **Grading Requirement:** Include strict Python type hinting and a Google-style docstring explaining your error handling.

### 2. `agent.py`
Write the LangGraph Node function and the System Prompt for your Agent.
* **Persona:** "You are a strict data retrieval engineer. Your only job is to use your tool to fetch JSON data for the user's target date. Do not analyze the data or add conversational text."

### 3. `test.py`
Write a Property-Based Test using Python's `unittest` framework.
* **To Do:** Write a script that calls your tool directly and asserts that the return type is a `dict`, and that it contains the key `"estimated_diameter"`.