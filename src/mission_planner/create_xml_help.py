import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
from pyproj import Geod

def clean_mission_xml(input_xml_path, output_xml_path):
    print(f"Loading XML from: {input_xml_path}...")
    
    NAMESPACE = "http://scc/xml/schemas"
    ET.register_namespace('', NAMESPACE)
    ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
    
    tree = ET.parse(input_xml_path)
    root = tree.getroot()
    
    ns = {'def': NAMESPACE}
    
    req_list_node = root.find('.//def:requirementList', ns)
    
    if req_list_node is None:
        print("Error: Could not find <requirementList> in the XML.")
        return

    geod = Geod(ellps="WGS84")
    
    reqs_to_remove = []
    
    count_fixed_ids = 0
    count_removed_area = 0
    count_removed_not_poly = 0
    total_scanned = 0
    
    for req in req_list_node.findall('def:requirement', ns):
        total_scanned += 1
        
        id_node = req.find('def:palRequirementId', ns)
        if id_node is not None and id_node.text:
            if '/' in id_node.text:
                id_node.text = id_node.text.split('/')[-1]
                count_fixed_ids += 1
                
        points = []
        boundary_node = req.find('.//def:polygonBoundary', ns)
        
        if boundary_node is not None:
            for pt_node in boundary_node.findall('def:geographicPoint', ns):
                lon_text = pt_node.find('def:long', ns)
                lat_text = pt_node.find('def:lat', ns)
                
                if lon_text is not None and lat_text is not None:
                    points.append((float(lon_text.text), float(lat_text.text)))
        
        if len(points) < 3:
            reqs_to_remove.append(req)
            count_removed_not_poly += 1
            continue
            
        poly = Polygon(points)
        
        area, perimeter = geod.geometry_area_perimeter(poly)
        area = abs(area) 
        
        if area < 1000000:
            reqs_to_remove.append(req)
            count_removed_area += 1

    for req in reqs_to_remove:
        req_list_node.remove(req)
        
    print(f"Saving cleaned XML to: {output_xml_path}...")
    tree.write(output_xml_path, encoding='UTF-8', xml_declaration=True)
    
    print("\n=== XML Cleanup Summary ===")
    print(f"Total targets scanned:        {total_scanned}")
    print(f"IDs fixed (slashes removed):  {count_fixed_ids}")
    print(f"Removed (Not a polygon):      {count_removed_not_poly}")
    print(f"Removed (Area < 1,000,000):   {count_removed_area}")
    print(f"Total targets remaining:      {total_scanned - len(reqs_to_remove)}")
    print("===========================\n")

input_file = "/home/user1/GIT/mission_planner/outputs/xml/mission_requirements_first.xml"
output_file = "mission_requirements_first_fixed.xml"

clean_mission_xml(input_file, output_file)