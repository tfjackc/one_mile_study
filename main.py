import os
from dir_funcs import create_folder
from mapping_functions import map_data
from arcgis_funcs import (
    get_target_taxlot,
    buffer_property,
    intersect_taxlots_helion,
    clip_taxlots,
    create_study_area,
    get_dwellings,
    add_fields
)

# eventually replace with an input statement or param0 for flexible input
lot_number = "lot_number"
taxlots_helion = "taxlot_layer"
address_points = "address_points"
arcproj = "aprx"
deer_layer = "deer_layer"
elk_layer = "elk_layer"
symbology_layers = ["symbology-layers"]


def run_one_mile_study(maptaxlot):
    # set directory
    main_dir = os.getcwd()
    # if dir does not exist --> create one
    create_folder(main_dir, maptaxlot)
    # set variables
    target_property = f"{maptaxlot}\\target_property.shp"
    one_mile_buffer = f"{maptaxlot}\\one_mile_buffer.shp"
    one_mile_within = f"{maptaxlot}\\one_mile_within.shp"
    one_mile_inside = f"{maptaxlot}\\one_mile_inside.shp"
    dwellings = f"{maptaxlot}\\dwellings.shp"
    study_area = f"{maptaxlot}\\study_area.shp"
    # ------------------------------------------
    # if data does not exist --> run arcpy functions to create data
    # ------------------------------------------
    # create target_property
    get_target_taxlot(
        main_dir,
        maptaxlot
    )
    # create one mile buffer
    buffer_property(
        os.path.join(main_dir, target_property),
        os.path.join(main_dir, one_mile_buffer)
    )
    # create one mile within layer
    intersect_taxlots_helion(
        os.path.join(main_dir, one_mile_buffer),
        os.path.join(main_dir, one_mile_within)
    )
    # create one mile inside layer
    clip_taxlots(
        os.path.join(main_dir, one_mile_buffer),
        os.path.join(main_dir, one_mile_within),
        os.path.join(main_dir, one_mile_inside)
    )
    # create study area
    create_study_area(
        os.path.join(main_dir, one_mile_within),
        os.path.join(main_dir, study_area)
    )
    # intersect address points to get dwellings
    get_dwellings(
        os.path.join(main_dir, one_mile_within),
        address_points,
        os.path.join(main_dir, dwellings)
    )
    # add fields (ID, & GISACRES)
    add_fields(
        os.path.join(main_dir, one_mile_within),
        os.path.join(main_dir, one_mile_inside)
    )
    # create mapping component
    map_data(
        arcproj=arcproj,
        target_property=os.path.join(main_dir, target_property),
        one_mile_buffer=os.path.join(main_dir, one_mile_buffer),
        one_mile_within=os.path.join(main_dir, one_mile_within),
        one_mile_inside=os.path.join(main_dir, one_mile_inside),
        dwellings=os.path.join(main_dir, dwellings),
        study_area=os.path.join(main_dir, study_area),
        deer_layer=deer_layer,
        elk_layer=elk_layer,
        lot_number=lot_number,
        symbology_layers=symbology_layers
    )


if __name__ == '__main__':
    run_one_mile_study(lot_number)