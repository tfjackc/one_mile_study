import arcpy
import os
import pandas as pd
import shutil
import geopandas as gpd
arcpy.env.overwriteOutput = True


def rename_layer(map_obj, old_layer_name, new_layer_name):
    try:
        layer = map_obj.listLayers(old_layer_name)[0]
        layer.name = new_layer_name
        print(f"Layer '{old_layer_name}' renamed to '{new_layer_name}'")
    except IndexError:
        print(f"Layer '{old_layer_name}' not found.")
    except Exception as e:
        print(f"Error renaming layer '{old_layer_name}': {e}")


def move_layer_in_map(map_obj, layer_name, target_layer_name):
    try:
        layer = map_obj.listLayers(layer_name)[0]
        # Get the target layer by name
        target_layer = map_obj.listLayers(target_layer_name)[0]
        # Move the layer
        map_obj.moveLayer(target_layer, layer, "BEFORE")
        print(f"Layer '{layer_name}' moved position")
    except IndexError:
        print(f"Layer '{layer_name}' or target layer {target_layer} not found.")
    except Exception as e:
        print(f"Error moving layer '{layer_name}': {e}")


def feature_class_to_dataframe(input_fc: str, input_fields: list = None):
    # get list of fields if desired fields specified
    OIDFieldName = arcpy.Describe(input_fc).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    # use all fields if no fields specified
    else:
        final_fields = [field.name for field in arcpy.ListFields(input_fc)]
    # build dataframe row by row using search cursor
    fc_dataframe = pd.DataFrame((row for row in arcpy.da.SearchCursor(input_fc, final_fields)), columns=final_fields)
    # set index to object id
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)

    return fc_dataframe


def dwelling_count(dwellings, one_mile_within, one_mile_inside, output_dir):
    # Load data
    dwelling_gdf = gpd.read_file(dwellings)
    within_gdf = gpd.read_file(one_mile_within)
    inside_gdf = gpd.read_file(one_mile_inside)

    # Subset the data to fields of interest
    dw_gdf = dwelling_gdf[['full_add_1', 'geometry']]
    w_gdf = within_gdf[['MAPTAXLOT', 'geometry']]
    i_gdf = inside_gdf[['MAPTAXLOT', 'geometry']]

    # Perform spatial join on the within taxlot data set
    join_within_gdf = w_gdf.sjoin(dw_gdf, how="left")
    join_inside_gdf = i_gdf.sjoin(dw_gdf, how="left")

    # To ensure we are not modifying a copy, operate on join_left_df directly
    join_within_gdf['count'] = join_within_gdf['full_add_1'].notnull().astype(int)
    join_inside_gdf['count'] = join_inside_gdf['full_add_1'].notnull().astype(int)

    # Optionally, create a new GeoDataFrame if you need only specific columns
    join_within_subset_gdf = join_within_gdf[['MAPTAXLOT', 'full_add_1', 'count']]
    join_inside_subset_gdf = join_inside_gdf[['MAPTAXLOT', 'full_add_1', 'count']]

    # Print the result or send to csv
    join_within_subset_gdf.to_csv(f"{output_dir}\\join_within_subset.csv")
    join_inside_subset_gdf.to_csv(f"{output_dir}\\join_inside_subset.csv")


def map_data(**kwargs):
    global current_map
    current_map = None
    aprx_path = None
    dir_path = None
    lot_number = None
    symbology_layers = None
    taxlots_within = None
    taxlots_inside = None
    dwellings = None

    # Process the input keyword arguments for special keys
    for key, value in kwargs.items():
        if key == 'arcproj':
            aprx_path = value
            aprx = arcpy.mp.ArcGISProject(aprx_path)
            current_map = aprx.listMaps()[0]
        elif key == 'target_property':
            dir_path = os.path.dirname(value)
        elif key == 'lot_number':
            lot_number = value
        elif key == 'symbology_layers':
            symbology_layers = value
        elif key == 'one_mile_within':
            taxlots_within = value
        elif key == 'one_mile_inside':
            taxlots_inside = value
        elif key == 'dwellings':
            dwellings = value

    # Add data paths to the map
    for key, value in kwargs.items():
        if key not in ['arcproj', 'lot_number', 'symbology_layers', 'one_mile_inside']:
            if current_map is not None:
                current_map.addDataFromPath(value)
                print(f"...{os.path.basename(value)} added to the map...")
            else:
                print(f"...Skipping {value} as the map is not initialized...")

    if current_map is not None:

        print("...Updating symbology...")
        symbology_layers = symbology_layers

        for num, layers in enumerate(current_map.listLayers()):
            print(f"{num}: {layers}")

        for num, symbology_layer in enumerate(symbology_layers):
            in_layers = current_map.listLayers()[num]
            arcpy.management.ApplySymbologyFromLayer(
                in_layer=in_layers,
                in_symbology_layer=symbology_layer
            )
            print(in_layers)
            if in_layers.name in ['target_property', 'study_area', 'dwellings']:
                rename_layer(current_map, in_layers.name, in_layers.name.capitalize().replace("_", " ").title())

        rename_layer(current_map, 'one_mile_within', 'Affected Within 1 Mile')
        rename_layer(current_map, 'one_mile_buffer', 'Mile Buffer')
        rename_layer(current_map, 'APP_DATA.dbo.CC_Elk_VIEW', 'Elk Winter Range')

        move_layer_in_map(current_map, "Target Property", "Elk Winter Range")
        move_layer_in_map(current_map, "Mile Buffer", "Elk Winter Range")
        move_layer_in_map(current_map, "Study Area", "Elk Winter Range")
        move_layer_in_map(current_map, "Affected Within 1 Mile", "Elk Winter Range")

        print("...Modifying layouts...")
        lyts_inside = aprx.listLayouts()[0]
        lyts_within = aprx.listLayouts()[1]

        maptaxlot_text_inside = lyts_inside.listElements()[0]
        maptaxlot_text_within = lyts_within.listElements()[0]
        maptaxlot_text_inside.text = lot_number
        maptaxlot_text_within.text = lot_number

        # create buffer to the increase the size of the map frame without adding it to the map
        arcpy.analysis.Buffer(taxlots_within, r"memory\withinBuffer", "100 Meters")
        arcpy.analysis.Buffer(taxlots_inside, r"memory\insideBuffer", "100 Meters")
        within_desc_buffer = arcpy.Describe(r"memory\withinBuffer")
        within_buff_ext = within_desc_buffer.extent
        inside_desc_buffer = arcpy.Describe(r"memory\insideBuffer")
        inside_buff_ext = inside_desc_buffer.extent
        #print(f"Map frame extent set to --> {within_buff_ext}")

        mapElem_inside = lyts_inside.listElements("MAPFRAME_ELEMENT")[0]
        mapElem_inside.camera.setExtent(inside_buff_ext)  # set map frame extent

        mapElem_within = lyts_within.listElements("MAPFRAME_ELEMENT")[0]
        mapElem_within.camera.setExtent(within_buff_ext)  # set map frame extent

        if aprx_path and dir_path:
            lyts_inside.exportToPDF(os.path.join(dir_path, "1MileInside.pdf"))  # export map to pdf
            lyts_within.exportToPDF(os.path.join(dir_path, "1MileWithin.pdf"))  # export map to pdf
            print("Maps exported to pdf")

            df_within = feature_class_to_dataframe(taxlots_within)
            df_within.to_csv(os.path.join(dir_path, "1MileWithin.csv"))
            df_inside = feature_class_to_dataframe(taxlots_inside)
            df_inside.to_csv(os.path.join(dir_path, "1MileInside.csv"))

            dwelling_count(dwellings, taxlots_within, taxlots_inside, dir_path)

            if os.path.exists(os.path.join(dir_path, "OneMileStudySpreadsheet.xlsx")):
                print(f"Already Exists: {os.path.basename(os.path.join(dir_path, 'OneMileStudySpreadsheet.xlsx'))}")
            else:
                shutil.copyfile(os.path.join(os.path.dirname(dir_path), "OneMileStudyTemplate.xlsx"), os.path.join(dir_path, "OneMileStudySpreadsheet.xlsx"))

            aprx.saveACopy(os.path.join(dir_path, "map.aprx"))
            print("Project saved to directory")
            print(' ')
            del aprx
        else:
            print("Project path or directory path is missing.")





