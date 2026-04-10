import unittest
import os
from agent import run_modeler_agent
from state import NEOState


class TestGeospatialModeler(unittest.TestCase):

    def test_html_map_generation(self):
        """
        Tests if the Agent successfully renders the Folium map
        and saves the HTML file to the correct directory.
        """
        # Create a mock state simulating data passed from Agent 3
        mock_state: NEOState = {
            "target_date": "2026-04-10",
            "raw_api_data": None,
            "physics_results": None,
            "threat_level": "MODERATE",
            "blast_radius_km": 50.0,
            "historical_match_context": "Test Context: Tunguska class event.",
            "final_map_path": None,
        }

        # Run the Agent
        updated_state = run_modeler_agent(mock_state)

        # 1. Assert the state contains a valid filepath string
        file_path = updated_state.get("final_map_path")
        self.assertIsNotNone(file_path)
        self.assertNotIn("ERROR", file_path)

        # 2. Assert the physical file actually exists on the computer
        self.assertTrue(os.path.exists(file_path))

        print(f"Test Passed! Map successfully saved at: {file_path}")
        print(
            "Go open the data/output_maps/simulation_latest.html file in your browser!"
        )


if __name__ == "__main__":
    unittest.main()
