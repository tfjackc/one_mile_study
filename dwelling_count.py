import geopandas as gpd

dwellings = "Dwellings"
within_one_mile = "SelectedTaxlots"
clipped_one_mile = "ClippedTaxlots"
lot_number = ""

dwelling_gdf = gpd.read_file(dwellings)
within_gdf = gpd.read_file(within_one_mile)
inside_gdf = gpd.read_file(clipped_one_mile)

dw_gdf = dwelling_gdf[['full_add_1', 'geometry']]
w_gdf = within_gdf[['MAPTAXLOT', 'geometry']]
i_gdf = inside_gdf[['MAPTAXLOT', 'geometry']]

join_within_gdf = w_gdf.sjoin(dw_gdf, how="left")
join_inside_gdf = i_gdf.sjoin(dw_gdf, how="left")

join_within_gdf['count'] = join_within_gdf['full_add_1'].notnull().astype(int)
join_inside_gdf['count'] = join_inside_gdf['full_add_1'].notnull().astype(int)

join_within_subset_gdf = join_within_gdf[['MAPTAXLOT', 'full_add_1', 'count']]
join_inside_subset_gdf = join_inside_gdf[['MAPTAXLOT', 'full_add_1', 'count']]

# send to csv
join_within_subset_gdf.to_csv(f"{lot_number}\join_within_subset.csv")
join_inside_subset_gdf.to_csv(f"{lot_number}\join_inside_subset.csv")