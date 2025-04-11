
"""
Oil Spill Impact Estimator - Utilities Package
----------------------------------------------
This package contains utility functions for geospatial operations,
data handling, and visualization.
"""

from .geo_utils import validate_coordinates, calculate_distance, calculate_area_from_polygon
from .visualization import create_map, display_map, generate_impact_charts
from .data_handler import load_oil_types, load_sample_data, save_simulation_results

__all__ = [
    'validate_coordinates',
    'calculate_distance',
    'calculate_area_from_polygon',
    'create_map',
    'display_map',
    'generate_impact_charts',
    'load_oil_types',
    'load_sample_data',
    'save_simulation_results'
]