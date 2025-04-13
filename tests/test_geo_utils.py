"""
Tests for the geospatial utility functions.
"""

import unittest
import math
import numpy as np
from shapely.geometry import Point, Polygon

from utils.geo_utils import (
    validate_coordinates,
    calculate_distance,
    calculate_area_from_polygon,
    convert_coordinates_to_pixels,
    create_grid_points,
    get_lat_lon_bounds,
    calculate_bearing,
    get_destination_point
)


class TestGeoUtils(unittest.TestCase):
    """Test cases for geospatial utility functions."""
    
    def test_validate_coordinates(self):
        """Test coordinate validation function."""
        # Valid coordinates
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(45.5, -120.5))
        
        # Invalid latitudes
        self.assertFalse(validate_coordinates(91, 0))
        self.assertFalse(validate_coordinates(-91, 0))
        
        # Invalid longitudes
        self.assertFalse(validate_coordinates(0, 181))
        self.assertFalse(validate_coordinates(0, -181))
        
        # Both invalid
        self.assertFalse(validate_coordinates(100, 200))
        
        # Edge cases
        self.assertTrue(validate_coordinates(90, 180))  # Exactly at the limits
        self.assertTrue(validate_coordinates(-90, -180))  # Exactly at the limits
    
    def test_calculate_distance(self):
        """Test the distance calculation function."""
        # Distance from a point to itself should be 0
        self.assertEqual(calculate_distance(0, 0, 0, 0), 0)
        
        # Known distances
        # New York to Los Angeles: ~3,940 km
        ny_lat, ny_lon = 40.7128, -74.0060
        la_lat, la_lon = 34.0522, -118.2437
        ny_to_la = calculate_distance(ny_lat, ny_lon, la_lat, la_lon)
        self.assertAlmostEqual(ny_to_la, 3940, delta=100)
        
        # London to Paris: ~340 km
        london_lat, london_lon = 51.5074, -0.1278
        paris_lat, paris_lon = 48.8566, 2.3522
        london_to_paris = calculate_distance(london_lat, london_lon, paris_lat, paris_lon)
        self.assertAlmostEqual(london_to_paris, 340, delta=10)
        
        # Check that distance is symmetric
        dist1 = calculate_distance(ny_lat, ny_lon, la_lat, la_lon)
        dist2 = calculate_distance(la_lat, la_lon, ny_lat, ny_lon)
        self.assertEqual(dist1, dist2)
    
    def test_calculate_area_from_polygon(self):
        """Test the polygon area calculation function."""
        # Create a simple 1 degree x 1 degree square at the equator
        # At the equator, 1 degree is approximately 111 km
        square_at_equator = Polygon([
            (0, 0), (1, 0), (1, 1), (0, 1), (0, 0)
        ])
        
        area = calculate_area_from_polygon(square_at_equator, 0.5)
        self.assertAlmostEqual(area, 111 * 111, delta=1000)  # Approximately 12,321 km²
        
        # Create a more complex polygon
        complex_polygon = Polygon([
            (0, 0), (1, 0), (1.5, 0.5), (1, 1), (0, 1), (0, 0)
        ])
        
        area = calculate_area_from_polygon(complex_polygon, 0.5)
        self.assertGreater(area, 0)
        
        # Test with an empty polygon
        empty_polygon = Polygon()
        area = calculate_area_from_polygon(empty_polygon, 0.5)
        self.assertEqual(area, 0)
    
    def test_convert_coordinates_to_pixels(self):
        """Test conversion of coordinates to pixel positions."""
        # Define map bounds and image size
        bounds = (-180, -90, 180, 90)  # whole world
        width, height = 360, 180  # 1 pixel per degree
        
        # Test center point
        center_pixel = convert_coordinates_to_pixels(0, 0, bounds, width, height)
        self.assertEqual(center_pixel, (180, 90))  # Center of the image
        
        # Test corners
        top_left = convert_coordinates_to_pixels(90, -180, bounds, width, height)
        self.assertEqual(top_left, (0, 0))
        
        bottom_right = convert_coordinates_to_pixels(-90, 180, bounds, width, height)
        self.assertEqual(bottom_right, (360, 180))
        
        # Test point outside bounds
        outside_point = convert_coordinates_to_pixels(100, 0, bounds, width, height)
        self.assertIsNone(outside_point)
    
    def test_create_grid_points(self):
        """Test creation of a grid of points around a center."""
        # Create a grid around a center point
        center_lat, center_lon = 45.0, -75.0
        radius_km = 10
        num_points = 100
        
        grid_points = create_grid_points(center_lat, center_lon, radius_km, num_points)
        
        # Check that we have approximately the requested number of points
        # (May be slightly less due to filtering by distance)
        self.assertGreaterEqual(len(grid_points), num_points * 0.7)
        self.assertLessEqual(len(grid_points), num_points * 1.3)
        
        # Check that all points are within the requested radius
        for lat, lon in grid_points:
            distance = calculate_distance(center_lat, center_lon, lat, lon)
            self.assertLessEqual(distance, radius_km)
        
        # Check that points are distributed around the center
        lats = [p[0] for p in grid_points]
        lons = [p[1] for p in grid_points]
        
        self.assertLess(min(lats), center_lat)
        self.assertGreater(max(lats), center_lat)
        self.assertLess(min(lons), center_lon)
        self.assertGreater(max(lons), center_lon)
    
    def test_get_lat_lon_bounds(self):
        """Test calculation of lat/lon bounds around a center point."""
        center_lat, center_lon = 45.0, -75.0
        radius_km = 10
        
        bounds = get_lat_lon_bounds(center_lat, center_lon, radius_km)
        min_lon, min_lat, max_lon, max_lat = bounds
        
        # Check that the bounds form a rectangle
        self.assertLess(min_lat, max_lat)
        self.assertLess(min_lon, max_lon)
        
        # Check that the center is inside the bounds
        self.assertGreater(center_lat, min_lat)
        self.assertLess(center_lat, max_lat)
        self.assertGreater(center_lon, min_lon)
        self.assertLess(center_lon, max_lon)
        
        # Check that the bounds are approximately the right size
        # Convert the radius to degrees at this latitude
        lat_radius_deg = radius_km / 111.0
        lon_radius_deg = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        self.assertAlmostEqual(center_lat - min_lat, lat_radius_deg, delta=0.01)
        self.assertAlmostEqual(max_lat - center_lat, lat_radius_deg, delta=0.01)
        self.assertAlmostEqual(center_lon - min_lon, lon_radius_deg, delta=0.01)
        self.assertAlmostEqual(max_lon - center_lon, lon_radius_deg, delta=0.01)
        
        # Test bounds at extreme latitudes
        polar_bounds = get_lat_lon_bounds(89.0, 0.0, radius_km)
        _, polar_min_lat, _, polar_max_lat = polar_bounds
        
        # Ensure we don't exceed valid latitude range
        self.assertGreaterEqual(polar_min_lat, -90)
        self.assertLessEqual(polar_max_lat, 90)
    
    def test_calculate_bearing(self):
        """Test calculation of bearing between two points."""
        # North: bearing should be 0 degrees
        bearing = calculate_bearing(0, 0, 1, 0)
        self.assertAlmostEqual(bearing, 0, delta=0.1)
        
        # East: bearing should be 90 degrees
        bearing = calculate_bearing(0, 0, 0, 1)
        self.assertAlmostEqual(bearing, 90, delta=0.1)
        
        # South: bearing should be 180 degrees
        bearing = calculate_bearing(0, 0, -1, 0)
        self.assertAlmostEqual(bearing, 180, delta=0.1)
        
        # West: bearing should be 270 degrees
        bearing = calculate_bearing(0, 0, 0, -1)
        self.assertAlmostEqual(bearing, 270, delta=0.1)
        
        # Northeast: bearing should be 45 degrees
        bearing = calculate_bearing(0, 0, 1, 1)
        self.assertAlmostEqual(bearing, 45, delta=0.1)
        
        # Real-world example: New York to London
        ny_lat, ny_lon = 40.7128, -74.0060
        london_lat, london_lon = 51.5074, -0.1278
        
        bearing = calculate_bearing(ny_lat, ny_lon, london_lat, london_lon)
        self.assertGreater(bearing, 0)
        self.assertLess(bearing, 90)  # Should be in northeast direction
    
    def test_get_destination_point(self):
        """Test calculation of a destination point based on bearing and distance."""
        # Start at origin, go 10 km north
        start_lat, start_lon = 0, 0
        bearing = 0  # North
        distance_km = 10
        
        dest_lat, dest_lon = get_destination_point(start_lat, start_lon, bearing, distance_km)
        
        # Destination should be north of start
        self.assertGreater(dest_lat, start_lat)
        self.assertAlmostEqual(dest_lon, start_lon, delta=0.001)  # Longitude shouldn't change
        
        # Distance should be approximately 10 km
        distance = calculate_distance(start_lat, start_lon, dest_lat, dest_lon)
        self.assertAlmostEqual(distance, distance_km, delta=0.1)
        
        # Test each cardinal direction
        for bearing, expected_direction in [
            (0, 'north'),    # North
            (90, 'east'),    # East
            (180, 'south'),  # South
            (270, 'west')    # West
        ]:
            dest_lat, dest_lon = get_destination_point(start_lat, start_lon, bearing, distance_km)
            
            if expected_direction == 'north':
                self.assertGreater(dest_lat, start_lat)
                self.assertAlmostEqual(dest_lon, start_lon, delta=0.001)
            elif expected_direction == 'east':
                self.assertAlmostEqual(dest_lat, start_lat, delta=0.001)
                self.assertGreater(dest_lon, start_lon)
            elif expected_direction == 'south':
                self.assertLess(dest_lat, start_lat)
                self.assertAlmostEqual(dest_lon, start_lon, delta=0.001)
            elif expected_direction == 'west':
                self.assertAlmostEqual(dest_lat, start_lat, delta=0.001)
                self.assertLess(dest_lon, start_lon)
        
        # Test with a real-world origin
        sydney_lat, sydney_lon = -33.8688, 151.2093
        
        # Go 100 km northeast from Sydney
        dest_lat, dest_lon = get_destination_point(sydney_lat, sydney_lon, 45, 100)
        
        # Distance should be approximately 100 km
        distance = calculate_distance(sydney_lat, sydney_lon, dest_lat, dest_lon)
        self.assertAlmostEqual(distance, 100, delta=1)
        
        # Bearing from Sydney to destination should be approximately 45 degrees
        reverse_bearing = calculate_bearing(sydney_lat, sydney_lon, dest_lat, dest_lon)
        self.assertAlmostEqual(reverse_bearing, 45, delta=1)


if __name__ == '__main__':
    unittest.main()