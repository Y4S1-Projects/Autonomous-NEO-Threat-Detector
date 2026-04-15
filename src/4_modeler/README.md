# Module 4 — Geospatial Synthesizer (Agent 4)

> **Advanced impact simulation engine with population analysis, temporal animation, and self-correcting behavior.**

## Overview

The Geospatial Synthesizer is the final agent in the AstroGuard pipeline. It consumes the accumulated threat intelligence from all upstream agents and produces an interactive HTML map simulating a theoretical asteroid impact.

This module goes beyond simple visualization — it implements **three advanced capabilities** that demonstrate true agentic reasoning:

| Feature                          | What It Does                                                    | Why It Matters                     |
| -------------------------------- | --------------------------------------------------------------- | ---------------------------------- |
| **Population Impact Estimation** | Haversine-based proximity analysis against 200+ world cities    | Data synthesis, not just rendering |
| **Temporal Blast Animation**     | Expanding shockwave with playable timeline (TimestampedGeoJson) | Military-grade visual simulation   |
| **Self-Correction Loop**         | Validates HTML output + retries on failure (max 2 retries)      | Self-Reflective MAS Architecture   |

---

## Architecture

```
State Input (from Agents 1-3)
    |
    ├── blast_radius_km
    ├── threat_level
    ├── historical_match_context
    └── asteroid_name
    |
    v
+-------------------------------+
|   generate_impact_map()       |
|   ├── _select_impact_coordinate()      |
|   ├── _estimate_affected_population()  |  <-- Haversine + CSV
|   ├── _build_blast_animation_geojson() |  <-- TimestampedGeoJson
|   ├── _build_popup_html()              |  <-- With population data
|   ├── _build_population_hud()          |  <-- Floating HUD
|   └── _build_legend_html()             |
+-------------------------------+
    |
    v
+-------------------------------+
|   Self-Correction Loop        |
|   ├── _validate_map_output()  |  <-- Read HTML, verify content
|   ├── Retry if data missing   |
|   └── Max 2 retries           |
+-------------------------------+
    |
    v
+-------------------------------+
|   LLM Verification            |
|   └── Qwen 2.5 confirms data |  <-- Including population stats
+-------------------------------+
    |
    v
State Output:
    ├── final_map_path
    └── estimated_affected_population
```

---

## Key Algorithms

### Haversine Formula

Used to calculate the great-circle distance between the impact site and each city in the dataset:

```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
d = R × c    (R = 6,371 km)
```

**Validated**: London to Paris = 343.6 km (actual: ~344 km)

### Population Estimation Pipeline

1. Load `data/worldcities_top500.csv` (200+ cities with lat/lon/population)
2. For each city, compute Haversine distance to impact site
3. If distance ≤ blast_radius_km → add to affected list
4. Sum populations and sort by proximity
5. Display in popup, legend, and floating HUD

### Temporal Animation

- Generates 10 GeoJSON frames representing expanding blast wave
- Each frame is a polygon circle at 5% → 100% of blast radius
- Uses Folium's `TimestampedGeoJson` plugin for playable timeline
- Animation auto-plays on map load with loop control

---

## Files

| File       | Lines | Description                                                               |
| ---------- | ----- | ------------------------------------------------------------------------- |
| `tools.py` | ~700  | Core tool with Haversine, population estimation, animation, map rendering |
| `agent.py` | ~280  | LangGraph node with self-correction loop and LLM verification             |
| `test.py`  | ~590  | 35 test cases across 9 test classes                                       |

---

## Test Suite

```bash
python src/4_modeler/test.py
```

| Category               | Tests  | Description                                           |
| ---------------------- | ------ | ----------------------------------------------------- |
| Happy Path             | 3      | LOW, MODERATE, HIGH threat level maps                 |
| Edge Cases             | 7      | Invalid/extreme inputs, graceful degradation          |
| Content Validation     | 4      | HTML structure, animation data, threat embedding      |
| Helper Functions       | 4      | Zoom, styles, coordinates, popup builder              |
| **Population Impact**  | 6      | Haversine formula, city proximity, sorting            |
| **Temporal Animation** | 4      | GeoJSON structure, frames, timestamps, geometry       |
| **Self-Correction**    | 3      | File validation, missing file detection, wrong threat |
| **Population HUD**     | 2      | Empty/populated HUD rendering                         |
| **LLM-as-a-Judge**     | 2      | Accuracy evaluation, mismatch detection               |
| **Total**              | **35** | All passing                                           |

---

## Dependencies

- `folium` — Map rendering and plugins
- `folium.plugins.TimestampedGeoJson` — Temporal animation
- `folium.plugins.MiniMap` — Navigation minimap
- `langchain-ollama` — LLM verification (graceful fallback)

## Data Files

- `data/worldcities_top500.csv` — 200+ world cities with lat, lon, population (public domain)
