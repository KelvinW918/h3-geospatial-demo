"""
Script 04: Hexagon neighbor analysis
Finds neighboring hexagons and identifies clusters of high-density zones
"""

import json
import h3
from collections import defaultdict, Counter

def load_hexagon_data(filename="data/hexagon_aggregated.json"):
    """Load aggregated hexagon statistics"""
    with open(filename, "r") as f:
        return json.load(f)

def get_hexagon_center(h3_index):
    """Get the center coordinates (latitude, longitude) of a hexagon"""
    try:
        if hasattr(h3, 'cell_to_latlng'):
            return h3.cell_to_latlng(h3_index)
        elif hasattr(h3, 'h3_to_geo'):
            return h3.h3_to_geo(h3_index)
        else:
            return (0, 0)
    except:
        return (0, 0)

def get_neighbors(h3_index):
    """Get all neighboring hexagons (sharing an edge)"""
    try:
        if hasattr(h3, 'grid_disk'):
            # grid_disk returns all hexagons within distance k=1 (including center)
            neighbors = h3.grid_disk(h3_index, 1)
            return [n for n in neighbors if n != h3_index]
        elif hasattr(h3, 'k_ring'):
            neighbors = h3.k_ring(h3_index, 1)
            return [n for n in neighbors if n != h3_index]
        elif hasattr(h3, 'hex_range'):
            return h3.hex_range(h3_index, 1)
        else:
            return []
    except Exception as e:
        print(f"⚠️ Error getting neighbors for {h3_index}: {e}")
        return []

def calculate_distance_between_centers(h3_index_a, h3_index_b):
    """Calculate distance in kilometers between two hexagon centers"""
    from geopy.distance import geodesic
    
    center_a = get_hexagon_center(h3_index_a)
    center_b = get_hexagon_center(h3_index_b)
    
    if center_a[0] == 0 or center_b[0] == 0:
        return 0
    
    return geodesic(center_a, center_b).kilometers

def build_neighbor_graph(hexagons):
    """
    Build a graph of neighboring hexagons
    Returns dictionary: hex_index -> list of neighbor indices
    """
    hex_indexes = [h["h3_index"] for h in hexagons]
    hex_set = set(hex_indexes)
    
    neighbor_graph = defaultdict(list)
    
    for hex_idx in hex_indexes:
        all_neighbors = get_neighbors(hex_idx)
        # Keep only neighbors that exist in our dataset
        existing_neighbors = [n for n in all_neighbors if n in hex_set]
        neighbor_graph[hex_idx] = existing_neighbors
    
    return neighbor_graph

def find_clusters(neighbor_graph, hexagons_by_index):
    """
    Find clusters of connected hexagons
    Uses flood fill / BFS algorithm
    """
    hex_indexes = list(neighbor_graph.keys())
    visited = set()
    clusters = []
    
    # Also track cluster density levels
    for hex_idx in hex_indexes:
        if hex_idx not in visited:
            # Start a new cluster
            cluster = []
            queue = [hex_idx]
            visited.add(hex_idx)
            
            while queue:
                current = queue.pop(0)
                cluster.append(current)
                
                for neighbor in neighbor_graph.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            if len(cluster) > 1:  # Only save clusters with 2+ hexagons
                # Calculate cluster statistics
                cluster_density = []
                cluster_avg_speeds = []
                total_points = 0
                
                for h in cluster:
                    data = hexagons_by_index.get(h, {})
                    cluster_density.append(data.get("density_level", "LOW"))
                    cluster_avg_speeds.append(data.get("avg_speed", 0))
                    total_points += data.get("point_count", 0)
                
                # Count density types
                high_count = cluster_density.count("HIGH")
                medium_count = cluster_density.count("MEDIUM")
                low_count = cluster_density.count("LOW")
                
                clusters.append({
                    "size": len(cluster),
                    "hexagons": cluster,
                    "total_points": total_points,
                    "avg_speed": round(sum(cluster_avg_speeds) / len(cluster_avg_speeds), 2),
                    "density_composition": {
                        "HIGH": high_count,
                        "MEDIUM": medium_count,
                        "LOW": low_count
                    }
                })
    
    return clusters

def find_high_density_clusters(clusters, min_size=3):
    """Find clusters that are predominantly high density"""
    high_density_clusters = []
    
    for i, cluster in enumerate(clusters):
        total = cluster["size"]
        high_count = cluster["density_composition"]["HIGH"]
        
        if high_count >= min_size or (high_count / total) >= 0.5:
            high_density_clusters.append({
                "cluster_id": i + 1,
                "size": cluster["size"],
                "high_density_count": high_count,
                "total_points": cluster["total_points"],
                "avg_speed": cluster["avg_speed"]
            })
    
    return high_density_clusters

def save_neighbor_results(neighbor_graph, clusters, high_density_clusters):
    """Save neighbor analysis results"""
    # Convert neighbor graph to serializable format
    graph_serializable = {k: v for k, v in neighbor_graph.items()}
    
    with open("data/neighbor_graph.json", "w") as f:
        json.dump(graph_serializable, f, indent=2)
    
    with open("data/clusters.json", "w") as f:
        json.dump(clusters, f, indent=2)
    
    with open("data/high_density_clusters.json", "w") as f:
        json.dump(high_density_clusters, f, indent=2)
    
    print(f"✅ Saved neighbor graph to data/neighbor_graph.json")
    print(f"✅ Saved clusters to data/clusters.json")
    print(f"✅ Saved high-density clusters to data/high_density_clusters.json")

def print_summary(hexagons, neighbor_graph, clusters, high_density_clusters):
    """Print neighbor analysis summary"""
    print("\n" + "="*60)
    print("🔗 NEIGHBOR & CLUSTER ANALYSIS")
    print("="*60)
    
    total_hexagons = len(hexagons)
    total_connections = sum(len(neighbors) for neighbors in neighbor_graph.values()) // 2
    
    print(f"🔶 Total hexagons with data: {total_hexagons}")
    print(f"🔗 Total neighbor connections: {total_connections}")
    print(f"📊 Average neighbors per hexagon: {total_connections * 2 / total_hexagons:.2f}")
    
    # Hexágonos aislados (sin vecinos)
    isolated = [h for h, n in neighbor_graph.items() if len(n) == 0]
    if isolated:
        print(f"⚠️ Isolated hexagons (no neighbors in dataset): {len(isolated)}")
    
    # Clusters encontrados
    print(f"\n🏘️ Clusters found: {len(clusters)}")
    if clusters:
        cluster_sizes = [c["size"] for c in clusters]
        print(f"   Largest cluster: {max(cluster_sizes)} hexagons")
        print(f"   Average cluster size: {sum(cluster_sizes)/len(cluster_sizes):.1f}")
    
    # Clusters de alta densidad
    print(f"\n🔥 High-density clusters (≥50% HIGH density): {len(high_density_clusters)}")
    for cluster in high_density_clusters[:3]:  # Show top 3
        print(f"   Cluster #{cluster['cluster_id']}: {cluster['size']} hexagons, "
              f"{cluster['high_density_count']} HIGH zones, "
              f"{cluster['total_points']} total points")
    
    # Ejemplo de vecindad
    print("\n📝 Sample neighbor relationship:")
    example_hex = list(neighbor_graph.keys())[0]
    neighbors = neighbor_graph[example_hex]
    print(f"   Hexagon: {example_hex[:12]}...")
    print(f"   Neighbors: {len(neighbors)}")
    if neighbors:
        print(f"   First neighbor: {neighbors[0][:12]}...")
    
    print("="*60)

# Run the script
if __name__ == "__main__":
    print("🔄 Loading hexagon aggregated data...")
    hexagons = load_hexagon_data()
    
    # Create a lookup dictionary for quick access
    hexagons_by_index = {h["h3_index"]: h for h in hexagons}
    
    print("🔗 Building neighbor graph...")
    neighbor_graph = build_neighbor_graph(hexagons)
    
    print("🏘️ Finding clusters...")
    clusters = find_clusters(neighbor_graph, hexagons_by_index)
    
    print("🔥 Identifying high-density clusters...")
    high_density_clusters = find_high_density_clusters(clusters, min_size=2)
    
    save_neighbor_results(neighbor_graph, clusters, high_density_clusters)
    print_summary(hexagons, neighbor_graph, clusters, high_density_clusters)
    
    print("\n✨ Done! Run next script: 05_visualize_map.py")