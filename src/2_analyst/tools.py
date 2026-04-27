import math
import logging
from typing import Dict
from langchain_core.tools import tool


@tool
def calculate_kinetic_energy(
    diameter_meters: float, velocity_kms: float
) -> Dict[str, float]:
    """
    Calculates the mass and kinetic energy of a Near-Earth Object based on first principles.
    
    Assumes the asteroid is roughly spherical and composed of standard
    stony chondrite material with a density of 3000 kg/m^3.

    Args:
        diameter_meters (float): Estimated diameter in meters.
        velocity_kms (float): Relative velocity in kilometers per second.

    Returns:
        Dict[str, float]: A dictionary containing the calculated mass (kg)
                          and kinetic energy (Joules).
    """
    try:
        logging.info("Tool executed: Calculating physics metrics.")

        # 1. Sanitize inputs to prevent LLM string-passing errors
        d = float(diameter_meters)
        v_kms = float(velocity_kms)

        # 2. Calculate Volume (Sphere) -> 4/3 * pi * r^3
        radius = d / 2.0
        volume = (4.0 / 3.0) * math.pi * (radius**3)

        # 3. Calculate Mass (Density = Mass/Volume) -> Mass = Volume * 3000 kg/m^3
        density_kg_m3 = 3000.0
        mass_kg = volume * density_kg_m3

        # 4. Calculate Kinetic Energy -> 0.5 * m * v^2
        # Must convert velocity to meters per second first
        v_ms = v_kms * 1000.0
        kinetic_energy_joules = 0.5 * mass_kg * (v_ms**2)

        results = {
            "mass_kg": round(mass_kg, 2),
            "kinetic_energy_joules": round(kinetic_energy_joules, 2),
        }

        logging.info(
            f"Physics calculation successful: {kinetic_energy_joules:e} Joules"
        )
        return results

    except Exception as e:
        logging.error(f"Physics engine failed: {e}")
        return {"error": 0.0}
