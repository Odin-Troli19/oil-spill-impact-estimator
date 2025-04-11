"""
Visualization Utilities
----------------------
Functions for creating maps and charts to visualize oil spill impacts.
"""

import os
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import webbrowser
from pathlib import Path
import tempfile
from shapely.geometry import mapping, Point, Polygon
from datetime import datetime

# Import local modules
from .geo_utils import get_lat_lon_bounds, calculate_area_from_polygon


def create_map(latitude, longitude, affected_area, oil_type, volume, output_file='spill_map.html'):
    """
    Create an interactive map visualization of the oil spill.
    
    Args:
        latitude (float): Latitude of the spill origin
        longitude (float): Longitude of the spill origin
        affected_area (dict): Dict with area info including polygon and area_km2
        oil_type (str): Type of oil spilled
        volume (float): Volume of oil spilled in barrels
        output_file (str): Path to save the HTML map file
        
    Returns:
        str: Path to the saved map file
    """
    # Determine map bounds based on the affected area
    if affected_area.get('polygon'):
        # Calculate the appropriate zoom based on the affected area
        area_km2 = affected_area.get('area_km2', 10)
        radius_km = max(5, np.sqrt(area_km2 / np.pi) * 3)  # 3x the radius for good visibility
        bounds = affected_area.get('polygon').bounds
        min_lon, min_lat, max_lon, max_lat = bounds
    else:
        # If no polygon is available, use a default radius
        radius_km = 20
        min_lon, min_lat, max_lon, max_lat = get_lat_lon_bounds(latitude, longitude, radius_km)
    
    # Create a map centered on the spill location
    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=8,
        tiles='CartoDB positron'  # Clean, light background
    )
    
    # Add a marker for the spill origin
    folium.Marker(
        location=[latitude, longitude],
        popup=f"<strong>Oil Spill Origin</strong><br>"
              f"Volume: {volume:,.0f} barrels<br>"
              f"Oil Type: {oil_type}<br>"
              f"Date: {datetime.now().strftime('%Y-%m-%d')}<br>"
              f"Coordinates: {latitude:.4f}, {longitude:.4f}",
        icon=folium.Icon(color='red', icon='exclamation-circle', prefix='fa')
    ).add_to(m)
    
    # Add the affected area polygon
    if affected_area.get('polygon'):
        # Get color based on oil type or thickness
        if 'color' in affected_area:
            fill_color = affected_area['color']
        else:
            # Default oil spill color scheme - darker for thicker areas
            fill_color = '#782D2D'  # Dark reddish brown
        
        # Convert shapely polygon to GeoJSON
        polygon_geojson = mapping(affected_area['polygon'])
        
        # Add the polygon to the map
        folium.GeoJson(
            polygon_geojson,
            name="Oil Spill Extent",
            style_function=lambda x: {
                'fillColor': fill_color,
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=f"Affected Area: {affected_area['area_km2']:.2f} km²"
        ).add_to(m)
        
        # Add a gradient effect for more realistic visualization
        # Create points within the polygon with varying opacity based on distance from center
        if affected_area.get('center'):
            # Extract coordinates from polygon for heat map
            polygon = affected_area['polygon']
            x, y = polygon.exterior.coords.xy
            
            # Create heat map points with weights
            heat_data = []
            for i in range(len(x)):
                # Skip some points to reduce density
                if i % 3 == 0:
                    # Weight decreases toward the edge
                    weight = 1.0 - (i / len(x))
                    heat_data.append([y[i], x[i], weight])
            
            # Add heat map
            HeatMap(
                heat_data,
                radius=15,
                blur=20,
                max_zoom=10,
                gradient={0.4: '#FFF5B8', 0.65: '#E8A238', 0.8: '#8E4E27', 1: '#782D2D'}
            ).add_to(m)
    
    # Add scale bar
    folium.plugins.MeasureControl(position='bottomleft', primary_length_unit='kilometers').add_to(m)
    
    # Add fullscreen button
    folium.plugins.Fullscreen().add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Fit the map to the bounds
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    
    # Add title and information
    title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 300px; height: 90px; 
                    background-color: white; border-radius: 5px; 
                    border: 2px solid grey; z-index: 9999; padding: 10px; 
                    font-size: 14px; font-family: Arial;">
            <b style="font-size: 16px;">Oil Spill Impact Estimation</b><br>
            Volume: {volume:,.0f} barrels<br>
            Affected Area: {affected_area['area_km2']:.2f} km²<br>
            Oil Type: {oil_type}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save the map to file
    output_path = Path(output_file)
    m.save(str(output_path))
    
    return str(output_path)


def display_map(map_file):
    """
    Open the generated map in the default web browser.
    
    Args:
        map_file (str): Path to the HTML map file
    """
    # Convert to absolute path
    map_path = os.path.abspath(map_file)
    
    # Open in web browser
    webbrowser.open('file://' + map_path)


def generate_impact_charts(impact_data, output_dir=None):
    """
    Generate charts visualizing the environmental impact of the oil spill.
    
    Args:
        impact_data (dict): Dictionary containing impact metrics
        output_dir (str): Directory to save chart images (None for temp dir)
        
    Returns:
        dict: Paths to the generated chart images
    """
    # Use temporary directory if no output directory specified
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    # Set Seaborn style
    sns.set(style="whitegrid")
    
    chart_files = {}
    
    # 1. Oil Distribution Chart (Pie Chart)
    if 'oil_fractions' in impact_data:
        plt.figure(figsize=(8, 6))
        fractions = impact_data['oil_fractions']
        labels = ['Evaporated', 'Dissolved', 'Surface']
        sizes = [fractions['evaporated'], fractions['dissolved'], fractions['surface']]
        colors = ['#f4d166', '#5fa3db', '#d93b48']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                startangle=90, shadow=False)
        plt.axis('equal')
        plt.title('Oil Distribution by State')
        
        # Save chart
        oil_dist_file = os.path.join(output_dir, 'oil_distribution.png')
        plt.savefig(oil_dist_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files['oil_distribution'] = oil_dist_file
    
    # 2. Environmental Impact Chart (Bar Chart)
    if all(k in impact_data for k in ['surface_area_km2', 'co2_emissions_tons', 'cleanup_time_days']):
        plt.figure(figsize=(10, 6))
        
        # Normalize values for comparison
        impact_values = {
            'Surface Area (km²)': impact_data['surface_area_km2'],
            'CO₂ Emissions (tons)': impact_data['co2_emissions_tons'] / 100,  # Scale down for visualization
            'Cleanup Time (days)': impact_data['cleanup_time_days'] * 5  # Scale up for visualization
        }
        
        # Create bar chart
        bars = plt.bar(impact_values.keys(), impact_values.values(), color=['#5fa3db', '#d93b48', '#8e7cc3'])
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom')
        
        plt.title('Environmental Impact Metrics')
        plt.ylabel('Normalized Values')
        plt.tight_layout()
        
        # Add a note about normalization
        plt.figtext(0.5, 0.01, 
                   "Note: CO₂ emissions divided by 100, cleanup time multiplied by 5 for visualization",
                   ha="center", fontsize=8, style='italic')
        
        # Save chart
        impact_file = os.path.join(output_dir, 'environmental_impact.png')
        plt.savefig(impact_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files['environmental_impact'] = impact_file
    
    # 3. Timeline Projection Chart
    if 'cleanup_time_days' in impact_data:
        plt.figure(figsize=(10, 6))
        
        # Create timeline data
        days = np.arange(0, int(impact_data['cleanup_time_days']) + 1)
        cleanup_progress = 100 * (1 - np.exp(-3 * days / impact_data['cleanup_time_days']))
        
        # Oil persistence (decreasing over time)
        if 'oil_fractions' in impact_data:
            surface_oil = 100 * impact_data['oil_fractions']['surface'] * np.exp(-4 * days / impact_data['cleanup_time_days'])
        else:
            surface_oil = 100 * np.exp(-4 * days / impact_data['cleanup_time_days'])
        
        # Plot the data
        plt.plot(days, cleanup_progress, 'b-', linewidth=2, label='Cleanup Progress (%)')
        plt.plot(days, surface_oil, 'r-', linewidth=2, label='Surface Oil Remaining (%)')
        
        # Add vertical line for estimated cleanup completion
        plt.axvline(x=impact_data['cleanup_time_days'], linestyle='--', color='gray')
        plt.text(impact_data['cleanup_time_days'] + 0.5, 50, 
                f"Estimated Cleanup: {impact_data['cleanup_time_days']:.1f} days", 
                rotation=90, va='center')
        
        plt.title('Oil Spill Cleanup Timeline Projection')
        plt.xlabel('Days Since Spill')
        plt.ylabel('Percentage')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Save chart
        timeline_file = os.path.join(output_dir, 'cleanup_timeline.png')
        plt.savefig(timeline_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files['cleanup_timeline'] = timeline_file
    
    return chart_files


def generate_comparison_chart(baseline_impact, scenarios, output_file=None):
    """
    Generate a chart comparing different oil spill scenarios.
    
    Args:
        baseline_impact (dict): Impact data for the baseline scenario
        scenarios (list): List of dicts with scenario impact data
        output_file (str): Path to save the chart image
        
    Returns:
        str: Path to the generated chart image
    """
    # Ensure we have at least one scenario to compare
    if not scenarios:
        return None
    
    # Use a temporary file if no output file specified
    if output_file is None:
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, 'scenario_comparison.png')
    
    # Set style
    sns.set(style="whitegrid")
    
    # Setup the figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    
    # Metrics to compare
    metrics = ['surface_area_km2', 'co2_emissions_tons', 'cleanup_time_days']
    titles = ['Surface Area (km²)', 'CO₂ Emissions (tons)', 'Cleanup Time (days)']
    colors = ['#5fa3db', '#d93b48', '#8e7cc3']
    
    # Prepare data for comparison
    scenario_names = ['Baseline'] + [s.get('name', f'Scenario {i+1}') for i, s in enumerate(scenarios)]
    
    # Plot each metric
    for i, (metric, title) in enumerate(zip(metrics, titles)):
        # Extract values for this metric
        values = [baseline_impact.get(metric, 0)]
        values.extend([s.get(metric, 0) for s in scenarios])
        
        # Create the bar chart
        bars = axes[i].bar(scenario_names, values, color=colors[i], alpha=0.7)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        axes[i].set_title(title)
        axes[i].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_animation_frames(dispersal_model, lat, lon, time_steps, output_dir):
    """
    Create a series of map images showing the progression of the oil spill over time.
    
    Args:
        dispersal_model (OilDispersalModel): The dispersal model
        lat (float): Latitude of the spill
        lon (float): Longitude of the spill
        time_steps (list): List of time points in hours
        output_dir (str): Directory to save the frames
        
    Returns:
        list: Paths to the generated frame images
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    frame_files = []
    
    # Create a frame for each time step
    for i, hours in enumerate(time_steps):
        # Update model time
        dispersal_model.time_hours = hours
        
        # Calculate affected area
        affected_area = dispersal_model.calculate_affected_area(lat, lon)
        
        # Create the map
        frame_file = os.path.join(output_dir, f'frame_{i:03d}.html')
        create_map(
            latitude=lat,
            longitude=lon,
            affected_area=affected_area,
            oil_type=dispersal_model.oil_properties.get('name', 'Unknown'),
            volume=dispersal_model.volume_m3 / 0.159,  # Convert back to barrels
            output_file=frame_file
        )
        
        frame_files.append(frame_file)
    
    return frame_files