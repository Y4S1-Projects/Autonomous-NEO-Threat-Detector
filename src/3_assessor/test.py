import unittest
from agent import run_rag_assessor_agent
from state import NEOState


class TestRAGAssessor(unittest.TestCase):

    def test_vector_database_retrieval(self):
        """
        Tests if the Agent successfully triggers ChromaDB, retrieves the
        correct semantic match based on the energy scale, and updates the state.
        """
        # Create a mock state simulating a massive planet-killer asteroid
        mock_state: NEOState = {
            "target_date": "2026-04-10",
            "raw_api_data": None,
            "physics_results": {"kinetic_energy_joules": 5.0e23},  # Huge energy
            "threat_level": None,
            "blast_radius_km": None,
            "historical_match_context": None,
            "final_map_path": None,
        }

        # Run the Agent
        updated_state = run_rag_assessor_agent(mock_state)

        # Assertions
        self.assertEqual(updated_state["threat_level"], "HIGH")
        self.assertIsNotNone(updated_state["blast_radius_km"])
        self.assertIn("Chicxulub", updated_state["historical_match_context"])

        print(f"Test Passed! Threat: {updated_state['threat_level']}")
        print(f"Retrieved Context: {updated_state['historical_match_context']}")


if __name__ == "__main__":
    unittest.main()
