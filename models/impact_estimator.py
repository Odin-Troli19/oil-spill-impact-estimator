"""
Oil Spill Impact Estimator
--------------------------
This module provides functionality for estimating the environmental impact
of oil spills, including affected surface area, carbon emissions, and
cleanup time.
"""

import math
import numpy as np
from datetime import datetime, timedelta


class ImpactEstimator:
    """
    Estimates the environmental impact of oil spills based on
    dispersal model outputs and oil properties.
    """
    
    def __init__(self, dispersal_model, environmental_sensitivity=1.0):
        """
        Initialize the impact estimator.
        
        Args:
            dispersal_model (OilDispersalModel): An initialized oil dispersal model
            environmental_sensitivity (float): A factor representing the environmental
                sensitivity of the spill location (1.0 = average, higher = more sensitive)
        """
        self.dispersal_model = dispersal_model
        self.environmental_sensitivity = environmental_sensitivity
        
        # Extract relevant properties from the dispersal model
        self.oil_properties = dispersal_model.oil_properties
        self.volume_m3 = dispersal_model.volume_m3
        self.volume_barrels = self.volume_m3 / 0.159  # Convert m³ to barrels
        
        # Cache for calculated values
        self._surface_area = None
        self._co2_emissions = None
        self._cleanup_time = None

    def calculate_surface_area(self):
        """
        Calculate the water surface area affected by the oil spill.
        
        Returns:
            float: Affected surface area in square kilometers
        """
        if self._surface_area is not None:
            return self._surface_area
            
        # Use the dispersal model to calculate the affected area
        affected_area = self.dispersal_model.calculate_affected_area()
        self._surface_area = affected_area['area_km2']
        
        return self._surface_area
        
    def calculate_co2_emissions(self):
        """
        Calculate the CO2 equivalent emissions from the oil spill.
        
        This includes both the direct emissions from the oil and the
        emissions associated with cleanup activities.
        
        Returns:
            float: CO2 equivalent emissions in metric tons
        """
        if self._co2_emissions is not None:
            return self._co2_emissions
        
        # Get oil fractions in different states
        fractions = self.dispersal_model.get_volume_fractions()
        evaporated = fractions['evaporated']
        dissolved = fractions['dissolved']
        surface = fractions['surface']
        
        # Oil-specific CO2 emission factor (metric tons CO2 per barrel)
        emission_factor = self.oil_properties.get('co2_emission_factor', 3.0)
        
        # Direct emissions from evaporated oil
        # Evaporated hydrocarbons eventually oxidize to CO2 in the atmosphere
        evaporated_emissions = self.volume_barrels * evaporated * emission_factor
        
        # Dissolved oil has a lower emission factor since some carbon stays in water
        dissolved_emissions = self.volume_barrels * dissolved * emission_factor * 0.5
        
        # Surface oil emissions depend on cleanup methods and natural degradation
        # This is a simplified estimate
        surface_emissions = self.volume_barrels * surface * emission_factor * 0.8
        
        # Additional emissions from cleanup operations
        # Based on energy used for cleanup per barrel of oil
        cleanup_emissions_factor = 0.1  # metric tons CO2 per barrel for cleanup
        cleanup_emissions = self.volume_barrels * surface * cleanup_emissions_factor
        
        # Total CO2 equivalent emissions
        total_emissions = evaporated_emissions + dissolved_emissions + surface_emissions + cleanup_emissions
        
        self._co2_emissions = total_emissions
        return total_emissions
        
    def estimate_cleanup_time(self):
        """
        Estimate the time required for cleanup operations.
        
        Returns:
            float: Estimated cleanup time in days
        """
        if self._cleanup_time is not None:
            return self._cleanup_time
            
        # Base cleanup time calculation
        # Factors affecting cleanup time:
        # 1. Volume of oil
        # 2. Type of oil (viscosity, persistence)
        # 3. Affected area
        # 4. Environmental sensitivity
        # 5. Weathering conditions (temp, wind, waves)
        
        # Base time per volume (days per 1000 barrels)
        base_time_per_volume = 1.5
        
        # Oil property factors
        viscosity = self.oil_properties.get('viscosity', 50.0)
        persistence = self.oil_properties.get('persistence_factor', 0.8)
        cleanup_difficulty = self.oil_properties.get('cleanup_difficulty', 3.0)
        
        # Calculate basic cleanup time based on volume
        volume_factor = self.volume_barrels / 1000
        basic_time = base_time_per_volume * volume_factor
        
        # Adjust for oil properties
        # Higher viscosity means longer cleanup
        viscosity_factor = min(3.0, max(0.5, (viscosity / 100.0) * 1.5))
        
        # Higher persistence means longer cleanup
        persistence_factor = min(2.0, max(1.0, persistence * 2.0))
        
        # Specific cleanup difficulty rating
        difficulty_factor = cleanup_difficulty / 3.0
        
        # Environmental conditions from the dispersal model
        wave_height = self.dispersal_model.wave_height
        wind_speed = self.dispersal_model.wind_speed
        water_temp = self.dispersal_model.water_temp
        
        # Weather factors
        # High waves make cleanup more difficult
        wave_factor = min(2.0, max(0.8, 0.8 + wave_height * 0.4))
        
        # High winds make cleanup more difficult
        wind_factor = min(1.5, max(0.8, 0.8 + (wind_speed / 20.0) * 0.5))
        
        # Cold temperatures increase cleanup time
        temp_factor = min(1.5, max(0.8, 1.5 - (water_temp / 30.0) * 0.5))
        
        # Area factor - larger areas take longer to clean but with diminishing returns
        area = self.calculate_surface_area()
        area_factor = min(3.0, max(1.0, 0.5 + (area / 100.0) * 0.5))
        
        # Environmental sensitivity factor
        sensitivity_factor = min(2.0, max(0.8, self.environmental_sensitivity))
        
        # Final cleanup time calculation with all factors
        cleanup_time = (
            basic_time *
            viscosity_factor *
            persistence_factor *
            difficulty_factor *
            wave_factor *
            wind_factor *
            temp_factor *
            area_factor *
            sensitivity_factor
        )
        
        # Add a small random component for natural variation
        randomness = np.random.normal(1.0, 0.05)  # 5% standard deviation
        cleanup_time *= randomness
        
        # Ensure the result is positive and reasonable
        cleanup_time = max(1.0, cleanup_time)
        
        self._cleanup_time = cleanup_time
        return cleanup_time
        
    def get_impact_summary(self):
        """
        Get a comprehensive summary of the environmental impact.
        
        Returns:
            dict: Summary of all calculated impacts
        """
        # Calculate all impacts if not already done
        surface_area = self.calculate_surface_area()
        co2_emissions = self.calculate_co2_emissions()
        cleanup_time = self.estimate_cleanup_time()
        
        # Get oil fractions
        fractions = self.dispersal_model.get_volume_fractions()
        
        # Get affected area details
        affected_area = self.dispersal_model.calculate_affected_area()
        
        # Compile the summary
        summary = {
            'volume_barrels': self.volume_barrels,
            'volume_m3': self.volume_m3,
            'surface_area_km2': surface_area,
            'co2_emissions_tons': co2_emissions,
            'cleanup_time_days': cleanup_time,
            'oil_fractions': fractions,
            'slick_thickness_mm': affected_area['thickness'],
            'oil_type': self.oil_properties.get('name', 'Unknown'),
            'environmental_sensitivity': self.environmental_sensitivity
        }
        
        return summary
    
    def estimate_wildlife_impact(self, location_type='open_ocean'):
        """
        Estimate the potential impact on wildlife in the affected area.
        
        Args:
            location_type (str): Type of location ('open_ocean', 'coastal', 'estuary', etc.)
            
        Returns:
            dict: Wildlife impact metrics
        """
        # Base impact metrics by location type
        base_impacts = {
            'open_ocean': {'density': 0.2, 'vulnerability': 0.6},
            'coastal': {'density': 0.8, 'vulnerability': 0.8},
            'estuary': {'density': 1.0, 'vulnerability': 1.0},
            'reef': {'density': 1.2, 'vulnerability': 0.9},
            'wetland': {'density': 1.0, 'vulnerability': 1.0},
            'river': {'density': 0.7, 'vulnerability': 0.8}
        }
        
        # Default to open ocean if location type not recognized
        if location_type not in base_impacts:
            location_type = 'open_ocean'
            
        # Get base impact values for this location
        density = base_impacts[location_type]['density']
        vulnerability = base_impacts[location_type]['vulnerability']
        
        # Calculate affected area
        surface_area = self.calculate_surface_area()
        
        # Calculate toxicity factor based on oil properties
        if 'environmental_toxicity' in self.oil_properties:
            toxicity_map = {
                'low': 0.3,
                'moderate': 0.6,
                'high': 0.8,
                'very high': 1.0
            }
            toxicity = toxicity_map.get(
                self.oil_properties['environmental_toxicity'].lower(),
                0.6  # Default to moderate if not specified
            )
        else:
            # Estimate toxicity from other properties if not explicitly given
            viscosity = self.oil_properties.get('viscosity', 50.0)
            density = self.oil_properties.get('density', 0.9)
            toxicity = min(1.0, max(0.3, (density - 0.8) * 2.0 + (viscosity / 1000.0) * 0.5))
        
        # Calculate volume factor - larger spills have worse impacts
        volume_factor = min(1.0, max(0.1, 0.1 + math.log10(self.volume_barrels / 100) * 0.3))
        
        # Calculate persistence impact
        persistence = self.oil_properties.get('persistence_factor', 0.8)
        
        # Estimate affected wildlife indicators
        mortality_rate = vulnerability * toxicity * volume_factor * persistence * 0.8
        
        # Estimate affected populations based on area and density
        birds_affected = surface_area * density * 100 * vulnerability
        marine_mammals_affected = surface_area * density * 5 * vulnerability
        fish_affected = surface_area * density * 1000 * vulnerability * 0.5  # Fish can avoid somewhat
        
        # Compile wildlife impact summary
        wildlife_impact = {
            'location_type': location_type,
            'wildlife_density': density,
            'wildlife_vulnerability': vulnerability,
            'oil_toxicity': toxicity,
            'mortality_rate': mortality_rate,
            'birds_affected': int(birds_affected),
            'marine_mammals_affected': int(marine_mammals_affected),
            'fish_affected': int(fish_affected),
            'long_term_ecosystem_impact': persistence * toxicity * self.environmental_sensitivity
        }
        
        return wildlife_impact
    
    def estimate_economic_impact(self, location_type='open_ocean'):
        """
        Estimate the economic impact of the oil spill.
        
        Args:
            location_type (str): Type of location affecting economic activities
            
        Returns:
            dict: Economic impact metrics in USD
        """
        # Calculate base cleanup cost
        # Average cleanup cost per barrel (USD)
        base_cleanup_cost_per_barrel = 10000
        
        # Location multipliers for cleanup costs
        location_multipliers = {
            'open_ocean': 1.0,
            'coastal': 2.0,
            'estuary': 2.5,
            'reef': 3.0,
            'wetland': 2.5,
            'river': 2.0,
            'port': 1.8
        }
        
        # Default to open ocean if location type not recognized
        location_mult = location_multipliers.get(location_type, 1.0)
        
        # Oil specific cleanup difficulty
        cleanup_difficulty = self.oil_properties.get('cleanup_difficulty', 3.0) / 3.0
        
        # Calculate cleanup cost
        cleanup_cost = (
            self.volume_barrels * 
            base_cleanup_cost_per_barrel * 
            location_mult * 
            cleanup_difficulty
        )
        
        # Calculate environmental damage cost (more abstract)
        surface_area = self.calculate_surface_area()
        environmental_damage = surface_area * 500000 * self.environmental_sensitivity
        
        # Calculate economic losses by sector
        tourism_impact = 0
        fishery_impact = 0
        shipping_impact = 0
        
        if location_type in ['coastal', 'reef', 'estuary']:
            # Tourism impacts for coastal areas
            tourism_impact = surface_area * 100000 * location_mult
            
        if location_type in ['coastal', 'estuary', 'river', 'reef']:
            # Fishery impacts
            fishery_impact = surface_area * 50000 * self.oil_properties.get('toxicity', 0.6)
            
        if location_type in ['port', 'river']:
            # Shipping/port impacts
            shipping_impact = 500000 * cleanup_difficulty * location_mult
        
        # Total economic impact
        total_economic_impact = cleanup_cost + environmental_damage + tourism_impact + fishery_impact + shipping_impact
        
        # Compile economic impact summary
        economic_impact = {
            'cleanup_cost_usd': int(cleanup_cost),
            'environmental_damage_usd': int(environmental_damage),
            'tourism_impact_usd': int(tourism_impact),
            'fishery_impact_usd': int(fishery_impact),
            'shipping_impact_usd': int(shipping_impact),
            'total_economic_impact_usd': int(total_economic_impact),
            'cost_per_barrel_usd': int(total_economic_impact / self.volume_barrels)
        }
        
        return economic_impact