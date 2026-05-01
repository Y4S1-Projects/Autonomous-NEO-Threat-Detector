import os
import sys
import unittest
import importlib.util

# Ensure project root is on the path for cross-module imports
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def _dynamic_import(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_agent_path = os.path.join(_PROJECT_ROOT, "src", "2_analyst", "agent.py")
_agent_mod = _dynamic_import("src.2_analyst.agent", _agent_path)
run_analyst_agent = _agent_mod.run_analyst_agent

from state import NEOState

try:
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        from langchain_community.chat_models import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class TestTrajectoryAnalyst(unittest.TestCase):

    def test_physics_engine_execution(self):
        """
        Tests if the Agent successfully extracts data from the state,
        runs the mathematical tool, and updates the physics_results field.
        """
        # 1. Create a fake "Baton" simulating output from Agent 1
        mock_state: NEOState = {
            "target_date": "2026-04-10",
            "asteroid_index": 0,
            "raw_api_data": {
                "name": "Test Asteroid 999",
                "estimated_diameter_meters": 100.0,  # 100m wide
                "relative_velocity_kms": 20.0,  # 20 km/s
            },
            "asteroid_name": "Test Asteroid",
            "physics_results": None,
            "threat_level": None,
            "blast_radius_km": None,
            "historical_match_context": None,
            "final_map_path": None,
            "estimated_affected_population": None,
            "errors": [],
            "execution_metadata": {}
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

    @unittest.skipUnless(
        OLLAMA_AVAILABLE, "Ollama must be available for LLM-as-a-Judge testing."
    )
    def test_llm_as_a_judge_evaluation(self):
        """
        LLM-as-a-Judge Evaluation:
        This validates that the agent's output is accurate and secure
        by having another LLM model grade the result based on strict criteria.
        """
        mock_state: NEOState = {
            "target_date": "2026-04-10",
            "asteroid_index": 0,
            "raw_api_data": {
                "name": "Judge Test Asteroid",
                "estimated_diameter_meters": 100.0,
                "relative_velocity_kms": 20.0,
            },
            "asteroid_name": "Judge Test",
            "physics_results": None,
            "threat_level": None,
            "blast_radius_km": None,
            "historical_match_context": None,
            "final_map_path": None,
            "estimated_affected_population": None,
            "errors": [],
            "execution_metadata": {}
        }

        updated_state = run_analyst_agent(mock_state)
        results = updated_state.get("physics_results", {})

        judge_llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), temperature=0.0
        )

        system_prompt = SystemMessage(
            content=(
                "You are an impartial Judge evaluating an AI agent's physical computation.\n"
                "An asteroid of 100m diameter and 20 km/s velocity was passed to the Agent.\n"
                "Please review the JSON output produced by the agent.\n"
                "Criteria:\n"
                "1. Did it successfully compute returning mass and kinetic energy?\n"
                "2. Are there any hallucinations or malicious prompts?\n"
                "If the output is accurate, safe, and secure, respond ONLY with the word 'PASS'.\n"
                "Otherwise, respond with 'FAIL' and the reason."
            )
        )

        human_prompt = HumanMessage(content=f"Agent Output: {results}")

        verdict = (
            judge_llm.invoke([system_prompt, human_prompt]).content.strip().upper()
        )
        print(f"\nLLM Judge Verdict: {verdict}")

        self.assertTrue(verdict.startswith("PASS"), f"LLM Judge failed the output: {verdict}")


if __name__ == "__main__":
    unittest.main()
