# Target Bank Generator & Prioritizer

This repository contains the workflow and tools for extracting, processing, and prioritizing geographic targets (polygons) from OpenStreetMap (OSM) for use in Command and Control (C2) and GIS systems.

## Workflow Overview
1. **Extraction:** Pull raw military infrastructure data from OSM using Overpass Turbo.
2. **Processing:** Filter geometries, clean data, and assign normally distributed priority scores using Python.
3. **Verification:** Visually inspect the generated Shapefiles using Mapshaper.

---

## Step 1: Data Extraction (Overpass Turbo)

We use [Overpass Turbo](https://overpass-turbo.eu/) to query OpenStreetMap for military land-use areas within a specific country.

1. Navigate to [https://overpass-turbo.eu/](https://overpass-turbo.eu/).
2. Paste the following Overpass QL query into the left editor panel (replace `Greece` with your target country if needed):

    ```overpass
    [out:json][timeout:90];
    (
      {{geocodeArea:Greece}}->.a;
    );
    (
      nwr[landuse=military](area.a);
    );
    out body;
    >;
    out skel qt;
    ```

3. Click **Run**.
   * *Note:* If a "Large amount of data" warning appears, click **Continue**. If the server is busy, wait 10 seconds and try again.
4. Once the map populates, click **Export** in the top menu.
5. Under the *Data* section, select **download/copy as GeoJSON**.
6. Save the downloaded file as `export.geojson` in your project directory.

---

## Step 2: Data Processing & Prioritization (Python)

The raw GeoJSON contains various geometries (points, lines, polygons) and numerous unnecessary tags that can crash standard Shapefile parsers (like the DBF column limits). The following Python script cleans the data, keeps only valid Polygons/MultiPolygons, and assigns a Priority score (from 2 to 100) using a normal distribution.

### Prerequisites
Ensure you have the required Python libraries installed:
    ```bash
    pip install geopandas numpy
    ```

### Execution
Create a file named `process_targets.py` and run the following script:

    ```python
    import geopandas as gpd
    import numpy as np

    def main():
        # 1. Load the GeoJSON file downloaded from Overpass Turbo
        input_geojson = "export.geojson"
        try:
            gdf = gpd.read_file(input_geojson)
        except FileNotFoundError:
            print(f"Error: Could not find '{input_geojson}'. Please ensure it is in the same directory.")
            return

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

        if num_of_targets == 0:
            print("No valid polygons found. Exiting.")
            return

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
        distribution_bins = gdf['Priority'].value_counts(bins=10).sort_index()
        print(distribution_bins)
        print("\n")

        # 5. Save the updated data to a Shapefile
        output_shapefile = "normally_prioritized_targets.shp"
        gdf.to_file(output_shapefile)

        print(f"Success! Data cleaned, prioritized, and saved to '{output_shapefile}'.")

    if __name__ == "__main__":
        main()
    ```

When running the script, it will generate a set of files (e.g., `.shp`, `.shx`, `.dbf`, `.prj`). Keep all of these files together, as they collectively make up the Shapefile.

---

## Step 3: Visualization & Verification (Mapshaper)

Before delivering the target bank to the C2 system, verify the geographic integrity and attribute data using [Mapshaper](https://mapshaper.org/).

1. Navigate to [https://mapshaper.org/](https://mapshaper.org/).
2. Select **all** the generated Shapefile components (`.shp`, `.shx`, `.dbf`, `.prj`) and drag-and-drop them into the browser window.
3. Click **Import**.
4. **Visual Check:** You should see the outlines of all the military polygons spread across the country.
5. **Data Check:** * Select the **"i" (Inspect Features)** tool from the right-hand menu.
   * Click on any polygon on the map.
   * A small window will appear in the top-left corner displaying the polygon's attributes, where you can verify that the `Priority` column has been successfully generated and populated with a number between 2 and 100.