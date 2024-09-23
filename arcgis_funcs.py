import arcpy
import os

taxlots_helion = "taxlot_layer"
rec = 0


def get_target_taxlot(dir, target):
    try:
        output_layer = os.path.join(dir, f"{target}\\target_property.shp")
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            print("Creating target property shapefile")
            arcpy.conversion.ExportFeatures(taxlots_helion, output_layer, where_clause=f"MAPTAXLOT='{target}'")
            print("Target property shapefile created")
    except Exception as e:
        print(f"An error occurred in function get_target_property: {e}")
        return None


def buffer_property(in_feature, output_layer):
    try:
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            print("...Creating one mile buffer...")
            arcpy.analysis.Buffer(in_feature, output_layer, buffer_distance_or_field="1 Mile")
    except Exception as e:
        print(f"An error occurred in function buffer_property: {e}")
        return None


def intersect_taxlots_helion(buffer_layer, output_layer):
    try:
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            print("...Creating one mile within shapefile...")
            one_mile_within = arcpy.management.SelectLayerByLocation(
                taxlots_helion,
                'INTERSECT',
                buffer_layer
            )
            arcpy.management.MakeFeatureLayer(one_mile_within, r'memory/copy_selection_taxlots')
            arcpy.management.CopyFeatures(r'memory/copy_selection_taxlots', output_layer)

    except Exception as e:
        print(f"An error occurred in function intersect_taxlots_helion: {e}")
        return None


def clip_taxlots(buffer_layer, taxlot_layer, output_layer):
    try:
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            print(f"...Clipping {os.path.basename(taxlot_layer)} and creating: {os.path.basename(output_layer)}...")
            arcpy.analysis.PairwiseClip(taxlot_layer, buffer_layer, output_layer)
    except Exception as e:
        print(f"An error occurred in function clip_taxlots: {e}")
        return None


def create_study_area(taxlot_layer, output_layer):
    try:
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            print(f"...Creating {os.path.basename(output_layer)}...")
            arcpy.analysis.Buffer(taxlot_layer, output_layer, buffer_distance_or_field="50 Feet", dissolve_option="ALL")
    except Exception as e:
        print(f"An error occurred in function create_study_area: {e}")
        return None


def get_dwellings(taxlot_layer, address_points, output_layer):
    try:
        if os.path.exists(output_layer):
            print(f"Already Exists: {output_layer}")
        else:
            dwellings = arcpy.management.SelectLayerByLocation(
                address_points,
                'INTERSECT',
                taxlot_layer
            )
            arcpy.management.MakeFeatureLayer(dwellings, r'memory/copy_selection_dwellings', where_clause="status='current'")
            arcpy.management.CopyFeatures(r'memory/copy_selection_dwellings', output_layer)
    except Exception as e:
        print(f"An error occurred in function get_dwellings: {e}")
        return None


def add_fields(within_layer, inside_layer):

    def auto_increment():
        global rec
        p_start = 1
        p_interval = 1
        if rec == 0:
            rec = p_start
        else:
            rec += p_interval
        return rec

    try:
        taxlot_layers = [within_layer, inside_layer]
        for layer in taxlot_layers:
            global rec
            rec = 0
            print(f"Iterating through: {arcpy.Describe(layer).name}")
            field_names = [f.name for f in arcpy.ListFields(layer)]
            field_check = ['ID', 'GISACRES']
            for field in field_check:
                if field in field_names:
                    print(f"{arcpy.Describe(layer).name} already contains field: {field}")
                elif field is not field_names:
                    print(f"...Creating fields: {field}...")
                    if field == 'ID':
                        arcpy.management.AddField(layer, "ID", "SHORT")
                        rows = arcpy.UpdateCursor(layer, "", "", "", field)
                        for row in rows:
                            row.setValue(field, auto_increment())
                            rows.updateRow(row)

                    elif field == 'GISACRES':
                        arcpy.management.AddField(layer, "GISACRES", "DOUBLE", field_precision=20, field_scale=2)
                        arcpy.management.CalculateGeometryAttributes(
                            layer,
                            [["GISACRES", "AREA"]],
                            area_unit="ACRES_US"
                        )
                    else:
                        pass
                else:
                    pass

    except Exception as e:
        print(f"An error occurred in function add_fields: {e}")
        return None