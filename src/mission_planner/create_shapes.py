import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

def generate_random_points_in_bbox(bbox, num_points):
    """Generate random points within a given bounding box (min_lon, min_lat, max_lon, max_lat)"""
    min_lon, min_lat, max_lon, max_lat = bbox
    lons = np.random.uniform(min_lon, max_lon, num_points)
    lats = np.random.uniform(min_lat, max_lat, num_points)
    return [Point(lon, lat) for lon, lat in zip(lons, lats)]

def main():
    print("Starting generation of 10,000 synthetic targets scenario...")

    # Define the 14 regions, their target counts, and their approximate bounding boxes [min_lon, min_lat, max_lon, max_lat]
    regions = [
        {"name": "1. Texas Coasts", "count": 100, "bbox": (-97.5, 25.8, -93.8, 29.8)},
        {"name": "2. Dallas-Austin-SanAntonio", "count": 300, "bbox": (-98.6, 29.3, -96.5, 33.0)},
        {"name": "3. SW Texas / Mexico Border", "count": 1500, "bbox": (-106.6, 25.8, -99.0, 29.5)},
        {"name": "4. Airports (GA, NM, TX, AZ)", "count": 200, "bbox": (-114.0, 31.0, -81.0, 35.0)},
        {"name": "5. TX/OK - LA/AR Border", "count": 500, "bbox": (-94.5, 32.0, -93.5, 34.0)},
        {"name": "6. Atlanta", "count": 3500, "bbox": (-84.5, 33.6, -84.2, 33.9)},
        {"name": "7. Florida", "count": 1000, "bbox": (-87.0, 25.0, -80.0, 31.0)},
        {"name": "8. Georgia", "count": 1000, "bbox": (-85.5, 30.5, -81.0, 35.0)},
        {"name": "9. SC Ports", "count": 100, "bbox": (-81.0, 32.0, -78.5, 33.9)},
        {"name": "10. Baja California (Mexico)", "count": 200, "bbox": (-115.0, 23.0, -109.0, 32.5)},
        {"name": "11. Mexico Ports", "count": 1000, "bbox": (-105.0, 15.0, -90.0, 25.0)},
        {"name": "12. Caribbean & SE Mexico", "count": 100, "bbox": (-90.0, 15.0, -75.0, 22.0)},
        {"name": "13. North Korea", "count": 200, "bbox": (124.0, 37.5, 130.0, 43.0)},
        {"name": "14. Other (Global)", "count": 300, "bbox": (-180.0, -50.0, 180.0, 50.0)}
    ]

    all_geometries = []
    all_regions = []

    # 1. Generate the targets geographically
    for region in regions:
        print(f"Generating {region['count']} targets for {region['name']}...")
        points = generate_random_points_in_bbox(region['bbox'], region['count'])
        
        # Buffer the points slightly to make them Polygons (0.002 degrees is approx a 200m radius facility)
        # This is because C2 systems often prefer Area Targets (Polygons) over Point Targets.
        polygons = [p.buffer(0.002) for p in points]
        
        all_geometries.extend(polygons)
        all_regions.extend([region['name']] * region['count'])

    # Verify total is exactly 10,000
    total_targets = len(all_geometries)
    print(f"\nTotal targets generated: {total_targets}")

    # 2. Create the GeoDataFrame
    gdf = gpd.GeoDataFrame({
        'Region': all_regions,
        'geometry': all_geometries
    }, crs="EPSG:4326")

    # 3. Assign Normal Distribution Priorities (2 to 100)
    mean = 51       
    std_dev = 16    
    priorities = np.random.normal(loc=mean, scale=std_dev, size=total_targets)
    priorities = np.clip(priorities, 2, 100)
    gdf['Priority'] = np.round(priorities).astype(int)

    # 4. Save to Shapefile
    output_shapefile = "scenario_10k_targets.shp"
    gdf.to_file(output_shapefile)
    print(f"Success! Data saved to '{output_shapefile}'. Ready for Mapshaper / Strategy System.")

if __name__ == "__main__":
    main()