# Module 4: The Geospatial Synthesizer 🌍
**Owner:** [Student 4 Name]
**Role:** Frontend & Geospatial Modeler

## Objective
Your goal is to generate the final "Wow" factor. You must synthesize the data, physics, and historical context into a standalone, interactive HTML map that the user can explore in their web browser.

## Required Deliverables

### 1. `tools.py`
Write the function `generate_impact_map(radius_km: float, threat_level: str, historical_context: str) -> str`.
* **Technique:** Use the `folium` Python library. 
* **Logic:** Generate a random ocean coordinate (Latitude/Longitude). Use `folium.Circle` to draw a blast radius over that coordinate. Color the circle based on the `threat_level` (e.g., red for HIGH, yellow for MODERATE). Add a `folium.Popup` containing the `historical_context` text.
* **Output:** Save the map to `data/output_maps/simulation.html`. The function should return the exact file path.
* **Grading Requirement:** Include strict Python type hinting and a docstring explaining the Folium rendering process.

### 2. `agent.py`
Write the LangGraph Node function and the System Prompt for your Agent.
* **Persona:** "You are a geospatial rendering engine. Read the `blast_radius_km`, `threat_level`, and `historical_match_context` from the state. Do not invent any new facts. Pass this exact data into your mapping tool to generate the final output."

### 3. `test.py`
Write a Hybrid Validation Test using Python's `unittest` and `os` modules.
* **To Do:** Write a script that checks `os.path.exists('data/output_maps/simulation.html')` to prove your tool generated the file successfully.