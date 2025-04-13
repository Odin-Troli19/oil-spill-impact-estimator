"""
Data Handling Utilities
----------------------
Functions for loading, saving, and processing data for the oil spill estimator.
"""

import os
import json
import csv
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


def load_oil_types(filepath=None):
    """
    Load oil type definitions from a JSON file.
    
    Args:
        filepath (str): Path to the oil types JSON file.
                        If None, uses the default location in the data directory.
                        
    Returns:
        dict: Dictionary of oil types and their properties
    """
    if filepath is None:
        # Try to find the default location
        root_dir = Path(__file__).parents[1]  # Go up two levels from this file
        default_paths = [
            root_dir / 'data' / 'oil_types.json',
            Path('data') / 'oil_types.json',  # Relative to current working directory
            Path('oil_types.json')  # Direct in current working directory
        ]
        
        # Try each path until we find a valid file
        for path in default_paths:
            if path.exists():
                filepath = path
                break
        
        if filepath is None:
            raise FileNotFoundError("Could not find oil_types.json in default locations")
    
    # Load the oil types
    with open(filepath, 'r') as f:
        oil_types = json.load(f)
    
    return oil_types


def load_sample_data(filepath=None):
    """
    Load sample spill data from a CSV file.
    
    Args:
        filepath (str): Path to the sample data CSV file.
                        If None, uses the default location in the data directory.
                        
    Returns:
        pandas.DataFrame: DataFrame containing the sample spill data
    """
    if filepath is None:
        # Try to find the default location
        root_dir = Path(__file__).parents[1]  # Go up two levels from this file
        default_paths = [
            root_dir / 'data' / 'sample_spills.csv',
            Path('data') / 'sample_spills.csv',  # Relative to current working directory
            Path('sample_spills.csv')  # Direct in current working directory
        ]
        
        # Try each path until we find a valid file
        for path in default_paths:
            if path.exists():
                filepath = path
                break
        
        if filepath is None:
            raise FileNotFoundError("Could not find sample_spills.csv in default locations")
    
    # Load the sample data
    try:
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        raise IOError(f"Error loading sample data: {str(e)}")


def save_simulation_results(results, filepath=None):
    """
    Save simulation results to a JSON file.
    
    Args:
        results (dict): Dictionary containing simulation results
        filepath (str): Path to save the results. If None, generates a timestamped filename.
        
    Returns:
        str: Path to the saved file
    """
    if filepath is None:
        # Generate a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory if it doesn't exist
        results_dir = Path('results')
        if not results_dir.exists():
            results_dir.mkdir(parents=True)
        
        filepath = results_dir / f"simulation_{timestamp}.json"
    
    # Convert Path object to string if necessary
    filepath_str = str(filepath)
    
    # Prepare results for serialization
    # Some objects (like shapely geometries) are not directly JSON serializable
    serializable_results = prepare_for_serialization(results)
    
    # Save to file
    with open(filepath_str, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    return filepath_str


def prepare_for_serialization(data):
    """
    Prepare data for JSON serialization by converting non-serializable objects.
    
    Args:
        data: Data to prepare (can be dict, list, or other types)
        
    Returns:
        Data in a JSON-serializable format
    """
    if isinstance(data, dict):
        # Process each item in the dictionary
        result = {}
        for key, value in data.items():
            # Skip None values
            if value is None:
                result[key] = None
            # Handle special objects
            elif key == 'polygon' and hasattr(value, 'wkt'):
                # Convert Shapely geometry to WKT string
                result[key] = value.wkt
            elif isinstance(value, (datetime, np.datetime64)):
                # Convert datetime to ISO format string
                result[key] = value.isoformat()
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                # Convert numpy integers to Python integers
                result[key] = int(value)
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                # Convert numpy floats to Python floats
                result[key] = float(value)
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                result[key] = prepare_for_serialization(value)
            else:
                try:
                    # Attempt to use the value as is
                    # This will work for strings, numbers, booleans, etc.
                    result[key] = value
                except (TypeError, OverflowError):
                    # If serialization fails, convert to string
                    result[key] = str(value)
        return result
    
    elif isinstance(data, list):
        # Process each item in the list
        return [prepare_for_serialization(item) for item in data]
    
    elif isinstance(data, (datetime, np.datetime64)):
        return data.isoformat()
    
    elif isinstance(data, (np.integer, np.int64, np.int32)):
        return int(data)
    
    elif isinstance(data, (np.floating, np.float64, np.float32)):
        return float(data)
    
    else:
        # Return the value as is if it's a basic type
        try:
            # This will check if it's JSON serializable
            json.dumps(data)
            return data
        except (TypeError, OverflowError):
            # If not serializable, convert to string
            return str(data)


def export_to_csv(results, filepath=None):
    """
    Export simulation results to a CSV file.
    
    Args:
        results (dict): Dictionary containing simulation results
        filepath (str): Path to save the CSV file. If None, generates a timestamped filename.
        
    Returns:
        str: Path to the saved file
    """
    if filepath is None:
        # Generate a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory if it doesn't exist
        results_dir = Path('results')
        if not results_dir.exists():
            results_dir.mkdir(parents=True)
        
        filepath = results_dir / f"simulation_{timestamp}.csv"
    
    # Flatten the nested dictionary for CSV export
    flat_data = flatten_dict(results)
    
    # Write to CSV
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header row
        writer.writerow(['Parameter', 'Value'])
        
        # Write data rows
        for key, value in flat_data.items():
            writer.writerow([key, value])
    
    return filepath


def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a nested dictionary into a single-level dictionary.
    
    Args:
        d (dict): The dictionary to flatten
        parent_key (str): The parent key for the current level
        sep (str): Separator between parent and child keys
        
    Returns:
        dict: Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict) and v:
            # Recursive call for nested dictionaries
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            # Add the key-value pair to our items
            items.append((new_key, v))
            
    return dict(items)


def load_environmental_data(latitude, longitude, filepath=None):
    """
    Load environmental data for a specific location.
    This is a placeholder - in a real application, this might fetch data
    from an external API or database.
    
    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        filepath (str): Optional path to a local environmental data file
        
    Returns:
        dict: Environmental data for the location
    """
    # This is a simplified implementation that returns dummy data
    # In a real application, you'd implement an API call or database lookup
    
    # Simulate seasonal temperature variations based on latitude
    month = datetime.now().month
    # Northern hemisphere: warmer in summer (June-August)
    # Southern hemisphere: warmer in summer (December-February)
    is_northern = latitude > 0
    
    if is_northern:
        # Northern hemisphere seasonal adjustment
        seasonal_factor = -abs(month - 7) / 6 + 1  # Peak at month 7 (July)
    else:
        # Southern hemisphere seasonal adjustment
        seasonal_factor = -abs(((month + 6) % 12) - 7) / 6 + 1  # Peak at month 1 (January)
    
    # Base temperature decreases with distance from equator
    base_temp = 30 - abs(latitude) * 0.5
    
    # Temperature with seasonal variation
    water_temp = base_temp + seasonal_factor * 10
    
    # Wind and wave data simplified based on latitude
    # Stronger winds/waves in higher latitudes
    wind_factor = 0.5 + abs(latitude) / 90
    
    # Environmental sensitivity - coastal areas more sensitive
    # This is very simplified - real data would be based on ecological factors
    
    # Dummy coordinates for coastal areas - in a real app, use a coastline database
    distance_to_coast = min(abs(longitude - (-120)), abs(longitude - (-80)), 
                           abs(longitude - 0), abs(longitude - 100))
    is_coastal = distance_to_coast < 5
    
    return {
        'water_temp_c': water_temp,
        'wind_speed_kmh': 10 + 20 * wind_factor * np.random.random(),
        'wave_height_m': 0.5 + 2 * wind_factor * np.random.random(),
        'environmental_sensitivity': 2.0 if is_coastal else 1.0,
        'location_type': 'coastal' if is_coastal else 'open_ocean'
    }