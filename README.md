# AstroGuard — Autonomous NEO Threat Detector

**RAG-Driven Multi-Agent Near-Earth Object Threat Assessment Pipeline**

> A locally-hosted, zero-cloud Multi-Agent System (MAS) for planetary defense, built with LangGraph, Ollama, and custom Python tools.

---

## Project Overview

AstroGuard is an autonomous pipeline that monitors Near-Earth Objects (NEOs) and generates interactive threat assessment visualizations. The system operates entirely on local infrastructure — no cloud APIs, no paid LLM subscriptions, and complete data privacy.

### What It Does

1. **Fetches** live asteroid telemetry from NASA's NeoWs API
2. **Computes** theoretical impact physics using first-principles calculations
3. **Retrieves** historical impact context using a local ChromaDB vector database (RAG)
4. **Visualizes** the results as an interactive geospatial map with Folium

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Engine | Ollama (local SLM) | Agent reasoning & verification |
| Orchestrator | LangGraph | State graph pipeline management |
| API Data | NASA NeoWs | Live asteroid telemetry |
| Vector DB | ChromaDB | Local RAG for historical impacts |
| Visualization | Folium / Leaflet.js | Interactive HTML map rendering |
| Env Config | python-dotenv | Centralized environment management |
| Observability | Python logging | Structured execution tracing |

---

## System Architecture

```
User Input (date)
    |
    v
+----------------------+
|  Agent 1: Telemetry  |  -- Fetches live NASA NeoWs data
|  Fetcher             |     Tool: fetch_nasa_neo_data()
+----------+-----------+
           | raw_api_data, asteroid_name
           v
+----------------------+
|  Agent 2: Trajectory |  -- Computes KE = 1/2 mv^2 physics
|  Analyst             |     Tool: calculate_kinetic_energy()
+----------+-----------+
           | physics_results
           v
+----------------------+
|  Agent 3: Semantic   |  -- Queries ChromaDB (RAG) for
|  RAG Assessor        |     historical impact context
+----------+-----------+     Tool: query_vector_memory()
           | threat_level, blast_radius_km, historical_context
           v
+----------------------+
|  Agent 4: Geospatial |  -- Renders interactive Folium
|  Synthesizer         |     HTML map with blast zones
+----------+-----------+     Tool: generate_impact_map()
           | final_map_path
           v
     simulation.html
```

### Global State Flow

All agents share a single `NEOState` dictionary managed by LangGraph. Each agent reads upstream data and writes to its own fields — no agent overwrites another agent's output. The state also tracks `errors` (non-fatal warnings) and `execution_metadata` (per-agent timing and status) for full observability.

---

## Setup & Installation

### Prerequisites

| Requirement | Version | Check |
|------------|---------|-------|
| Python | 3.10+ | `python --version` |
| Ollama | Latest | [Download](https://ollama.com/) |
| Git | Any | `git --version` |

### Step 1: Clone & Install Dependencies

```bash
git clone <repository-url>
cd Autonomous-NEO-Threat-Detector

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Get your free key at https://api.nasa.gov/
NASA_API_KEY=your_nasa_api_key_here

# LLM model (see Step 3 for how to choose this)
OLLAMA_MODEL=qwen2.5:7b
```

> **Note:** The NASA `DEMO_KEY` works but is rate-limited to 30 requests/hour. Get a free unlimited key at [api.nasa.gov](https://api.nasa.gov/).

### Step 3: Install & Select the Best LLM

This project uses **Ollama** to run local Small Language Models. The system is model-agnostic — you can swap any Ollama-compatible model without changing code.

#### 3a. Install Ollama Models

Download one or more models to evaluate:

```bash
# Recommended candidates
ollama pull qwen2.5:7b      # 4.7 GB — Best balance of speed + accuracy
ollama pull llama3.1         # 4.9 GB — Strong reasoning
ollama pull phi3             # 2.2 GB — Lightweight, fast
```

#### 3b. Benchmark Models (Recommended)

We provide a built-in benchmark tool that evaluates each model against the exact prompts used in the pipeline. This ensures you deploy the best model for YOUR hardware.

**The benchmark tests 4 criteria:**

| Test | What It Measures | Why It Matters |
|------|-----------------|----------------|
| **Format Adherence** | Outputs pure JSON without markdown or explanation | Bad formatting crashes the parser |
| **RAG Comprehension** | Single-word threat classification from context | Agent 3 needs exact format |
| **Anti-Hallucination** | Reports only provided data, no invented facts | Core safety requirement |
| **Tool Instruction** | Acknowledges tool use, doesn't fabricate data | Agent 1 must not guess API data |

**Run the benchmark for each model (one at a time due to RAM):**

```bash
# Test Model 1
python benchmark.py qwen2.5:7b
ollama stop qwen2.5:7b

# Test Model 2
python benchmark.py llama3.1
ollama stop llama3.1

# Test Model 3
python benchmark.py phi3
ollama stop phi3

# Compare all results
python benchmark.py --compare
```

> **Important:** Always run `ollama stop <model>` before testing the next model to free GPU/RAM.

#### 3c. Our Benchmark Results

We systematically tested three models. Results are saved in `benchmark_results/`:

| Model | Avg Score | Avg Latency | Format | RAG | Hallucination | Tool |
|-------|-----------|-------------|--------|-----|---------------|------|
| **qwen2.5:7b** | **100/100** | **17.71s** | 100 | 100 | 100 | 100 |
| llama3.1 | 100/100 | 19.00s | 100 | 100 | 100 | 100 |
| phi3 | 72.5/100 | 20.95s | 20 | 70 | 100 | 100 |

**Selected Model: `qwen2.5:7b`**
- Perfect accuracy (100/100) — tied with llama3.1
- Fastest inference (17.71s avg) — 7% faster than llama3.1
- phi3 failed format adherence (wrapped JSON in markdown fences) and RAG comprehension (added extra explanation text instead of a single word)

#### 3d. Using a Different Model

To switch models at any time, simply update your `.env` file:

```env
OLLAMA_MODEL=llama3.1
```

All agents automatically read from this single configuration point — no code changes required. You can also benchmark any new model:

```bash
ollama pull mistral:7b
python benchmark.py mistral:7b
python benchmark.py --compare
```

### Step 4: Verify the Setup

```bash
# Verify NASA API connection
python -c "from dotenv import load_dotenv; import os, requests; load_dotenv('.env'); key=os.getenv('NASA_API_KEY'); r=requests.get(f'https://api.nasa.gov/neo/rest/v1/feed?start_date=2026-04-15&end_date=2026-04-15&api_key={key}'); print(f'NASA API: {r.status_code}')"

# Verify Ollama is running
ollama list
```

---

## Running the Pipeline

```bash
# Run with today's date
python main.py

# Run with a specific date
python main.py 2026-04-15

# Run with named argument
python main.py --date 2026-04-15
```

### Output

| Artifact | Location | Description |
|----------|----------|-------------|
| Execution Log | `logs/system_run.log` | Agent activations, tool calls, state transitions, timing |
| Impact Map | `data/output_maps/simulation_latest.html` | Interactive Leaflet.js visualization |

Open the HTML map in any browser to explore the blast zones, threat legend, and historical context popup.

---

## Testing

### Individual Module Tests

Each team member maintains their own test suite in their agent directory:

```bash
# Test Module 4 (Geospatial Synthesizer)
python src/4_modeler/test.py
```

### Unified Test Harness

The project includes a consolidated test harness that discovers and runs all agent tests plus integration-level state preservation tests:

```bash
python tests/test_harness.py
```

### Test Coverage (Module 4)

| Category | Count | Description |
|----------|-------|-------------|
| Happy Path | 3 | LOW, MODERATE, HIGH threat level map generation |
| Edge Cases | 5 | Negative/zero/tiny/huge radius, invalid types, unknown threat levels |
| Content Validation | 3 | HTML structure, data embedding, file size bounds |
| Helper Functions | 4 | Zoom scaling, style lookup, coordinate selection, popup builder |
| LLM-as-a-Judge | 2 | Accuracy evaluation + mismatch detection via Ollama |
| **Total** | **19** | **All passing** |

### LLM-as-a-Judge Pattern

The test suite implements the LLM-as-a-Judge evaluation pattern where the local SLM acts as a quality gate:

- **Accuracy Test:** The LLM verifies that the generated map output is internally consistent (threat level matches blast radius matches historical context)
- **Mismatch Detection:** The LLM is given intentionally contradictory data (LOW threat + extinction-level description) and must detect the inconsistency

This validates that the model can serve as a reliable verification layer in the pipeline.

---

## Project Structure

```
Autonomous-NEO-Threat-Detector/
|-- main.py                        # LangGraph pipeline orchestrator
|-- state.py                       # Global NEOState definition
|-- benchmark.py                   # LLM model benchmarking tool
|-- requirements.txt               # Python dependencies
|-- .env                           # Local config (gitignored)
|-- .env.example                   # Config template (committed)
|-- src/
|   |-- __init__.py
|   |-- 1_fetcher/                 # Agent 1: NASA API data retrieval
|   |   |-- agent.py               #   LangGraph node function
|   |   |-- tools.py               #   fetch_nasa_neo_data()
|   |   +-- test.py
|   |-- 2_analyst/                 # Agent 2: Physics computation
|   |   |-- agent.py
|   |   |-- tools.py               #   calculate_kinetic_energy()
|   |   +-- test.py
|   |-- 3_assessor/                # Agent 3: ChromaDB RAG assessment
|   |   |-- agent.py
|   |   |-- tools.py               #   query_vector_memory()
|   |   +-- test.py
|   +-- 4_modeler/                 # Agent 4: Folium map visualization
|       |-- agent.py               #   LLM verification + system prompt
|       |-- tools.py               #   generate_impact_map()
|       |-- test.py                #   19 tests + LLM-as-a-Judge
|       +-- README.md              #   Module-specific documentation
|-- tests/
|   +-- test_harness.py            # Unified testing harness
|-- benchmark_results/             # Saved model benchmark data
|   |-- qwen2.5_7b.json
|   |-- llama3.1.json
|   +-- phi3.json
|-- data/
|   |-- historical_corpus.txt      # RAG corpus for ChromaDB
|   |-- output_maps/               # Generated HTML maps
|   +-- vector_db/                 # ChromaDB persistent storage
+-- logs/
    +-- system_run.log             # Observability trace log
```

---

## Configuration Reference

All configuration is centralized in the `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NASA_API_KEY` | Yes | `DEMO_KEY` | NASA NeoWs API key ([get one free](https://api.nasa.gov/)) |
| `OLLAMA_MODEL` | No | `qwen2.5:7b` | Ollama model name for all agents |

---

## Team Contributions

| Agent | Custom Tool | Key Responsibility |
|-------|-------------|-------------------|
| Telemetry Fetcher | `fetch_nasa_neo_data()` | Live NASA API integration |
| Trajectory Analyst | `calculate_kinetic_energy()` | First-principles physics |
| Semantic RAG Assessor | `query_vector_memory()` | ChromaDB vector search |
| Geospatial Synthesizer | `generate_impact_map()` | Interactive Folium map + LLM verification |
