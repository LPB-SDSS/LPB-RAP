"""LAFORET-PLUC-BE-RAP/OC/SFM - Filepaths
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK)"""


import os
import Parameters

# get the correct scenario input folder:
if Parameters.get_model_scenario() == 'weak_conservation':
    scenario_folder_inputs = os.path.join(os.getcwd(), 'inputs_weak_conservation')
elif Parameters.get_model_scenario() == 'enforced_conservation':
    scenario_folder_inputs = os.path.join(os.getcwd(), 'inputs_enforced_conservation')
elif Parameters.get_model_scenario() == 'no_conservation':
    scenario_folder_inputs = os.path.join(os.getcwd(), 'inputs_no_conservation')


# main input folders
folder_inputs_initial = os.path.join(os.getcwd(), scenario_folder_inputs, 'initial')

folder_inputs_static = os.path.join(os.getcwd(), scenario_folder_inputs, 'static')

folder_inputs_projection = os.path.join(os.getcwd(), scenario_folder_inputs, 'projection')

if Parameters.demand_configuration['overall_method'] == 'yield_units' or Parameters.demand_configuration['internal_or_external'] == 'external':
    folder_inputs_timeseries = os.path.join(os.getcwd(), scenario_folder_inputs, 'timeseries')

# SH: LPB alternation - initiate paths to input files
file_initial_LULC_input = os.path.join(
    folder_inputs_initial, 'initial_LULC_input')

file_initial_LULC_simulated_input = os.path.join(
    folder_inputs_initial, 'initial_LULC_simulated_input')

file_initial_LULC_simulated_for_worst_case_scenario_input = os.path.join(
    folder_inputs_initial, 'initial_LULC_simulated_for_worst_case_scenario_input')

file_initial_AGB_simulated_for_worst_case_scenario_input = os.path.join(
    folder_inputs_initial, 'initial_AGB_simulated_for_worst_case_scenario_input')

file_initial_net_forest_simulated_for_worst_case_scenario_input = os.path.join(
    folder_inputs_initial, 'initial_net_forest_simulated_for_worst_case_scenario_input')

file_initial_settlements_simulated_for_worst_case_scenario_input = os.path.join(
    folder_inputs_initial, 'initial_settlements_simulated_for_worst_case_scenario_input')

file_initial_settlements_input = os.path.join(
    folder_inputs_initial, 'initial_settlements_input')

file_initial_net_forest_input = os.path.join(
    folder_inputs_initial, 'initial_net_forest_input')

file_initial_plantation_age_input = os.path.join(
    folder_inputs_initial, 'initial_plantation_age_input')

file_initial_AGB_input = os.path.join(
    folder_inputs_initial, 'initial_AGB_input')

file_static_restricted_areas_input = os.path.join(
    folder_inputs_static, 'static_de-jure_restricted-areas_input')

file_static_excluded_areas_input = os.path.join(
    folder_inputs_static, 'static_excluded_areas_input')

file_static_dem_input = os.path.join(
    folder_inputs_static, 'static_dem_input')

file_static_null_mask_input = os.path.join(
    folder_inputs_static, 'static_null_mask_input')

file_static_streets_input = os.path.join(
    folder_inputs_static, 'static_streets_input')

file_static_cities_input = os.path.join(
    folder_inputs_static, 'static_cities_input')

file_static_freshwater_input = os.path.join(
    folder_inputs_static, 'static_freshwater_input')

file_static_succession_herbaceous_vegetation_input = os.path.join(
    folder_inputs_static, 'static_succession_herbaceous_vegetation_input.txt')

file_static_succession_shrubs_input = os.path.join(
    folder_inputs_static, 'static_succession_shrubs_input.txt')

file_static_succession_forest_input = os.path.join(
    folder_inputs_static, 'static_succession_forest_input.txt')

file_static_tile_1_input = os.path.join(
    folder_inputs_static, 'static_tile_1_input.map')

file_static_tile_2_input = os.path.join(
    folder_inputs_static, 'static_tile_2_input.map')

file_static_tile_3_input = os.path.join(
    folder_inputs_static, 'static_tile_3_input.map')

file_static_tile_4_input = os.path.join(
    folder_inputs_static, 'static_tile_4_input.map')

file_static_tile_5_input = os.path.join(
    folder_inputs_static, 'static_tile_5_input.map')

file_static_tile_6_input = os.path.join(
    folder_inputs_static, 'static_tile_6_input.map')

file_static_tile_7_input = os.path.join(
    folder_inputs_static, 'static_tile_7_input.map')

file_static_tile_8_input = os.path.join(
    folder_inputs_static, 'static_tile_8_input.map')

file_projection_decadal_population_2010_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2010_input')

file_projection_decadal_population_2020_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2020_input')

file_projection_decadal_population_2030_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2030_input')

file_projection_decadal_population_2040_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2040_input')

file_projection_decadal_population_2050_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2050_input')

file_projection_decadal_population_2060_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2060_input')

file_projection_decadal_population_2070_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2070_input')

file_projection_decadal_population_2080_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2080_input')

file_projection_decadal_population_2090_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2090_input')

file_projection_decadal_population_2100_input = os.path.join(
    folder_inputs_projection, 'projection_decadal_population_2100_input')

# potential natural vegetation distribution
file_projection_potential_natural_vegetation_distribution_2018_2020_input = os.path.join(
    folder_inputs_projection, 'projection_potential_natural_vegetation_distribution_2018-2020_input')

file_projection_potential_natural_vegetation_distribution_2021_2040_input = os.path.join(
    folder_inputs_projection, 'projection_potential_natural_vegetation_distribution_2021-2040_input')

file_projection_potential_natural_vegetation_distribution_2041_2060_input = os.path.join(
    folder_inputs_projection, 'projection_potential_natural_vegetation_distribution_2041-2060_input')

file_projection_potential_natural_vegetation_distribution_2061_2080_input = os.path.join(
    folder_inputs_projection, 'projection_potential_natural_vegetation_distribution_2061-2080_input')

file_projection_potential_natural_vegetation_distribution_2081_2100_input = os.path.join(
    folder_inputs_projection, 'projection_potential_natural_vegetation_distribution_2081-2100_input')

# AGB potential undisturbed maximum
file_projection_potential_maximum_undisturbed_AGB_2018_2020_input = os.path.join(
    folder_inputs_projection, 'projection_potential_maximum_undisturbed_AGB_2018-2020_input')

file_projection_potential_maximum_undisturbed_AGB_2021_2040_input = os.path.join(
    folder_inputs_projection, 'projection_potential_maximum_undisturbed_AGB_2021-2040_input')

file_projection_potential_maximum_undisturbed_AGB_2041_2060_input = os.path.join(
    folder_inputs_projection, 'projection_potential_maximum_undisturbed_AGB_2041-2060_input')

file_projection_potential_maximum_undisturbed_AGB_2061_2080_input = os.path.join(
    folder_inputs_projection, 'projection_potential_maximum_undisturbed_AGB_2061-2080_input')

file_projection_potential_maximum_undisturbed_AGB_2081_2100_input = os.path.join(
    folder_inputs_projection, 'projection_potential_maximum_undisturbed_AGB_2081-2100_input')

# AGB potential annual increment undisturbed
file_projection_potential_annual_undisturbed_AGB_increment_2018_2020_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_undisturbed_AGB_increment_2018-2020_input')

file_projection_potential_annual_undisturbed_AGB_increment_2021_2040_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_undisturbed_AGB_increment_2021-2040_input')

file_projection_potential_annual_undisturbed_AGB_increment_2041_2060_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_undisturbed_AGB_increment_2041-2060_input')

file_projection_potential_annual_undisturbed_AGB_increment_2061_2080_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_undisturbed_AGB_increment_2061-2080_input')

file_projection_potential_annual_undisturbed_AGB_increment_2081_2100_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_undisturbed_AGB_increment_2081-2100_input')

# AGB potential annual increment disturbed
file_projection_potential_annual_disturbed_AGB_increment_2018_2020_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_disturbed_AGB_increment_2018-2020_input')

file_projection_potential_annual_disturbed_AGB_increment_2021_2040_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_disturbed_AGB_increment_2021-2040_input')

file_projection_potential_annual_disturbed_AGB_increment_2041_2060_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_disturbed_AGB_increment_2041-2060_input')

file_projection_potential_annual_disturbed_AGB_increment_2061_2080_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_disturbed_AGB_increment_2061-2080_input')

file_projection_potential_annual_disturbed_AGB_increment_2081_2100_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_disturbed_AGB_increment_2081-2100_input')

# AGB potential annual increment plantation
file_projection_potential_annual_plantation_AGB_increment_2018_2020_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_plantation_AGB_increment_2018-2020_input')

file_projection_potential_annual_plantation_AGB_increment_2021_2040_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_plantation_AGB_increment_2021-2040_input')

file_projection_potential_annual_plantation_AGB_increment_2041_2060_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_plantation_AGB_increment_2041-2060_input')

file_projection_potential_annual_plantation_AGB_increment_2061_2080_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_plantation_AGB_increment_2061-2080_input')

file_projection_potential_annual_plantation_AGB_increment_2081_2100_input = os.path.join(
    folder_inputs_projection, 'projection_potential_annual_plantation_AGB_increment_2081-2100_input')

# potential yield for PLUC demand / yield simulation, LPB alternation:
if Parameters.demand_configuration['overall_method'] == 'yield_units':
    # cropland-annual crops
    file_projection_potential_yield_cropland_annual_crops_2018_2020_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_cropland-annual_crops_2018-2020_input')

    file_projection_potential_yield_cropland_annual_crops_2021_2040_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_cropland-annual_crops_2021-2040_input')

    file_projection_potential_yield_cropland_annual_crops_2041_2060_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_cropland-annual_crops_2041-2060_input')

    file_projection_potential_yield_cropland_annual_crops_2061_2080_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_cropland-annual_crops_2061-2080_input')

    file_projection_potential_yield_cropland_annual_crops_2081_2100_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_cropland-annual_crops_2081-2100_input')

    # agroforestry crops (may be later extended to meat and wood)
    file_projection_potential_yield_agroforestry_crops_2018_2020_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_agroforestry_crops_2018-2020_input')

    file_projection_potential_yield_agroforestry_crops_2021_2040_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_agroforestry_crops_2021-2040_input')

    file_projection_potential_yield_agroforestry_crops_2041_2060_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_agroforestry_crops_2041-2060_input')

    file_projection_potential_yield_agroforestry_crops_2061_2080_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_agroforestry_crops_2061-2080_input')

    file_projection_potential_yield_agroforestry_crops_2081_2100_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_agroforestry_crops_2081-2100_input')

    # livestock density
    file_projection_potential_yield_livestock_density_2018_2020_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_livestock_density_2018-2020_input')

    file_projection_potential_yield_livestock_density_2021_2040_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_livestock_density_2021-2040_input')

    file_projection_potential_yield_livestock_density_2041_2060_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_livestock_density_2041-2060_input')

    file_projection_potential_yield_livestock_density_2061_2080_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_livestock_density_2061-2080_input')

    file_projection_potential_yield_livestock_density_2081_2100_input = os.path.join(
        folder_inputs_projection, 'projection_potential_yield_livestock_density_2081-2100_input')

# TIMESERIES
# deterministic
if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'external':
    file_deterministic_demand_footprint_input = os.path.join(
    folder_inputs_timeseries,'deterministic_approach','deterministic_demand_footprint_input.csv')

if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
    file_deterministic_demand_yield_units_input = os.path.join(
    folder_inputs_timeseries,'deterministic_approach','deterministic_demand_yield_units_input.csv')

    file_deterministic_maximum_yield_input = os.path.join(
    folder_inputs_timeseries,'deterministic_approach','deterministic_maximum_yield_input.csv')

# stochastic
if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
    file_stochastic_demand_yield_units_HIGH_input = os.path.join(
    folder_inputs_timeseries,'stochastic_approach','stochastic_demand_yield_units_HIGH_input.csv')

    file_stochastic_demand_yield_units_LOW_input = os.path.join(
    folder_inputs_timeseries,'stochastic_approach','stochastic_demand_yield_units_LOW_input.csv')

    file_stochastic_maximum_yield_input = os.path.join(
    folder_inputs_timeseries,'stochastic_approach','stochastic_maximum_yield_input.csv')


#=================================================================================================#

# SH: LPB alternation - initiate output folders
# SH: output folders level 0
if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
    main_output_folder = 'outputs_footprint_internal'
if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'external':
    main_output_folder = 'outputs_footprint_external'
if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
    main_output_folder = 'outputs_yield_units_deterministic'
if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
    main_output_folder = 'outputs_yield_units_stochastic'

# level 1
folder_outputs = os.path.join(os.getcwd(), main_output_folder, 'outputs_' + str(Parameters.get_model_scenario()))
os.makedirs(folder_outputs, exist_ok=True)

# SH: output folders level 2
folder_LPB = os.path.join(os.getcwd(), folder_outputs, 'LPB')
os.makedirs(folder_LPB, exist_ok=True)

folder_RAP = os.path.join(os.getcwd(), folder_outputs, 'RAP')
os.makedirs(folder_RAP, exist_ok=True)

folder_SFM = os.path.join(os.getcwd(), folder_outputs, 'SFM')
os.makedirs(folder_SFM, exist_ok=True)

folder_OC = os.path.join(os.getcwd(), folder_outputs, 'OC')
os.makedirs(folder_OC, exist_ok=True)

# SH: output folders level 3
folder_slope = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'model_internal_slope_map')
os.makedirs(folder_slope, exist_ok=True)

folder_TEST = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'TEST')
os.makedirs(folder_TEST, exist_ok=True)

# LPB
folder_GIFs = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'GIFs')
os.makedirs(folder_GIFs, exist_ok=True)

folder_CSVs = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'CSVs')
os.makedirs(folder_CSVs, exist_ok=True)

folder_LPB_tidy_data = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'tidy_data')
os.makedirs(folder_LPB_tidy_data, exist_ok=True)

if Parameters.get_fragmentation_mplc_RAP_analysis_choice() == True:
    folder_PylandStats_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'PyLandStats_mplc_analysis')
    os.makedirs(folder_PylandStats_mplc, exist_ok=True)

# SFM
folder_SFM_GIFs = os.path.join(
    os.getcwd(), folder_outputs, 'SFM', 'GIFs')
os.makedirs(folder_SFM_GIFs, exist_ok=True)

folder_SFM_CSVs = os.path.join(
    os.getcwd(), folder_outputs, 'SFM', 'CSVs')
os.makedirs(folder_SFM_CSVs, exist_ok=True)

folder_SFM_tidy_data = os.path.join(
    os.getcwd(), folder_outputs, 'SFM', 'tidy_data')
os.makedirs(folder_SFM_tidy_data, exist_ok=True)

# OC
folder_OC_GIFs = os.path.join(
    os.getcwd(), folder_outputs, 'OC', 'GIFs')
os.makedirs(folder_OC_GIFs, exist_ok=True)

folder_OC_CSVs = os.path.join(
    os.getcwd(), folder_outputs, 'OC', 'CSVs')
os.makedirs(folder_OC_CSVs, exist_ok=True)

folder_OC_tidy_data = os.path.join(
    os.getcwd(), folder_outputs, 'OC', 'tidy_data')
os.makedirs(folder_OC_tidy_data, exist_ok=True)

# RAP
folder_RAP_tidy_data = os.path.join(
    os.getcwd(), folder_outputs, 'RAP', 'tidy_data')
os.makedirs(folder_RAP_tidy_data, exist_ok=True)

if Parameters.get_fragmentation_mplc_RAP_analysis_choice() == True:
    folder_PylandStats_RAP = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'PyLandStats_RAP_analysis')
    os.makedirs(folder_PylandStats_RAP, exist_ok=True)

if Parameters.get_worst_case_scenario_decision() is True:
    folder_inputs_simulated_for_worst_case_scenario_from_LPB_BAU = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'inputs_simulated_for_worst-case-scenario_from_LPB_BAU')
    os.makedirs(folder_inputs_simulated_for_worst_case_scenario_from_LPB_BAU, exist_ok=True)

folder_LULCC_simulation = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'LULCC_simulation')
os.makedirs(folder_LULCC_simulation, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_LULCC_most_probable_landscape_configuration = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'LULCC_most_probable_landscape_configuration')
    os.makedirs(folder_LULCC_most_probable_landscape_configuration, exist_ok=True)

folder_conflict_in_restricted_areas = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'conflict_in_restricted_areas')
os.makedirs(folder_conflict_in_restricted_areas, exist_ok=True)

folder_CONFLICT_most_probable_landscape_configuration = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'CONFLICT_most_probable_landscape_configuration')
os.makedirs(folder_CONFLICT_most_probable_landscape_configuration, exist_ok=True)

folder_AGB = os.path.join(os.getcwd(), folder_outputs, 'LPB', 'AGB')
os.makedirs(folder_AGB, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_AGB_most_probable_landscape_configuration = os.path.join(os.getcwd(), folder_outputs, 'LPB', 'AGB_most_probable_landscape_configuration')
    os.makedirs(folder_AGB_most_probable_landscape_configuration, exist_ok=True)

folder_anthropogenic_features_deterministic = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'ANTHROPOGENIC_FEATURES_DETERMINISTIC')
os.makedirs(folder_anthropogenic_features_deterministic, exist_ok=True)

folder_degradation_regeneration = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration')
os.makedirs(folder_degradation_regeneration, exist_ok=True)

folder_forest_probability_maps = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'forest_probability_maps')
os.makedirs(folder_forest_probability_maps, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration')
    os.makedirs(
        folder_REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration, exist_ok=True)

folder_succession_age = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'succession_age')
os.makedirs(folder_succession_age, exist_ok=True)

# folder_RAP_simulation = os.path.join(
#     os.getcwd(), 'outputs', 'RAP', 'RAP_simulation')
# os.makedirs(folder_RAP_simulation, exist_ok=True)

# SH: output folders level 4
folder_dynamic_environment_map_probabilistic = os.path.join(os.getcwd(
), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic')
os.makedirs(folder_dynamic_environment_map_probabilistic, exist_ok=True)

folder_dynamic_singular_LUTs_probabilistic = os.path.join(os.getcwd(
), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic')
os.makedirs(folder_dynamic_singular_LUTs_probabilistic, exist_ok=True)

folder_dynamic_settlements_deterministic = os.path.join(os.getcwd(
), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_settlements_deterministic')
os.makedirs(folder_dynamic_settlements_deterministic, exist_ok=True)

folder_dynamic_anthropogenic_impact_buffer_deterministic = os.path.join(os.getcwd(
), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_anthropogenic_impact_buffer_deterministic')
os.makedirs(
    folder_dynamic_anthropogenic_impact_buffer_deterministic, exist_ok=True)

folder_dynamic_population_deterministic = os.path.join(os.getcwd(
), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_population_deterministic')
os.makedirs(folder_dynamic_population_deterministic, exist_ok=True)

probabilistic_output_options_dictionary = Parameters.get_LPB_basic_probabilistic_output_options()
if Parameters.demand_configuration['overall_method'] == 'yield_units' and probabilistic_output_options_dictionary['yield_maps'] == True:
    folder_dynamic_yield_maps_probabilistic = os.path.join(os.getcwd(
    ), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_yield_maps_probabilistic')
    os.makedirs(folder_dynamic_yield_maps_probabilistic, exist_ok=True)

    # LUT02_cropland-annual_crop_yields
    if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
        folder_LUT02_cropland_annual_crop_yields = os.path.join(os.getcwd(
        ), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_yield_maps_probabilistic', 'LUT02_cropland-annual_crop_yields')
        os.makedirs(folder_LUT02_cropland_annual_crop_yields, exist_ok=True)

    # LUT03_pasture_livestock_yields
    if 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
        folder_LUT03_pasture_livestock_yields = os.path.join(os.getcwd(
        ), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_yield_maps_probabilistic', 'LUT03_pasture_livestock_yields')
        os.makedirs(folder_LUT03_pasture_livestock_yields, exist_ok=True)

    # LUT04_agroforestry_crop_yields
    if 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
        folder_LUT04_agroforestry_crop_yields = os.path.join(os.getcwd(
        ), folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_yield_maps_probabilistic', 'LUT04_agroforestry_crop_yields')
        os.makedirs(folder_LUT04_agroforestry_crop_yields, exist_ok=True)





# folder_dynamic_undisturbed_forest_probabilistic = os.path.join(os.getcwd(
# ), 'outputs', 'LPB', 'LULCC_simulation', 'dynamic_undisturbed_forest_probabilistic')
# os.makedirs(folder_dynamic_undisturbed_forest_probabilistic, exist_ok=True)

# folder_dynamic_net_forest_probabilistic = os.path.join(os.getcwd(
# ), 'outputs', 'LPB', 'LULCC_simulation', 'dynamic_net_forest_probabilistic')
# os.makedirs(folder_dynamic_net_forest_probabilistic, exist_ok=True)

folder_land_use_conflict = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'conflict_in_restricted_areas', 'land_use_conflict')
os.makedirs(folder_land_use_conflict, exist_ok=True)

folder_forest_land_use_conflict = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'conflict_in_restricted_areas', 'forest_land_use_conflict')
os.makedirs(folder_forest_land_use_conflict, exist_ok=True)

folder_degradation_low = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'degradation_low')
os.makedirs(folder_degradation_low, exist_ok=True)

folder_degradation_moderate = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'degradation_moderate')
os.makedirs(folder_degradation_moderate, exist_ok=True)

folder_degradation_severe = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'degradation_severe')
os.makedirs(folder_degradation_severe, exist_ok=True)

folder_degradation_absolute = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'degradation_absolute')
os.makedirs(folder_degradation_absolute, exist_ok=True)

folder_regeneration_low = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'regeneration_low')
os.makedirs(folder_regeneration_low, exist_ok=True)

folder_regeneration_medium = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'regeneration_medium')
os.makedirs(folder_regeneration_medium, exist_ok=True)

folder_regeneration_high = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'regeneration_high')
os.makedirs(folder_regeneration_high, exist_ok=True)

folder_regeneration_full = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'degradation_regeneration', 'regeneration_full')
os.makedirs(folder_regeneration_full, exist_ok=True)

# folder_gross_forest = os.path.join(
#     os.getcwd(), 'outputs', 'LPB', 'forest_probability_maps', 'gross_forest')
# os.makedirs(folder_gross_forest, exist_ok=True)

folder_net_forest = os.path.join(
    os.getcwd(), folder_outputs, 'LPB', 'forest_probability_maps', 'net_forest')
os.makedirs(folder_net_forest, exist_ok=True)

# folder_undisturbed_forest = os.path.join(
#     os.getcwd(), 'outputs', 'LPB', 'forest_probability_maps', 'undisturbed_forest')
# os.makedirs(folder_undisturbed_forest, exist_ok=True)

# folder_disturbed_forest = os.path.join(
#     os.getcwd(), 'outputs', 'LPB', 'forest_probability_maps', 'disturbed_forest')
# os.makedirs(folder_disturbed_forest, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_LULCC_initial_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'LULCC_most_probable_landscape_configuration', 'initial_most_probable_landscape_configuration')
    os.makedirs(folder_LULCC_initial_mplc, exist_ok=True)

    folder_LULCC_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'LULCC_most_probable_landscape_configuration',
        'most_probable_landscape_configuration')
    os.makedirs(folder_LULCC_mplc, exist_ok=True)

    folder_LULCC_mplc_probabilities = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'LULCC_most_probable_landscape_configuration',
        'most_probable_landscape_configuration_probabilities')
    os.makedirs(folder_LULCC_mplc_probabilities, exist_ok=True)

    folder_LULCC_mplc_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'LULCC_most_probable_landscape_configuration',
        'most_probable_landscape_configuration_probabilities_classified')
    os.makedirs(folder_LULCC_mplc_probabilities_classified, exist_ok=True)

if Parameters.get_model_scenario() != 'worst case' and Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_CONFLICT_mplc_forest_land_use = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'CONFLICT_most_probable_landscape_configuration', 'forest_land_use_conflict_probabilities_classified')
    os.makedirs(folder_CONFLICT_mplc_forest_land_use, exist_ok=True)

    folder_CONFLICT_mplc_land_use = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'CONFLICT_most_probable_landscape_configuration',
        'land_use_conflict_probabilities_classified')
    os.makedirs(folder_CONFLICT_mplc_land_use, exist_ok=True)

    folder_CONFLICT_mplc_active_land_use = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'CONFLICT_most_probable_landscape_configuration',
        'mplc_land_use_in_restricted_areas')
    os.makedirs(folder_CONFLICT_mplc_active_land_use, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_100years_no_impact_forest_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration', '100years_no_impact')
    os.makedirs(
        folder_100years_no_impact_forest_mplc, exist_ok=True)

    folder_remaining_no_impact_forest_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration',
        'remaining_no_impact')
    os.makedirs(
        folder_remaining_no_impact_forest_mplc, exist_ok=True)

    folder_undisturbed_forest_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB',
        'REMAINING_NO_IMPACT_plus_100_YEARS_NO_IMPACT_most_probable_landscape_configuration',
        'undisturbed_forest')
    os.makedirs(
        folder_undisturbed_forest_mplc, exist_ok=True)

if Parameters.get_worst_case_scenario_decision() is True:
    folder_inputs_initial_worst_case_scenario = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'inputs_simulated_for_worst-case-scenario_from_LPB_' + str(Parameters.get_model_scenario()), 'initial')
    os.makedirs(folder_inputs_initial_worst_case_scenario, exist_ok=True)

# SH: output folders level 5
folder_LUT01 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT01')
os.makedirs(folder_LUT01, exist_ok=True)

folder_LUT02 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT02')
os.makedirs(folder_LUT02, exist_ok=True)

folder_LUT03 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT03')
os.makedirs(folder_LUT03, exist_ok=True)

folder_LUT04 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT04')
os.makedirs(folder_LUT04, exist_ok=True)

folder_LUT05 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT05')
os.makedirs(folder_LUT05, exist_ok=True)

folder_LUT06 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT06')
os.makedirs(folder_LUT06, exist_ok=True)

folder_LUT07 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT07')
os.makedirs(folder_LUT07, exist_ok=True)

folder_LUT08 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT08')
os.makedirs(folder_LUT08, exist_ok=True)

folder_LUT09 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT09')
os.makedirs(folder_LUT09, exist_ok=True)

folder_LUT10 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT10')
os.makedirs(folder_LUT10, exist_ok=True)

folder_LUT11 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT11')
os.makedirs(folder_LUT11, exist_ok=True)

folder_LUT12 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT12')
os.makedirs(folder_LUT12, exist_ok=True)

folder_LUT13 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT13')
os.makedirs(folder_LUT13, exist_ok=True)

folder_LUT14 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT14')
os.makedirs(folder_LUT14, exist_ok=True)

folder_LUT15 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT15')
os.makedirs(folder_LUT15, exist_ok=True)

folder_LUT16 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT16')
os.makedirs(folder_LUT16, exist_ok=True)

folder_LUT17 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT17')
os.makedirs(folder_LUT17, exist_ok=True)

folder_LUT18 = os.path.join(os.getcwd(), folder_outputs, 'LPB',
                            'LULCC_simulation', 'dynamic_singular_LUTs_probabilistic', 'LUT18')
os.makedirs(folder_LUT18, exist_ok=True)

if Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
    folder_FOREST_PROBABILITY_MAPS_fud_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_disturbed_undisturbed', 'most_probable_landscape_configuration')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_fud_mplc, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_disturbed_undisturbed', 'most_probable_landscape_configuration_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_fng_mplc = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_net_gross', 'most_probable_landscape_configuration')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_fng_mplc, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_fng_mplc_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_net_gross', 'most_probable_landscape_configuration_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_fng_mplc_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_disturbed_undisturbed',
        'most_probable_landscape_configuration_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_undisturbed_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_only_undisturbed_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_undisturbed_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_disturbed_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_only_disturbed_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_disturbed_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_degradation_and_regeneration')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_degradation_and_regeneration_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_deforested_LUT17_probabilities_classified = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_deforested_LUT17_probabilities_classified')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_deforested_LUT17_probabilities_classified, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_mplc_forest_conversion = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_mplc_conversion')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_mplc_forest_conversion, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_mplc_forest_undisturbed_habitat = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_mplc_truly_undisturbed_forest_habitat')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_mplc_forest_undisturbed_habitat, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_mplc_net_detailed = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_net_detailed')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_mplc_net_detailed, exist_ok=True)

    folder_FOREST_PROBABILITY_MAPS_mplc_net_boolean = os.path.join(
        os.getcwd(), folder_outputs, 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration',
        'forest_net_boolean')
    os.makedirs(
        folder_FOREST_PROBABILITY_MAPS_mplc_net_boolean, exist_ok=True)



if Parameters.get_order_of_forest_deforestation_and_conversion() is True:
    folder_deforested_before_conversion = os.path.join(os.getcwd(), folder_outputs, 'LPB', 'forest_probability_maps', 'deforested_before_conversion')
    os.makedirs(folder_deforested_before_conversion, exist_ok=True)

###############################################################################
################# MPLC ########################################################
###############################################################################

file_static_mplc_correction_rules_for_abandoned_types_input = os.path.join(
    folder_inputs_static, 'static_correction_rules_for_abandoned_types_input.txt')

###############################################################################
################# RAP #########################################################
###############################################################################

if Parameters.get_model_version() == 'LPB-RAP':
    file_static_RAP_other_ecosystems_input = os.path.join(
        folder_inputs_static, 'static_RAP_other_ecosystems_input')

    folder_RAP_CSVs = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'CSVs')
    os.makedirs(folder_RAP_CSVs, exist_ok=True)

    folder_RAP_GIFs = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'GIFs')
    os.makedirs(folder_RAP_GIFs, exist_ok=True)

    folder_RAP_targeted_net_forest = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'targeted_net_forest')
    os.makedirs(folder_RAP_targeted_net_forest, exist_ok=True)

    folder_RAP_POSSIBLE_LANDSCAPE_CONFIGURATION = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'POSSIBLE_LANDSCAPE_CONFIGURATION')
    os.makedirs(folder_RAP_POSSIBLE_LANDSCAPE_CONFIGURATION, exist_ok=True)

    folder_RAP_restricted_areas = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'restricted_areas')
    os.makedirs(folder_RAP_restricted_areas, exist_ok=True)

    folder_RAP_potential_minimum_restoration = os.path.join(
        os.getcwd(), folder_outputs, 'RAP', 'potential_minimum_restoration')
    os.makedirs(folder_RAP_potential_minimum_restoration, exist_ok=True)


