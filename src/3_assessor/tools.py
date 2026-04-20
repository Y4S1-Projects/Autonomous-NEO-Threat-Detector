import os
import chromadb
import logging
from typing import Dict


def _estimate_blast_radius_km(energy_joules: float) -> float:
    """
    Estimate blast radius from kinetic energy using a cube-root scaling law.

    Formula:
        radius_km = 2.0 * (yield_megatons)^(1/3)
        where yield_megatons = energy_joules / 4.184e15

    This keeps radii physically responsive to each asteroid's unique
    kinetic energy while remaining stable for visualization.
    """
    try:
        e = float(energy_joules)
    except (TypeError, ValueError):
        return 1.0

    if e <= 0:
        return 1.0

    yield_megatons = e / 4.184e15
    radius_km = 2.0 * (yield_megatons ** (1.0 / 3.0))

    # Clamp to avoid unrealistic extremes in rendering.
    return round(max(1.0, min(radius_km, 2000.0)), 2)


def query_vector_memory(energy_joules: float) -> Dict[str, str]:
    """
    Queries a local ChromaDB vector database to find the closest historical
    asteroid impact matching the current kinetic energy.

    If the database is empty, it automatically initializes and embeds
    the historical corpus from the local text file.

    Args:
        energy_joules (float): The calculated kinetic energy in Joules.

    Returns:
        Dict[str, str]: A dictionary containing the Threat Level,
                        Blast Radius (km), and Historical Context string.
    """
    logging.info("Tool executed: Querying Vector Memory (RAG).")

    # 1. Resolve local paths securely
    base_dir = os.path.dirname(__file__)
    db_path = os.path.abspath(os.path.join(base_dir, "../../data/vector_db"))
    corpus_path = os.path.abspath(
        os.path.join(base_dir, "../../data/historical_corpus.txt")
    )

    # 2. Initialize Local ChromaDB
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="historical_impacts")

    # 3. Auto-seed the database if it's empty (runs only on first execution)
    if collection.count() == 0:
        logging.info("Vector DB empty. Embedding historical corpus...")
        with open(corpus_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        ids = [f"doc_{i}" for i in range(len(lines))]
        # ChromaDB automatically handles the mathematical vector embeddings here!
        collection.add(documents=lines, ids=ids)

    # 4. Semantic Strategy: Convert the raw number into a semantic search query
    if energy_joules > 1e20:
        search_query = "massive kinetic energy planet-killer global extinction"
    elif energy_joules > 1e16:
        search_query = "megatons regional destruction flattened city"
    else:
        search_query = "kilotons airburst shattered windows minor damage"

    # 5. Perform the Vector Search
    results = collection.query(
        query_texts=[search_query],
        n_results=1,  # We only want the absolute closest match
    )

    best_match_text = results["documents"][0][0]

    # 6. Parse the structured text string from the DB
    # Example format: "ID: 123 | Threat: LOW | Blast Radius: 15 km | Context..."
    parts = [p.strip() for p in best_match_text.split("|")]

    threat = parts[1].split(":")[1].strip()
    context = parts[3].strip()

    # Blast radius must be asteroid-specific from actual kinetic energy,
    # not inherited from historical text snippets.
    radius_km = _estimate_blast_radius_km(energy_joules)

    return {
        "threat_level": threat,
        "blast_radius_km": radius_km,
        "historical_match_context": context,
    }
