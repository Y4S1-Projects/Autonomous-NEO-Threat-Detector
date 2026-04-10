import unittest
from tools import fetch_nasa_neo_data


class TestTelemetryFetcher(unittest.TestCase):

    def test_successful_api_fetch(self):
        """
        Property-Based Test: Asserts that the tool successfully connects
        to NASA and returns a dictionary with the required 'name' key.
        """
        # We test with a known date
        test_date = "2026-04-10"
        result = fetch_nasa_neo_data(test_date)

        # 1. Assert the function didn't crash and returned a dictionary
        self.assertIsInstance(result, dict)

        # 2. Assert it didn't return our custom error message
        self.assertNotIn("error", result)

        # 3. Assert the sanitized data contains the required float/string keys
        self.assertIn("name", result)
        self.assertIn("estimated_diameter_meters", result)
        self.assertIn("relative_velocity_kms", result)

        print(f"Test Passed! Extracted Asteroid: {result['name']}")


if __name__ == "__main__":
    unittest.main()
