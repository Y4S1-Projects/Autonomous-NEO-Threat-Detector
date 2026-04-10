import unittest
from agent import run_analyst_agent
from state import NEOState


class TestTrajectoryAnalyst(unittest.TestCase):

    def test_physics_engine_execution(self):
        """
        Tests if the Agent successfully extracts data from the state,
        runs the mathematical tool, and updates the physics_results field.
        """
        # 1. Create a fake "Baton" simulating output from Agent 1
        mock_state: NEOState = {
            "target_date": "2026-04-10",
            "raw_api_data": {
                "name": "Test Asteroid 999",
                "estimated_diameter_meters": 100.0,  # 100m wide
                "relative_velocity_kms": 20.0,  # 20 km/s
            },
            "physics_results": None,
            "threat_level": None,
            "blast_radius_km": None,
            "historical_match_context": None,
            "final_map_path": None,
        }

        # 2. Run the Analyst Agent node
        updated_state = run_analyst_agent(mock_state)

        # 3. Assertions
        results = updated_state.get("physics_results")

        self.assertIsNotNone(results)
        self.assertNotIn("error", results)
        self.assertIn("kinetic_energy_joules", results)

        # A 100m asteroid at 20km/s should have roughly 3.14e14 Joules of energy
        self.assertGreater(results["kinetic_energy_joules"], 0.0)

        print(
            f"Test Passed! Calculated Energy: {results['kinetic_energy_joules']:e} Joules"
        )


if __name__ == "__main__":
    unittest.main()
