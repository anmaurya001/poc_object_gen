import os
from pathlib import Path

# Directory paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "generated_assets"
PROMPTS_FILE = BASE_DIR / "prompts.json"

# TRELLIS pipeline settings
TRELLIS_MODEL = "JeffreyXiang/TRELLIS-text-large"
SPCONV_ALGO = "native"

# INITIAL MESSAGE
INITIAL_MESSAGE = "Hello! I'm your helpful scene planning assistant. Please describe the scene you'd like to create."

# Generation parameters
DEFAULT_SEED = 42
DEFAULT_SPARSE_STEPS = 25
DEFAULT_SLAT_STEPS = 25
DEFAULT_CFG_STRENGTH = 7.0

# Agent settings
AGENT_MODEL = "meta/llama-3.1-8b-instruct"
AGENT_BASE_URL = "http://localhost:8000/v1"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
