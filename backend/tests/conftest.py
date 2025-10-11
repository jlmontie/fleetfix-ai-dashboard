"""
Pytest configuration and fixtures for FleetFix AI Dashboard tests
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
# Look for .env in the project root (one level up from backend)
project_root = backend_dir.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment variables from {env_file}")
else:
    # If no .env file, try to load from backend directory
    backend_env = backend_dir / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)
        print(f"✓ Loaded environment variables from {backend_env}")
    else:
        print("⚠ No .env file found - using system environment variables only")
        print(f"  Looked in: {env_file}")
        print(f"  Looked in: {backend_env}")

# Set default environment variables for testing if not present
if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    print("⚠ No API keys found in environment variables")
    print("  Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run AI agent tests")
