"""
Oil Spill Dispersal Model
-------------------------
This module simulates the dispersal of oil in a marine environment
based on spill parameters and environmental conditions.
"""

import math
import numpy as np
from datetime import datetime, timedelta
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class OilDispersalModel:
    """
    Model for simulating the dispersal and behavior of oil spills.
    
    This class implements algorithms for calculating how oil spreads
    over water based on its physical properties, environmental conditions,
    and time since the spill occurred.
    """
    
    def __init__(self, volume, oil_properties, time_hours=24, 
                 wind_speed=10.0, water_temp=15.0, wave_height=0.5):
        """
        Initialize the dispersal model with spill and environmental parameters.
        
        Args:
            volume (float): Volume of oil spilled in barrels
            oil_properties (dict): Physical and chemical properties of the oil
            time_hours (float): Time since spill in hours (default: 24 hours)
            wind_speed (float): Wind speed in km/h (default: 10 km/h)
            water_temp (float): Water temperature in °C (default: 15°C)
            wave_height (float): Wave height in meters (default: 0.5m)
        """
        # Convert barrels to cubic meters (1 barrel = 0.159 cubic meters)
        self.volume_m3 = volume * 0.159
        self.oil_properties = oil_properties
        self.time_hours = time_hours
        self.wind_speed = wind_speed
        self.water_temp = water_temp
        self.wave_height = wave_height
        
        # Additional calculated properties
        self.density = oil_properties.get('density', 0.9)  # g/cm³
        self.viscosity = oil_properties.get('viscosity', 50.0)  # cP
        self.surface_tension = oil_properties.get('surface_tension', 25.0)  # mN/m
        self.evaporation_rate = oil_properties.get('evaporation_rate', 0.3)
        
        # Store the computed affected area and shape for later use
        self._affected_area = None
        self._spill_polygon = None
        self._slick_thickness = None
        self._evaporated_fraction = None
        self._dissolved_fraction = None
        
    def calculate_affected_area(self, lat=0.0, lon=0.0, simulate=True):
        """
        Calculate the water surface area affected by the oil spill.
        
        Args:
            lat (float): Latitude of the spill origin
            lon (float): Longitude of the spill origin
            simulate (bool): Whether to run the full simulation
            
        Returns:
            dict: Information about the affected area including:
                - area_km2: Total area in square kilometers
                - polygon: Shapely polygon of the affected area
                - center: Center coordinates (lat, lon)
                - thickness: Average slick thickness in mm
                - evaporated: Fraction of oil evaporated
                - dissolved: Fraction of oil dissolved
        """
        if simulate:
            self._run_simulation(lat, lon)
        
        # If we already calculated the affected area, return it
        if self._affected_area is not None:
            return self._affected_area
            
        # Calculate the initial slick area using the Fay algorithm
        # This is a simplified version of the Fay spreading equations
        time_seconds = self.time_hours * 3600
        
        # Calculate volume after evaporation and dissolution
        evaporated_fraction = self._calculate_evaporation()
        dissolved_fraction = self._calculate_dissolution()
        
        remaining_volume = self.volume_m3 * (1 - evaporated_fraction - dissolved_fraction)
        
        # Fay's equation for final area (simplified)
        # A = k * V^(3/4) * t^(1/4) * (g * Δρ/ρ)^(1/8) / (ν^(1/4) * σ^(1/2))
        # where:
        # - k is a constant (approximately 0.5-2.0)
        # - V is volume
        # - t is time
        # - g is gravitational acceleration
        # - Δρ/ρ is relative density difference
        # - ν is kinematic viscosity
        # - σ is surface tension
        
        k = 1.45  # Empirical constant
        g = 9.81  # Gravitational acceleration (m/s²)
        relative_density_diff = (1.03 - self.density) / 1.03  # Seawater density ≈ 1.03 g/cm³
        
        # Wind and wave effects - this is a simplification of complex processes
        wind_factor = 1.0 + (self.wind_speed / 20.0) * 0.5
        wave_factor = 1.0 + (self.wave_height / 1.0) * 0.3
        
        # Calculate area in m²
        area_m2 = (
            k * 
            (remaining_volume ** 0.75) * 
            (time_seconds ** 0.25) * 
            ((g * abs(relative_density_diff)) ** 0.125) / 
            ((self.viscosity * 0.001) ** 0.25 * (self.surface_tension * 0.001) ** 0.5) *
            wind_factor * 
            wave_factor
        )
        
        # Convert to km²
        area_km2 = area_m2 / 1_000_000
        
        # Calculate average slick thickness (mm)
        avg_thickness_mm = (remaining_volume / area_m2) * 1000
        
        # Store the affected area information
        self._affected_area = {
            'area_km2': area_km2,
            'center': (lat, lon),
            'thickness': avg_thickness_mm,
            'evaporated': evaporated_fraction,
            'dissolved': dissolved_fraction,
            'polygon': self._spill_polygon
        }
        
        return self._affected_area
    
    def _run_simulation(self, lat, lon):
        """
        Run a full simulation of the oil spill dispersal.
        
        Args:
            lat (float): Latitude of the spill origin
            lon (float): Longitude of the spill origin
        """
        # Calculate the evaporated and dissolved fractions
        self._evaporated_fraction = self._calculate_evaporation()
        self._dissolved_fraction = self._calculate_dissolution()
        
        # Calculate the spreading using a simplified model
        self._simulate_spreading(lat, lon)
    
    def _calculate_evaporation(self):
        """
        Calculate the fraction of oil that has evaporated based on time and conditions.
        
        Returns:
            float: Fraction of oil evaporated (0.0 to 1.0)
        """
        # Simplified evaporation model using oil properties and environmental factors
        # E(t) = Emax * (1 - exp(-k * t))
        # where:
        # - Emax is the maximum fraction that can evaporate (based on oil type)
        # - k is an evaporation rate constant affected by temperature and wind
        
        # Base rate from oil properties
        base_evap_rate = self.oil_properties.get('evaporation_rate', 0.3)
        
        # Temperature effect: evaporation increases with temperature
        # Simple linear relationship with reference at 15°C
        temp_factor = 1.0 + (self.water_temp - 15.0) * 0.03
        
        # Wind effect: evaporation increases with wind speed
        # Simple linear relationship with reference at 10 km/h
        wind_factor = 1.0 + (self.wind_speed - 10.0) * 0.02
        
        # Compute effective evaporation rate
        effective_rate = base_evap_rate * temp_factor * wind_factor
        
        # Maximum evaporation is based on the oil's composition
        max_evaporation = min(0.9, self.oil_properties.get('evaporation_rate', 0.3) * 2.5)
        
        # Time-dependent evaporation using exponential decay model
        evaporation_constant = 0.05  # per hour
        evaporated_fraction = max_evaporation * (1 - math.exp(-evaporation_constant * self.time_hours))
        
        # Limit to physical bounds
        evaporated_fraction = min(max(0.0, evaporated_fraction), max_evaporation)
        
        return evaporated_fraction
    
    def _calculate_dissolution(self):
        """
        Calculate the fraction of oil that has dissolved in water.
        
        Returns:
            float: Fraction of oil dissolved (0.0 to 1.0)
        """
        # Simplified dissolution model
        # Dissolution is affected by oil solubility, water temperature, wave action
        
        base_solubility = self.oil_properties.get('solubility', 0.01)
        
        # Temperature effect: dissolution increases with temperature
        temp_factor = 1.0 + (self.water_temp - 15.0) * 0.02
        
        # Wave effect: dissolution increases with wave action
        wave_factor = 1.0 + (self.wave_height - 0.5) * 0.5
        
        # Time effect: dissolution is time-dependent but saturates
        time_factor = min(1.0, self.time_hours / 48.0)
        
        dissolved_fraction = base_solubility * temp_factor * wave_factor * time_factor
        
        # Limit to physical bounds
        dissolved_fraction = min(max(0.0, dissolved_fraction), 0.2)  # Dissolution rarely exceeds 20%
        
        return dissolved_fraction
    
    def _simulate_spreading(self, lat, lon):
        """
        Simulate the spreading of oil to generate a polygon representing the affected area.
        
        Args:
            lat (float): Latitude of the spill origin
            lon (float): Longitude of the spill origin
        """
        # Simplified model for generating a polygon representing the spill
        # In a real model, this would be based on ocean currents, wind patterns, etc.
        
        # Calculate the primary dimensions of the spill based on our affected area
        if self._affected_area is None:
            area_info = self.calculate_affected_area(lat, lon, simulate=False)
            area_km2 = area_info['area_km2']
        else:
            area_km2 = self._affected_area['area_km2']
        
        # Convert area to radius (assuming circular shape as starting point)
        # A = πr²
        radius_km = math.sqrt(area_km2 / math.pi)
        
        # Deform the circle based on wind direction (simplified)
        # We'll assume the wind is blowing towards the north-east (45°)
        # In a real model, wind direction would be an input parameter
        wind_direction_rad = math.radians(45)
        
        # Wind deformation factor
        wind_deform = min(0.6, self.wind_speed / 60.0)
        
        # Create points around the perimeter with some deformation
        num_points = 36  # Number of points around the perimeter
        polygon_points = []
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            
            # Deform the radius based on wind direction
            # Maximum elongation in the wind direction, compression perpendicular to it
            angle_diff = abs(((angle - wind_direction_rad + math.pi) % (2 * math.pi)) - math.pi)
            stretch_factor = 1.0 + (wind_deform * math.cos(angle_diff))
            
            # Calculate the deformed radius for this angle
            r = radius_km * stretch_factor
            
            # Add some randomness for a more realistic shape
            r *= 1.0 + 0.1 * np.random.rand()
            
            # Convert to lat/lon coordinates (simplified)
            # 111 km per degree of latitude, 111*cos(lat) km per degree of longitude
            delta_lat = r / 111.0 * math.sin(angle)
            delta_lon = r / (111.0 * math.cos(math.radians(lat))) * math.cos(angle)
            
            point_lat = lat + delta_lat
            point_lon = lon + delta_lon
            
            polygon_points.append((point_lon, point_lat))
        
        # Create a shapely polygon from the points
        self._spill_polygon = Polygon(polygon_points)
    
    def get_volume_fractions(self):
        """
        Get the fractions of oil in different states.
        
        Returns:
            dict: Fractions of oil (evaporated, dissolved, surface)
        """
        if self._evaporated_fraction is None:
            self._evaporated_fraction = self._calculate_evaporation()
            
        if self._dissolved_fraction is None:
            self._dissolved_fraction = self._calculate_dissolution()
            
        surface_fraction = 1.0 - self._evaporated_fraction - self._dissolved_fraction
        
        return {
            'evaporated': self._evaporated_fraction,
            'dissolved': self._dissolved_fraction,
            'surface': surface_fraction
        }
    
    def get_slick_thickness(self):
        """
        Get the estimated average thickness of the oil slick.
        
        Returns:
            float: Average thickness in millimeters
        """
        if self._affected_area is None:
            self.calculate_affected_area()
            
        return self._affected_area['thickness']