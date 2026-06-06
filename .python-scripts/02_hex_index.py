"""
Script 02: Convert GPS coordinates to H3 hexagons
Takes the generated points and assigns each to an H3 hexagon cell
Compatible with older h3 library versions
"""

import json
import h3
from collections import Counter

# Configuración
RESOLUTION = 9  # Resolución H3 (0=grande, 15=pequeño)

def lat_lng_to_h3(lat, lng, resolution):
    """
    Convert latitude/longitude to H3 index
    Compatible with different h3 versions
    """
    # Probar diferentes formas de llamar a h3
    if hasattr(h3, 'latlng_to_cell'):
        # Versión nueva (h3 4.x)
        return h3.latlng_to_cell(lat, lng, resolution)
    elif hasattr(h3, 'geo_to_h3'):
        # Versión antigua (h3 3.x)
        return h3.geo_to_h3(lat, lng, resolution)
    else:
        # Otra alternativa
        return h3.h3_index_from_latlng(lat, lng, resolution)

def load_points(filename="data/points.json"):
    """Load points from JSON file"""
    with open(filename, "r") as f:
        return json.load(f)

def add_h3_indexes(points, resolution):
    """
    Add H3 index to each point
    Returns points_with_h3 and hexagon statistics
    """
    points_with_h3 = []
    hexagon_counts = Counter()
    
    for point in points:
        lat = point["lat"]
        lng = point["lng"]
        
        # Convertir a H3
        h3_index = lat_lng_to_h3(lat, lng, resolution)
        
        # Crear nuevo objeto con H3 agregado
        point_with_h3 = point.copy()
        point_with_h3["h3_index"] = h3_index
        point_with_h3["h3_resolution"] = resolution
        
        points_with_h3.append(point_with_h3)
        hexagon_counts[h3_index] += 1
    
    return points_with_h3, hexagon_counts

def get_hexagon_area(resolution):
    """Get approximate hexagon area in km²"""
    try:
        if hasattr(h3, 'cell_area'):
            return h3.cell_area(resolution, unit='km^2')
        elif hasattr(h3, 'hex_area'):
            return h3.hex_area(resolution, unit='km^2')
    except:
        # Valor aproximado para resolución 9
        areas = {0: 4254000, 1: 607800, 2: 86800, 3: 12400, 4: 1772, 
                 5: 253, 6: 36.1, 7: 5.16, 8: 0.737, 9: 0.105, 
                 10: 0.015, 11: 0.00215, 12: 0.000307, 13: 0.0000438, 
                 14: 0.00000626, 15: 0.000000894}
        return areas.get(resolution, 0.105)

def save_results(points_with_h3, hexagon_counts, resolution):
    """Save results to JSON files"""
    # Guardar puntos con H3
    with open("data/points_with_h3.json", "w") as f:
        json.dump(points_with_h3, f, indent=2)
    
    # Guardar estadísticas de hexágonos
    hexagon_data = [
        {"h3_index": hex_id, "count": count}
        for hex_id, count in hexagon_counts.items()
    ]
    with open("data/hexagon_stats.json", "w") as f:
        json.dump(hexagon_data, f, indent=2)
    
    print(f"✅ Saved {len(points_with_h3)} points with H3 to data/points_with_h3.json")
    print(f"✅ Saved {len(hexagon_data)} hexagon stats to data/hexagon_stats.json")

def print_summary(points_with_h3, hexagon_counts, resolution):
    """Print summary statistics"""
    hex_area = get_hexagon_area(resolution)
    
    print("\n" + "="*60)
    print("📍 H3 INDEXING SUMMARY")
    print("="*60)
    print(f"🔷 H3 Resolution: {resolution}")
    print(f"📏 Approx hexagon area: ~{hex_area:.4f} km²")
    print(f"🚗 Total points indexed: {len(points_with_h3)}")
    print(f"🔶 Unique hexagons: {len(hexagon_counts)}")
    print(f"📊 Average points per hexagon: {len(points_with_h3)/len(hexagon_counts):.2f}")
    
    most_common = hexagon_counts.most_common(1)[0]
    print(f"🔥 Most crowded hexagon: {most_common[0][:10]}... ({most_common[1]} points)")
    
    # Mostrar ejemplo de un punto convertido
    print("\n📝 Sample conversion:")
    sample = points_with_h3[0]
    print(f"   Coordinates: {sample['lat']}, {sample['lng']}")
    print(f"   H3 Index: {sample['h3_index']}")
    print(f"   Resolution: {sample['h3_resolution']}")
    
    print("="*60)

# Run the script
if __name__ == "__main__":
    print("🔄 Loading points...")
    points = load_points()
    
    print(f"🔷 Converting {len(points)} points to H3 resolution {RESOLUTION}...")
    points_with_h3, hexagon_counts = add_h3_indexes(points, RESOLUTION)
    
    save_results(points_with_h3, hexagon_counts, RESOLUTION)
    print_summary(points_with_h3, hexagon_counts, RESOLUTION)
    
    print("\n✨ Done! Run next script: 03_hex_aggregation.py")