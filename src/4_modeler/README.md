# Module 4: The Geospatial Synthesizer 🌍

**Owner:** Member 4 (Frontend & Geospatial Modeler)  
**Role:** Transform technical pipeline data into an interactive visual artifact

---

## Objective

The Geospatial Synthesizer is the final agent in the AstroGuard pipeline. It consumes all upstream data — NASA telemetry, physics calculations, and RAG-retrieved historical context — and produces a professional, interactive HTML map that serves as the pipeline's visual output.

## Architecture

```
State Input:                          Tool Output:
  blast_radius_km  ──┐
  threat_level     ──┤── generate_impact_map() ──→ simulation_latest.html
  historical_context ┤
  asteroid_name    ──┘
```

## Deliverables

### 1. `tools.py` — `generate_impact_map()`

**Purpose:** Render an interactive Folium/Leaflet map with:

- **Multiple tile layers** — Dark Mode, Street Map, Light Mode with layer switcher
- **Graduated blast zones** — Kill Zone (30%), Damage Zone (70%), Shockwave Zone (100%)
- **Color-coded styling** — Amber (LOW), Deep Orange (MODERATE), Dark Red (HIGH)
- **Rich HTML popup** — Structured threat intelligence with historical context
- **Floating legend** — Threat classification scale with active indicator
- **Title overlay** — Asteroid designation and simulation label
- **MiniMap plugin** — Navigation context for zoomed views

**Type Hinting:** Full Python type annotations on all functions including `Optional`, `Dict`, `Tuple`.  
**Error Handling:** Input validation, type coercion, negative value clamping, graceful error strings.  
**Docstrings:** Comprehensive Google-style docstrings with Args, Returns, and Example sections.

### 2. `agent.py` — Geospatial Synthesizer Agent

**System Prompt:**

> "You are a geospatial rendering verification engine for the AstroGuard planetary defense system. You MUST NOT invent, estimate, or hallucinate any scientific data. Your ONLY job is to confirm that the rendering tool produced a valid output file and provide a brief, factual summary."

**LLM Integration:**

- Uses Ollama (phi3) for a post-rendering **verification step**
- The LLM does NOT generate the map — it validates the tool's output
- Graceful fallback if Ollama is unavailable

**Observability:**

- Logs agent activation, state extraction, tool execution, and completion
- Records execution metadata (timestamps, duration, status) in the global state

### 3. `test.py` — Comprehensive Hybrid Test Suite (18 test cases)

| Category           | Tests | Description                                                  |
| ------------------ | ----- | ------------------------------------------------------------ |
| Happy Path         | 3     | All three threat levels (LOW, MODERATE, HIGH)                |
| Edge Cases         | 5     | Negative/zero radius, invalid types, unknown threat levels   |
| Content Validation | 3     | HTML structure, data embedding, Leaflet presence             |
| Helper Functions   | 4     | Zoom scaling, style lookup, coordinate selection, popup HTML |
| LLM-as-a-Judge     | 2     | Accuracy evaluation + mismatch detection                     |

## Challenges Faced

1. **Numeric directory names** — Python doesn't allow `import src.4_modeler`, requiring `importlib` for dynamic imports
2. **Ollama availability** — Not all team machines have Ollama running, so all LLM interactions use graceful fallbacks
3. **Map rendering consistency** — Ocean coordinates are randomized for realism, requiring zoom-level auto-calculation
