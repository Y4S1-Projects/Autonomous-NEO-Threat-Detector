# 🛡️ AstroGuard — Autonomous NEO Threat Detector

**RAG-Driven Multi-Agent Near-Earth Object Threat Assessment Pipeline**

---

## 📖 Project Overview

AstroGuard is a locally-hosted, zero-cloud **Multi-Agent System (MAS)** designed for planetary defense. It operates as an autonomous pipeline that:

1. **Monitors** Near-Earth Object (NEO) telemetry from NASA's live API
2. **Computes** theoretical impact physics using first-principles calculations
3. **Retrieves** historical impact context using a local ChromaDB vector database (RAG)
4. **Visualizes** the results as an interactive geospatial map with Folium

The system is strictly built using **local Small Language Models (SLMs)** via [Ollama](https://ollama.com/), orchestrated by **LangGraph**, ensuring 100% data privacy and zero API costs.

---

## 🏗️ System Architecture

The pipeline operates **sequentially**, passing a strict Global State (`NEOState`) between four specialized agents without losing context:

```
User Input (date)
    │
    ▼
┌──────────────────────┐
│  Agent 1: Telemetry  │  ── Fetches live NASA NeoWs data
│  Fetcher             │
└──────────┬───────────┘
           │ raw_api_data
           ▼
┌──────────────────────┐
│  Agent 2: Trajectory │  ── Computes KE = ½mv² physics
│  Analyst             │
└──────────┬───────────┘
           │ physics_results
           ▼
┌──────────────────────┐
│  Agent 3: Semantic   │  ── Queries ChromaDB (RAG) for
│  RAG Assessor        │     historical impact context
└──────────┬───────────┘
           │ threat_level, blast_radius_km, historical_context
           ▼
┌──────────────────────┐
│  Agent 4: Geospatial │  ── Renders interactive Folium
│  Synthesizer         │     HTML map with blast zones
└──────────┬───────────┘
           │ final_map_path
           ▼
     simulation.html
```

### Technology Stack

| Component     | Technology     | Purpose                          |
| ------------- | -------------- | -------------------------------- |
| LLM Engine    | Ollama (phi3)  | Local SLM for agent reasoning    |
| Orchestrator  | LangGraph      | State graph pipeline management  |
| API Data      | NASA NeoWs     | Live asteroid telemetry          |
| Vector DB     | ChromaDB       | Local RAG for historical impacts |
| Visualization | Folium         | Interactive HTML map rendering   |
| Observability | Python logging | Structured execution tracing     |

---

## ⚙️ Local Setup & Installation

### Prerequisites

1. **Python 3.10+** installed on your machine
2. **Ollama** installed locally — download from [ollama.com](https://ollama.com/)

### 1. Initialize the LLM Engine

Download and start the local model:

```bash
ollama pull phi3
ollama run phi3
```

> **Note:** Keep the Ollama app running in your system tray while using AstroGuard.

### 2. Setup the Python Environment

Create a virtual environment and install dependencies:

**Windows (PowerShell):**

```powershell
# Create the virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install all required libraries
python -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. API Keys (NASA Open Data)

By default, the Fetcher agent uses the NASA `DEMO_KEY`. To avoid rate-limiting:

1. Get a free key from [api.nasa.gov](https://api.nasa.gov/)
2. Edit the `.env` file in the project root:
   ```
   NASA_API_KEY=your_actual_key_here
   ```

---

## 🚀 Running the System

```bash
# Run with today's date
python main.py

# Run with a specific date
python main.py 2026-04-12

# Run with named argument
python main.py --date 2026-04-12
```

### Output

- **Logs:** Execution traces, state handoffs, and tool calls → `logs/system_run.log`
- **Map:** Interactive geospatial visualization → `data/output_maps/simulation_latest.html`

Open the HTML file in any browser to explore the interactive impact simulation.

---

## 🧪 Testing

### Run Individual Module Tests

```bash
# Test the Modeler (Module 4)
python src/4_modeler/test.py
```

### Run the Unified Test Harness

```bash
# Run all tests across all agents
python tests/test_harness.py

# Or with pytest
python -m pytest tests/test_harness.py -v
```

The unified harness discovers and executes all individual agent tests plus integration-level state preservation tests.

---

## 📁 Project Structure

```
Autonomous-NEO-Threat-Detector/
├── main.py                    # Pipeline orchestrator (LangGraph)
├── state.py                   # Global NEOState definition
├── requirements.txt           # Python dependencies
├── .env                       # API keys (gitignored)
├── src/
│   ├── 1_fetcher/             # Agent 1: NASA API data retrieval
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── test.py
│   ├── 2_analyst/             # Agent 2: Physics computation
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── test.py
│   ├── 3_assessor/            # Agent 3: ChromaDB RAG assessment
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── test.py
│   └── 4_modeler/             # Agent 4: Folium map visualization
│       ├── agent.py
│       ├── tools.py
│       └── test.py
├── tests/
│   └── test_harness.py        # Unified testing harness
├── data/
│   ├── historical_corpus.txt  # RAG corpus for ChromaDB
│   ├── output_maps/           # Generated HTML maps
│   └── vector_db/             # ChromaDB persistent storage
└── logs/
    └── system_run.log         # Observability trace log
```

---

## 👥 Kay Functionalities

| Agent                  | Tool                         | Key Responsibility        |
| ---------------------- | ---------------------------- | ------------------------- |
| Telemetry Fetcher      | `fetch_nasa_neo_data()`      | Live NASA API integration |
| Trajectory Analyst     | `calculate_kinetic_energy()` | First-principles physics  |
| Semantic RAG Assessor  | `query_vector_memory()`      | ChromaDB vector search    |
| Geospatial Synthesizer | `generate_impact_map()`      | Interactive Folium map    |
