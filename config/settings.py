"""
Oil Spill Impact Estimator Configuration
----------------------------------------
This module contains configuration settings and constants for the
Oil Spill Impact Estimator application.
"""

import os
from pathlib import Path

# Project Structure
# -----------------
# Root directory of the project
ROOT_DIR = Path(__file__).parents[1]

# Data directory
DATA_DIR = ROOT_DIR / 'data'

# Results directory
RESULTS_DIR = ROOT_DIR / 'results'

# Default file paths
DEFAULT_OIL_TYPES_FILE = DATA_DIR / 'oil_types.json'
DEFAULT_SAMPLE_DATA_FILE = DATA_DIR / 'sample_spills.csv'

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Dispersal Model Settings
# -----------------------
# Default time for dispersal simulation (hours)
DEFAULT_SIMULATION_TIME_HOURS = 24

# Default environmental conditions
DEFAULT_WIND_SPEED_KMH = 10.0
DEFAULT_WATER_TEMP_C = 15.0
DEFAULT_WAVE_HEIGHT_M = 0.5

# Coefficients for Fay's spreading equation
FAY_CONSTANT = 1.45

# Maximum fraction of oil that can evaporate
MAX_EVAPORATION_FRACTION = 0.9

# Maximum fraction of oil that can dissolve
MAX_DISSOLUTION_FRACTION = 0.2

# Default environmental sensitivity factor
DEFAULT_ENVIRONMENTAL_SENSITIVITY = 1.0

# Visualization Settings
# ---------------------
# Default map settings
DEFAULT_MAP_ZOOM = 8
DEFAULT_MAP_TILE = 'CartoDB positron'

# Oil spill color scheme
OIL_SPILL_COLORS = {
    'surface': '#782D2D',  # Dark reddish brown
    'edge': '#8E4E27',     # Medium brown
    'thin': '#E8A238',     # Light brown
    'sheen': '#FFF5B8'     # Pale yellow
}

# Chart color scheme
CHART_COLORS = {
    'evaporated': '#f4d166',  # Yellow
    'dissolved': '#5fa3db',   # Blue
    'surface': '#d93b48',     # Red
    'cleanup': '#8e7cc3',     # Purple
    'wildlife': '#6aa84f',    # Green
    'economic': '#f1c232'     # Gold
}

# Location type definitions
LOCATION_TYPES = [
    'open_ocean',
    'coastal',
    'estuary',
    'reef',
    'wetland',
    'river',
    'port'
]

# Cleanup Methods
CLEANUP_METHODS = [
    'mechanical',        # Physical removal with skimmers, etc.
    'dispersant',        # Chemical dispersants
    'burning',           # Controlled burning of oil
    'booms',             # Containment booms
    'absorbents',        # Absorbing materials
    'manual',            # Manual cleanup (e.g., by workers)
    'bioremediation',    # Using microorganisms to break down oil
    'vacuum',            # Vacuum equipment
    'washing',           # High-pressure washing of shorelines
    'none'               # No cleanup performed
]

# Impact Assessment Settings
# -------------------------
# Base cleanup cost per barrel (USD)
BASE_CLEANUP_COST_PER_BARREL = 10000

# Location multipliers for cleanup costs
LOCATION_MULTIPLIERS = {
    'open_ocean': 1.0,
    'coastal': 2.0,
    'estuary': 2.5,
    'reef': 3.0,
    'wetland': 2.5,
    'river': 2.0,
    'port': 1.8
}

# Base time per volume for cleanup (days per 1000 barrels)
BASE_TIME_PER_VOLUME = 1.5

# Wildlife impact base values by location type
WILDLIFE_BASE_IMPACTS = {
    'open_ocean': {'density': 0.2, 'vulnerability': 0.6},
    'coastal': {'density': 0.8, 'vulnerability': 0.8},
    'estuary': {'density': 1.0, 'vulnerability': 1.0},
    'reef': {'density': 1.2, 'vulnerability': 0.9},
    'wetland': {'density': 1.0, 'vulnerability': 1.0},
    'river': {'density': 0.7, 'vulnerability': 0.8}
}

# Toxicity values for qualitative environmental toxicity ratings
TOXICITY_MAP = {
    'low': 0.3,
    'moderate': 0.6,
    'high': 0.8,
    'very high': 1.0
}

# API Keys and External Services
# -----------------------------
# OpenStreetMap usage policy URL
OSM_USAGE_POLICY_URL = 'https://operations.osmfoundation.org/policies/tiles/'

# API key for external weather services (if used)
# Replace with your actual API key if needed
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')

# Development Settings
# -------------------
# Debug mode
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Logging level
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Version
VERSION = '0.1.0'