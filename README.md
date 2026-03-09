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

```
python3 src/mission_planner/normal_distribution_priorities.py
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