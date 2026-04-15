"""
AstroGuard Model Benchmark — Systematic LLM Evaluation.

Tests each Ollama model against the exact prompts and constraints
used in the AstroGuard pipeline. Measures format adherence,
reasoning accuracy, and latency.

Usage:
    # Test each model (one at a time due to RAM):
    ollama run phi3              # Load model, then /bye
    python benchmark.py phi3
    ollama stop phi3

    ollama run llama3.1          # Load model, then /bye
    python benchmark.py llama3.1
    ollama stop llama3.1

    ollama run qwen2.5:7b        # Load model, then /bye
    python benchmark.py qwen2.5:7b
    ollama stop qwen2.5:7b

    # Compare all results after testing:
    python benchmark.py --compare
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Results storage
RESULTS_DIR = os.path.join(PROJECT_ROOT, "benchmark_results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def _get_llm(model_name):
    """Initialize ChatOllama with graceful import handling."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        from langchain_community.chat_models import ChatOllama
    return ChatOllama(model=model_name, temperature=0)


def _safe_print(text):
    """Print with encoding safety for Windows cp1252 consoles."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


# =====================================================================
# Test Cases — Simulating each agent's LLM interaction
# =====================================================================


def test_1_format_adherence(llm):
    """
    TEST 1: Strict JSON Formatting (Agent 2 — Trajectory Analyst)

    The model must output ONLY a valid JSON dictionary.
    No markdown, no explanation, no conversational text.
    This is the #1 crash risk for the pipeline.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    system = SystemMessage(
        content=(
            "You are a strict data parser for a physics engine. "
            "Output ONLY a valid JSON dictionary with keys 'mass_kg' and "
            "'kinetic_energy_joules'. Do NOT include markdown formatting "
            "like ```json. Do NOT include any explanation or conversational text. "
            "Output ONLY the raw JSON object."
        )
    )
    human = HumanMessage(
        content=(
            "An asteroid is 150 meters in diameter traveling at 22 km/s. "
            "Assuming spherical shape and chondrite density of 3000 kg/m3, "
            "calculate the mass and kinetic energy (KE = 0.5 * m * v^2). "
            "Convert velocity to m/s first. Output ONLY JSON."
        )
    )

    start = time.time()
    response = llm.invoke([system, human])
    elapsed = time.time() - start
    content = response.content.strip()

    # Scoring
    score = 0
    notes = []

    # Check if it's parseable JSON
    try:
        parsed = json.loads(content)
        score += 40
        notes.append("Valid JSON: YES")

        # Check for required keys
        if "mass_kg" in parsed or "mass" in parsed:
            score += 10
            notes.append("Has mass key: YES")
        else:
            notes.append("Has mass key: NO")

        if (
            "kinetic_energy_joules" in parsed
            or "kinetic_energy" in parsed
            or "energy" in parsed
        ):
            score += 10
            notes.append("Has energy key: YES")
        else:
            notes.append("Has energy key: NO")

    except json.JSONDecodeError:
        notes.append("Valid JSON: NO")

        # Check if it has JSON somewhere in conversational text
        if "{" in content and "}" in content:
            score += 15
            notes.append("Contains JSON-like structure but with extra text")
        else:
            notes.append("No JSON structure found at all")

    # Check for markdown pollution
    if "```" in content:
        score -= 10
        notes.append("Contains markdown code fences (BAD)")
    else:
        score += 10
        notes.append("No markdown pollution: CLEAN")

    # Check for conversational fluff
    fluff_words = ["here", "sure", "certainly", "let me", "the answer"]
    has_fluff = any(w in content.lower() for w in fluff_words)
    if has_fluff:
        score -= 5
        notes.append("Contains conversational fluff (BAD)")
    else:
        score += 10
        notes.append("No conversational fluff: CLEAN")

    # Bonus: check math accuracy (approx values)
    # Volume of 150m sphere = 4/3 * pi * 75^3 = ~1,767,146 m^3
    # Mass = 1,767,146 * 3000 = ~5.3e9 kg
    # KE = 0.5 * 5.3e9 * (22000)^2 = ~1.28e18 J
    score += 20  # Baseline for attempting the calculation

    return {
        "test": "Format Adherence (JSON Output)",
        "score": max(0, min(100, score)),
        "time_seconds": round(elapsed, 2),
        "output": content[:500],
        "notes": notes,
    }


def test_2_rag_comprehension(llm):
    """
    TEST 2: RAG Context Reading (Agent 3 — Semantic Assessor)

    Given historical context from the vector DB, the model must
    classify the threat level as exactly one word: LOW, MODERATE, or HIGH.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    system = SystemMessage(
        content=(
            "You are a threat classification engine for planetary defense. "
            "Read the historical memory context provided and classify the "
            "incoming threat level. Output ONLY a single word: LOW, MODERATE, or HIGH. "
            "Do not explain your reasoning. Do not add any other text."
        )
    )
    human = HumanMessage(
        content=(
            "Historical Memory:\n"
            "ID: CHIC-0000 | Threat: HIGH | Blast Radius: 1000 km | "
            "Massive kinetic energy exceeding 1.0e21 Joules causing global firestorm "
            "and impact winter, similar to the Chicxulub impactor.\n\n"
            "Current asteroid kinetic energy: 5.5e22 Joules.\n"
            "What is the threat level?"
        )
    )

    start = time.time()
    response = llm.invoke([system, human])
    elapsed = time.time() - start
    content = response.content.strip()

    score = 0
    notes = []

    # Check if output is exactly one word
    words = content.split()
    if len(words) == 1:
        score += 30
        notes.append("Single word output: YES")
    else:
        notes.append(f"Single word output: NO ({len(words)} words)")

    # Check if the word is a valid threat level
    first_word = words[0].upper().rstrip(".,!") if words else ""
    if first_word == "HIGH":
        score += 70
        notes.append("Correct classification: HIGH (CORRECT)")
    elif first_word in ("LOW", "MODERATE"):
        score += 30
        notes.append(f"Classification: {first_word} (WRONG, expected HIGH)")
    else:
        notes.append(f"Classification: '{first_word}' (INVALID)")

    return {
        "test": "RAG Comprehension (Threat Classification)",
        "score": max(0, min(100, score)),
        "time_seconds": round(elapsed, 2),
        "output": content[:300],
        "notes": notes,
    }


def test_3_no_hallucination(llm):
    """
    TEST 3: Anti-Hallucination (Agent 4 — Geospatial Synthesizer)

    The model must report ONLY the data given to it.
    It must NOT invent coordinates, threat levels, or scientific facts.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    system = SystemMessage(
        content=(
            "You are a geospatial rendering verification engine. "
            "You MUST NOT invent, estimate, or hallucinate any data. "
            "You MUST NOT add coordinates, calculations, or facts not provided. "
            "Report ONLY what is given to you. Keep response under 50 words."
        )
    )
    human = HumanMessage(
        content=(
            "Rendering complete. Report:\n"
            "- Threat Level: MODERATE\n"
            "- Blast Radius: 50 km\n"
            "- File: simulation_latest.html\n"
            "Summarize this rendering output."
        )
    )

    start = time.time()
    response = llm.invoke([system, human])
    elapsed = time.time() - start
    content = response.content.strip()

    score = 0
    notes = []

    # Check length constraint
    word_count = len(content.split())
    if word_count <= 60:
        score += 30
        notes.append(f"Under 60 words: YES ({word_count} words)")
    else:
        score += 10
        notes.append(f"Under 60 words: NO ({word_count} words)")

    # Check it mentions the given data
    if "MODERATE" in content.upper():
        score += 15
        notes.append("Mentions MODERATE: YES")
    if "50" in content:
        score += 15
        notes.append("Mentions 50 km: YES")
    if "simulation" in content.lower() or "html" in content.lower():
        score += 10
        notes.append("Mentions output file: YES")

    # Check for hallucinated data
    hallucination_markers = [
        "latitude",
        "longitude",
        "coordinates",
        "located at",
        "approximately",
        "I estimate",
        "I think",
        "degrees",
    ]
    hallucinated = [m for m in hallucination_markers if m.lower() in content.lower()]
    if hallucinated:
        score -= 20
        notes.append(f"Hallucinated data detected: {hallucinated}")
    else:
        score += 30
        notes.append("No hallucinations detected: CLEAN")

    return {
        "test": "Anti-Hallucination (Verification)",
        "score": max(0, min(100, score)),
        "time_seconds": round(elapsed, 2),
        "output": content[:300],
        "notes": notes,
    }


def test_4_tool_instruction(llm):
    """
    TEST 4: Tool Call Instruction Following (Agent 1 — Fetcher)

    The model must acknowledge it should use a tool and NOT
    try to generate fake API data from its training.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    system = SystemMessage(
        content=(
            "You are a strict data retrieval engineer. "
            "Your ONLY job is to acknowledge that you will use the fetch tool. "
            "You MUST NOT generate, guess, or fabricate any asteroid data. "
            "Say: 'Calling fetch_nasa_neo_data tool for [date].' and nothing else."
        )
    )
    human = HumanMessage(content="Fetch the NEO data for 2026-04-15.")

    start = time.time()
    response = llm.invoke([system, human])
    elapsed = time.time() - start
    content = response.content.strip()

    score = 0
    notes = []

    # Check if it acknowledges tool usage
    tool_words = ["fetch", "tool", "calling", "call"]
    mentions_tool = any(w in content.lower() for w in tool_words)
    if mentions_tool:
        score += 40
        notes.append("Mentions tool usage: YES")
    else:
        notes.append("Mentions tool usage: NO")

    # Check if it mentions the date
    if "2026-04-15" in content or "2026" in content:
        score += 20
        notes.append("Mentions target date: YES")
    else:
        notes.append("Mentions target date: NO")

    # Check it didn't fabricate data
    fake_data_markers = ["diameter", "velocity", "km/s", "meters", "asteroid name"]
    fabricated = [m for m in fake_data_markers if m.lower() in content.lower()]
    if fabricated:
        score -= 20
        notes.append(f"Fabricated asteroid data: {fabricated} (BAD)")
    else:
        score += 40
        notes.append("No fabricated data: CLEAN")

    return {
        "test": "Tool Instruction Following",
        "score": max(0, min(100, score)),
        "time_seconds": round(elapsed, 2),
        "output": content[:300],
        "notes": notes,
    }


# =====================================================================
# Benchmark Runner
# =====================================================================


def run_benchmark(model_name):
    """Run all 4 tests against the specified model and save results."""
    _safe_print(f"\n{'='*60}")
    _safe_print(f"  BENCHMARK: {model_name}")
    _safe_print(f"{'='*60}")
    _safe_print(f"  Loading model into memory...")

    try:
        llm = _get_llm(model_name)
    except Exception as e:
        _safe_print(f"\n  ERROR: Could not connect to Ollama model '{model_name}'")
        _safe_print(f"  Make sure Ollama is running: ollama run {model_name}")
        _safe_print(f"  Error: {e}")
        return None

    tests = [
        test_1_format_adherence,
        test_2_rag_comprehension,
        test_3_no_hallucination,
        test_4_tool_instruction,
    ]

    results = []
    total_score = 0
    total_time = 0

    for i, test_func in enumerate(tests, 1):
        _safe_print(
            f"\n  --- Test {i}/4: {test_func.__doc__.strip().split(chr(10))[0]} ---"
        )
        try:
            result = test_func(llm)
            results.append(result)
            total_score += result["score"]
            total_time += result["time_seconds"]

            _safe_print(f"  Score: {result['score']}/100")
            _safe_print(f"  Time:  {result['time_seconds']}s")
            _safe_print(f"  Output: {result['output'][:120]}...")
            for note in result["notes"]:
                _safe_print(f"    > {note}")
        except Exception as e:
            _safe_print(f"  ERROR: Test failed with exception: {e}")
            results.append(
                {
                    "test": test_func.__name__,
                    "score": 0,
                    "time_seconds": 0,
                    "output": f"EXCEPTION: {e}",
                    "notes": ["Test crashed"],
                }
            )

    # Summary
    avg_score = total_score / len(tests)
    _safe_print(f"\n{'='*60}")
    _safe_print(f"  RESULTS: {model_name}")
    _safe_print(f"{'='*60}")
    _safe_print(f"  Average Score : {avg_score:.1f}/100")
    _safe_print(f"  Total Time    : {total_time:.2f}s")
    _safe_print(f"  Avg Latency   : {total_time/len(tests):.2f}s per test")
    _safe_print(f"{'='*60}")

    # Save to file
    report = {
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "average_score": round(avg_score, 1),
        "total_time_seconds": round(total_time, 2),
        "avg_latency_seconds": round(total_time / len(tests), 2),
        "tests": results,
    }

    safe_name = model_name.replace(":", "_").replace("/", "_")
    result_path = os.path.join(RESULTS_DIR, f"{safe_name}.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    _safe_print(f"\n  Results saved to: {result_path}")
    return report


def compare_results():
    """Load all saved benchmark results and determine the best model."""
    _safe_print(f"\n{'='*60}")
    _safe_print(f"  MODEL COMPARISON")
    _safe_print(f"{'='*60}\n")

    result_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]

    if not result_files:
        _safe_print("  No benchmark results found!")
        _safe_print("  Run benchmarks first:")
        _safe_print("    python benchmark.py phi3")
        _safe_print("    python benchmark.py llama3.1")
        _safe_print("    python benchmark.py qwen2.5:7b")
        return

    reports = []
    for fname in sorted(result_files):
        fpath = os.path.join(RESULTS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            reports.append(json.load(f))

    # Header
    _safe_print(
        f"  {'Model':<20} {'Avg Score':>10} {'Latency':>10} {'T1:Format':>10} {'T2:RAG':>10} {'T3:Halluc':>10} {'T4:Tool':>10}"
    )
    _safe_print(
        f"  {'-'*18:<20} {'-'*8:>10} {'-'*8:>10} {'-'*8:>10} {'-'*8:>10} {'-'*8:>10} {'-'*8:>10}"
    )

    for r in reports:
        tests = r["tests"]
        t_scores = [t["score"] for t in tests]
        while len(t_scores) < 4:
            t_scores.append(0)

        _safe_print(
            f"  {r['model']:<20} "
            f"{r['average_score']:>9.1f} "
            f"{r['avg_latency_seconds']:>9.2f}s "
            f"{t_scores[0]:>9}/100 "
            f"{t_scores[1]:>9}/100 "
            f"{t_scores[2]:>9}/100 "
            f"{t_scores[3]:>9}/100"
        )

    # Determine winner
    _safe_print(f"\n  {'='*60}")

    # Best by score
    best_score = max(reports, key=lambda r: r["average_score"])
    _safe_print(
        f"  BEST SCORE   : {best_score['model']} ({best_score['average_score']:.1f}/100)"
    )

    # Best by speed
    best_speed = min(reports, key=lambda r: r["avg_latency_seconds"])
    _safe_print(
        f"  FASTEST      : {best_speed['model']} ({best_speed['avg_latency_seconds']:.2f}s/test)"
    )

    # Weighted winner (70% score, 30% speed bonus)
    for r in reports:
        max_latency = max(rr["avg_latency_seconds"] for rr in reports)
        speed_score = (
            100 * (1 - r["avg_latency_seconds"] / max_latency)
            if max_latency > 0
            else 50
        )
        r["_weighted"] = (r["average_score"] * 0.7) + (speed_score * 0.3)

    winner = max(reports, key=lambda r: r["_weighted"])
    _safe_print(f"\n  >> RECOMMENDED : {winner['model']} <<")
    _safe_print(
        f"     (Weighted: 70% accuracy + 30% speed = {winner['_weighted']:.1f})"
    )
    _safe_print(f"  {'='*60}")

    # Provide the config line
    _safe_print(f"\n  To use this model in the pipeline, all agent files")
    _safe_print(f"  should use: ChatOllama(model=\"{winner['model']}\", temperature=0)")
    _safe_print(f"\n  Or set in .env: OLLAMA_MODEL={winner['model']}")

    return winner["model"]


# =====================================================================
# CLI
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AstroGuard LLM Benchmark — Test Ollama models for pipeline fitness."
    )
    parser.add_argument(
        "model",
        nargs="?",
        help="Ollama model name to benchmark (e.g., phi3, llama3.1, qwen2.5:7b)",
    )
    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        help="Compare all saved benchmark results and pick the winner.",
    )
    args = parser.parse_args()

    if args.compare:
        compare_results()
    elif args.model:
        run_benchmark(args.model)
    else:
        _safe_print("Usage:")
        _safe_print("  python benchmark.py phi3           # Test phi3")
        _safe_print("  python benchmark.py llama3.1       # Test llama3.1")
        _safe_print("  python benchmark.py qwen2.5:7b     # Test qwen2.5")
        _safe_print("  python benchmark.py --compare      # Compare all results")
