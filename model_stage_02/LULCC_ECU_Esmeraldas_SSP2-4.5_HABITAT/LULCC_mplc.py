"""LAFORET-PLUC-BE-RAP/SFM/OC - LULCC_mplc
Sonja Holler (SH, RAP), Melvin Lippe (ML, OC) and Daniel Kuebler (DK, SFM),
2021/Q2 - 2023/Q3
model stage 2: 2024/Q1-Q2

Developed in Python 3.9+ and PCRaster 4.3.1+

This module aggregates the LPB-basic output of Monte Carlo averages to a new singular map per time step by the highest probability of a pixel.

ATTENTION: the exported maps in this module might get used in LPB-RAP, therefore they are restricted to the 8 characters maximum and have a time step suffix."""

# HINT: within comments "class" refers almost always to the class output for the GIFs-maps, only for the classified probabilities maps "class/category" is one of seven categories

# SH: execute LPB-mplc
import ast
from datetime import datetime
import time
import pcraster
from pcraster import *
from pcraster.framework import *
import builtins
import numpy
import Parameters
import Filepaths
import generate_PCRaster_conform_output_name
import sys, os
import json
import operator
#import PyLandStats_adapter
import subprocess
import tempfile


# check for habitat analysis if the OUTPUTS folder contains already input which cannot be overwritten, break with assert message
habitat_analysis_outputs_folder = Filepaths.folder_habitat_analysis_mplc_outputs
for dirpath, dirnames, files in os.walk(habitat_analysis_outputs_folder):
    assert len(files) == 0, f'\nACTION REQUIRED:\nthe folder\n{habitat_analysis_outputs_folder}\nalready contains files - DELETE or RENAME it, the Omniscape- & Circuitscape-files cannot be overwritten!'

#get the habitat analysis dictionaries
habitat_analysis_dictionary = Parameters.get_habitat_analysis_choice() # perform habitat analysis at all?
habitat_analysis_simulation_years_list = Parameters.get_habitat_analysis_simulation_years_choice() # perform each year or selected years only time intensive components
habitat_connectivity_simulation_dictionary = Parameters.get_potential_habitat_connectivity_simulation_choice() # Use Omniscape?
PHC_simulation_dictionary = Parameters.get_potential_habitat_corridors_simulation_choice() # Use Circuitscape?
LPBRAP_Omniscape_settings_dictionary = Parameters.get_LPBRAP_Omniscape_settings_dictionary()
LPBRAP_Circuitscape_settings_dictionary = Parameters.get_LPBRAP_Circuitscape_settings_dictionary()


if habitat_analysis_dictionary['do_habitat_analysis'] == True:
    if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True or PHC_simulation_dictionary['simulate_PHCs'] == True:
        if(habitat_connectivity_simulation_dictionary['simulation_in'] == 'mplc' or habitat_connectivity_simulation_dictionary['simulation_in'] == 'mplc+RAP') or (PHC_simulation_dictionary['simulation_in'] == 'mplc' or PHC_simulation_dictionary['simulation_in'] == 'mplc+RAP'):
            # Define map transformation methods
            # map_to_asc
            def map_to_asc(in_filename, out_filename, no_data=-9999):
                cmd = f"map2asc -a -m {no_data} {in_filename} {out_filename}"
                subprocess.run(cmd.split(), check=True)

            # asc_to_map
            def asc_to_map(clone, in_filename, dtype="S"):
                fname = tempfile.NamedTemporaryFile(delete=False)
                cmd = f"asc2map --clone {clone} -{dtype} -a {in_filename} {fname.name}.map"
                subprocess.run(cmd.split(), check=True)
                return readmap(f"{fname.name}.map")

            try:
                from configparser import ConfigParser
            except ImportError:
                from ConfigParser import ConfigParser  # ver. < 3.0


            if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
                # defining setclone for larger map extent
                def _setclone_extended():
                    original_landscape_extent_map = readmap(Filepaths.file_static_null_mask_input)
                    original_landscape_extent_numpy = pcr2numpy(original_landscape_extent_map, -9999)
                    original_west = pcraster._pcraster.clone().west()
                    original_north = pcraster._pcraster.clone().north()
                    # getting padding pixels (Omniscape radius)
                    cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
                    # halo padding in numpy
                    numpy_raster_padded = numpy.pad(original_landscape_extent_numpy,
                                                    pad_width=cells_to_add,
                                                    mode="constant",
                                                    constant_values=-9999)
                    # getting padded raster properties and SETCLONE LARGE:
                    number_of_rows = int(numpy.shape(numpy_raster_padded)[0])
                    number_of_cols = int(numpy.shape(numpy_raster_padded)[1])
                    pixel_size = float(Parameters.get_cell_length_in_m())
                    west = float(original_west - (pixel_size * cells_to_add))
                    north = float(original_north + (pixel_size * cells_to_add))
                    pcraster.setclone(number_of_rows, number_of_cols, pixel_size, west, north)
                    numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar,
                                                        array=numpy_raster_padded,
                                                        mv=-9999)
                    report_setclone_extended_input_map_path = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map')
                    report(numpy_raster_padded_map, report_setclone_extended_input_map_path)


                    # defining setclone original extent
                def _setclone_original():
                    pcraster.setclone(f"{Filepaths.file_static_null_mask_input}.map")


# =================================================================== #
# For testing, debugging and submission: set random seed to make the results consistent (1)
# set random seed 0 = every time new results
seed = int(Parameters.get_random_seed())
setrandomseed(seed)

# =================================================================== #
# # ATTENTION: The PCRaster maptotal has a rounding error, therefore we use the numpy calculation
# def numpy_maptotal(a_map):
#     numpy_maptotal = pcr2numpy(a_map, 0).sum()
#     return numpy_maptotal
#
# maptotal = numpy_maptotal

# =================================================================== #
# SH: LPB alternation
# the configuration of this dictionary in Parameters.py determines the LPB-mplc inputs und according calculations.
# Options set to false in Parameters.py will decrease needed hard drive space but also analytical output in LPB-mplc.
global probabilistic_output_options_dictionary
probabilistic_output_options_dictionary = Parameters.get_LPB_basic_probabilistic_output_options()
# =================================================================== #
# global variables for dynamic use in GIF files

global dictionary_of_anthropogenic_features
dictionary_of_anthropogenic_features = {}
dictionary_of_anthropogenic_features['population'] = {}
dictionary_of_anthropogenic_features['streets'] = {}
dictionary_of_anthropogenic_features['cities'] = {}
dictionary_of_anthropogenic_features['settlements'] = {}
global dictionary_of_accumulated_land_use_in_restricted_areas
dictionary_of_accumulated_land_use_in_restricted_areas = {}
dictionary_of_accumulated_land_use_in_restricted_areas[1] = {}
dictionary_of_accumulated_land_use_in_restricted_areas[2] = {}
dictionary_of_accumulated_land_use_in_restricted_areas[3] = {}
dictionary_of_accumulated_land_use_in_restricted_areas[4] = {}
dictionary_of_accumulated_land_use_in_restricted_areas[5] = {}
global dictionary_of_net_forest_information
dictionary_of_net_forest_information = {}
dictionary_of_net_forest_information['probable_net_forest_area'] = {}
dictionary_of_net_forest_information['probable_percentage_of_landscape'] = {}
dictionary_of_net_forest_information['mplc_net_forest_area'] = {}
dictionary_of_net_forest_information['mplc_percentage_of_landscape'] = {}
dictionary_of_net_forest_information['mplc_net_disturbed_area'] = {}
dictionary_of_net_forest_information['mplc_net_disturbed_percentage_of_landscape'] = {}
dictionary_of_net_forest_information['mplc_net_undisturbed_area'] = {}
dictionary_of_net_forest_information['mplc_net_undisturbed_percentage_of_landscape'] = {}
global dictionary_of_undisturbed_forest
dictionary_of_undisturbed_forest = {}
dictionary_of_undisturbed_forest['succession_age'] = 0
dictionary_of_undisturbed_forest['maptotal_undisturbed_forest'] = []
dictionary_of_undisturbed_forest['maptotal_new_undisturbed_forest'] = []
global list_of_new_pixels_of_forest_land_use_conflict
list_of_new_pixels_of_forest_land_use_conflict = []
global list_of_new_pixels_of_land_use_conflict
list_of_new_pixels_of_land_use_conflict = []
global list_of_new_converted_forest_area
list_of_new_converted_forest_area = []
global list_of_new_deforested_area
list_of_new_deforested_area = []

# =================================================================== #

class MostProbableLandscapeConfiguration(DynamicModel):
    def __init__(self):
        DynamicModel.__init__(self)
        setclone(f"{Filepaths.file_static_null_mask_input}.map")

    def initial(self):
        print('\n>>> running initial ...')

        self.start_time = datetime.now()

        #### prepare tidy data ######
        self.tidy_output_folder, self.tidy_output_files_definitions = self._prepare_tidy_output()
        print('\nprepared tidy data output')

        print('\nloading maps and CSV data ...')

        # import all needed maps
        self.null_mask_map = readmap(Filepaths.file_static_null_mask_input)
        self.static_restricted_areas_map = readmap(Filepaths.file_static_restricted_areas_input)
        self.dem_map = readmap(Filepaths.file_static_dem_input)
        self.cities_map = readmap(Filepaths.file_static_cities_input)
        self.cities_map = cover(boolean(self.cities_map), boolean(self.null_mask_map))
        self.streets_map = readmap(Filepaths.file_static_streets_input)
        self.streets_map = cover(boolean(self.streets_map), boolean(self.null_mask_map))

        # create map with small noise to prevent the same probabilities
        self.small_noise_map = uniform(1) / 1000000

        # =================================================================== #
        # determine once the original number of sample folders for a note on the output CSV

        sample_folders = list([file for file in os.listdir(
            Filepaths.folder_dynamic_environment_map_probabilistic) if not file.startswith('.')]) # imports the LUTs sub-folders as a List

        self.original_number_of_samples = len(sample_folders)

        # =================================================================== #

        # import the singular LUTs MC averages with a nested dictionary:
        self.dictionary_of_LUTs_MC_averages_dictionaries = {} # nested dictionary result 1
        singular_LUT_MC_average_dictionary = {} # result 18 dictionaries numbered 1 to 18 with 1-N time steps as keys and 1-N time steps files as values

        sub_folders_LUTs = list([file for file in os.listdir(
            Filepaths.folder_dynamic_singular_LUTs_probabilistic) if not file.startswith('.')]) # imports the LUTs sub-folders as a List
        # sort them in the right order
        sub_folders_LUTs = sorted(sub_folders_LUTs)
        count = 1
        for a_sub_folder in sub_folders_LUTs:
            # name the nested dictionaries like the nominal land use types (1 - 18)
            a_name = count
            # built the path to the MC averages folder
            path_to_MC_averages_folder = os.path.join(Filepaths.folder_dynamic_singular_LUTs_probabilistic, a_sub_folder, 'MC-averages')
            # now list the files in the MC average folder
            files_in_MC_average = list([file for file in os.listdir(
                path_to_MC_averages_folder) if not file.startswith('.')])
            # sort them in the right order
            files_in_MC_average = sorted(files_in_MC_average)
            iteration = 1
            singular_LUT_MC_average_dictionary[a_name] = {}
            for a_file in files_in_MC_average:
                a_key = iteration # number the keys as time steps (1-N)
                a_value = readmap(os.path.join(path_to_MC_averages_folder, a_file)) # get each single time step MC average
                singular_LUT_MC_average_dictionary[a_name][a_key] = a_value # append new key and value to the the singular LUT dict
                iteration += 1
            self.dictionary_of_LUTs_MC_averages_dictionaries.update(singular_LUT_MC_average_dictionary)  # update zieht nur den letzten Eintrag/überschreibt
            count += 1

        # =================================================================== #
        # TODO Melvin: copy to OC or use here
        ## Attention: required method for extraction in dynamic
        # SH for ML model stage 3
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and probabilistic_output_options_dictionary['yield_maps'] == True:
            # import the yield maps MC averages of the user-defined selected LUTs
            self.dictionary_of_agricultural_yields_MCaverages = {} # nested dictionary

            # LUT02_cropland-annual_crop_yields
            # LUT03_pasture_livestock_yields
            # LUT04_agroforestry_crop_yields

            singular_yield_dictionary = {}

            sub_folders_yields = list([file for file in os.listdir(
                Filepaths.folder_dynamic_yield_maps_probabilistic ) if not file.startswith('.')])  # imports the sub-folders

            for a_sub_folder in sub_folders_yields:
                if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield'] and a_sub_folder == 'LUT02_cropland-annual_crop_yields':
                    a_name = 'LUT02_cropland_annual_crop_yields'
                elif 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield'] and a_sub_folder == 'LUT03_pasture_livestock_yields':
                    a_name = 'LUT03_pasture_livestock_yields'
                elif 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield'] and a_sub_folder == 'LUT04_agroforestry_crop_yields':
                    a_name = 'LUT04_agroforestry_crop_yields'

                # built the path to the MC averages folder
                path_to_MC_averages_folder = os.path.join(Filepaths.folder_dynamic_yield_maps_probabilistic,
                                                                  a_sub_folder, 'MC-averages')
                # now list the files in the MC average folder
                files_in_MC_average = list([file for file in os.listdir(
                            path_to_MC_averages_folder) if not file.startswith('.')])
                # sort them in the right order
                files_in_MC_average = sorted(files_in_MC_average)
                iteration = 1
                singular_yield_dictionary[a_name] = {}
                for a_file in files_in_MC_average:
                    a_key = iteration  # number the keys as time steps (1-N)
                    a_value = readmap(
                        os.path.join(path_to_MC_averages_folder, a_file))  # get each single time step MC average
                    singular_yield_dictionary[a_name][a_key] = a_value  # append new key and value to the the singular LUT dict
                    iteration += 1
                self.dictionary_of_agricultural_yields_MCaverages.update(
                            singular_yield_dictionary)


        # =================================================================== #

        if probabilistic_output_options_dictionary['degradation_regeneration_maps'] == True:
            # import the singular forest degradation and regeneration categories
            self.dictionary_of_degradation_and_regeneration_dictionaries = {} # nested dictionary

            # degradation low = 1
            # degradation moderate = 2
            # degradation severe = 3
            # degradation absolute = 4

            # regeneration low = 5
            # regeneration medium = 6
            # regeneration high = 7
            # regeneration full = 8

            singular_degradation_or_regeneration_dictionary = {}  # result 8 dictionaries numbered 1 to 8 with 1-N time steps as keys and 1-N time steps files as values

            sub_folders_degradation_regeneration = list([file for file in os.listdir(
                Filepaths.folder_degradation_regeneration) if not file.startswith('.')]) # imports the sub-folders

            for a_sub_folder in sub_folders_degradation_regeneration:
                if a_sub_folder == 'degradation_low':
                    a_name = 1
                elif a_sub_folder == 'degradation_moderate':
                    a_name = 2
                elif a_sub_folder == 'degradation_severe':
                    a_name = 3
                elif a_sub_folder == 'degradation_absolute':
                    a_name = 4
                elif a_sub_folder == 'regeneration_low':
                    a_name = 5
                elif a_sub_folder == 'regeneration_medium':
                    a_name = 6
                elif a_sub_folder == 'regeneration_high':
                    a_name = 7
                elif a_sub_folder == 'regeneration_full':
                    a_name = 8
                # built the path to the MC averages folder
                path_to_MC_averages_folder = os.path.join(Filepaths.folder_degradation_regeneration,
                                                          a_sub_folder, 'MC-averages')
                # now list the files in the MC average folder
                files_in_MC_average = list([file for file in os.listdir(
                    path_to_MC_averages_folder) if not file.startswith('.')])
                # sort them in the right order
                files_in_MC_average = sorted(files_in_MC_average)
                iteration = 1
                singular_degradation_or_regeneration_dictionary[a_name] = {}
                for a_file in files_in_MC_average:
                    a_key = iteration  # number the keys as time steps (1-N)
                    a_value = readmap(
                        os.path.join(path_to_MC_averages_folder, a_file))  # get each single time step MC average
                    singular_degradation_or_regeneration_dictionary[a_name][
                        a_key] = a_value  # append new key and value to the the singular LUT dict
                    iteration += 1
                self.dictionary_of_degradation_and_regeneration_dictionaries.update(
                    singular_degradation_or_regeneration_dictionary)

        # =================================================================== #

        if probabilistic_output_options_dictionary['conflict_maps'] == True:
            # Forest Land Use Conflict in restricted areas
            self.dictionary_of_forest_land_use_conflict_files = {}

            path_to_forest_land_use_conflict_MC_average = os.path.join(Filepaths.folder_forest_land_use_conflict, 'MC-averages')

            forest_land_use_conflict_files = list([file for file in os.listdir(
                path_to_forest_land_use_conflict_MC_average) if not file.startswith('.')])
            forest_land_use_conflict_files = sorted(forest_land_use_conflict_files)

            iteration = 1
            for a_file in forest_land_use_conflict_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(os.path.join(path_to_forest_land_use_conflict_MC_average, a_file))  # get each single time step MC average
                self.dictionary_of_forest_land_use_conflict_files[a_key] = a_value # append it to the dictionary
                iteration += 1


            # Land Use Conflict in restricted areas
            self.dictionary_of_land_use_conflict_files = {}

            path_to_land_use_conflict_MC_average = os.path.join(Filepaths.folder_forest_land_use_conflict,'MC-averages')

            land_use_conflict_files = list([file for file in os.listdir(
                path_to_land_use_conflict_MC_average) if not file.startswith('.')])
            land_use_conflict_files = sorted(land_use_conflict_files)

            iteration = 1
            for a_file in land_use_conflict_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(os.path.join(path_to_land_use_conflict_MC_average, a_file))  # get each single time step MC average
                self.dictionary_of_land_use_conflict_files[a_key] = a_value  # append it to the dictionary
                iteration += 1

        # =================================================================== #

        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            # net forest
            self.dictionary_of_net_forest_files = {}

            path_to_net_forest_MC_average = os.path.join(Filepaths.folder_net_forest, 'MC-averages')

            net_forest_files = list([file for file in os.listdir(
                path_to_net_forest_MC_average) if not file.startswith('.')])
            net_forest_files = sorted(net_forest_files)

            iteration = 1
            for a_file in net_forest_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(os.path.join(path_to_net_forest_MC_average, a_file))  # get each single time step MC average
                self.dictionary_of_net_forest_files[a_key] = a_value  # append it to the dictionary
                iteration += 1

        # =================================================================== #

        if probabilistic_output_options_dictionary['AGB_map'] == True:
             # AGB
            self.dictionary_of_AGB_files = {}

            path_to_AGB_MC_average = os.path.join(Filepaths.folder_AGB, 'MC-averages')

            AGB_files = list([file for file in os.listdir(
                path_to_AGB_MC_average) if not file.startswith('.')])
            AGB_files = sorted(AGB_files)

            iteration = 1
            for a_file in AGB_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(
                        os.path.join(path_to_AGB_MC_average, a_file))  # get each single time step MC average
                self.dictionary_of_AGB_files[a_key] = a_value  # append it to the dictionary
                iteration += 1

        # =================================================================== #

        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            self.initial_AGB_input_map = readmap(Filepaths.file_initial_AGB_input)
        elif Parameters.get_model_scenario() == 'no_conservation':
            self.initial_AGB_input_map = readmap(Filepaths.file_initial_AGB_simulated_for_worst_case_scenario_input)
        # =================================================================== #

        if probabilistic_output_options_dictionary['succession_age_map'] == True:
             # AGB
            self.dictionary_of_succession_age_files = {}

            path_to_succession_age_MC_average = os.path.join(Filepaths.folder_succession_age, 'MC-averages')

            sa_files = list([file for file in os.listdir(
                path_to_succession_age_MC_average) if not file.startswith('.')])
            sa_files = sorted(sa_files)

            iteration = 1
            for a_file in sa_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(
                        os.path.join(path_to_succession_age_MC_average, a_file))  # get each single time step MC average
                self.dictionary_of_succession_age_files[a_key] = a_value  # append it to the dictionary
                iteration += 1

        # =================================================================== #

        # anthropogenic impact buffer (deterministic)
        self.dictionary_of_anthropogenic_impact_buffer_files = {}

        path_to_anthropogenic_impact_buffer_files = os.path.join(Filepaths.folder_dynamic_anthropogenic_impact_buffer_deterministic)

        anthropogenic_impact_buffer_files = list([file for file in os.listdir(
            path_to_anthropogenic_impact_buffer_files) if not file.startswith('.')])
        anthropogenic_impact_buffer_files = sorted(anthropogenic_impact_buffer_files)

        iteration = 1
        for a_file in anthropogenic_impact_buffer_files:
            a_key = iteration  # number the keys as time steps (1-N)
            a_value = readmap(os.path.join(path_to_anthropogenic_impact_buffer_files, a_file))  # get each single time step MC average
            self.dictionary_of_anthropogenic_impact_buffer_files[a_key] = a_value  # append it to the dictionary
            iteration += 1

        # =================================================================== #

        # settlements (deterministic)
        self.dictionary_of_settlements_files = {}

        path_to_settlement_files = os.path.join(
            Filepaths.folder_dynamic_settlements_deterministic)

        settlements_files = list([file for file in os.listdir(
            path_to_settlement_files) if not file.startswith('.')])
        settlements_files = sorted(settlements_files)

        iteration = 1
        for a_file in settlements_files:
            a_key = iteration  # number the keys as time steps (1-N)
            a_value = readmap(
                os.path.join(path_to_settlement_files, a_file))  # get each single time step MC average
            self.dictionary_of_settlements_files[a_key] = a_value  # append it to the dictionary
            iteration += 1

        # =================================================================== #

        if Parameters.get_order_of_forest_deforestation_and_conversion() is True:
            if probabilistic_output_options_dictionary['deforested_net_forest_map'] == True:
                # deforested for demand in input biomass before conversion
                self.dictionary_of_deforested_for_input_biomass_before_conversion_files = {}

                path_to_deforested_files_MC_averages = os.path.join(
                    Filepaths.folder_deforested_before_conversion, 'MC-averages')

                deforested_files = list([file for file in os.listdir(
                    path_to_deforested_files_MC_averages) if not file.startswith('.')])
                deforested_files = sorted(deforested_files)

                iteration = 1
                for a_file in deforested_files:
                    a_key = iteration  # number the keys as time steps (1-N)
                    a_value = readmap(
                        os.path.join(path_to_deforested_files_MC_averages, a_file))  # get each single time step MC average
                    self.dictionary_of_deforested_for_input_biomass_before_conversion_files[a_key] = a_value  # append it to the dictionary
                    iteration += 1

        # =================================================================== #

        # for AGB/Carbon import the climate derived datasets necessary

        # climate period inputs dictionary
        self.climate_period_inputs_dictionary = {
            # projections in time and/or space for:

            # potential forest distribution
            'file_projection_potential_natural_vegetation_distribution_2018_2020_input': readmap(
                Filepaths.file_projection_potential_natural_vegetation_distribution_2018_2020_input),
            'file_projection_potential_natural_vegetation_distribution_2021_2040_input': readmap(
                Filepaths.file_projection_potential_natural_vegetation_distribution_2021_2040_input),
            'file_projection_potential_natural_vegetation_distribution_2041_2060_input': readmap(
                Filepaths.file_projection_potential_natural_vegetation_distribution_2041_2060_input),
            'file_projection_potential_natural_vegetation_distribution_2061_2080_input': readmap(
                Filepaths.file_projection_potential_natural_vegetation_distribution_2061_2080_input),
            'file_projection_potential_natural_vegetation_distribution_2081_2100_input': readmap(
                Filepaths.file_projection_potential_natural_vegetation_distribution_2081_2100_input),

            # potential maximum AGB
            'file_projection_potential_maximum_undisturbed_AGB_2018_2020_input': readmap(
                Filepaths.file_projection_potential_maximum_undisturbed_AGB_2018_2020_input),
            'file_projection_potential_maximum_undisturbed_AGB_2021_2040_input': readmap(
                Filepaths.file_projection_potential_maximum_undisturbed_AGB_2021_2040_input),
            'file_projection_potential_maximum_undisturbed_AGB_2041_2060_input': readmap(
                Filepaths.file_projection_potential_maximum_undisturbed_AGB_2041_2060_input),
            'file_projection_potential_maximum_undisturbed_AGB_2061_2080_input': readmap(
                Filepaths.file_projection_potential_maximum_undisturbed_AGB_2061_2080_input),
            'file_projection_potential_maximum_undisturbed_AGB_2081_2100_input': readmap(
                Filepaths.file_projection_potential_maximum_undisturbed_AGB_2081_2100_input)
        }
                    # =================================================================== #

        # dictionary of top crops yields
        self.dictionary_of_top_crops_yields = Parameters.get_regional_top_crops_yields_in_Mg_per_ha()

        # =================================================================== #

        # get LaForeT tiles (the maps must be numbered in the order of the Parameters tiles_dictionaries)
        self.dictionary_of_tiles_identifier = Parameters.get_tiles_identifier()
        self.dictionary_of_tiles_maps = {}

        for an_entry in self.dictionary_of_tiles_identifier: # iterate through the default Parameters.py dictionary
            if an_entry == 1 and os.path.exists(Filepaths.file_static_tile_1_input) == True: # check if the physical input map exists
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(Filepaths.file_static_tile_1_input) # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = list(self.dictionary_of_tiles_identifier[an_entry].keys())[0] # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = list(self.dictionary_of_tiles_identifier[an_entry].values())[0] # get the name
            elif an_entry == 1 and os.path.exists(Filepaths.file_static_tile_1_input) == False:# if no input map exists declare the dictionary for the tile as empty
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 2 and os.path.exists(Filepaths.file_static_tile_2_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_2_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 2 and os.path.exists(Filepaths.file_static_tile_2_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 3 and os.path.exists(Filepaths.file_static_tile_3_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_3_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 3 and os.path.exists(Filepaths.file_static_tile_3_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 4 and os.path.exists(Filepaths.file_static_tile_4_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_4_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 4 and os.path.exists(Filepaths.file_static_tile_4_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 5 and os.path.exists(Filepaths.file_static_tile_5_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_5_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 5 and os.path.exists(Filepaths.file_static_tile_5_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 6 and os.path.exists(Filepaths.file_static_tile_6_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_6_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 6 and os.path.exists(Filepaths.file_static_tile_6_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 7 and os.path.exists(Filepaths.file_static_tile_7_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_7_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 7 and os.path.exists(Filepaths.file_static_tile_7_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            if an_entry == 8 and os.path.exists(Filepaths.file_static_tile_8_input) == True:
                self.dictionary_of_tiles_maps[an_entry] = {}
                self.dictionary_of_tiles_maps[an_entry]['map'] = readmap(
                    Filepaths.file_static_tile_8_input)  # get the map
                self.dictionary_of_tiles_maps[an_entry]['identifier'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].keys())[0]  # get the identifier
                self.dictionary_of_tiles_maps[an_entry]['name'] = \
                list(self.dictionary_of_tiles_identifier[an_entry].values())[0]  # get the name
            elif an_entry == 8 and os.path.exists(Filepaths.file_static_tile_8_input) == False:
                self.dictionary_of_tiles_maps[an_entry] = None

            an_entry += 1



        # =================================================================== #
        print('\nMC averages and accompanying maps from LPB-basic imported')
        # =================================================================== #

        # import the CSV data from LPB_log-file for comparison

        # to get the population peak year built a list of the population data, search with max() and return the index position to add to the initial simulation year +1 (zero indexing)
        list_of_population_values_per_year = []


        # order is : key=year, Value = list of: population, settlements, share smallholder population, ha demand LUT01, ha demand LUT02, ha demand LUT03, ha demand LUT04, ha demand LUT05, demand AGB
        self.LPB_basic_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the header
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the population peak data)
                    break
                a_key = row[0]  # the year shall be the key
                row.pop(0)
                a_values_list = row  # all other values in the list except year
                self.LPB_basic_log_file_dictionary.update({a_key: a_values_list})
                population_data = row[0]
                list_of_population_values_per_year.append(int(population_data))
        print('\nCSV data from LPB-basic_log-file imported')

        max_population = builtins.max(list_of_population_values_per_year)

        index_position_of_max_population = list_of_population_values_per_year.index(max_population, 0,
                                                                                    len(list_of_population_values_per_year))  # search in the list for the value between 0 and last entry index position

        self.population_peak_year = Parameters.get_initial_simulation_year() + index_position_of_max_population

        # import data from CSV LPB-basic-LUT01_log-file
        self.LPB_basic_LUT01_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT01_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the header
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the please note data)
                    break
                a_key = row[1]  # the year shall be the key
                row.pop(0) # eliminate time step
                row.pop(0) # eliminate year
                a_values_list = row  # all other values in the list except year and tme step
                self.LPB_basic_LUT01_log_file_dictionary.update({a_key: a_values_list})
        print('\nCSV data from LPB-basic-LUT01_log-file imported')

        # import data from CSV LPB-basic-LUT05_log-file
        self.LPB_basic_LUT05_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT05_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the header
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the please note data)
                    break
                a_key = row[1]  # the year shall be the key
                row.pop(0)  # eliminate time step
                row.pop(0)  # eliminate year
                a_values_list = row  # all other values in the list except year and tme step
                self.LPB_basic_LUT05_log_file_dictionary.update({a_key: a_values_list})
        print('\nCSV data from LPB-basic-LUT05_log-file imported')

        # import data from CSV LPB-basic-abandoned_types_log-file
        self.LPB_basic_abandoned_types_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-abandoned-types_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the header
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the please note data)
                    break
                a_key = row[1]  # the year shall be the key
                row.pop(0)  # eliminate time step
                row.pop(0)  # eliminate year
                a_values_list = row  # all other values in the list except year and tme step
                self.LPB_basic_abandoned_types_log_file_dictionary.update({a_key: a_values_list})
        print('\nCSV data from LPB-basic-abandoned-types_log-file imported')

        # =================================================================== #
        # SH: if simulated with yields, import the area for the selected LUTs (maximum over all samples) from the CSV
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            # import data from the log file LPB-basic-agricultural-types_log-file.csv
            self.LPB_basic_agricultural_types_log_file_dictionary = {}

            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-agricultural-types_log-file.csv'),
                      'r') as csv_file_to_read:
                log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
                next(log_file_reader, None)  # skip the title
                next(log_file_reader, None)  # skip the header
                for row in log_file_reader:  # reads each row as a list
                    if row == []:  # break when you hit an empty row (not to read in the please note data)
                        break
                    a_key = row[1]  # the year shall be the key
                    row.pop(0)  # eliminate time step
                    row.pop(0)  # eliminate year
                    a_values_list = row  # all other values in the list except year and tme step
                    self.LPB_basic_agricultural_types_log_file_dictionary.update({a_key: a_values_list})
            print('\nCSV data from LPB-basic-agricultural-types_log-file.csv imported')

        # =================================================================== #

        # import data from CSV LPB-basic-LUT17_log-file
        self.LPB_basic_LUT17_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT17_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the header
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the please note data)
                    break
                a_key = row[1]  # the year shall be the key
                row.pop(0)  # eliminate time step
                row.pop(0)  # eliminate year
                a_values_list = row  # all other values in the list except year and time step
                self.LPB_basic_LUT17_log_file_dictionary.update({a_key: a_values_list})
        print('\nCSV data from LPB-basic-LUT17_log-file imported')

        # =================================================================== #

        # self.peak_demands_year: Active LUTs plus plantation harvested and deforested sites

        # external time series:
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            # Step 1) get the according values from the dictionaries
            LUT01_dictionary = dict(self.LPB_basic_LUT01_log_file_dictionary)
            for a_key, a_value in LUT01_dictionary.items():
                LUT01_dictionary[a_key] = a_value[2] # max value

            LUT02to04_dictionary = dict(self.LPB_basic_agricultural_types_log_file_dictionary) # data is noted in additional log file
            for a_key, a_value in LUT02to04_dictionary.items():
                LUT02to04_dictionary[a_key] = sum(map(int, a_value)) # max values

            LUT05_dictionary = dict(self.LPB_basic_LUT05_log_file_dictionary)
            for a_key, a_value in LUT05_dictionary.items():
                LUT05_dictionary[a_key] = a_value[2] # max values

            LUT18_dictionary = dict(self.LPB_basic_abandoned_types_log_file_dictionary)
            for a_key, a_value in LUT18_dictionary.items():
                LUT18_dictionary[a_key] = a_value[3] # mean LUT18 4th in list

            # add LUT17
            LUT17_dictionary = dict(self.LPB_basic_LUT17_log_file_dictionary)
            for a_key, a_value in LUT17_dictionary.items():
                LUT17_dictionary[a_key] = a_value[1] # mean LUT17 2nd in list

            # Step 2) extract values from all dictionaries per key (year) and add them up to one sum value per year
            LUTs_dictionary_of_dictionaries = [LUT01_dictionary, LUT02to04_dictionary, LUT05_dictionary, LUT18_dictionary, LUT17_dictionary]
            demands_per_LUT_per_timestep_dictionary = {}
            for a_key in LUTs_dictionary_of_dictionaries[0]:
                demands_per_LUT_per_timestep_dictionary[a_key] = [d[a_key] for d in LUTs_dictionary_of_dictionaries]

            sum_of_demands_per_LUT_per_timestep_dictionary = {}
            for a_key, a_value in demands_per_LUT_per_timestep_dictionary.items():
                sum_of_demands_per_LUT_per_timestep_dictionary[a_key] = sum(map(int, a_value))

            # Step 3) get the peak demand year
            peak_demands_year = builtins.max(sum_of_demands_per_LUT_per_timestep_dictionary.items(), key=operator.itemgetter(1))[0]
            self.peak_demands_year = int(peak_demands_year)

        # for all external time series note the self.peak_demands_year in a CSV to be used in RAP
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            # note the data in a CSV file
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-external-time-series_peak-demands-year.csv'), 'w',
                      newline='') as LPB_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_file)
                LPB_file_data = ['peak_demands_year:', self.peak_demands_year]
                writer.writerow(LPB_file_data)
                print('\nNoted self.peak_demands_year ' + str(self.peak_demands_year) + ' in LPB-external-time-series_peak-demands-year.csv')

        # =================================================================== #
        # Model stage 2:
        # get PHCs simulation choice dictionary
        self.PHCs_simulation_choice_dictionary = Parameters.get_potential_habitat_corridors_simulation_choice()

        # =================================================================== #

        # PRE-PRODUCED MAPS AND VALUES
        print('\npre-produced maps and values initialized')

        # slope calculation
        self.dem_map = scalar(self.dem_map)
        self.slope_map = slope(self.dem_map)

        # difficult terrain per land use type
        self.difficult_terrain_slope_restriction_dictionary = Parameters.get_difficult_terrain_slope_restriction_dictionary()
        # in the dictionary the key is the land use type and the minimum value for difficult terrain list index 0
        self.difficult_terrain_LUT01_map = ifthen(
            pcrge(self.slope_map, self.difficult_terrain_slope_restriction_dictionary[1][0]), self.slope_map)
        self.difficult_terrain_LUT02_map = ifthen(
            pcrge(self.slope_map, self.difficult_terrain_slope_restriction_dictionary[2][0]), self.slope_map)
        self.difficult_terrain_LUT03_map = ifthen(
            pcrge(self.slope_map, self.difficult_terrain_slope_restriction_dictionary[3][0]), self.slope_map)
        self.difficult_terrain_LUT04_map = ifthen(
            pcrge(self.slope_map, self.difficult_terrain_slope_restriction_dictionary[4][0]), self.slope_map)
        self.difficult_terrain_LUT05_map = ifthen(
            pcrge(self.slope_map, self.difficult_terrain_slope_restriction_dictionary[5][0]), self.slope_map)

        # prepare the restricted areas map for use
        self.static_restricted_areas_map = cover(boolean(self.static_restricted_areas_map), boolean(self.null_mask_map))

        # get a base map of the null mask and the restricted areas, this is to be combined with the classified probability maps
        # of 7 classes, therefore the class numbers are 8 and 9
        self.region_and_restricted_areas_base_map = ifthenelse(scalar(self.static_restricted_areas_map) == scalar(1),
                                                               scalar(9),  # restricted areas are the second class
                                                               scalar(self.null_mask_map) + scalar(
                                                                   8))  # the basic region the first class

        # determine the 100 % area once as a reference
        print('\ndetermine the hundred percent area as a reference for the simulation output ...')
        one_mask_map = scalar(self.null_mask_map) + 1
        self.hundred_percent_area = int(maptotal(scalar(one_mask_map)))
        print('full landscape area, i.e. 100 % for reference, is', self.hundred_percent_area,
              Parameters.get_pixel_size())

        print('\npre-produced maps and values done')


        # =================================================================== #

        # open the new CSV LPB-mplc_log-file
        command = "python Create_LPB_mplc_log_file.py"
        subprocess.run(command.split(), check=True)
        # os.system(command)
        print('\nfiling LPB-mplc_log-file.csv initiated ...')

        # =================================================================== #

        print('\nrunning initial done')

    def _prepare_tidy_output(self):
        output_folder = Filepaths.folder_LPB_tidy_data

        # define output files and column headers
        output_files_definitions = {
            'LPB_area_demands_' + str(Parameters.get_model_scenario()): ['LUT_code','demand'],
            'LPB_AGB_demand_' + str(Parameters.get_model_scenario()):['demand'],
            'LPB_anthropogenic_features_' + str(Parameters.get_model_scenario()): ['type', 'pixels'],
            'LPB_anthropogenic_impact_buffer_' + str(Parameters.get_model_scenario()): ['pixels', 'percentage'],
            'LPB_land_use_mplc_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels', 'percentage'],
            'LPB_land_use_mplc_difficult_terrain_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels', 'percentage'],
            'LPB_land_use_mplc_restricted_areas_accumulated_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels','percentage'],
            'LPB_land_use_mplc_restricted_areas_new_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'LPB_land_use_mplc_restricted_areas_new_on_former_forest_pixels_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'LPB_land_use_mplc_restricted_areas_remaining_forest_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'LPB_land_use_mplc_allocated_locally_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels', 'percentage'],
            'LPB_land_use_mplc_allocated_regionally_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels', 'percentage'],
            'LPB_land_use_mplc_unallocated_' + str(Parameters.get_model_scenario()): ['LUT_code', 'unit', 'area'],
            'LPB_possibly_hidden_deforestation_' + str(Parameters.get_model_scenario()): ['pixels','percentage'],
            'LPB_forest_conversion_' + str(Parameters.get_model_scenario()): ['Aspect', 'pixels', 'percentage'],
            'LPB_forest_conversion_by_type_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'LPB_forest_deforestation_' + str(Parameters.get_model_scenario()): ['Aspect', 'pixels'],
            'LPB_forest_corrective_allocation_' + str(Parameters.get_model_scenario()): ['Aspect', 'pixels'],
            'LPB_landscape_modelling_probabilities_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_land_use_in_restricted_areas_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage', 'specification'],
            'LPB_forest_net_gross_disturbed_undisturbed_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_forest_impacted_by_anthropogenic_features_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_forest_remaining_without_anthropogenic_impact_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_forest_degradation_regeneration_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_forest_types_AGB_Carbon_' + str(Parameters.get_model_scenario()): ['type', 'AGB', 'Carbon'],
            'LPB_forest_100years_without_anthropogenic_impact_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_forest_habitat_' + str(Parameters.get_model_scenario()): ['class', 'pixels', 'percentage'],
            'LPB_yields_' + str(Parameters.get_model_scenario()): ['crop', 'source_LUT', 'pixels', 'yield_minimum', 'yield_mean', 'yield_maximum'],
        }

        if Parameters.get_umbrella_species_ecosystem_fragmentation_analysis_mplc_RAP_analysis_choice() == True:
            fragmentation_dict = {
                'LPB_fragmentation_' + str(Parameters.get_model_scenario()): ['Aspect','value']
            }
            output_files_definitions.update(fragmentation_dict)

        if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True:
            Omniscape_normalized_dict = {
                'LPB_Omniscape_transformed_normalized_pixels_' + str(Parameters.get_model_scenario()): ['Aspect','value']
            }
            output_files_definitions.update(Omniscape_normalized_dict)

        for file_name, header_columns in output_files_definitions.items():
            header_columns.insert(0, 'time_step')

            with open((os.path.join(output_folder, file_name + '.csv')), 'w', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_file_writer.writerow(header_columns)

        # export lut lookup tables
        LUTs_dictionary = {
            'LUT01': Parameters.LUT01,
            'LUT02': Parameters.LUT02,
            'LUT03': Parameters.LUT03,
            'LUT04': Parameters.LUT04,
            'LUT05': Parameters.LUT05,
            'LUT06': Parameters.LUT06,
            'LUT07': Parameters.LUT07,
            'LUT08': Parameters.LUT08,
            'LUT09': Parameters.LUT09,
            'LUT10': Parameters.LUT10,
            'LUT11': Parameters.LUT11,
            'LUT12': Parameters.LUT12,
            'LUT13': Parameters.LUT13,
            'LUT14': Parameters.LUT14,
            'LUT15': Parameters.LUT15,
            'LUT16': Parameters.LUT16,
            'LUT17': Parameters.LUT17,
            'LUT18': Parameters.LUT18,
            'LUT19': Parameters.LUT19
        }

        with open((os.path.join(output_folder, 'mplc_LUTs_lookup_table.csv')), 'w', newline='') as csv_file:
            csv_file_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for key, value in LUTs_dictionary.items():
                csv_file_writer.writerow([key, value])

        return output_folder, output_files_definitions



    def dynamic(self):
        # management variables
        self.time_step = self.currentTimeStep()
        if self.time_step == 1:
            self.year = Parameters.get_initial_simulation_year()
        else:
            self.year += 1

        print('\n>>> running dynamic for time step', self.time_step, '...')

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

        # call the methods in this order:
        if self.time_step == 1:
            self.preset_variables_in_case_of_decreased_analysis()
        self.make_LPB_basic_log_file_data_for_the_time_step_accessible()
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            self.make_LPB_basic_agricultural_types_log_file_data_for_the_time_step_accessible()
        self.make_LPB_basic_LUT01_log_file_data_for_the_time_step_accessible()
        self.make_LPB_basic_LUT05_log_file_data_for_the_time_step_accessible()
        self.make_LPB_basic_abandoned_types_log_file_data_for_the_time_step_accessible()
        self.make_LPB_basic_LUT17_log_file_data_for_the_time_step_accessible()
        self.make_climate_period_data_for_the_time_step_accessible()
        self.calculate_most_probable_landscape_configuration()
        self.create_tiles_subsets()
        self.calculate_anthropogenic_features()
        if Parameters.get_order_of_forest_deforestation_and_conversion() is True:
            if probabilistic_output_options_dictionary['deforested_net_forest_map'] == True:
                self.calculate_hidden_deforestation_for_input_biomass()
            else:
                self.maximum_deforested_for_input_biomass_area = 'analysis disabled'
                self.maximum_deforested_for_input_biomass_percentage_of_landscape = 'analysis disabled'
        else:
            self.maximum_deforested_for_input_biomass_area = 'deforestation = LUT17'
            self.maximum_deforested_for_input_biomass_percentage_of_landscape = 'deforestation = LUT17'
        self.construct_user_defined_gross_forest()
        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            self.calculate_net_forest_most_probable_landscape_configuration()
        self.construct_deforestation_and_forest_conversion_maps()
        self.construct_forest_disturbed_and_undisturbed_probability_maps_for_the_singular_LUTs()
        if probabilistic_output_options_dictionary['conflict_maps'] == True:
            self.construct_forest_land_use_and_land_use_conflict_maps()
        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            self.derive_mplc_disturbed_and_undisturbed_net_and_gross_forest()
            self.derive_mplc_gross_and_net_forest_impacted_by_anthropogenic_impact_buffer()
            self.derive_mplc_nominal_undisturbed_forest_habitat()
        self.derive_local_and_regional_land_use_amounts()
        if probabilistic_output_options_dictionary['degradation_regeneration_maps'] == True:
            self.derive_forest_degradation_and_regeneration()
        if probabilistic_output_options_dictionary['AGB_map'] == True:
            self.derive_AGB_and_Carbon()
        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            if probabilistic_output_options_dictionary['succession_age_map'] == True:
                self.derive_remaining_forest_without_direct_anthropogenic_impact_for_100_years()
            self.derive_remaining_forest_without_direct_anthropogenic_impact_for_the_time_step()
        self.derive_user_defined_succession_to_undisturbed_forest_for_the_time_step()
        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            self.calculate_gross_minus_net_forest()
        self.calculate_singular_AGB_demands_for_the_time_step()
        self.calculate_top_crops_yields_for_the_time_step()
        # TODO Melvin: this method extracts your yield MC averages per time step:
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and probabilistic_output_options_dictionary['yield_maps'] == True:
            self.calculate_based_on_agricultural_yields()
        if habitat_analysis_dictionary['do_habitat_analysis'] == True:
            self.calculate_umbrella_species_altitude_habitat_environment_map()
            if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True or PHC_simulation_dictionary['simulate_PHCs'] == True:
                self.calculate_umbrella_species_habitat_analysis_inputs()
            if Parameters.get_umbrella_species_ecosystem_fragmentation_analysis_mplc_RAP_analysis_choice() == True:
                self.calculate_umbrella_species_ecosystem_fragmentation()
            if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True:
                if habitat_connectivity_simulation_dictionary['simulation_in'] == 'mplc' or habitat_connectivity_simulation_dictionary['simulation_in'] == 'mplc+RAP':
                    if self.year in habitat_analysis_simulation_years_list:
                        self.calculate_umbrella_species_habitat_connectivity()
            if PHC_simulation_dictionary['simulate_PHCs'] == True:
                if PHC_simulation_dictionary['simulation_in'] == 'mplc' or PHC_simulation_dictionary['simulation_in'] == 'mplc+RAP':
                    if self.year in habitat_analysis_simulation_years_list:
                        self.calculate_umbrella_species_PHCs()
            if Parameters.get_habitat_analysis_averaging_choice() == True and (self.year == Parameters.get_last_simulation_year()):
                self.calculate_umbrella_species_averaged_time_frames()
        self.save_data_last_time_step_for_comparison()
        self.export_data_to_LPB_mplc_log_file()
        self.export_data_to_tidy_data_folder()

        print('\nrunning dynamic for time step', self.time_step, 'done')

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #



    def preset_variables_in_case_of_decreased_analysis(self):
        """In case decreased output options are chosen in Parameters.py the variables are set to a dummy value:"""

        self.population = 'analysis disabled'
        # anthropogenic features
        self.cities = 'analysis disabled'
        self.settlements = 'analysis disabled'
        self.streets = 'analysis disabled'
        self.built_up_additionally = 'analysis disabled'
        # anthropogenic impact buffer 1 total area
        self.anthropogenic_impact_buffer_area = 'analysis disabled'
        self.percentage_of_landscape_anthropogenic_impact_buffer = 'analysis disabled'

        self.demand_LUT01 = 'analysis disabled'
        self.allocated_pixels_LUT01 = 'analysis disabled'
        self.percentage_of_landscape_LUT01 = 'analysis disabled'
        self.allocated_pixels_in_difficult_terrain_LUT01_area = 'analysis disabled'
        self.percentage_of_landscape_difficult_terrain_LUT01 = 'analysis disabled'
        self.LUT01_mplc_in_restricted_areas_area = 'analysis disabled'
        self.percentage_of_landscape_LUT01_in_restricted_areas = 'analysis disabled'
        self.LUT01_mplc_new_in_restricted_areas_area = 'analysis disabled'
        self.LUT01_mplc_new_on_former_forest_pixel_area = 'analysis disabled'
        self.settlements_local_LUT01_area = 'analysis disabled'
        self.percentage_of_landscape_settlements_local_LUT01 = 'analysis disabled'
        self.regional_excess_LUT01 = 'analysis disabled'
        self.percentage_of_landscape_regional_excess_LUT01 = 'analysis disabled'
        self.unallocated_pixels_LUT01 = 'analysis disabled'
        # LUT02
        self.demand_LUT02 = 'analysis disabled'
        self.allocated_pixels_LUT02 = 'analysis disabled'
        self.percentage_of_landscape_LUT02 = 'analysis disabled'
        self.allocated_pixels_in_difficult_terrain_LUT02_area = 'analysis disabled'
        self.percentage_of_landscape_difficult_terrain_LUT02 = 'analysis disabled'
        self.LUT02_mplc_in_restricted_areas_area = 'analysis disabled'
        self.percentage_of_landscape_LUT02_in_restricted_areas = 'analysis disabled'
        self.LUT02_mplc_new_in_restricted_areas_area = 'analysis disabled'
        self.LUT02_mplc_new_on_former_forest_pixel_area = 'analysis disabled'
        self.settlements_local_LUT02_area = 'analysis disabled'
        self.percentage_of_landscape_settlements_local_LUT02 = 'analysis disabled'
        self.regional_excess_LUT02 = 'analysis disabled'
        self.percentage_of_landscape_regional_excess_LUT02 = 'analysis disabled'
        self.unallocated_pixels_LUT02 = 'analysis disabled'
        # LUT03
        self.demand_LUT03 = 'analysis disabled'
        self.allocated_pixels_LUT03 = 'analysis disabled'
        self.percentage_of_landscape_LUT03 = 'analysis disabled'
        self.allocated_pixels_in_difficult_terrain_LUT03_area = 'analysis disabled'
        self.percentage_of_landscape_difficult_terrain_LUT03 = 'analysis disabled'
        self.LUT03_mplc_in_restricted_areas_area = 'analysis disabled'
        self.percentage_of_landscape_LUT03_in_restricted_areas = 'analysis disabled'
        self.LUT03_mplc_new_in_restricted_areas_area = 'analysis disabled'
        self.LUT03_mplc_new_on_former_forest_pixel_area = 'analysis disabled'
        self.settlements_local_LUT03_area = 'analysis disabled'
        self.percentage_of_landscape_settlements_local_LUT03 = 'analysis disabled'
        self.regional_excess_LUT03 = 'analysis disabled'
        self.percentage_of_landscape_regional_excess_LUT03 = 'analysis disabled'
        self.unallocated_pixels_LUT03 = 'analysis disabled'
        # LUT04
        self.demand_LUT04 = 'analysis disabled'
        self.allocated_pixels_LUT04 = 'analysis disabled'
        self.percentage_of_landscape_LUT04 = 'analysis disabled'
        self.allocated_pixels_in_difficult_terrain_LUT04_area = 'analysis disabled'
        self.percentage_of_landscape_difficult_terrain_LUT04 = 'analysis disabled'
        self.LUT04_mplc_in_restricted_areas_area = 'analysis disabled'
        self.percentage_of_landscape_LUT04_in_restricted_areas = 'analysis disabled'
        self.LUT04_mplc_new_in_restricted_areas_area = 'analysis disabled'
        self.LUT04_mplc_new_on_former_forest_pixel_area = 'analysis disabled'
        self.settlements_local_LUT04_area = 'analysis disabled'
        self.percentage_of_landscape_settlements_local_LUT04 = 'analysis disabled'
        self.regional_excess_LUT04 = 'analysis disabled'
        self.percentage_of_landscape_regional_excess_LUT04 = 'analysis disabled'
        self.unallocated_pixels_LUT04 = 'analysis disabled'
        # LUT05
        self.demand_LUT05 = 'analysis disabled'
        self.allocated_pixels_LUT05 = 'analysis disabled'
        self.percentage_of_landscape_LUT05 = 'analysis disabled'
        self.allocated_pixels_in_difficult_terrain_LUT05_area = 'analysis disabled'
        self.percentage_of_landscape_difficult_terrain_LUT05 = 'analysis disabled'
        self.LUT05_mplc_in_restricted_areas_area = 'analysis disabled'
        self.percentage_of_landscape_LUT05_in_restricted_areas = 'analysis disabled'
        self.LUT05_mplc_new_in_restricted_areas_area = 'analysis disabled'
        self.LUT05_mplc_new_on_former_forest_pixel_area = 'analysis disabled'
        self.settlements_local_LUT05_area = 'analysis disabled'
        self.percentage_of_landscape_settlements_local_LUT05 = 'analysis disabled'
        self.regional_excess_LUT05 = 'analysis disabled'
        self.percentage_of_landscape_regional_excess_LUT05 = 'analysis disabled'
        self.unallocated_pixels_LUT05 = 'analysis disabled'
        # LUT06
        self.allocated_pixels_LUT06 = 'analysis disabled'
        self.percentage_of_landscape_LUT06 = 'analysis disabled'
        # LUT07
        self.allocated_pixels_LUT07 = 'analysis disabled'
        self.percentage_of_landscape_LUT07 = 'analysis disabled'
        # LUT08
        self.allocated_pixels_LUT08 = 'analysis disabled'
        self.percentage_of_landscape_LUT08 = 'analysis disabled'
        # LUT09
        self.allocated_pixels_LUT09 = 'analysis disabled'
        self.percentage_of_landscape_LUT09 = 'analysis disabled'
        # LUT10
        self.allocated_pixels_LUT10 = 'analysis disabled'
        self.percentage_of_landscape_LUT10 = 'analysis disabled'
        # LUT11
        self.allocated_pixels_LUT11 = 'analysis disabled'
        self.percentage_of_landscape_LUT11 = 'analysis disabled'
        # LUT12
        self.allocated_pixels_LUT12 = 'analysis disabled'
        self.percentage_of_landscape_LUT12 = 'analysis disabled'
        # LUT13
        self.allocated_pixels_LUT13 = 'analysis disabled'
        self.percentage_of_landscape_LUT13 = 'analysis disabled'
        # LUT14
        self.allocated_pixels_LUT14 = 'analysis disabled'
        self.percentage_of_landscape_LUT14 = 'analysis disabled'
        # LUT15
        self.allocated_pixels_LUT15 = 'analysis disabled'
        self.percentage_of_landscape_LUT15 = 'analysis disabled'
        # LUT16
        self.allocated_pixels_LUT16 = 'analysis disabled'
        self.percentage_of_landscape_LUT16 = 'analysis disabled'
        # LUT17
        self.demand_AGB = 'analysis disabled'
        self.demand_LUT17_minimum = 'analysis disabled'
        self.demand_LUT17_mean = 'analysis disabled'
        self.demand_LUT17_maximum = 'analysis disabled'
        self.allocated_pixels_LUT17 = 'analysis disabled'
        self.percentage_of_landscape_LUT17 = 'analysis disabled'
        # LUT18
        self.allocated_pixels_LUT18 = 'analysis disabled'
        self.percentage_of_landscape_LUT18 = 'analysis disabled'
        # LUT19
        self.allocated_pixels_LUT19 = 'analysis disabled'
        self.percentage_of_landscape_LUT19 = 'analysis disabled'
        # AGB Mg harvested

        # HIDDEN DEFORESTATION
        self.maximum_deforested_for_input_biomass_area = 'analysis disabled'
        self.maximum_deforested_for_input_biomass_percentage_of_landscape = 'analysis disabled'

        # CONVERTED FOREST (new land use type)
        self.converted_forest_area = 'analysis disabled'
        self.converted_forest_area_percentage_of_landscape = 'analysis disabled'

        # LANDSCAPE MODELLING PROBABILITY/UNCERTAINTY
        self.pixels_in_probability_class_1 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_1 = 'analysis disabled'
        self.pixels_in_probability_class_2 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_2 = 'analysis disabled'
        self.pixels_in_probability_class_3 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_3 = 'analysis disabled'
        self.pixels_in_probability_class_4 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_4 = 'analysis disabled'
        self.pixels_in_probability_class_5 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_5 = 'analysis disabled'
        self.pixels_in_probability_class_6 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_6 = 'analysis disabled'
        self.pixels_in_probability_class_7 = 'analysis disabled'
        self.percentage_of_landscape_probability_class_7 = 'analysis disabled'

        # LAND USE IN RESTRICTED AREAS
        self.restricted_areas_area = 'analysis disabled'
        self.restricted_areas_area_percentage_of_landscape = 'analysis disabled'
        self.total_of_land_use_in_restricted_areas_area = 'analysis disabled'
        self.total_of_land_use_in_restricted_areas_area_percentage_of_restricted_area = 'analysis disabled'
        self.total_of_new_land_use_in_restricted_areas_area = 'analysis disabled'
        self.total_of_new_land_use_in_restricted_areas_area_percentage_of_restricted_area = 'analysis disabled'
        self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area = 'analysis disabled'
        self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area_percentage_of_restricted_area = 'analysis disabled'
        self.mplc_disturbed_in_restricted_areas_area = 'analysis disabled'
        self.mplc_disturbed_in_restricted_areas_percentage_of_restricted_area = 'analysis disabled'
        self.mplc_undisturbed_in_restricted_areas_area = 'analysis disabled'
        self.mplc_undisturbed_in_restricted_areas_percentage_of_restricted_area = 'analysis disabled'

        # FOREST net gross disturbed undisturbed
        self.gross_forest_mplc_area = 'analysis disabled'
        self.gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.net_forest_mplc_area = 'analysis disabled'
        self.net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.gross_mplc_disturbed_forest_area = 'analysis disabled'
        self.gross_mplc_disturbed_forest_percentage_of_landscape = 'analysis disabled'
        self.gross_mplc_undisturbed_forest_area = 'analysis disabled'
        self.gross_mplc_undisturbed_forest_percentage_of_landscape = 'analysis disabled'
        self.net_mplc_disturbed_forest_area = 'analysis disabled'
        self.net_mplc_disturbed_forest_percentage_of_landscape = 'analysis disabled'
        self.net_mplc_undisturbed_forest_area = 'analysis disabled'
        self.net_mplc_undisturbed_forest_percentage_of_landscape = 'analysis disabled'
        self.gross_minus_net_forest_disturbed_mplc_area = 'analysis disabled'
        self.gross_minus_net_forest_disturbed_mplc_percentage_of_landscape = 'analysis disabled'
        self.gross_minus_net_forest_undisturbed_mplc_area = 'analysis disabled'
        self.gross_minus_net_forest_undisturbed_mplc_percentage_of_landscape = 'analysis disabled'

        # TRUE FOREST IMPACTED BY ANTHROPOGENIC FEATURES (LUT08)
        self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area = 'analysis disabled'
        self.true_gross_forest_impacted_by_anthropogenic_features_mplc_percentage_of_landscape = 'analysis disabled'
        self.true_net_forest_impacted_by_anthropogenic_features_mplc_area = 'analysis disabled'
        self.true_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = 'analysis disabled'
        self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area = 'analysis disabled'
        self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = 'analysis disabled'

        # FOREST DEGRADATION/REGENERATION
        # 1) degradation
        # degradation low
        self.low_degradation_net_forest_mplc_area = 'analysis disabled'
        self.low_degradation_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.low_degradation_gross_forest_mplc_area = 'analysis disabled'
        self.low_degradation_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.low_degradation_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # degradation moderate
        self.moderate_degradation_net_forest_mplc_area = 'analysis disabled'
        self.moderate_degradation_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.moderate_degradation_gross_forest_mplc_area = 'analysis disabled'
        self.moderate_degradation_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.moderate_degradation_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # degradation severe
        self.severe_degradation_net_forest_mplc_area = 'analysis disabled'
        self.severe_degradation_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.severe_degradation_gross_forest_mplc_area = 'analysis disabled'
        self.severe_degradation_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.severe_degradation_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # degradation absolute (= LUT17 net forest deforested)
        self.absolute_degradation_net_forest_mplc_area = 'analysis disabled'
        self.absolute_degradation_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.absolute_degradation_net_forest_disturbed_mplc_area = 'analysis disabled'
        self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape = 'analysis disabled'
        self.absolute_degradation_net_forest_undisturbed_mplc_area = 'analysis disabled'
        self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape = 'analysis disabled'

        # 2) regeneration
        # regeneration low
        self.low_regeneration_net_forest_mplc_area = 'analysis disabled'
        self.low_regeneration_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.low_regeneration_gross_forest_mplc_area = 'analysis disabled'
        self.low_regeneration_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.low_regeneration_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # regeneration medium
        self.medium_regeneration_net_forest_mplc_area = 'analysis disabled'
        self.medium_regeneration_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.medium_regeneration_gross_forest_mplc_area = 'analysis disabled'
        self.medium_regeneration_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.medium_regeneration_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # regeneration high
        self.high_regeneration_net_forest_mplc_area = 'analysis disabled'
        self.high_regeneration_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.high_regeneration_gross_forest_mplc_area = 'analysis disabled'
        self.high_regeneration_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.high_regeneration_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        # regeneration full (climax stadium, still not all primary forest traits given))
        self.full_regeneration_net_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_gross_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_disturbed_forest_net_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_disturbed_forest_gross_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_disturbed_forest_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_net_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_gross_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_gross_forest_mplc_percentage_of_landscape = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area = 'analysis disabled'
        self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = 'analysis disabled'


        # FOREST AGB in Mg -> tC
        # potential maximum AGB
        self.potential_maximum_undisturbed_forest_AGB_maptotal = 'analysis disabled'
        self.potential_maximum_undisturbed_forest_AGB_Carbon = 'analysis disabled'
        # initial AGB simulation start
        self.initial_AGB_maptotal = 'analysis disabled'
        self.initial_AGB_Carbon = 'analysis disabled'
        self.initial_AGB_percentage_of_potential_maximum_undisturbed_AGB = 'analysis disabled'
        # demand AGB for the time step
        self.demand_timber_AGB = 'analysis disabled'
        self.demand_fuelwood_AGB = 'analysis disabled'
        self.demand_charcoal_AGB = 'analysis disabled'
        self.demand_AGB = 'analysis disabled'
        # final total AGB for the time step
        self.final_AGB_gross_forest_maptotal = 'analysis disabled'
        self.final_AGB_gross_forest_Carbon = 'analysis disabled'
        self.final_AGB_net_forest_maptotal = 'analysis disabled'
        self.final_AGB_net_forest_Carbon = 'analysis disabled'
        self.final_AGB_gross_minus_net_forest_maptotal = 'analysis disabled'
        self.final_AGB_gross_minus_net_forest_Carbon = 'analysis disabled'

        # final AGB agroforestry
        self.final_agroforestry_AGB_maptotal = 'analysis disabled'
        self.final_agroforestry_AGB_Carbon = 'analysis disabled'
        # final AGB plantation
        self.final_plantation_AGB_maptotal = 'analysis disabled'
        self.final_plantation_AGB_Carbon = 'analysis disabled'
        # final AGB disturbed forest
        self.final_disturbed_forest_AGB_gross_forest_maptotal = 'analysis disabled'
        self.final_disturbed_forest_AGB_gross_forest_Carbon = 'analysis disabled'
        self.final_disturbed_forest_AGB_net_forest_maptotal = 'analysis disabled'
        self.final_disturbed_forest_AGB_net_forest_Carbon = 'analysis disabled'
        self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest = 'analysis disabled'
        self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal = 'analysis disabled'
        self.final_disturbed_forest_AGB_gross_minus_net_forest_Carbon = 'analysis disabled'
        self.final_disturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_disturbed_forest = 'analysis disabled'
        # final AGB undisturbed forest
        self.final_undisturbed_forest_AGB_gross_forest_maptotal = 'analysis disabled'
        self.final_undisturbed_forest_AGB_gross_forest_Carbon = 'analysis disabled'
        self.final_undisturbed_forest_AGB_net_forest_maptotal = 'analysis disabled'
        self.final_undisturbed_forest_AGB_net_forest_Carbon = 'analysis disabled'
        self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest = 'analysis disabled'
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal = 'analysis disabled'
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_Carbon = 'analysis disabled'
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_undisturbed_forest = 'analysis disabled'


        # FOREST REMAINING without direct anthropogenic impact
        # gross forest
        # undisturbed
        self.remaining_gross_undisturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_gross_undisturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'
        # disturbed
        self.remaining_gross_disturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_gross_disturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'
        # net forest
        # undisturbed
        self.remaining_net_undisturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_net_undisturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'
        # disturbed
        self.remaining_net_disturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_net_disturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'
        # gross minus net
        # undisturbed
        self.remaining_gross_minus_net_undisturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_gross_minus_net_undisturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'
        # disturbed
        self.remaining_gross_minus_net_disturbed_forest_without_impact_area = 'analysis disabled'
        self.remaining_gross_minus_net_disturbed_forest_without_impact_percentage_of_landscape = 'analysis disabled'

        # FOREST 100 years without anthropogenic impact (potential primary stadium)
        # former disturbed forest
        self.former_disturbed_gross_forest_100years_without_impact_area = 'analysis disabled'
        self.former_disturbed_gross_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'
        self.former_disturbed_net_forest_100years_without_impact_area = 'analysis disabled'
        self.former_disturbed_net_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'
        self.former_disturbed_gross_minus_net_forest_100years_without_impact_area = 'analysis disabled'
        self.former_disturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'
        # initial undisturbed forest
        self.initial_undisturbed_gross_forest_100years_without_impact_area = 'analysis disabled'
        self.initial_undisturbed_gross_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'
        self.initial_undisturbed_net_forest_100years_without_impact_area = 'analysis disabled'
        self.initial_undisturbed_net_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'
        self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area = 'analysis disabled'
        self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = 'analysis disabled'

        # FOREST HABITAT DISTURBED AND UNDISTURBED
        self.mplc_disturbed_forest_fringe_area = 'analysis disabled'
        self.mplc_disturbed_forest_fringe_percentage_of_landscape = 'analysis disabled'
        self.mplc_undisturbed_forest_habitat_area = 'analysis disabled'
        self.mplc_undisturbed_forest_habitat_percentage_of_landscape = 'analysis disabled'

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

    def make_LPB_basic_log_file_data_for_the_time_step_accessible(self):
        # make the LPB-basic CSV data accessible for the time step
        # order is : key=year, values = list of: population[0], settlements[1], share smallholder population[2], ha demand LUT01[3], ha demand LUT02[4], ha demand LUT03[5], ha demand LUT04[6], ha demand LUT05[7|, demand AGB[8]
        a_key = self.year
        if str(a_key) in self.LPB_basic_log_file_dictionary:
            self.population = self.LPB_basic_log_file_dictionary[str(a_key)][0]
            self.settlements = self.LPB_basic_log_file_dictionary[str(a_key)][1]
            self.share_smallholder = self.LPB_basic_log_file_dictionary[str(a_key)][2]
            self.demand_LUT01 = self.LPB_basic_log_file_dictionary[str(a_key)][3]
            self.demand_LUT02 = self.LPB_basic_log_file_dictionary[str(a_key)][4]
            self.demand_LUT03 = self.LPB_basic_log_file_dictionary[str(a_key)][5]
            self.demand_LUT04 = self.LPB_basic_log_file_dictionary[str(a_key)][6]
            self.demand_LUT05 = self.LPB_basic_log_file_dictionary[str(a_key)][7]
            self.demand_AGB = self.LPB_basic_log_file_dictionary[str(a_key)][8]

        # =================================================================== #
    def make_LPB_basic_agricultural_types_log_file_data_for_the_time_step_accessible(self):
        """This method is only used in the yield units approach. It takes the LPB basic maximum area simulation values
        for the selected LUTs which were simulated with yield and provides the values here as demand.
        Note that thereby the variable unallocated demand is de facto disabled."""

        a_key = str(self.year)
        if str(a_key) in self.LPB_basic_agricultural_types_log_file_dictionary:
            self.demand_LUT02 = self.LPB_basic_agricultural_types_log_file_dictionary[a_key][0]
            self.demand_LUT03 = self.LPB_basic_agricultural_types_log_file_dictionary[a_key][1]
            self.demand_LUT04 = self.LPB_basic_agricultural_types_log_file_dictionary[a_key][2]


        # =================================================================== #

    def make_LPB_basic_LUT01_log_file_data_for_the_time_step_accessible(self):

        a_key = str(self.year)
        if a_key in self.LPB_basic_LUT01_log_file_dictionary:
            self.demand_LUT01_minimum = self.LPB_basic_LUT01_log_file_dictionary[a_key][0]
            self.demand_LUT01_mean = self.LPB_basic_LUT01_log_file_dictionary[a_key][1]
            self.demand_LUT01_maximum = self.LPB_basic_LUT01_log_file_dictionary[a_key][2]

        # set the demand to the maximum of all values
        self.demand_LUT01 = self.demand_LUT01_maximum

    # =================================================================== #

    def make_LPB_basic_LUT05_log_file_data_for_the_time_step_accessible(self):

        a_key = str(self.year)
        if a_key in self.LPB_basic_LUT05_log_file_dictionary:
            self.simulated_LUT05_minimum = self.LPB_basic_LUT05_log_file_dictionary[a_key][0]
            self.simulated_LUT05_mean = self.LPB_basic_LUT05_log_file_dictionary[a_key][1]
            self.simulated_LUT05_maximum = self.LPB_basic_LUT05_log_file_dictionary[a_key][2]

    # =================================================================== #

    def make_LPB_basic_abandoned_types_log_file_data_for_the_time_step_accessible(self):

        a_key = str(self.year)
        if a_key in self.LPB_basic_abandoned_types_log_file_dictionary:
            self.simulated_LUT14_mean = int(self.LPB_basic_abandoned_types_log_file_dictionary[a_key][0])
            self.simulated_LUT15_mean = int(self.LPB_basic_abandoned_types_log_file_dictionary[a_key][1])
            self.simulated_LUT16_mean = int(self.LPB_basic_abandoned_types_log_file_dictionary[a_key][2])
            self.simulated_LUT18_mean = int(self.LPB_basic_abandoned_types_log_file_dictionary[a_key][3])

        # NOW SET THE NOTED AND TO BE SIMULATED DEMAND TO THE MAXIMUM VALUE:
        self.demand_LUT01 = self.demand_LUT01_maximum

    # =================================================================== #

    def make_LPB_basic_LUT17_log_file_data_for_the_time_step_accessible(self):

        a_key = str(self.year)
        if a_key in self.LPB_basic_LUT17_log_file_dictionary:
            self.demand_LUT17_minimum = self.LPB_basic_LUT17_log_file_dictionary[a_key][0]
            self.demand_LUT17_mean = self.LPB_basic_LUT17_log_file_dictionary[a_key][1]
            self.demand_LUT17_maximum = self.LPB_basic_LUT17_log_file_dictionary[a_key][2]

        # =================================================================== #


    def make_climate_period_data_for_the_time_step_accessible(self):

        print('reading climate period input data for the time step initiated ...')
        # # Read the according maps for potential forest distribution and AGB for the year within the climate period

        if self.year <= 2020:
            # potential distribution
            input_projection_potential_natural_vegetation_distribution_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_natural_vegetation_distribution_2018_2020_input']
            self.projection_potential_natural_vegetation_distribution_map = cover(
                scalar(input_projection_potential_natural_vegetation_distribution_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2018_2020_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))

        elif self.year >= 2021 and self.year <= 2040:
            # potential distribution
            input_projection_potential_natural_vegetation_distribution_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_natural_vegetation_distribution_2021_2040_input']
            self.projection_potential_natural_vegetation_distribution_map = cover(
                scalar(input_projection_potential_natural_vegetation_distribution_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2021_2040_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))

        elif self.year >= 2041 and self.year <= 2060:
            # potential distribution
            input_projection_potential_natural_vegetation_distribution_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_natural_vegetation_distribution_2041_2060_input']
            self.projection_potential_natural_vegetation_distribution_map = cover(
                scalar(input_projection_potential_natural_vegetation_distribution_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2041_2060_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))

        elif self.year >= 2061 and self.year <= 2080:
            # potential distribution
            input_projection_potential_natural_vegetation_distribution_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_natural_vegetation_distribution_2061_2080_input']
            self.projection_potential_natural_vegetation_distribution_map = cover(
                scalar(input_projection_potential_natural_vegetation_distribution_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2061_2080_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))

        elif self.year >= 2081 and self.year <= 2100:
            # potential distribution
            input_projection_potential_natural_vegetation_distribution_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_natural_vegetation_distribution_2081_2100_input']
            self.projection_potential_natural_vegetation_distribution_map = cover(
                scalar(input_projection_potential_natural_vegetation_distribution_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2081_2100_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))

        print('reading climate period input data for the time step done')

        # =================================================================== #

    def calculate_most_probable_landscape_configuration(self):
        """THE KEY: compare the maps by highest probability per pixel and note the according probability and LUT.A
        if full anthropogenic impact is to be simulated the active land use types plus deforestation are allocated again based on probabilities."""

        print('\ncalculating most probable landscape configuration ...')

        # SH & DK:

        self.most_probable_landscape_configuration_probabilities_map = self.null_mask_map # initialize the map
        self.most_probable_landscape_configuration_map = self.null_mask_map

        if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
            """SH: RAP BASIS - In this method maximum anthropogenic impact is simulated on the LPB-basic probabilities 
            - all demand must be allocated as long as space is available and abandoned areas in regard to the last time step exactly placed."""

            range_of_all_land_use_types = range(1, (Parameters.get_total_number_of_land_use_types() + 1))
            list_of_land_use_type_maps_for_the_time_step = []
            for a_LUT in range_of_all_land_use_types:
                a_LUT_map = self.dictionary_of_LUTs_MC_averages_dictionaries[a_LUT][self.time_step]
                list_of_land_use_type_maps_for_the_time_step.append(a_LUT_map)

            # get the basic probabilities map
            initial_most_probable_landscape_configuration_probabilities_map = ifthenelse(
                (max(*list_of_land_use_type_maps_for_the_time_step) > scalar(0)),
                max(*list_of_land_use_type_maps_for_the_time_step),
                scalar(self.null_mask_map))

            # get the basic nominal map
            initial_most_probable_landscape_configuration_map = nominal(self.null_mask_map)

            for LUT_key, dictionary_of_LUT_probability_maps in self.dictionary_of_LUTs_MC_averages_dictionaries.items():
                LUT_probability_map_per_time_step_i = dictionary_of_LUT_probability_maps[self.time_step]
                temporal_landscape_map = ifthen(
                    LUT_probability_map_per_time_step_i == initial_most_probable_landscape_configuration_probabilities_map,
                    nominal(LUT_key))
                initial_most_probable_landscape_configuration_map = cover(temporal_landscape_map,
                                                                       initial_most_probable_landscape_configuration_map)

            pcraster_conform_map_name = 'ini_mplc'
            time_step = self.time_step  # needed for PCraster conform output
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(initial_most_probable_landscape_configuration_map,
                   os.path.join(Filepaths.folder_LULCC_initial_mplc, output_map_name))
            print('initial_most_probable_landscape_configuration_map created and stored as "ini_mplc" in:',
                  Filepaths.folder_LULCC_initial_mplc)

            # TRACK FOREST CONVERSION
            LUT08_prior_corrective_allocation = self._update_current_area_occupied(8,
                                                                        initial_most_probable_landscape_configuration_map)
            print('Forest_disturbed_prior_corrective_allocation:', LUT08_prior_corrective_allocation)
            LUT09_prior_corrective_allocation = self._update_current_area_occupied(9,
                                                                        initial_most_probable_landscape_configuration_map)
            print('Forest_undisturbed_prior_corrective_allocation:', LUT09_prior_corrective_allocation)
            self.forest_prior_corrective_allocation = LUT08_prior_corrective_allocation + LUT09_prior_corrective_allocation
            print('Forest_total_prior_corrective_allocation:', self.forest_prior_corrective_allocation)

            # now add the demand based maps for the active land use types plus deforestation
            list_of_active_land_use_types = Parameters.get_active_land_use_types_list()
            list_of_active_land_use_types.append(17) # add LUT17 net forest - - deforested

            # since we operate on probabilities, we need a map with cells that are already changed
            immutable_cells_map = scalar(self.null_mask_map)  # initialize the map

            # another map is needed to combine the changes for the probabilities
            corrected_accumulated_probabilities_map = scalar(self.null_mask_map)

            # to place the abandoned areas exactly compare last time step allocated and unallocated area with the demand of this timestep (after timestep 1)
            abandoned_area_agricultural_LUT = 0

            # for that calculation the probabilities_map for the abandoned types is needed
            abandoned_LUT_probabilities_map = self.null_mask_map

            # declare the temporal map prior, since allocation order can change
            temporal_most_probable_landscape_configuration_map = initial_most_probable_landscape_configuration_map

            for a_type in list_of_active_land_use_types:
                # note the biome vegtation type probabilities for final correction of allocation of excess by probabilities
                herbaceous_vegetation_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[6][self.time_step]
                shrubs_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[7][self.time_step]
                disturbed_forest_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[8][self.time_step]
                # get the demand per active land use type
                demand = 0
                if a_type == 1:
                    demand = int(self.demand_LUT01_maximum)
                    # LUT01 stays unchanged after the population peak, since structures still seal the ground
                    if self.year == self.population_peak_year:
                        self.peak_demand = demand
                    if self.year > self.population_peak_year:
                        demand = self.peak_demand
                    # LUT01 has no unallocated pixels unless the landscape is entirely sealed
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    # for LUT01 attach the probabilities map, here just called abandoned to shorten the code:
                    abandoned_LUT_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[1][self.time_step]
                elif a_type == 2:
                    demand = int(self.demand_LUT02)
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    abandoned_area_agricultural_LUT = self.simulated_LUT14_mean
                    abandoned_LUT_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[14][self.time_step]
                elif a_type == 3:
                    demand = int(self.demand_LUT03)
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    abandoned_area_agricultural_LUT = self.simulated_LUT15_mean
                    abandoned_LUT_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[15][self.time_step]
                elif a_type == 4:
                    demand = int(self.demand_LUT04)
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    abandoned_area_agricultural_LUT = self.simulated_LUT16_mean
                    abandoned_LUT_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[16][self.time_step]
                elif a_type == 5:
                    demand = int(self.demand_LUT05)
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    # for LUT05 attach the abanonded value (= LUT18 plantation deforested) and the probabilities map, here just called abandoned to shorten the code:
                    abandoned_area_agricultural_LUT = self.simulated_LUT18_mean
                    abandoned_LUT_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[18][
                        self.time_step]
                elif a_type == 17:
                    demand = int(self.demand_LUT17_mean)
                    temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map
                    # "abandoned type" is disturbed forest 8
                # get the LUT probabilities map instead of suitabilities
                probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[a_type][self.time_step]
                # perform the corrective allocation to maximum impact simulated (demand must be met)
                a_LUT_probabilities_with_maximum_anthropogenic_impact_map,\
                immutable_cells_map,\
                temporal_most_probable_landscape_configuration_map = self._corrective_allocation(temporal_most_probable_landscape_configuration_map,
                                                                                                 a_type,
                                                                                                 demand,
                                                                                                 probabilities_map,
                                                                                                 herbaceous_vegetation_probabilities_map,
                                                                                                 shrubs_probabilities_map,
                                                                                                 disturbed_forest_probabilities_map,
                                                                                                 immutable_cells_map,
                                                                                                 abandoned_area_agricultural_LUT,
                                                                                                 abandoned_LUT_probabilities_map)
                # correct the total probabilities map by correction to the LUT depend probabilities
                corrected_accumulated_probabilities_map += a_LUT_probabilities_with_maximum_anthropogenic_impact_map

            # eliminate the zeros
            pure_corrected_accumulated_probabilities_map = ifthen(scalar(corrected_accumulated_probabilities_map) > scalar(0),
                                                                  scalar(corrected_accumulated_probabilities_map))

            # get the final corrected probabilities map
            final_most_probable_landscape_configuration_probabilities_with_anthropogenic_impact_map = cover(scalar(pure_corrected_accumulated_probabilities_map),
                                                                                                            scalar(initial_most_probable_landscape_configuration_probabilities_map))

            # get the final nominal landscape
            final_most_probable_landscape_configuration_with_anthropogenic_impact_map = temporal_most_probable_landscape_configuration_map

            # TRACK FOREST CONVERSION
            LUT08_post_corrective_allocation = self._update_current_area_occupied(8,
                                                                                   final_most_probable_landscape_configuration_with_anthropogenic_impact_map)
            print('Forest_disturbed_post_corrective_allocation:', LUT08_post_corrective_allocation)
            LUT09_post_corrective_allocation = self._update_current_area_occupied(9,
                                                                                   final_most_probable_landscape_configuration_with_anthropogenic_impact_map)
            print('Forest_undisturbed_post_corrective_allocation:', LUT09_post_corrective_allocation)
            self.forest_post_corrective_allocation = LUT08_post_corrective_allocation + LUT09_post_corrective_allocation
            print('Forest_total_post_corrective_allocation:', self.forest_post_corrective_allocation)

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
            # THE KEY TO LPB-mplc with maximum anthropogenic impact
            # compare the maps by highest probability per pixel and note the according probability,
            # cover the initial map by a map per active LUT based on probability
            # accounting for the complete demand if space is available

            self.most_probable_landscape_configuration_probabilities_map = final_most_probable_landscape_configuration_probabilities_with_anthropogenic_impact_map
            self.most_probable_landscape_configuration_map = final_most_probable_landscape_configuration_with_anthropogenic_impact_map

            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
            pcraster_conform_map_name = 'mplcprob'
            time_step = self.time_step  # needed for PCraster conform output
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(self.most_probable_landscape_configuration_probabilities_map,
                   os.path.join(Filepaths.folder_LULCC_mplc_probabilities, output_map_name))
            print('self.most_probable_landscape_configuration_probabilities_map created and stored as "mplcprob" in:',
                  Filepaths.folder_LULCC_mplc_probabilities)

            pcraster_conform_map_name = 'mplc'
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(self.most_probable_landscape_configuration_map,
                   os.path.join(Filepaths.folder_LULCC_mplc, output_map_name))
            print('self.most_probable_landscape_configuration_map created and stored as "mplc" in:',
                  Filepaths.folder_LULCC_mplc)


        elif Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == False:
            """This method takes the probabilities as is - not all demand is accounted for."""

            range_of_all_land_use_types = range(1, (Parameters.get_total_number_of_land_use_types() + 1))
            list_of_land_use_type_maps_for_the_time_step = []
            for a_LUT in range_of_all_land_use_types:
                a_LUT_map = self.dictionary_of_LUTs_MC_averages_dictionaries[a_LUT][self.time_step]
                list_of_land_use_type_maps_for_the_time_step.append(a_LUT_map)

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
            # THE KEY TO LPB-mplc
            # compare the maps by highest probability per pixel and note the according probability
            # ATTENTION: PCRaster max
            self.most_probable_landscape_configuration_probabilities_map = ifthenelse((max(*list_of_land_use_type_maps_for_the_time_step) > scalar(0)),
                                                                                      max(*list_of_land_use_type_maps_for_the_time_step),
                                                                                      scalar(self.null_mask_map))
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
            pcraster_conform_map_name = 'mplcprob'
            time_step = self.time_step  # needed for PCraster conform output
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
            report(self.most_probable_landscape_configuration_probabilities_map,os.path.join(Filepaths.folder_LULCC_mplc_probabilities, output_map_name))
            print('self.most_probable_landscape_configuration_probabilities_map created and stored as "mplcprob" in:',
                  Filepaths.folder_LULCC_mplc_probabilities)

        # 1.1.1) the classified probabilities map
        # now reclassify this map to achieve 7 classes for the output GIF
        # classify the values in 7 classes:
        # class/category 1 = 0 %
        # class/category 2 = >0 to 20 %
        # class/category 3 = >20 to 40 %
        # class/category 4 = >40 to 60 %
        # class/category 5 = >60 to 80 %
        # class/category 6 = >80 to <100 %
        # class/category 7 = 100 %

        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map == scalar(0),
            scalar(1),
            scalar(self.null_mask_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map > scalar(0),
            scalar(2),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map > scalar(0.2),
            scalar(3),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map > scalar(0.4),
            scalar(4),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map > scalar(0.6),
            scalar(5),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map > scalar(0.8),
            scalar(6),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))
        classified_most_probable_landscape_configuration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_probabilities_map == scalar(1),
            scalar(7),
            scalar(classified_most_probable_landscape_configuration_probabilities_map))

        # count the pixels in the categories for the log file
        self.pixels_in_probability_class_1 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 1))))
        self.percentage_of_landscape_probability_class_1 = round(
            float((self.pixels_in_probability_class_1 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_2 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 2))))
        self.percentage_of_landscape_probability_class_2 = round(
            float((self.pixels_in_probability_class_2 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_3 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 3))))
        self.percentage_of_landscape_probability_class_3 = round(
            float((self.pixels_in_probability_class_3 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_4 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 4))))
        self.percentage_of_landscape_probability_class_4 = round(
            float((self.pixels_in_probability_class_4 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_5 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 5))))
        self.percentage_of_landscape_probability_class_5 = round(
            float((self.pixels_in_probability_class_5 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_6 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 6))))
        self.percentage_of_landscape_probability_class_6 = round(
            float((self.pixels_in_probability_class_6 / self.hundred_percent_area) * 100), 2)

        self.pixels_in_probability_class_7 = int(
            maptotal(scalar(boolean(classified_most_probable_landscape_configuration_probabilities_map == 7))))
        self.percentage_of_landscape_probability_class_7 = round(
            float((self.pixels_in_probability_class_7 / self.hundred_percent_area) * 100), 2)

        # report the map
        pcraster_conform_map_name = 'mplcclpr'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
        report(classified_most_probable_landscape_configuration_probabilities_map, os.path.join(Filepaths.folder_LULCC_mplc_probabilities_classified, output_map_name))
        print('classified_most_probable_landscape_configuration_probabilities_map created and stored as "mplcclpr" in:',
              Filepaths.folder_LULCC_mplc_probabilities_classified)

        self.classified_most_probable_landscape_configuration_probabilities_map = classified_most_probable_landscape_configuration_probabilities_map

        if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == False:
            # 1.2) the nominal map
            # get the nominal land use types for the pixels with highest probability
            self.most_probable_landscape_configuration_map = nominal(self.null_mask_map)

            for LUT_key, dictionary_of_LUT_probability_maps in self.dictionary_of_LUTs_MC_averages_dictionaries.items():
                LUT_probability_map_per_time_step_i = dictionary_of_LUT_probability_maps[self.time_step]
                temporal_landscape_map = ifthen(LUT_probability_map_per_time_step_i == self.most_probable_landscape_configuration_probabilities_map,
                                                nominal(LUT_key))
                self.most_probable_landscape_configuration_map = cover(temporal_landscape_map, self.most_probable_landscape_configuration_map)

            pcraster_conform_map_name = 'mplc'
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
            report(self.most_probable_landscape_configuration_map, os.path.join(Filepaths.folder_LULCC_mplc, output_map_name))
            print('self.most_probable_landscape_configuration_map created and stored as "mplc" in:',
                  Filepaths.folder_LULCC_mplc)

        # needed for no further anthropogenic impact on forest comparison (former disturbed, initial undisturbed)
        if self.time_step == 1:
            self.initial_most_probable_landscape_configuration_map = self.most_probable_landscape_configuration_map

        # 1.3) SH: count the pixels per LUT in the map, draw %,
        # compare with demand (ha unallocated = trans-regional leakage likely) for active LUTs
        self.demand_LUT01 = int(self.demand_LUT01)
        self.allocated_pixels_LUT01 = int(maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 1))))
        self.percentage_of_landscape_LUT01 = round(float((self.allocated_pixels_LUT01 / self.hundred_percent_area) * 100), 2)
        self.unallocated_pixels_LUT01 = self.demand_LUT01 - self.allocated_pixels_LUT01

        self.demand_LUT02 = int(self.demand_LUT02)
        self.allocated_pixels_LUT02 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 2))))
        self.percentage_of_landscape_LUT02 = round(
            float((self.allocated_pixels_LUT02 / self.hundred_percent_area) * 100), 2)
        self.unallocated_pixels_LUT02 = self.demand_LUT02 - self.allocated_pixels_LUT02

        self.demand_LUT03 = int(self.demand_LUT03)
        self.allocated_pixels_LUT03 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 3))))
        self.percentage_of_landscape_LUT03 = round(
            float((self.allocated_pixels_LUT03 / self.hundred_percent_area) * 100), 2)
        self.unallocated_pixels_LUT03 = self.demand_LUT03 - self.allocated_pixels_LUT03

        self.demand_LUT04 = int(self.demand_LUT04)
        self.allocated_pixels_LUT04 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 4))))
        self.percentage_of_landscape_LUT04 = round(
            float((self.allocated_pixels_LUT04 / self.hundred_percent_area) * 100), 2)
        self.unallocated_pixels_LUT04 = self.demand_LUT04 - self.allocated_pixels_LUT04

        self.demand_LUT05 = int(self.demand_LUT05)
        self.allocated_pixels_LUT05 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 5))))
        self.percentage_of_landscape_LUT05 = round(
            float((self.allocated_pixels_LUT05 / self.hundred_percent_area) * 100), 2)
        self.unallocated_pixels_LUT05 = self.demand_LUT05 - self.allocated_pixels_LUT05

        self.allocated_pixels_LUT06 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 6))))
        self.percentage_of_landscape_LUT06 = round(
            float((self.allocated_pixels_LUT06 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT07 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 7))))
        self.percentage_of_landscape_LUT07 = round(
            float((self.allocated_pixels_LUT07 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT08 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 8))))
        self.percentage_of_landscape_LUT08 = round(
            float((self.allocated_pixels_LUT08 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT09 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 9))))
        self.percentage_of_landscape_LUT09 = round(
            float((self.allocated_pixels_LUT09 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT10 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 10))))
        self.percentage_of_landscape_LUT10 = round(
            float((self.allocated_pixels_LUT10 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT11 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 11))))
        self.percentage_of_landscape_LUT11 = round(
            float((self.allocated_pixels_LUT11 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT12 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 12))))
        self.percentage_of_landscape_LUT12 = round(
            float((self.allocated_pixels_LUT12 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT13 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 13))))
        self.percentage_of_landscape_LUT13 = round(
            float((self.allocated_pixels_LUT13 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT14 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 14))))
        self.percentage_of_landscape_LUT14 = round(
            float((self.allocated_pixels_LUT14 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT15 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 15))))
        self.percentage_of_landscape_LUT15 = round(
            float((self.allocated_pixels_LUT15 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT16 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 16))))
        self.percentage_of_landscape_LUT16 = round(
            float((self.allocated_pixels_LUT16 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT17 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 17))))
        self.percentage_of_landscape_LUT17 = round(
            float((self.allocated_pixels_LUT17 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT18 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 18))))
        self.percentage_of_landscape_LUT18 = round(
            float((self.allocated_pixels_LUT18 / self.hundred_percent_area) * 100), 2)

        self.allocated_pixels_LUT19 = int(
            maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 19))))
        self.percentage_of_landscape_LUT19 = round(
            float((self.allocated_pixels_LUT19 / self.hundred_percent_area) * 100), 2)

        # 1.4) SH: count the pixels per LUT per difficult terrain in the map, draw %

        # LUT01
        allocated_pixels_in_difficult_terrain_LUT01_map = ifthen(
            boolean(self.difficult_terrain_LUT01_map),
            scalar(self.most_probable_landscape_configuration_map) == scalar(1))
        self.allocated_pixels_in_difficult_terrain_LUT01_area = int(
            maptotal(scalar(boolean(allocated_pixels_in_difficult_terrain_LUT01_map))))
        self.percentage_of_landscape_difficult_terrain_LUT01 = round(
            float((self.allocated_pixels_in_difficult_terrain_LUT01_area / self.hundred_percent_area) * 100), 2)

        # LUT02
        allocated_pixels_in_difficult_terrain_LUT02_map = ifthen(
            boolean(self.difficult_terrain_LUT02_map),
            scalar(self.most_probable_landscape_configuration_map) == scalar(2))
        self.allocated_pixels_in_difficult_terrain_LUT02_area = int(
            maptotal(scalar(boolean(allocated_pixels_in_difficult_terrain_LUT02_map))))
        self.percentage_of_landscape_difficult_terrain_LUT02 = round(
            float((self.allocated_pixels_in_difficult_terrain_LUT02_area / self.hundred_percent_area) * 100), 2)

        # LUT03
        allocated_pixels_in_difficult_terrain_LUT03_map = ifthen(
            boolean(self.difficult_terrain_LUT03_map),
            scalar(self.most_probable_landscape_configuration_map) == scalar(3))
        self.allocated_pixels_in_difficult_terrain_LUT03_area = int(
            maptotal(scalar(boolean(allocated_pixels_in_difficult_terrain_LUT03_map))))
        self.percentage_of_landscape_difficult_terrain_LUT03 = round(
            float((self.allocated_pixels_in_difficult_terrain_LUT03_area / self.hundred_percent_area) * 100), 2)

        # LUT04
        allocated_pixels_in_difficult_terrain_LUT04_map = ifthen(
            boolean(self.difficult_terrain_LUT04_map),
            scalar(self.most_probable_landscape_configuration_map) == scalar(4))
        self.allocated_pixels_in_difficult_terrain_LUT04_area = int(
            maptotal(scalar(boolean(allocated_pixels_in_difficult_terrain_LUT04_map))))
        self.percentage_of_landscape_difficult_terrain_LUT04 = round(
            float((self.allocated_pixels_in_difficult_terrain_LUT04_area / self.hundred_percent_area) * 100), 2)

        # LUT05
        allocated_pixels_in_difficult_terrain_LUT05_map = ifthen(
            boolean(self.difficult_terrain_LUT05_map),
            scalar(self.most_probable_landscape_configuration_map) == scalar(5))
        self.allocated_pixels_in_difficult_terrain_LUT05_area = int(
            maptotal(scalar(boolean(allocated_pixels_in_difficult_terrain_LUT05_map))))
        self.percentage_of_landscape_difficult_terrain_LUT05 = round(
            float((self.allocated_pixels_in_difficult_terrain_LUT05_area / self.hundred_percent_area) * 100), 2)

        print('calculating most probable landscape configuration done')

        """SH: SAVE self.most_probable_landscape_configuration_map FOR THE WORST CASE SCENARIO IF REQUIRED"""

        if Parameters.get_worst_case_scenario_decision() is True:
            if Parameters.get_the_initial_simulation_year_for_the_worst_case_scenario() == self.year:
                print('\nsaving the most probable landscape configuration for the worst case scenario for the year',
                      self.year, '...')
                report(self.most_probable_landscape_configuration_map, os.path.join(
                    Filepaths.folder_inputs_initial_worst_case_scenario,
                    'initial_LULC_simulated_for_worst_case_scenario_input.map'))
                print('-> saved self.most_probable_landscape_configuration_map for the year', str(self.year),
                      'as initial_LULC_simulated_for_worst_case_scenario_input.map in:',
                      Filepaths.folder_inputs_initial_worst_case_scenario)

        # =================================================================== #

    def _corrective_allocation(self,
                               temporal_most_probable_landscape_configuration_map,
                               a_type,
                               demand,
                               probabilities_map,
                               herbaceous_vegetation_probabilities_map,
                               shrubs_probabilities_map,
                               disturbed_forest_probabilities_map,
                               immutable_cells_map,
                               abandoned_area_agricultural_LUT,
                               abandoned_LUT_probabilities_map):
        """This methods corrects the basic most probable probabilities map to maximum anthropogenic impact"""
        ## ATTENTION:
        # probability maps (mc averages) can contain more cells than demand
        # aggregated maps (by highest probability) can contain less cells than demand

        # # TRACK FOREST CONVERSION
        # LUT08_prior_correction = self._update_current_area_occupied(8, temporal_most_probable_landscape_configuration_map)
        # print('Forest_disturbed_prior:', LUT08_prior_correction)
        # LUT09_prior_correction = self._update_current_area_occupied(9,
        #                                                             temporal_most_probable_landscape_configuration_map)
        # print('Forest_undisturbed_prior:', LUT09_prior_correction)
        # forest_prior_conversion = LUT08_prior_correction + LUT09_prior_correction
        # print('Forest_total_prior:', forest_prior_conversion)
        #
        # # TRACK SUCCESSION AND BIOME CORRECTION LUTS
        # LUT06_prior_correction = self._update_current_area_occupied(6,
        #                                                             temporal_most_probable_landscape_configuration_map)
        # print('Herbaceous_vegetation_prior:', LUT06_prior_correction)
        # LUT07_prior_correction = self._update_current_area_occupied(7,
        #                                                             temporal_most_probable_landscape_configuration_map)
        # print('Shrubs_prior:', LUT07_prior_correction)

        # PREPARATION FOR NO CHANGES - return map if no change is simulated
        a_LUT_probabilities_with_maximum_anthropogenic_impact_map = probabilities_map
        immutable_cells_map = immutable_cells_map
        temporal_most_probable_landscape_configuration_map = temporal_most_probable_landscape_configuration_map

        # STEP 1 MEET DEMAND OF THE ACTIVE LUTS BY ADDITION OF CELLS
        if a_type in [1, 2, 3, 4, 5, 17]:
            print('LUT', a_type, 'demand', int(demand))

            # get the current area occupied by the LUT
            current_area_occupied_by_LUT = self._update_current_area_occupied(a_type, temporal_most_probable_landscape_configuration_map)

            # special calculation for plantations - get the maximum value simulated in basic for the year
            if a_type == 5:
                total_plantations_demand = demand
                demand = int(self.simulated_LUT05_maximum) # simulate the standing plantations

            # add the current cells occupied to the immutables map
            immutable_cells_map = ifthenelse(scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                                             scalar(1),
                                             scalar(immutable_cells_map))

            # subtract the already immutable cells from the probability map
            remaining_probabilities_map = ifthen(scalar(immutable_cells_map) != scalar(1),
                                                 probabilities_map)

            # and eliminate the zeros
            remaining_probabilities_map = ifthen(scalar(remaining_probabilities_map) != scalar(0),
                                                 scalar(remaining_probabilities_map))

            # add small noise to prevent the same probabilities
            remaining_probabilities_map = remaining_probabilities_map + self.small_noise_map

            # order the remaining probabilities map
            remaining_probabilities_map_ordered = order(remaining_probabilities_map)

            # get the mapmaximum of the ordered probabilities map
            map_maximum = int(mapmaximum(remaining_probabilities_map_ordered))

            # get the unallocated demand
            demand_unallocated = int(demand) - int(current_area_occupied_by_LUT)
            print('LUT', a_type, 'demand_unallocated is:', int(demand_unallocated))

            # FOR ALL LUTS CORRECT TO MORE CELLS IF DEMAND IS NOT MET YET
            if demand_unallocated > 0:
                print('LUT', a_type, 'correct to MORE cells')
                # get the threshold value above which the probabilities will be chosen:
                threshold = map_maximum - demand_unallocated

                print('LUT', a_type, 'probabilities map threshold for addition is:', int(threshold))

                # pick the probabilities for the LUT above the threshold value
                a_LUT_probabilities_with_maximum_anthropogenic_impact_map = ifthen(remaining_probabilities_map_ordered > scalar(threshold),
                                                                                   scalar(probabilities_map))

                a_LUT_probabilities_with_maximum_anthropogenic_impact_map = cover(scalar(a_LUT_probabilities_with_maximum_anthropogenic_impact_map),
                                                                                  scalar(self.null_mask_map))


                # get the nominal map
                a_LUT_nominal_with_maximum_anthropogenic_impact_map = ifthen(remaining_probabilities_map_ordered > scalar(threshold),
                                                                             nominal(a_type))

                # built the new temporal most probable landscape configuration
                temporal_most_probable_landscape_configuration_map = cover(nominal(a_LUT_nominal_with_maximum_anthropogenic_impact_map),
                                                                           nominal(temporal_most_probable_landscape_configuration_map))

                # note the cells on the dynamic immutables map
                immutable_cells_map = ifthenelse(
                    scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                    scalar(1),
                    scalar(immutable_cells_map))

                print('LUT', a_type, 'new area occupied after addition: ', int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))

            # STEP 2a CORRECT LUT01 TOO LESS CELLS WITH BIOME PIXEL INFORMATION
            if a_type == 1 and demand_unallocated < 0:

                print('LUT', a_type, 'correction to less cells by biome pixels')

                print('LUT', a_type, 'current area occupied: ',
                      int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))

                # first get the current distribution of the LUT
                current_LUT_distribution_map = ifthen(
                    scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                    scalar(1))

                # note the probabilities in this distribution
                current_LUT_probabilities_distribution_map = ifthen(scalar(current_LUT_distribution_map) == scalar(1),
                                                                    scalar(abandoned_LUT_probabilities_map))

                # and eliminate the zeros
                current_LUT_probabilities_distribution_map = ifthen(
                    scalar(current_LUT_probabilities_distribution_map) != scalar(0),
                    scalar(current_LUT_probabilities_distribution_map))

                # add small noise to prevent the same probabilities
                current_LUT_probabilities_distribution_map = current_LUT_probabilities_distribution_map + self.small_noise_map

                # order this map
                current_LUT_probabilities_distribution_ordered_map = order(current_LUT_probabilities_distribution_map)

                # get the maximum probability
                map_maximum = mapmaximum(current_LUT_probabilities_distribution_ordered_map)

                # the threshold under which land use will be transformed to the biome information LUT
                threshold = map_maximum - demand
                print('LUT', a_type, 'probabilities map threshold for subtraction is:', int(threshold))

                # get the pixels that need to be corrected
                correction_boolean_map = ifthen(
                    scalar(current_LUT_probabilities_distribution_ordered_map) <= scalar(threshold),
                    scalar(1))

                # now correct the map for the type depending on biome information
                correction_rules = Filepaths.file_static_mplc_correction_rules_for_abandoned_types_input

                types_correction_map = lookupscalar(correction_rules,
                                                    correction_boolean_map,
                                                    self.projection_potential_natural_vegetation_distribution_map)

                temporal_most_probable_landscape_configuration_map = cover(scalar(types_correction_map),
                                                                           scalar(
                                                                               temporal_most_probable_landscape_configuration_map))

                # indicate the substituted correction pixels with small noise probabilities and note it on the full return map
                substituted_probabilities_map = ifthen(
                    scalar(types_correction_map) != scalar(0),
                    scalar(self.small_noise_map))

                combined_probabilities_map = cover(
                    scalar(substituted_probabilities_map),
                    scalar(current_LUT_probabilities_distribution_map))

                current_LUT_probabilities_distribution_map = cover(
                    scalar(combined_probabilities_map),
                    scalar(self.null_mask_map))

                a_LUT_probabilities_with_maximum_anthropogenic_impact_map = current_LUT_probabilities_distribution_map

                immutable_cells_map = ifthenelse(
                    scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                    scalar(1),
                    scalar(immutable_cells_map))

                print('LUT', a_type, 'new area occupied after subtraction: ',
                      int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))

            # STEP 2b FOR ALL LUTS EXCEPT LUT01 CORRECT IF TOO MANY CELLS ARE ALLOCATED
            if a_type in [2, 3, 4, 5, 17] and demand_unallocated < 0:
                print('LUT', a_type, 'correct to LESS cells')

                # first declare the abandoned/deforested type per source LUT
                unused_LUT = 0
                if a_type == 2:
                    unused_LUT = 14
                elif a_type == 3:
                    unused_LUT = 15
                elif a_type == 4:
                    unused_LUT = 16
                elif a_type == 5:
                    unused_LUT = 18
                elif a_type == 17:
                    unused_LUT = 8

                # get the new area allocated
                current_area_occupied_by_LUT = self._update_current_area_occupied(a_type, temporal_most_probable_landscape_configuration_map)

                # count the initial declared abandoned cells in the map for this LUT
                #self.initial_abandoned_cells_maptotal = self._update_current_area_occupied(unused_LUT, temporal_most_probable_landscape_configuration_map)

                # get the difference to demand
                difference = demand - current_area_occupied_by_LUT
                # 0 = demand is exactly satisfied
                # positive = demand needs to be allocated
                # negative = too much area allocated

                print('LUT', a_type, 'demand vs allocated difference', difference)

                # correct only if the difference is negative, meaning, that too much area was allocated
                if a_type in [2, 3, 4, 5] and difference < 0: # agricultural types and plantations
                    print('LUT', a_type, 'correction to LESS cells')
                    # first get the current distribution of the LUT
                    current_LUT_distribution_map = ifthen(scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                                                          scalar(1))

                    # note the probabilities in this distribution
                    current_LUT_probabilities_distribution_map = ifthen(scalar(current_LUT_distribution_map) == scalar(1),
                                                                        scalar(probabilities_map))

                    # and eliminate the zeros
                    current_LUT_probabilities_distribution_map = ifthen(scalar(current_LUT_probabilities_distribution_map) != scalar(0),
                                                                        scalar(current_LUT_probabilities_distribution_map))

                    # add small noise to prevent the same probabilities
                    current_LUT_probabilities_distribution_map = current_LUT_probabilities_distribution_map + self.small_noise_map

                    # order this map
                    current_LUT_probabilities_distribution_ordered_map = order(current_LUT_probabilities_distribution_map)

                    # get the minimum probability
                    map_minimum = mapminimum(current_LUT_probabilities_distribution_ordered_map)

                    # the threshold under which land use will be changed to abandoned / deforested
                    threshold = map_minimum + abs(difference) # change the negative number into a positive one for calculation
                    print('LUT', a_type, 'probabilities map threshold for subtraction is:', int(threshold))

                    # now correct the map for the types
                    correction_map = ifthen(scalar(current_LUT_probabilities_distribution_ordered_map) < scalar(threshold),
                                            scalar(unused_LUT))

                    # now take the new unused LUT cells and add small noise for them to the abandoned LUT probabilities map, so they can be corrected to biome infomartion
                    abandoned_LUT_probabilities_map = ifthenelse(scalar(correction_map) == scalar(unused_LUT),
                                                                 scalar(self.small_noise_map),
                                                                 abandoned_LUT_probabilities_map)

                    # proceed for the current active LUT
                    correction_map_combined = cover(scalar(correction_map), scalar(temporal_most_probable_landscape_configuration_map))

                    # pick the probabilities for the LUT for the remaining cells
                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = ifthen(
                        scalar(correction_map_combined) == scalar(a_type),
                        scalar(probabilities_map))

                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = cover(
                        scalar(a_LUT_probabilities_with_maximum_anthropogenic_impact_map),
                        scalar(self.null_mask_map))

                    # note the cells on the dynamic immutables map
                    immutable_cells_map = ifthenelse(
                        scalar(correction_map_combined) == scalar(a_type),
                        scalar(1),
                        scalar(immutable_cells_map))

                    # correct the nominal map to the new original LUTs distribution
                    a_LUT_nominal_with_maximum_anthropogenic_impact_map = ifthen(
                        scalar(correction_map_combined) == scalar(a_type),
                        nominal(correction_map_combined))

                    a_LUT_nominal_with_maximum_anthropogenic_impact_map = cover(
                        nominal(a_LUT_nominal_with_maximum_anthropogenic_impact_map),
                        nominal(self.null_mask_map))

                    # built the new temporal most probable landscape configuration
                    temporal_most_probable_landscape_configuration_map = correction_map_combined

                    print('LUT', a_type, 'new area occupied: ',
                          int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))


                # correct the excess of allocation by probabilities for LUT17
                if a_type == 17 and difference < 0: # forest based type
                    print('forest based LUT', a_type, 'correction to LESS cells')
                    corrective_LUT = 8 # change back to disturbed forest if too much area was allocated by probabilities

                    # first get the current distribution of the LUT
                    current_LUT_distribution_map = ifthen(
                        scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                        scalar(1))

                    # note the probabilities in this distribution
                    current_LUT_probabilities_distribution_map = ifthen(scalar(current_LUT_distribution_map) == scalar(1),
                                                                        scalar(probabilities_map))

                    # and eliminate the zeros
                    current_LUT_probabilities_distribution_map = ifthen(
                        scalar(current_LUT_probabilities_distribution_map) != scalar(0),
                        scalar(current_LUT_probabilities_distribution_map))

                    # add small noise to prevent the same probabilities
                    current_LUT_probabilities_distribution_map = current_LUT_probabilities_distribution_map + self.small_noise_map

                    # order this map
                    current_LUT_probabilities_distribution_ordered_map = order(current_LUT_probabilities_distribution_map)

                    # get the minimum probability
                    map_minimum = mapminimum(current_LUT_probabilities_distribution_ordered_map)

                    # the threshold under which land use will be changed to disturbed forest
                    threshold = map_minimum + abs(difference)  # change the negative number into a positive one for calculation

                    print('LUT', a_type, 'probabilities map threshold for final correction is:', int(threshold))

                    # now correct the map for the types
                    correction_map = ifthen(scalar(current_LUT_probabilities_distribution_ordered_map) < scalar(threshold),
                                            scalar(corrective_LUT))

                    correction_map = cover(scalar(correction_map),
                                           scalar(temporal_most_probable_landscape_configuration_map))

                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = ifthenelse(scalar(correction_map) > scalar(0),
                                                                                           scalar(disturbed_forest_probabilities_map), # note the probability of disturbed forest
                                                                                           a_LUT_probabilities_with_maximum_anthropogenic_impact_map)


                    temporal_most_probable_landscape_configuration_map = correction_map

                    print('LUT', a_type, 'area after correction is:', int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == 17)))))


            # correct the area for abandoned plots
            if a_type in [2, 3, 4, 5]:

                # adapt to the current handled LUT abandoned
                if a_type == 2:
                    a_type = 14
                elif a_type == 3:
                    a_type = 15
                elif a_type == 4:
                    a_type = 16
                elif a_type == 5:
                    a_type = 18

                # count the current declared abandoned cells in the map
                current_abandoned_cells_maptotal = int(maptotal(scalar(boolean(scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type)))))

                # check if they need correction going down
                if current_abandoned_cells_maptotal < abandoned_area_agricultural_LUT:
                    print('LUT', a_type, 'correction to MORE cells')

                    correction_value = abandoned_area_agricultural_LUT - current_abandoned_cells_maptotal

                    print('LUT', a_type, 'calculated abandoned area:', abandoned_area_agricultural_LUT)
                    #print('LUT', a_type, 'initial area:', self.initial_abandoned_cells_maptotal)
                    print('LUT', a_type, 'current area:', current_abandoned_cells_maptotal)
                    print('LUT', a_type, 'to be corrected area:', correction_value)

                    # add the current cells occupied to the immutables map
                    immutable_cells_map = ifthenelse(
                        scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                        scalar(1),
                        scalar(immutable_cells_map))

                    # subtract the already immutable cells from the probability map
                    remaining_probabilities_map = ifthen(scalar(immutable_cells_map) != scalar(1),
                                                         abandoned_LUT_probabilities_map)

                    # and eliminate the zeros
                    remaining_probabilities_map = ifthen(scalar(remaining_probabilities_map) != scalar(0),
                                                         scalar(remaining_probabilities_map))

                    # add small noise to prevent the same probabilities
                    remaining_probabilities_map = remaining_probabilities_map + self.small_noise_map

                    # order the remaining probabilities map
                    remaining_probabilities_map_ordered = order(remaining_probabilities_map)

                    # get the mapmaximum of the ordered probabilities map
                    map_maximum = int(mapmaximum(remaining_probabilities_map_ordered))

                    threshold = map_maximum - correction_value

                    print('LUT', a_type, 'probabilities map threshold for addition is:', int(threshold))

                    # pick the probabilities for the LUT above the threshold value
                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = ifthen(
                        remaining_probabilities_map_ordered >= scalar(threshold),
                        scalar(abandoned_LUT_probabilities_map))

                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = cover(
                        scalar(a_LUT_probabilities_with_maximum_anthropogenic_impact_map),
                        scalar(self.null_mask_map))

                    # get the nominal map
                    a_LUT_nominal_with_maximum_anthropogenic_impact_map = ifthen(
                        remaining_probabilities_map_ordered >= scalar(threshold),
                        nominal(a_type))

                    # built the new temporal most probable landscape configuration
                    temporal_most_probable_landscape_configuration_map = cover(
                        nominal(a_LUT_nominal_with_maximum_anthropogenic_impact_map),
                        nominal(temporal_most_probable_landscape_configuration_map))

                    # note the cells on the dynamic immutables map
                    immutable_cells_map = ifthenelse(
                        scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                        scalar(1),
                        scalar(immutable_cells_map))

                    print('LUT', a_type, 'new area occupied after addition: ',
                          int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))

                # check if they need correction going down
                if current_abandoned_cells_maptotal > abandoned_area_agricultural_LUT :
                    print('LUT', a_type, 'correction to LESS cells')

                    # calculate the correction value
                    correction_value = current_abandoned_cells_maptotal - abandoned_area_agricultural_LUT

                    print('LUT', a_type, 'calculated abandoned area:', abandoned_area_agricultural_LUT)
                    #print('LUT', a_type, 'initial area:', self.initial_abandoned_cells_maptotal)
                    print('LUT', a_type, 'current area:', current_abandoned_cells_maptotal)
                    print('LUT', a_type, 'to be corrected area:', correction_value)

                    # first get the current distribution of the LUT
                    current_LUT_distribution_map = ifthen(
                                scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                                scalar(1))

                    # note the probabilities in this distribution
                    current_LUT_probabilities_distribution_map = ifthen(scalar(current_LUT_distribution_map) == scalar(1),
                                                                                scalar(abandoned_LUT_probabilities_map))


                    # and eliminate the zeros
                    current_LUT_probabilities_distribution_map = ifthen(
                                scalar(current_LUT_probabilities_distribution_map) != scalar(0),
                                scalar(current_LUT_probabilities_distribution_map))

                    # add small noise to prevent the same probabilities
                    current_LUT_probabilities_distribution_map = current_LUT_probabilities_distribution_map + self.small_noise_map

                    # order this map
                    current_LUT_probabilities_distribution_ordered_map = order(current_LUT_probabilities_distribution_map)

                    # get the minimum probability
                    map_minimum = int(mapminimum(current_LUT_probabilities_distribution_ordered_map))

                    # the threshold under which land use will be transformed from abandoned to the biome information LUT
                    threshold = map_minimum + correction_value
                    print('LUT', a_type, 'probabilities map threshold for subtraction is:', int(threshold))

                    # get the pixels that need to be corrected
                    correction_boolean_map = ifthen(
                                scalar(current_LUT_probabilities_distribution_ordered_map) <= scalar(threshold),
                                scalar(1))

                    # now correct the map for the type depending on biome information
                    correction_rules = Filepaths.file_static_mplc_correction_rules_for_abandoned_types_input

                    types_correction_map = lookupscalar(correction_rules,
                                                                correction_boolean_map,
                                                                self.projection_potential_natural_vegetation_distribution_map)

                    temporal_most_probable_landscape_configuration_map = cover(scalar(types_correction_map),
                                                   scalar(temporal_most_probable_landscape_configuration_map))


                    # FINISH: CHECK FOR CURRENT DISTRIBUTION
                    print('LUT', a_type, 'new area occupied after subtraction: ',
                              int(maptotal(scalar(boolean(temporal_most_probable_landscape_configuration_map == a_type)))))

                    # CORRECTED PROBABILITIES
                    probabilities_herbaceous_vegetation_map = ifthen(types_correction_map == 6,
                                                                         herbaceous_vegetation_probabilities_map)

                    probabilities_shrubs_map = ifthen(types_correction_map == 7,
                                                          shrubs_probabilities_map)

                    probabilities_forest_map = ifthen(types_correction_map == 8,
                                                          disturbed_forest_probabilities_map)

                    combined_probabilities_map = cover(scalar(probabilities_shrubs_map), scalar(probabilities_herbaceous_vegetation_map))
                    combined_probabilities_map = cover(scalar(probabilities_forest_map), scalar(combined_probabilities_map))

                    a_LUT_probabilities_with_maximum_anthropogenic_impact_map = cover(scalar(combined_probabilities_map), scalar(a_LUT_probabilities_with_maximum_anthropogenic_impact_map))

                    # note the cells on the dynamic immutables map
                    immutable_cells_map = ifthenelse(
                        scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                        scalar(1),
                        scalar(immutable_cells_map))

                # sign the types back to the active type
                if a_type == 14:
                    a_type = 2
                elif a_type == 15:
                    a_type = 3
                elif a_type == 16:
                    a_type = 4
                elif a_type == 18:
                    a_type = 5

                 # note the cells on the dynamic immutables map
                immutable_cells_map = ifthenelse(
                    scalar(temporal_most_probable_landscape_configuration_map) == scalar(a_type),
                    scalar(1),
                    scalar(immutable_cells_map))


        # # TRACK FOREST CONVERSION
        # LUT08_post_correction = self._update_current_area_occupied(8,
        #                                                                     temporal_most_probable_landscape_configuration_map)
        # print('Forest_disturbed_post:', LUT08_post_correction)
        # LUT09_post_correction = self._update_current_area_occupied(9,
        #                                                                     temporal_most_probable_landscape_configuration_map)
        # print('Forest_undisturbed_post:', LUT09_post_correction)
        # forest_post_conversion = LUT08_post_correction + LUT09_post_correction
        # print('Forest_total_post:', forest_post_conversion)
        #
        # # TRACK SUCCESSION AND BIOME CORRECTION LUTS
        # LUT06_post_correction = self._update_current_area_occupied(6,
        #                                                             temporal_most_probable_landscape_configuration_map)
        # print('Herbaceous_vegetation_post:', LUT06_post_correction)
        # LUT07_post_correction = self._update_current_area_occupied(7,
        #                                                             temporal_most_probable_landscape_configuration_map)
        # print('Shrubs_post:', LUT07_post_correction)

        return a_LUT_probabilities_with_maximum_anthropogenic_impact_map, immutable_cells_map, temporal_most_probable_landscape_configuration_map

        # =================================================================== #

    def _update_current_area_occupied(self, a_type, initial_most_probable_landscape_configuration_map):
        # SH: LPB alternation - count the cells in current environment
        current_area_occupied_by_LUT_map = ifthen(initial_most_probable_landscape_configuration_map == a_type,
                                                       scalar(1))
        current_area_occupied_by_LUT = int(maptotal(scalar(current_area_occupied_by_LUT_map)))
        print('LUT', a_type, 'current area occupied is:', current_area_occupied_by_LUT,
              Parameters.get_pixel_size())

        return current_area_occupied_by_LUT

    def create_tiles_subsets(self):
        """ LAFORET method: create subsets for the original study areas."""

        print('\ncreating regional tiles subsets ...')

        if self.time_step == 1:

            # first filter the nested dictionary to remove sub-dictionaries which value is None

            self.dictionary_of_tiles_maps_clean = {}

            def remove_keys_with_none_values(item):
                if not hasattr(item, 'items'):
                    return item
                else:
                    return {key: remove_keys_with_none_values(value) for key, value in item.items() if value is not None}

            self.dictionary_of_tiles_maps_clean = remove_keys_with_none_values(self.dictionary_of_tiles_maps)

            # in time step 1 get for each tile the output folder with identifier and name
            for an_entry in self.dictionary_of_tiles_maps_clean:
                a_tile_identifier = self.dictionary_of_tiles_maps_clean[an_entry]['identifier']
                a_tile_name = self.dictionary_of_tiles_maps_clean[an_entry]['name']
                a_subset_output_folder = os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'TILES_MPLC', 'tile_' + str(a_tile_identifier) + '_' + str(a_tile_name))
                os.makedirs(a_subset_output_folder, exist_ok=True)

        # for all time steps and given entries create a map
        for an_entry in self.dictionary_of_tiles_maps_clean:
            a_tile_map = self.dictionary_of_tiles_maps_clean[an_entry]['map']
            a_tile_identifier = self.dictionary_of_tiles_maps_clean[an_entry]['identifier']
            a_tile_name = self.dictionary_of_tiles_maps_clean[an_entry]['name']
            a_subset_output_folder = os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'TILES_MPLC',
                                                       'tile_' + str(a_tile_identifier) + '_' + str(
                                                           a_tile_name))
            a_mplc_subset_map = ifthen(scalar(a_tile_map) == scalar(1),
                                       scalar(self.most_probable_landscape_configuration_map))

            # report
            time_step = self.time_step
            pcraster_conform_map_name = 'tile_' + str(a_tile_identifier)
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
            report(a_mplc_subset_map, os.path.join(a_subset_output_folder, output_map_name))
            print('a_mplc_subset_map for', str(a_tile_identifier), 'created and stored as', output_map_name, 'in:',
                  a_subset_output_folder)

        print('creating regional tiles subsets done')

        # =================================================================== #

    def calculate_anthropogenic_features(self):
        """Derives the pixels for cities, settlements, streets and additional built up."""

        print('\ncalculating anthropogenic features ...')

        # 0) based on population:
        dictionary_of_anthropogenic_features['population'][self.time_step] = self.population

        # 1) cities (those are static, calculated on the input file)
        self.cities = int(maptotal(scalar(self.cities_map)))

        # 2) self.settlements (those are modelled deterministically and imported as values via CSV from LPB-basic
        self.settlements = int(self.settlements)

        # 3) streets (this is static)
        self.streets = int(maptotal(scalar(self.streets_map)))

        # 4)  additional built up in the landscape - this is probabilistic based modelled in LPB-basic and aggregated in LPB-mplc
        built_up_total = self.allocated_pixels_LUT01
        self.built_up_additionally = built_up_total - self.cities - self.settlements - self.streets

        # MAKE A GIF FOR THE DEVELOPMENT OF SETTLEMENTS WITHIN ANTHROPOGENIC FEATURES
        anthropogenic_features_deterministic_map = (scalar(self.streets_map) + 1) # class 1 region, class 2 streets
        anthropogenic_features_deterministic_map = ifthenelse(scalar(self.cities_map) == scalar(1),
                                                              scalar(3), # class 3 cities
                                                              scalar(anthropogenic_features_deterministic_map))

        settlements_map = self.dictionary_of_settlements_files[self.time_step]
        reclassified_settlements_map = ifthen(scalar(settlements_map) == scalar(1),
                                 scalar(settlements_map) + 3) # class 4 settlements

        anthropogenic_features_deterministic_map = cover(scalar(reclassified_settlements_map), scalar(anthropogenic_features_deterministic_map))

        # count the cells
        street_pixels = int(maptotal(scalar(self.streets_map)))
        dictionary_of_anthropogenic_features['streets'][self.time_step]= street_pixels
        cities_pixels = int(maptotal(scalar(self.cities_map)))
        dictionary_of_anthropogenic_features['cities'][self.time_step] = cities_pixels
        settlements_pixels = int(maptotal(scalar(boolean(anthropogenic_features_deterministic_map == 4))))
        dictionary_of_anthropogenic_features['settlements'][self.time_step] = settlements_pixels


        # enhance cities and settlements for the GIF
        radius_cities_buffer = spreadmaxzone(self.cities_map, 0, 1, 1500)
        visual_anthropogenic_features_deterministic_map = ifthenelse(scalar(radius_cities_buffer) > 0,
                                                                     scalar(3),
                                                                     anthropogenic_features_deterministic_map)

        radius_settlements_buffer = spreadmaxzone(boolean(settlements_map), 0, 1, 1000)
        visual_anthropogenic_features_deterministic_map = ifthenelse(scalar(radius_settlements_buffer) > 0,
                                                                     scalar(4),
                                                                     visual_anthropogenic_features_deterministic_map)

        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'vanfedet'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(visual_anthropogenic_features_deterministic_map,
               os.path.join(Filepaths.folder_anthropogenic_features_deterministic,
                            output_map_name))
        print('visual_anthropogenic_features_deterministic_map created and stored as "vanfedet" in:',
              Filepaths.folder_anthropogenic_features_deterministic)


        print('calculating anthropogenic features done')

        # =================================================================== #

    def calculate_hidden_deforestation_for_input_biomass(self):
        """In case deforestation for input biomass is calculated first get the possible maximum impact area from the probabilities map."""

        print('\ncalculating hidden deforestation for demand in input biomass ...')

        deforested_for_input_biomass_probabilities_map = self.dictionary_of_deforested_for_input_biomass_before_conversion_files[self.time_step]

        boolean_maximum_deforested_for_input_biomass_map = boolean(deforested_for_input_biomass_probabilities_map)

        self.maximum_deforested_for_input_biomass_area = int(maptotal(scalar(boolean_maximum_deforested_for_input_biomass_map)))

        self.maximum_deforested_for_input_biomass_percentage_of_landscape = round(
            float((self.maximum_deforested_for_input_biomass_area / self.hundred_percent_area) * 100), 2)

        print('calculating hidden deforestation for demand in input biomass done')

        # =================================================================== #

    def construct_user_defined_gross_forest(self):
        """gross forest is depended on the users interpretation noted in Parameters.py"""

        self.gross_forest_LUTs_list = Parameters.get_gross_forest_LUTs_list()

        self.user_defined_gross_forest_map = self.null_mask_map
        for a_LUT in self.gross_forest_LUTs_list:
            self.user_defined_gross_forest_map = ifthenelse(
                scalar(self.most_probable_landscape_configuration_map) == scalar(a_LUT),
                scalar(1),
                scalar(self.user_defined_gross_forest_map))

        # =================================================================== #

    def calculate_net_forest_most_probable_landscape_configuration(self):
        """SH: NET FOREST most probable landscape configuration. Since net forest is simulated probabilistically in LPB-basic, it needs to get calculated again in LPB-mplc."""

        print('\ncalculating net forest most probable landscape configuration ...')

        for a_key in self.dictionary_of_net_forest_files:
            if a_key == self.time_step:
                net_forest_probabilities_map = self.dictionary_of_net_forest_files[a_key]

        net_forest_probabilities_map = cover(scalar(net_forest_probabilities_map), scalar(self.null_mask_map))

        boolean_net_forest_probabilities_map = ifthenelse(scalar(net_forest_probabilities_map) > scalar(0),
                                                          boolean(1),
                                                          boolean(self.null_mask_map))

        net_forest_probable_area = int(maptotal(scalar(boolean(scalar(boolean_net_forest_probabilities_map) == scalar(1)))))
        dictionary_of_net_forest_information['probable_net_forest_area'][self.time_step] = net_forest_probable_area

        net_forest_probable_percentage_of_landscape = round(
            float((net_forest_probable_area / self.hundred_percent_area) * 100), 2)
        dictionary_of_net_forest_information['probable_percentage_of_landscape'][self.time_step] = net_forest_probable_percentage_of_landscape

        environment_in_net_forest_probabilities_map = ifthen(scalar(boolean_net_forest_probabilities_map) == scalar(1),
                                                             scalar(self.most_probable_landscape_configuration_map))

        disturbed_net_forest_map = ifthen(environment_in_net_forest_probabilities_map == 8,
                                          scalar(1))

        undisturbed_net_forest_map = ifthen(environment_in_net_forest_probabilities_map == 9,
                                          scalar(1))

        self.net_forest_mplc_map = cover(scalar(disturbed_net_forest_map), scalar(undisturbed_net_forest_map))

        self.net_forest_mplc_map = cover(scalar(self.net_forest_mplc_map), scalar(self.null_mask_map))

        """SH: SAVE self.net_forest_mplc_map FOR THE WORST CASE SCENARIO IF REQUIRED"""

        if Parameters.get_worst_case_scenario_decision() is True:
            if Parameters.get_the_initial_simulation_year_for_the_worst_case_scenario() == self.year:
                print('\nsaving self.net_forest_mplc_map for the worst case scenario for the year',
                      self.year, '...')
                report(self.net_forest_mplc_map, os.path.join(
                    Filepaths.folder_inputs_initial_worst_case_scenario,
                    'initial_net_forest_simulated_for_worst_case_scenario_input.map'))
                print('-> saved self.net_forest_mplc_map for the year', str(self.year),
                      'as initial_net_forest_simulated_for_worst_case_scenario_input.map in:',
                      Filepaths.folder_inputs_initial_worst_case_scenario)

        # log file variables
        self.net_forest_mplc_area = int(maptotal(scalar(boolean(self.net_forest_mplc_map == 1))))
        dictionary_of_net_forest_information['mplc_net_forest_area'][self.time_step] = self.net_forest_mplc_area

        self.net_forest_mplc_percentage_of_landscape = round(
            float((self.net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        dictionary_of_net_forest_information['mplc_percentage_of_landscape'][self.time_step] = self.net_forest_mplc_percentage_of_landscape

        self.net_forest_environment_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                                nominal(self.most_probable_landscape_configuration_map),
                                                nominal(self.null_mask_map))

        self.net_mplc_disturbed_forest_area = int(maptotal(scalar(boolean(scalar(self.net_forest_environment_map) == scalar(8)))))
        dictionary_of_net_forest_information['mplc_net_disturbed_area'][self.time_step] = self.net_mplc_disturbed_forest_area

        self.net_mplc_disturbed_forest_percentage_of_landscape = round(
            float((self.net_mplc_disturbed_forest_area / self.hundred_percent_area) * 100), 2)
        dictionary_of_net_forest_information['mplc_net_disturbed_percentage_of_landscape'][self.time_step] = self.net_mplc_disturbed_forest_percentage_of_landscape

        self.net_mplc_undisturbed_forest_area = int(maptotal(scalar(boolean(scalar(self.net_forest_environment_map) == scalar(9)))))
        dictionary_of_net_forest_information['mplc_net_undisturbed_area'][self.time_step] = self.net_mplc_undisturbed_forest_area

        self.net_mplc_undisturbed_forest_percentage_of_landscape = round(
            float((self.net_mplc_undisturbed_forest_area / self.hundred_percent_area) * 100), 2)
        dictionary_of_net_forest_information['mplc_net_undisturbed_percentage_of_landscape'][self.time_step] = self.net_mplc_undisturbed_forest_percentage_of_landscape

        # GIF classes
        # 1 = region (black), 2 = gross forest(grey), 3 = net forest based on probability(yellow), 4 = mplc net forest disturbed(petrol), 5 = mplc net forest undisturbed(green)

        # SH: gross forest: consisting of net_forest, other forest disturbed an undisturbed, agroforestry and plantations
        # include plantations only if user defined
        list_of_gross_forest_LUTs = Parameters.get_gross_forest_LUTs_list()

        if 8 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                           scalar(3),  # category other disturbed forest
                                           scalar(self.null_mask_map))

        if 9 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                                           scalar(3),  # category  other undisturbed forest
                                           scalar(gross_forest_mplc_map))

        if 4 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(4),
                                           scalar(4),  # category agroforestry
                                           scalar(gross_forest_mplc_map))

        if 5 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(5),
                                               scalar(5),  # category plantation
                                               scalar(gross_forest_mplc_map))

        gross_forest_mplc_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                           scalar(2),  # category net forest
                                           scalar(gross_forest_mplc_map))

        gross_forest_mplc_map = ifthenelse(scalar(gross_forest_mplc_map) == scalar(0),
                                           scalar(1),  # category region
                                           scalar(gross_forest_mplc_map))

        self.gross_forest_mplc_map = gross_forest_mplc_map

        net_forest_base_map = ifthenelse(scalar(self.gross_forest_mplc_map) > scalar(1),
                                         scalar(2), # class 2 gross forest
                                         scalar(self.null_mask_map) + 1) # class 1 region

        classified_mplc_net_forest_map = ifthenelse(scalar(boolean_net_forest_probabilities_map) == scalar(1),
                                                    scalar(3), # class 3 all cells with a probability greater 0
                                                    scalar(net_forest_base_map)) # class 1 and 2

        net_forest_disturbed_map = ifthen(scalar(self.net_forest_environment_map) == scalar(8),
                                          scalar(4)) # class 4 disturbed in mplc

        net_forest_undisturbed_map = ifthen(scalar(self.net_forest_environment_map) == scalar(9),
                                            scalar(5))  # class 5 disturbed in mplc

        classified_mplc_net_forest_map = cover(scalar(net_forest_disturbed_map),
                                               scalar(classified_mplc_net_forest_map)) # + disturbed

        classified_mplc_net_forest_map = cover(scalar(net_forest_undisturbed_map),
                                               scalar(classified_mplc_net_forest_map))  # + undisturbed

        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'mplcnfcl'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_mplc_net_forest_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_net_detailed,
                            output_map_name))
        print('classified_mplc_net_forest_map created and stored as "mplcnfcl" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_net_detailed)

        # built a simple boolean net forest map to be used in RAP
        boolean_net_forest_disturbed_map = ifthen(scalar(net_forest_disturbed_map) == scalar(4),
                                                  scalar(1))

        boolean_net_forest_undisturbed_map = ifthen(scalar(net_forest_undisturbed_map) == scalar(5),
                                                    scalar(1))

        boolean_net_forest_mplc_map = cover(scalar(boolean_net_forest_disturbed_map), scalar(boolean_net_forest_undisturbed_map))
        boolean_net_forest_mplc_map = cover(scalar(boolean_net_forest_mplc_map), scalar(self.null_mask_map))

        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'mplcnfbo'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(boolean_net_forest_mplc_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_net_boolean,
                            output_map_name))
        print('boolean_net_forest_mplc_map created and stored as "mplcnfbo" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_net_boolean)

        print('calculating net forest most probable landscape configuration done')

        # =================================================================== #

    def construct_deforestation_and_forest_conversion_maps(self):
        """Show deforestation and conversion of forest"""

        print('\ncalculating deforestation and forest conversion maps ...')

        #1) net forest deforestation by outtake of input biomass for timber, fuelwood and charcoal - LUT17
        a_LUT17_probabilities_map = self.dictionary_of_LUTs_MC_averages_dictionaries[17][self.time_step]

        deforested_for_outtake_of_input_biomass_maximum_area = int(maptotal(scalar(boolean(a_LUT17_probabilities_map > 0))))
        list_of_new_deforested_area.append(deforested_for_outtake_of_input_biomass_maximum_area)

        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map == scalar(0),
            scalar(1),
            scalar(self.null_mask_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map > scalar(0),
            scalar(2),
            scalar(classified_LUT17_probabilities_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map > scalar(0.2),
            scalar(3),
            scalar(classified_LUT17_probabilities_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map > scalar(0.4),
            scalar(4),
            scalar(classified_LUT17_probabilities_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map > scalar(0.6),
            scalar(5),
            scalar(classified_LUT17_probabilities_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map > scalar(0.8),
            scalar(6),
            scalar(classified_LUT17_probabilities_map))
        classified_LUT17_probabilities_map = ifthenelse(
            a_LUT17_probabilities_map == scalar(1),
            scalar(7),
            scalar(classified_LUT17_probabilities_map))


        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'fodefopc'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_LUT17_probabilities_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_deforested_LUT17_probabilities_classified, output_map_name))
        print('classified_LUT17_probabilities_map created and stored as "fodefopc" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_deforested_LUT17_probabilities_classified)

        # mplc deforestation
        mplc_deforestation_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(17),
                                        scalar(1))

        self.mplc_deforestation_maptotal = int(maptotal(mplc_deforestation_map))

        if time_step == 1:
            self.mplc_deforestation_accumulated = 0
        self.mplc_deforestation_accumulated = self.mplc_deforestation_accumulated + self.mplc_deforestation_maptotal


        # forest conversion to other land use mplc
        if self.time_step == 1:
            if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
                if Parameters.get_presimulation_correction_step_needed() is True:
                    environment_last_time_step_map = readmap(Filepaths.file_initial_LULC_simulated_input)
                else:
                    environment_last_time_step_map = readmap(Filepaths.file_initial_LULC_input)
            elif Parameters.get_model_scenario() == 'no_conservation':
                environment_last_time_step_map = readmap(Filepaths.file_initial_LULC_simulated_for_worst_case_scenario_input)
        else:
            environment_last_time_step_map = self.mplc_environment_last_time_step

        # built the forest map of last time step
        forest_last_timestep_map = ifthenelse(environment_last_time_step_map == 8,
                                              scalar(1),
                                              scalar(self.null_mask_map))

        forest_last_timestep_map = ifthenelse(environment_last_time_step_map == 9,
                                              scalar(1),
                                              scalar(forest_last_timestep_map))

        forest_last_timestep_map = ifthen(scalar(forest_last_timestep_map) == scalar(1), # eliminate the zeros
                                          scalar(1))

        # built the current active land use types map
        active_land_use_now_map = scalar(self.null_mask_map)
        for a_LUT in Parameters.get_active_land_use_types_list(): # Parameters.get_active_land_use_types_list()
            active_land_use_now_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(a_LUT),
                                                 scalar(1),
                                                 scalar(active_land_use_now_map))

        active_land_use_now_map = ifthen(scalar(active_land_use_now_map) != scalar(0), # eliminate the zeros
                                         scalar(1))

        # only where both maps match is forest converted from the last time step
        converted_forest_map = ifthen(active_land_use_now_map == forest_last_timestep_map,
                                      scalar(1))  # show the forest that is converted

        self.converted_forest_area = int(maptotal(converted_forest_map))

        # show the singular LUTs
        LUT01_converted_forest_map = ifthen(boolean(self.most_probable_landscape_configuration_map == 1) == boolean(forest_last_timestep_map == 1),
                                            scalar(1))
        self.LUT01_converted_forest_area = int(maptotal(LUT01_converted_forest_map))

        LUT02_converted_forest_map = ifthen(
            boolean(self.most_probable_landscape_configuration_map == 2) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        self.LUT02_converted_forest_area = int(maptotal(LUT02_converted_forest_map))

        LUT03_converted_forest_map = ifthen(
            boolean(self.most_probable_landscape_configuration_map == 3) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        self.LUT03_converted_forest_area = int(maptotal(LUT03_converted_forest_map))

        LUT04_converted_forest_map = ifthen(
            boolean(self.most_probable_landscape_configuration_map == 4) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        self.LUT04_converted_forest_area = int(maptotal(LUT04_converted_forest_map))

        LUT05_converted_forest_map = ifthen(
            boolean(self.most_probable_landscape_configuration_map == 5) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        self.LUT05_converted_forest_area = int(maptotal(LUT05_converted_forest_map))



        ###########

        if self.time_step == 1:
            self.converted_forest_area_accumulated = 0
        self.converted_forest_area_accumulated = self.converted_forest_area_accumulated + self.converted_forest_area

        list_of_new_converted_forest_area.append(self.converted_forest_area)

        self.converted_forest_area_percentage_of_landscape = round(
            float((self.converted_forest_area / self.hundred_percent_area) * 100), 2)

        # classify the gif for the output in two classes
        converted_forest_map = cover(scalar(converted_forest_map), scalar(self.null_mask_map))
        classified_converted_forest_map = converted_forest_map + 1 # class 1 is the region, class 2 is the converted forest

        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'mplcfoco'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_converted_forest_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_forest_conversion,
                            output_map_name))
        print('classified_converted_forest_map created and stored as "mplcfoco" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_forest_conversion)


        print('calculating deforestation and forest conversion maps done')

        # =================================================================== #

    def construct_forest_disturbed_and_undisturbed_probability_maps_for_the_singular_LUTs(self):
        """ SH: PROBABILITY MAPS FOR SINGULAR FOREST LUTS: shows the LPB-basic calculated probability for forest disturbed and undisturbed """

        print('\nconstructing singular forest LUTs probability maps ...')

        #1) disturbed forest
        # get the according MC average map
        disturbed_forest_MC_average_map = self.dictionary_of_LUTs_MC_averages_dictionaries[8][self.time_step]

        # classify it for the output GIF
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map == scalar(0),
            scalar(1),
            scalar(self.null_mask_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map > scalar(0),
            scalar(2),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map > scalar(0.2),
            scalar(3),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map > scalar(0.4),
            scalar(4),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map > scalar(0.6),
            scalar(5),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map > scalar(0.8),
            scalar(6),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))
        classified_disturbed_forest_MC_average_probabilities_map = ifthenelse(
            disturbed_forest_MC_average_map == scalar(1),
            scalar(7),
            scalar(classified_disturbed_forest_MC_average_probabilities_map))

        # report
        pcraster_conform_map_name = 'fodiclpr'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_disturbed_forest_MC_average_probabilities_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_disturbed_probabilities_classified, output_map_name))
        print('classified_disturbed_forest_MC_average_probabilities_map created and stored as "fodiclpr" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_disturbed_probabilities_classified)

        # 1) undisturbed forest
        # get the according MC average map
        undisturbed_forest_MC_average_map = self.dictionary_of_LUTs_MC_averages_dictionaries[9][self.time_step]

        # classify it for the output GIF
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map == scalar(0),
            scalar(1),
            scalar(self.null_mask_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map > scalar(0),
            scalar(2),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map > scalar(0.2),
            scalar(3),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map > scalar(0.4),
            scalar(4),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map > scalar(0.6),
            scalar(5),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map > scalar(0.8),
            scalar(6),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))
        classified_undisturbed_forest_MC_average_probabilities_map = ifthenelse(
            undisturbed_forest_MC_average_map == scalar(1),
            scalar(7),
            scalar(classified_undisturbed_forest_MC_average_probabilities_map))

        # report
        pcraster_conform_map_name = 'founclpr'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_undisturbed_forest_MC_average_probabilities_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_undisturbed_probabilities_classified,
                            output_map_name))
        print('classified_undisturbed_forest_MC_average_probabilities_map created and stored as "founclpr" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_undisturbed_probabilities_classified)

        print('constructing singular forest LUTs probability maps done')

        # =================================================================== #

    def construct_forest_land_use_and_land_use_conflict_maps(self):
        """ SH: CONFLICT maps based on the LPB-basic."""

        print('\nconstructing forest land use conflict and land use conflict in restricted areas probability maps ...')

        if self.time_step == 1:
            if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
                if Parameters.get_presimulation_correction_step_needed() == True:
                    self.mplc_environment_last_time_step = readmap(Filepaths.file_initial_LULC_simulated_input)
                else:
                    self.mplc_environment_last_time_step = readmap(Filepaths.file_initial_LULC_input)
            elif Parameters.get_model_scenario() == 'no_conservation':
                self.mplc_environment_last_time_step = readmap(Filepaths.file_initial_LULC_simulated_for_worst_case_scenario_input)
        else:
            self.mplc_environment_last_time_step = self.mplc_environment_last_time_step

        # RESTRICTED AREAS
        restricted_areas_map = ifthen(scalar(self.static_restricted_areas_map) == scalar(1),
                                      scalar(1))
        self.restricted_areas_area = int(maptotal(restricted_areas_map))

        self.restricted_areas_area_percentage_of_landscape = round(
            float((self.restricted_areas_area / self.hundred_percent_area) * 100), 2)


        # 1) Forest Land Use Conflict in restricted areas (from LPB-basic: only the new pixels for the time step are evaluated)
        forest_land_use_conflict_probabilities_map = self.null_mask_map # initiate the file

        for a_key in self.dictionary_of_forest_land_use_conflict_files:
            if a_key == self.time_step:
                forest_land_use_conflict_probabilities_map = self.dictionary_of_forest_land_use_conflict_files[a_key]

        forest_land_use_conflict_probabilities_map = ifthen(scalar(self.static_restricted_areas_map) == scalar(1),
                                                            scalar(forest_land_use_conflict_probabilities_map)) # reduce the map to the restricted areas

        forest_land_use_conflict_probabilities_map = ifthen(scalar(forest_land_use_conflict_probabilities_map) > scalar(0),
                                                            scalar(forest_land_use_conflict_probabilities_map)) # eliminate the zeros

        self.new_pixels_of_forest_land_use_conflict_area = int(maptotal(scalar(boolean(forest_land_use_conflict_probabilities_map))))
        list_of_new_pixels_of_forest_land_use_conflict.append(self.new_pixels_of_forest_land_use_conflict_area)

        # class 1 (0 % probability) is not be shown, since it shall show the distribution in the restricted areas
        # classified_forest_land_use_conflict_probabilities_map = ifthen(
        #     forest_land_use_conflict_probabilities_map == scalar(0),
        #     scalar(1),
        #     scalar(forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map > scalar(0),
            scalar(2),
            scalar(forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map > scalar(0.2),
            scalar(3),
            scalar(classified_forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map > scalar(0.4),
            scalar(4),
            scalar(classified_forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map > scalar(0.6),
            scalar(5),
            scalar(classified_forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map > scalar(0.8),
            scalar(6),
            scalar(classified_forest_land_use_conflict_probabilities_map))
        classified_forest_land_use_conflict_probabilities_map = ifthenelse(
            forest_land_use_conflict_probabilities_map == scalar(1),
            scalar(7),
            scalar(classified_forest_land_use_conflict_probabilities_map))

        # combine it with the base map
        classified_forest_land_use_conflict_probabilities_map = cover(scalar(classified_forest_land_use_conflict_probabilities_map),
                                                                      scalar(self.region_and_restricted_areas_base_map))

        pcraster_conform_map_name = 'foluconf'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
        report(classified_forest_land_use_conflict_probabilities_map, os.path.join(Filepaths.folder_CONFLICT_mplc_forest_land_use, output_map_name))
        print('classified_forest_land_use_conflict_probabilities_map created and stored as "foluconf" in:', Filepaths.folder_CONFLICT_mplc_forest_land_use)

        # 2) Land Use Conflict in restricted areas (from LPB-basic: only the new pixels for the time step are evaluated)
        for a_key in self.dictionary_of_land_use_conflict_files:
            if a_key == self.time_step:
                land_use_conflict_probabilities_map = self.dictionary_of_land_use_conflict_files[a_key]

        land_use_conflict_probabilities_map = ifthen(scalar(self.static_restricted_areas_map) == scalar(1),
                                                     scalar(land_use_conflict_probabilities_map)) # reduce the map to the restricted areas

        land_use_conflict_probabilities_map = ifthen(scalar(land_use_conflict_probabilities_map) > scalar(0),
                                                     scalar(land_use_conflict_probabilities_map)) # eliminate the 0s

        self.new_pixels_of_land_use_conflict_area = int(maptotal(scalar(boolean(land_use_conflict_probabilities_map))))
        list_of_new_pixels_of_land_use_conflict.append(self.new_pixels_of_land_use_conflict_area)

        # Class 1 is not to be displayed, since it shall show the distribution within the restricted areas
        # classified_land_use_conflict_probabilities_map = ifthenelse(
        #     land_use_conflict_probabilities_map == scalar(0),
        #     scalar(1),
        #     scalar(land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map > scalar(0),
            scalar(2),
            scalar(land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map > scalar(0.2),
            scalar(3),
            scalar(classified_land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map > scalar(0.4),
            scalar(4),
            scalar(classified_land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map > scalar(0.6),
            scalar(5),
            scalar(classified_land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map > scalar(0.8),
            scalar(6),
            scalar(classified_land_use_conflict_probabilities_map))
        classified_land_use_conflict_probabilities_map = ifthenelse(
            land_use_conflict_probabilities_map == scalar(1),
            scalar(7),
            scalar(classified_land_use_conflict_probabilities_map))

        # combine it with the basemap
        classified_land_use_conflict_probabilities_map = cover(
            scalar(classified_land_use_conflict_probabilities_map),
            scalar(self.region_and_restricted_areas_base_map))

        pcraster_conform_map_name = 'luconf'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_land_use_conflict_probabilities_map,
               os.path.join(Filepaths.folder_CONFLICT_mplc_land_use, output_map_name))
        print(
            'classified_land_use_conflict_probabilities_map created and stored as "luconf" in:',
            Filepaths.folder_CONFLICT_mplc_land_use)

        # count the total of potential conflict pixels in the most probable map
        all_land_use_in_restricted_areas_in_mplc_map = ifthen(scalar(self.static_restricted_areas_map) == scalar(1),
                                                              nominal(self.most_probable_landscape_configuration_map))

        active_land_use_in_restricted_areas_map = self.region_and_restricted_areas_base_map # class 8 (region) and class 9 (restricted areas)

        # LUT01
        boolean_LUT01_mplc_in_restricted_areas_map = ifthen(scalar(all_land_use_in_restricted_areas_in_mplc_map) == scalar(1),
                                                            boolean(1))

        active_land_use_in_restricted_areas_map = cover(scalar(boolean_LUT01_mplc_in_restricted_areas_map), scalar(active_land_use_in_restricted_areas_map)) # class 1

        self.LUT01_mplc_in_restricted_areas_area = int(maptotal(scalar(boolean_LUT01_mplc_in_restricted_areas_map)))
        dictionary_of_accumulated_land_use_in_restricted_areas[1][self.time_step] = self.LUT01_mplc_in_restricted_areas_area

        self.percentage_of_landscape_LUT01_in_restricted_areas = round(
            float((self.LUT01_mplc_in_restricted_areas_area / self.hundred_percent_area) * 100), 2)

        # LUT02
        boolean_LUT02_mplc_in_restricted_areas_map = ifthen(
            scalar(all_land_use_in_restricted_areas_in_mplc_map) == scalar(2),
            boolean(1))

        active_land_use_in_restricted_areas_map = cover((scalar(boolean_LUT02_mplc_in_restricted_areas_map) + scalar(1)), # class 2
                                                        scalar(active_land_use_in_restricted_areas_map))

        self.LUT02_mplc_in_restricted_areas_area = int(maptotal(scalar(boolean_LUT02_mplc_in_restricted_areas_map)))
        dictionary_of_accumulated_land_use_in_restricted_areas[2][self.time_step] = self.LUT02_mplc_in_restricted_areas_area

        self.percentage_of_landscape_LUT02_in_restricted_areas = round(
            float((self.LUT02_mplc_in_restricted_areas_area / self.hundred_percent_area) * 100), 2)

        # LUT03
        boolean_LUT03_mplc_in_restricted_areas_map = ifthen(
            scalar(all_land_use_in_restricted_areas_in_mplc_map) == scalar(3),
            boolean(1))

        active_land_use_in_restricted_areas_map = cover(
            (scalar(boolean_LUT03_mplc_in_restricted_areas_map) + scalar(2)), # class 3
            scalar(active_land_use_in_restricted_areas_map))

        self.LUT03_mplc_in_restricted_areas_area = int(maptotal(scalar(boolean_LUT03_mplc_in_restricted_areas_map)))
        dictionary_of_accumulated_land_use_in_restricted_areas[3][self.time_step] = self.LUT03_mplc_in_restricted_areas_area

        self.percentage_of_landscape_LUT03_in_restricted_areas = round(
            float((self.LUT03_mplc_in_restricted_areas_area / self.hundred_percent_area) * 100), 2)

        #LUT04
        boolean_LUT04_mplc_in_restricted_areas_map = ifthen(
            scalar(all_land_use_in_restricted_areas_in_mplc_map) == scalar(4),
            boolean(1))

        active_land_use_in_restricted_areas_map = cover(
            (scalar(boolean_LUT04_mplc_in_restricted_areas_map) + scalar(3)),  # class 4
            scalar(active_land_use_in_restricted_areas_map))

        self.LUT04_mplc_in_restricted_areas_area = int(maptotal(scalar(boolean_LUT04_mplc_in_restricted_areas_map)))
        dictionary_of_accumulated_land_use_in_restricted_areas[4][self.time_step] = self.LUT04_mplc_in_restricted_areas_area

        self.percentage_of_landscape_LUT04_in_restricted_areas = round(
            float((self.LUT04_mplc_in_restricted_areas_area / self.hundred_percent_area) * 100), 2)

        # LUT05
        boolean_LUT05_mplc_in_restricted_areas_map = ifthen(
            scalar(all_land_use_in_restricted_areas_in_mplc_map) == scalar(5),
            boolean(1))

        active_land_use_in_restricted_areas_map = cover(
            (scalar(boolean_LUT05_mplc_in_restricted_areas_map) + scalar(4)),  # class 5
            scalar(active_land_use_in_restricted_areas_map))

        self.LUT05_mplc_in_restricted_areas_area = int(maptotal(scalar(boolean_LUT05_mplc_in_restricted_areas_map)))
        dictionary_of_accumulated_land_use_in_restricted_areas[5][self.time_step] = self.LUT05_mplc_in_restricted_areas_area

        self.percentage_of_landscape_LUT05_in_restricted_areas = round(
            float((self.LUT05_mplc_in_restricted_areas_area / self.hundred_percent_area) * 100), 2)

        # report
        pcraster_conform_map_name = 'mplclura'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(active_land_use_in_restricted_areas_map,
               os.path.join(Filepaths.folder_CONFLICT_mplc_active_land_use, output_map_name))
        print(
            'active_land_use_in_restricted_areas_map created and stored as "mplclura" in:',
            Filepaths.folder_CONFLICT_mplc_active_land_use)

        # NEW IN THIS TIME STEP
        all_land_use_in_restricted_areas_in_mplc_last_time_step_map = ifthen(scalar(self.static_restricted_areas_map) == scalar(1),
                                                                             nominal(self.mplc_environment_last_time_step))

        # LUT01
        LUT01_in_restricted_areas_last_time_step_map = ifthenelse(scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(1),
                                                                  scalar(1),
                                                                  scalar(self.null_mask_map))
        LUT01_new_in_restricted_areas_map = ifthenelse((scalar(LUT01_in_restricted_areas_last_time_step_map) == 1) == (scalar(boolean_LUT01_mplc_in_restricted_areas_map) == 1),
                                                       scalar(0),
                                                       scalar(boolean_LUT01_mplc_in_restricted_areas_map))
        self.LUT01_mplc_new_in_restricted_areas_area = int(maptotal(LUT01_new_in_restricted_areas_map))

        # LUT02
        LUT02_in_restricted_areas_last_time_step_map = ifthenelse(
            scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(2),
            scalar(1),
            scalar(self.null_mask_map))
        LUT02_new_in_restricted_areas_map = ifthenelse((scalar(LUT02_in_restricted_areas_last_time_step_map) == 1) == (
                    scalar(boolean_LUT02_mplc_in_restricted_areas_map) == 1),
                                                       scalar(0),
                                                       scalar(boolean_LUT02_mplc_in_restricted_areas_map))
        self.LUT02_mplc_new_in_restricted_areas_area = int(maptotal(LUT02_new_in_restricted_areas_map))

        # LUT03
        LUT03_in_restricted_areas_last_time_step_map = ifthenelse(
            scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(3),
            scalar(1),
            scalar(self.null_mask_map))
        LUT03_new_in_restricted_areas_map = ifthenelse((scalar(LUT03_in_restricted_areas_last_time_step_map) == 1) == (
                    scalar(boolean_LUT03_mplc_in_restricted_areas_map) == 1),
                                                       scalar(0),
                                                       scalar(boolean_LUT03_mplc_in_restricted_areas_map))
        self.LUT03_mplc_new_in_restricted_areas_area = int(maptotal(LUT03_new_in_restricted_areas_map))

        # LUT04
        LUT04_in_restricted_areas_last_time_step_map = ifthenelse(
            scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(4),
            scalar(1),
            scalar(self.null_mask_map))
        LUT04_new_in_restricted_areas_map = ifthenelse((scalar(LUT04_in_restricted_areas_last_time_step_map) == 1) == (
                    scalar(boolean_LUT04_mplc_in_restricted_areas_map) == 1),
                                                       scalar(0),
                                                       scalar(boolean_LUT04_mplc_in_restricted_areas_map))
        self.LUT04_mplc_new_in_restricted_areas_area = int(maptotal(LUT04_new_in_restricted_areas_map))

        # LUT05
        LUT05_in_restricted_areas_last_time_step_map = ifthenelse(
            scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(5),
            scalar(1),
            scalar(self.null_mask_map))
        LUT05_new_in_restricted_areas_map = ifthenelse((scalar(LUT05_in_restricted_areas_last_time_step_map) == 1) == (
                    scalar(boolean_LUT05_mplc_in_restricted_areas_map) == 1),
                                                       scalar(0),
                                                       scalar(boolean_LUT05_mplc_in_restricted_areas_map))
        self.LUT05_mplc_new_in_restricted_areas_area = int(maptotal(LUT05_new_in_restricted_areas_map))

        # NEW IN RESTRICTED AREAS ON FORMER FOREST PIXELS
        forest_pixels_disturbed_last_time_step_map = ifthen(scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(8),
                                                            scalar(1))
        forest_pixels_undisturbed_last_time_step_map = ifthen(
            scalar(all_land_use_in_restricted_areas_in_mplc_last_time_step_map) == scalar(9),
            scalar(1))
        forest_pixels_last_time_step_map = cover(forest_pixels_disturbed_last_time_step_map, forest_pixels_undisturbed_last_time_step_map)

        all_land_use_in_restricted_areas_on_former_forest_pixels_map = ifthen(scalar(forest_pixels_last_time_step_map) == scalar(1),
                                                                              scalar(self.most_probable_landscape_configuration_map))

        # LUT01
        LUT01_mplc_new_on_former_forest_pixel_map = ifthen(all_land_use_in_restricted_areas_on_former_forest_pixels_map == 1,
                                                           scalar(1))
        self.LUT01_mplc_new_on_former_forest_pixel_area = int(maptotal(LUT01_mplc_new_on_former_forest_pixel_map))

        # LUT02
        LUT02_mplc_new_on_former_forest_pixel_map = ifthen(
            all_land_use_in_restricted_areas_on_former_forest_pixels_map == 2,
            scalar(1))
        self.LUT02_mplc_new_on_former_forest_pixel_area = int(maptotal(LUT02_mplc_new_on_former_forest_pixel_map))

        # LUT03
        LUT03_mplc_new_on_former_forest_pixel_map = ifthen(
            all_land_use_in_restricted_areas_on_former_forest_pixels_map == 3,
            scalar(1))
        self.LUT03_mplc_new_on_former_forest_pixel_area = int(maptotal(LUT03_mplc_new_on_former_forest_pixel_map))

        # LUT04
        LUT04_mplc_new_on_former_forest_pixel_map = ifthen(
            all_land_use_in_restricted_areas_on_former_forest_pixels_map == 4,
            scalar(1))
        self.LUT04_mplc_new_on_former_forest_pixel_area = int(maptotal(LUT04_mplc_new_on_former_forest_pixel_map))

        # LUT05
        LUT05_mplc_new_on_former_forest_pixel_map = ifthen(
            all_land_use_in_restricted_areas_on_former_forest_pixels_map == 5,
            scalar(1))
        self.LUT05_mplc_new_on_former_forest_pixel_area = int(maptotal(LUT05_mplc_new_on_former_forest_pixel_map))

        self.total_of_land_use_in_restricted_areas_area = self.LUT01_mplc_in_restricted_areas_area + \
                                                          self.LUT02_mplc_in_restricted_areas_area + \
                                                          self.LUT03_mplc_in_restricted_areas_area + \
                                                          self.LUT04_mplc_in_restricted_areas_area + \
                                                          self.LUT05_mplc_in_restricted_areas_area

        self.total_of_land_use_in_restricted_areas_area_percentage_of_restricted_area = round(
            float((self.total_of_land_use_in_restricted_areas_area / self.restricted_areas_area) * 100), 2)

        self.total_of_new_land_use_in_restricted_areas_area = self.LUT01_mplc_new_in_restricted_areas_area + \
                                                              self.LUT02_mplc_new_in_restricted_areas_area + \
                                                              self.LUT03_mplc_new_in_restricted_areas_area + \
                                                              self.LUT04_mplc_new_in_restricted_areas_area + \
                                                              self.LUT05_mplc_new_in_restricted_areas_area

        self.total_of_new_land_use_in_restricted_areas_area_percentage_of_restricted_area = round(
            float((self.total_of_new_land_use_in_restricted_areas_area / self.restricted_areas_area) * 100), 2)

        self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area = self.LUT01_mplc_new_on_former_forest_pixel_area + \
                                                                                      self.LUT02_mplc_new_on_former_forest_pixel_area + \
                                                                                      self.LUT03_mplc_new_on_former_forest_pixel_area + \
                                                                                      self.LUT04_mplc_new_on_former_forest_pixel_area + \
                                                                                      self.LUT05_mplc_new_on_former_forest_pixel_area

        self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area_percentage_of_restricted_area = round(
            float((self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area / self.restricted_areas_area) * 100), 2)

        # DISTURBED AND UNDISTURBED IN RESTRICTED AREAS
        disturbed_in_restricted_areas_map = ifthen(all_land_use_in_restricted_areas_on_former_forest_pixels_map == 8,
                                                   scalar(1))
        self.mplc_disturbed_in_restricted_areas_area = int(maptotal(disturbed_in_restricted_areas_map))

        self.mplc_disturbed_in_restricted_areas_percentage_of_restricted_area = round(
            float((self.mplc_disturbed_in_restricted_areas_area/ self.restricted_areas_area) * 100),
            2)

        undisturbed_in_restricted_areas_map = ifthen(
            all_land_use_in_restricted_areas_on_former_forest_pixels_map == 9,
            scalar(1))
        self.mplc_undisturbed_in_restricted_areas_area = int(maptotal(undisturbed_in_restricted_areas_map))

        self.mplc_undisturbed_in_restricted_areas_percentage_of_restricted_area = round(
            float((self.mplc_undisturbed_in_restricted_areas_area / self.restricted_areas_area) * 100),
            2)


        print('constructing forest land use conflict and land use conflict in restricted areas probability maps done')

        # =================================================================== #

    def derive_mplc_disturbed_and_undisturbed_net_and_gross_forest(self):
        # SH: most probable landscape configuration for disturbed and undisturbed forest in total and for net forest (COMBINED GIF)

        print('\nderiving the most probable landscape configuration for net and gross disturbed and undisturbed forest ...')

        # 1) in total
        true_forest_mplc_map = ifthen(scalar(self.null_mask_map) == scalar(0),
                                      scalar(1)) # the region is the first category

        true_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                          scalar(2), # the second category for the GIF = disturbed forest
                                          scalar(true_forest_mplc_map))

        true_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                                          scalar(3), # the third category for the GIF 0 = undisturbed forest
                                          scalar(true_forest_mplc_map))

        environment_in_net_forest_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                                   scalar(self.most_probable_landscape_configuration_map),
                                                   scalar(self.null_mask_map))

        true_forest_mplc_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(8),
                                          scalar(4), # fourth category is disturbed in net forest
                                          scalar(true_forest_mplc_map))

        true_forest_mplc_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(9),
                                          scalar(5),  # fifth category is undisturbed in net forest
                                          scalar(true_forest_mplc_map))

        pcraster_conform_map_name = 'mplctrfo'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(true_forest_mplc_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_fud_mplc, output_map_name))
        print('true_forest_mplc_map created and stored as "mplctrfo" in:', Filepaths.folder_FOREST_PROBABILITY_MAPS_fud_mplc)

        # classified probabilities
        true_forest_mplc_probabilities_classified_map = ifthenelse(scalar(true_forest_mplc_map) > scalar(1),
                                                                   scalar(self.classified_most_probable_landscape_configuration_probabilities_map),
                                                                   scalar(8))

        pcraster_conform_map_name = 'mplctfpr'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(true_forest_mplc_probabilities_classified_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified, output_map_name))
        print('true_forest_mplc_probabilities_classified_map created and stored as "mplctfpr" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified )

        # SH: gross forest: consisting of net_forest, other forest disturbed an undisturbed, agroforestry and plantations
        # include only if user defined
        list_of_gross_forest_LUTs = Parameters.get_gross_forest_LUTs_list()

        if 8 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                           scalar(3), # category other disturbed forest
                                           scalar(self.null_mask_map))

        if 9 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                                           scalar(3),  # category  other undisturbed forest
                                           scalar(gross_forest_mplc_map))

        if 4 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(4),
                                           scalar(4),  # category agroforestry
                                           scalar(gross_forest_mplc_map))

        if 5 in list_of_gross_forest_LUTs:
            gross_forest_mplc_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(5),
                                               scalar(5),  # category plantation
                                               scalar(gross_forest_mplc_map))

        gross_forest_mplc_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                           scalar(2),  # category net forest
                                           scalar(gross_forest_mplc_map))

        gross_forest_mplc_map = ifthenelse(scalar(gross_forest_mplc_map) == scalar(0),
                                           scalar(1),  # category region
                                           scalar(gross_forest_mplc_map))

        self.gross_forest_mplc_map = gross_forest_mplc_map

        # log file variables
        self.gross_forest_mplc_area = int(maptotal(scalar(boolean(gross_forest_mplc_map != 1))))
        self.gross_forest_mplc_percentage_of_landscape = round(
            float((self.gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        self.gross_mplc_disturbed_forest_area = int(maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 8))))
        self.gross_mplc_disturbed_forest_percentage_of_landscape = round(
            float((self.gross_mplc_disturbed_forest_area / self.hundred_percent_area) * 100), 2)

        self.gross_mplc_undisturbed_forest_area = int(maptotal(scalar(boolean(self.most_probable_landscape_configuration_map == 9))))
        self.gross_mplc_undisturbed_forest_percentage_of_landscape = round(
            float((self.gross_mplc_undisturbed_forest_area / self.hundred_percent_area) * 100), 2)


        pcraster_conform_map_name = 'mplcfng'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(gross_forest_mplc_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_fng_mplc, output_map_name))
        print(
            'gross_forest_mplc_map created and stored as "mplcfng" in:',
            Filepaths.folder_FOREST_PROBABILITY_MAPS_fng_mplc )

        # classified probabilities
        gross_forest_mplc_probabilities_classified_map = ifthenelse(scalar(gross_forest_mplc_map) > scalar(1),
                                                                   scalar(self.classified_most_probable_landscape_configuration_probabilities_map),
                                                                   scalar(8))

        pcraster_conform_map_name = 'mplcfngp'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(gross_forest_mplc_probabilities_classified_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_fng_mplc_probabilities_classified, output_map_name))
        print(
            'gross_forest_mplc_probabilities_classified_map created and stored as "mplcfngp" in:',
            Filepaths.folder_FOREST_PROBABILITY_MAPS_fng_mplc_probabilities_classified)



        print('deriving the most probable landscape configuration for net and gross disturbed and undisturbed forest done')

        # =================================================================== #

    def derive_mplc_gross_and_net_forest_impacted_by_anthropogenic_impact_buffer(self):
        """ SH: applying the LPB-basic deterministic anthropogenic impact buffer."""

        print('\nderiving impacted disturbed forest from the deterministic LPB-basic impact buffer ...')

        for a_key in self.dictionary_of_anthropogenic_impact_buffer_files:
            if a_key == self.time_step:
                self.anthropogenic_impact_buffer_map = self.dictionary_of_anthropogenic_impact_buffer_files[a_key]

        self.anthropogenic_impact_buffer_area = int(maptotal(scalar(self.anthropogenic_impact_buffer_map)))

        self.percentage_of_landscape_anthropogenic_impact_buffer = round(
            float((self.anthropogenic_impact_buffer_area / self.hundred_percent_area) * 100), 2)

        # gross forest
        gross_forest_disturbed_impacted_by_anthropogenic_features_map = ifthenelse(scalar(self.anthropogenic_impact_buffer_map) == scalar(1),
                                                                         boolean(self.most_probable_landscape_configuration_map == 8),
                                                                         boolean(self.null_mask_map))

        gross_forest_undisturbed_impacted_by_anthropogenic_features_map = ifthenelse(
            scalar(self.anthropogenic_impact_buffer_map) == scalar(1),
            boolean(self.most_probable_landscape_configuration_map == 9),
            boolean(self.null_mask_map))

        gross_forest_impacted_by_anthropogenic_features_map = cover(boolean(gross_forest_disturbed_impacted_by_anthropogenic_features_map),
                                                                    boolean(gross_forest_undisturbed_impacted_by_anthropogenic_features_map))

        self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area = int(maptotal(scalar(gross_forest_impacted_by_anthropogenic_features_map)))
        self.true_gross_forest_impacted_by_anthropogenic_features_mplc_percentage_of_landscape = round(
            float((self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area / self.hundred_percent_area) * 100), 2)

        # net forest (all impacted forest is already LUT08)
        net_forest_impacted_by_anthropogenic_features_map = ifthenelse(
            scalar(self.anthropogenic_impact_buffer_map) == scalar(1),
            boolean(self.net_forest_mplc_map),
            boolean(self.null_mask_map))

        self.true_net_forest_impacted_by_anthropogenic_features_mplc_area = int(maptotal(scalar(net_forest_impacted_by_anthropogenic_features_map)))
        self.true_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = round(
            float((self.true_net_forest_impacted_by_anthropogenic_features_mplc_area / self.gross_forest_mplc_area) * 100), 2)

        print('deriving impacted disturbed forest from the deterministic LPB-basic impact buffer done')


        # =================================================================== #

    def derive_mplc_nominal_undisturbed_forest_habitat(self):
        """ Apply the disturbed fringe calculation to the mplc landscape in case some mplc pixels at forest fringe are undisturbed.
        Derive the nominal undisturbed forest habitat for net, gross forest and if BAU for forest in restricted areas."""

        print('\nderiving undisturbed forest core/center habitat ...')

        # 1)
        all_forest_cells_map = ifthenelse(self.most_probable_landscape_configuration_map == 8,  # disturbed forest
                                          scalar(1),
                                          scalar(self.null_mask_map))

        all_forest_cells_map = ifthenelse(self.most_probable_landscape_configuration_map == 9,  # undisturbed forest
                                          scalar(1),
                                          scalar(all_forest_cells_map))

        only_forest_cells_map = ifthen(all_forest_cells_map == 1,
                                       all_forest_cells_map)

        # get the forest fringe
        scalar_self = scalar(only_forest_cells_map)
        # SH: Count cells within a 3x3 window to determine the forest fringe cells
        window_length = 3 * Parameters.get_cell_length_in_m()  # 9(-1) cells if not forest fringe
        number_neighbors_forest_map = windowtotal(scalar_self, window_length) - scalar_self

        forest_fringe_map = ifthen(scalar(number_neighbors_forest_map) < scalar(8),
                                   # forest fringes are determined by missing pixels in the window (less than 9 (-1) present)
                                   scalar(1))

        new_disturbed_forest_fringe = ifthen(forest_fringe_map > 0,
                                             nominal(8))

        self.mplc_disturbed_forest_fringe_area = int(maptotal(scalar(boolean(new_disturbed_forest_fringe))))
        self.mplc_disturbed_forest_fringe_percentage_of_landscape = round(
            float((self.mplc_disturbed_forest_fringe_area / self.hundred_percent_area) * 100), 2)

        disturbed_environment_map = cover(nominal(new_disturbed_forest_fringe), nominal(self.most_probable_landscape_configuration_map))

        undisturbed_environment_map = ifthen(disturbed_environment_map == 9,
                                             scalar(1))

        self.mplc_undisturbed_forest_habitat_area = int(maptotal(undisturbed_environment_map))
        self.mplc_undisturbed_forest_habitat_percentage_of_landscape = round(
            float((self.mplc_undisturbed_forest_habitat_area / self.hundred_percent_area) * 100), 2)

        # 2) show the area in context of net, gross forest and restricted areas (BAU: current; worst case: former))

        gross_undisturbed_forest_habitat_map = undisturbed_environment_map

        gross_plus_net_undisturbed_forest_habitat_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                                                   scalar(2), # class 2 net forest
                                                                   scalar(gross_undisturbed_forest_habitat_map)) # class 1 gross forest

        gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map = ifthen(self.static_restricted_areas_map == 1,
                                                                                boolean(gross_plus_net_undisturbed_forest_habitat_map))

        gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map = ifthen(scalar(gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map) == scalar(1),
                                                                                scalar(3)) # class 3 undisturbed forest in restricted areas

        gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map = cover(scalar(gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map),
                                                                               scalar(gross_plus_net_undisturbed_forest_habitat_map)) # combine class 1,2 3

        mplc_nominal_undisturbed_forest_habitat_map = cover(scalar(gross_plus_net_plus_forest_undisturbed_in_restricted_areas_map),
                                                          # class 1 gross, class 2 net, class 3 restricted areas
                                                          scalar(
                                                              self.region_and_restricted_areas_base_map))  # class 8 region class 9 restricted areas

        # report the map
        time_step = self.time_step
        pcraster_conform_map_name = 'mplchaun'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(mplc_nominal_undisturbed_forest_habitat_map,
               os.path.join(
                   Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_forest_undisturbed_habitat,
                   output_map_name))
        print(
            'mplc_nominal_undisturbed_forest_habitat_map created and stored as "mplchaun" in:',
            Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_forest_undisturbed_habitat)

        print('deriving nominal undisturbed forest habitat done')

        # =================================================================== #

    def derive_local_and_regional_land_use_amounts(self):
        """ SH: deriving local land use for settlements and regional excess. """

        print('\nderiving local land use for settlements and regional excess ...')

        for a_key in self.dictionary_of_settlements_files:
            if a_key == self.time_step:
                settlements_map = self.dictionary_of_settlements_files[a_key]

        # get the draw areas of settlements
        spread_map = spreadmaxzone(boolean(settlements_map), 0, 1,
                                   Parameters.get_regional_mean_impact_of_settlements_distance_in_m())
        settlements_impact_buffer_map = ifthenelse(scalar(spread_map) > scalar(0),
                                                   boolean(1),
                                                   boolean(self.null_mask_map))

        # derive for each active LUT the amount of cells WITHIN the local radius and the regional excess
        # LUT01
        settlements_local_LUT01_map = ifthen(scalar(settlements_impact_buffer_map) == scalar(1),
                                             self.most_probable_landscape_configuration_map == 1)

        self.settlements_local_LUT01_area = int(maptotal(scalar(boolean(settlements_local_LUT01_map))))

        self.percentage_of_landscape_settlements_local_LUT01 = round(
            float((self.settlements_local_LUT01_area / self.hundred_percent_area) * 100), 2)

        self.regional_excess_LUT01 = self.allocated_pixels_LUT01 - self.settlements_local_LUT01_area

        self.percentage_of_landscape_regional_excess_LUT01 = round(
            float((self.regional_excess_LUT01 / self.hundred_percent_area) * 100), 2)

        # LUT02
        settlements_local_LUT02_map = ifthen(scalar(settlements_impact_buffer_map) == scalar(1),
                                             self.most_probable_landscape_configuration_map == 2)

        self.settlements_local_LUT02_area = int(maptotal(scalar(boolean(settlements_local_LUT02_map))))

        self.percentage_of_landscape_settlements_local_LUT02 = round(
            float((self.settlements_local_LUT02_area / self.hundred_percent_area) * 100), 2)

        self.regional_excess_LUT02 = self.allocated_pixels_LUT02 - self.settlements_local_LUT02_area

        self.percentage_of_landscape_regional_excess_LUT02 = round(
            float((self.regional_excess_LUT02 / self.hundred_percent_area) * 100), 2)

        # LUT03
        settlements_local_LUT03_map = ifthen(scalar(settlements_impact_buffer_map) == scalar(1),
                                             self.most_probable_landscape_configuration_map == 3)

        self.settlements_local_LUT03_area = int(maptotal(scalar(boolean(settlements_local_LUT03_map))))

        self.percentage_of_landscape_settlements_local_LUT03 = round(
            float((self.settlements_local_LUT03_area / self.hundred_percent_area) * 100), 2)

        self.regional_excess_LUT03 = self.allocated_pixels_LUT03 - self.settlements_local_LUT03_area

        self.percentage_of_landscape_regional_excess_LUT03 = round(
            float((self.regional_excess_LUT03 / self.hundred_percent_area) * 100), 2)

        # LUT04
        settlements_local_LUT04_map = ifthen(scalar(settlements_impact_buffer_map) == scalar(1),
                                             self.most_probable_landscape_configuration_map == 4)

        self.settlements_local_LUT04_area = int(maptotal(scalar(boolean(settlements_local_LUT04_map))))

        self.percentage_of_landscape_settlements_local_LUT04 = round(
            float((self.settlements_local_LUT04_area / self.hundred_percent_area) * 100), 2)

        self.regional_excess_LUT04 = self.allocated_pixels_LUT04 - self.settlements_local_LUT04_area

        self.percentage_of_landscape_regional_excess_LUT04 = round(
            float((self.regional_excess_LUT04 / self.hundred_percent_area) * 100), 2)

        # LUT05
        settlements_local_LUT05_map = ifthen(scalar(settlements_impact_buffer_map) == scalar(1),
                                             self.most_probable_landscape_configuration_map == 5)

        self.settlements_local_LUT05_area = int(maptotal(scalar(boolean(settlements_local_LUT05_map))))

        self.percentage_of_landscape_settlements_local_LUT05 = round(
            float((self.settlements_local_LUT05_area / self.hundred_percent_area) * 100), 2)

        self.regional_excess_LUT05 = self.allocated_pixels_LUT05 - self.settlements_local_LUT05_area

        self.percentage_of_landscape_regional_excess_LUT05 = round(
            float((self.regional_excess_LUT05 / self.hundred_percent_area) * 100), 2)

        print('deriving local land use for settlements and regional excess done')

        # =================================================================== #

    def derive_forest_degradation_and_regeneration(self):
        """ SH: deriving the most probable landscape configuration of forest degradation and regeneration."""

        print('\nderiving the most probable landscape configuration of forest degradation and regeneration ...')

        time_step = self.time_step

        # SH: FOREST DEGRADATION AND REGENERATION PROBABILITIES
        range_of_degradation_and_regeneration_classes = range(1, (8 + 1))
        list_of_degradation_and_regeneration_maps_for_the_time_step = []
        for a_type in range_of_degradation_and_regeneration_classes:
            a_degradation_or_regeneration_map = self.dictionary_of_degradation_and_regeneration_dictionaries[a_type][
                self.time_step]
            list_of_degradation_and_regeneration_maps_for_the_time_step.append(a_degradation_or_regeneration_map)

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
        # THE KEY TO LPB-mplc
        # compare the maps by highest probability per pixel and note the according probability
        self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            (max(*list_of_degradation_and_regeneration_maps_for_the_time_step) > scalar(0)),
            max(*list_of_degradation_and_regeneration_maps_for_the_time_step),
            scalar(self.null_mask_map))
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

        # now reclassify this map to achieve 7 classes for the output GIF
        # classify the values in 7 classes:
        # class 1 = 0 %
        # class 2 = >0 to 20 %
        # class 3 = >20 to 40 %
        # class 4 = >40 to 60 %
        # class 5 = >60 to 80 %
        # class 6 = >80 to <100 %
        # class 7 = 100 %

        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map == scalar(0),
            scalar(1),
            scalar(self.null_mask_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map > scalar(0),
            scalar(2),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map > scalar(0.2),
            scalar(3),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map > scalar(0.4),
            scalar(4),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map > scalar(0.6),
            scalar(5),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map > scalar(0.8),
            scalar(6),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))
        classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map = ifthenelse(
            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map == scalar(1),
            scalar(7),
            scalar(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map))

        # report the map
        pcraster_conform_map_name = 'mplcfdrp'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration_probabilities_classified, output_map_name))
        print('classified_most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map created and stored as "mplcfdrp" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration_probabilities_classified)

        # 1.2) the nominal map
        # get the nominal land use types for the pixels with highest probability
        self.most_probable_landscape_configuration_degradation_and_regeneration_map = nominal(self.null_mask_map)

        for a_name, dictionary_of_degradation_and_regeneration_probability_maps in self.dictionary_of_degradation_and_regeneration_dictionaries.items():
            degradation_or_regeneration_probability_map_per_time_step_i = \
            dictionary_of_degradation_and_regeneration_probability_maps[self.time_step]

            degradation_or_regeneration_probability_map_per_time_step_i = ifthen(scalar(degradation_or_regeneration_probability_map_per_time_step_i) > scalar(0),
                                                                                 scalar(degradation_or_regeneration_probability_map_per_time_step_i))

            temporal_landscape_map = ifthen(degradation_or_regeneration_probability_map_per_time_step_i ==
                                            self.most_probable_landscape_configuration_degradation_and_regeneration_probabilities_map,
                                            nominal(a_name))
            self.most_probable_landscape_configuration_degradation_and_regeneration_map = cover(temporal_landscape_map,
                                                                                               self.most_probable_landscape_configuration_degradation_and_regeneration_map)
            self.most_probable_landscape_configuration_degradation_and_regeneration_map = cover(nominal(self.most_probable_landscape_configuration_degradation_and_regeneration_map), nominal(self.null_mask_map))

        # classified map for GIF of degradation and regeneration
        # region base map class 9 black
        # gross forest base map class 10 grey
        gross_forest_and_region_map = ifthenelse(scalar(self.gross_forest_mplc_map) > scalar(1), # get the data where gross forest is
                                                 scalar(10), # classify it as class 10
                                                 scalar(self.null_mask_map) + scalar(9)) # the rest of the region is class 9
        self.most_probable_landscape_configuration_degradation_and_regeneration_map = ifthenelse(scalar(self.most_probable_landscape_configuration_degradation_and_regeneration_map) > scalar(0), # where data ...
                                                                                                 scalar(self.most_probable_landscape_configuration_degradation_and_regeneration_map), #... is display the nominal category
                                                                                                 scalar(gross_forest_and_region_map)) # else display the region and gross forest

        pcraster_conform_map_name = 'mplcfdrn'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.most_probable_landscape_configuration_degradation_and_regeneration_map,
               os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration, output_map_name))
        print('self.most_probable_landscape_configuration_degradation_and_regeneration_map created and stored as "mplcfdrn" in:',
              Filepaths.folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration)

        # log file variables
        # for gross forest:
        self.mplc_degradation_and_regeneration_gross_forest_map = self.most_probable_landscape_configuration_degradation_and_regeneration_map
        # for net forest
        self.mplc_degradation_and_regeneration_net_forest_map = ifthenelse(boolean(self.net_forest_mplc_map),
                                                                           self.most_probable_landscape_configuration_degradation_and_regeneration_map,
                                                                           scalar(self.null_mask_map))


        # degradation low = 1   - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 1
        # degradation moderate = 2 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 2
        # degradation severe = 3 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 3
        # degradation absolute = 4 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 4

        # regeneration low = 5 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 5
        # regeneration medium = 6 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 6
        # regeneration high = 7 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 7
        # regeneration full = 8 - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 8

        # FOREST DEGRADATION/REGENERATION
        # 1) degradation
        # degradation low - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 1
        # self.low_degradation_net_forest_mplc_area
        self.low_degradation_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 1))))
        # self.low_degradation_net_forest_mplc_percentage_of_landscape
        self.low_degradation_net_forest_mplc_percentage_of_landscape = round(
            float((self.low_degradation_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.low_degradation_gross_forest_mplc_area
        self.low_degradation_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 1))))
        # self.low_degradation_gross_forest_mplc_percentage_of_landscape
        self.low_degradation_gross_forest_mplc_percentage_of_landscape = round(
            float((self.low_degradation_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # degradation moderate - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 2
        # self.moderate_degradation_net_forest_mplc_area
        self.moderate_degradation_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 2))))
        # self.moderate_degradation_net_forest_mplc_percentage_of_landscape
        self.moderate_degradation_net_forest_mplc_percentage_of_landscape = round(
            float((self.low_degradation_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.moderate_degradation_gross_forest_mplc_area
        self.moderate_degradation_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 2))))
        # self.moderate_degradation_gross_forest_mplc_percentage_of_landscape
        self.moderate_degradation_gross_forest_mplc_percentage_of_landscape = round(
            float((self.moderate_degradation_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # degradation severe - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 3
        # self.severe_degradation_net_forest_mplc_area
        self.severe_degradation_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 3))))
        # self.severe_degradation_net_forest_mplc_percentage_of_landscape
        self.severe_degradation_net_forest_mplc_percentage_of_landscape = round(
            float((self.severe_degradation_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.severe_degradation_gross_forest_mplc_area
        self.severe_degradation_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 3))))
        # self.severe_degradation_gross_forest_mplc_percentage_of_landscape
        self.severe_degradation_gross_forest_mplc_percentage_of_landscape = round(
            float((self.severe_degradation_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # degradation absolute (= LUT17 net forest deforested) - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 4
        # self.absolute_degradation_net_forest_mplc_area
        self.absolute_degradation_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 4))))
        # self.absolute_degradation_net_forest_mplc_percentage_of_landscape
        self.absolute_degradation_net_forest_mplc_percentage_of_landscape = round(
            float((self.absolute_degradation_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # Calculations which require the environment map of the last time step:
        if self.time_step == 1:
            self.absolute_degradation_net_forest_disturbed_mplc_area = 'cannot be calculated in time step 1'
            self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape = 'cannot be calculated in time step 1'
            self.absolute_degradation_net_forest_undisturbed_mplc_area = 'cannot be calculated in time step 1'
            self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape = 'cannot be calculated in time step 1'
        else:
            absolute_degradation_only_map = ifthenelse(self.mplc_degradation_and_regeneration_net_forest_map == 4,
                                                       scalar(self.mplc_degradation_and_regeneration_net_forest_map),
                                                       scalar(self.null_mask_map))

            # self.absolute_degradation_net_forest_disturbed_mplc_area
            former_disturbed_net_forest_pixels_absolute_degraded_map = ifthenelse(scalar(absolute_degradation_only_map) > scalar(0),
                                                                                  scalar(self.mplc_environment_last_time_step) == scalar(8),
                                                                                  boolean(self.null_mask_map))

            self.absolute_degradation_net_forest_disturbed_mplc_area = int(maptotal(scalar(boolean(former_disturbed_net_forest_pixels_absolute_degraded_map))))
            # self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape
            self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape = round(
                float((self.absolute_degradation_net_forest_disturbed_mplc_area / self.hundred_percent_area) * 100), 2)

            # self.absolute_degradation_net_forest_undisturbed_mplc_area
            former_undisturbed_net_forest_pixels_absolute_degraded_map = ifthenelse(
                scalar(absolute_degradation_only_map) > scalar(0),
                scalar(self.mplc_environment_last_time_step) == scalar(9),
                boolean(self.null_mask_map))

            self.absolute_degradation_net_forest_undisturbed_mplc_area = int(maptotal(scalar(boolean(former_undisturbed_net_forest_pixels_absolute_degraded_map))))
            # self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape
            self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape = round(
                float((self.absolute_degradation_net_forest_undisturbed_mplc_area / self.hundred_percent_area) * 100), 2)

        # 2) REGENERATION
        # regeneration low - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 5
        # self.low_regeneration_net_forest_mplc_area
        self.low_regeneration_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 5))))
        # self.low_regeneration_net_forest_mplc_percentage_of_landscape
        self.low_regeneration_net_forest_mplc_percentage_of_landscape = round(
            float((self.low_regeneration_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.low_regeneration_gross_forest_mplc_area
        self.low_regeneration_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 5))))
        # self.low_regeneration_gross_forest_mplc_percentage_of_landscape
        self.low_regeneration_gross_forest_mplc_percentage_of_landscape  = round(
            float((self.low_regeneration_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # regeneration medium - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 6
        # self.medium_regeneration_net_forest_mplc_area
        self.medium_regeneration_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 6))))
        # self.medium_regeneration_net_forest_mplc_percentage_of_landscape
        self.medium_regeneration_net_forest_mplc_percentage_of_landscape = round(
            float((self.medium_regeneration_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.medium_regeneration_gross_forest_mplc_area
        self.medium_regeneration_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 6))))
        # self.medium_regeneration_gross_forest_mplc_percentage_of_landscape
        self.medium_regeneration_gross_forest_mplc_percentage_of_landscape = round(
            float((self.medium_regeneration_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # regeneration high - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 7
        # self.high_regeneration_net_forest_mplc_area
        self.high_regeneration_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 7))))
        # self.high_regeneration_net_forest_mplc_percentage_of_landscape
        self.high_regeneration_net_forest_mplc_percentage_of_landscape = round(
            float((self.high_regeneration_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.high_regeneration_gross_forest_mplc_area
        self.high_regeneration_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 7))))
        # self.high_regeneration_gross_forest_mplc_percentage_of_landscape
        self.high_regeneration_gross_forest_mplc_percentage_of_landscape = round(
            float((self.high_regeneration_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # regeneration full (climax stadium, still not all primary forest traits given)) - self.most_probable_landscape_configuration_degradation_and_regeneration_map = 8
        # self.full_regeneration_net_forest_mlc_area
        self.full_regeneration_net_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_net_forest_map == 8))))
        # self.full_regeneration_net_forest_mplc_percentage_of_landscape
        self.full_regeneration_net_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)
        # self.full_regeneration_gross_forest_mplc_area
        self.full_regeneration_gross_forest_mplc_area = int(maptotal(scalar(boolean(self.mplc_degradation_and_regeneration_gross_forest_map == 8))))
        # self.full_regeneration_gross_forest_mplc_percentage_of_landscape
        self.full_regeneration_gross_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_disturbed_forest_net_forest_mplc_area
        disturbed_forest_in_net_forest = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                                    scalar(self.net_forest_environment_map) == scalar(8),
                                                    boolean(self.null_mask_map))
        full_regeneration_disturbed_net_forest_map = ifthenelse(self.mplc_degradation_and_regeneration_net_forest_map == 8,
                                                                scalar(disturbed_forest_in_net_forest),
                                                                scalar(self.null_mask_map))

        self.full_regeneration_disturbed_forest_net_forest_mplc_area = int(maptotal(scalar(boolean(full_regeneration_disturbed_net_forest_map))))
        # self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape
        self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_disturbed_forest_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_disturbed_forest_gross_forest_mplc_area
        disturbed_forest_in_gross_forest = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                                      scalar(1),
                                                      scalar(self.null_mask_map))

        full_regeneration_disturbed_gross_forest_map = ifthenelse(
            self.mplc_degradation_and_regeneration_gross_forest_map == 8,
            scalar(disturbed_forest_in_gross_forest),
            scalar(self.null_mask_map))

        self.full_regeneration_disturbed_forest_gross_forest_mplc_area = int(maptotal(scalar(boolean(full_regeneration_disturbed_gross_forest_map))))
        # self.full_regeneration_disturbed_forest_gross_forest_mplc_percentage_of_landscape
        self.full_regeneration_disturbed_forest_gross_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_disturbed_forest_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_undisturbed_forest_net_forest_mplc_area
        undisturbed_forest_in_net_forest = ifthenelse(scalar(self.net_forest_environment_map) == scalar(9),
                                                      boolean(1),
                                                      boolean(self.null_mask_map))

        full_regeneration_undisturbed_net_forest_map = ifthenelse(
            self.mplc_degradation_and_regeneration_net_forest_map == 8,
            scalar(undisturbed_forest_in_net_forest),
            scalar(self.null_mask_map))

        self.full_regeneration_undisturbed_forest_net_forest_mplc_area = int(maptotal(scalar(boolean(full_regeneration_undisturbed_net_forest_map))))
        # self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape
        self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_undisturbed_forest_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_undisturbed_forest_gross_forest_mplc_area
        undisturbed_forest_in_gross_forest = ifthenelse(
            scalar(self.most_probable_landscape_configuration_map) == scalar(9),
            scalar(1),
            scalar(self.null_mask_map))

        full_regeneration_undisturbed_gross_forest_map = ifthenelse(
            self.mplc_degradation_and_regeneration_gross_forest_map == 8,
            scalar(undisturbed_forest_in_gross_forest),
            scalar(self.null_mask_map))

        self.full_regeneration_undisturbed_forest_gross_forest_mplc_area = int(maptotal(scalar(boolean(full_regeneration_undisturbed_gross_forest_map))))

        # self.full_regeneration_undisturbed_forest_gross_forest_mplc_percentage_of_landscape
        self.full_regeneration_undisturbed_forest_gross_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_undisturbed_forest_gross_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        print('deriving the most probable landscape configuration of forest degradation and regeneration done')

        # =================================================================== #

    def derive_AGB_and_Carbon(self):
        """ SH: AGB is taken from LPB-basic probabilistic modelling and combined with the LPB-mplc landscape."""

        print('\nderiving AGB and tC ...')

        # get the MC average AGB map
        self.AGB_map = self.dictionary_of_AGB_files[self.time_step]

        # FOREST AGB in Mg -> Carbon
        # potential maximum AGB
        potential_maximum_undisturbed_forest_AGB_map = ifthenelse(scalar(self.projection_potential_natural_vegetation_distribution_map) == scalar(3),
                                                                  scalar(self.projection_potential_maximum_undisturbed_AGB_map),
                                                                  scalar(self.null_mask_map))

        self.potential_maximum_undisturbed_forest_AGB_maptotal = float(maptotal(potential_maximum_undisturbed_forest_AGB_map))
        self.potential_maximum_undisturbed_forest_AGB_maptotal = round(self.potential_maximum_undisturbed_forest_AGB_maptotal, 3)

        self.potential_maximum_undisturbed_forest_AGB_Carbon = round(self.potential_maximum_undisturbed_forest_AGB_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

        # INITIAL AGB FOR Climate periods
        # initial AGB simulation start
        # self.initial_AGB_maptotal
        if self.time_step == 1:
            # get the input AGB map
            if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
                input_AGB_map = readmap(Filepaths.file_initial_AGB_input)
            elif Parameters.get_model_scenario() == 'no_conservation':
                input_AGB_map = readmap(Filepaths.file_initial_AGB_simulated_for_worst_case_scenario_input)

            # get the user defined gross forest area and according initial AGB
            gross_forest_initial_AGB_map = ifthen(scalar(self.user_defined_gross_forest_map) == scalar(1), # combines the mplc landscape of user defined areas to be evaluated with ...
                                                       scalar(input_AGB_map)) # the initial AGB map

            self.initial_AGB_maptotal = float(maptotal(gross_forest_initial_AGB_map))
            self.initial_AGB_maptotal = round(self.initial_AGB_maptotal, 3)

            # self.initial_AGB_tC
            self.initial_AGB_Carbon = round(self.initial_AGB_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

            self.initial_AGB_percentage_of_potential_maximum_undisturbed_AGB = round(
                         float((self.initial_AGB_maptotal / self.potential_maximum_undisturbed_forest_AGB_maptotal) * 100), 2)

        # FINAL AGB FOR THE SINGULAR TIME STEPS:
        # self.final_AGB_gross_forest_maptotal

        final_AGB_gross_forest_map = ifthen(scalar(self.user_defined_gross_forest_map) == scalar(1), # combines the mplc landscape with ...
                                            scalar(self.AGB_map)) # the MC average after the time step calculations

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'mplc_AGB'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(final_AGB_gross_forest_map,
               os.path.join(Filepaths.folder_AGB_most_probable_landscape_configuration, output_map_name))
        print(
            'final_AGB_gross_forest_map created and stored as "mplc_AGB" in:',
            Filepaths.folder_AGB_most_probable_landscape_configuration)

        """SH: SAVE final_AGB_gross_forest_map FOR THE WORST CASE SCENARIO IF REQUIRED"""

        if Parameters.get_worst_case_scenario_decision() is True:
            if Parameters.get_the_initial_simulation_year_for_the_worst_case_scenario() == self.year:
                print('\nsaving final_AGB_gross_forest_map for the worst case scenario for the year',
                      self.year, '...')
                report(final_AGB_gross_forest_map, os.path.join(
                    Filepaths.folder_inputs_initial_worst_case_scenario,
                    'initial_AGB_simulated_for_worst_case_scenario_input.map'))
                print('-> saved final_AGB_gross_forest_map for the year', str(self.year),
                      'as initial_AGB_simulated_for_worst_case_scenario_input.map in:',
                      Filepaths.folder_inputs_initial_worst_case_scenario)

        self.final_AGB_gross_forest_maptotal = float(maptotal(final_AGB_gross_forest_map))
        self.final_AGB_gross_forest_maptotal = round(self.final_AGB_gross_forest_maptotal, 3)

        # self.final_AGB_gross_forest_tC
        self.final_AGB_gross_forest_Carbon = round(self.final_AGB_gross_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

        # self.final_AGB_net_forest_maptotal
        final_AGB_net_forest_map = ifthen(scalar(self.net_forest_mplc_map) == scalar(1),
                                          scalar(self.AGB_map))

        self.final_AGB_net_forest_maptotal = float(maptotal(final_AGB_net_forest_map))
        self.final_AGB_net_forest_maptotal = round(self.final_AGB_net_forest_maptotal, 3)

        # self.final_AGB_net_forest_tC
        self.final_AGB_net_forest_Carbon = round(self.final_AGB_net_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)


        # IF USER DEFINED PROVIDE THE ACCORDING VALUES, ELSE DECLARE AS NOT GROSS FOREST
        exception_value = str('user-defined not considered gross forest')

        # final AGB disturbed forest
        if 8 in self.gross_forest_LUTs_list:
            # self.final_disturbed_forest_AGB_gross_forest_maptotal
            final_disturbed_forest_AGB_gross_forest_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                                                 scalar(self.AGB_map))

            self.final_disturbed_forest_AGB_gross_forest_maptotal = float(maptotal(final_disturbed_forest_AGB_gross_forest_map))
            self.final_disturbed_forest_AGB_gross_forest_maptotal = round(self.final_disturbed_forest_AGB_gross_forest_maptotal, 3)

            # self.final_disturbed_forest_AGB_gross_forest_tC
            self.final_disturbed_forest_AGB_gross_forest_Carbon = round(self.final_disturbed_forest_AGB_gross_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

            # self.final_disturbed_forest_AGB_net_forest_maptotal
            final_disturbed_forest_AGB_net_forest_map = ifthen(scalar(self.net_forest_environment_map) == scalar(8),
                                                           scalar(self.AGB_map))
            self.final_disturbed_forest_AGB_net_forest_maptotal = float(maptotal(final_disturbed_forest_AGB_net_forest_map))
            self.final_disturbed_forest_AGB_net_forest_maptotal = round(self.final_disturbed_forest_AGB_net_forest_maptotal, 3)

            # self.final_disturbed_forest_AGB_net_forest_tC
            self.final_disturbed_forest_AGB_net_forest_Carbon = round(self.final_disturbed_forest_AGB_gross_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

            # self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest
            self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest = round(
            float((self.final_disturbed_forest_AGB_net_forest_maptotal / self.final_disturbed_forest_AGB_gross_forest_maptotal) * 100), 2)
        else:
            self.final_disturbed_forest_AGB_gross_forest_maptotal = exception_value
            self.final_disturbed_forest_AGB_gross_forest_Carbon = exception_value
            self.final_disturbed_forest_AGB_net_forest_maptotal = exception_value
            self.final_disturbed_forest_AGB_net_forest_Carbon = exception_value
            self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest = exception_value


        # final AGB undisturbed forest
        if 9 in self.gross_forest_LUTs_list:
            # self.final_undisturbed_forest_AGB_gross_forest_maptotal
            final_undisturbed_forest_AGB_gross_forest_map = ifthen(
                scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                scalar(self.AGB_map))

            self.final_undisturbed_forest_AGB_gross_forest_maptotal = float(maptotal(final_undisturbed_forest_AGB_gross_forest_map))
            self.final_undisturbed_forest_AGB_gross_forest_maptotal = round(self.final_undisturbed_forest_AGB_gross_forest_maptotal, 3)

            # self.final_undisturbed_forest_AGB_gross_forest_tC
            self.final_undisturbed_forest_AGB_gross_forest_Carbon = round(self.final_undisturbed_forest_AGB_gross_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

            # self.final_undisturbed_forest_AGB_net_forest_maptotal
            final_undisturbed_forest_AGB_net_forest_map = ifthen(scalar(self.net_forest_environment_map) == scalar(9),
                                                             scalar(self.AGB_map))
            self.final_undisturbed_forest_AGB_net_forest_maptotal = float(maptotal(final_undisturbed_forest_AGB_net_forest_map))
            self.final_undisturbed_forest_AGB_net_forest_maptotal = round(self.final_undisturbed_forest_AGB_net_forest_maptotal,3)

            # self.final_undisturbed_forest_AGB_net_forest_tC
            self.final_undisturbed_forest_AGB_net_forest_Carbon = round(self.final_undisturbed_forest_AGB_net_forest_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

            # self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest
            self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest = round(
                float((self.final_undisturbed_forest_AGB_net_forest_maptotal / self.final_undisturbed_forest_AGB_gross_forest_maptotal) * 100), 2)
        else:
            self.final_undisturbed_forest_AGB_gross_forest_maptotal = exception_value
            self.final_undisturbed_forest_AGB_gross_forest_Carbon = exception_value
            self.final_undisturbed_forest_AGB_net_forest_maptotal = exception_value
            self.final_undisturbed_forest_AGB_net_forest_Carbon = exception_value
            self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest = exception_value

        # agroforestry
        if 4 in self.gross_forest_LUTs_list:
            final_agrofrestry_AGB_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(4),
                                                  scalar(self.AGB_map))
            self.final_agroforestry_AGB_maptotal = float(maptotal(final_agrofrestry_AGB_map))
            self.final_agroforestry_AGB_maptotal = round(self.final_agroforestry_AGB_maptotal, 3)

            self.final_agroforestry_AGB_Carbon = round(self.final_agroforestry_AGB_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)
        else:
            self.final_agroforestry_AGB_maptotal = exception_value
            self.final_agroforestry_AGB_Carbon = exception_value


        # plantation
        if 5 in self.gross_forest_LUTs_list:
            final_plantation_AGB_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(5),
                                           scalar(self.AGB_map))
            self.final_plantation_AGB_maptotal = float(maptotal(final_plantation_AGB_map))
            self.final_plantation_AGB_maptotal = round(self.final_plantation_AGB_maptotal, 3)

            self.final_plantation_AGB_Carbon = round(self.final_plantation_AGB_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)
        else:
            self.final_plantation_AGB_maptotal = exception_value
            self.final_plantation_AGB_Carbon = exception_value

        print('deriving AGB and tC done')

        # =================================================================== #

    def derive_remaining_forest_without_direct_anthropogenic_impact_for_100_years(self):
        """ SH: FOREST 100 years without anthropogenic impact (assumed potential primary stadium)."""
        # 1) disturbed forest pixels which are documented by TMF up to 36 years and initially set with random age achieve
        # without further simulated impact the undisturbed/"potential primary" status by age 100 via succession (implemented in LPB-basic, gives a stochastic result, earliest 2082)
        # 2) initial remaining undisturbed pixels also "potential primary status" by the simulated age 100 are counted from 36 onwards

        # get the MC average succession age map
        self.succession_age_map = self.dictionary_of_succession_age_files[self.time_step]

        # get the user defined value of succession to undisturbed forest (100 by default)
        threshold_value_undisturbed_forest = Parameters.get_user_defined_undisturbed_succession_age_forest()

        print('\nderiving remaining forest without direct anthropogenic impact for 100 years ...')

        if self.time_step == 1: # initiates the maps, nothing else happens in time step 1
            self.forest_a_100years_without_impact_map = self.region_and_restricted_areas_base_map # contains classes 8 and 9 for the background
        else:
            # built the according info map (100 years undisturbed forest in the context of the region)
            self.forest_a_100years_without_impact_map = ifthenelse(scalar(self.succession_age_map) >= scalar(threshold_value_undisturbed_forest),
                                                                   scalar(1),
                                                                   scalar(self.null_mask_map))

            gross_forest_a_100years_without_impact_map = ifthenelse(pcrand(boolean(self.forest_a_100years_without_impact_map), boolean(self.gross_forest_mplc_map)),
                                                                       scalar(1), # category 1 gross forest
                                                                       scalar(self.null_mask_map))

            net_forest_a_100years_without_impact_map = ifthenelse(
                    pcrand(boolean(self.forest_a_100years_without_impact_map), boolean(self.net_forest_mplc_map)),
                    scalar(2),  # category net  forest
                    scalar(self.null_mask_map))

            combined_gross_net_forest_a_100years_without_impact_map = ifthenelse(scalar(net_forest_a_100years_without_impact_map) == scalar(2),
                                                                                     scalar(2),
                                                                                     scalar(gross_forest_a_100years_without_impact_map))


            self.forest_a_100years_without_impact_map = ifthenelse(scalar(combined_gross_net_forest_a_100years_without_impact_map) > scalar(0),
                                                                   scalar(combined_gross_net_forest_a_100years_without_impact_map), # class 1 gross forest, class 2 net forest
                                                                   scalar(self.region_and_restricted_areas_base_map)) # classes 8(region) and 9(restricted areas)

        pcraster_conform_map_name = 'mplcfnoi'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
        report(self.forest_a_100years_without_impact_map, os.path.join(Filepaths.folder_100years_no_impact_forest_mplc, output_map_name))
        print('self.forest_a_100years_without_impact_map created and stored as "mplcfnoi" in:',
                    Filepaths.folder_100years_no_impact_forest_mplc)

        if time_step == 1:
            self.former_disturbed_gross_forest_map = ifthenelse(scalar(self.initial_most_probable_landscape_configuration_map) == scalar(8),
                                                                scalar(1),
                                                                scalar(self.null_mask_map))
            self.initial_undisturbed_gross_forest_map = ifthenelse(scalar(self.initial_most_probable_landscape_configuration_map) == scalar(9),
                                                                   scalar(1),
                                                                   scalar(self.null_mask_map))
            net_forest_initial_environment_map = ifthenelse(scalar(self.net_forest_mplc_map) == scalar(1),
                                                            scalar(self.initial_most_probable_landscape_configuration_map),
                                                            scalar(self.null_mask_map))
            self.former_disturbed_net_forest_map = ifthenelse(scalar(net_forest_initial_environment_map) == scalar(8),
                                                              scalar(1),
                                                              scalar(self.null_mask_map))
            self.initial_undisturbed_net_forest_map = ifthenelse(
                scalar(net_forest_initial_environment_map) == scalar(9),
                scalar(1),
                scalar(self.null_mask_map))

        # former disturbed forest (initial age: random 1 to 36)
        # gross disturbed forest
        a_100_years_no_impact_on_former_disturbed_gross_forest_map = ifthenelse(scalar(self.succession_age_map) >= scalar(threshold_value_undisturbed_forest),
                                                                                scalar(self.former_disturbed_gross_forest_map),
                                                                                scalar(self.null_mask_map))

        self.former_disturbed_gross_forest_100years_without_impact_area = int(maptotal(scalar(boolean(a_100_years_no_impact_on_former_disturbed_gross_forest_map))))

        self.former_disturbed_gross_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.former_disturbed_gross_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        # net disturbed forest
        a_100_years_no_impact_on_former_disturbed_net_forest_map = ifthenelse(
            scalar(self.succession_age_map) >= scalar(threshold_value_undisturbed_forest),
            scalar(self.former_disturbed_net_forest_map),
            scalar(self.null_mask_map))

        self.former_disturbed_net_forest_100years_without_impact_area = int(maptotal(scalar(boolean(a_100_years_no_impact_on_former_disturbed_net_forest_map))))
        self.former_disturbed_net_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.former_disturbed_net_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        # initial undisturbed forest (initial age: 36)
        # gross undisturbed forest
        a_100_years_no_impact_on_initial_undisturbed_gross_forest_map = ifthenelse(
            scalar(self.succession_age_map) >= scalar(threshold_value_undisturbed_forest),
            scalar(self.initial_undisturbed_gross_forest_map),
            scalar(self.null_mask_map))

        self.initial_undisturbed_gross_forest_100years_without_impact_area = int(maptotal(scalar(boolean(a_100_years_no_impact_on_initial_undisturbed_gross_forest_map))))

        self.initial_undisturbed_gross_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.initial_undisturbed_gross_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        # net undisturbed forest
        a_100_years_no_impact_on_initial_undisturbed_net_forest_map = ifthenelse(
            scalar(self.succession_age_map) >= scalar(threshold_value_undisturbed_forest),
            scalar(self.initial_undisturbed_net_forest_map),
            scalar(self.null_mask_map))

        self.initial_undisturbed_net_forest_100years_without_impact_area = int(maptotal(scalar(boolean(a_100_years_no_impact_on_initial_undisturbed_net_forest_map))))

        self.initial_undisturbed_net_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.initial_undisturbed_net_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        print('deriving remaining forest without direct anthropogenic impact for 100 years done')

        # =================================================================== #

    def derive_user_defined_succession_to_undisturbed_forest_for_the_time_step(self):
        """Displays the cells that are new undisturbed forest cells by user defined succession age for the time step"""

        print('\nderiving user-defined undisturbed forest succession ...')

        self.user_defined_succession_age_to_undisturbed_forest = Parameters.get_user_defined_undisturbed_succession_age_forest()
        dictionary_of_undisturbed_forest['succession_age'] = self.user_defined_succession_age_to_undisturbed_forest

        if self.time_step == 1:
            # create the regional base map
            self.base_map = ifthen(scalar(self.null_mask_map) == scalar(0),
                              scalar(1))

            # for the initial time step initialize the current distribution of undisturbed forest
            self.current_undisturbed_forest_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                                                    scalar(2)) # categorize it as class 2, 1 is the region

            # derive map total
            maptotal_undisturbed_forest = int(maptotal(scalar(self.current_undisturbed_forest_map)) / 2)

            self.export_map = cover(scalar(self.current_undisturbed_forest_map), scalar(self.base_map))


            dictionary_of_undisturbed_forest['maptotal_undisturbed_forest'].append(maptotal_undisturbed_forest)
            dictionary_of_undisturbed_forest['maptotal_new_undisturbed_forest'].append(0)

        else:
            # for each time step now check if new cells have popped up and map them additionally to the remaining undisturbed forest extent

            # first evaluate the current map from last time step for the last extent
            undisturbed_last_time_step_map = cover(scalar(self.current_undisturbed_forest_map), scalar(self.null_mask_map))

            # check for less or new cells
            self.current_undisturbed_forest_map = ifthenelse(
                scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                scalar(2),  # categorize it as class 2
                scalar(self.null_mask_map))

            # get the new cells in this time step (includes region cells)
            difference_map = ifthen(scalar(undisturbed_last_time_step_map) == scalar(0),
                                    scalar(self.current_undisturbed_forest_map))

            # eliminate the zeros from the current undisturbed map
            self.current_undisturbed_forest_map = ifthen(scalar(self.current_undisturbed_forest_map) != scalar(0),
                                                         scalar(self.current_undisturbed_forest_map))

            # derive map total
            maptotal_undisturbed_forest = int(maptotal(scalar(self.current_undisturbed_forest_map)) / 2)

            # in case new cells popped up, declare them as class 3
            new_undisturbed_pixels_map = ifthen(scalar(difference_map) == scalar(2),
                                                scalar(3))

            # derive map total of new cells
            maptotal_new_undisturbed_forest = int(maptotal(scalar(new_undisturbed_pixels_map)) / 3)

            # now combine the maps for GIF visualization
            export_map = cover(scalar(new_undisturbed_pixels_map), scalar(self.current_undisturbed_forest_map))
            export_map = cover(scalar(export_map), scalar(self.base_map))
            self.export_map = export_map

            dictionary_of_undisturbed_forest['maptotal_undisturbed_forest'].append(maptotal_undisturbed_forest)
            dictionary_of_undisturbed_forest['maptotal_new_undisturbed_forest'].append(maptotal_new_undisturbed_forest)

        pcraster_conform_map_name = 'mplcuduf'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.export_map,
               os.path.join(Filepaths.folder_undisturbed_forest_mplc, output_map_name))
        print('self.export_map (current and new undisturbed forest cells) created and stored as "mplcuduf" in:',
              Filepaths.folder_undisturbed_forest_mplc)

        print('deriving user-defined undisturbed forest succession done')

        # =================================================================== #

    def derive_remaining_forest_without_direct_anthropogenic_impact_for_the_time_step(self):
        """ SH: REMAINING FOREST WITHOUT ANTHROPOGENIC IMPACT PER TIME STEP (NET AND GROSS)."""

        print('\nderiving remaining forest without direct anthropogenic impact for each time step ...')

        # gross forest disturbed
        gross_forest_disturbed_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(8),
                                                scalar(self.most_probable_landscape_configuration_map),
                                                scalar(self.null_mask_map))
        # gross forest undisturbed
        gross_forest_undisturbed_map = ifthenelse(scalar(self.most_probable_landscape_configuration_map) == scalar(9),
                                                  scalar(self.most_probable_landscape_configuration_map),
                                                  scalar(self.null_mask_map))
        # net forest disturbed
        net_forest_disturbed_map = ifthenelse(scalar(self.net_forest_environment_map) == scalar(8),
                                              scalar(self.net_forest_environment_map),
                                              scalar(self.null_mask_map))
        # net forest undisturbed
        net_forest_undisturbed_map = ifthenelse(scalar(self.net_forest_environment_map) == scalar(9),
                                              scalar(self.net_forest_environment_map),
                                              scalar(self.null_mask_map))
        # combined and classes
        combined_classified_forest_map = ifthenelse(boolean(gross_forest_disturbed_map),
                                                    scalar(1), # class 1 gross disturbed forest
                                                    scalar(self.null_mask_map))
        combined_classified_forest_map = ifthenelse(boolean(gross_forest_undisturbed_map),
                                                    scalar(2),  # class 2 gross undisturbed forest
                                                    scalar(combined_classified_forest_map))
        combined_classified_forest_map = ifthenelse(boolean(net_forest_disturbed_map),
                                                    scalar(3),  # class 3 net disturbed forest
                                                    scalar(combined_classified_forest_map))
        combined_classified_forest_map = ifthenelse(boolean(net_forest_undisturbed_map),
                                                    scalar(4),  # class 4 net undisturbed forest
                                                    scalar(combined_classified_forest_map))

        # subtraction of anthropogenic impact buffer
        no_impact_forest_map = ifthenelse(boolean(self.anthropogenic_impact_buffer_map),
                                          scalar(0),
                                          scalar(combined_classified_forest_map))
        # base map for BAU and worst case scenario
        remaining_no_impact_map = ifthenelse(scalar(no_impact_forest_map) == scalar(0),
                                             scalar(self.region_and_restricted_areas_base_map),
                                             scalar(no_impact_forest_map))

        # report
        pcraster_conform_map_name = 'mplcfrni'
        time_step = self.time_step  # needed for PCraster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(remaining_no_impact_map,
               os.path.join(Filepaths.folder_remaining_no_impact_forest_mplc, output_map_name))
        print('remaining_no_impact_map created and stored as "mplcfrni" in:',
              Filepaths.folder_remaining_no_impact_forest_mplc)

        # log file variables
        # gross
        gross_forest_disturbed_no_impact_map = ifthen(boolean(self.anthropogenic_impact_buffer_map == 0),
                                                      scalar(gross_forest_disturbed_map))
        self.remaining_gross_disturbed_forest_without_impact_area = int(maptotal(scalar(gross_forest_disturbed_no_impact_map)))
        self.remaining_gross_disturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_gross_disturbed_forest_without_impact_area / self.hundred_percent_area) * 100), 2)

        gross_forest_undisturbed_no_impact_map = ifthen(boolean(self.anthropogenic_impact_buffer_map == 0),
                                                      scalar(gross_forest_undisturbed_map))
        self.remaining_gross_undisturbed_forest_without_impact_area = int(
            maptotal(scalar(gross_forest_undisturbed_no_impact_map)))
        self.remaining_gross_undisturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_gross_undisturbed_forest_without_impact_area / self.hundred_percent_area) * 100), 2)

        # net
        net_forest_disturbed_no_impact_map = ifthen(boolean(self.anthropogenic_impact_buffer_map == 0),
                                                      scalar(net_forest_disturbed_map))
        self.remaining_net_disturbed_forest_without_impact_area = int(
            maptotal(scalar(net_forest_disturbed_no_impact_map)))
        self.remaining_net_disturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_net_disturbed_forest_without_impact_area / self.hundred_percent_area) * 100), 2)

        net_forest_undisturbed_no_impact_map = ifthen(boolean(self.anthropogenic_impact_buffer_map == 0),
                                                    scalar(net_forest_undisturbed_map))
        self.remaining_net_undisturbed_forest_without_impact_area = int(
            maptotal(scalar(net_forest_undisturbed_no_impact_map)))
        self.remaining_net_undisturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_net_undisturbed_forest_without_impact_area / self.hundred_percent_area) * 100), 2)

        print('deriving remaining forest without direct anthropogenic impact for each time step done')

        # =================================================================== #

    def calculate_gross_minus_net_forest(self):
        """ SH: ALL GROSS MINUS NET FOREST CALCULATIONS."""

        print('\ncalculating gross minus net forest ...')

        self.gross_minus_net_forest_disturbed_mplc_area = self.gross_mplc_disturbed_forest_area - self.net_mplc_disturbed_forest_area
        self.gross_minus_net_forest_disturbed_mplc_percentage_of_landscape = round(
            float((self.gross_minus_net_forest_disturbed_mplc_area / self.hundred_percent_area) * 100), 2)

        self.gross_minus_net_forest_undisturbed_mplc_area = self.gross_mplc_undisturbed_forest_area - self.net_mplc_undisturbed_forest_area
        self.gross_minus_net_forest_undisturbed_mplc_percentage_of_landscape = round(
            float((self.gross_minus_net_forest_undisturbed_mplc_area / self.hundred_percent_area) * 100), 2)

        self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area = self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area - self.true_net_forest_impacted_by_anthropogenic_features_mplc_area
        self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = round(
            float((self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area / self.gross_forest_mplc_area) * 100), 2)

        self.former_disturbed_gross_minus_net_forest_100years_without_impact_area = self.former_disturbed_gross_forest_100years_without_impact_area - self.former_disturbed_net_forest_100years_without_impact_area
        self.former_disturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.former_disturbed_gross_minus_net_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area = self.initial_undisturbed_gross_forest_100years_without_impact_area - self.initial_undisturbed_net_forest_100years_without_impact_area
        self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = round(
            float((self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area / self.hundred_percent_area) * 100), 2)

        self.remaining_gross_minus_net_disturbed_forest_without_impact_area = self.remaining_gross_disturbed_forest_without_impact_area - self.remaining_net_disturbed_forest_without_impact_area
        self.remaining_gross_minus_net_disturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_gross_minus_net_disturbed_forest_without_impact_area / self.hundred_percent_area) * 100),2)

        self.remaining_gross_minus_net_undisturbed_forest_without_impact_area = self.remaining_gross_undisturbed_forest_without_impact_area - self.remaining_net_undisturbed_forest_without_impact_area
        self.remaining_gross_minus_net_undisturbed_forest_without_impact_percentage_of_landscape = round(
            float((self.remaining_gross_minus_net_undisturbed_forest_without_impact_area / self.hundred_percent_area) * 100), 2)

        # self.low_degradation_gross_minus_net_forest_mplc_area
        self.low_degradation_gross_minus_net_forest_mplc_area = self.low_degradation_gross_forest_mplc_area - self.low_degradation_net_forest_mplc_area
        # self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape
        self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.low_degradation_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.moderate_degradation_gross_minus_net_forest_mplc_area
        self.moderate_degradation_gross_minus_net_forest_mplc_area = self.moderate_degradation_gross_forest_mplc_area - self.moderate_degradation_net_forest_mplc_area
        # self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape
        self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.moderate_degradation_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.severe_degradation_gross_minus_net_forest_mplc_area
        self.severe_degradation_gross_minus_net_forest_mplc_area = self.severe_degradation_gross_forest_mplc_area - self.severe_degradation_net_forest_mplc_area
        # self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape
        self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.severe_degradation_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)




        # self.low_regeneration_gross_minus_net_forest_mplc_area
        self.low_regeneration_gross_minus_net_forest_mplc_area = self.low_regeneration_gross_forest_mplc_area - self.low_regeneration_net_forest_mplc_area
        # self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape
        self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.low_regeneration_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.medium_regeneration_gross_minus_net_forest_mplc_area
        self.medium_regeneration_gross_minus_net_forest_mplc_area = self.medium_regeneration_gross_forest_mplc_area - self.medium_regeneration_net_forest_mplc_area
        # self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape
        self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.medium_regeneration_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.high_regeneration_gross_minus_net_forest_mplc_area
        self.high_regeneration_gross_minus_net_forest_mplc_area = self.high_regeneration_gross_forest_mplc_area - self.high_regeneration_net_forest_mplc_area
        # self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape
        self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.high_regeneration_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area
        self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area = self.full_regeneration_disturbed_forest_gross_forest_mplc_area - self.full_regeneration_disturbed_forest_net_forest_mplc_area
        # self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape
        self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area
        self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area = self.full_regeneration_undisturbed_forest_gross_forest_mplc_area - self.full_regeneration_undisturbed_forest_net_forest_mplc_area
        # self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape
        self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = round(
            float((self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area / self.hundred_percent_area) * 100), 2)

        # self.final_AGB_gross_minus_net_forest_maptotal
        self.final_AGB_gross_minus_net_forest_maptotal = self.final_AGB_gross_forest_maptotal - self.final_AGB_net_forest_maptotal
        # self.final_AGB_gross_minus_net_forest_tC
        self.final_AGB_gross_minus_net_forest_Carbon = round(self.final_AGB_gross_forest_Carbon - self.final_AGB_net_forest_Carbon, 3)

        # self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal
        self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal = self.final_disturbed_forest_AGB_gross_forest_maptotal - self.final_disturbed_forest_AGB_net_forest_maptotal
        # self.final_disturbed_forest_AGB_gross_minus_net_forest_tC
        self.final_disturbed_forest_AGB_gross_minus_net_forest_Carbon = round(self.final_disturbed_forest_AGB_gross_forest_Carbon - self.final_disturbed_forest_AGB_net_forest_Carbon, 3)

        # self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal = round(self.final_undisturbed_forest_AGB_gross_forest_maptotal - self.final_undisturbed_forest_AGB_net_forest_maptotal, 3)
        # self.final_undisturbed_forest_AGB_gross_minus_net_forest_tC
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_Carbon = round(self.final_undisturbed_forest_AGB_gross_forest_Carbon - self.final_undisturbed_forest_AGB_net_forest_Carbon, 3)

        # self.final_disturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_disturbed_forest
        self.final_disturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_disturbed_forest = round(
            float((self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal / self.final_disturbed_forest_AGB_gross_forest_maptotal) * 100), 2)

        # self.final_undisturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_undisturbed_forest
        self.final_undisturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_undisturbed_forest = round(
            float((self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal / self.final_undisturbed_forest_AGB_gross_forest_maptotal) * 100), 2)

        print('calculating gross minus net forest done')

        # =================================================================== #


    def calculate_singular_AGB_demands_for_the_time_step(self):
        """ SH: calculating singular AGB demands for the time step for the CSV."""

        print('\ncalculating singular AGB demands for the time step for the CSV ...')

        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
            # AGB data:
            regional_AGB_demand_per_person_per_year = Parameters.get_regional_AGB_demand_per_person()
            AGB_total_demand_in_Mg_per_person_per_year = float(regional_AGB_demand_per_person_per_year[0])
            AGB_demand_timber_in_Mg_per_person_per_year = float(regional_AGB_demand_per_person_per_year[1])
            AGB_demand_fuelwood_in_Mg_per_person_per_year = float(regional_AGB_demand_per_person_per_year[2])
            AGB_demand_charcoal_in_Mg_per_person_per_year = float(regional_AGB_demand_per_person_per_year[3])

            self.demand_timber_AGB = round(AGB_demand_timber_in_Mg_per_person_per_year * int(self.population), 3)

            self.demand_fuelwood_AGB = round(AGB_demand_fuelwood_in_Mg_per_person_per_year * int(self.population), 3)

            self.demand_charcoal_AGB = round(AGB_demand_charcoal_in_Mg_per_person_per_year * int(self.population), 3)

            self.demand_AGB = round(AGB_total_demand_in_Mg_per_person_per_year * int(self.population), 3)
        else:
            self.demand_timber_AGB = 'agglomerated_in_total_AGB_demand'
            self.demand_fuelwood_AGB = 'agglomerated_in_total_AGB_demand'
            self.demand_charcoal_AGB = 'agglomerated_in_total_AGB_demand'
            # self.demand_AGB = is noted from LPB basic log file

        print('calculating singular AGB demands for the time step for the CSV done')


        # =================================================================== #

    def calculate_top_crops_yields_for_the_time_step(self):
        """ SH: 5 top crops per country were selected, number is key, values are a list of:
        [name[0], mean yield[1], standard deviation yield[2], percentage of acreage[3] for [4] LUT02(cropland-annual) or LUT04(agroforestry) for the region]"""

        print('\ncalculating top crops potential yields for the CSV ...')

        self.top_crops_data_lists_dictionary = {}

        for a_top_crop in self.dictionary_of_top_crops_yields:
            singular_top_crop_dictionary = {
                'name': self.dictionary_of_top_crops_yields[a_top_crop][0],
                'mean_yield': self.dictionary_of_top_crops_yields[a_top_crop][1],
                'standard_deviation_yield': self.dictionary_of_top_crops_yields[a_top_crop][2],
                'percentage_of_acreage': self.dictionary_of_top_crops_yields[a_top_crop][3],
                'source_LUT': self.dictionary_of_top_crops_yields[a_top_crop][4]
            }

            if singular_top_crop_dictionary['source_LUT'] == Parameters.LUT02:
                considered_total_LUT_acreage_for_the_time_step = self.allocated_pixels_LUT02
            if singular_top_crop_dictionary['source_LUT'] == Parameters.LUT04:
                considered_total_LUT_acreage_for_the_time_step = self.allocated_pixels_LUT04

            singular_top_crop_dictionary['share_of_LUT_acreage'] = math.ceil(
                (considered_total_LUT_acreage_for_the_time_step / 100) * singular_top_crop_dictionary['percentage_of_acreage'])

            singular_top_crop_dictionary['yield_minimum'] = round(
                singular_top_crop_dictionary['share_of_LUT_acreage'] * (singular_top_crop_dictionary['mean_yield'] - singular_top_crop_dictionary['standard_deviation_yield']),
                2)

            singular_top_crop_dictionary['yield_mean'] = round(
                singular_top_crop_dictionary['share_of_LUT_acreage'] * singular_top_crop_dictionary['mean_yield'], 2)

            singular_top_crop_dictionary['yield_maximum'] = round(
                singular_top_crop_dictionary['share_of_LUT_acreage'] * (singular_top_crop_dictionary['mean_yield'] + singular_top_crop_dictionary['standard_deviation_yield']),
                2)

            self.top_crops_data_lists_dictionary[a_top_crop] = singular_top_crop_dictionary

        print('calculating top crops potential yields for the CSV done')

        # =================================================================== #
        # TODO Melvin: check if required here or copy to OC

    def calculate_based_on_agricultural_yields(self):
        """SH: Extracts for the selected LUTs the MC averages from the dictionary per time step"""

        # LUT02_cropland-annual_crop_yields
        # LUT03_pasture_livestock_yields
        # LUT04_agroforestry_crop_yields

        print('\nextracting yield MC averages for the time step  ...')

        if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            LUT02_MCaverage_yield_map = self.dictionary_of_agricultural_yields_MCaverages['LUT02_cropland_annual_crop_yields'][self.time_step]
        if 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            LUT03_MCaverage_yield_map = self.dictionary_of_agricultural_yields_MCaverages['LUT03_pasture_livestock_yields'][self.time_step]
        if 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            LUT04_MCaverage_yield_map = self.dictionary_of_agricultural_yields_MCaverages['LUT04_agroforestry_crop_yields'][self.time_step]

        # TODO Melvin: use maps for operations

        print('extracting yield MC averages for the time step done')

        # =================================================================== #

    # M O D E L  S T A G E  2

    def calculate_umbrella_species_altitude_habitat_environment_map(self):

        print('\ncalculating umbrella species habitat by altitude range  ...')

        umbrella_species_altitude_range_dictionary = Parameters.get_umbrella_species_altitude_range_dictionary()
        altitude_min = umbrella_species_altitude_range_dictionary['altitude_min']
        altitude_max = umbrella_species_altitude_range_dictionary['altitude_max']

        altitude_min_map = ifthen(scalar(self.dem_map) >= scalar(altitude_min),
                                  scalar(self.dem_map))

        self.umbrella_species_altitudinal_range_environment_map = ifthen(scalar(altitude_min_map) <= scalar(altitude_max),
                                                                         scalar(self.most_probable_landscape_configuration_map))

        # if the user defined additional areas that are not potential habitat, extract them here:
        static_excluded_areas_for_umbrella_species_input_map = readmap(Filepaths.file_static_excluded_areas_for_umbrella_species_input)
        self.umbrella_species_altitudinal_range_environment_map = ifthen(scalar(static_excluded_areas_for_umbrella_species_input_map) != scalar(1),
                                                                         self.umbrella_species_altitudinal_range_environment_map)

        pcraster_conform_map_name = 'mplcaltra'
        time_step = self.time_step  # needed for PCRaster conform output
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.umbrella_species_altitudinal_range_environment_map,
               os.path.join(Filepaths.folder_altitude_range_habitat_environment_map_mplc, output_map_name))
        print('self.umbrella_species_altitudinal_range_environment_map created and stored as "mplcaltra" in:',
              Filepaths.folder_altitude_range_habitat_environment_map_mplc)

        print('\ncalculating umbrella species habitat by altitude range  done')

    # =================================================================== #

    def calculate_umbrella_species_ecosystem_fragmentation(self):

        print('\ncalculating fragmentation and p.r.n. further user-defined landstats  ...')

        # variables used:
        user_defined_umbrella_species_core_habitat_LUTs_list = Parameters.get_umbrella_species_core_habitat_LUTs_list()
        user_defined_umbrella_species_minimum_patch_size = Parameters.get_umbrella_species_minimum_patch_size()
        # map used in multiple methods: core LUTs continuos areas in altitudinal range
        # map with land use types
        contiguous_areas_map = self.null_mask_map
        for a_LUT in user_defined_umbrella_species_core_habitat_LUTs_list:
            temp_contiguous_areas_map = ifthen(
                scalar(a_LUT) == scalar(self.umbrella_species_altitudinal_range_environment_map),
                scalar(self.umbrella_species_altitudinal_range_environment_map))
            contiguous_areas_map = cover(scalar(temp_contiguous_areas_map), scalar(contiguous_areas_map))
        pure_contiguous_areas_LUTs_map = ifthen(scalar(contiguous_areas_map) != scalar(0),
                                                scalar(contiguous_areas_map))
        # map areas and select only above threshold value for clump
        to_be_calculated_areas_map = ifthen(scalar(pure_contiguous_areas_LUTs_map) != scalar(0),
                                            nominal(0))
        area_map = clump(to_be_calculated_areas_map)  # give all areas IDs
        area_map = areaarea(area_map)  # calculate each area
        # Result A: areas above area threshold
        pure_contiguous_areas_above_threshold_map = ifthen(
            scalar(area_map) >= scalar(user_defined_umbrella_species_minimum_patch_size),
            scalar(area_map))
        # Result B: areas with LUTs above area threshold
        pure_contiguous_areas_above_threshold_LUTs_map = ifthen(
            scalar(pure_contiguous_areas_above_threshold_map) != scalar(0),
            nominal(pure_contiguous_areas_LUTs_map))
        # Result C: nominal 0 for polygons above area threshold
        pure_contiguous_areas_above_threshold_polygons_map = ifthen(
            scalar(pure_contiguous_areas_above_threshold_map) != scalar(0),
            nominal(0))

        # extract the boolean landscape of ecosystem fragmentation for the umbrella species
        analysis_input_map = ifthen(scalar(pure_contiguous_areas_above_threshold_polygons_map) == scalar(0),
                                    boolean(1))

        # report the map for a GIF of ecosystem fragmentation
        # append the time step in format 001
        length_of_time_step = len(str(self.time_step))
        if length_of_time_step == 1:
            output_time_step_suffix = '00' + str(self.time_step)
        elif length_of_time_step == 2:
            output_time_step_suffix = '0' + str(self.time_step)
        elif length_of_time_step == 3:
            output_time_step_suffix = '' + str(self.time_step)

        umbrella_species_ecosystem_fragmentation_map = cover(scalar(analysis_input_map), scalar(self.null_mask_map))
        report(umbrella_species_ecosystem_fragmentation_map,
               os.path.join(Filepaths.folder_ecosystem_fragmentation_mplc, 'umbrella_species_ecosystem_fragmentation.' + output_time_step_suffix))
        print('reported umbrella_species_ecosystem_fragmentation_map')


        # create the Patch-ID map as input for PyLandStats
        clump_map = clump(analysis_input_map)
        self.maximum_number_of_patches = int(mapmaximum(scalar(clump_map)))
        self.total_area_of_patches = int(maptotal(scalar(analysis_input_map)))

        report(clump_map,
               os.path.join(Filepaths.folder_ecosystem_fragmentation_PatchID_mplc,
                            'umbrella_species_ecosystem_fragmentation_PatchID.' + output_time_step_suffix))
        print('reported umbrella_species_ecosystem_fragmentation PatchID map')

        if self.year in habitat_analysis_simulation_years_list:
            if Parameters.get_landscape_metrics_analysis_choice() == True:
                # perform the analysis on landscape with the singular patches (csv output) in PylandStats
                time_step = str(self.time_step)
                module = 'mplc'
                subprocess.run(['python', 'PyLandStats_adapter.py', time_step, module])

        print('calculating fragmentation and p.r.n. further user-defined landstats done')

        # =================================================================== #

        # model stage 2: OMNISCAPE & Circuitscape
    def calculate_umbrella_species_habitat_analysis_inputs(self):
        """produce on self.umbrella_species_altitudinal_range_environment_map the input files resistance, sources, grounds, polygons & habitat as .map outputs and transform them to .asc"""

        print('\ncalculating input files for Omniscape and Circuitscape  ...')

        # append the time step in format 001
        length_of_time_step = len(str(self.time_step))
        if length_of_time_step == 1:
            output_time_step_suffix = '00' + str(self.time_step)
        elif length_of_time_step == 2:
            output_time_step_suffix = '0' + str(self.time_step)
        elif length_of_time_step == 3:
            output_time_step_suffix = '' + str(self.time_step)

        # variables used in multiple methods:
        user_defined_umbrella_species_core_habitat_LUTs_list = Parameters.get_umbrella_species_core_habitat_LUTs_list()
        user_defined_umbrella_species_minimum_patch_size = Parameters.get_umbrella_species_minimum_patch_size()
        # map used in multiple methods: core LUTs continuos areas in altitudinal range
        # map with land use types
        contiguous_areas_map = self.null_mask_map
        for a_LUT in user_defined_umbrella_species_core_habitat_LUTs_list:
            temp_contiguous_areas_map = ifthen(scalar(a_LUT) == scalar(self.umbrella_species_altitudinal_range_environment_map),
                                               scalar(self.umbrella_species_altitudinal_range_environment_map))
            contiguous_areas_map = cover(scalar(temp_contiguous_areas_map), scalar(contiguous_areas_map))
        pure_contiguous_areas_LUTs_map = ifthen(scalar(contiguous_areas_map) != scalar(0),
                                           scalar(contiguous_areas_map))
        # map areas and select only above threshold value for clump
        to_be_calculated_areas_map = ifthen(scalar(pure_contiguous_areas_LUTs_map) != scalar(0),
                                                        nominal(0))
        area_map = clump(to_be_calculated_areas_map)  # give all areas IDs
        area_map = areaarea(area_map)  # calculate each area
        # Result A: areas above area threshold
        pure_contiguous_areas_above_threshold_map = ifthen(scalar(area_map) >= scalar(user_defined_umbrella_species_minimum_patch_size),
                                                           scalar(area_map))
        # Result B: areas with LUTs above area threshold
        pure_contiguous_areas_above_threshold_LUTs_map = ifthen(scalar(pure_contiguous_areas_above_threshold_map) != scalar(0),
                                                                nominal(pure_contiguous_areas_LUTs_map))
        # Result C: nominal 0 for polygons above area threshold
        pure_contiguous_areas_above_threshold_polygons_map = ifthen(scalar(pure_contiguous_areas_above_threshold_map) != scalar(0),
                                                                nominal(0))
        # Result D: numbered polygons above area threshold
        pure_contiguous_areas_above_threshold_polygons_numbered_map = clump(pure_contiguous_areas_above_threshold_polygons_map)



        # R E S I S T A N C E S
        user_defined_habitat_analysis_dictionary_resistances = Parameters.get_umbrella_species_LUTs_to_resistance_values_dictionary()

        # built the map
        resistance_map = scalar(self.null_mask_map)
        for a_LUT, a_resistance in user_defined_habitat_analysis_dictionary_resistances.items():
            temp_resistance_map = ifthen(scalar(self.umbrella_species_altitudinal_range_environment_map) == scalar(a_LUT),
                                         scalar(a_resistance))
            resistance_map = cover(temp_resistance_map, resistance_map)

        # eliminate 0 and -9999
        pure_resistance_map = ifthen(scalar(resistance_map) != (scalar(0)),
                                     scalar(resistance_map))

        pure_resistance_map = ifthen(scalar(pure_resistance_map) != (scalar(-9999)),
                                     scalar(pure_resistance_map))

        # if an extended extent is required, calculate it now with the map average value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_resistance_map
            # save raster to extract it later
            self.boolean_raster_resistances = boolean(raster)
            # padding value = raster average
            map_average_value = float( maptotal(scalar(raster)) / maptotal(scalar(boolean(raster))) )
            # transforming to numpy, filling mv and padded areas with map_average_value
            numpy_raster = pcr2numpy(raster, map_average_value)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant", constant_values=map_average_value)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_resistance_map
        # save as .map
        report_map_time_step_name = 'resistances_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_resistance_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_resistance_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_resistance_ascii,
                               'resistances_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.resistances_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_resistance_ascii,
                                                       'resistances_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()





        # S O U R C E S
        user_defined_habitat_analysis_dictionary_sources = Parameters.get_umbrella_species_LUTs_to_sources_in_amps_dictionary()
        sources_map = self.null_mask_map
        for a_LUT, a_source_value in user_defined_habitat_analysis_dictionary_sources.items():
            temp_source_map = ifthen(scalar(self.most_probable_landscape_configuration_map) == scalar(a_LUT),   #ifthen(scalar(pure_contiguous_areas_above_threshold_LUTs_map) == scalar(a_LUT)
                                     scalar(a_source_value))
            sources_map = cover(scalar(temp_source_map), scalar(sources_map))

        # eliminate 0 and -9999
        pure_sources_map = ifthen(scalar(sources_map) != scalar(0),
                                  scalar(sources_map))
        pure_sources_map = ifthen(scalar(pure_sources_map) != scalar(-9999),
                                  scalar(pure_sources_map))

        # if an extended extent is required, calculate it now with the mv value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_sources_map
            # save raster to extract it later
            self.boolean_raster_sources = boolean(raster)
            # transforming to numpy, filling mv and padded areas with mv value
            numpy_raster = pcr2numpy(raster, -9999)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant",
                                            constant_values=-9999)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_sources_map
        # save as .map
        report_map_time_step_name = 'sources_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_sources_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_sources_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_sources_ascii,
                               'sources_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.sources_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_sources_ascii,
                                                   'sources_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()



        # G R O U N D S
        user_defined_habitat_analysis_dictionary_grounds = Parameters.get_umbrella_species_LUTs_to_grounds_in_ohms_dictionary()

        # get a map of the grounds values in the altitudinal range
        initial_grounds_map = self.null_mask_map
        for a_LUT, a_ground_value in user_defined_habitat_analysis_dictionary_grounds.items():
            temp_grounds_map = ifthen(scalar(self.umbrella_species_altitudinal_range_environment_map) == scalar(a_LUT),
                                      scalar(a_ground_value))
            initial_grounds_map = cover(scalar(temp_grounds_map), scalar(initial_grounds_map))

        # select only the border pixels (find all pixels with less than 8 neighbors)
        scalar_self = scalar(boolean(self.umbrella_species_altitudinal_range_environment_map))
        # SH: Count cells within a 3x3 window to determine the forest fringe cells
        window_length = 3 * Parameters.get_cell_length_in_m()  # 9(-1) cells if not forest fringe
        number_neighbors_altitude_map = windowtotal(scalar_self, window_length) - scalar_self

        altitudinal_range_fringe_map = ifthen(scalar(number_neighbors_altitude_map) < scalar(8), # fringes are determined by missing pixels in the window (less than 9 (-1) present)
                                       scalar(1))

        # select only the core habitat pixels in the border pixels
        altitudinal_range_fringe_LUTs_map = ifthen(scalar(altitudinal_range_fringe_map) == scalar(1),
                                                   scalar(self.umbrella_species_altitudinal_range_environment_map))

        altitudinal_range_fringe_LUTs_core_habitat_map = self.null_mask_map
        for a_LUT in user_defined_umbrella_species_core_habitat_LUTs_list:
            temp_core_habitat_map = ifthen(scalar(a_LUT) == scalar(altitudinal_range_fringe_LUTs_map),
                                           scalar(altitudinal_range_fringe_LUTs_map))
            altitudinal_range_fringe_LUTs_core_habitat_map = cover(scalar(temp_core_habitat_map), scalar(altitudinal_range_fringe_LUTs_core_habitat_map))

        # transform to grounds map
        pure_grounds_map = ifthen(scalar(altitudinal_range_fringe_LUTs_core_habitat_map) > scalar(0),
                                  scalar(initial_grounds_map))

        # if an extended extent is required, calculate it now with the mv value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_grounds_map
            # save raster to extract it later
            self.boolean_raster_grounds = boolean(raster)
            # transforming to numpy, filling mv and padded areas with mv value
            numpy_raster = pcr2numpy(raster, -9999)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant",
                                            constant_values=-9999)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_grounds_map
        # save as .map
        report_map_time_step_name = 'grounds_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_grounds_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_grounds_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_grounds_ascii,
                               'grounds_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.grounds_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_grounds_ascii,
                                                   'grounds_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()



        # P O L Y G O N S
        pure_polygons_map = pure_contiguous_areas_above_threshold_polygons_numbered_map

        # if an extended extent is required, calculate it now with the mv value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_polygons_map
            # save raster to extract it later
            self.boolean_raster_polygons = boolean(raster)
            # transforming to numpy, filling mv and padded areas with mv value
            numpy_raster = pcr2numpy(raster, -9999)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant",
                                            constant_values=-9999)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_polygons_map
        # save as .map
        report_map_time_step_name = 'polygons_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_polygons_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_polygons_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_polygons_ascii,
                               'polygons_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.polygons_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_polygons_ascii,
                                                    'polygons_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()



        # P O I N T S
        # expression_map for areaorder:
        expression_map = ifthen(scalar(pure_polygons_map) > scalar(0),
                                ordinal(1))
        # number the cells within polygons
        areaorder_map = areaorder(expression_map, ordinal(pure_polygons_map))
        # get the cells with value 1 from each polygon and set the polygon number again
        pure_points_map = ifthen(scalar(areaorder_map) == scalar(1),
                                 scalar(pure_polygons_map))

        # if an extended extent is required, calculate it now with the mv value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_points_map
            # save raster to extract it later
            self.boolean_raster_points = boolean(raster)
            # transforming to numpy, filling mv and padded areas with mv value
            numpy_raster = pcr2numpy(raster, -9999)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant",
                                            constant_values=-9999)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_points_map
        # save as .map
        report_map_time_step_name = 'points_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_points_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_points_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_points_ascii,
                               'points_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.points_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_points_ascii,
                                                  'points_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()



        # H A B I T A T

        # built the map
        pure_habitat_map = pure_resistance_map

        # if an extended extent is required, calculate it now with the map average value
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # PADDING WITH RADIUS AND SUPPLYING MAP AVERAGE VALUE SURFACE
            # raster to expand by radius with map average value
            raster = pure_habitat_map
            # save raster to extract it later
            self.boolean_raster_habitat = boolean(raster)
            # padding value = raster average
            map_average_value = float(maptotal(scalar(raster)) / maptotal(scalar(boolean(raster))))
            # transforming to numpy, filling mv and padded areas with map_average_value
            numpy_raster = pcr2numpy(raster, map_average_value)
            cells_to_add = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_raster_padded = numpy.pad(numpy_raster, pad_width=cells_to_add, mode="constant",
                                            constant_values=map_average_value)
            _setclone_extended()
            # transforming to pcr
            numpy_raster_padded_map = numpy2pcr(dataType=pcraster.Scalar, array=numpy_raster_padded, mv=-9999)
        # REPORT
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            report_map = numpy_raster_padded_map
        else:
            report_map = pure_habitat_map
        # save as .map
        report_map_time_step_name = 'habitat_time_step_' + output_time_step_suffix + '.map'
        report(report_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_habitat_map, report_map_time_step_name))

        # transform to .asc as input file
        in_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_habitat_map, report_map_time_step_name)
        out_map = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_habitat_ascii,
                               'habitat_time_step_' + output_time_step_suffix + '.asc')
        map_to_asc(in_map, out_map)

        # save ascii file path for use in analysis
        self.habitat_file_time_step = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_habitat_ascii,
                                                   'habitat_time_step_' + output_time_step_suffix + '.asc')

        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            _setclone_original()


        #----------------------------------------------------------------------#
        # Preset variables and maps for tidy data and GIFs

        # regional base map for GIFs, report it to subfolder with time step suffix, overwrite it later if time step analysis is executed for that year

        if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True:
            self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map = self.null_mask_map
            report_map = self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map
            report_map_time_step_name = 'normalized_reclassified.' + output_time_step_suffix
            report(report_map,
                   os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape_transformed_normalized_reclassified, report_map_time_step_name))

        if PHC_simulation_dictionary['simulate_PHCs'] == True:
            self.Circuitscape_rescaled_voltmap_time_step_map = self.null_mask_map
            report_map = self.Circuitscape_rescaled_voltmap_time_step_map
            report_map_time_step_name = 'voltmap_rescaled.' + output_time_step_suffix
            report(report_map,
                   os.path.join(
                       Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_transformed_voltmap_rescaled,
                       report_map_time_step_name))

        # Omniscape output normalized variables for tidy data
        self.Omniscape_normalized_blocked_flow = None
        self.Omniscape_normalized_impeded_flow = None
        self.Omniscape_normalized_reduced_flow = None
        self.Omniscape_normalized_diffuse_flow = None
        self.Omniscape_normalized_intensified_flow = None
        self.Omniscape_normalized_channelized_flow = None

        print('\ncalculating input files for Omniscape and Circuitscape done')

        # =================================================================== #

        # model stage 2: OMNISCAPE
    def calculate_umbrella_species_habitat_connectivity(self):
        """If chosen, here is simulated habitat connectivity in Omniscape in Julia."""

        print('\nusing Omniscape  ...')

        # append the time step in format 001
        length_of_time_step = len(str(self.time_step))
        if length_of_time_step == 1:
            output_time_step_suffix = '00' + str(self.time_step)
        elif length_of_time_step == 2:
            output_time_step_suffix = '0' + str(self.time_step)
        elif length_of_time_step == 3:
            output_time_step_suffix = '' + str(self.time_step)

        # CREATE INI FILE

        # NAME .ini
        Omniscape_configuration_ini_time_step = '{0}{1}{2}'.format(str('Omniscape_configuration_time_step_'), str(output_time_step_suffix), str('.ini'))
        print(Omniscape_configuration_ini_time_step)

        # instantiate
        config = ConfigParser()

        # parse existing example file
        configuration_file = os.path.join(Filepaths.file_initial_habitat_analysis_Omniscape_configuration_ini)
        config.read(configuration_file)

        # update input files for the time step output ini
        config.set('Input files', 'resistance_file', self.resistances_file_time_step)
        config.set('Input files', 'source_file', self.sources_file_time_step)

        # update the output file name
        # delivers three outputs: normalized, cumulative, flow potential
        Omiscape_outputs_folder = Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape
        output_file_name = 'Connectivity_time_step_' + output_time_step_suffix
        output_file_path = os.path.join(Omiscape_outputs_folder, output_file_name)
        config.set('Options', 'project_name', output_file_path)

        # update further options
        config.set('Options', 'radius', str(LPBRAP_Omniscape_settings_dictionary['radius']))
        config.set('Options', 'block_size', str(LPBRAP_Omniscape_settings_dictionary['block_size']))
        config.set('Options', 'source_threshold', str(LPBRAP_Omniscape_settings_dictionary['source_threshold']))
        config.set('Options', 'source_from_resistance', str(LPBRAP_Omniscape_settings_dictionary['source_from_resistance']))
        config.set('Options', 'r_cutoff', str(LPBRAP_Omniscape_settings_dictionary['r_cutoff']))
        config.set('Options', 'connect_four_neighbors_only', str(LPBRAP_Omniscape_settings_dictionary['connect_four_neighbors_only']))
        config.set('Options', 'mask_nodata', str(LPBRAP_Omniscape_settings_dictionary['mask_nodata']))


        # save to a file
        Omniscape_time_step_configuration_ini_LPBRAP = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_Omniscape_ini_files, Omniscape_configuration_ini_time_step)
        with open(Omniscape_time_step_configuration_ini_LPBRAP, 'w') as configfile:
            config.write(configfile)

        # CALL OMNISCAPE
        subprocess.run(['python', 'Omniscape-in-julia_adapter.py', Omniscape_time_step_configuration_ini_LPBRAP])

        # Import NOMRALIZED CURRMAP from Omniscape:
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # SUBTRACTING PADDING AND FILLED IN AREAS
            _setclone_extended()
            # load and transform analysis output map
            in_filename_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                                             str('Connectivity_time_step_' + output_time_step_suffix),
                                                                             'normalized_cum_currmap.asc')
            extended_analysis_output_map = asc_to_map(clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                                                      in_filename= in_filename_ascii)
            # convert to numpy.ndarray 2D
            numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
            # subtract the halo by slicing
            cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_landscape_extent_original = numpy_landscape_extent_large[0 + cells_to_subtract : numpy_landscape_extent_large.shape[0] - cells_to_subtract,
                                                                           0 + cells_to_subtract : numpy_landscape_extent_large.shape[1] - cells_to_subtract].copy()
            # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
            _setclone_original()
            final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
            normalized_cumulative_current_map_time_step_map = ifthen(self.boolean_raster_resistances == boolean(1),
                                                                     scalar(final_map))
        else:
            # get the asc map in the original extent
            ## get the file
            normalized_cumulative_current_map_time_step_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                                             str('Connectivity_time_step_' + output_time_step_suffix),
                                                                             'normalized_cum_currmap.asc')
            ## transform it
            normalized_cumulative_current_map_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), normalized_cumulative_current_map_time_step_ascii)

        ## save for visualization in R
        report(normalized_cumulative_current_map_time_step_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape_PCRaster_normalized, 'normalized_cum_currmap.' + output_time_step_suffix))
        print('reported normalized_cumulative_current_map_time_step_map')

        # Import CUM CURRMAP from Omniscape:
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # SUBTRACTING PADDING AND FILLED IN AREAS
            _setclone_extended()
            # load and transform analysis output map
            in_filename_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                              str('Connectivity_time_step_' + output_time_step_suffix),
                                                              'cum_currmap.asc')
            extended_analysis_output_map = asc_to_map(clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                                                      in_filename= in_filename_ascii)
            # convert to numpy.ndarray 2D
            numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
            # subtract the halo by slicing
            cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_landscape_extent_original = numpy_landscape_extent_large[0 + cells_to_subtract : numpy_landscape_extent_large.shape[0] - cells_to_subtract,
                                                                           0 + cells_to_subtract : numpy_landscape_extent_large.shape[1] - cells_to_subtract].copy()
            # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
            _setclone_original()
            final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
            cumulative_current_map_time_step_map = ifthen(self.boolean_raster_resistances == boolean(1),
                                                          scalar(final_map))
        else:
            ## get the file
            cumulative_current_map_time_step_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                                  str('Connectivity_time_step_' + output_time_step_suffix),
                                                                  'cum_currmap.asc')
            ## transform it
            cumulative_current_map_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), cumulative_current_map_time_step_ascii)
        ## save for visualization in R
        report(cumulative_current_map_time_step_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape_PCRaster_cumulative, 'cum_currmap.' + output_time_step_suffix))
        print('reported cumulative_current_map_time_step_map')


        # Import flow_potential from Omniscape:
        if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
            # SUBTRACTING PADDING AND FILLED IN AREAS
            _setclone_extended()
            # load and transform analysis output map
            in_filename_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                          str('Connectivity_time_step_' + output_time_step_suffix),
                                                          'flow_potential.asc')
            extended_analysis_output_map = asc_to_map(clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                                                      in_filename= in_filename_ascii)
            # convert to numpy.ndarray 2D
            numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
            # subtract the halo by slicing
            cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
            numpy_landscape_extent_original = numpy_landscape_extent_large[0 + cells_to_subtract : numpy_landscape_extent_large.shape[0] - cells_to_subtract,
                                                                           0 + cells_to_subtract : numpy_landscape_extent_large.shape[1] - cells_to_subtract].copy()
            # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
            _setclone_original()
            final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
            flow_potential_map_time_step_map = ifthen(self.boolean_raster_resistances == boolean(1),
                                                      scalar(final_map))
        else:
            ## get the file
            flow_potential_map_time_step_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape,
                                                              str('Connectivity_time_step_' + output_time_step_suffix),
                                                              'flow_potential.asc')
            ## transform it
            flow_potential_map_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), flow_potential_map_time_step_ascii)
        ## save for visualization in R
        report(flow_potential_map_time_step_map,
               os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape_PCRaster_flow, 'flow_potential.' + output_time_step_suffix))
        print('reported flow_potential_map_time_step_map')

        #---------------------------------------------------------------------#
        # additional analysis and visualization on Omniscape output:

        reclassification_dict = Parameters.get_Omniscape_normalized_flow_classification_dictionary()

        for a_class, a_description_dict in reclassification_dict.items():
            for a_description, a_formula_dict in a_description_dict.items():
                an_operand = a_formula_dict.get('operand')
                a_threshold = a_formula_dict.get('threshold')

                def condition(a, b, operand):
                    if operand == "<":
                        return a < scalar(b)
                    elif operand == ">":
                        return a > scalar(b)
                    elif operand == ">=":
                        return a >= scalar(b)
                    elif operand == "<=":
                        return a <= scalar(b)
                    elif operand == "==":
                        return a == scalar(b)
                    elif operand == "!=":
                        return a != scalar(b)

                singular_class_map = ifthen(condition(scalar(normalized_cumulative_current_map_time_step_map), a_threshold, an_operand),
                                            scalar(a_class))
                self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map = cover(scalar(singular_class_map),
                                                                                                    scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map))
                # note the values
                if a_description == 'reduced_flow':
                    self.Omniscape_normalized_reduced_flow = int(maptotal(scalar(boolean(
                        scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                            a_class)))))
                elif a_description == 'impeded_flow':
                    self.Omniscape_normalized_impeded_flow = int(maptotal(scalar(boolean(
                        scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                            a_class)))))
                elif a_description == 'blocked_flow':
                    self.Omniscape_normalized_blocked_flow = int(maptotal(scalar(boolean(
                        scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                            a_class)))))
                elif a_description == 'diffuse_flow':
                    self.Omniscape_normalized_diffuse_flow = int(maptotal(scalar(boolean(
                        scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                            a_class)))))
                elif a_description == 'intensified_flow':
                    self.Omniscape_normalized_intensified_flow = int(maptotal(scalar(boolean(
                        scalar(self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                            a_class)))))
                elif a_description == 'channelized_flow':
                    self.Omniscape_normalized_channelized_flow = int(maptotal(scalar(boolean(scalar(
                        self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map) == scalar(
                        a_class)))))

        # save the reclassified map
        report_map = self.Omniscape_normalized_cumulative_current_reclassified_map_time_step_map
        report_map_time_step_name = 'normalized_reclassified.' + output_time_step_suffix
        report(report_map,
               os.path.join(
                   Filepaths.folder_habitat_analysis_mplc_outputs_Omniscape_transformed_normalized_reclassified,
                   report_map_time_step_name))

        print('\nusing Omniscape and transforming results done')

        # =================================================================== #

        # model stage 2: CIRCUITSCAPE
    def calculate_umbrella_species_PHCs(self):
        """If chosen, here are potential habitat corridors simulated in Circuitscape in Julia."""

        print('\nusing Circuitscape  ...')

        # append the time step in format 001
        length_of_time_step = len(str(self.time_step))
        if length_of_time_step == 1:
            output_time_step_suffix = '00' + str(self.time_step)
        elif length_of_time_step == 2:
            output_time_step_suffix = '0' + str(self.time_step)
        elif length_of_time_step == 3:
            output_time_step_suffix = '' + str(self.time_step)

        # NAME .ini
        Circuitscape_configuration_ini_time_step = '{0}{1}{2}'.format(str('Circuitscape_configuration_time_step_'),
                                                                   str(output_time_step_suffix), str('.ini'))
        print(Circuitscape_configuration_ini_time_step)

        # instantiate
        config = ConfigParser()

        # parse existing example file
        configuration_file = os.path.join(Filepaths.file_initial_habitat_analysis_Circuitscape_configuration_ini)
        config.read(configuration_file)

        # update input files for the time step output ini
        config.set('Options for advanced mode', 'source_file', self.sources_file_time_step)
        config.set('Options for advanced mode','ground_file', self.grounds_file_time_step)
        config.set('Short circuit regions (aka polygons)', 'polygon_file', self.polygons_file_time_step)
        config.set('Habitat raster or graph', 'habitat_file', self.habitat_file_time_step)
        # for non-advanced scenario runs:
        config.set('Options for pairwise and one-to-all and all-to-one modes', 'point_file', self.points_file_time_step)

        # update further options
        config.set('Options for advanced mode', 'ground_file_is_resistances', str(LPBRAP_Circuitscape_settings_dictionary['ground_file_is_resistances']))
        config.set('Options for advanced mode', 'remove_src_or_gnd', str(LPBRAP_Circuitscape_settings_dictionary['remove_src_or_gnd']))
        config.set('Options for advanced mode', 'use_unit_currents', str(LPBRAP_Circuitscape_settings_dictionary['use_unit_currents']))
        config.set('Options for advanced mode', 'use_direct_grounds', str(LPBRAP_Circuitscape_settings_dictionary['use_direct_grounds']))

        config.set('Output options', 'set_null_currents_to_nodata', str(LPBRAP_Circuitscape_settings_dictionary['set_null_currents_to_nodata']))
        config.set('Output options', 'set_null_voltages_to_nodata', str(LPBRAP_Circuitscape_settings_dictionary['set_null_voltages_to_nodata']))

        config.set('Short circuit regions (aka polygons)', 'use_polygons', str(LPBRAP_Circuitscape_settings_dictionary['use_polygons']))

        config.set('Connection scheme for raster habitat data', 'connect_four_neighbors_only', str(LPBRAP_Circuitscape_settings_dictionary['connect_four_neighbors_only']))
        config.set('Connection scheme for raster habitat data', 'connect_using_avg_resistances', str(LPBRAP_Circuitscape_settings_dictionary['connect_using_avg_resistances']))

        config.set('Circuitscape mode', 'scenario', str(LPBRAP_Circuitscape_settings_dictionary['scenario']))

        # update the output file name
        # delivers three outputs: .out file, curmap voltmap in asc

        Circuitscape_outputs_folder = Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape
        output_file_name = str('PHCs_time_step_' + output_time_step_suffix + '.out')
        output_file_path = os.path.join(Circuitscape_outputs_folder, output_file_name)
        config.set('Output options', 'output_file', output_file_path)

        # save to a file
        Circuitscape_time_step_configuration_ini_LPBRAP = os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs_Circuitscape_ini_files,
                                  Circuitscape_configuration_ini_time_step)
        with open(Circuitscape_time_step_configuration_ini_LPBRAP, 'w') as configfile:
            config.write(configfile)

        # CALL CIRCUITSCAPE
        subprocess.run(['python', 'Circuitscape-in-julia_adapter.py', Circuitscape_time_step_configuration_ini_LPBRAP])

        if PHC_simulation_dictionary['simulation_scenario'] == 'advanced':
            # Import curmap from Circuitscape:
            if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
                # SUBTRACTING PADDING AND FILLED IN AREAS
                _setclone_extended()
                # load and transform analysis output map
                in_filename_ascii = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape, str('PHCs_time_step_' + output_time_step_suffix + '_curmap.asc'))
                extended_analysis_output_map = asc_to_map(
                    clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                    in_filename=in_filename_ascii)
                # convert to numpy.ndarray 2D
                numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
                # subtract the halo by slicing
                cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
                numpy_landscape_extent_original = numpy_landscape_extent_large[
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             0] - cells_to_subtract,
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             1] - cells_to_subtract].copy()
                # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
                _setclone_original()
                final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
                curmap_time_step_map = ifthen(self.boolean_raster_habitat == boolean(1),
                                                          scalar(final_map))
            else:
                ## get the file
                curmap_time_step_ascii = os.path.join(
                    Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape,
                    str('PHCs_time_step_' + output_time_step_suffix + '_curmap.asc'))
                ## transform it
                curmap_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), curmap_time_step_ascii)
            ## save for visualization in R
            report(curmap_time_step_map,
                   os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_to_PCRaster_curmap, 'curmap.' + output_time_step_suffix))
            print('reported curmap_time_step_map')


            # Import voltmap from Circuitscape:
            if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
                # SUBTRACTING PADDING AND FILLED IN AREAS
                _setclone_extended()
                # load and transform analysis output map
                in_filename_ascii = os.path.join(
                    Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape,
                    str('PHCs_time_step_' + output_time_step_suffix + '_voltmap.asc'))
                extended_analysis_output_map = asc_to_map(
                    clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                    in_filename=in_filename_ascii)
                # convert to numpy.ndarray 2D
                numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
                # subtract the halo by slicing
                cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
                numpy_landscape_extent_original = numpy_landscape_extent_large[
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             0] - cells_to_subtract,
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             1] - cells_to_subtract].copy()
                # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
                _setclone_original()
                final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
                voltmap_time_step_map = ifthen(self.boolean_raster_habitat == boolean(1),
                                                          scalar(final_map))
            else:
                ## get the file
                voltmap_time_step_ascii = os.path.join(
                    Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape,
                    str('PHCs_time_step_' + output_time_step_suffix + '_voltmap.asc'))
                ## transform it
                voltmap_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), voltmap_time_step_ascii)
            ## save for visualization in R
            report(voltmap_time_step_map,
                   os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_to_PCRaster_voltmap, 'voltmap.' + output_time_step_suffix))
            print('reported voltmap_time_step_map')

        if PHC_simulation_dictionary['simulation_scenario'] == 'pairwise':
            # Import cumulative curmap from Circuitscape:
            if LPBRAP_Omniscape_settings_dictionary['simulation_buffer_integrated'] == False:
                # SUBTRACTING PADDING AND FILLED IN AREAS
                _setclone_extended()
                # load and transform analysis output map
                in_filename_ascii = os.path.join(
                    Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape,
                    str('PHCs_time_step_' + output_time_step_suffix + '_cum_curmap.asc'))
                extended_analysis_output_map = asc_to_map(
                    clone=os.path.join(Filepaths.folder_habitat_analysis_mplc_inputs, 'setclone_extended_input.map'),
                    in_filename=in_filename_ascii)
                # convert to numpy.ndarray 2D
                numpy_landscape_extent_large = pcr2numpy(extended_analysis_output_map, -9999)
                # subtract the halo by slicing
                cells_to_subtract = LPBRAP_Omniscape_settings_dictionary['radius']
                numpy_landscape_extent_original = numpy_landscape_extent_large[
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             0] - cells_to_subtract,
                                                  0 + cells_to_subtract: numpy_landscape_extent_large.shape[
                                                                             1] - cells_to_subtract].copy()
                # SETCLONE ORIGINAL, transform to PCR and subtract all filled in areas
                _setclone_original()
                final_map = numpy2pcr(pcraster.Scalar, numpy_landscape_extent_original, -9999)
                cum_curmap_time_step_map = ifthen(self.boolean_raster_habitat == boolean(1),
                                                          scalar(final_map))
            else:
                ## get the file
                cum_curmap_time_step_ascii = os.path.join(
                    Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape,
                    str('PHCs_time_step_' + output_time_step_suffix + '_cum_curmap.asc'))
                ## transform it
                cum_curmap_time_step_map = asc_to_map((f"{Filepaths.file_static_null_mask_input}.map"), cum_curmap_time_step_ascii)
            ## save for visualization in R
            report(cum_curmap_time_step_map,
                   os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_to_PCRaster_cum_curmap,
                                'cum_curmap.' + output_time_step_suffix))
            print('reported cum_curmap_time_step_map')

        #---------------------------------------------------------------------#
        # additional analysis on Circuitscape output

        if PHC_simulation_dictionary['simulation_scenario'] == 'advanced':
            # rescale voltmap_time_step_map to 0.01-1 each analyzed time step for averaging
            # first eliminate zeros
            pure_voltmap = ifthen(scalar(voltmap_time_step_map) != scalar(0),
                                  scalar(voltmap_time_step_map))

            # transform to numpy array, indicate mv
            numpy_pure_voltmap = pcr2numpy(pure_voltmap, -9999)

            # rescale operation to 0.1-1
            numpy_pure_voltmap_rescaled = numpy.interp(numpy_pure_voltmap, (numpy_pure_voltmap.min(), numpy_pure_voltmap.max()), (0.01, +1))

            # transform back to PCRaster
            pcraster_pure_voltmap_rescaled = numpy2pcr(pcraster.Scalar, numpy_pure_voltmap_rescaled, -9999)

            pure_voltmap_rescaled = ifthen(scalar(pure_voltmap) > scalar(0),
                                           pcraster_pure_voltmap_rescaled)

            # cover operation for GIF and averaging
            self.Circuitscape_rescaled_voltmap_time_step_map = cover(scalar(pure_voltmap_rescaled), scalar(self.Circuitscape_rescaled_voltmap_time_step_map))

            # save the rescaled map for GIFs etc.
            report_map = self.Circuitscape_rescaled_voltmap_time_step_map
            report_map_time_step_name = 'voltmap_rescaled.' + output_time_step_suffix
            report(report_map,
                   os.path.join(
                       Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_transformed_voltmap_rescaled,
                       report_map_time_step_name))
            print('reported self.Circuitscape_rescaled_voltmap_time_step_map')

        print('\nusing Circuitscape and transforming results done')

        # =================================================================== #

    def calculate_umbrella_species_averaged_time_frames(self):

        print('\naveraging user-defined time frames ...')

        # function for averaging
        def averaging_maps(input_maps, output_file_name):
            # derived from PCRaster MCaverage
            # calculate average
            sum = scalar(0)
            count = scalar(0)
            for input_map in input_maps:
                sum = sum + input_map
                count = ifthen(defined(input_map), count + 1)
            mean = sum / count
            # export result
            report(mean, output_file_name)

        # required user-input:
        user_defined_time_frames_for_averaging_nested_dictionary = Parameters.get_habitat_analysis_averaging_time_frames_dictionary()

        # convert time frames to time steps
        #(1) complete the lists
        simulation_years_complete_list = list(range(Parameters.get_initial_simulation_year(), Parameters.get_last_simulation_year() + 1))
        time_steps_complete_list = list(range(1, Parameters.get_number_of_time_steps() + 1))

        #(2) find the index positions of the years within the time steps and translate to updated dict
        user_defined_time_steps_for_averaging_dictionary_of_lists = {}
        for a_time_frame, a_time_range in user_defined_time_frames_for_averaging_nested_dictionary.items():
            print('time_frame:', a_time_frame)
            for key in a_time_range:
                start_year = a_time_range['first_year']
                print('start_year:', start_year)
                # find index position
                index_position_of_start_year = simulation_years_complete_list.index(start_year)
                # get the time step equivalent
                start_time_step = time_steps_complete_list[index_position_of_start_year]
                print('start_time_step:', start_time_step)
                last_year = a_time_range['last_year']
                print('last_year:', last_year)
                # find index position
                index_position_of_last_year = simulation_years_complete_list.index(last_year)
                # get the time step equivalent
                last_time_step = time_steps_complete_list[index_position_of_last_year]
                print('last_time_step:', last_time_step)
                # build a list
                time_steps_list = list(range(start_time_step, last_time_step + 1))
                # get to the actual time step format with zfill
                time_steps_list = [str(i).zfill(3) for i in time_steps_list]
                # now build the new dictionary
                user_defined_time_steps_for_averaging_dictionary_of_lists.update({a_time_frame:time_steps_list})

        if PHC_simulation_dictionary['simulation_scenario'] == 'advanced':
            # draw the maps, apply averaging and save results to subfolder with map suffix:
            for a_period, a_time_step_list in user_defined_time_steps_for_averaging_dictionary_of_lists.items():
                # rescaled Circuitscape voltmap
                period_maps = []

                for a_time_step in a_time_step_list:
                    print('a_time_step:', a_time_step)
                    file_path_of_map_of_time_step = os.path.join(
                        Filepaths.folder_habitat_analysis_mplc_outputs_Circuitscape_transformed_voltmap_rescaled,
                        'voltmap_rescaled.' + a_time_step)

                    map_of_time_step = readmap(file_path_of_map_of_time_step)
                    period_maps.append(map_of_time_step)

                output_file_path = os.path.join(Filepaths.folder_habitat_analysis_mplc_outputs, 'LPB-RAP_averaged_results')
                os.makedirs(output_file_path, exist_ok=True)
                output_file_name = f'{Parameters.get_umbrella_species_name()}_averaged_rescaled_voltmap_period_{a_period}.map'

                # apply function
                print('averaging, this may take a while')
                averaging_maps(input_maps=period_maps,
                               output_file_name=os.path.join(output_file_path, output_file_name))

                print('reported', output_file_name, 'to', output_file_path)

        print('\naveraging user-defined time frames done')

        # =================================================================== #

    def save_data_last_time_step_for_comparison(self):
        """SH: Simply saving the required maps and values for the next time step to compare."""

        print('\nsaving the most probable landscape configuration for calculations in the next time step  ...')

        self.mplc_environment_last_time_step = self.most_probable_landscape_configuration_map

        self.allocated_pixels_LUT02_last_time_step = self.allocated_pixels_LUT02
        self.unallocated_pixels_LUT02_last_time_step = self.unallocated_pixels_LUT02

        self.allocated_pixels_LUT03_last_time_step = self.allocated_pixels_LUT03
        self.unallocated_pixels_LUT03_last_time_step = self.unallocated_pixels_LUT03

        self.allocated_pixels_LUT04_last_time_step = self.allocated_pixels_LUT04
        self.unallocated_pixels_LUT04_last_time_step = self.unallocated_pixels_LUT04

        print('saving the most probable landscape configuration for calculations in the next time step done')
        # =================================================================== #

    def export_data_to_LPB_mplc_log_file(self):
        """ SH: Note the according variables in the CSV file for further analysis."""

        # note the data in the LPB-mplc_log-file
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-mplc_log-file.csv'),'a', newline='') as LPB_mplc_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_mplc_log_file)
            LPB_mplc_log_file_data = [self.time_step,
                                      self.year,
                                      self.population,
                                      # anthropogenic features
                                      self.cities,
                                      self.settlements,
                                      self.streets,
                                      self.built_up_additionally,
                                      # anthropogenic impact buffer 1 total area
                                      self.anthropogenic_impact_buffer_area,
                                      self.percentage_of_landscape_anthropogenic_impact_buffer,
                                      #LUT01
                                      self.demand_LUT01,
                                      self.allocated_pixels_LUT01,
                                      self.percentage_of_landscape_LUT01,
                                      self.allocated_pixels_in_difficult_terrain_LUT01_area,
                                      self.percentage_of_landscape_difficult_terrain_LUT01,
                                      self.LUT01_mplc_in_restricted_areas_area,
                                      self.percentage_of_landscape_LUT01_in_restricted_areas,
                                      self.LUT01_mplc_new_in_restricted_areas_area,
                                      self.LUT01_mplc_new_on_former_forest_pixel_area,
                                      self.settlements_local_LUT01_area,
                                      self.percentage_of_landscape_settlements_local_LUT01,
                                      self.regional_excess_LUT01,
                                      self.percentage_of_landscape_regional_excess_LUT01,
                                      self.unallocated_pixels_LUT01,
                                      # LUT02
                                      self.demand_LUT02,
                                      self.allocated_pixels_LUT02,
                                      self.percentage_of_landscape_LUT02,
                                      self.allocated_pixels_in_difficult_terrain_LUT02_area,
                                      self.percentage_of_landscape_difficult_terrain_LUT02,
                                      self.LUT02_mplc_in_restricted_areas_area,
                                      self.percentage_of_landscape_LUT02_in_restricted_areas,
                                      self.LUT02_mplc_new_in_restricted_areas_area,
                                      self.LUT02_mplc_new_on_former_forest_pixel_area,
                                      self.settlements_local_LUT02_area,
                                      self.percentage_of_landscape_settlements_local_LUT02,
                                      self.regional_excess_LUT02,
                                      self.percentage_of_landscape_regional_excess_LUT02,
                                      self.unallocated_pixels_LUT02,
                                      # LUT03
                                      self.demand_LUT03,
                                      self.allocated_pixels_LUT03,
                                      self.percentage_of_landscape_LUT03,
                                      self.allocated_pixels_in_difficult_terrain_LUT03_area,
                                      self.percentage_of_landscape_difficult_terrain_LUT03,
                                      self.LUT03_mplc_in_restricted_areas_area,
                                      self.percentage_of_landscape_LUT03_in_restricted_areas,
                                      self.LUT03_mplc_new_in_restricted_areas_area,
                                      self.LUT03_mplc_new_on_former_forest_pixel_area,
                                      self.settlements_local_LUT03_area,
                                      self.percentage_of_landscape_settlements_local_LUT03,
                                      self.regional_excess_LUT03,
                                      self.percentage_of_landscape_regional_excess_LUT03,
                                      self.unallocated_pixels_LUT03,
                                      # LUT04
                                      self.demand_LUT04,
                                      self.allocated_pixels_LUT04,
                                      self.percentage_of_landscape_LUT04,
                                      self.allocated_pixels_in_difficult_terrain_LUT04_area,
                                      self.percentage_of_landscape_difficult_terrain_LUT04,
                                      self.LUT04_mplc_in_restricted_areas_area,
                                      self.percentage_of_landscape_LUT04_in_restricted_areas,
                                      self.LUT04_mplc_new_in_restricted_areas_area,
                                      self.LUT04_mplc_new_on_former_forest_pixel_area,
                                      self.settlements_local_LUT04_area,
                                      self.percentage_of_landscape_settlements_local_LUT04,
                                      self.regional_excess_LUT04,
                                      self.percentage_of_landscape_regional_excess_LUT04,
                                      self.unallocated_pixels_LUT04,
                                      # LUT05
                                      self.demand_LUT05,
                                      self.allocated_pixels_LUT05,
                                      self.percentage_of_landscape_LUT05,
                                      self.allocated_pixels_in_difficult_terrain_LUT05_area,
                                      self.percentage_of_landscape_difficult_terrain_LUT05,
                                      self.LUT05_mplc_in_restricted_areas_area,
                                      self.percentage_of_landscape_LUT05_in_restricted_areas,
                                      self.LUT05_mplc_new_in_restricted_areas_area,
                                      self.LUT05_mplc_new_on_former_forest_pixel_area,
                                      self.settlements_local_LUT05_area,
                                      self.percentage_of_landscape_settlements_local_LUT05,
                                      self.regional_excess_LUT05,
                                      self.percentage_of_landscape_regional_excess_LUT05,
                                      self.unallocated_pixels_LUT05,
                                      # LUT06
                                      self.allocated_pixels_LUT06,
                                      self.percentage_of_landscape_LUT06,
                                      # LUT07
                                      self.allocated_pixels_LUT07,
                                      self.percentage_of_landscape_LUT07,
                                      # LUT08
                                      self.allocated_pixels_LUT08,
                                      self.percentage_of_landscape_LUT08,
                                      # LUT09
                                      self.allocated_pixels_LUT09,
                                      self.percentage_of_landscape_LUT09,
                                      # LUT10
                                      self.allocated_pixels_LUT10,
                                      self.percentage_of_landscape_LUT10,
                                      # LUT11
                                      self.allocated_pixels_LUT11,
                                      self.percentage_of_landscape_LUT11,
                                      # LUT12
                                      self.allocated_pixels_LUT12,
                                      self.percentage_of_landscape_LUT12,
                                      # LUT13
                                      self.allocated_pixels_LUT13,
                                      self.percentage_of_landscape_LUT13,
                                      # LUT14
                                      self.allocated_pixels_LUT14,
                                      self.percentage_of_landscape_LUT14,
                                      # LUT15
                                      self.allocated_pixels_LUT15,
                                      self.percentage_of_landscape_LUT15,
                                      # LUT16
                                      self.allocated_pixels_LUT16,
                                      self.percentage_of_landscape_LUT16,
                                      # LUT17
                                      self.demand_AGB,
                                      self.demand_LUT17_minimum,
                                      self.demand_LUT17_mean,
                                      self.demand_LUT17_maximum,
                                      self.allocated_pixels_LUT17,
                                      self.percentage_of_landscape_LUT17,
                                      # LUT18
                                      self.allocated_pixels_LUT18,
                                      self.percentage_of_landscape_LUT18,
                                      # LUT19
                                      self.allocated_pixels_LUT19,
                                      self.percentage_of_landscape_LUT19,
                                      # AGB Mg harvested

                                      # HIDDEN DEFORESTATION
                                      self.maximum_deforested_for_input_biomass_area,
                                      self.maximum_deforested_for_input_biomass_percentage_of_landscape,

                                      # CONVERTED FOREST (new land use type)
                                      self.converted_forest_area,
                                      self.converted_forest_area_percentage_of_landscape,

                                      # LANDSCAPE MODELLING PROBABILITY/UNCERTAINTY
                                      self.pixels_in_probability_class_1,
                                      self.percentage_of_landscape_probability_class_1,
                                      self.pixels_in_probability_class_2,
                                      self.percentage_of_landscape_probability_class_2,
                                      self.pixels_in_probability_class_3,
                                      self.percentage_of_landscape_probability_class_3,
                                      self.pixels_in_probability_class_4,
                                      self.percentage_of_landscape_probability_class_4,
                                      self.pixels_in_probability_class_5,
                                      self.percentage_of_landscape_probability_class_5,
                                      self.pixels_in_probability_class_6,
                                      self.percentage_of_landscape_probability_class_6,
                                      self.pixels_in_probability_class_7,
                                      self.percentage_of_landscape_probability_class_7,

                                      # LAND USE IN RESTRICTED AREAS
                                      self.restricted_areas_area,
                                      self.restricted_areas_area_percentage_of_landscape,
                                      self.total_of_land_use_in_restricted_areas_area,
                                      self.total_of_land_use_in_restricted_areas_area_percentage_of_restricted_area,
                                      self.total_of_new_land_use_in_restricted_areas_area,
                                      self.total_of_new_land_use_in_restricted_areas_area_percentage_of_restricted_area,
                                      self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area,
                                      self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area_percentage_of_restricted_area,
                                      self.mplc_disturbed_in_restricted_areas_area,
                                      self.mplc_disturbed_in_restricted_areas_percentage_of_restricted_area,
                                      self.mplc_undisturbed_in_restricted_areas_area,
                                      self.mplc_undisturbed_in_restricted_areas_percentage_of_restricted_area,

                                      # FOREST net gross disturbed undisturbed
                                      self.gross_forest_mplc_area,
                                      self.gross_forest_mplc_percentage_of_landscape,
                                      self.net_forest_mplc_area,
                                      self.net_forest_mplc_percentage_of_landscape,
                                      self.gross_mplc_disturbed_forest_area,
                                      self.gross_mplc_disturbed_forest_percentage_of_landscape,
                                      self.gross_mplc_undisturbed_forest_area,
                                      self.gross_mplc_undisturbed_forest_percentage_of_landscape,
                                      self.net_mplc_disturbed_forest_area,
                                      self.net_mplc_disturbed_forest_percentage_of_landscape,
                                      self.net_mplc_undisturbed_forest_area,
                                      self.net_mplc_undisturbed_forest_percentage_of_landscape,
                                      self.gross_minus_net_forest_disturbed_mplc_area,
                                      self.gross_minus_net_forest_disturbed_mplc_percentage_of_landscape,
                                      self.gross_minus_net_forest_undisturbed_mplc_area,
                                      self.gross_minus_net_forest_undisturbed_mplc_percentage_of_landscape,

                                      # TRUE FOREST IMPACTED BY ANTHROPOGENIC FEATURES (LUT08)
                                      self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area,
                                      self.true_gross_forest_impacted_by_anthropogenic_features_mplc_percentage_of_landscape,
                                      self.true_net_forest_impacted_by_anthropogenic_features_mplc_area,
                                      self.true_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest,
                                      self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area,
                                      self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest,

                                      # FOREST DEGRADATION/REGENERATION
                                      # 1) degradation
                                      # degradation low
                                      self.low_degradation_net_forest_mplc_area,
                                      self.low_degradation_net_forest_mplc_percentage_of_landscape,
                                      self.low_degradation_gross_forest_mplc_area,
                                      self.low_degradation_gross_forest_mplc_percentage_of_landscape,
                                      self.low_degradation_gross_minus_net_forest_mplc_area,
                                      self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # degradation moderate
                                      self.moderate_degradation_net_forest_mplc_area,
                                      self.moderate_degradation_net_forest_mplc_percentage_of_landscape,
                                      self.moderate_degradation_gross_forest_mplc_area,
                                      self.moderate_degradation_gross_forest_mplc_percentage_of_landscape,
                                      self.moderate_degradation_gross_minus_net_forest_mplc_area,
                                      self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # degradation severe
                                      self.severe_degradation_net_forest_mplc_area,
                                      self.severe_degradation_net_forest_mplc_percentage_of_landscape,
                                      self.severe_degradation_gross_forest_mplc_area,
                                      self.severe_degradation_gross_forest_mplc_percentage_of_landscape,
                                      self.severe_degradation_gross_minus_net_forest_mplc_area,
                                      self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # degradation absolute (= LUT17 net forest deforested)
                                      self.absolute_degradation_net_forest_mplc_area,
                                      self.absolute_degradation_net_forest_mplc_percentage_of_landscape,
                                      self.absolute_degradation_net_forest_disturbed_mplc_area,
                                      self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape,
                                      self.absolute_degradation_net_forest_undisturbed_mplc_area,
                                      self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape,

                                      # 2) regeneration
                                      # regeneration low
                                      self.low_regeneration_net_forest_mplc_area,
                                      self.low_regeneration_net_forest_mplc_percentage_of_landscape,
                                      self.low_regeneration_gross_forest_mplc_area,
                                      self.low_regeneration_gross_forest_mplc_percentage_of_landscape,
                                      self.low_regeneration_gross_minus_net_forest_mplc_area,
                                      self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # regeneration medium
                                      self.medium_regeneration_net_forest_mplc_area,
                                      self.medium_regeneration_net_forest_mplc_percentage_of_landscape,
                                      self.medium_regeneration_gross_forest_mplc_area,
                                      self.medium_regeneration_gross_forest_mplc_percentage_of_landscape,
                                      self.medium_regeneration_gross_minus_net_forest_mplc_area,
                                      self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # regeneration high
                                      self.high_regeneration_net_forest_mplc_area,
                                      self.high_regeneration_net_forest_mplc_percentage_of_landscape,
                                      self.high_regeneration_gross_forest_mplc_area,
                                      self.high_regeneration_gross_forest_mplc_percentage_of_landscape,
                                      self.high_regeneration_gross_minus_net_forest_mplc_area,
                                      self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      # regeneration full (climax stadium, still not all primary forest traits given))
                                      self.full_regeneration_net_forest_mplc_area,
                                      self.full_regeneration_net_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_gross_forest_mplc_area,
                                      self.full_regeneration_gross_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_disturbed_forest_net_forest_mplc_area,
                                      self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_disturbed_forest_gross_forest_mplc_area,
                                      self.full_regeneration_disturbed_forest_gross_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area,
                                      self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_undisturbed_forest_net_forest_mplc_area,
                                      self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_undisturbed_forest_gross_forest_mplc_area,
                                      self.full_regeneration_undisturbed_forest_gross_forest_mplc_percentage_of_landscape,
                                      self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area,
                                      self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape,


                                      # FOREST AGB in Mg -> tC
                                      # potential maximum AGB
                                      self.potential_maximum_undisturbed_forest_AGB_maptotal,
                                      self.potential_maximum_undisturbed_forest_AGB_Carbon,
                                      # initial AGB simulation start
                                      self.initial_AGB_maptotal,
                                      self.initial_AGB_Carbon,
                                      self.initial_AGB_percentage_of_potential_maximum_undisturbed_AGB,
                                      # demand AGB for the time step
                                      self.demand_timber_AGB,
                                      self.demand_fuelwood_AGB,
                                      self.demand_charcoal_AGB,
                                      self.demand_AGB,
                                      # final total AGB for the time step
                                      self.final_AGB_gross_forest_maptotal,
                                      self.final_AGB_gross_forest_Carbon,
                                      self.final_AGB_net_forest_maptotal,
                                      self.final_AGB_net_forest_Carbon,
                                      self.final_AGB_gross_minus_net_forest_maptotal,
                                      self.final_AGB_gross_minus_net_forest_Carbon,

                                      # final AGB agroforestry
                                      self.final_agroforestry_AGB_maptotal,
                                      self.final_agroforestry_AGB_Carbon,
                                      # final AGB plantation
                                      self.final_plantation_AGB_maptotal,
                                      self.final_plantation_AGB_Carbon,
                                      # final AGB disturbed forest
                                      self.final_disturbed_forest_AGB_gross_forest_maptotal,
                                      self.final_disturbed_forest_AGB_gross_forest_Carbon,
                                      self.final_disturbed_forest_AGB_net_forest_maptotal,
                                      self.final_disturbed_forest_AGB_net_forest_Carbon,
                                      self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest,
                                      self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal,
                                      self.final_disturbed_forest_AGB_gross_minus_net_forest_Carbon,
                                      self.final_disturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_disturbed_forest,
                                      # final AGB undisturbed forest
                                      self.final_undisturbed_forest_AGB_gross_forest_maptotal,
                                      self.final_undisturbed_forest_AGB_gross_forest_Carbon,
                                      self.final_undisturbed_forest_AGB_net_forest_maptotal,
                                      self.final_undisturbed_forest_AGB_net_forest_Carbon,
                                      self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest,
                                      self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal,
                                      self.final_undisturbed_forest_AGB_gross_minus_net_forest_Carbon,
                                      self.final_undisturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_undisturbed_forest,


                                      # FOREST REMAINING without direct anthropogenic impact
                                      # gross forest
                                      # undisturbed
                                      self.remaining_gross_undisturbed_forest_without_impact_area,
                                      self.remaining_gross_undisturbed_forest_without_impact_percentage_of_landscape,
                                      # disturbed
                                      self.remaining_gross_disturbed_forest_without_impact_area,
                                      self.remaining_gross_disturbed_forest_without_impact_percentage_of_landscape,
                                      # net forest
                                      # undisturbed
                                      self.remaining_net_undisturbed_forest_without_impact_area,
                                      self.remaining_net_undisturbed_forest_without_impact_percentage_of_landscape,
                                      # disturbed
                                      self.remaining_net_disturbed_forest_without_impact_area,
                                      self.remaining_net_disturbed_forest_without_impact_percentage_of_landscape,
                                      # gross minus net
                                      # undisturbed
                                      self.remaining_gross_minus_net_undisturbed_forest_without_impact_area,
                                      self.remaining_gross_minus_net_undisturbed_forest_without_impact_percentage_of_landscape,
                                      # disturbed
                                      self.remaining_gross_minus_net_disturbed_forest_without_impact_area,
                                      self.remaining_gross_minus_net_disturbed_forest_without_impact_percentage_of_landscape,

                                      # FOREST 100 years without anthropogenic impact (potential primary stadium)
                                      # former disturbed forest
                                      self.former_disturbed_gross_forest_100years_without_impact_area,
                                      self.former_disturbed_gross_forest_100years_without_impact_percentage_of_landscape,
                                      self.former_disturbed_net_forest_100years_without_impact_area,
                                      self.former_disturbed_net_forest_100years_without_impact_percentage_of_landscape,
                                      self.former_disturbed_gross_minus_net_forest_100years_without_impact_area,
                                      self.former_disturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape,
                                      # initial undisturbed forest
                                      self.initial_undisturbed_gross_forest_100years_without_impact_area,
                                      self.initial_undisturbed_gross_forest_100years_without_impact_percentage_of_landscape,
                                      self.initial_undisturbed_net_forest_100years_without_impact_area,
                                      self.initial_undisturbed_net_forest_100years_without_impact_percentage_of_landscape,
                                      self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area,
                                      self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape,

                                      # FOREST HABITAT DISTURBED AND UNDISTURBED
                                      self.mplc_disturbed_forest_fringe_area,
                                      self.mplc_disturbed_forest_fringe_percentage_of_landscape,
                                      self.mplc_undisturbed_forest_habitat_area,
                                      self.mplc_undisturbed_forest_habitat_percentage_of_landscape,

                                      # 5 TOP CROPS YIELDS
                                      # 1
                                      self.top_crops_data_lists_dictionary[1]['share_of_LUT_acreage'],
                                      self.top_crops_data_lists_dictionary[1]['yield_minimum'],
                                      self.top_crops_data_lists_dictionary[1]['yield_mean'],
                                      self.top_crops_data_lists_dictionary[1]['yield_maximum'],
                                      # 2
                                      self.top_crops_data_lists_dictionary[2]['share_of_LUT_acreage'],
                                      self.top_crops_data_lists_dictionary[2]['yield_minimum'],
                                      self.top_crops_data_lists_dictionary[2]['yield_mean'],
                                      self.top_crops_data_lists_dictionary[2]['yield_maximum'],
                                      # 3
                                      self.top_crops_data_lists_dictionary[3]['share_of_LUT_acreage'],
                                      self.top_crops_data_lists_dictionary[3]['yield_minimum'],
                                      self.top_crops_data_lists_dictionary[3]['yield_mean'],
                                      self.top_crops_data_lists_dictionary[3]['yield_maximum'],
                                      # 4
                                      self.top_crops_data_lists_dictionary[4]['share_of_LUT_acreage'],
                                      self.top_crops_data_lists_dictionary[4]['yield_minimum'],
                                      self.top_crops_data_lists_dictionary[4]['yield_mean'],
                                      self.top_crops_data_lists_dictionary[4]['yield_maximum'],
                                      # 5
                                      self.top_crops_data_lists_dictionary[5]['share_of_LUT_acreage'],
                                      self.top_crops_data_lists_dictionary[5]['yield_minimum'],
                                      self.top_crops_data_lists_dictionary[5]['yield_mean'],
                                      self.top_crops_data_lists_dictionary[5]['yield_maximum']
                                      ]
            writer.writerow(LPB_mplc_log_file_data)
            print('\nadded time step ' + str(self.year) + ' data to LPB-mplc_log-file')

        if self.time_step == Parameters.get_number_of_time_steps():
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-mplc_log-file.csv'), 'a', newline='') as LPB_mplc_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_mplc_log_file)
                writer.writerow([])
                writer.writerow(['PLEASE NOTE:'])
                writer.writerow(['all values are:'])
                writer.writerow(['either the number of simulated pixels (discrete number),'])
                writer.writerow(['___in this model application equivalent with: ' + str(Parameters.get_pixel_size())])
                writer.writerow(['or the percentage (given with two decimal digits) in reference to'])
                writer.writerow(['___the complete simulated region [if not noted otherwise],'])
                writer.writerow(['___in this simulation equivalent to: ' + str(self.hundred_percent_area) + str(' ') + str(Parameters.get_pixel_size())])
                writer.writerow([])
                writer.writerow(['* Gross forest: Based on Copernicus pixels of forest (>15 % tree coverage for a 100x100m pixel). Can contain up to all of the the LUTs 08(disturbed forest), 09(undisturbed forest), 04(agroforestry) and 05(plantations) if not noted otherwise. LUT08 and 09 may also contain parks and gardens in the landscape.'])
                writer.writerow(['* Net forest: Initial net forest file is the as „forest“ declared land surface by national maps. The actual percentage in LPB may differ since it only recognizes LUT 08 and 09 as forest and passes those on dynamically (with subtraction and addition at the forest fringe).'])
                writer.writerow([])
                writer.writerow(['Variables per time step: ' + str(len(LPB_mplc_log_file_data))])
                writer.writerow(['Entries for ' + str(Parameters.get_number_of_time_steps()) + ' time steps in total: ' + str(Parameters.get_number_of_time_steps() * len(LPB_mplc_log_file_data))])
                writer.writerow([])
                writer.writerow(['Aggregation in LPB-mplc based on LPB-basic samples: ' + str(self.original_number_of_samples)])
                if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
                    writer.writerow([])
                    writer.writerow(['Simulation of most probable landscape configuration conducted WITH additional corrective allocation to simulate maximum anthropogenic impact.'])
                elif Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == False:
                    writer.writerow([])
                    writer.writerow(['Simulation of most probable landscape configuration conducted WITHOUT additional corrective allocation to simulate maximum anthropogenic impact.'])
                if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
                    writer.writerow([])
                    writer.writerow(['Population peak year: ' + str(self.population_peak_year)])
                    writer.writerow(['Peak demands year: ' + str(self.peak_demands_year)])

    def export_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        output_files_data = {
            'LPB_area_demands_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.demand_LUT01],
                ['LUT02', self.demand_LUT02],
                ['LUT03', self.demand_LUT03],
                ['LUT04', self.demand_LUT04],
                ['LUT05', self.demand_LUT05],
            ],
            'LPB_AGB_demand_' + str(Parameters.get_model_scenario()): [
                [self.demand_AGB]
            ],

            'LPB_anthropogenic_features_' + str(Parameters.get_model_scenario()): [
                ['cities', self.cities],
                ['settlements', self.settlements],
                ['streets', self.streets],
                ['additional_built-up', self.built_up_additionally]
            ],
            'LPB_anthropogenic_impact_buffer_' + str(Parameters.get_model_scenario()): [
                [self.anthropogenic_impact_buffer_area, self.percentage_of_landscape_anthropogenic_impact_buffer]
            ],
            'LPB_land_use_mplc_'+ str(Parameters.get_model_scenario()): [
                ['LUT01', self.allocated_pixels_LUT01, self.percentage_of_landscape_LUT01],
                ['LUT02', self.allocated_pixels_LUT02, self.percentage_of_landscape_LUT02],
                ['LUT03', self.allocated_pixels_LUT03, self.percentage_of_landscape_LUT03],
                ['LUT04', self.allocated_pixels_LUT04, self.percentage_of_landscape_LUT04],
                ['LUT05', self.allocated_pixels_LUT05, self.percentage_of_landscape_LUT05],
                ['LUT06', self.allocated_pixels_LUT06, self.percentage_of_landscape_LUT06],
                ['LUT07', self.allocated_pixels_LUT07, self.percentage_of_landscape_LUT07],
                ['LUT08', self.allocated_pixels_LUT08, self.percentage_of_landscape_LUT08],
                ['LUT09', self.allocated_pixels_LUT09, self.percentage_of_landscape_LUT09],
                ['LUT10', self.allocated_pixels_LUT10, self.percentage_of_landscape_LUT10],
                ['LUT11', self.allocated_pixels_LUT11, self.percentage_of_landscape_LUT11],
                ['LUT12', self.allocated_pixels_LUT12, self.percentage_of_landscape_LUT12],
                ['LUT13', self.allocated_pixels_LUT13, self.percentage_of_landscape_LUT13],
                ['LUT14', self.allocated_pixels_LUT14, self.percentage_of_landscape_LUT14],
                ['LUT15', self.allocated_pixels_LUT15, self.percentage_of_landscape_LUT15],
                ['LUT16', self.allocated_pixels_LUT16, self.percentage_of_landscape_LUT16],
                ['LUT17', self.allocated_pixels_LUT17, self.percentage_of_landscape_LUT17],
                ['LUT18', self.allocated_pixels_LUT18, self.percentage_of_landscape_LUT18],
                ['LUT19', self.allocated_pixels_LUT19, self.percentage_of_landscape_LUT19]
            ],
            'LPB_land_use_mplc_difficult_terrain_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.allocated_pixels_in_difficult_terrain_LUT01_area, self.percentage_of_landscape_difficult_terrain_LUT01],
                ['LUT02', self.allocated_pixels_in_difficult_terrain_LUT02_area, self.percentage_of_landscape_difficult_terrain_LUT02],
                ['LUT03', self.allocated_pixels_in_difficult_terrain_LUT03_area, self.percentage_of_landscape_difficult_terrain_LUT03],
                ['LUT04', self.allocated_pixels_in_difficult_terrain_LUT04_area, self.percentage_of_landscape_difficult_terrain_LUT04],
                ['LUT05', self.allocated_pixels_in_difficult_terrain_LUT05_area, self.percentage_of_landscape_difficult_terrain_LUT05]
            ],
            'LPB_land_use_mplc_restricted_areas_accumulated_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.LUT01_mplc_in_restricted_areas_area, self.percentage_of_landscape_LUT01_in_restricted_areas],
                ['LUT02', self.LUT02_mplc_in_restricted_areas_area, self.percentage_of_landscape_LUT02_in_restricted_areas],
                ['LUT03', self.LUT03_mplc_in_restricted_areas_area, self.percentage_of_landscape_LUT03_in_restricted_areas],
                ['LUT04', self.LUT04_mplc_in_restricted_areas_area, self.percentage_of_landscape_LUT04_in_restricted_areas],
                ['LUT05', self.LUT05_mplc_in_restricted_areas_area, self.percentage_of_landscape_LUT05_in_restricted_areas]
            ],
            'LPB_land_use_mplc_restricted_areas_new_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.LUT01_mplc_new_in_restricted_areas_area],
                ['LUT02', self.LUT02_mplc_new_in_restricted_areas_area],
                ['LUT03', self.LUT03_mplc_new_in_restricted_areas_area],
                ['LUT04', self.LUT04_mplc_new_in_restricted_areas_area],
                ['LUT05', self.LUT05_mplc_new_in_restricted_areas_area]
            ],
            'LPB_land_use_mplc_restricted_areas_new_on_former_forest_pixels_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.LUT01_mplc_new_on_former_forest_pixel_area],
                ['LUT02', self.LUT02_mplc_new_on_former_forest_pixel_area],
                ['LUT03', self.LUT03_mplc_new_on_former_forest_pixel_area],
                ['LUT04', self.LUT04_mplc_new_on_former_forest_pixel_area],
                ['LUT05', self.LUT05_mplc_new_on_former_forest_pixel_area]
            ],
            'LPB_land_use_mplc_restricted_areas_remaining_forest_' + str(Parameters.get_model_scenario()): [
                ['LUT08', self.mplc_disturbed_in_restricted_areas_area],
                ['LUT09', self.mplc_undisturbed_in_restricted_areas_area]
            ],
            'LPB_land_use_mplc_allocated_locally_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.settlements_local_LUT01_area, self.percentage_of_landscape_settlements_local_LUT01],
                ['LUT02', self.settlements_local_LUT02_area, self.percentage_of_landscape_settlements_local_LUT02],
                ['LUT03', self.settlements_local_LUT03_area, self.percentage_of_landscape_settlements_local_LUT03],
                ['LUT04', self.settlements_local_LUT04_area, self.percentage_of_landscape_settlements_local_LUT04],
                ['LUT05', self.settlements_local_LUT05_area, self.percentage_of_landscape_settlements_local_LUT05]
            ],
            'LPB_land_use_mplc_allocated_regionally_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.regional_excess_LUT01, self.percentage_of_landscape_regional_excess_LUT01],
                ['LUT02', self.regional_excess_LUT02, self.percentage_of_landscape_regional_excess_LUT02],
                ['LUT03', self.regional_excess_LUT03, self.percentage_of_landscape_regional_excess_LUT03],
                ['LUT04', self.regional_excess_LUT04, self.percentage_of_landscape_regional_excess_LUT04],
                ['LUT05', self.regional_excess_LUT05, self.percentage_of_landscape_regional_excess_LUT05]
            ],
            'LPB_land_use_mplc_unallocated_' + str(Parameters.get_model_scenario()): [
                ['LUT01', Parameters.get_pixel_size(), self.unallocated_pixels_LUT01],
                ['LUT02', Parameters.get_pixel_size(), self.unallocated_pixels_LUT02],
                ['LUT03', Parameters.get_pixel_size(), self.unallocated_pixels_LUT03],
                ['LUT04', Parameters.get_pixel_size(), self.unallocated_pixels_LUT04],
                ['LUT05', Parameters.get_pixel_size(), self.unallocated_pixels_LUT05],
            ],
            'LPB_possibly_hidden_deforestation_' + str(Parameters.get_model_scenario()): [
                [self.maximum_deforested_for_input_biomass_area, self.maximum_deforested_for_input_biomass_percentage_of_landscape]
            ],
            'LPB_forest_conversion_' + str(Parameters.get_model_scenario()): [
                ['per time step', self.converted_forest_area, self.converted_forest_area_percentage_of_landscape],
                ['accumulated', self.converted_forest_area_accumulated, None]
            ],
            'LPB_forest_conversion_by_type_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.LUT01_converted_forest_area],
                ['LUT02', self.LUT02_converted_forest_area],
                ['LUT03', self.LUT03_converted_forest_area],
                ['LUT04', self.LUT04_converted_forest_area],
                ['LUT05', self.LUT05_converted_forest_area],
            ],
            'LPB_forest_deforestation_' + str(Parameters.get_model_scenario()): [
                ['per time step', self.mplc_deforestation_maptotal],
                ['accumulated', self.mplc_deforestation_accumulated]
            ],
            'LPB_forest_corrective_allocation_' + str(Parameters.get_model_scenario()): [
                ['prior corrective allocation', self.forest_prior_corrective_allocation],
                ['post corrective allocation', self.forest_post_corrective_allocation],
            ],
            'LPB_landscape_modelling_probabilities_' + str(Parameters.get_model_scenario()): [
                ['0 %', self.pixels_in_probability_class_1, self.percentage_of_landscape_probability_class_1],
                ['>0 - 20 %', self.pixels_in_probability_class_2, self.percentage_of_landscape_probability_class_2],
                ['>20 - 40 %', self.pixels_in_probability_class_3, self.percentage_of_landscape_probability_class_3],
                ['>40 - 60 %', self.pixels_in_probability_class_4, self.percentage_of_landscape_probability_class_4],
                ['>60 - 80 %', self.pixels_in_probability_class_5, self.percentage_of_landscape_probability_class_5],
                ['>80 - <100 %', self.pixels_in_probability_class_6, self.percentage_of_landscape_probability_class_6],
                ['100 %', self.pixels_in_probability_class_7, self.percentage_of_landscape_probability_class_7]
            ],
            'LPB_land_use_in_restricted_areas_' + str(Parameters.get_model_scenario()): [
                ['restricted_area', self.restricted_areas_area, self.restricted_areas_area_percentage_of_landscape, 'percentage of landscape'],
                ['total_landuse_restricted_areas', self.total_of_land_use_in_restricted_areas_area,
                 self.total_of_land_use_in_restricted_areas_area_percentage_of_restricted_area,'percentage of restricted area'],
                ['total_new_landuse_restricted_areas', self.total_of_new_land_use_in_restricted_areas_area,
                 self.total_of_new_land_use_in_restricted_areas_area_percentage_of_restricted_area,
                 'percentage of restricted area'],
                ['total_new_landuse_restricted_areas_on_former_forest', self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area,
                 self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area_percentage_of_restricted_area,
                 'percentage of restricted area']
            ],
            'LPB_forest_net_gross_disturbed_undisturbed_' + str(Parameters.get_model_scenario()): [
                ['gross_forest_all_forest_types', self.gross_forest_mplc_area, self.gross_forest_mplc_percentage_of_landscape],
                ['net_forest_total_disturbed_undisturbed', self.net_forest_mplc_area, self.net_forest_mplc_percentage_of_landscape],
                ['gross_disturbed_forest', self.gross_mplc_disturbed_forest_area, self.gross_mplc_disturbed_forest_percentage_of_landscape],
                ['gross_undisturbed_forest', self.gross_mplc_undisturbed_forest_area, self.gross_mplc_undisturbed_forest_percentage_of_landscape],
                ['net_disturbed_forest', self.net_mplc_disturbed_forest_area, self.net_mplc_disturbed_forest_percentage_of_landscape],
                ['net_undisturbed_forest', self.net_mplc_undisturbed_forest_area, self.net_mplc_undisturbed_forest_percentage_of_landscape],
                ['gross_minus_net_disturbed_forest', self.gross_minus_net_forest_disturbed_mplc_area, self.gross_minus_net_forest_disturbed_mplc_percentage_of_landscape],
                ['gross_minus_net_undisturbed_forest', self.gross_minus_net_forest_undisturbed_mplc_area, self.gross_minus_net_forest_undisturbed_mplc_percentage_of_landscape]
            ],
            'LPB_forest_impacted_by_anthropogenic_features_' + str(Parameters.get_model_scenario()): [
                ['impacted_gross_forest_disturbed_undisturbed', self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area, self.true_gross_forest_impacted_by_anthropogenic_features_mplc_percentage_of_landscape],
                ['impacted_net_forest_disturbed_undisturbed', self.true_net_forest_impacted_by_anthropogenic_features_mplc_area, self.true_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest],
                ['impacted_gross_minus_net_forest_disturbed_undisturbed', self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area, self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest]
            ],
            'LPB_forest_remaining_without_anthropogenic_impact_' + str(Parameters.get_model_scenario()): [
                ['gross_undisturbed_forest', self.remaining_gross_undisturbed_forest_without_impact_area, self.remaining_gross_undisturbed_forest_without_impact_percentage_of_landscape],
                ['gross_disturbed_forest', self.remaining_gross_disturbed_forest_without_impact_area, self.remaining_gross_disturbed_forest_without_impact_percentage_of_landscape],
                ['net_undisturbed_forest', self.remaining_net_undisturbed_forest_without_impact_area, self.remaining_net_undisturbed_forest_without_impact_percentage_of_landscape],
                ['net_disturbed_forest', self.remaining_net_disturbed_forest_without_impact_area, self.remaining_net_disturbed_forest_without_impact_percentage_of_landscape],
                ['gross_minus_net_undisturbed_forest', self.remaining_gross_minus_net_undisturbed_forest_without_impact_area, self.remaining_gross_minus_net_undisturbed_forest_without_impact_percentage_of_landscape],
                ['gross_minus_net_disturbed_forest', self.remaining_gross_minus_net_disturbed_forest_without_impact_area, self.remaining_gross_minus_net_disturbed_forest_without_impact_percentage_of_landscape]
            ],
            'LPB_forest_degradation_regeneration_' + str(Parameters.get_model_scenario()): [
                ['degradation_low_net_forest', self.low_degradation_net_forest_mplc_area, self.low_degradation_net_forest_mplc_percentage_of_landscape],
                ['degradation_low_gross_forest', self.low_degradation_gross_forest_mplc_area, self.low_degradation_gross_forest_mplc_percentage_of_landscape],
                ['degradation_low_gross_minus_net_forest', self.low_degradation_gross_minus_net_forest_mplc_area, self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['degradation_moderate_net_forest', self.moderate_degradation_net_forest_mplc_area, self.moderate_degradation_net_forest_mplc_percentage_of_landscape],
                ['degradation_moderate_gross_forest', self.moderate_degradation_gross_forest_mplc_area, self.moderate_degradation_gross_forest_mplc_percentage_of_landscape],
                ['degradation_moderate_gross_minus_net_forest', self.moderate_degradation_gross_minus_net_forest_mplc_area, self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['degradation_severe_net_forest', self.severe_degradation_net_forest_mplc_area, self.severe_degradation_net_forest_mplc_percentage_of_landscape],
                ['degradation_severe_gross_forest', self.severe_degradation_gross_forest_mplc_area, self.severe_degradation_gross_forest_mplc_percentage_of_landscape],
                ['degradation_severe_gross_minus_net_forest', self.severe_degradation_gross_minus_net_forest_mplc_area, self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['degradation_absolute_net_forest', self.absolute_degradation_net_forest_mplc_area, self.absolute_degradation_net_forest_mplc_percentage_of_landscape],
                ['degradation_absolute_net_disturbed_forest', self.absolute_degradation_net_forest_disturbed_mplc_area, self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape],
                ['degradation_absolute_net_undisturbed_forest', self.absolute_degradation_net_forest_undisturbed_mplc_area, self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape],

                ['regeneration_low_net_forest', self.low_regeneration_net_forest_mplc_area, self.low_regeneration_net_forest_mplc_percentage_of_landscape],
                ['regeneration_low_gross_forest', self.low_regeneration_gross_forest_mplc_area, self.low_regeneration_gross_forest_mplc_percentage_of_landscape],
                ['regeneration_low_gross_minus_net_forest', self.low_regeneration_gross_minus_net_forest_mplc_area, self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['regeneration_medium_net_forest', self.medium_regeneration_net_forest_mplc_area, self.medium_regeneration_net_forest_mplc_percentage_of_landscape],
                ['regeneration_medium_gross_forest', self.medium_regeneration_gross_forest_mplc_area, self.medium_regeneration_gross_forest_mplc_percentage_of_landscape],
                ['regeneration_medium_gross_minus_net_forest', self.medium_regeneration_gross_minus_net_forest_mplc_area, self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['regeneration_high_net_forest', self.high_regeneration_net_forest_mplc_area, self.high_regeneration_net_forest_mplc_percentage_of_landscape],
                ['regeneration_high_gross_forest', self.high_regeneration_gross_forest_mplc_area, self.high_regeneration_gross_forest_mplc_percentage_of_landscape],
                ['regeneration_high_gross_minus_net_forest', self.high_regeneration_gross_minus_net_forest_mplc_area, self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape],

                ['regeneration_full_net_forest', self.full_regeneration_net_forest_mplc_area, self.full_regeneration_net_forest_mplc_percentage_of_landscape],
                ['regeneration_full_gross_forest', self.full_regeneration_gross_forest_mplc_area, self.full_regeneration_gross_forest_mplc_percentage_of_landscape],
                ['regeneration_full_disturbed_net_forest', self.full_regeneration_disturbed_forest_net_forest_mplc_area, self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape],
                ['regeneration_full_undisturbed_net_forest', self.full_regeneration_undisturbed_forest_net_forest_mplc_area, self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape],
                ['regeneration_full_disturbed_gross_minus_net_forest', self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area, self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape],
                ['regeneration_full_undisturbed_gross_minus_net_forest', self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area, self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape]
            ],
            'LPB_forest_types_AGB_Carbon_' + str(Parameters.get_model_scenario()): [
                ['potential_maximum_undisturbed_AGB', self.potential_maximum_undisturbed_forest_AGB_maptotal, self.potential_maximum_undisturbed_forest_AGB_Carbon],
                ['initial_AGB_gross_forest_simulation_start', self.initial_AGB_maptotal, self.initial_AGB_Carbon],
                ['final_total_AGB_gross_forest', self.final_AGB_gross_forest_maptotal, self.final_AGB_gross_forest_Carbon],
                ['final_total_AGB_net_forest', self.final_AGB_net_forest_maptotal, self.final_AGB_net_forest_Carbon],
                ['final_total_AGB_gross_minus_net_forest', self.final_AGB_gross_minus_net_forest_maptotal, self.final_AGB_gross_minus_net_forest_Carbon],
                ['final_total_AGB_agroforestry', self.final_agroforestry_AGB_maptotal, self.final_agroforestry_AGB_Carbon],
                ['final_total_AGB_plantation', self.final_plantation_AGB_maptotal, self.final_plantation_AGB_Carbon],
                ['final_total_AGB_gross_disturbed_forest', self.final_disturbed_forest_AGB_gross_forest_maptotal, self.final_disturbed_forest_AGB_gross_forest_Carbon],
                ['final_total_AGB_net_disturbed_forest', self.final_disturbed_forest_AGB_net_forest_maptotal, self.final_disturbed_forest_AGB_net_forest_Carbon],
                ['final_total_AGB_gross_minus_net_disturbed_forest', self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal, self.final_disturbed_forest_AGB_gross_minus_net_forest_Carbon],
                ['final_total_AGB_gross_undisturbed_forest', self.final_undisturbed_forest_AGB_gross_forest_maptotal, self.final_undisturbed_forest_AGB_gross_forest_Carbon ],
                ['final_total_AGB_net_undisturbed_forest', self.final_undisturbed_forest_AGB_net_forest_maptotal, self.final_undisturbed_forest_AGB_net_forest_Carbon],
                ['final_total_AGB_gross_minus_net_undisturbed_forest', self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal, self.final_undisturbed_forest_AGB_gross_minus_net_forest_Carbon],
            ],
            'LPB_forest_100years_without_anthropogenic_impact_' + str(Parameters.get_model_scenario()): [
                ['former_disturbed_forest_gross',
                 self.former_disturbed_gross_forest_100years_without_impact_area,
                 self.former_disturbed_gross_forest_100years_without_impact_percentage_of_landscape],
                ['former_disturbed_forest_net',
                 self.former_disturbed_net_forest_100years_without_impact_area,
                 self.former_disturbed_net_forest_100years_without_impact_percentage_of_landscape],
                ['former_disturbed_forest_gross_minus_net',
                 self.former_disturbed_gross_minus_net_forest_100years_without_impact_area,
                 self.former_disturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape],
                ['initial_undisturbed_forest_gross',
                 self.initial_undisturbed_gross_forest_100years_without_impact_area,
                 self.initial_undisturbed_gross_forest_100years_without_impact_percentage_of_landscape],
                ['initial_undisturbed_forest_net',
                 self.initial_undisturbed_net_forest_100years_without_impact_area,
                 self.initial_undisturbed_net_forest_100years_without_impact_percentage_of_landscape],
                ['initial_undisturbed_forest_gross_minus_net',
                 self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area,
                 self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape]
            ],
            'LPB_forest_habitat_' + str(Parameters.get_model_scenario()): [
                ['disturbed_habitat', self.mplc_disturbed_forest_fringe_area, self.mplc_disturbed_forest_fringe_percentage_of_landscape],
                ['undisturbed_habitat', self.mplc_undisturbed_forest_habitat_area, self.mplc_undisturbed_forest_habitat_percentage_of_landscape]
            ],
            'LPB_yields_' + str(Parameters.get_model_scenario()): [
                [crop_dict['name'],
                 crop_dict['source_LUT'],
                 crop_dict['share_of_LUT_acreage'],
                 crop_dict['yield_minimum'],
                 crop_dict['yield_mean'],
                 crop_dict['yield_maximum']] for crop_dict in self.top_crops_data_lists_dictionary.values()
            ]
        }

        if Parameters.get_umbrella_species_ecosystem_fragmentation_analysis_mplc_RAP_analysis_choice() == True:
            fragmentation_output_dict = {
                'LPB_fragmentation_' + str(Parameters.get_model_scenario()): [
                    ['maximum_patch_number', self.maximum_number_of_patches],
                    ['total_area_of_patches', self.total_area_of_patches]
                ]
            }
            output_files_data.update(fragmentation_output_dict)

        if habitat_connectivity_simulation_dictionary['simulate_connectivity'] == True:
            Omniscape_normalized_output_dict = {
                'LPB_Omniscape_transformed_normalized_pixels_' + str(Parameters.get_model_scenario()): [
                    ['blocked_flow', self.Omniscape_normalized_blocked_flow],
                    ['impeded_flow', self.Omniscape_normalized_impeded_flow],
                    ['reduced_flow', self.Omniscape_normalized_reduced_flow],
                    ['diffuse_flow', self.Omniscape_normalized_diffuse_flow],
                    ['intensified_flow', self.Omniscape_normalized_intensified_flow],
                    ['channelized_flow', self.Omniscape_normalized_channelized_flow]
                ]
            }
            output_files_data.update(Omniscape_normalized_output_dict)

        for output_file, column_headers in self.tidy_output_files_definitions.items():

            with open(os.path.join(Filepaths.folder_LPB_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file)

                for data_of_row in output_files_data[output_file]:
                    # add time step
                    data_of_row.insert(0, self.time_step)

                    assert len(column_headers) == len(
                        data_of_row), f'headers: {column_headers}, row data: {data_of_row}'

                    csv_file_writer.writerow(data_of_row)

    def postdynamic(self):
        print('\n>>> running postdynamic ...')

        print('\nno further statistics to be calculated')

        if Parameters.get_GIFs_production_choice() == True:

            # make all the movies
            print('\nmaking movies 05 to 26 for mplc - each for', Parameters.get_number_of_time_steps(), 'time steps ...')

            movies_start_time = datetime.now()

            # 05
            print('\nLPB_movie_05 making movie of land use for the most probable landscape configuration ...')
            command = "python LPB_movie_05_LULCC_mplc.py"
            os.system(command)
            print('making movie of land use for the most probable landscape configuration done')

            # 06
            print('\nLPB_movie_06 making movie of land use for the most probable landscape configuration VIRIDIS ACCESSIBLE...')
            command = "python LPB_movie_06_LULCC_mplc_VA.py"
            os.system(command)
            print('making movie of land use for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 07
            print('\nLPB_movie_07 making movie of land use for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE...')
            command = "python LPB_movie_07_LULCC_mplc_probabilities_VA.py"
            os.system(command)
            print('making movie of land use for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 08 dictionary_of_anthropogenic_features
            print('\nLPB_movie_08 making movie of anthropogenic features deterministic VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_08_ANTHROPOGENIC_FEATURES_DETERMINISTIC_VA.py %r" % json.dumps(
                dictionary_of_anthropogenic_features)
            os.system(command)
            print('making movie of anthropogenic features deterministic VIRIDIS ACCESSIBLE done')

            # 09 dictionary_of_accumulated_land_use_in_restricted_areas
            print(
                '\nLPB_movie_09 making movie of most probable landscape configuration active land use types in restricted areas VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_09_CONFLICT_ACTIVE_LAND_USE_IN_RESTRICTED_AREAS_mplc_VA.py %r" % json.dumps(
                dictionary_of_accumulated_land_use_in_restricted_areas)
            os.system(command)
            print(
                'making movie of most probable landscape configuration active land use types in restricted areas VIRIDIS ACCESSIBLE done')

            # 10
            print('\nLPB_movie_10 making movie of forest land use conflict for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE...')
            command = "python LPB_movie_10_CONFLICT-FOREST_probabilities_VA.py "+",".join(map(str,list_of_new_pixels_of_forest_land_use_conflict))
            os.system(command)
            print('making movie of forest land use conflict for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 11
            print('\nLPB_movie_11 making movie of land use conflict for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE...')
            command = "python LPB_movie_11_CONFLICT-LAND-USE_probabilities_VA.py "+",".join(map(str,list_of_new_pixels_of_land_use_conflict))
            os.system(command)
            print('making movie of land use conflict for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 12
            print(
                '\nLPB_movie_12 making movie of forest degradation and regeneration for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_12_DEGRADATION+REGENERATION_probabilities_VA.py"
            os.system(command)
            print(
                'making movie of forest degradation and regeneration for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 13
            print('\nLPB_movie_13 making movie of forest degradation and regeneration for the most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_13_DEGRADATION+REGENERATION_mplc_VA.py"
            os.system(command)
            print('making movie of forest degradation and regeneration for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 14 list of new converted forest area
            print('\nLPB_movie_14 making movie of mplc forest conversion VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_14_FOREST_conversion_mplc_VA.py " + ",".join(
                map(str, list_of_new_converted_forest_area))
            os.system(command)
            print('making movie of mplc forest conversion VIRIDIS ACCESSIBLE done')

            # 15 list of new deforested area
            print('\nLPB_movie_15 making movie of deforestation classified probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_15_FOREST_deforested_LUT17_probabilities_VA.py " + ",".join(
                map(str, list_of_new_deforested_area))
            os.system(command)
            print('making movie of deforestation classified probabilities VIRIDIS ACCESSIBLE done')

            # 16
            print(
                '\nLPB_movie_16 making movie of forest a 100 years with no impact distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_16_FOREST-100YEARS-NO-IMPACT_mplc_VA.py"
            os.system(command)
            print(
                'making movie of forest a 100 years with no impact distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 17
            print(
                '\nLPB_movie_17 making movie of disturbed and undisturbed forest distribution for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_17_FOREST-DISTURBED+UNDISTURBED_probabilities_VA.py"
            os.system(command)
            print(
                'making movie of disturbed and undisturbed forest distribution for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 18
            print(
                '\nLPB_movie_18 making movie of disturbed and undisturbed forest distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_18_FOREST-DISTURBED+UNDISTURBED_mplc_VA.py"
            os.system(command)
            print(
                'making movie of disturbed and undisturbed forest distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 19
            print(
                '\nLPB_movie_19 making movie of net and gross forest distribution for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_19_FOREST-NET+GROSS_probabilities_VA.py"
            os.system(command)
            print(
                'making movie of net and gross forest distribution for the most probable landscape configuration probabilities VIRIDIS ACCESSIBLE done')

            # 20
            print('\nLPB_movie_20 making movie of net and gross forest distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_20_FOREST-NET+GROSS_mplc_VA.py"
            os.system(command)
            print('making movie of net and gross forest distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 21
            print('\nLPB_movie_21 making movie of disturbed forest classified probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_21_FOREST-ONLY-DISTURBED_probabilities_VA.py"
            os.system(command)
            print('making movie of disturbed forest classified probabilities VIRIDIS ACCESSIBLE done')

            # 22
            print('\nLPB_movie_22 making movie of undisturbed forest classified probabilities VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_22_FOREST-ONLY-UNDISTURBED_probabilities_VA.py"
            os.system(command)
            print('making movie of undisturbed forest classified probabilities VIRIDIS ACCESSIBLE done')

            # 23
            print('\nLPB_movie_23 making movie of remaining forest with no impact distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_23_FOREST-REMAINING-NO-IMPACT_mplc_VA.py"
            os.system(command)
            print('making movie of remaining forest with no impact distribution for the most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 24
            print('\nLPB_movie_24 making movie of mplc nominal undisturbed forest habitat VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_24_FOREST-UNDISTURBED-HABITAT_mplc_VA.py"
            os.system(command)
            print('making movie of mplc nominal undisturbed forest habitat VIRIDIS ACCESSIBLE done')

            # 25 dictionary_of_net_forest_information
            print('\nLPB_movie_25 making movie of net forest detailed most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_25_NET_FOREST_DETAILED_mplc_VA.py %r" % json.dumps(
                dictionary_of_net_forest_information)
            os.system(command)
            print('making movie of net forest detailed most probable landscape configuration VIRIDIS ACCESSIBLE done')

            # 26 dictionary_of_undisturbed_forest
            print('\nLPB_movie_26 making movie of undisturbed forest detailed most probable landscape configuration VIRIDIS ACCESSIBLE ...')
            command = "python LPB_movie_26_UNDISTURBED_FOREST_DETAILED_mplc_VA.py %r" % json.dumps(
                dictionary_of_undisturbed_forest)
            os.system(command)
            print('making movie of undisturbed forest detailed most probable landscape configuration VIRIDIS ACCESSIBLE done')

            movies_end_time = datetime.now()
            print('making movies done')
            print('time elapsed for movie production: {}'.format(movies_end_time - movies_start_time))





            if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
                # ONLY 1 SLIDE GIFs to extract the input map(s)
                print('\nONE SLIDE GIFs ...')

                #1
                print('\n1. making one GIF of the initial input map for visual comparison ...')
                command = "python LPB_initial_01_LULC_input_map_visualization.py"
                os.system(command)
                print('making one GIF of the initial input map for visual comparison done')

                #2
                print('\n2. making one GIF of the initial input map for visual comparison VIRIDIS ACCESSIBLE ...')
                command = "python LPB_initial_02_LULC_input_map_visualization_VA.py"
                os.system(command)
                print('making one GIF of the initial input map for visual comparison VIRIDIS ACCESSIBLE done')

            if Parameters.get_presimulation_correction_step_needed() is True:
                # 1
                print('\nmaking one GIF of the simulated initial input map for visual comparison ...')
                command = "python LPB_initial_03_LULC_simulated_input_map_visualization.py"
                os.system(command)
                print('making one GIF of the simulated initial input map for visual comparison done')

                # 2
                print('\nmaking one GIF of the simulated initial input map for visual comparison VIRIDIS ACCESSIBLE ...')
                command = "python LPB_initial_04_LULC_simulated_input_map_visualization_VA.py"
                os.system(command)
                print('making one GIF of the simulated initial input map for visual comparison VIRIDIS ACCESSIBLE done')

            if Parameters.get_worst_case_scenario_decision() is True:
                # 1
                print('\nmaking one GIF of the WORST CASE simulated initial input map for visual comparison ...')
                command = "python LPB_initial_05_LULC_WORST-CASE_simulated_input_map_visualization.py"
                os.system(command)
                print('making one GIF of the WORST CASE simulated initial input map for visual comparison done')

                # 2
                print('\nmaking one GIF of the WORST CASE simulated initial input map for visual comparison VIRIDIS ACCESSIBLE ...')
                command = "python LPB_initial_06_LULC_WORST-CASE_simulated_input_map_visualization_VA.py"
                os.system(command)
                print('making one GIF of the WORST CASE simulated initial input map for visual comparison VIRIDIS ACCESSIBLE done')

                print('\nONE SLIDE GIFs DONE')

        print('\nrunning postdynamic done')
        self.end_time = datetime.now()
        print('time elapsed for LPB-mplc execution: {}'.format(self.end_time - self.start_time))


###################################################################################################


number_of_time_steps = Parameters.get_number_of_time_steps()
my_model = MostProbableLandscapeConfiguration()
dynamic_model = DynamicFramework(my_model, number_of_time_steps)
dynamic_model.run()
my_model.postdynamic()

