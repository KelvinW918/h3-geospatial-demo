"""
Script 01: Generate random GPS points
Creates 1000 random coordinates around Caracas, Venezuela
"""

import random
import json
from datetime import datetime
from faker import Faker

# Inicializar Faker
fake = Faker()

# Centro aproximado de Caracas, Venezuela
CENTER_LAT = 10.4806
CENTER_LNG = -66.9036

# Radio de dispersión en grados (~10km)
RADIUS_DEGREES = 0.1

def generate_random_point(center_lat, center_lng, radius_deg):
    """Generate a random point within a radius of center"""
    lat = center_lat + random.uniform(-radius_deg, radius_deg)
    lng = center_lng + random.uniform(-radius_deg, radius_deg)
    return lat, lng

def generate_points(n_points=1000):
    """Generate n random GPS points with fake vehicle IDs"""
    points = []
    
    for i in range(n_points):
        lat, lng = generate_random_point(CENTER_LAT, CENTER_LNG, RADIUS_DEGREES)
        
        point = {
            "id": i + 1,
            "vehicle_id": fake.license_plate(),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "timestamp": datetime.now().isoformat(),
            "speed": random.randint(0, 120)  # speed in km/h
        }
        points.append(point)
    
    return points

def save_points_to_json(points, filename="data/points.json"):
    """Save points to JSON file"""
    with open(filename, "w") as f:
        json.dump(points, f, indent=2)
    print(f"✅ Saved {len(points)} points to {filename}")

def print_summary(points):
    """Print summary of generated points"""
    print("\n" + "="*50)
    print("📊 GENERATION SUMMARY")
    print("="*50)
    print(f"📍 Center: {CENTER_LAT}, {CENTER_LNG}")
    print(f"📡 Radius: {RADIUS_DEGREES} degrees (~10km)")
    print(f"🚗 Total points: {len(points)}")
    print(f"📝 Sample point:")
    print(f"   Vehicle: {points[0]['vehicle_id']}")
    print(f"   Coordinates: {points[0]['lat']}, {points[0]['lng']}")
    print(f"   Speed: {points[0]['speed']} km/h")
    print("="*50)

# Run the script
if __name__ == "__main__":
    print("🔄 Generating random GPS points...")
    points = generate_points(1000)
    save_points_to_json(points)
    print_summary(points)
    print("\n✨ Done! Run next script: 02_hex_index.py")