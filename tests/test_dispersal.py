"""
Tests for the oil spill dispersal model.
"""

import unittest
import math
import numpy as np
from shapely.geometry import Polygon

from models.dispersal_model import OilDispersalModel


class TestDispersalModel(unittest.TestCase):
    """Test cases for the OilDispersalModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock oil properties dictionary for testing
        self.oil_properties = {
            'name': 'Test Oil',
            'density': 0.85,
            'viscosity': 10.0,
            'surface_tension': 25.0,
            'evaporation_rate': 0.3,
            'solubility': 0.02,
            'persistence_factor': 0.7
        }
        
        # Create a dispersal model instance for testing
        self.model = OilDispersalModel(
            volume=1000,  # 1000 barrels
            oil_properties=self.oil_properties,
            time_hours=24,
            wind_speed=10.0,
            water_temp=15.0,
            wave_height=0.5
        )
    
    def test_initialization(self):
        """Test that the model initializes correctly with given parameters."""
        self.assertEqual(self.model.volume_m3, 1000 * 0.159)  # barrels to cubic meters
        self.assertEqual(self.model.oil_properties, self.oil_properties)
        self.assertEqual(self.model.time_hours, 24)
        self.assertEqual(self.model.wind_speed, 10.0)
        self.assertEqual(self.model.water_temp, 15.0)
        self.assertEqual(self.model.wave_height, 0.5)
        
        # Check derived properties
        self.assertEqual(self.model.density, 0.85)
        self.assertEqual(self.model.viscosity, 10.0)
        self.assertEqual(self.model.surface_tension, 25.0)
        self.assertEqual(self.model.evaporation_rate, 0.3)
    
    def test_calculate_affected_area(self):
        """Test that affected area calculation returns expected structure."""
        lat, lon = 45.0, -75.0
        area_info = self.model.calculate_affected_area(lat, lon)
        
        # Check that we get a dictionary with expected keys
        self.assertIsInstance(area_info, dict)
        self.assertIn('area_km2', area_info)
        self.assertIn('center', area_info)
        self.assertIn('thickness', area_info)
        self.assertIn('evaporated', area_info)
        self.assertIn('dissolved', area_info)
        self.assertIn('polygon', area_info)
        
        # Check that the values are of expected types
        self.assertIsInstance(area_info['area_km2'], float)
        self.assertIsInstance(area_info['center'], tuple)
        self.assertIsInstance(area_info['thickness'], float)
        self.assertIsInstance(area_info['evaporated'], float)
        self.assertIsInstance(area_info['dissolved'], float)
        self.assertIsInstance(area_info['polygon'], Polygon)
        
        # Check that the area is positive
        self.assertGreater(area_info['area_km2'], 0)
        
        # Check that center coordinates match input
        self.assertEqual(area_info['center'], (lat, lon))
        
        # Check that fractions are between 0 and 1
        self.assertGreaterEqual(area_info['evaporated'], 0)
        self.assertLessEqual(area_info['evaporated'], 1)
        self.assertGreaterEqual(area_info['dissolved'], 0)
        self.assertLessEqual(area_info['dissolved'], 1)
    
    def test_calculate_evaporation(self):
        """Test the evaporation calculation."""
        evaporated = self.model._calculate_evaporation()
        
        # Evaporation should be between 0 and 1
        self.assertGreaterEqual(evaporated, 0)
        self.assertLessEqual(evaporated, 1)
        
        # Higher temperature should increase evaporation
        self.model.water_temp = 25.0
        evaporated_hot = self.model._calculate_evaporation()
        self.model.water_temp = 5.0
        evaporated_cold = self.model._calculate_evaporation()
        
        self.assertGreater(evaporated_hot, evaporated_cold)
        
        # Higher wind should increase evaporation
        self.model.water_temp = 15.0  # Reset temperature
        self.model.wind_speed = 20.0
        evaporated_windy = self.model._calculate_evaporation()
        self.model.wind_speed = 5.0
        evaporated_calm = self.model._calculate_evaporation()
        
        self.assertGreater(evaporated_windy, evaporated_calm)
    
    def test_calculate_dissolution(self):
        """Test the dissolution calculation."""
        dissolved = self.model._calculate_dissolution()
        
        # Dissolution should be between 0 and 1
        self.assertGreaterEqual(dissolved, 0)
        self.assertLessEqual(dissolved, 1)
        
        # Higher temperature should increase dissolution
        self.model.water_temp = 25.0
        dissolved_hot = self.model._calculate_dissolution()
        self.model.water_temp = 5.0
        dissolved_cold = self.model._calculate_dissolution()
        
        self.assertGreater(dissolved_hot, dissolved_cold)
        
        # Higher waves should increase dissolution
        self.model.water_temp = 15.0  # Reset temperature
        self.model.wave_height = 2.0
        dissolved_wavy = self.model._calculate_dissolution()
        self.model.wave_height = 0.1
        dissolved_calm = self.model._calculate_dissolution()
        
        self.assertGreater(dissolved_wavy, dissolved_calm)
    
    def test_simulate_spreading(self):
        """Test the spreading simulation."""
        lat, lon = 45.0, -75.0
        
        # Run the simulation
        self.model._simulate_spreading(lat, lon)
        
        # Check that a polygon was created
        self.assertIsNotNone(self.model._spill_polygon)
        self.assertIsInstance(self.model._spill_polygon, Polygon)
        
        # Check that the polygon is valid and not empty
        self.assertTrue(self.model._spill_polygon.is_valid)
        self.assertFalse(self.model._spill_polygon.is_empty)
        
        # Check that the polygon's centroid is close to the spill location
        centroid = self.model._spill_polygon.centroid
        distance_degrees = math.sqrt((centroid.x - lon)**2 + (centroid.y - lat)**2)
        self.assertLess(distance_degrees, 0.1)  # Should be within 0.1 degrees
    
    def test_get_volume_fractions(self):
        """Test that volume fractions sum to 1."""
        fractions = self.model.get_volume_fractions()
        
        # Check that we have the expected keys
        self.assertIn('evaporated', fractions)
        self.assertIn('dissolved', fractions)
        self.assertIn('surface', fractions)
        
        # Check that fractions are between 0 and 1
        self.assertGreaterEqual(fractions['evaporated'], 0)
        self.assertLessEqual(fractions['evaporated'], 1)
        self.assertGreaterEqual(fractions['dissolved'], 0)
        self.assertLessEqual(fractions['dissolved'], 1)
        self.assertGreaterEqual(fractions['surface'], 0)
        self.assertLessEqual(fractions['surface'], 1)
        
        # Check that fractions sum to 1 (within floating point precision)
        total = fractions['evaporated'] + fractions['dissolved'] + fractions['surface']
        self.assertAlmostEqual(total, 1.0, places=10)
    
    def test_time_dependence(self):
        """Test that the model results change with time."""
        # Get results at 24 hours
        self.model.time_hours = 24
        area_24h = self.model.calculate_affected_area(45.0, -75.0)
        
        # Get results at 48 hours
        self.model.time_hours = 48
        area_48h = self.model.calculate_affected_area(45.0, -75.0)
        
        # Area should increase with time
        self.assertGreater(area_48h['area_km2'], area_24h['area_km2'])
        
        # Evaporation should increase with time
        self.assertGreater(area_48h['evaporated'], area_24h['evaporated'])
        
        # Thickness should decrease with time
        self.assertLess(area_48h['thickness'], area_24h['thickness'])
    
    def test_oil_type_dependence(self):
        """Test that different oil types produce different results."""
        # Create a model with a different oil type
        heavy_oil_properties = {
            'name': 'Heavy Oil',
            'density': 0.95,
            'viscosity': 500.0,
            'surface_tension': 30.0,
            'evaporation_rate': 0.1,
            'solubility': 0.01,
            'persistence_factor': 0.9
        }
        
        heavy_model = OilDispersalModel(
            volume=1000,
            oil_properties=heavy_oil_properties,
            time_hours=24,
            wind_speed=10.0,
            water_temp=15.0,
            wave_height=0.5
        )
        
        # Get results for both oil types
        light_area = self.model.calculate_affected_area(45.0, -75.0)
        heavy_area = heavy_model.calculate_affected_area(45.0, -75.0)
        
        # Light oil should spread more
        self.assertGreater(light_area['area_km2'], heavy_area['area_km2'])
        
        # Light oil should evaporate more
        self.assertGreater(light_area['evaporated'], heavy_area['evaporated'])
        
        # Heavy oil should have thicker slick
        self.assertGreater(heavy_area['thickness'], light_area['thickness'])


if __name__ == '__main__':
    unittest.main()