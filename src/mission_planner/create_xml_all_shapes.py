import geopandas as gpd
import pandas as pd
import numpy as np
import datetime
import glob
import os

data_dir = "/home/user1/GIT/mission_planner/data/raw/*.geojson"
geojson_files = glob.glob(data_dir)

if not geojson_files:
    print("No GeoJSON files found in the specified directory.")
    exit()

gdfs = [] 
total_original_targets = 0

print(f"Found {len(geojson_files)} GeoJSON files. Processing...")

for file in geojson_files:
    filename = os.path.basename(file)
    print(f"\nProcessing {filename}...")
    
    temp_gdf = gpd.read_file(file)
    total_original_targets += len(temp_gdf)
    
    temp_gdf = temp_gdf[temp_gdf.geom_type.isin(['Polygon', 'MultiPolygon'])]
    
    if len(temp_gdf) > 0:
        temp_metric = temp_gdf.to_crs(temp_gdf.estimate_utm_crs())
        temp_metric = temp_metric[temp_metric.geometry.area >= 1000000]
        temp_gdf = temp_metric.to_crs(epsg=4326)
        
        print(f"  -> Valid targets after area filter: {len(temp_gdf)}")
        gdfs.append(temp_gdf)

if gdfs:
    gdf = pd.concat(gdfs, ignore_index=True)
else:
    print("No valid targets remained after filtering.")
    exit()

print(f"\nTotal targets loaded originally: {total_original_targets}")
print(f"Total targets remaining from all files after area filter: {len(gdf)}")

# =====================================================================
# 3. Limit to maximum 1000 shapes (from the COMBINED data)
# =====================================================================
MAX_TARGETS = 1000
if len(gdf) > MAX_TARGETS:
    print(f"Reducing combined target count from {len(gdf)} to {MAX_TARGETS}...")
    gdf = gdf.sample(n=MAX_TARGETS, random_state=42).copy()
    
    gdf = gdf.reset_index(drop=True)

# =====================================================================
# 4. Generate Normal Distribution Priorities (Range 1-8)
# =====================================================================
num_of_targets = len(gdf)
mean = 6        # Center of the 1-8 range (based on your script)
std_dev = 1.5   # Scaled down for a tighter range

# Generate values based on normal distribution
priorities = np.random.normal(loc=mean, scale=std_dev, size=num_of_targets)

# Clip values to ensure they stay within the 1-8 range
priorities = np.clip(priorities, 1, 8)

# Round to nearest integer and assign to the GeoDataFrame
gdf['Priority'] = np.round(priorities).astype(int)

# =====================================================================
# 5. Generate the XML file
# =====================================================================
print("\nGenerating combined XML file...")

# Current creation time for the XML Header
creation_time_sec = int(datetime.datetime.now().timestamp())
creation_time_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

# Time constraints for the imagingDates
start_date = "2011-06-05T00:00:00.000"
end_date = "2013-01-01T01:00:00.000"

# Variable to accumulate all targets
all_requirements_xml = ""

# Iterate through each polygon
for index, row in gdf.iterrows():
    priority = row['Priority']
    
    # Clean the ID to remove 'relation/' or 'way/'
    raw_id = row.get('id', index + 1)
    req_id = str(raw_id).split('/')[-1] 
    
    # Extract polygon coordinates
    geom = row['geometry']
    coords = []
    if geom.geom_type == 'Polygon':
        coords = list(geom.exterior.coords)
    elif geom.geom_type == 'MultiPolygon':
        coords = list(geom.geoms[0].exterior.coords)
    
    # Build the coordinates block with 6 decimal places
    points_xml = ""
    for lon, lat in coords:
        points_xml += f"""
            <geographicPoint>
                <long>{lon:.6f}</long>
                <lat>{lat:.6f}</lat>
                <heightUnknown/>
            </geographicPoint>"""

    # Build the complete target block (Requirement)
    req_xml = f"""
<requirement>
    <palRequirementId>{req_id}</palRequirementId>
    <requirementName>TestReq</requirementName>
    <type>Standing</type>
    <extraRequirement>false</extraRequirement>
    <deleted>false</deleted>
    <priority>{priority}</priority>
    <unPlannedElsewhere>false</unPlannedElsewhere>
    <plannedElsewhere>false</plannedElsewhere>
    <disseminationPriority>7</disseminationPriority>
    <worstAcceptableResolution>1</worstAcceptableResolution>
    <cloudCoverageForcast>0</cloudCoverageForcast>
    <percentUnusableData>20</percentUnusableData>
    <displayText>No Comments</displayText>
    <targetImageData>
        <targetCenterHeight>500</targetCenterHeight>
        <polygonBoundary>{points_xml}
        </polygonBoundary>
        <nominalTargetGroundContrast/>
        <niirsNotApplicable/>
    </targetImageData>
    <desirability>7</desirability>
    <anchor>true</anchor>
    <monoImaging/>
    <coverageConstraints>
        <oneScan>true</oneScan>
        <oneScow>false</oneScow>
    </coverageConstraints>
    <timeConstraints>
        <imagingDates>
            <dateRange>
                <start>{start_date}</start>
                <end>{end_date}</end>
            </dateRange>
        </imagingDates>
        <noImagingTimes/>
    </timeConstraints>
</requirement>"""
    
    all_requirements_xml += req_xml

# Build the main XML envelope
final_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<message xmlns="http://scc/xml/schemas" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://scc/xml/schemas V:sccXSD_Message.xsd">
    <iccHeader>
        <messageType>MissionRequirements</messageType>
        <originator>foo</originator>
        <originatorAddress>foo-bar</originatorAddress>
        <recipient>bar-foo</recipient>
        <creationTime>{creation_time_sec}</creationTime>
        <creationTimeString>{creation_time_str}</creationTimeString>
    </iccHeader>
    <missionRequirementsData>
        <satellite>OF7</satellite>
        <scowId>Foo#10225#BAR#-#1</scowId>
        <planRequirementId>1693___1720</planRequirementId>
        <updatedRequirementList>false</updatedRequirementList>
        <requirementList>{all_requirements_xml}
        </requirementList>
    </missionRequirementsData>
</message>"""

# =====================================================================
# 6. Save the file
# =====================================================================
output_xml_path = "combined_mission_requirements.xml"
with open(output_xml_path, "w", encoding="utf-8") as f:
    f.write(final_xml)

print(f"Success! Targets from all files combined and saved to '{output_xml_path}'")