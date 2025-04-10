# oil-spill-impact-estimator
A Python-based tool to estimate the environmental impact of oil spills using geospatial mapping and simplified dispersal models.

# Oil Spill Impact Estimator

A Python-based tool to estimate the environmental impact of oil spills using geospatial mapping and simplified dispersal models.

## Overview

This project provides a simulation and visualization platform for estimating the effects of oil spills. Given basic inputs like spill volume, oil type, and coordinates, it calculates the affected water surface area, CO₂-equivalent emissions, and estimated cleanup time. Maps are rendered using Folium or GeoPandas to visualize the spill impact.

## Inputs

- Spill volume (in barrels or liters)
- Spill coordinates (latitude and longitude)
- Type of oil (e.g., crude, diesel, bunker fuel)

## Outputs

- Estimated surface area affected (km²)
- Estimated CO₂-equivalent emissions (kg)
- Approximate cleanup time (in days)
- Interactive map of the affected region

## Features

- Geospatial visualization using Folium/GeoPandas
- Basic oil dispersal simulation
- Oil property database (density, spread rate, emissions factor)
- Modular and extensible architecture
- Unit-tested core logic

## 🗂 Project Structure

