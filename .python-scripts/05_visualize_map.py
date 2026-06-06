"""
Script 05: Interactive map visualization
Creates an HTML map with hexagons colored by density
"""

import json
import folium
from folium import plugins
from branca.colormap import LinearColormap
import webbrowser
import os

def load_geojson(filename="outputs/hexagons.geojson"):
    """Load the GeoJSON file with hexagon polygons"""
    with open(filename, "r") as f:
        return json.load(f)

def load_aggregated_data(filename="data/hexagon_aggregated.json"):
    """Load aggregated hexagon statistics"""
    with open(filename, "r") as f:
        return json.load(f)

def create_color_map():
    """Create a color map for density levels"""
    # RGB: Green (low) -> Yellow (medium) -> Red (high)
    colors = ['#2ecc71', '#f1c40f', '#e74c3c']
    vmin = 0
    vmax = 100
    
    return LinearColormap(colors, vmin=vmin, vmax=vmax)

def get_hexagon_color(point_count, density_level):
    """Get color based on density level"""
    if density_level == "HIGH":
        return '#e74c3c'  # Red
    elif density_level == "MEDIUM":
        return '#f1c40f'  # Yellow
    else:
        return '#2ecc71'  # Green

def create_popup_content(hexagon_props):
    """Create HTML content for popup tooltip"""
    density_color = {
        "HIGH": "🔴",
        "MEDIUM": "🟡", 
        "LOW": "🟢"
    }.get(hexagon_props.get("density_level", "LOW"), "⚪")
    
    return f"""
    <div style="font-family: monospace; font-size: 12px; min-width: 200px;">
        <b style="font-size: 14px;">{density_color} Hexagon Stats</b>
        <hr style="margin: 5px 0;">
        <b>📍 Points:</b> {hexagon_props.get('point_count', 0)}<br>
        <b>🚗 Vehicles:</b> {hexagon_props.get('unique_vehicles', 0)}<br>
        <b>⚡ Avg Speed:</b> {hexagon_props.get('avg_speed', 0)} km/h<br>
        <b>🐢 Min Speed:</b> {hexagon_props.get('min_speed', 0)} km/h<br>
        <b>🐰 Max Speed:</b> {hexagon_props.get('max_speed', 0)} km/h<br>
        <b>📊 Density:</b> {hexagon_props.get('density_level', 'UNKNOWN')}
    </div>
    """

def add_hexagon_points_map(geojson_data, hexagon_stats):
    """Create main map with hexagons"""
    
    # Center around Caracas
    center_lat = 10.4806
    center_lng = -66.9036
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles='CartoDB dark_matter',  # Dark mode map
        control_scale=True
    )
    
    # Create a lookup for quick stats access
    stats_lookup = {stat['h3_index']: stat for stat in hexagon_stats}
    
    # Add hexagon layers
    for feature in geojson_data['features']:
        h3_index = feature['h3_index']
        props = feature['properties']
        
        # Get density-based color
        density_level = props.get('density_level', 'LOW')
        color = get_hexagon_color(props.get('point_count', 0), density_level)
        
        # Create popup
        popup_html = create_popup_content(props)
        popup = folium.Popup(popup_html, max_width=300)
        
        # Add hexagon polygon
        folium.GeoJson(
            feature,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'white',
                'weight': 1,
                'fillOpacity': 0.6,
                'opacity': 0.8
            },
            popup=popup,
            tooltip=f"📊 {props.get('point_count', 0)} points | {density_level} density"
        ).add_to(m)
    
    return m

def add_original_points_map(m):
    """Add original GPS points as markers (optional layer)"""
    try:
        with open("data/points.json", "r") as f:
            points = json.load(f)
        
        # Create a feature group for points
        fg_points = folium.FeatureGroup(name="📍 GPS Points (Show/Hide)")
        
        # Add a subset of points (every 20th point to avoid clutter)
        for i, point in enumerate(points[::20]):  # Show only 5% of points
            folium.CircleMarker(
                location=[point['lat'], point['lng']],
                radius=3,
                color='cyan',
                fill=True,
                fill_color='cyan',
                fill_opacity=0.5,
                popup=f"Vehicle: {point['vehicle_id']}<br>Speed: {point['speed']} km/h",
                weight=1
            ).add_to(fg_points)
        
        fg_points.add_to(m)
        return True
    except Exception as e:
        print(f"⚠️ Could not load original points: {e}")
        return False

def add_heatmap_layer(m):
    """Add heatmap layer for density visualization"""
    try:
        with open("data/points.json", "r") as f:
            points = json.load(f)
        
        # Prepare data for heatmap
        heat_data = [[point['lat'], point['lng']] for point in points]
        
        # Add heatmap plugin
        plugins.HeatMap(
            heat_data,
            radius=15,
            blur=10,
            max_zoom=1,
            min_opacity=0.3
        ).add_to(m)
        
        return True
    except Exception as e:
        print(f"⚠️ Could not add heatmap: {e}")
        return False

def add_legend(m):
    """Add a legend to the map"""
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; 
                right: 10px; 
                z-index: 1000; 
                background-color: rgba(0,0,0,0.8); 
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 12px;
                border: 1px solid #444;">
        <b>📊 Density Legend</b><br>
        <span style="color: #e74c3c;">🔴 HIGH</span> (≥50 points)<br>
        <span style="color: #f1c40f;">🟡 MEDIUM</span> (20-49 points)<br>
        <span style="color: #2ecc71;">🟢 LOW</span> (&lt;20 points)<br>
        <hr style="margin: 5px 0;">
        <span style="color: cyan;">●</span> Individual GPS points<br>
        <span style="color: orange;">🔥</span> Heatmap layer
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))

def add_layer_control(m):
    """Add layer control to toggle layers"""
    folium.LayerControl(position='topright', collapsed=False).add_to(m)

def save_and_open_map(m, filename="outputs/hexagon_density_map.html"):
    """Save map to HTML and open in browser"""
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Save map
    m.save(filename)
    print(f"✅ Map saved to {filename}")
    
    # Open in browser
    webbrowser.open(f"file://{os.path.abspath(filename)}")
    print("🌍 Map opened in your default browser")
    
    return filename

def print_summary():
    """Print visualization summary"""
    print("\n" + "="*60)
    print("🗺️ VISUALIZATION SUMMARY")
    print("="*60)
    print("📊 Map features included:")
    print("   • Hexagons colored by density (RED/YELLOW/GREEN)")
    print("   • Popup tooltips with detailed stats")
    print("   • GPS points layer (can be toggled)")
    print("   • Heatmap overlay for density visualization")
    print("   • Dark mode base map")
    print("   • Interactive legend")
    print("\n💡 Tips:")
    print("   • Click on any hexagon to see details")
    print("   • Use Layer Control (top-right) to toggle layers")
    print("   • Zoom in/out to explore the area")
    print("="*60)

# Run the script
if __name__ == "__main__":
    print("🗺️ Loading GeoJSON data...")
    geojson_data = load_geojson()
    
    print("📊 Loading aggregated statistics...")
    hexagon_stats = load_aggregated_data()
    
    print("🎨 Creating interactive map...")
    m = add_hexagon_points_map(geojson_data, hexagon_stats)
    
    print("📍 Adding original GPS points layer...")
    add_original_points_map(m)
    
    print("🔥 Adding heatmap layer...")
    add_heatmap_layer(m)
    
    print("📖 Adding legend...")
    add_legend(m)
    
    print("🎮 Adding layer control...")
    add_layer_control(m)
    
    print_summary()
    
    print("\n💾 Saving and opening map...")
    save_and_open_map(m)
    
    print("\n✨ COMPLETE! All 5 scripts executed successfully!")
    print("\n📁 Files generated in /outputs and /data folders")