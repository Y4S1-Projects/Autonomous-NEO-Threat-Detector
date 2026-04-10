# Autonomous-NEO-Threat-Detector
RAG-Driven Multi-Agent Near-Earth Object Threat Assessment Pipeline

Autonomous NEO Threat Assessment Pipeline


## 📖 Project Overview
AstroGuard is a locally-hosted, zero-cloud Multi-Agent System (MAS) designed for planetary defense. It acts as an autonomous pipeline that monitors Near-Earth Object (NEO) telemetry, calculates theoretical impact physics, retrieves historical impact context using a local Vector Database (RAG), and synthesizes the data into an interactive geospatial map.

The system is strictly built using local Small Language Models (SLMs) via Ollama, orchestrated by LangGraph, ensuring 100% data privacy and zero API costs.

## 🏗️ System Architecture & Team Modules
The pipeline operates sequentially, passing a strict Global State (`NEOState`) between four specialized agents without losing context.

* **Module 1: The Telemetry Fetcher** (Live API Data)
  * *Role:* Safely retrieves and sanitizes live JSON data from the NASA NeoWs endpoint.
* **Module 2: The Trajectory Analyst** (Physics Engine)
  * *Role:* Computes mathematical kinetic energy and estimated mass based on first-principles physics.
* **Module 3: The Semantic RAG Assessor** (AI Backend)
  * *Role:* Queries a local ChromaDB vector database to provide historical context (e.g., Tunguska, Chicxulub) based on the calculated energy scale.
* **Module 4: The Geospatial Synthesizer** (Frontend/Visualization)
  * *Role:* Renders a standalone, interactive `simulation.html` map using Folium, plotting the blast radius and threat data.

---

## ⚙️ Local Setup & Installation

### Prerequisites
1. **Python 3.10+** installed on your machine.
2. **Ollama** installed locally (Download from [ollama.com](https://ollama.com/)).

### 1. Initialize the LLM Engine
Before running the code, you must ensure the local model is downloaded and running in the background. Open your terminal and run:
```bash
ollama run phi3
(Note: Keep the Ollama app running in your system tray while developing).

2. Setup the Python Environment
To prevent dependency conflicts, initialize a fresh virtual environment. Run these commands in the root of the astroguard_mas folder:

For Windows:

PowerShell
# Create the virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install all required libraries
python -m pip install -r requirements.txt
For Mac/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. API Keys (NASA Open Data)
By default, the Fetcher agent uses the NASA DEMO_KEY. To prevent rate-limiting during team testing:

Get a free key from api.nasa.gov.

Create a .env file in the root directory.

Add the following line: NASA_API_KEY=your_actual_key_here

🚀 Running the System
Once all agents are developed and integrated into main.py, run the pipeline from the root directory:

Bash
python main.py
Observability & Outputs
Logs: Execution traces, state handoffs, and LLM tool calls are recorded in logs/system_run.log.

Visual Output: The final geospatial map will be generated and saved to data/output_maps/simulation.html. Double-click this file to view the interactive rendering in your browser.