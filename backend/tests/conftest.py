"""Test environment. Runs before any app module is imported.

Tests never touch the development database and never call a real LLM.
"""

import os

os.environ["TRIAGE_PROVIDER"] = "simulated"
os.environ["SIMULATED_FAILURE_RATE"] = "0.0"
os.environ["POSTGRES_DB"] = os.environ.get("POSTGRES_TEST_DB", "civicpulse_test")
