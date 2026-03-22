import geopandas as gpd
import numpy as np

# 1. Load the GeoJSON file downloaded from Overpass Turbo
input_geojson = "data/raw/export_beach.geojson"
gdf = gpd.read_file(input_geojson)

# --- Fixes for Shapefile limitations ---

# Fix A: Filter geometries. Keep only Polygons and MultiPolygons (drop Lines/Points)
gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]

# Fix B: Clean columns. Keep only essential tags to prevent DBF format crashes
important_columns = ['id', 'name', 'military', 'aeroway', 'landuse', 'geometry']
existing_columns = [col for col in important_columns if col in gdf.columns]
gdf = gdf[existing_columns]

# ---------------------------------------

# Check the number of remaining valid targets
num_of_targets = len(gdf)
print(f"Assigning normal distribution priorities to {num_of_targets} valid polygon targets...\n")

# 2. Generate normal distribution (range: 2 to 100)
mean = 51       
std_dev = 16    
priorities = np.random.normal(loc=mean, scale=std_dev, size=num_of_targets)

# Clip the values to ensure nothing is outside the 2-100 range
priorities = np.clip(priorities, 2, 100)

# Round to nearest integer since priorities are usually whole numbers
priorities = np.round(priorities).astype(int)

# 3. Add the Priority column to the GeoDataFrame
gdf['Priority'] = priorities

# 4. Print the distribution to the console to verify the bell curve
print("--- Priority Distribution Statistics ---")
print(gdf['Priority'].describe())
print("\n--- Priority Bins (Checking the Bell Curve) ---")
# This will show how many targets fall into each decile (e.g., 2-11, 12-21, etc.)
distribution_bins = gdf['Priority'].value_counts(bins=10).sort_index()
print(distribution_bins)
print("\n")

# 5. Save the updated data to a Shapefile
output_shapefile = "normally_prioritized_targets_beach.shp"
gdf.to_file(output_shapefile)

print(f"Success! Data cleaned, prioritized, and saved to '{output_shapefile}'.")