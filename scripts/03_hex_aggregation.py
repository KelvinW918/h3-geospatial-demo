"""
Script 03: Hexagon aggregation and density analysis
Groups points by H3 hexagon and calculates statistics per zone
"""

import json
import h3
from collections import defaultdict
import statistics

def load_points_with_h3(filename="data/points_with_h3.json"):
    """Load points that already have H3 indexes"""
    with open(filename, "r") as f:
        return json.load(f)

def aggregate_by_hexagon(points):
    """
    Group points by H3 hexagon and calculate statistics per zone
    Returns dictionary with hexagon as key and aggregated data as value
    """
    hexagon_data = defaultdict(lambda: {
        "points": [],
        "vehicle_ids": set(),
        "speeds": [],
        "point_count": 0,
        "avg_speed": 0,
        "unique_vehicles": 0
    })
    
    for point in points:
        h3_index = point["h3_index"]
        
        # Agregar datos al hexágono correspondiente
        hexagon_data[h3_index]["points"].append(point)
        hexagon_data[h3_index]["vehicle_ids"].add(point["vehicle_id"])
        hexagon_data[h3_index]["speeds"].append(point["speed"])
        hexagon_data[h3_index]["point_count"] += 1
    
    # Calcular estadísticas finales para cada hexágono
    for h3_index, data in hexagon_data.items():
        data["avg_speed"] = round(statistics.mean(data["speeds"]), 2)
        data["unique_vehicles"] = len(data["vehicle_ids"])
        data["speed_std"] = round(statistics.stdev(data["speeds"]) if len(data["speeds"]) > 1 else 0, 2)
        data["min_speed"] = min(data["speeds"])
        data["max_speed"] = max(data["speeds"])
        
        # Clasificar densidad (cuántos puntos por hexágono)
        if data["point_count"] >= 50:
            data["density_level"] = "HIGH"
        elif data["point_count"] >= 20:
            data["density_level"] = "MEDIUM"
        else:
            data["density_level"] = "LOW"
        
        # Limpiar datos pesados para el JSON (no guardar todos los puntos individuales)
        data["points_count"] = data["point_count"]
        del data["points"]  # Eliminar puntos individuales para no llenar el archivo
        del data["speeds"]  # Ya calculamos el promedio
        data["vehicle_ids"] = list(data["vehicle_ids"])  # Convertir set a lista para JSON
    
    return hexagon_data

def get_hexagon_boundary(h3_index):
    """Get the boundary coordinates of a hexagon as a polygon"""
    try:
        if hasattr(h3, 'cell_to_boundary'):
            return h3.cell_to_boundary(h3_index)
        elif hasattr(h3, 'h3_to_geo_boundary'):
            return h3.h3_to_geo_boundary(h3_index)
        else:
            return []
    except:
        return []

def add_geometries_to_hexagons(hexagon_data):
    """Add polygon geometries to hexagons for visualization"""
    hexagons_with_geo = []
    
    for h3_index, data in hexagon_data.items():
        try:
            boundary = get_hexagon_boundary(h3_index)
            if boundary:
                # Convertir boundary a formato GeoJSON polygon
                # El boundary viene como lista de (lat, lng), necesitamos (lng, lat) para GeoJSON
                coordinates = [[lng, lat] for lat, lng in boundary]
                # Cerrar el polígono (repetir el primer punto)
                coordinates.append(coordinates[0])
                
                hexagon_geo = {
                    "h3_index": h3_index,
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coordinates]
                    },
                    "properties": {
                        "point_count": data["point_count"],
                        "density_level": data["density_level"],
                        "avg_speed": data["avg_speed"],
                        "unique_vehicles": data["unique_vehicles"],
                        "min_speed": data["min_speed"],
                        "max_speed": data["max_speed"]
                    }
                }
                hexagons_with_geo.append(hexagon_geo)
        except Exception as e:
            print(f"⚠️ Error getting boundary for {h3_index}: {e}")
    
    return hexagons_with_geo

def save_aggregated_results(hexagon_data, hexagons_geojson):
    """Save aggregation results to files"""
    # Guardar estadísticas agregadas (sin geometría)
    aggregated_list = []
    for h3_index, data in hexagon_data.items():
        aggregated_list.append({
            "h3_index": h3_index,
            "point_count": data["point_count"],
            "density_level": data["density_level"],
            "avg_speed": data["avg_speed"],
            "unique_vehicles": data["unique_vehicles"],
            "min_speed": data["min_speed"],
            "max_speed": data["max_speed"]
        })
    
    with open("data/hexagon_aggregated.json", "w") as f:
        json.dump(aggregated_list, f, indent=2)
    
    # Guardar GeoJSON para mapas
    geojson_output = {
        "type": "FeatureCollection",
        "features": hexagons_geojson
    }
    
    with open("outputs/hexagons.geojson", "w") as f:
        json.dump(geojson_output, f, indent=2)
    
    print(f"✅ Saved aggregated stats to data/hexagon_aggregated.json")
    print(f"✅ Saved GeoJSON to outputs/hexagons.geojson")

def print_summary(hexagon_data, total_points):
    """Print density analysis summary"""
    print("\n" + "="*60)
    print("📊 DENSITY & AGGREGATION SUMMARY")
    print("="*60)
    
    total_hexagons = len(hexagon_data)
    high_density = sum(1 for d in hexagon_data.values() if d["density_level"] == "HIGH")
    medium_density = sum(1 for d in hexagon_data.values() if d["density_level"] == "MEDIUM")
    low_density = sum(1 for d in hexagon_data.values() if d["density_level"] == "LOW")
    
    print(f"🔶 Total hexagons with points: {total_hexagons}")
    print(f"📊 Density distribution:")
    print(f"   🔴 HIGH density (≥50 points): {high_density} hexagons")
    print(f"   🟡 MEDIUM density (20-49 points): {medium_density} hexagons")
    print(f"   🟢 LOW density (<20 points): {low_density} hexagons")
    
    # Velocidad promedio por zona
    all_speeds = []
    for data in hexagon_data.values():
        all_speeds.extend([data["avg_speed"]] * data["point_count"])
    global_avg_speed = round(statistics.mean(all_speeds), 2)
    
    print(f"\n🚗 Traffic analysis:")
    print(f"   📍 Global average speed: {global_avg_speed} km/h")
    
    # Hexágono más lento y más rápido
    slowest_hex = min(hexagon_data.items(), key=lambda x: x[1]["avg_speed"])
    fastest_hex = max(hexagon_data.items(), key=lambda x: x[1]["avg_speed"])
    
    print(f"   🐢 Slowest zone avg speed: {slowest_hex[1]['avg_speed']} km/h ({slowest_hex[1]['point_count']} points)")
    print(f"   🐰 Fastest zone avg speed: {fastest_hex[1]['avg_speed']} km/h ({fastest_hex[1]['point_count']} points)")
    
    print("="*60)

# Run the script
if __name__ == "__main__":
    print("🔄 Loading points with H3 indexes...")
    points = load_points_with_h3()
    
    print(f"📊 Aggregating {len(points)} points by hexagon...")
    hexagon_data = aggregate_by_hexagon(points)
    
    print("🗺️ Generating geometries for visualization...")
    hexagons_geojson = add_geometries_to_hexagons(hexagon_data)
    
    save_aggregated_results(hexagon_data, hexagons_geojson)
    print_summary(hexagon_data, len(points))
    
    print("\n✨ Done! Run next script: 04_hex_neighbors.py")