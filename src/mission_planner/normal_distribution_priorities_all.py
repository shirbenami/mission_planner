import geopandas as gpd
import pandas as pd
import numpy as np
import glob
import os

def main():
    input_folder = "data/raw"
    geojson_files = glob.glob(os.path.join(input_folder, "*.geojson"))
    
    if not geojson_files:
        print(f"Error: No .geojson files found in '{input_folder}'.")
        return

    print(f"Found {len(geojson_files)} GeoJSON files. Merging them...")

    gdfs = []
    
    for file in geojson_files:
        try:
            print(f"  Reading {os.path.basename(file)}...")
            temp_gdf = gpd.read_file(file)
            
            
            temp_gdf = temp_gdf[temp_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            
            important_columns = ['id', 'name', 'military', 'aeroway', 'landuse', 'geometry']
            existing_columns = [col for col in important_columns if col in temp_gdf.columns]
            temp_gdf = temp_gdf[existing_columns]
            
            temp_gdf['source'] = os.path.basename(file)
            
            gdfs.append(temp_gdf)
            
        except Exception as e:
            print(f"  -> FAILED to process {file}: {e}")

    if not gdfs:
        print("No valid polygon data found in any of the files.")
        return

    gdf = pd.concat(gdfs, ignore_index=True)

    num_of_targets = len(gdf)
    print(f"\nAssigning normal distribution priorities to a total of {num_of_targets} valid polygon targets...\n")

    mean = 51       
    std_dev = 16    
    priorities = np.random.normal(loc=mean, scale=std_dev, size=num_of_targets)

    priorities = np.clip(priorities, 2, 100)

    priorities = np.round(priorities).astype(int)

    gdf['Priority'] = priorities

    print("--- Priority Distribution Statistics ---")
    print(gdf['Priority'].describe())
    print("\n--- Priority Bins (Checking the Bell Curve) ---")
    distribution_bins = gdf['Priority'].value_counts(bins=10).sort_index()
    print(distribution_bins)
    print("\n")

    output_shapefile = "normally_prioritized_targets_ALL.shp"
    gdf.to_file(output_shapefile)

    print(f"Success! Data from all {len(geojson_files)} files was cleaned, prioritized, and saved to '{output_shapefile}'.")

if __name__ == "__main__":
    main()