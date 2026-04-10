import os
import folium
import logging


def generate_impact_map(
    radius_km: float, threat_level: str, historical_context: str
) -> str:
    """
    Renders an interactive HTML map visualizing the theoretical asteroid impact zone.

    Generates a map centered on a hypothetical Pacific Ocean coordinate. It draws
    a color-coded blast radius and embeds the RAG-retrieved historical context
    into an interactive popup.

    Args:
        radius_km (float): The theoretical blast radius in kilometers.
        threat_level (str): The classification (LOW, MODERATE, HIGH).
        historical_context (str): The context string retrieved from the Vector DB.

    Returns:
        str: The absolute file path to the generated HTML simulation file.
    """
    logging.info("Tool executed: Generating Folium Geospatial Map.")

    try:
        # 1. Define a hypothetical impact coordinate (Central Pacific Ocean)
        impact_lat = 0.0
        impact_lon = -120.0

        # 2. Determine visual styling based on the Threat Level
        color_map = {"LOW": "orange", "MODERATE": "red", "HIGH": "darkred"}
        zone_color = color_map.get(threat_level, "blue")

        # 3. Initialize the Map (Zoomed out to see the whole planet/ocean)
        simulation_map = folium.Map(
            location=[impact_lat, impact_lon],
            zoom_start=3,
            tiles="CartoDB positron",  # Clean, dark-mode style map
        )

        # 4. Draw the Blast Radius (Folium uses meters for circle radius)
        radius_meters = float(radius_km) * 1000.0

        folium.Circle(
            radius=radius_meters,
            location=[impact_lat, impact_lon],
            popup=f"<b>Threat: {threat_level}</b><br><hr>{historical_context}",
            color=zone_color,
            fill=True,
            fill_color=zone_color,
            fill_opacity=0.4,
        ).add_to(simulation_map)

        # 5. Add a central marker for the exact impact point
        folium.Marker(
            location=[impact_lat, impact_lon],
            icon=folium.Icon(color="black", icon="info-sign"),
            tooltip="Hypothetical Impact Ground Zero",
        ).add_to(simulation_map)

        # 6. Save the file
        base_dir = os.path.dirname(__file__)
        output_dir = os.path.abspath(os.path.join(base_dir, "../../data/output_maps"))

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Name the file dynamically
        file_path = os.path.join(output_dir, "simulation_latest.html")
        simulation_map.save(file_path)

        logging.info(f"Map successfully rendered and saved to {file_path}")
        return file_path

    except Exception as e:
        logging.error(f"Geospatial rendering failed: {e}")
        return "ERROR: Rendering failed."
