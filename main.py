# Entry point for the application (CLI or GUI)

#!/usr/bin/env python3
"""
Oil Spill Impact Estimator
--------------------------
A tool to estimate the environmental impact of oil spills based on
location, volume, and type of oil.
"""

import os
import argparse
import json
from pathlib import Path

from models.dispersal_model import OilDispersalModel
from models.impact_estimator import ImpactEstimator
from utils.geo_utils import validate_coordinates
from utils.visualization import create_map, display_map
from utils.data_handler import load_oil_types


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Estimate environmental impact of an oil spill."
    )
    
    parser.add_argument(
        "--volume", 
        type=float, 
        required=True,
        help="Volume of the oil spill in barrels"
    )
    
    parser.add_argument(
        "--lat", 
        type=float, 
        required=True,
        help="Latitude of the spill location"
    )
    
    parser.add_argument(
        "--lon", 
        type=float, 
        required=True,
        help="Longitude of the spill location"
    )
    
    parser.add_argument(
        "--oil-type", 
        type=str, 
        required=True,
        help="Type of oil spilled (e.g., 'crude', 'diesel', 'heavy_fuel')"
    )
    
    parser.add_argument(
        "--output-map", 
        type=str,
        default="spill_map.html",
        help="Filename for the output map (default: spill_map.html)"
    )
    
    parser.add_argument(
        "--show-map", 
        action="store_true",
        help="Display the map after generation"
    )
    
    return parser.parse_args()


def validate_inputs(args, oil_types):
    """Validate user inputs."""
    errors = []
    
    # Validate volume
    if args.volume <= 0:
        errors.append("Volume must be a positive number")
    
    # Validate coordinates
    if not validate_coordinates(args.lat, args.lon):
        errors.append(f"Invalid coordinates: {args.lat}, {args.lon}")
    
    # Validate oil type
    if args.oil_type not in oil_types:
        errors.append(f"Unknown oil type: '{args.oil_type}'. Available types: {list(oil_types.keys())}")
    
    return errors


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load oil types data
    try:
        oil_types = load_oil_types()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading oil types data: {e}")
        return 1
    
    # Validate inputs
    errors = validate_inputs(args, oil_types)
    if errors:
        print("Input validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    
    # Initialize models
    oil_properties = oil_types[args.oil_type]
    dispersal_model = OilDispersalModel(
        volume=args.volume,
        oil_properties=oil_properties
    )
    
    impact_estimator = ImpactEstimator(
        dispersal_model=dispersal_model
    )
    
    # Run the simulation and calculate impacts
    try:
        print(f"\nSimulating oil spill of {args.volume} barrels of {args.oil_type} oil at ({args.lat}, {args.lon})...\n")
        
        # Simulate dispersal
        affected_area = dispersal_model.calculate_affected_area(lat=args.lat, lon=args.lon)
        
        # Calculate environmental impacts
        surface_area = impact_estimator.calculate_surface_area()
        co2_emissions = impact_estimator.calculate_co2_emissions()
        cleanup_time = impact_estimator.estimate_cleanup_time()
        
        # Display results
        print("=== IMPACT ESTIMATION RESULTS ===")
        print(f"Affected water surface area: {surface_area:.2f} km²")
        print(f"Estimated CO2 equivalent emissions: {co2_emissions:.2f} metric tons")
        print(f"Estimated cleanup time: {cleanup_time:.1f} days")
        
        # Create map visualization
        map_path = create_map(
            latitude=args.lat,
            longitude=args.lon,
            affected_area=affected_area,
            oil_type=args.oil_type,
            volume=args.volume,
            output_file=args.output_map
        )
        
        print(f"\nMap visualization saved to: {map_path}")
        
        # Display map if requested
        if args.show_map:
            display_map(map_path)
            
        return 0
        
    except Exception as e:
        print(f"Error during simulation: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())