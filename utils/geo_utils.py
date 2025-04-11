"""
Geospatial Utilities
-------------------
Utility functions for geographic calculations and coordinate validation.
"""

import math
import numpy as np
from shapely.geometry import Point, Polygon
import pyproj
from functools import partial
from shapely.ops import transform


def validate_coordinates(latitude, longitude):
    """
    Validate that the given coordinates are within valid ranges.
    
    Args:
        latitude (float): Latitude in decimal degrees
        longitude (float): Longitude in decimal degrees
        
    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    # Check latitude range: -90 to 90 degrees
    if latitude < -90 or latitude > 90:
        return False
    
    # Check longitude range: -180 to 180 degrees
    if longitude < -180 or longitude > 180:
        return False
    
    return True


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    Uses the Haversine formula.
    
    Args:
        lat1 (float): Latitude of point 1 in decimal degrees
        lon1 (float): Longitude of point 1 in decimal degrees
        lat2 (float): Latitude of point 2 in decimal degrees
        lon2 (float): Longitude of point 2 in decimal degrees
        
    Returns:
        float: Distance in kilometers
    """
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance


def calculate_area_from_polygon(polygon, latitude):
    """
    Calculate the area of a shapely polygon in square kilometers,
    taking into account the Earth's curvature.
    
    Args:
        polygon (shapely.geometry.Polygon): The polygon to calculate area for
        latitude (float): Approximate latitude of the polygon (for projection)
        
    Returns:
        float: Area in square kilometers
    """
    # If we have an empty polygon, return 0
    if polygon is None or polygon.is_empty:
        return 0.0
    
    # Create a suitable equal-area projection centered on the polygon
    proj_string = f"+proj=aea +lat_1={latitude-5} +lat_2={latitude+5} +lat_0={latitude} +lon_0={polygon.centroid.x}"
    projection = pyproj.Proj(proj_string)
    wgs84 = pyproj.Proj("+proj=longlat +datum=WGS84")
    
    # Create a transformer function
    project = partial(
        pyproj.transform,
        wgs84,          # source coordinate system
        projection      # destination coordinate system
    )
    
    # Transform the polygon to the equal-area projection
    projected_polygon = transform(project, polygon)
    
    # Calculate the area in square meters and convert to square kilometers
    area_sq_km = projected_polygon.area / 1_000_000
    
    return area_sq_km


def convert_coordinates_to_pixels(lat, lon, bounds, width, height):
    """
    Convert latitude and longitude to pixel coordinates on an image.
    
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        bounds (tuple): Map bounds as (min_lon, min_lat, max_lon, max_lat)
        width (int): Width of the image in pixels
        height (int): Height of the image in pixels
        
    Returns:
        tuple: (x, y) pixel coordinates
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    
    # Check if coordinates are within bounds
    if lat < min_lat or lat > max_lat or lon < min_lon or lon > max_lon:
        return None
    
    # Convert to normalized coordinates (0-1)
    x_norm = (lon - min_lon) / (max_lon - min_lon)
    y_norm = 1.0 - (lat - min_lat) / (max_lat - min_lat)  # Flip Y axis
    
    # Convert to pixel coordinates
    x_px = int(x_norm * width)
    y_px = int(y_norm * height)
    
    return (x_px, y_px)


def create_grid_points(center_lat, center_lon, radius_km, num_points=100):
    """
    Create a grid of points around a center location.
    
    Args:
        center_lat (float): Center latitude in decimal degrees
        center_lon (float): Center longitude in decimal degrees
        radius_km (float): Radius from center in kilometers
        num_points (int): Approximate number of points to generate
        
    Returns:
        list: List of (lat, lon) tuples
    """
    # Estimate number of points in each direction
    n = int(math.sqrt(num_points))
    
    # Convert radius from km to degrees (approximately)
    # 1 degree of latitude is approximately 111 km
    radius_lat = radius_km / 111.0
    # 1 degree of longitude is approximately 111 * cos(lat) km
    radius_lon = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    # Create a grid
    lat_vals = np.linspace(center_lat - radius_lat, center_lat + radius_lat, n)
    lon_vals = np.linspace(center_lon - radius_lon, center_lon + radius_lon, n)
    
    # Generate all combinations of lat/lon
    grid_points = []
    for lat in lat_vals:
        for lon in lon_vals:
            # Calculate distance from center
            dist = calculate_distance(center_lat, center_lon, lat, lon)
            # Only include points within the radius
            if dist <= radius_km:
                grid_points.append((lat, lon))
    
    return grid_points


def get_lat_lon_bounds(center_lat, center_lon, radius_km):
    """
    Calculate latitude/longitude bounds for a map centered on a point.
    
    Args:
        center_lat (float): Center latitude in decimal degrees
        center_lon (float): Center longitude in decimal degrees
        radius_km (float): Radius in kilometers
        
    Returns:
        tuple: (min_lon, min_lat, max_lon, max_lat)
    """
    # Convert radius to degrees
    radius_lat = radius_km / 111.0  # Approx. 111 km per degree of latitude
    radius_lon = radius_km / (111.0 * math.cos(math.radians(center_lat)))  # Longitude depends on latitude
    
    # Calculate bounds
    min_lat = center_lat - radius_lat
    max_lat = center_lat + radius_lat
    min_lon = center_lon - radius_lon
    max_lon = center_lon + radius_lon
    
    # Ensure bounds are within valid latitude/longitude ranges
    min_lat = max(-90, min_lat)
    max_lat = min(90, max_lat)
    min_lon = max(-180, min_lon)
    max_lon = min(180, max_lon)
    
    return (min_lon, min_lat, max_lon, max_lat)


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing (direction) from point 1 to point 2.
    
    Args:
        lat1 (float): Latitude of point 1 in decimal degrees
        lon1 (float): Longitude of point 1 in decimal degrees
        lat2 (float): Latitude of point 2 in decimal degrees
        lon2 (float): Longitude of point 2 in decimal degrees
        
    Returns:
        float: Bearing in degrees (0 = North, 90 = East, etc.)
    """
    # Convert to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    # Calculate the bearing
    x = math.sin(lon2 - lon1) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    bearing_rad = math.atan2(x, y)
    
    # Convert back to degrees and normalize
    bearing_deg = math.degrees(bearing_rad)
    bearing_deg = (bearing_deg + 360) % 360
    
    return bearing_deg


def get_destination_point(lat, lon, bearing, distance_km):
    """
    Calculate the destination point given a starting point, bearing, and distance.
    
    Args:
        lat (float): Starting latitude in decimal degrees
        lon (float): Starting longitude in decimal degrees
        bearing (float): Bearing in degrees (0 = North, 90 = East, etc.)
        distance_km (float): Distance in kilometers
        
    Returns:
        tuple: (destination_lat, destination_lon) in decimal degrees
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing_rad = math.radians(bearing)
    
    # Calculate the destination point
    angular_distance = distance_km / R
    
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance) +
        math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing_rad)
    )
    
    lon2 = lon1 + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2)
    )
    
    # Convert back to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    
    # Normalize longitude
    lon2 = ((lon2 + 180) % 360) - 180
    
    return (lat2, lon2)