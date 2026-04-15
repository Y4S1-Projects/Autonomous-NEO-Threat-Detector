import os
import requests
import logging
from typing import Dict, Any


def fetch_nasa_neo_data(target_date: str, asteroid_index: int = 0) -> Dict[str, Any]:
    """
    Fetches Near-Earth Object telemetry from the NASA API.

    This tool makes a synchronous HTTP GET request to the NeoWs endpoint.
    It sanitizes the massive JSON payload to return only the most critical
    data points (name, diameter, and velocity) for the asteroid at the 
    specified index (after sorting by max estimated diameter).

    Args:
        target_date (str): The date to query in 'YYYY-MM-DD' format.
        asteroid_index (int): The index of the asteroid to process for this run 
                              (default 0 means largest).

    Returns:
        Dict[str, Any]: A sanitized dictionary containing the asteroid's name,
                        estimated diameter (meters), and velocity (km/s).
                        Returns an error dictionary if the network fails or 
                        index is out of bounds.
    """
    # Use the DEMO_KEY by default, or an environment variable if set
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={target_date}&end_date={target_date}&api_key={api_key}"

    try:
        logging.info(f"Tool executed: Fetching NASA data for {target_date} (Index: {asteroid_index})")

        # Adding a 10-second timeout prevents the LangGraph pipeline from hanging forever
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        raw_asteroids = data.get("near_earth_objects", {}).get(target_date, [])

        if not raw_asteroids:
            return {"error": f"No asteroids found for date {target_date}"}
            
        # Sort by diameter, largest first to prioritize the biggest threats
        asteroids = sorted(
            raw_asteroids,
            key=lambda a: a.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0),
            reverse=True
        )
        
        if asteroid_index >= len(asteroids):
             return {"error": f"Asteroid index {asteroid_index} out of bounds (only {len(asteroids)} found)."}

        # Grab the requested asteroid in the list to analyze
        target_asteroid = asteroids[asteroid_index]

        sanitized_data = {
            "name": target_asteroid.get("name"),
            "estimated_diameter_meters": target_asteroid["estimated_diameter"][
                "meters"
            ]["estimated_diameter_max"],
            "relative_velocity_kms": target_asteroid["close_approach_data"][0][
                "relative_velocity"
            ]["kilometers_per_second"],
        }

        return sanitized_data

    except requests.exceptions.RequestException as e:
        logging.error(f"NASA API Connection Failed: {e}")
        return {"error": "Failed to connect to NASA API."}
