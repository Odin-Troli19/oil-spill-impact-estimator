"""
Tests for the oil spill impact estimator.
"""

import unittest
import numpy as np

from models.dispersal_model import OilDispersalModel
from models.impact_estimator import ImpactEstimator


class TestImpactEstimator(unittest.TestCase):
    """Test cases for the ImpactEstimator class."""
    
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
            'persistence_factor': 0.7,
            'co2_emission_factor': 3.0,
            'cleanup_difficulty': 3.0,
            'environmental_toxicity': 'moderate'
        }
        
        # Create a dispersal model instance for testing
        self.dispersal_model = OilDispersalModel(
            volume=1000,  # 1000 barrels
            oil_properties=self.oil_properties,
            time_hours=24,
            wind_speed=10.0,
            water_temp=15.0,
            wave_height=0.5
        )
        
        # Create an impact estimator instance
        self.impact_estimator = ImpactEstimator(
            dispersal_model=self.dispersal_model,
            environmental_sensitivity=1.0
        )
    
    def test_initialization(self):
        """Test that the estimator initializes correctly with given parameters."""
        self.assertEqual(self.impact_estimator.dispersal_model, self.dispersal_model)
        self.assertEqual(self.impact_estimator.environmental_sensitivity, 1.0)
        self.assertEqual(self.impact_estimator.oil_properties, self.oil_properties)
        self.assertEqual(self.impact_estimator.volume_m3, 1000 * 0.159)
        self.assertEqual(self.impact_estimator.volume_barrels, 1000)
    
    def test_calculate_surface_area(self):
        """Test surface area calculation."""
        # Calculate surface area
        surface_area = self.impact_estimator.calculate_surface_area()
        
        # Surface area should be positive
        self.assertGreater(surface_area, 0)
        
        # Surface area should match what's in the dispersal model
        affected_area = self.dispersal_model.calculate_affected_area()
        self.assertEqual(surface_area, affected_area['area_km2'])
        
        # Test caching - should return the same value without recalculating
        self.impact_estimator._surface_area = 123.456
        self.assertEqual(self.impact_estimator.calculate_surface_area(), 123.456)
    
    def test_calculate_co2_emissions(self):
        """Test CO2 emissions calculation."""
        # Calculate CO2 emissions
        co2_emissions = self.impact_estimator.calculate_co2_emissions()
        
        # CO2 emissions should be positive
        self.assertGreater(co2_emissions, 0)
        
        # Check that emissions scale with volume
        large_dispersal_model = OilDispersalModel(
            volume=10000,  # 10x more
            oil_properties=self.oil_properties,
            time_hours=24,
            wind_speed=10.0,
            water_temp=15.0,
            wave_height=0.5
        )
        
        large_impact_estimator = ImpactEstimator(
            dispersal_model=large_dispersal_model,
            environmental_sensitivity=1.0
        )
        
        large_co2_emissions = large_impact_estimator.calculate_co2_emissions()
        
        # Emissions should scale approximately linearly with volume
        # (not exactly due to different fractions)
        ratio = large_co2_emissions / co2_emissions
        self.assertGreater(ratio, 8)  # Should be close to 10x
        self.assertLess(ratio, 12)
        
        # Test caching - should return the same value without recalculating
        self.impact_estimator._co2_emissions = 123.456
        self.assertEqual(self.impact_estimator.calculate_co2_emissions(), 123.456)
    
    def test_estimate_cleanup_time(self):
        """Test cleanup time estimation."""
        # Estimate cleanup time
        cleanup_time = self.impact_estimator.estimate_cleanup_time()
        
        # Cleanup time should be positive
        self.assertGreater(cleanup_time, 0)
        
        # Check that cleanup time is affected by oil properties
        # Create a more difficult oil type
        heavy_oil_properties = dict(self.oil_properties)
        heavy_oil_properties['viscosity'] = 500.0  # More viscous
        heavy_oil_properties['persistence_factor'] = 0.9  # More persistent
        heavy_oil_properties['cleanup_difficulty'] = 5.0  # Higher difficulty
        
        heavy_dispersal_model = OilDispersalModel(
            volume=1000,
            oil_properties=heavy_oil_properties,
            time_hours=24,
            wind_speed=10.0,
            water_temp=15.0,
            wave_height=0.5
        )
        
        heavy_impact_estimator = ImpactEstimator(
            dispersal_model=heavy_dispersal_model,
            environmental_sensitivity=1.0
        )
        
        heavy_cleanup_time = heavy_impact_estimator.estimate_cleanup_time()
        
        # Heavy oil should take longer to clean up
        self.assertGreater(heavy_cleanup_time, cleanup_time)
        
        # Check that cleanup time is affected by environmental sensitivity
        sensitive_impact_estimator = ImpactEstimator(
            dispersal_model=self.dispersal_model,
            environmental_sensitivity=2.0  # More sensitive
        )
        
        sensitive_cleanup_time = sensitive_impact_estimator.estimate_cleanup_time()
        
        # More sensitive areas should take longer to clean up
        self.assertGreater(sensitive_cleanup_time, cleanup_time)
        
        # Test caching - should return the same value without recalculating
        self.impact_estimator._cleanup_time = 123.456
        self.assertEqual(self.impact_estimator.estimate_cleanup_time(), 123.456)
    
    def test_get_impact_summary(self):
        """Test that impact summary contains all expected information."""
        summary = self.impact_estimator.get_impact_summary()
        
        # Check that the summary contains all expected keys
        expected_keys = [
            'volume_barrels',
            'volume_m3',
            'surface_area_km2',
            'co2_emissions_tons',
            'cleanup_time_days',
            'oil_fractions',
            'slick_thickness_mm',
            'oil_type',
            'environmental_sensitivity'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # Check that values are of expected types
        self.assertIsInstance(summary['volume_barrels'], float)
        self.assertIsInstance(summary['volume_m3'], float)
        self.assertIsInstance(summary['surface_area_km2'], float)
        self.assertIsInstance(summary['co2_emissions_tons'], float)
        self.assertIsInstance(summary['cleanup_time_days'], float)
        self.assertIsInstance(summary['oil_fractions'], dict)
        self.assertIsInstance(summary['slick_thickness_mm'], float)
        self.assertIsInstance(summary['oil_type'], str)
        self.assertIsInstance(summary['environmental_sensitivity'], float)
    
    def test_estimate_wildlife_impact(self):
        """Test wildlife impact estimation."""
        # Estimate wildlife impact for different location types
        ocean_impact = self.impact_estimator.estimate_wildlife_impact('open_ocean')
        coastal_impact = self.impact_estimator.estimate_wildlife_impact('coastal')
        reef_impact = self.impact_estimator.estimate_wildlife_impact('reef')
        
        # Check that we have the expected keys
        expected_keys = [
            'location_type',
            'wildlife_density',
            'wildlife_vulnerability',
            'oil_toxicity',
            'mortality_rate',
            'birds_affected',
            'marine_mammals_affected',
            'fish_affected',
            'long_term_ecosystem_impact'
        ]
        
        for key in expected_keys:
            self.assertIn(key, ocean_impact)
        
        # Coastal and reef areas should have higher impacts than open ocean
        self.assertGreater(coastal_impact['wildlife_density'], ocean_impact['wildlife_density'])
        self.assertGreater(coastal_impact['mortality_rate'], ocean_impact['mortality_rate'])
        self.assertGreater(coastal_impact['birds_affected'], ocean_impact['birds_affected'])
        
        self.assertGreater(reef_impact['wildlife_density'], ocean_impact['wildlife_density'])
        self.assertGreater(reef_impact['long_term_ecosystem_impact'], ocean_impact['long_term_ecosystem_impact'])
    
    def test_estimate_economic_impact(self):
        """Test economic impact estimation."""
        # Estimate economic impact for different location types
        ocean_impact = self.impact_estimator.estimate_economic_impact('open_ocean')
        coastal_impact = self.impact_estimator.estimate_economic_impact('coastal')
        port_impact = self.impact_estimator.estimate_economic_impact('port')
        
        # Check that we have the expected keys
        expected_keys = [
            'cleanup_cost_usd',
            'environmental_damage_usd',
            'tourism_impact_usd',
            'fishery_impact_usd',
            'shipping_impact_usd',
            'total_economic_impact_usd',
            'cost_per_barrel_usd'
        ]
        
        for key in expected_keys:
            self.assertIn(key, ocean_impact)
        
        # Coastal areas should have higher tourism and fishery impacts
        self.assertGreater(coastal_impact['tourism_impact_usd'], ocean_impact['tourism_impact_usd'])
        self.assertGreater(coastal_impact['fishery_impact_usd'], ocean_impact['fishery_impact_usd'])
        
        # Ports should have shipping impacts
        self.assertGreater(port_impact['shipping_impact_usd'], 0)
        self.assertEqual(ocean_impact['shipping_impact_usd'], 0)
        
        # Total impact should be the sum of individual impacts
        total = (ocean_impact['cleanup_cost_usd'] +
                 ocean_impact['environmental_damage_usd'] +
                 ocean_impact['tourism_impact_usd'] +
                 ocean_impact['fishery_impact_usd'] +
                 ocean_impact['shipping_impact_usd'])
        
        self.assertEqual(ocean_impact['total_economic_impact_usd'], total)
        
        # Cost per barrel should be total divided by barrels
        cost_per_barrel = ocean_impact['total_economic_impact_usd'] / self.impact_estimator.volume_barrels
        self.assertEqual(ocean_impact['cost_per_barrel_usd'], int(cost_per_barrel))


if __name__ == '__main__':
    unittest.main()