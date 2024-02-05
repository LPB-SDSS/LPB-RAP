"""RAP.py LAFORET-PLUC-BE-RAP/SFM - Restoration Area Potentials (RAP)
Sonja Holler (SH)
2021/Q4 - 2022/Q3

This module calculates the Restoration Area Potentials on the basis of LPB-basic and LPB-mplc data.

ATTENTION: Although simulated time step for time step the results do not display dynamic development as a sequence
but individual possible entry points for landscape restoration for the conditions based on population development."""

# TODO in model stage 2:
#  RAP LUT 25 CSV
#  external time series peak demands CSV
#  Forest fragmentation
#  potential habitat corridors.

# SH: execute LPB-RAP

from datetime import datetime
import pcraster
from pcraster import *
from pcraster.framework import *
import numpy
import subprocess
import builtins
import Parameters
import Filepaths
import generate_PCRaster_conform_output_name
import sys, os
import json
import ast
import PyLandStats_adapter

# =================================================================== #
# For testing, debugging and submission: set random seed to make the results consistent (1)
# set random seed 0 = every time new results
seed = int(Parameters.get_random_seed())
setrandomseed(seed)

# =================================================================== #
# ATTENTION: The PCRaster maptotal has a rounding error, therefore we use the numpy calculation
# def numpy_maptotal(a_map):
#     numpy_maptotal = pcr2numpy(a_map, 0).sum()
#     return numpy_maptotal
#
# maptotal = numpy_maptotal

# =================================================================== #
# global variables for dynamic use in GIF files
# RAP used dicts
global dictionary_of_net_forest_information
dictionary_of_net_forest_information = {}
dictionary_of_net_forest_information['RAP_net_forest_area'] = {}
dictionary_of_net_forest_information['RAP_percentage_of_landscape'] = {}
dictionary_of_net_forest_information['RAP_net_disturbed_area'] = {}
dictionary_of_net_forest_information['RAP_net_disturbed_percentage_of_landscape'] = {}
dictionary_of_net_forest_information['RAP_net_undisturbed_area'] = {}
dictionary_of_net_forest_information['RAP_net_undisturbed_percentage_of_landscape'] = {}

global targeted_net_forest_dictionary
targeted_net_forest_dictionary = {}
targeted_net_forest_dictionary['initial_area'] = 0
targeted_net_forest_dictionary['targeted_percentage_increment'] = 0
targeted_net_forest_dictionary['targeted_area_increment'] = 0
targeted_net_forest_dictionary['targeted_total_area'] = 0

global RAP_population_and_LUTs_shares_dictionary
RAP_population_and_LUTs_shares_dictionary = {}
RAP_population_and_LUTs_shares_dictionary['population'] = []
RAP_population_and_LUTs_shares_dictionary['smallholder_share'] = []
RAP_population_and_LUTs_shares_dictionary['RAP_agroforestry'] = []
RAP_population_and_LUTs_shares_dictionary['RAP_plantation'] = []
RAP_population_and_LUTs_shares_dictionary['RAP_reforestation'] = []
RAP_population_and_LUTs_shares_dictionary['RAP_other_ecosystems'] = []
RAP_population_and_LUTs_shares_dictionary['RAP_restoration_of_degraded_forest'] = []

global RAP_potential_minimum_restoration_dictionary
RAP_potential_minimum_restoration_dictionary = {}
RAP_potential_minimum_restoration_dictionary['population_peak_year'] = 0
RAP_potential_minimum_restoration_dictionary['peak_demands_year'] = 0
RAP_potential_minimum_restoration_dictionary['LUT22'] = []
RAP_potential_minimum_restoration_dictionary['LUT23'] = []
RAP_potential_minimum_restoration_dictionary['LUT24'] = []
RAP_potential_minimum_restoration_dictionary['LUT25'] = []

# RAP used lists
global list_restricted_areas
list_restricted_areas = []
global list_of_LUTs_for_definition_of_potential_restricted_areas
list_of_LUTs_for_definition_of_potential_restricted_areas = []
# =================================================================== #

class PossibleLandscapeConfiguration(DynamicModel):
    def __init__(self):
        DynamicModel.__init__(self)
        setclone(f"{Filepaths.file_static_null_mask_input}.map")

    def initial(self):
        print('\n>>> running initial ...')

        #### prepare tidy data ######
        self.tidy_output_folder, self.tidy_output_files_definitions = self._prepare_tidy_output()
        print('\nprepared tidy data output')

        self.start_time = datetime.now()

        print('\nloading maps and CSV data ...')

        # import all needed maps
        self.null_mask_map = readmap(Filepaths.file_static_null_mask_input)
        self.static_restricted_areas_map = readmap(Filepaths.file_static_restricted_areas_input)
        self.dem_map = readmap(Filepaths.file_static_dem_input)
        self.cities_map = readmap(Filepaths.file_static_cities_input)
        self.cities_map = cover(boolean(self.cities_map), boolean(self.null_mask_map))
        self.streets_map = readmap(Filepaths.file_static_streets_input)
        self.streets_map = cover(boolean(self.streets_map), boolean(self.null_mask_map))
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            self.initial_net_forest_national_map = readmap(Filepaths.file_initial_net_forest_input)
            self.initial_net_forest_national_map = cover(boolean(self.initial_net_forest_national_map), boolean(self.null_mask_map))
        elif Parameters.get_model_scenario() == 'no_conservation':
            self.initial_net_forest_national_map = readmap(Filepaths.file_initial_net_forest_simulated_for_worst_case_scenario_input)
            self.initial_net_forest_national_map = cover(boolean(self.initial_net_forest_national_map),
                                                         boolean(self.null_mask_map))
        self.additional_ecosystems_to_be_restored_map = readmap(Filepaths.file_static_RAP_other_ecosystems_input)
        self.additional_ecosystems_to_be_restored_map = cover(boolean(self.additional_ecosystems_to_be_restored_map), boolean(self.null_mask_map))

        # =================================================================== #
        # determine once the original number of sample folders for a note on the output CSV

        sample_folders = list([file for file in os.listdir(
            Filepaths.folder_dynamic_environment_map_probabilistic) if not file.startswith('.')]) # imports as a List

        self.original_number_of_samples = len(sample_folders)

        # =================================================================== #
        # load the dictionary required for the allocation of targeted additional net forest area and the weights

        targeted_additional_net_forest_allocation_dictionary = Parameters.get_targeted_additional_net_forest_allocation_dictionary()

        self.variables_dictionary = targeted_additional_net_forest_allocation_dictionary

        self.weights_list = Parameters.get_weights_list_net_forest()

        # =================================================================== #

        # GET THE BASIC MPLC LANDSCAPE FILES FOR RAP
        self.dictionary_of_mplc_files = {}

        path_to_mplc_files = Filepaths.folder_LULCC_mplc

        mplc_files = list([file for file in os.listdir(
            path_to_mplc_files) if not file.startswith('.')])
        mplc_files = sorted(mplc_files)

        iteration = 1
        for a_file in mplc_files:
            a_key = iteration  # number the keys as time steps (1-N)
            a_value = readmap(os.path.join(path_to_mplc_files, a_file))  # get each single time step MC average
            self.dictionary_of_mplc_files[a_key] = a_value # append it to the dictionary
            iteration += 1

        # =================================================================== #

        # get the mplc net forest files
        self.dictionary_of_mplc_net_forest_files = {}

        path_to_mplc_net_forest_files = Filepaths.folder_FOREST_PROBABILITY_MAPS_mplc_net_boolean

        mplc_files = list([file for file in os.listdir(
            path_to_mplc_net_forest_files) if not file.startswith('.')])
        mplc_files = sorted(mplc_files)

        iteration = 1
        for a_file in mplc_files:
            a_key = iteration  # number the keys as time steps (1-N)
            a_value = readmap(os.path.join(path_to_mplc_net_forest_files, a_file))  # get each single time step MC average
            self.dictionary_of_mplc_net_forest_files[a_key] = a_value  # append it to the dictionary
            iteration += 1

        # =================================================================== #

        self.dictionary_of_mplc_AGB_files = {}

        path_to_mplc_AGB_MC_average = os.path.join(Filepaths.folder_AGB_most_probable_landscape_configuration)

        AGB_files = list([file for file in os.listdir(
            path_to_mplc_AGB_MC_average) if not file.startswith('.')])
        AGB_files = sorted(AGB_files)

        iteration = 1
        for a_file in AGB_files:
            a_key = iteration  # number the keys as time steps (1-N)
            a_value = readmap(
                    os.path.join(path_to_mplc_AGB_MC_average, a_file))  # get each single time step MC average
            self.dictionary_of_mplc_AGB_files[a_key] = a_value  # append it to the dictionary
            iteration += 1

        # =================================================================== #

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
        print('\nmplc maps and accompanying maps from LPB-basic and LPB-mplc imported')
        # =================================================================== #

        # import the CSV data from LPB-mplc_log-file for comparison
        # order is : key=year, Value = list of all other values (300)

        # to get the population peak year built a list of the population data, search with max() and return the index position to add to the initial simulation year +1 (zero indexing)

        list_of_population_values_per_year = []


        self.LPB_mplc_log_file_dictionary = {}

        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-mplc_log-file.csv'), 'r') as csv_file_to_read:
            log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
            next(log_file_reader, None)  # skip the title
            next(log_file_reader, None)  # skip the ULTRA category
            next(log_file_reader, None)  # skip the SUPRA category
            next(log_file_reader, None)  # skip the category
            next(log_file_reader, None)  # skip the sub-category
            for row in log_file_reader:  # reads each row as a list
                if row == []:  # break when you hit an empty row (not to read in the notes)
                    break
                a_key = row[1]  # the year shall be the key
                row.pop(0) # pop time step
                row.pop(0)  # pop year
                a_values_list = row  # all other values in the list except year and time step
                self.LPB_mplc_log_file_dictionary.update({a_key: a_values_list})
                population_data = row[0]
                list_of_population_values_per_year.append(int(population_data))
        print('\nCSV data from LPB-mplc_log-file imported')

        max_population = builtins.max(list_of_population_values_per_year)

        index_position_of_max_population = list_of_population_values_per_year.index(max_population, 0, len(list_of_population_values_per_year)) # search in the list for the value between 0 and last entry index position

        self.population_peak_year = Parameters.get_initial_simulation_year() + index_position_of_max_population

        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
            # set the variable depending on the population peak year (gets altered during simulation)
            self.RAP_potential_additional_restricted_areas = 'same as population peak year'
        else:
            # set the variable depending on the peak demands year (gets altered during simulation)
            self.RAP_potential_additional_restricted_areas = 'same as peak demands year'

        print('\npopulation peak year is:', self.population_peak_year)

        # get the simulated peak demands year
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-external-time-series_peak-demands-year.csv'), 'r') as csv_file_to_read:
                log_file_reader = csv.reader(csv_file_to_read, delimiter=',')
                for row in log_file_reader:  # reads each row as a list
                    if row == []:  # break when you hit an empty row
                        break
                    row.pop(0)  # pop info
                    peak_demands_year = row[0]
                    self.peak_demands_year = int(peak_demands_year)
            print('\nself.peak_demands_year imported:', self.peak_demands_year)

        # =================================================================== #
        # M O D E L  S T A G E 2

        # only when local wood consumption
        if Parameters.get_local_wood_consumption_simulation_choice() == True:
            # NOMINAL CLASSES
            # degradation low = 1
            # degradation moderate = 2
            # degradation severe = 3
            # degradation absolute = 4

            # regeneration low = 5
            # regeneration medium = 6
            # regeneration high = 7
            # regeneration full = 8

            self.dictionary_of_mplc_degradation_regeneration_files = {}

            path_to_mplc_fdr = os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_degradation_and_regeneration)

            fdr_files = list([file for file in os.listdir(
                path_to_mplc_fdr) if not file.startswith('.')])
            fdr_files = sorted(fdr_files)

            iteration = 1
            for a_file in fdr_files:
                a_key = iteration  # number the keys as time steps (1-N)
                a_value = readmap(
                    os.path.join(path_to_mplc_fdr, a_file))  # get each single time step
                self.dictionary_of_mplc_degradation_regeneration_files[a_key] = a_value  # append it to the dictionary
                iteration += 1

        # =================================================================== #

        # model stage 2:
        # user-defined degradation stages dictionary
        self.user_defined_RAPLUT25_input_degradation_stages_dictionary = Parameters.get_user_defined_RAPLUT25_input_degradation_stages()

        # =================================================================== #

        # model stage 2:
        # get PHCs simulation choice dictionary
        self.PHCs_simulation_choice_dictionary = Parameters.get_potential_habitat_corridors_simulation_choice()

        # =================================================================== #

        # PRE-PRODUCED MAPS AND VALUES
        print('\npre-produced maps and values initialized')

        # prepare the restricted areas map for use
        self.static_restricted_areas_map = cover(boolean(self.static_restricted_areas_map), boolean(self.null_mask_map))

        # determine the 100 % area once as a reference
        print('\ndetermine the hundred percent area as a reference for the simulation output ...')
        one_mask_map = scalar(self.null_mask_map) + 1
        self.hundred_percent_area = int(maptotal(one_mask_map))
        print('full landscape area, i.e. 100 % for reference, is', self.hundred_percent_area,
              Parameters.get_pixel_size())

        print('\npre-produced maps and values done')

        # =================================================================== #

        # open the new CSV LPB-RAP_log-file
        command = "python Create_LPB_RAP_log_file.py"
        subprocess.run(command.split(), check=True)
        # os.system(command)
        print('\nfiling LPB-RAP_log-file.csv initiated ...')

        # =================================================================== #

        print('\nrunning initial done')

    def _prepare_tidy_output(self):
        output_folder = Filepaths.folder_RAP_tidy_data

        # define output files and column headers
        output_files_definitions = {
            'RAP_land_use_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels', 'percentage'],
            'RAP_total_' + str(Parameters.get_model_scenario()): ['pixels', 'percentage'],
            'RAP_minimum_mitigation_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'RAP_potential_AGB_Carbon_' + str(Parameters.get_model_scenario()): ['LUT_code', 'LUT_mean', 'potential_AGB', 'potential_Carbon'],
            'RAP_potential_total_AGB_Carbon_' + str(Parameters.get_model_scenario()): ['potential_AGB', 'potential_Carbon'],
            'RAP_targeted_net_forest_' + str(Parameters.get_model_scenario()): ['category', 'pixels', 'percentage']
        }

        if Parameters.get_fragmentation_mplc_RAP_analysis_choice() == True:
            fragmentation_dict = {
                'RAP_fragmentation_' + str(Parameters.get_model_scenario()): ['Aspect','value']
            }
            output_files_definitions.update(fragmentation_dict)

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
            'LUT21': Parameters.LUT21,
            'LUT22': Parameters.LUT22,
            'LUT23': Parameters.LUT23,
            'LUT24': Parameters.LUT24,
            'LUT25': Parameters.LUT25
        }

        with open((os.path.join(output_folder, 'RAP_LUTs_lookup_table.csv')), 'w', newline='') as csv_file:
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
        self.make_LPB_mplc_log_file_data_for_the_time_step_accessible() # get the baseline data
        if Parameters.get_local_wood_consumption_simulation_choice() == True and not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            self.make_forest_degradation_maps_for_the_time_step_accessible()
        self.calculate_initial_national_net_forest_plus_percentage_goal() # get the goal and net forest landscape configuration to achieve once
        self.get_climate_period_data()
        self.calculate_RAP_other_ecosystems_mask()
        if (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            self.calculate_population_peak_land_use_mask()
        else:
            self.calculate_peak_demands_year_land_use_mask()
        self.calculate_RAP_possible_landscape_configuration() # calculate based on mplc files, potential natural vegetation and net forest goal
        self.create_tiles_subsets() # store RAP tiles
        self.calculate_RAP_potential_minimum_restoration()
        if (Parameters.demand_configuration['overall_method'] == 'footprint' and
                Parameters.demand_configuration['internal_or_external'] == 'internal'and self.year == self.population_peak_year):
            self.calculate_RAP_potential_additional_restricted_areas()
        elif not (Parameters.demand_configuration['overall_method'] == 'footprint' and
                Parameters.demand_configuration['internal_or_external'] == 'internal') and self.year == self.peak_demands_year:
            self.calculate_RAP_potential_additional_restricted_areas()
        self.calculate_RAP_net_forest_possible_landscape_configuration() # store the comparison files for net forest
        self.derive_RAP_AGB_and_Carbon() # calculate the additional possible AGB for climax stadium
        self.update_RAP_potential_additional_restricted_areas()
        if Parameters.get_fragmentation_mplc_RAP_analysis_choice() == True:
            self.calculate_fragmentation()
        if self.PHCs_simulation_choice_dictionary['simulate_PHCs'] == True and (self.PHCs_simulation_choice_dictionary['simulation_in'] == 'RAP'
                                                                                or self.PHCs_simulation_choice_dictionary['simulation_in'] == 'mplc+RAP'):
            self.simulate_potential_habitat_corridors()
        if Parameters.get_worst_case_scenario_decision() == True and (Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation'):
            self.calculate_worst_case_scenario_percent_increment_net_forest()
        self.export_data_to_LPB_RAP_log_file()
        self.export_data_to_tidy_data_folder()

        print('\nrunning dynamic for time step', self.time_step, 'done')

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

    def make_LPB_mplc_log_file_data_for_the_time_step_accessible(self):
        # make the LPB-basic CSV data accessible for the time step
        # order is : key=year, values = list of: population[0], settlements[1], share smallholder population[2], ha demand LUT01[3], ha demand LUT02[4], ha demand LUT03[5], ha demand LUT04[6], ha demand LUT05[7|, demand AGB[8]
        a_key = str(self.year)
        if a_key in self.LPB_mplc_log_file_dictionary:
            self.population = self.LPB_mplc_log_file_dictionary[a_key][0]
            # anthropogenic features
            self.cities = self.LPB_mplc_log_file_dictionary[a_key][1]
            self.settlements = self.LPB_mplc_log_file_dictionary[a_key][2]
            self.streets = self.LPB_mplc_log_file_dictionary[a_key][3]
            self.built_up_additionally = self.LPB_mplc_log_file_dictionary[a_key][4]
            # anthropogenic impact buffer 1 total area
            self.anthropogenic_impact_buffer_area = self.LPB_mplc_log_file_dictionary[a_key][5]
            self.percentage_of_landscape_anthropogenic_impact_buffer = self.LPB_mplc_log_file_dictionary[a_key][6]
            # LUT01
            self.demand_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][7]
            self.allocated_pixels_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][8]
            self.percentage_of_landscape_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][9]
            self.allocated_pixels_in_difficult_terrain_LUT01_area = self.LPB_mplc_log_file_dictionary[a_key][10]
            self.percentage_of_landscape_difficult_terrain_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][11]
            self.LUT01_mplc_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][12]
            self.percentage_of_landscape_LUT01_in_restricted_areas = self.LPB_mplc_log_file_dictionary[a_key][13]
            self.LUT01_mplc_new_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][14]
            self.LUT01_mplc_new_on_former_forest_pixel_area = self.LPB_mplc_log_file_dictionary[a_key][15]
            self.settlements_local_LUT01_area = self.LPB_mplc_log_file_dictionary[a_key][16]
            self.percentage_of_landscape_settlements_local_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][17]
            self.regional_excess_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][18]
            self.percentage_of_landscape_regional_excess_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][19]
            self.unallocated_pixels_LUT01 = self.LPB_mplc_log_file_dictionary[a_key][20]
            # LUT02
            self.demand_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][21]
            self.allocated_pixels_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][22]
            self.percentage_of_landscape_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][23]
            self.allocated_pixels_in_difficult_terrain_LUT02_area = self.LPB_mplc_log_file_dictionary[a_key][24]
            self.percentage_of_landscape_difficult_terrain_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][25]
            self.LUT02_mplc_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][26]
            self.percentage_of_landscape_LUT02_in_restricted_areas = self.LPB_mplc_log_file_dictionary[a_key][27]
            self.LUT02_mplc_new_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][28]
            self.LUT02_mplc_new_on_former_forest_pixel_area = self.LPB_mplc_log_file_dictionary[a_key][29]
            self.settlements_local_LUT02_area = self.LPB_mplc_log_file_dictionary[a_key][30]
            self.percentage_of_landscape_settlements_local_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][31]
            self.regional_excess_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][32]
            self.percentage_of_landscape_regional_excess_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][33]
            self.unallocated_pixels_LUT02 = self.LPB_mplc_log_file_dictionary[a_key][34]
            # LUT03
            self.demand_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][35]
            self.allocated_pixels_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][36]
            self.percentage_of_landscape_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][37]
            self.allocated_pixels_in_difficult_terrain_LUT03_area = self.LPB_mplc_log_file_dictionary[a_key][38]
            self.percentage_of_landscape_difficult_terrain_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][39]
            self.LUT03_mplc_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][40]
            self.percentage_of_landscape_LUT03_in_restricted_areas = self.LPB_mplc_log_file_dictionary[a_key][41]
            self.LUT03_mplc_new_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][42]
            self.LUT03_mplc_new_on_former_forest_pixel_area = self.LPB_mplc_log_file_dictionary[a_key][43]
            self.settlements_local_LUT03_area = self.LPB_mplc_log_file_dictionary[a_key][44]
            self.percentage_of_landscape_settlements_local_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][45]
            self.regional_excess_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][46]
            self.percentage_of_landscape_regional_excess_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][47]
            self.unallocated_pixels_LUT03 = self.LPB_mplc_log_file_dictionary[a_key][48]
            # LUT04
            self.demand_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][49]
            self.allocated_pixels_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][50]
            self.percentage_of_landscape_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][51]
            self.allocated_pixels_in_difficult_terrain_LUT04_area = self.LPB_mplc_log_file_dictionary[a_key][52]
            self.percentage_of_landscape_difficult_terrain_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][53]
            self.LUT04_mplc_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][54]
            self.percentage_of_landscape_LUT04_in_restricted_areas = self.LPB_mplc_log_file_dictionary[a_key][55]
            self.LUT04_mplc_new_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][56]
            self.LUT04_mplc_new_on_former_forest_pixel_area = self.LPB_mplc_log_file_dictionary[a_key][57]
            self.settlements_local_LUT04_area = self.LPB_mplc_log_file_dictionary[a_key][58]
            self.percentage_of_landscape_settlements_local_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][59]
            self.regional_excess_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][60]
            self.percentage_of_landscape_regional_excess_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][61]
            self.unallocated_pixels_LUT04 = self.LPB_mplc_log_file_dictionary[a_key][62]
            # LUT05
            self.demand_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][63]
            self.allocated_pixels_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][64]
            self.percentage_of_landscape_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][65]
            self.allocated_pixels_in_difficult_terrain_LUT05_area = self.LPB_mplc_log_file_dictionary[a_key][66]
            self.percentage_of_landscape_difficult_terrain_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][67]
            self.LUT05_mplc_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][68]
            self.percentage_of_landscape_LUT05_in_restricted_areas = self.LPB_mplc_log_file_dictionary[a_key][69]
            self.LUT05_mplc_new_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][70]
            self.LUT05_mplc_new_on_former_forest_pixel_area = self.LPB_mplc_log_file_dictionary[a_key][71]
            self.settlements_local_LUT05_area = self.LPB_mplc_log_file_dictionary[a_key][72]
            self.percentage_of_landscape_settlements_local_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][73]
            self.regional_excess_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][74]
            self.percentage_of_landscape_regional_excess_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][75]
            self.unallocated_pixels_LUT05 = self.LPB_mplc_log_file_dictionary[a_key][76]
            # LUT06
            self.allocated_pixels_LUT06 = self.LPB_mplc_log_file_dictionary[a_key][77]
            self.percentage_of_landscape_LUT06 = self.LPB_mplc_log_file_dictionary[a_key][78]
            # LUT07
            self.allocated_pixels_LUT07 = self.LPB_mplc_log_file_dictionary[a_key][79]
            self.percentage_of_landscape_LUT07 = self.LPB_mplc_log_file_dictionary[a_key][80]
            # LUT08
            self.allocated_pixels_LUT08 = self.LPB_mplc_log_file_dictionary[a_key][81]
            self.percentage_of_landscape_LUT08 = self.LPB_mplc_log_file_dictionary[a_key][82]
            # LUT09
            self.allocated_pixels_LUT09 = self.LPB_mplc_log_file_dictionary[a_key][83]
            self.percentage_of_landscape_LUT09 = self.LPB_mplc_log_file_dictionary[a_key][84]
            # LUT10
            self.allocated_pixels_LUT10 = self.LPB_mplc_log_file_dictionary[a_key][85]
            self.percentage_of_landscape_LUT10 = self.LPB_mplc_log_file_dictionary[a_key][86]
            # LUT11
            self.allocated_pixels_LUT11 = self.LPB_mplc_log_file_dictionary[a_key][87]
            self.percentage_of_landscape_LUT11 = self.LPB_mplc_log_file_dictionary[a_key][88]
            # LUT12
            self.allocated_pixels_LUT12 = self.LPB_mplc_log_file_dictionary[a_key][89]
            self.percentage_of_landscape_LUT12 = self.LPB_mplc_log_file_dictionary[a_key][90]
            # LUT13
            self.allocated_pixels_LUT13 = self.LPB_mplc_log_file_dictionary[a_key][91]
            self.percentage_of_landscape_LUT13 = self.LPB_mplc_log_file_dictionary[a_key][92]
            # LUT14
            self.allocated_pixels_LUT14 = self.LPB_mplc_log_file_dictionary[a_key][93]
            self.percentage_of_landscape_LUT14 = self.LPB_mplc_log_file_dictionary[a_key][94]
            # LUT15
            self.allocated_pixels_LUT15 = self.LPB_mplc_log_file_dictionary[a_key][95]
            self.percentage_of_landscape_LUT15 = self.LPB_mplc_log_file_dictionary[a_key][96]
            # LUT16
            self.allocated_pixels_LUT16 = self.LPB_mplc_log_file_dictionary[a_key][97]
            self.percentage_of_landscape_LUT16 = self.LPB_mplc_log_file_dictionary[a_key][98]
            # LUT17
            self.demand_AGB = self.LPB_mplc_log_file_dictionary[a_key][99]
            self.demand_LUT17_minimum = self.LPB_mplc_log_file_dictionary[a_key][100]
            self.demand_LUT17_mean = self.LPB_mplc_log_file_dictionary[a_key][101]
            self.demand_LUT17_maximum = self.LPB_mplc_log_file_dictionary[a_key][102]
            self.allocated_pixels_LUT17 = self.LPB_mplc_log_file_dictionary[a_key][103]
            self.percentage_of_landscape_LUT17 = self.LPB_mplc_log_file_dictionary[a_key][104]
            # LUT18
            self.allocated_pixels_LUT18 = self.LPB_mplc_log_file_dictionary[a_key][105]
            self.percentage_of_landscape_LUT18 = self.LPB_mplc_log_file_dictionary[a_key][106]
            # AGB Mg harvested

            # HIDDEN DEFORESTATION
            self.maximum_deforested_for_input_biomass_area = self.LPB_mplc_log_file_dictionary[a_key][107]
            self.maximum_deforested_for_input_biomass_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][108]

            # CONVERTED FOREST (new land use type)
            self.converted_forest_area = self.LPB_mplc_log_file_dictionary[a_key][109]
            self.converted_forest_area_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][110]

            # LANDSCAPE MODELLING PROBABILITY/UNCERTAINTY
            self.pixels_in_probability_class_1 = self.LPB_mplc_log_file_dictionary[a_key][111]
            self.percentage_of_landscape_probability_class_1 = self.LPB_mplc_log_file_dictionary[a_key][112]
            self.pixels_in_probability_class_2 = self.LPB_mplc_log_file_dictionary[a_key][113]
            self.percentage_of_landscape_probability_class_2 = self.LPB_mplc_log_file_dictionary[a_key][114]
            self.pixels_in_probability_class_3 = self.LPB_mplc_log_file_dictionary[a_key][115]
            self.percentage_of_landscape_probability_class_3 = self.LPB_mplc_log_file_dictionary[a_key][116]
            self.pixels_in_probability_class_4 = self.LPB_mplc_log_file_dictionary[a_key][117]
            self.percentage_of_landscape_probability_class_4 = self.LPB_mplc_log_file_dictionary[a_key][118]
            self.pixels_in_probability_class_5 = self.LPB_mplc_log_file_dictionary[a_key][119]
            self.percentage_of_landscape_probability_class_5 = self.LPB_mplc_log_file_dictionary[a_key][120]
            self.pixels_in_probability_class_6 = self.LPB_mplc_log_file_dictionary[a_key][121]
            self.percentage_of_landscape_probability_class_6 = self.LPB_mplc_log_file_dictionary[a_key][122]
            self.pixels_in_probability_class_7 = self.LPB_mplc_log_file_dictionary[a_key][123]
            self.percentage_of_landscape_probability_class_7 = self.LPB_mplc_log_file_dictionary[a_key][124]

            # LAND USE IN RESTRICTED AREAS
            self.restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][125]
            self.restricted_areas_area_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][126]
            self.total_of_land_use_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][127]
            self.total_of_land_use_in_restricted_areas_area_percentage_of_restricted_area = self.LPB_mplc_log_file_dictionary[a_key][128]
            self.total_of_new_land_use_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][129]
            self.total_of_new_land_use_in_restricted_areas_area_percentage_of_restricted_area = self.LPB_mplc_log_file_dictionary[a_key][130]
            self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area = self.LPB_mplc_log_file_dictionary[a_key][131]
            self.total_of_new_land_use_in_restricted_areas_on_former_forest_pixels_area_percentage_of_restricted_area = self.LPB_mplc_log_file_dictionary[a_key][132]
            self.mplc_disturbed_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][133]
            self.mplc_disturbed_in_restricted_areas_percentage_of_restricted_area = self.LPB_mplc_log_file_dictionary[a_key][134]
            self.mplc_undisturbed_in_restricted_areas_area = self.LPB_mplc_log_file_dictionary[a_key][135]
            self.mplc_undisturbed_in_restricted_areas_percentage_of_restricted_area = self.LPB_mplc_log_file_dictionary[a_key][136]

            # FOREST net gross disturbed undisturbed
            self.gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][137]
            self.gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][138]
            self.net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][139]
            self.net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][140]
            self.gross_mplc_disturbed_forest_area = self.LPB_mplc_log_file_dictionary[a_key][141]
            self.gross_mplc_disturbed_forest_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][142]
            self.gross_mplc_undisturbed_forest_area = self.LPB_mplc_log_file_dictionary[a_key][143]
            self.gross_mplc_undisturbed_forest_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][144]
            self.net_mplc_disturbed_forest_area = self.LPB_mplc_log_file_dictionary[a_key][145]
            self.net_mplc_disturbed_forest_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][146]
            self.net_mplc_undisturbed_forest_area = self.LPB_mplc_log_file_dictionary[a_key][147]
            self.net_mplc_undisturbed_forest_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][148]
            self.gross_minus_net_forest_disturbed_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][149]
            self.gross_minus_net_forest_disturbed_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][150]
            self.gross_minus_net_forest_undisturbed_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][151]
            self.gross_minus_net_forest_undisturbed_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][152]

            # TRUE FOREST IMPACTED BY ANTHROPOGENIC FEATURES (LUT08)
            self.true_gross_forest_impacted_by_anthropogenic_features_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][153]
            self.true_gross_forest_impacted_by_anthropogenic_features_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][154]
            self.true_net_forest_impacted_by_anthropogenic_features_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][155]
            self.true_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = self.LPB_mplc_log_file_dictionary[a_key][156]
            self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][157]
            self.true_gross_minus_net_forest_impacted_by_anthropogenic_features_mplc_percentage_of_gross_forest = self.LPB_mplc_log_file_dictionary[a_key][158]

            # FOREST DEGRADATION/REGENERATION
            # 1) degradation
            # degradation low
            self.low_degradation_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][159]
            self.low_degradation_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][160]
            self.low_degradation_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][161]
            self.low_degradation_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][162]
            self.low_degradation_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][163]
            self.low_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][164]
            # degradation moderate
            self.moderate_degradation_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][165]
            self.moderate_degradation_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][166]
            self.moderate_degradation_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][167]
            self.moderate_degradation_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][168]
            self.moderate_degradation_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][169]
            self.moderate_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][170]
            # degradation severe
            self.severe_degradation_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][171]
            self.severe_degradation_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][172]
            self.severe_degradation_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][173]
            self.severe_degradation_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][174]
            self.severe_degradation_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][175]
            self.severe_degradation_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][176]
            # degradation absolute (= LUT17 net forest deforested)
            self.absolute_degradation_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][177]
            self.absolute_degradation_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][178]
            self.absolute_degradation_net_forest_disturbed_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][179]
            self.absolute_degradation_net_forest_disturbed_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][180]
            self.absolute_degradation_net_forest_undisturbed_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][181]
            self.absolute_degradation_net_forest_undisturbed_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][182]

            # 2) regeneration
            # regeneration low
            self.low_regeneration_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][183]
            self.low_regeneration_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][184]
            self.low_regeneration_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][185]
            self.low_regeneration_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][186]
            self.low_regeneration_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][187]
            self.low_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][188]
            # regeneration medium
            self.medium_regeneration_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][189]
            self.medium_regeneration_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][190]
            self.medium_regeneration_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][191]
            self.medium_regeneration_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][192]
            self.medium_regeneration_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][193]
            self.medium_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][194]
            # regeneration high
            self.high_regeneration_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][195]
            self.high_regeneration_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][196]
            self.high_regeneration_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][197]
            self.high_regeneration_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][198]
            self.high_regeneration_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][199]
            self.high_regeneration_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][200]
            # regeneration full (climax stadium, still not all primary forest traits given))
            self.full_regeneration_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][201]
            self.full_regeneration_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][202]
            self.full_regeneration_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][203]
            self.full_regeneration_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][204]
            self.full_regeneration_disturbed_forest_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][205]
            self.full_regeneration_disturbed_forest_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][206]
            self.full_regeneration_disturbed_forest_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][207]
            self.full_regeneration_disturbed_forest_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][208]
            self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][209]
            self.full_regeneration_disturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][210]
            self.full_regeneration_undisturbed_forest_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][211]
            self.full_regeneration_undisturbed_forest_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][212]
            self.full_regeneration_undisturbed_forest_gross_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][213]
            self.full_regeneration_undisturbed_forest_gross_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][214]
            self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_area = self.LPB_mplc_log_file_dictionary[a_key][215]
            self.full_regeneration_undisturbed_forest_gross_minus_net_forest_mplc_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][216]

            # FOREST AGB in Mg -> tC
            # potential maximum AGB
            self.potential_maximum_undisturbed_forest_AGB_maptotal = self.LPB_mplc_log_file_dictionary[a_key][217]
            self.potential_maximum_undisturbed_forest_AGB_Carbon = self.LPB_mplc_log_file_dictionary[a_key][218]
            # initial AGB simulation start
            self.initial_AGB_maptotal = self.LPB_mplc_log_file_dictionary[a_key][219]
            self.initial_AGB_Carbon = self.LPB_mplc_log_file_dictionary[a_key][220]
            self.initial_AGB_percentage_of_potential_maximum_undisturbed_AGB = self.LPB_mplc_log_file_dictionary[a_key][221]
            # demand AGB for the time step
            self.demand_timber_AGB = self.LPB_mplc_log_file_dictionary[a_key][222]
            self.demand_fuelwood_AGB = self.LPB_mplc_log_file_dictionary[a_key][223]
            self.demand_charcoal_AGB = self.LPB_mplc_log_file_dictionary[a_key][224]
            self.demand_AGB = self.LPB_mplc_log_file_dictionary[a_key][225]
            # final total AGB for the time step
            self.final_AGB_gross_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][226]
            self.final_AGB_gross_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][227]
            self.final_AGB_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][228]
            self.final_AGB_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][229]
            self.final_AGB_gross_minus_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][230]
            self.final_AGB_gross_minus_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][231]

            # final AGB agroforestry
            self.final_agroforestry_AGB_maptotal = self.LPB_mplc_log_file_dictionary[a_key][232]
            self.final_agroforestry_AGB_Carbon = self.LPB_mplc_log_file_dictionary[a_key][233]
            # final AGB plantation
            self.final_plantation_AGB_maptotal = self.LPB_mplc_log_file_dictionary[a_key][234]
            self.final_plantation_AGB_Carbon = self.LPB_mplc_log_file_dictionary[a_key][235]
            # final AGB disturbed forest
            self.final_disturbed_forest_AGB_gross_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][236]
            self.final_disturbed_forest_AGB_gross_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][237]
            self.final_disturbed_forest_AGB_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][238]
            self.final_disturbed_forest_AGB_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][239]
            self.final_disturbed_forest_AGB_net_forest_percentage_of_gross_disturbed_forest = self.LPB_mplc_log_file_dictionary[a_key][240]
            self.final_disturbed_forest_AGB_gross_minus_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][241]
            self.final_disturbed_forest_AGB_gross_minus_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][242]
            self.final_disturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_disturbed_forest = self.LPB_mplc_log_file_dictionary[a_key][243]
            # final AGB undisturbed forest
            self.final_undisturbed_forest_AGB_gross_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][244]
            self.final_undisturbed_forest_AGB_gross_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][245]
            self.final_undisturbed_forest_AGB_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][246]
            self.final_undisturbed_forest_AGB_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][247]
            self.final_undisturbed_forest_AGB_net_forest_percentage_of_gross_undisturbed_forest = self.LPB_mplc_log_file_dictionary[a_key][248]
            self.final_undisturbed_forest_AGB_gross_minus_net_forest_maptotal = self.LPB_mplc_log_file_dictionary[a_key][249]
            self.final_undisturbed_forest_AGB_gross_minus_net_forest_Carbon = self.LPB_mplc_log_file_dictionary[a_key][250]
            self.final_undisturbed_forest_AGB_gross_minus_net_forest_percentage_of_gross_undisturbed_forest = self.LPB_mplc_log_file_dictionary[a_key][251]

            # FOREST REMAINING without direct anthropogenic impact
            # gross forest
            # undisturbed
            self.remaining_gross_undisturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][252]
            self.remaining_gross_undisturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][253]
            # disturbed
            self.remaining_gross_disturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][254]
            self.remaining_gross_disturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][255]
            # net forest
            # undisturbed
            self.remaining_net_undisturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][256]
            self.remaining_net_undisturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][257]
            # disturbed
            self.remaining_net_disturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][258]
            self.remaining_net_disturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][259]
            # gross minus net
            # undisturbed
            self.remaining_gross_minus_net_undisturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][260]
            self.remaining_gross_minus_net_undisturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][261]
            # disturbed
            self.remaining_gross_minus_net_disturbed_forest_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][262]
            self.remaining_gross_minus_net_disturbed_forest_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][263]

            # FOREST 100 years without anthropogenic impact (potential primary stadium)
            # former disturbed forest
            self.former_disturbed_gross_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][264]
            self.former_disturbed_gross_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][265]
            self.former_disturbed_net_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][266]
            self.former_disturbed_net_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][267]
            self.former_disturbed_gross_minus_net_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][268]
            self.former_disturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][269]
            # initial undisturbed forest
            self.initial_undisturbed_gross_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][270]
            self.initial_undisturbed_gross_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][271]
            self.initial_undisturbed_net_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][271]
            self.initial_undisturbed_net_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][273]
            self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_area = self.LPB_mplc_log_file_dictionary[a_key][274]
            self.initial_undisturbed_gross_minus_net_forest_100years_without_impact_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][275]

            # FOREST HABITAT DISTURBED AND UNDISTURBED
            self.mplc_disturbed_forest_fringe_area = self.LPB_mplc_log_file_dictionary[a_key][276]
            self.mplc_disturbed_forest_fringe_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][277]
            self.mplc_undisturbed_forest_habitat_area = self.LPB_mplc_log_file_dictionary[a_key][278]
            self.mplc_undisturbed_forest_habitat_percentage_of_landscape = self.LPB_mplc_log_file_dictionary[a_key][279]

            # 5 TOP CROPS YIELDS
            # 1
            self.top_crop_1_share_of_LUT_acreage = self.LPB_mplc_log_file_dictionary[a_key][280]
            self.top_crop_1_yield_minimum = self.LPB_mplc_log_file_dictionary[a_key][281]
            self.top_crop_1_yield_mean = self.LPB_mplc_log_file_dictionary[a_key][282]
            self.top_crop_1_yield_maximum = self.LPB_mplc_log_file_dictionary[a_key][283]
            # 2
            self.top_crop_2_share_of_LUT_acreage = self.LPB_mplc_log_file_dictionary[a_key][284]
            self.top_crop_2_yield_minimum = self.LPB_mplc_log_file_dictionary[a_key][285]
            self.top_crop_2_yield_mean = self.LPB_mplc_log_file_dictionary[a_key][286]
            self.top_crop_2_yield_maximum = self.LPB_mplc_log_file_dictionary[a_key][287]
            # 3
            self.top_crop_3_share_of_LUT_acreage = self.LPB_mplc_log_file_dictionary[a_key][288]
            self.top_crop_3_yield_minimum = self.LPB_mplc_log_file_dictionary[a_key][289]
            self.top_crop_3_yield_mean = self.LPB_mplc_log_file_dictionary[a_key][290]
            self.top_crop_3_yield_maximum = self.LPB_mplc_log_file_dictionary[a_key][291]
            # 4
            self.top_crop_4_share_of_LUT_acreage = self.LPB_mplc_log_file_dictionary[a_key][292]
            self.top_crop_4_yield_minimum = self.LPB_mplc_log_file_dictionary[a_key][293]
            self.top_crop_4_yield_mean = self.LPB_mplc_log_file_dictionary[a_key][294]
            self.top_crop_4_yield_maximum = self.LPB_mplc_log_file_dictionary[a_key][295]
            # 5
            self.top_crop_5_share_of_LUT_acreage = self.LPB_mplc_log_file_dictionary[a_key][296]
            self.top_crop_5_yield_minimum = self.LPB_mplc_log_file_dictionary[a_key][297]
            self.top_crop_5_yield_mean = self.LPB_mplc_log_file_dictionary[a_key][298]
            self.top_crop_5_yield_maximum = self.LPB_mplc_log_file_dictionary[a_key][299]


        # =================================================================== #

    def make_forest_degradation_maps_for_the_time_step_accessible(self):

        print('\nextracting user-defined forest degradation map info for RAP LUT25 ...')

        list_of_user_defined_degradation_stages = []

        if self.user_defined_RAPLUT25_input_degradation_stages_dictionary['degradation_severe'] == True:
            list_of_user_defined_degradation_stages.append(3)
        if self.user_defined_RAPLUT25_input_degradation_stages_dictionary['degradation_moderate'] == True:
            list_of_user_defined_degradation_stages.append(2)
        if self.user_defined_RAPLUT25_input_degradation_stages_dictionary['degradation_low'] == True:
            list_of_user_defined_degradation_stages.append(1)

        # NOMINAL CLASSES
        # degradation low = 1
        # degradation moderate = 2
        # degradation severe = 3
        # degradation absolute = 4

        # regeneration low = 5
        # regeneration medium = 6
        # regeneration high = 7
        # regeneration full = 8

        # get the general map of forest degradation and regeneration for the time step
        a_key = self.time_step
        if a_key in self.dictionary_of_mplc_degradation_regeneration_files:
            time_step_fdr_map = self.dictionary_of_mplc_degradation_regeneration_files[a_key]

        # extract the user-defined degradation stages
        self.user_defined_degradation_stages_map = boolean(self.null_mask_map)
        for a_stage in list_of_user_defined_degradation_stages:
            temporal_time_step_map = ifthen(scalar(time_step_fdr_map) == scalar(a_stage),
                                            boolean(1))
            self.user_defined_degradation_stages_map = cover(boolean(temporal_time_step_map), boolean(self.user_defined_degradation_stages_map))

        print('extracting user-defined forest degradation map info for RAP LUT25 done')

        # =================================================================== #

    def calculate_initial_national_net_forest_plus_percentage_goal(self):
        """This method calculates amount and position of the targeted area goal for net forest.
        It is only needed once."""

        if self.time_step == 1:
            # depending on scenario calculate the required amount:
             # 1) calculate how much new area should be allocated:
             # get the initial area number
            self.inital_net_forest_national_area = int(maptotal(scalar(self.initial_net_forest_national_map)))
            targeted_net_forest_dictionary['initial_area'] = self.inital_net_forest_national_area
            # get the required additional percentage
            self.net_forest_percentage_increment_goal = Parameters.get_net_forest_percentage_increment_goal()
            targeted_net_forest_dictionary[
                'targeted_percentage_increment'] = self.net_forest_percentage_increment_goal

            # calculate the needed amount (round up to a full pixel)
            self.required_additional_net_forest_area = math.ceil((self.inital_net_forest_national_area / 100) * self.net_forest_percentage_increment_goal)
            targeted_net_forest_dictionary['targeted_area_increment'] = self.required_additional_net_forest_area
            # calculate the targeted total amount
            self.RAP_targeted_total_net_forest_area = self.inital_net_forest_national_area + self.required_additional_net_forest_area
            targeted_net_forest_dictionary['targeted_total_area'] = self.RAP_targeted_total_net_forest_area

            self.RAP_targeted_net_forest_percentage_of_landscape = round(
                float((self.RAP_targeted_total_net_forest_area / self.hundred_percent_area) * 100), 2)


            # 2) allocate around forest fringe starting top-down from pixels with 7 neighbors:
            # no immutables are derived by design, since this is calculated for a regional landscape perspective

            # get the forest fringe suitability
            scalar_self = scalar(self.initial_net_forest_national_map)

            # SH: Count cells within a 3x3 window to determine the forest fringe cells
            window_length = 3 * Parameters.get_cell_length_in_m()  # 9(-1) cells if not forest fringe
            number_neighbors_net_forest_map = windowtotal(scalar_self, window_length) - scalar_self

            net_forest_fringe_map = ifthen(scalar(number_neighbors_net_forest_map) < scalar(8),
                                           # forest fringes are determined by missing pixels in the window (less than 9 (-1) present)
                                           scalar(number_neighbors_net_forest_map))

            # JV: The number of neighbors are turned into suitability values between 0 and 1
            maximum_number_neighbors = ((window_length / celllength()) ** 2) - 1
            net_forest_fringe_suitability_map = ifthen(net_forest_fringe_map > 0,
                                                       number_neighbors_net_forest_map / maximum_number_neighbors)

            suitability_map = spatial(scalar(0))
            # LPB alternation
            # 1 number of neighbors same class
            # 7 distance to net forest edge
            # 8 current land use
            print('\ncalculating suitabilities for net forest increment initiated ...')
            for a_factor in [1, 7, 8]:
                if a_factor == 1:  # suitability factor = number of neighbors same class
                    suitability_map += self.weights_list[0] * \
                                       self._get_neighbor_suitability(net_forest_map=self.initial_net_forest_national_map)
                    print('neighbor suitability for net forest increment calculated')
                elif a_factor == 7:  # suitability factor = distance to net forest edge
                    suitability_map += self.weights_list[1] * \
                                       self._get_net_forest_edge_suitability(net_forest_map=self.initial_net_forest_national_map)
                    print('net forest edge suitability for net forest increment calculated')
                elif a_factor == 8:  # suitability factor = current land use
                    suitability_map += self.weights_list[2] * \
                                       self._get_current_land_use_type_suitability(net_forest_map=self.initial_net_forest_national_map)
                    print('current land use type suitability for net forest increment calculated')
            net_forest_increment_suitability_map = ifthen(scalar(self.initial_net_forest_national_map) == scalar(0),
                                                                     suitability_map)
            net_forest_increment_suitability_map = self._normalize_map(
                net_forest_increment_suitability_map)
            print('maximum suitability map for net forest increment calculated')

            ordered_suitability_map = order(net_forest_increment_suitability_map)
            map_maximum_ordered_suitability = mapmaximum(ordered_suitability_map)
            threshold = map_maximum_ordered_suitability - self.required_additional_net_forest_area

            # make it first a classified GIF map
            targeted_net_forest_map = ifthen(ordered_suitability_map > threshold,
                                             scalar(3))

            # PER SCENARIO TARGETED NET FOREST MAP
            targeted_net_forest_map = cover(scalar(targeted_net_forest_map),
                                            scalar(self.initial_net_forest_national_map))

            targeted_net_forest_maptotal = int (maptotal(scalar(boolean(targeted_net_forest_map > 0))))

            targeted_net_forest_map = ifthenelse(targeted_net_forest_map != 3, # class 3 is additionally required area
                                                 targeted_net_forest_map + 1, # class 1 is the region, class 2 is existing net forest according to national map
                                                 targeted_net_forest_map)

            pcraster_conform_map_name = 'RAP_tnf'
            time_step = self.time_step  # needed for PCraster conform output
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(targeted_net_forest_map,
                   os.path.join(Filepaths.folder_RAP_targeted_net_forest, output_map_name))
            print('targeted_net_forest_map created and stored as "RAP_tnf" in:',
                  Filepaths.folder_RAP_targeted_net_forest)


            # make it a boolean map for further use
            self.targeted_net_forest_map = ifthenelse(targeted_net_forest_map  >= 2,
                                                      boolean(1),
                                                      boolean(self.null_mask_map))

        # =================================================================== #

    def _get_neighbor_suitability(self, net_forest_map):
        """ JV: Return suitability map based on number of neighbors with a related type."""
        boolean_self = pcreq(scalar(net_forest_map), scalar(1))
        scalar_self = scalar(boolean_self)
        # JV: Count number of neighbors with 'true' in a window with length from parameters
        # JV: and assign this value to the center cell
        variables_list = self.variables_dictionary.get(1)
        window_length = variables_list[0]
        number_neighbors_net_forest = windowtotal(
            scalar_self, window_length) - scalar_self
        # JV: The number of neighbors are turned into suitability values between 0 and 1
        maximum_number_neighbors = ((window_length / celllength()) ** 2) - 1
        neighbor_suitability = number_neighbors_net_forest / maximum_number_neighbors
        ## JV:   report(neighbor_suitability, 'neighbor_suitability')
        return neighbor_suitability

        # =================================================================== #

    def _get_net_forest_edge_suitability(self, net_forest_map):

        distances_to_net_forest_edge_map = spread(net_forest_map, 1, 1)
        net_forest_edge_suitability_map = self._normalize_map(-1 / distances_to_net_forest_edge_map)
        return net_forest_edge_suitability_map

        # =================================================================== #

    def _get_current_land_use_type_suitability(self, net_forest_map):
        """ JV: Return suitability map based on current land use type."""
        variables_dictionary = self.variables_dictionary.get(8)
        current_map = self.null_mask_map
        for a_key in variables_dictionary.keys():
            current_map = ifthenelse(pcreq(net_forest_map, a_key),
                                     variables_dictionary.get(a_key),
                                     scalar(current_map))  # SH: changed to scalar
        current_land_use_type_suitability_map = self._normalize_map(current_map)
        return current_land_use_type_suitability_map

        # =================================================================== #

    def _normalize_map(self, a_map):
        """ JV: Return a normalized version of the input map."""
        map_maximum = mapmaximum(a_map)
        map_minimum = mapminimum(a_map)
        difference = float(map_maximum - map_minimum)
        if difference < 0.000001:
            normalized_map = (a_map - map_minimum) / 0.000001
        else:
            normalized_map = (a_map - map_minimum) / difference
        return normalized_map

        # =================================================================== #

    def get_climate_period_data(self):

        print('\nreading climate period input data for the time step initiated ...')
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

    def calculate_RAP_other_ecosystems_mask(self):
        """This method calculates the existing other ecosystem pixels in the initial input map as a mask for Landscape restoration.
        If provided further user information is incorporated.
        Only needed once."""

        if self.time_step == 1:
            print('\ncalculating RAP other ecosystems mask ...')

            # get the information contained in the original map (COPERNICUS LUTS)
            initial_LULC_map = readmap(Filepaths.file_initial_LULC_input) # this map contains all pixels

            self.initial_RAP_other_ecosystem_map = ifthenelse(scalar(initial_LULC_map) == scalar(10), # moss, lichen, bare, sparse vegetation
                                                              scalar(1),
                                                              scalar(self.null_mask_map))

            self.initial_RAP_other_ecosystem_map = ifthenelse(scalar(initial_LULC_map) == scalar(11), # herbaceous wetland
                                                              scalar(1),
                                                              scalar(self.initial_RAP_other_ecosystem_map))

            # add external information, which is not contained in the original map
            self.initial_RAP_other_ecosystem_map = ifthenelse(scalar(self.additional_ecosystems_to_be_restored_map) == scalar(1), # other ecosystems in the landscape to be restored if available
                                                              scalar(1),
                                                              scalar(self.initial_RAP_other_ecosystem_map))

            print('calculating RAP other ecosystems mask done')

        # =================================================================== #

    def calculate_population_peak_land_use_mask(self):
        """ This method produces a boolean mask of land use of the population peak.
        It will be used to simulate the potentially successfull restoration measures prior population peak.
        only needed once"""

        if self.time_step == 1:

            print('\ncalculating RAP population peak land use mask ...')

            time_step_key = self.population_peak_year - int(Parameters.get_initial_simulation_year()) + 1

            print('population_time_step_key is:', time_step_key)

            population_peak_mplc_mask_basic_map = self.dictionary_of_mplc_files[time_step_key]

            list_of_active_land_use_types = Parameters.get_active_land_use_types_list()
            list_of_active_land_use_types.append(18) # plantation deforested is needed because it symbolizes static demand

            temporal_mask_map = self.null_mask_map
            for a_LUT in list_of_active_land_use_types:
                temporal_mask_map = ifthenelse(scalar(population_peak_mplc_mask_basic_map) == scalar(a_LUT),
                                               scalar(1),
                                               scalar(temporal_mask_map))

            self.population_peak_land_use_mask_map = temporal_mask_map

            print('\ncalculating RAP population peak land use mask done')

    # =================================================================== #

    def calculate_peak_demands_year_land_use_mask(self):
        """ This method produces a boolean mask of land use of the population peak.
        It will be used to simulate the potentially successfull restoration measures prior population peak.
        only needed once"""

        if self.time_step == 1:

            print('\ncalculating RAP peak demands year land use mask ...')

            time_step_key = self.peak_demands_year - int(Parameters.get_initial_simulation_year()) + 1

            print('peak_demands_year_time_step_key is:', time_step_key)

            peak_demands_year_mplc_mask_basic_map = self.dictionary_of_mplc_files[time_step_key]

            list_of_active_land_use_types = Parameters.get_active_land_use_types_list()
            list_of_active_land_use_types.append(18) # plantation deforested is needed because it symbolizes static demand

            temporal_mask_map = self.null_mask_map
            for a_LUT in list_of_active_land_use_types:
                temporal_mask_map = ifthenelse(scalar(peak_demands_year_mplc_mask_basic_map) == scalar(a_LUT),
                                               scalar(1),
                                               scalar(temporal_mask_map))

            self.peak_demands_year_land_use_mask_map = temporal_mask_map

            print('\ncalculating RAP peak demands year land use mask done')

    # =================================================================== #

    def calculate_RAP_possible_landscape_configuration(self):
        """THE KEY: RAP LUTs allocations are based on a conflict free allocation procedure building on the mplc landscape."""

        print('\ncalculating possible landscape configuration ...')

        # get the base map for the time step
        mplc_input_landscape = self.dictionary_of_mplc_files[self.time_step]

        # declare the temporal landscape to be altered for the RAP types
        temporal_possible_landscape_configuration_map = mplc_input_landscape  # get from dictionary for the time step

        # get the list of types to allocate
        list_of_RAP_land_use_types = Parameters.get_list_of_RAP_land_use_types()

        for a_type in list_of_RAP_land_use_types:
            # perform the re-interpretation of the landscape
            temporal_possible_landscape_configuration_map = self._RAP_allocation(temporal_possible_landscape_configuration_map,
                                                                                      a_type)
        # get the final nominal landscape
        self.possible_landscape_configuration_map = temporal_possible_landscape_configuration_map

        # report output
        time_step = self.time_step
        pcraster_conform_map_name = 'RAP'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.possible_landscape_configuration_map,
               os.path.join(Filepaths.folder_RAP_POSSIBLE_LANDSCAPE_CONFIGURATION, output_map_name))
        print('self.possible_landscape_configuration_map created and stored as "RAP" in:',
              Filepaths.folder_RAP_POSSIBLE_LANDSCAPE_CONFIGURATION)

            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#

        RAP_population_and_LUTs_shares_dictionary['population'].append(self.population)
        self.population_number_of_smallholders = math.ceil(
            (int(self.population) / 100) * Parameters.get_regional_share_smallholders_of_population())
        RAP_population_and_LUTs_shares_dictionary['smallholder_share'].append(self.population_number_of_smallholders)

        # 1.3) SH: count the pixels per LUT in the map, draw %,
        # to compare with mplc show active LUTs, abandoned LUTs plus RAP LUTs

        # LUT01
        self.RAP_allocated_pixels_LUT01 = int(maptotal(scalar(boolean(self.possible_landscape_configuration_map == 1))))
        self.RAP_percentage_of_landscape_LUT01 = round(float((self.RAP_allocated_pixels_LUT01 / self.hundred_percent_area) * 100), 2)

        # LUT02
        self.RAP_allocated_pixels_LUT02 = 'subsumed in LUT21'

        # LUT03
        self.RAP_allocated_pixels_LUT03 = 'subsumed in LUT21'

        # LU04
        self.RAP_allocated_pixels_LUT04 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 4))))
        self.RAP_percentage_of_landscape_LUT04 = round(
            float((self.RAP_allocated_pixels_LUT04 / self.hundred_percent_area) * 100), 2)

        # LUT05
        self.RAP_allocated_pixels_LUT05 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 5))))
        self.RAP_percentage_of_landscape_LUT05 = round(
            float((self.RAP_allocated_pixels_LUT05 / self.hundred_percent_area) * 100), 2)

        # LUT06
        self.RAP_allocated_pixels_LUT06 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 6))))
        self.RAP_percentage_of_landscape_LUT06 = round(
            float((self.RAP_allocated_pixels_LUT06 / self.hundred_percent_area) * 100), 2)

        # LUT07
        self.RAP_allocated_pixels_LUT07 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 7))))
        self.RAP_percentage_of_landscape_LUT07 = round(
            float((self.RAP_allocated_pixels_LUT07 / self.hundred_percent_area) * 100), 2)

        # LUT08
        self.RAP_allocated_pixels_LUT08 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 8))))
        self.RAP_percentage_of_landscape_LUT08 = round(
            float((self.RAP_allocated_pixels_LUT08 / self.hundred_percent_area) * 100), 2)

        # LUT09
        self.RAP_allocated_pixels_LUT09 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 9))))
        self.RAP_percentage_of_landscape_LUT09 = round(
            float((self.RAP_allocated_pixels_LUT09 / self.hundred_percent_area) * 100), 2)

        # LUT10
        self.RAP_allocated_pixels_LUT10 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 10))))
        self.RAP_percentage_of_landscape_LUT10 = round(
            float((self.RAP_allocated_pixels_LUT10 / self.hundred_percent_area) * 100), 2)

        # LUT11
        self.RAP_allocated_pixels_LUT11 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 11))))
        self.RAP_percentage_of_landscape_LUT11 = round(
            float((self.RAP_allocated_pixels_LUT11 / self.hundred_percent_area) * 100), 2)

        # LUT12
        self.RAP_allocated_pixels_LUT12 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 12))))
        self.RAP_percentage_of_landscape_LUT12 = round(
            float((self.RAP_allocated_pixels_LUT12 / self.hundred_percent_area) * 100), 2)

        # LUT13
        self.RAP_allocated_pixels_LUT13 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 13))))
        self.RAP_percentage_of_landscape_LUT13 = round(
            float((self.RAP_allocated_pixels_LUT13 / self.hundred_percent_area) * 100), 2)

        # LUT14
        self.RAP_allocated_pixels_LUT14 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 14))))
        self.RAP_percentage_of_landscape_LUT14 = round(
            float((self.RAP_allocated_pixels_LUT14 / self.hundred_percent_area) * 100), 2)

        # LUT15
        self.RAP_allocated_pixels_LUT15 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 15))))
        self.RAP_percentage_of_landscape_LUT15 = round(
            float((self.RAP_allocated_pixels_LUT15 / self.hundred_percent_area) * 100), 2)

        # LUT16
        self.RAP_allocated_pixels_LUT16 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 16))))
        self.RAP_percentage_of_landscape_LUT16 = round(
            float((self.RAP_allocated_pixels_LUT16 / self.hundred_percent_area) * 100), 2)

        # LUT17
        self.RAP_allocated_pixels_LUT17 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 17))))
        self.RAP_percentage_of_landscape_LUT17 = round(
            float((self.RAP_allocated_pixels_LUT17 / self.hundred_percent_area) * 100), 2)

        # LUT18
        self.RAP_allocated_pixels_LUT18 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 18))))
        self.RAP_percentage_of_landscape_LUT18 = round(
            float((self.RAP_allocated_pixels_LUT18 / self.hundred_percent_area) * 100), 2)

        # ADDITIONAL RAP LUTS
        # LUT21
        self.RAP_allocated_pixels_LUT21 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 21))))
        self.RAP_percentage_of_landscape_LUT21 = round(
            float((self.RAP_allocated_pixels_LUT21 / self.hundred_percent_area) * 100), 2)
        RAP_population_and_LUTs_shares_dictionary['RAP_agroforestry'].append(self.RAP_allocated_pixels_LUT21)

        # LUT22
        self.RAP_allocated_pixels_LUT22 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 22))))
        self.RAP_percentage_of_landscape_LUT22 = round(
            float((self.RAP_allocated_pixels_LUT22 / self.hundred_percent_area) * 100), 2)
        RAP_population_and_LUTs_shares_dictionary['RAP_plantation'].append(self.RAP_allocated_pixels_LUT22)

        # LUT23
        self.RAP_allocated_pixels_LUT23 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 23))))
        self.RAP_percentage_of_landscape_LUT23 = round(
            float((self.RAP_allocated_pixels_LUT23 / self.hundred_percent_area) * 100), 2)
        RAP_population_and_LUTs_shares_dictionary['RAP_reforestation'].append(self.RAP_allocated_pixels_LUT23)

        # LUT24
        self.RAP_allocated_pixels_LUT24 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 24))))
        self.RAP_percentage_of_landscape_LUT24 = round(
            float((self.RAP_allocated_pixels_LUT24 / self.hundred_percent_area) * 100), 2)
        RAP_population_and_LUTs_shares_dictionary['RAP_other_ecosystems'].append(self.RAP_allocated_pixels_LUT24)

        self.RAP_allocated_pixels_LUT25 = int(
            maptotal(scalar(boolean(self.possible_landscape_configuration_map == 24))))
        self.RAP_percentage_of_landscape_LUT25 = round(
            float((self.RAP_allocated_pixels_LUT25 / self.hundred_percent_area) * 100), 2)
        RAP_population_and_LUTs_shares_dictionary['RAP_restoration_of_degraded_forest'].append(self.RAP_allocated_pixels_LUT25)

        # TOTAL RAP AND PERCENTAGE OF LANDSCAPE
        self.RAP_total = self.RAP_allocated_pixels_LUT21 + \
                         self.RAP_allocated_pixels_LUT22 + \
                         self.RAP_allocated_pixels_LUT23 + \
                         self.RAP_allocated_pixels_LUT24 + \
                         self.RAP_allocated_pixels_LUT25

        self.RAP_total_percentage_of_landscape = round(
            float((self.RAP_total / self.hundred_percent_area) * 100), 2)



        print('calculating possible landscape configuration done')

        # =================================================================== #

    def _RAP_allocation(self, temporal_possible_landscape_configuration_map, a_type):
        """This methods corrects the most probable landscape configuration map to the possible RAP LUTs"""

        # return map if no change is simulated
        temporal_possible_landscape_configuration_map = temporal_possible_landscape_configuration_map

        # ALLOCATE ON THE TRADITIONAL LUTS BASED ON ACTIVE RAP LUT TYPE

        if a_type == 21: # TRANSFORMATION FROM LUT CROPLAND-ANNUAL AND PASTURE TO AGROFORESTRY (DISPLAYED IS THE TOTAL POTENTIAL)

            temporal_possible_landscape_configuration_map = ifthenelse(
                scalar(temporal_possible_landscape_configuration_map) == scalar(2), # cropland-annual
                scalar(a_type),
                scalar(temporal_possible_landscape_configuration_map))

            temporal_possible_landscape_configuration_map = ifthenelse(
                scalar(temporal_possible_landscape_configuration_map) == scalar(3), # pasture
                scalar(a_type),
                scalar(temporal_possible_landscape_configuration_map))

        elif a_type == 22: # ADDITIONAL RAP PLANTATION OUTSIDE TARGETED NET FOREST AREA

            # get first the area naturally suited for reforestation and the intended net forest area
            potential_RAP_plantation_map = ifthen(
                scalar(self.projection_potential_natural_vegetation_distribution_map) == scalar(3), # only calculate on forest biome pixels
                scalar(self.targeted_net_forest_map)) # indicate where targeted net forest is

            RAP_plantation_environment_map = ifthen(scalar(potential_RAP_plantation_map) == scalar(0), # only calculate where no net forest is targeted
                                                    scalar(temporal_possible_landscape_configuration_map)) # get the environment LUTs

            RAP_plantation_environment_map = ifthen(scalar(self.initial_RAP_other_ecosystem_map) == scalar(0), # only calculate where no other ecosystems are placed
                                                    scalar(RAP_plantation_environment_map))

            # declare which land use types in the mplc map get changed to reforestation to RAP plantation in the area above
            list_of_mplc_LUTs_to_transform = [6,  # herbaceous vegetation
                                              7,  # shrubs
                                              14,  # 'cropland-annual - - abandoned'
                                              15,  # 'pasture - - abandoned'
                                              16,  # 'agroforestry - - abandoned'
                                              17]  # 'net forest - - deforested'

            # iterate over the landscape ...
            for a_LUT in list_of_mplc_LUTs_to_transform:
                temporal_plantation_environment_map = ifthen(scalar(RAP_plantation_environment_map) == scalar(a_LUT),
                                                                    scalar(a_type))

                # ... and combine within the method the new information with the temporal map
                temporal_possible_landscape_configuration_map = cover(scalar(temporal_plantation_environment_map),
                                                                      scalar(
                                                                          temporal_possible_landscape_configuration_map))

        elif a_type == 23: # REFORESTATION INSIDE TARGETED NET FOREST AREA

            # get first the area naturally suited for reforestation and the intended net forest area
            potential_reforestation_map = ifthen(scalar(self.projection_potential_natural_vegetation_distribution_map) == scalar(3), # only where forest biome is located
                                                 scalar(self.targeted_net_forest_map)) # and net forest is indicated

            reforestation_environment_map = ifthen(scalar(potential_reforestation_map) == scalar(1), # only calculate where net forest is targeted
                                                   scalar(temporal_possible_landscape_configuration_map)) # get the environment LUTs

            reforestation_environment_map = ifthen(scalar(self.initial_RAP_other_ecosystem_map) == scalar(0), # only calculate where no other ecosystems are placed
                                                    scalar(reforestation_environment_map))

            # declare which land use types in the mplc map get changed to reforestation in the area above
            list_of_mplc_LUTs_to_transform = [6, # herbaceous vegetation
                                              7, # shrubs
                                              14, # 'cropland-annual - - abandoned'
                                              15, # 'pasture - - abandoned'
                                              16, # 'agroforestry - - abandoned'
                                              17] # 'net forest - - deforested'

            # iterate over the landscape ...
            for a_LUT in list_of_mplc_LUTs_to_transform:
                temporal_reforestation_environment_map = ifthen(scalar(reforestation_environment_map) == scalar(a_LUT),
                                                                scalar(a_type))

                # ... and combine within the method the new information with the temporal map
                temporal_possible_landscape_configuration_map = cover(scalar(temporal_reforestation_environment_map),
                                                                      scalar(temporal_possible_landscape_configuration_map))

        elif a_type == 24: # RECREATION OF OTHER ECOSYSTEMS

            # ATTENTION: Currently this code can mostly only recognize ecosystem pixels which exclude anthropogenic use, so cultivation associated ecosystems would need new hardcoding

            # filter the cells in the current landscape which might be another ecosystem in the beginning and are now abandoned/deforested or even in succession again
            list_of_mplc_LUTs_to_transform = [6,  # herbaceous vegetation
                                              7,  # shrubs
                                              8,  # disturbed forest
                                              14,  # 'cropland-annual - - abandoned'
                                              15,  # 'pasture - - abandoned'
                                              16,  # 'agroforestry - - abandoned'
                                              17]  # 'net forest - - deforested'

            temporal_map_of_abandoned_or_deforested_types = self.null_mask_map
            for a_LUT in list_of_mplc_LUTs_to_transform:
                temporal_map_of_abandoned_or_deforested_types = ifthenelse(scalar(temporal_possible_landscape_configuration_map) == scalar(a_LUT),
                                                                           scalar(1),
                                                                           scalar(temporal_map_of_abandoned_or_deforested_types))

            temp_map_LUTs = ifthen(temporal_map_of_abandoned_or_deforested_types == 1,
                                   temporal_map_of_abandoned_or_deforested_types)

            temp_map_recent_ecosystem_restoration_potential = ifthen(temp_map_LUTs == 1,
                                                                     self.initial_RAP_other_ecosystem_map)

            temp_map_recent_ecosystem_restoration_potential = cover(scalar(temp_map_recent_ecosystem_restoration_potential), scalar(self.null_mask_map))

            temporal_possible_landscape_configuration_map = ifthenelse(scalar(temp_map_recent_ecosystem_restoration_potential) == scalar(1), # if the pixel is a former other ecosystem and now abandoned/deforested ...
                                                                       scalar(a_type), # ... indicate other ecosystem restoration
                                                                       scalar(temporal_possible_landscape_configuration_map))

        elif a_type == 25: # Allocation of RAP-LUT 25 restoration of degraded forest

            # ATTENTION: This LUT is only allocated on LUT08 according to the user-defined input degradation stages

            # filter the landscape for current disturbed forest (only applicable land use type for degraded forest)
            temporal_map_of_disturbed_forest = ifthenelse(scalar(temporal_possible_landscape_configuration_map) == scalar(8),
                                                          scalar(1),
                                                          scalar(self.null_mask_map))

            # get the cells that are described as degraded
            temporal_degraded_forest_map = ifthen(scalar(self.user_defined_degradation_stages_map) == scalar(1),
                                                  scalar(temporal_map_of_disturbed_forest))
            # filter potentially missing cells
            temporal_degraded_forest_map = ifthen(scalar(temporal_degraded_forest_map) > scalar(0),
                                                  scalar(1))

            # apply allocation
            temporal_degraded_forest_map = cover(scalar(temporal_degraded_forest_map), scalar(self.null_mask_map))

            temporal_possible_landscape_configuration_map = ifthenelse(scalar(temporal_degraded_forest_map) == scalar(1), # if the pixel is degraded forest ..
                                                                       scalar(a_type),  # ... indicate restoration
                                                                       scalar(temporal_possible_landscape_configuration_map))

        return temporal_possible_landscape_configuration_map

        # =================================================================== #

    def create_tiles_subsets(self):
        """ LAFORET method: create subset GIFs for the original study areas."""

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
                a_subset_output_folder = os.path.join(os.getcwd(), Filepaths.folder_outputs, 'RAP', 'TILES_RAP', 'tile_' + str(a_tile_identifier) + '_' + str(a_tile_name))
                os.makedirs(a_subset_output_folder, exist_ok=True)

        # for all time steps and given entries create a map
        for an_entry in self.dictionary_of_tiles_maps_clean:
            a_tile_map = self.dictionary_of_tiles_maps_clean[an_entry]['map']
            a_tile_identifier = self.dictionary_of_tiles_maps_clean[an_entry]['identifier']
            a_tile_name = self.dictionary_of_tiles_maps_clean[an_entry]['name']
            a_subset_output_folder = os.path.join(os.getcwd(), Filepaths.folder_outputs, 'RAP', 'TILES_RAP',
                                                       'tile_' + str(a_tile_identifier) + '_' + str(
                                                           a_tile_name))
            a_RAP_subset_map = ifthen(scalar(a_tile_map) == scalar(1),
                                       scalar(self.possible_landscape_configuration_map))

            # report
            time_step = self.time_step
            pcraster_conform_map_name = 'tile_' + str(a_tile_identifier)
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
            report(a_RAP_subset_map, os.path.join(a_subset_output_folder, output_map_name))
            print('a_RAP_subset_map for', str(a_tile_identifier), 'created and stored as', output_map_name, 'in:',
                  a_subset_output_folder)

        print('creating regional tiles subsets done')

        # =================================================================== #

    def calculate_RAP_potential_minimum_restoration(self):
        """This method shows area for potential successfull restoration outside the population peak mask prior restoration and
        on the possible landscape configuration afterwards. RAP LUT21 is not part of this calculation."""

        print('\ncalculating potential minimum restoration ...')

        RAP_potential_minimum_restoration_dictionary['population_peak_year'] = self.population_peak_year
        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
            RAP_potential_minimum_restoration_dictionary['peak_demands_year'] = self.population_peak_year
        else:
            RAP_potential_minimum_restoration_dictionary['peak_demands_year'] = self.peak_demands_year

        # First, get the according land use mask
        land_use_mask_map = self.null_mask_map
        if (Parameters.demand_configuration['overall_method'] == 'footprint' and
                Parameters.demand_configuration['internal_or_external'] == 'internal') and self.year <= self.population_peak_year:
            land_use_mask_map = self.population_peak_land_use_mask_map
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and
                Parameters.demand_configuration['internal_or_external'] == 'internal') and self.year <= self.peak_demands_year:
            land_use_mask_map = self.peak_demands_year_land_use_mask_map
        else:
            list_of_active_land_use_types = [1, # built-up
                                             5, # plantation
                                             18, # plantation deforested
                                             21] # cropland annual and pasture which might not be transformed yet

            temporal_mask_map = self.null_mask_map
            for a_LUT in list_of_active_land_use_types:
                temporal_mask_map = ifthenelse(scalar(self.possible_landscape_configuration_map) == scalar(a_LUT),
                                               scalar(1),
                                               scalar(temporal_mask_map))
            land_use_mask_map = temporal_mask_map

        # Secondly built a map that shows the remaining restoration outside this area (excluded is RAP LUT 21).
        potential_minimum_restoration_environment_map = ifthen(scalar(land_use_mask_map) == scalar(0),
                                                               scalar(self.possible_landscape_configuration_map))

        potential_minimum_restoration_LUT22_map = ifthen(
            scalar(potential_minimum_restoration_environment_map) == scalar(22), # RAP plantation
            scalar(2)) # class 2 for the GIF
        self.maptotal_potential_minimum_LUT22 = int(maptotal(scalar(boolean(potential_minimum_restoration_LUT22_map == 2))))
        RAP_potential_minimum_restoration_dictionary['LUT22'].append(self.maptotal_potential_minimum_LUT22)

        potential_minimum_restoration_LUT23_map = ifthen(
            scalar(potential_minimum_restoration_environment_map) == scalar(23), # RAP reforestation
            scalar(3))  # class  for the GIF
        self.maptotal_potential_minimum_LUT23 = int(maptotal(scalar(boolean(potential_minimum_restoration_LUT23_map == 3))))
        RAP_potential_minimum_restoration_dictionary['LUT23'].append(self.maptotal_potential_minimum_LUT23)

        potential_minimum_restoration_LUT24_map = ifthen(
            scalar(potential_minimum_restoration_environment_map) == scalar(24), # RAP other ecosystems
            scalar(4))  # class  for the GIF
        self.maptotal_potential_minimum_LUT24 = int(maptotal(scalar(boolean(potential_minimum_restoration_LUT24_map == 4))))
        RAP_potential_minimum_restoration_dictionary['LUT24'].append(self.maptotal_potential_minimum_LUT24)

        potential_minimum_restoration_LUT25_map = ifthen(
            scalar(potential_minimum_restoration_environment_map) == scalar(25),  # RAP other ecosystems
            scalar(5))  # class  for the GIF
        self.maptotal_potential_minimum_LUT25 = int(
            maptotal(scalar(boolean(potential_minimum_restoration_LUT25_map == 5))))
        RAP_potential_minimum_restoration_dictionary['LUT25'].append(self.maptotal_potential_minimum_LUT25)

        potential_minimum_restoration_map = cover(scalar(potential_minimum_restoration_LUT22_map), scalar(potential_minimum_restoration_LUT23_map))
        potential_minimum_restoration_map = cover(scalar(potential_minimum_restoration_LUT24_map), scalar(potential_minimum_restoration_map))
        potential_minimum_restoration_map = cover(scalar(potential_minimum_restoration_LUT25_map), scalar(potential_minimum_restoration_map))
        potential_minimum_restoration_map = cover(scalar(potential_minimum_restoration_map),
                                                  scalar(scalar(self.null_mask_map) + scalar(1)))

        # report
        time_step = self.time_step
        pcraster_conform_map_name = 'RAP_pmr'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(potential_minimum_restoration_map, os.path.join(Filepaths.folder_RAP_potential_minimum_restoration, output_map_name))
        print('potential_minimum_restoration_map created and stored as RAP_pmr in:',
              Filepaths.folder_RAP_potential_minimum_restoration)



        print('calculating potential minimum restoration done')

        # =================================================================== #

    def calculate_RAP_potential_additional_restricted_areas(self):
        """This method is based on the maximum anthropogenic impact for the population peak year."""

        print('\ncalculating potential additional restricted areas ...')

        # note the year of the population peak for the GIF
        list_restricted_areas.append(self.year)

        list_of_restricted_LUTs = Parameters.get_list_of_LUTs_for_definition_of_potential_restricted_areas()

        global list_of_LUTs_for_definition_of_potential_restricted_areas
        list_of_LUTs_for_definition_of_potential_restricted_areas = list_of_restricted_LUTs

        temporal_map_of_potential_area = self.null_mask_map

        for a_LUT in list_of_LUTs_for_definition_of_potential_restricted_areas:
            temporal_map_of_potential_area = ifthenelse(scalar(self.possible_landscape_configuration_map) == scalar(a_LUT),
                                                        scalar(2),
                                                        scalar(temporal_map_of_potential_area))

        RAP_suggested_and_existing_areas_map = ifthenelse(scalar(self.static_restricted_areas_map) == scalar(1),
                                                      scalar(1),
                                                      scalar(temporal_map_of_potential_area)) # region and new areas

        RAP_suggested_and_existing_areas_map = RAP_suggested_and_existing_areas_map + 1 # 1 = region, 2 = old restricted areas, 3 = suggested additional areas

        # report
        report(RAP_suggested_and_existing_areas_map, os.path.join(Filepaths.folder_RAP_restricted_areas, 'RAP_restricted_areas.map'))
        print('RAP_suggested_and_existing_areas_map.map created and stored as RAP_restricted_areas.map in:',
              Filepaths.folder_RAP_restricted_areas)

        # note the area for the GIF:
        maptotal_of_existing_restricted_areas = int(maptotal(scalar(boolean(RAP_suggested_and_existing_areas_map == 2))))
        list_restricted_areas.append(maptotal_of_existing_restricted_areas)
        existing_restricted_areas_percentage_of_landscape = round(
            float((maptotal_of_existing_restricted_areas / self.hundred_percent_area) * 100), 2)
        list_restricted_areas.append(existing_restricted_areas_percentage_of_landscape)
        # note the area for the GIF:
        maptotal_of_suggested_restricted_areas = int(maptotal(scalar(boolean(RAP_suggested_and_existing_areas_map == 3))))
        list_restricted_areas.append(maptotal_of_suggested_restricted_areas)
        ## note the area for the CSV
        self.RAP_potential_additional_restricted_areas = maptotal_of_suggested_restricted_areas
        # combine and note percentage
        potential_total_area_restricted_areas = maptotal_of_existing_restricted_areas + maptotal_of_suggested_restricted_areas
        potential_total_restricted_areas_percentage_of_landscape = round(
            float((potential_total_area_restricted_areas / self.hundred_percent_area) * 100), 2)
        list_restricted_areas.append(potential_total_restricted_areas_percentage_of_landscape)

        # Export to CSV too
        # create a new CSV
        with open(os.path.join(os.getcwd(), Filepaths.folder_RAP_CSVs,
                               'LPB-RAP_additional_suggested_restricted_areas.csv'), 'w',
                  newline='') as LPB_RAP_log_file:
            writer = csv.writer(LPB_RAP_log_file)
            LPB_writer = csv.writer(LPB_RAP_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-RAP additional suggested restricted areas',
                                  Parameters.get_country(), Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_RAP_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=['Position','Value'])
            LPB_writer.writeheader()

        # SAVE info in user CSV
        with open(os.path.join(os.getcwd(), Filepaths.folder_RAP_CSVs,
                                   'LPB-RAP_additional_suggested_restricted_areas.csv'), 'a',
                      newline='') as LPB_RAP_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_RAP_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer = csv.writer(LPB_RAP_log_file)
            writer.writerow(['Population_peak_year: ', self.year])
            writer.writerow(['List_of_restricted_LUTs: ', list_of_restricted_LUTs])
            writer.writerow(['Existing_restricted_areas_area: ', maptotal_of_existing_restricted_areas])
            writer.writerow(['Existing_restricted_areas_percentage_of_landscape: ', existing_restricted_areas_percentage_of_landscape])
            writer.writerow(['Suggested_restricted_areas_area:', maptotal_of_suggested_restricted_areas])
            writer.writerow(['Potential_total_area_restricted_areas: ', potential_total_area_restricted_areas])
            writer.writerow(['Potential_total_area_restricted_areas_percentage_of_landscape:', potential_total_restricted_areas_percentage_of_landscape])

        print('\ncalculating potential additional restricted areas done')


        # =================================================================== #

    def calculate_RAP_net_forest_possible_landscape_configuration(self):
        """SH: Calculate the possible new extent of net forest in the landscape."""
        # That is in addition to the existing mplc net forest with LUT23 reforestation

        print('\ncalculating net forest possible configuration ...')

        net_forest_mplc_map = self.dictionary_of_mplc_net_forest_files[self.time_step]

        # the basic map is the mplc map
        net_forest_possible_map = net_forest_mplc_map

        # additionally LUT23 is accounted for
        net_forest_possible_map = ifthenelse(scalar(self.possible_landscape_configuration_map) == scalar(23),
                                                  scalar(1),
                                                  scalar(net_forest_possible_map))

        self.RAP_total_possible_net_forest = int(maptotal(scalar(boolean(scalar(net_forest_possible_map) == scalar(1)))))
        # dictionary_of_net_forest_information['probable_net_forest_area'][self.time_step] = self.total_possible_net_forest,

        self.RAP_net_forest_possible_area_percentage_of_landscape = round(
            float((self.RAP_total_possible_net_forest / self.hundred_percent_area) * 100), 2)
        # dictionary_of_net_forest_information['probable_percentage_of_landscape'][self.time_step] = self.net_forest_possible_area_percentage_of_landscape

        self.RAP_amount_achieved_possible_net_forest = self.RAP_total_possible_net_forest - self.RAP_targeted_total_net_forest_area

        if self.RAP_amount_achieved_possible_net_forest >= 0:
            self.RAP_target_achieved_net_forest = 'YES'
        else:
            self.RAP_target_achieved_net_forest = 'NO'

        print('calculating net forest possible landscape configuration done')

        # =================================================================== #

    def derive_RAP_AGB_and_Carbon(self):
        """ SH: AGB is taken from LPB-mplc probabilistic modelling and combined with the LPB-RAP landscape (based on initial AGB values)."""

        print('\nderiving AGB and Carbon ...')

        # Calculate once the mean values for the potential land use types based on the initial AGB map
        if self.time_step == 1:
            initial_AGB_map = readmap(Filepaths.file_initial_AGB_input)
            initial_mplc_map = self.dictionary_of_mplc_files[self.time_step]

            # RAP agroforestry mean
            agroforestry_AGB_map = ifthen(initial_mplc_map == 4,
                                          scalar(initial_AGB_map))

            self.RAP_AGB_mean_agroforestry = float(maptotal(agroforestry_AGB_map)) / int(maptotal(scalar(boolean(agroforestry_AGB_map))))
            self.RAP_AGB_mean_agroforestry = round(self.RAP_AGB_mean_agroforestry, 3)

            print('RAP agroforestry mean:', self.RAP_AGB_mean_agroforestry)

            # RAP plantation mean (derived from disturbed forest)
            plantation_AGB_map = ifthen(initial_mplc_map == 8,
                                        initial_AGB_map)

            self.RAP_AGB_mean_plantation = float(maptotal(plantation_AGB_map)) / int(maptotal(scalar(boolean(plantation_AGB_map))))
            self.RAP_AGB_mean_plantation = round(self.RAP_AGB_mean_plantation, 3)

            print('RAP plantation mean:', self.RAP_AGB_mean_plantation)

            # RAP reforestation mean (derived from undisturbed forest)
            reforestation_AGB_map = ifthen(initial_mplc_map == 9,
                                           initial_AGB_map)

            self.RAP_AGB_mean_reforestation = float(maptotal(reforestation_AGB_map)) / int(maptotal(scalar(boolean(reforestation_AGB_map))))
            self.RAP_AGB_mean_reforestation = round(self.RAP_AGB_mean_reforestation, 3)

            print('RAP reforestation mean:', self.RAP_AGB_mean_reforestation)

        # Calculate for each time step the potential AGB and tC if it would be grown plots in the RAP landscape
        mplc_AGB_map = self.dictionary_of_mplc_AGB_files[self.time_step]

        RAP_AGB_map = ifthenelse(self.possible_landscape_configuration_map == 21, # RAP agroforestry
                                 scalar(self.RAP_AGB_mean_agroforestry),
                                 scalar(mplc_AGB_map))

        RAP_AGB_map = ifthenelse(self.possible_landscape_configuration_map == 22,  # RAP plantation
                                 scalar(self.RAP_AGB_mean_plantation),
                                 scalar(RAP_AGB_map))

        RAP_AGB_map = ifthenelse(self.possible_landscape_configuration_map == 23,  # RAP reforestation
                                 scalar(self.RAP_AGB_mean_reforestation),
                                 scalar(RAP_AGB_map))

        RAP_AGB_map = ifthenelse(self.possible_landscape_configuration_map == 24,  # other ecosystems (not Forest AGB)
                                 scalar(0),
                                 scalar(RAP_AGB_map))
        # TOTAL
        self.RAP_AGB_maptotal = float(maptotal(RAP_AGB_map))
        self.RAP_AGB_maptotal = round(self.RAP_AGB_maptotal, 3)

        self.RAP_AGB_Carbon = round(self.RAP_AGB_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(), 3)

        # AGROFORESTRY
        RAP_AGB_agroforestry_map = ifthen(self.possible_landscape_configuration_map == 21,
                                          scalar(RAP_AGB_map))

        self.RAP_AGB_agroforestry_mean_maptotal = float(maptotal(RAP_AGB_agroforestry_map))
        self.RAP_AGB_agroforestry_mean_maptotal = round(self.RAP_AGB_agroforestry_mean_maptotal, 3)

        self.RAP_AGB_agroforestry_mean_Carbon = round(self.RAP_AGB_agroforestry_mean_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(),
                                    3)

        # PLANTATION
        RAP_AGB_plantation_map = ifthen(self.possible_landscape_configuration_map == 22,
                                          scalar(RAP_AGB_map))

        self.RAP_AGB_plantation_mean_maptotal = float(maptotal(RAP_AGB_plantation_map))
        self.RAP_AGB_plantation_mean_maptotal = round(self.RAP_AGB_plantation_mean_maptotal, 3)

        self.RAP_AGB_plantation_mean_Carbon = round(
            self.RAP_AGB_plantation_mean_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(),
            3)

        # REFORESTATION
        RAP_AGB_reforestation_map = ifthen(self.possible_landscape_configuration_map == 23,
                                        scalar(RAP_AGB_map))

        self.RAP_AGB_reforestation_mean_maptotal = float(maptotal(RAP_AGB_reforestation_map))
        self.RAP_AGB_reforestation_mean_maptotal = round(self.RAP_AGB_reforestation_mean_maptotal, 3)

        self.RAP_AGB_reforestation_mean_Carbon = round(
            self.RAP_AGB_reforestation_mean_maptotal * Parameters.get_biomass_to_carbon_IPCC_conversion_factor(),
            3)

        print('deriving AGB and Carbon done')

        # =================================================================== #

    def update_RAP_potential_additional_restricted_areas(self):
        """This methods simply updates the following variable for use in the CSV"""

        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
            if self.year > self.population_peak_year:
                self.RAP_potential_additional_restricted_areas = 'likely increasing after population peak year'
        else:
            if self.year > self.peak_demands_year:
                self.RAP_potential_additional_restricted_areas = 'likely increasing after peak demands year'

        # =================================================================== #

    def calculate_fragmentation(self):

        print('\ncalculating fragmentation and p.r.n. further user-defined landstats  ...')

        # get the LUT(s) on which fragmentation and p.r.n. further landstats shall be calculated for a boolean map
        list_of_input_LUTs = Parameters.get_fragmentation_RAP()

        # extract the boolean landscape
        analysis_input_map = boolean(self.null_mask_map)
        for a_LUT in list_of_input_LUTs:
            a_LUT_map = ifthen(scalar(self.possible_landscape_configuration_map) == scalar(a_LUT),
                                   boolean(1))
            analysis_input_map = cover(boolean(a_LUT_map), boolean(analysis_input_map))

        # get all 0 out of the map, otherwise PCraster clump assigns them as class 1
        analysis_input_map = ifthen(boolean(analysis_input_map) == boolean(1),
                                        boolean(analysis_input_map))

        # perform the analysis in PylandStats
        module = 'RAP'
        (self.maximum_number_of_patches, self.total_area_of_patches) = \
            PyLandStats_adapter.analysis(analysis_input_map, self.time_step, module)

        print('calculating fragmentation and p.r.n. further user-defined landstats done')

        # =================================================================== #

        # model stage 2:
    def simulate_potential_habitat_corridors(self):
            """If chosen, here are potential habitat corridors simulated in Circuitscape in Julia."""

        # =================================================================== #

    def calculate_worst_case_scenario_percent_increment_net_forest(self):
        """This method is only executed once to produce the output for user information"""

        if self.time_step == 1:

            # create a new CSV
            with open(os.path.join(os.getcwd(), Filepaths.folder_RAP_CSVs, 'LPB-RAP_targeted_net_forest_increment_for_worst-case.csv'),'w', newline='') as LPB_RAP_log_file:
                writer = csv.writer(LPB_RAP_log_file)
                LPB_writer = csv.writer(LPB_RAP_log_file, delimiter=' ',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # Create a title for the CSV
                LPB_log_file_title = ['LPB-RAP targeted net forest increment for worst-case scenario', Parameters.get_country(), Parameters.get_region(),
                                      Parameters.get_model_baseline_scenario(),
                                      Parameters.get_model_scenario() + ' scenario']
                LPB_writer.writerow(LPB_log_file_title)
                # Create the header
                LPB_writer = csv.writer(LPB_RAP_log_file, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                LPB_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=['initial_simulation_year',
                                                                          'initial_net_forest_area',
                                                                          'initial_net_forest_increment',
                                                                          'initial_total_targeted_net_forest',
                                                                          'worst-case_simulation_start_year',
                                                                          'worst-case_net_forest',
                                                                          'worst_case_targeted_increment_area',
                                                                          'TARGETED_NET_FOREST_INCREMENT_IN_PERCENT'])
                LPB_writer.writeheader()

            # load the required maps and get maptotals:
            initial_net_forest_map = readmap(Filepaths.file_initial_net_forest_input)
            initial_net_forest_map_maptotal = int(maptotal(scalar(initial_net_forest_map)))

            worst_case_scenario_net_forest_input_map = readmap(os.path.join(
                Filepaths.folder_inputs_initial_worst_case_scenario, 'initial_net_forest_simulated_for_worst_case_scenario_input.map'))
            worst_case_scenario_net_forest_input_map_maptotal = int(maptotal(scalar(worst_case_scenario_net_forest_input_map)))

            # get the BAU oder BAU+ increment for the initial simulation year
            initial_increment = Parameters.get_net_forest_percentage_increment_goal()

            # calculate the initial increment total
            increment_area = (initial_net_forest_map_maptotal / 100) * initial_increment
            initial_total_targeted_net_forest_area = math.ceil(initial_net_forest_map_maptotal + increment_area)

            # now calculate the required total percent increment for the worst-case scenario to cover loss by land use at terrestrial surface level and dynamic land use
            worst_case_targeted_increment_area = initial_total_targeted_net_forest_area - worst_case_scenario_net_forest_input_map_maptotal
            worst_case_targeted_increment_percent = round((worst_case_targeted_increment_area * 100 / worst_case_scenario_net_forest_input_map_maptotal), 3)
            print('\nworst-case RAP targeted net forest increment in percent is: ', worst_case_targeted_increment_percent)

            # get the target initial simulation year for worst case
            worst_case_initial_simulation_year = int(Parameters.get_the_initial_simulation_year_for_the_worst_case_scenario())

            # SAVE info in user CSV
            with open(os.path.join(os.getcwd(), Filepaths.folder_RAP_CSVs, 'LPB-RAP_targeted_net_forest_increment_for_worst-case.csv'),'a', newline='') as LPB_RAP_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_RAP_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                LPB_RAP_log_file_data = [self.year,
                                         initial_net_forest_map_maptotal,
                                         initial_increment,
                                         initial_total_targeted_net_forest_area,
                                         worst_case_initial_simulation_year,
                                         worst_case_scenario_net_forest_input_map_maptotal,
                                         worst_case_targeted_increment_area,
                                         worst_case_targeted_increment_percent]
                writer.writerow(LPB_RAP_log_file_data)


        # =================================================================== #

    def export_data_to_LPB_RAP_log_file(self):
        """ SH: Note the according variables in the CSV file for further analysis."""

        # note the data in the LPB-mplc_log-file
        with open(os.path.join(Filepaths.folder_RAP_CSVs, 'LPB-RAP_log-file.csv'),'a', newline='') as LPB_RAP_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_RAP_log_file)
            LPB_RAP_log_file_data = [self.time_step,
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
                                     # LUT01-RAP
                                     self.RAP_allocated_pixels_LUT01,
                                     self.RAP_percentage_of_landscape_LUT01,

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
                                     # LUT02-RAP
                                     self.RAP_allocated_pixels_LUT02,

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
                                     # LUT03-RAP
                                     self.RAP_allocated_pixels_LUT03,

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
                                     #LUT04-RAP
                                     self.RAP_allocated_pixels_LUT04,
                                     self.RAP_percentage_of_landscape_LUT04,

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
                                     # LUT05-RAP
                                     self.RAP_allocated_pixels_LUT05,
                                     self.RAP_percentage_of_landscape_LUT05,

                                      # LUT06
                                      self.allocated_pixels_LUT06,
                                      self.percentage_of_landscape_LUT06,
                                     # LUT06-RAP
                                     self.RAP_allocated_pixels_LUT06,
                                     self.RAP_percentage_of_landscape_LUT06,

                                      # LUT07
                                      self.allocated_pixels_LUT07,
                                      self.percentage_of_landscape_LUT07,
                                     # LUT07-RAP
                                     self.RAP_allocated_pixels_LUT07,
                                     self.RAP_percentage_of_landscape_LUT07,

                                      # LUT08
                                      self.allocated_pixels_LUT08,
                                      self.percentage_of_landscape_LUT08,
                                     # LUT08-RAP
                                     self.RAP_allocated_pixels_LUT08,
                                     self.RAP_percentage_of_landscape_LUT08,

                                      # LUT09
                                      self.allocated_pixels_LUT09,
                                      self.percentage_of_landscape_LUT09,
                                     # LUT09-RAP
                                     self.RAP_allocated_pixels_LUT09,
                                     self.RAP_percentage_of_landscape_LUT09,

                                     # LUT10
                                      self.allocated_pixels_LUT10,
                                      self.percentage_of_landscape_LUT10,
                                     # LUT10-RAP
                                     self.RAP_allocated_pixels_LUT10,
                                     self.RAP_percentage_of_landscape_LUT10,

                                      # LUT11
                                      self.allocated_pixels_LUT11,
                                      self.percentage_of_landscape_LUT11,
                                     # LUT11-RAP
                                     self.RAP_allocated_pixels_LUT11,
                                     self.RAP_percentage_of_landscape_LUT11,

                                      # LUT12
                                      self.allocated_pixels_LUT12,
                                      self.percentage_of_landscape_LUT12,
                                     # LUT12-RAP
                                     self.RAP_allocated_pixels_LUT12,
                                     self.RAP_percentage_of_landscape_LUT12,

                                      # LUT13
                                      self.allocated_pixels_LUT13,
                                      self.percentage_of_landscape_LUT13,
                                     # LUT13-RAP
                                     self.RAP_allocated_pixels_LUT13,
                                     self.RAP_percentage_of_landscape_LUT13,

                                      # LUT14
                                      self.allocated_pixels_LUT14,
                                      self.percentage_of_landscape_LUT14,
                                     # LUT14-RAP
                                     self.RAP_allocated_pixels_LUT14,
                                     self.RAP_percentage_of_landscape_LUT14,

                                      # LUT15
                                      self.allocated_pixels_LUT15,
                                      self.percentage_of_landscape_LUT15,
                                     # LUT15-RAP
                                     self.RAP_allocated_pixels_LUT15,
                                     self.RAP_percentage_of_landscape_LUT15,

                                      # LUT16
                                      self.allocated_pixels_LUT16,
                                      self.percentage_of_landscape_LUT16,
                                     # LUT16-RAP
                                     self.RAP_allocated_pixels_LUT16,
                                     self.RAP_percentage_of_landscape_LUT16,


                                      # LUT17
                                      self.demand_AGB,
                                      self.demand_LUT17_minimum,
                                      self.demand_LUT17_mean,
                                      self.demand_LUT17_maximum,
                                      self.allocated_pixels_LUT17,
                                      self.percentage_of_landscape_LUT17,
                                     # LUT17-RAP
                                     self.RAP_allocated_pixels_LUT17,
                                     self.RAP_percentage_of_landscape_LUT17,

                                      # LUT18
                                      self.allocated_pixels_LUT18,
                                      self.percentage_of_landscape_LUT18,
                                      # LUT18-RAP
                                     self.RAP_allocated_pixels_LUT18,
                                     self.RAP_percentage_of_landscape_LUT18,

                                     # exclusive RAP-LUTs
                                     self.RAP_allocated_pixels_LUT21,
                                     self.RAP_percentage_of_landscape_LUT21,

                                     self.RAP_allocated_pixels_LUT22,
                                     self.RAP_percentage_of_landscape_LUT22,

                                     self.RAP_allocated_pixels_LUT23,
                                     self.RAP_percentage_of_landscape_LUT23,

                                     self.RAP_allocated_pixels_LUT24,
                                     self.RAP_percentage_of_landscape_LUT24,

                                     # model stage 2: LUT25
                                     self.RAP_allocated_pixels_LUT25,
                                     self.RAP_percentage_of_landscape_LUT25,

                                     # RAP total
                                     self.RAP_total,
                                     self.RAP_total_percentage_of_landscape,

                                     # RAP - TARGETED RAP FOREST ACHIEVED?
                                     self.RAP_targeted_total_net_forest_area,
                                     self.RAP_targeted_net_forest_percentage_of_landscape,
                                     self.RAP_total_possible_net_forest,
                                     self.RAP_net_forest_possible_area_percentage_of_landscape,
                                     self.RAP_amount_achieved_possible_net_forest,
                                     self.RAP_target_achieved_net_forest,

                                     # RAP potential minimum restoration / mitigation
                                     self.maptotal_potential_minimum_LUT22,
                                     self.maptotal_potential_minimum_LUT23,
                                     self.maptotal_potential_minimum_LUT24,
                                     self.maptotal_potential_minimum_LUT25, # model stage 2

                                     # RAP - potential for additional restricted areas
                                     self.RAP_potential_additional_restricted_areas,


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

                                     # RAP AGB
                                     # agroforestry
                                     self.RAP_AGB_mean_agroforestry,
                                     self.RAP_AGB_agroforestry_mean_maptotal,
                                     self.RAP_AGB_agroforestry_mean_Carbon,
                                    # plantation
                                     self.RAP_AGB_mean_plantation,
                                     self.RAP_AGB_plantation_mean_maptotal,
                                     self.RAP_AGB_plantation_mean_Carbon,
                                    # reforestation
                                     self.RAP_AGB_mean_reforestation,
                                     self.RAP_AGB_reforestation_mean_maptotal,
                                     self.RAP_AGB_reforestation_mean_Carbon,
                                    # RAP total (mplc plus RAP)
                                     self.RAP_AGB_maptotal,
                                     self.RAP_AGB_Carbon,


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
                                      self.top_crop_1_share_of_LUT_acreage,
                                      self.top_crop_1_yield_minimum,
                                      self.top_crop_1_yield_mean,
                                      self.top_crop_1_yield_maximum,
                                      # 2
                                      self.top_crop_2_share_of_LUT_acreage,
                                      self.top_crop_2_yield_minimum,
                                      self.top_crop_2_yield_mean,
                                      self.top_crop_2_yield_maximum,
                                      # 3
                                      self.top_crop_3_share_of_LUT_acreage,
                                      self.top_crop_3_yield_minimum,
                                      self.top_crop_3_yield_mean,
                                      self.top_crop_3_yield_maximum,
                                      # 4
                                      self.top_crop_4_share_of_LUT_acreage,
                                      self.top_crop_4_yield_minimum,
                                      self.top_crop_4_yield_mean,
                                      self.top_crop_4_yield_maximum,
                                      # 5
                                      self.top_crop_5_share_of_LUT_acreage,
                                      self.top_crop_5_yield_minimum,
                                      self.top_crop_5_yield_mean,
                                      self.top_crop_5_yield_maximum
                                      ]
            writer.writerow(LPB_RAP_log_file_data)
            print('\nadded time step ' + str(self.year) + ' data to LPB-RAP_log-file')

        if self.time_step == Parameters.get_number_of_time_steps():
            with open(os.path.join(Filepaths.folder_RAP_CSVs, 'LPB-RAP_log-file.csv'), 'a', newline='') as LPB_RAP_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_RAP_log_file)
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
                writer.writerow(['Variables per time step: ' + str(len(LPB_RAP_log_file_data))])
                writer.writerow(['Entries for ' + str(Parameters.get_number_of_time_steps()) + ' time steps in total: ' + str(Parameters.get_number_of_time_steps() * len(LPB_RAP_log_file_data))])
                writer.writerow([])
                writer.writerow(['Aggregation in LPB-mplc based on LPB-basic samples: ' + str(self.original_number_of_samples)])
                if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
                    writer.writerow([])
                    writer.writerow(['Simulation of most probable landscape configuration conducted WITH additional corrective allocation to simulate maximum anthropogenic impact.'])
                elif Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == False:
                    writer.writerow([])
                    writer.writerow(['Simulation of most probable landscape configuration conducted WITHOUT additional corrective allocation to simulate maximum anthropogenic impact.'])
                writer.writerow([])
                writer.writerow(['RAP (Restoration Area Potentials) are not to be viewed as a sequence: each simulated year assumes, that no restoration has been implemented until this point! They denote individual entry points to FLR or possible mitigation measures!'])
                if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
                    writer.writerow([])
                    writer.writerow(['Population peak year: ' + str(self.population_peak_year)])
                    writer.writerow(['Peak demands year: ' + str(self.peak_demands_year)])

    def export_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        output_files_data = {
            'RAP_land_use_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.RAP_allocated_pixels_LUT01, self.RAP_percentage_of_landscape_LUT01],
                ['LUT02', None, None],
                ['LUT03', None, None],
                ['LUT04', self.RAP_allocated_pixels_LUT04, self.RAP_percentage_of_landscape_LUT04],
                ['LUT05', self.RAP_allocated_pixels_LUT05, self.RAP_percentage_of_landscape_LUT05],
                ['LUT06', self.RAP_allocated_pixels_LUT06, self.RAP_percentage_of_landscape_LUT06],
                ['LUT07', self.RAP_allocated_pixels_LUT07, self.RAP_percentage_of_landscape_LUT07],
                ['LUT08', self.RAP_allocated_pixels_LUT08, self.RAP_percentage_of_landscape_LUT08],
                ['LUT09', self.RAP_allocated_pixels_LUT09, self.RAP_percentage_of_landscape_LUT09],
                ['LUT10', self.RAP_allocated_pixels_LUT10, self.RAP_percentage_of_landscape_LUT10],
                ['LUT11', self.RAP_allocated_pixels_LUT11, self.RAP_percentage_of_landscape_LUT11],
                ['LUT12', self.RAP_allocated_pixels_LUT12, self.RAP_percentage_of_landscape_LUT12],
                ['LUT13', self.RAP_allocated_pixels_LUT13, self.RAP_percentage_of_landscape_LUT13],
                ['LUT14', self.RAP_allocated_pixels_LUT14, self.RAP_percentage_of_landscape_LUT14],
                ['LUT15', self.RAP_allocated_pixels_LUT15, self.RAP_percentage_of_landscape_LUT15],
                ['LUT16', self.RAP_allocated_pixels_LUT16, self.RAP_percentage_of_landscape_LUT16],
                ['LUT17', self.RAP_allocated_pixels_LUT17, self.RAP_percentage_of_landscape_LUT17],
                ['LUT18', self.RAP_allocated_pixels_LUT18, self.RAP_percentage_of_landscape_LUT18],
                ['LUT21', self.RAP_allocated_pixels_LUT21, self.RAP_percentage_of_landscape_LUT21],
                ['LUT22', self.RAP_allocated_pixels_LUT22, self.RAP_percentage_of_landscape_LUT22],
                ['LUT23', self.RAP_allocated_pixels_LUT23, self.RAP_percentage_of_landscape_LUT23],
                ['LUT24', self.RAP_allocated_pixels_LUT24, self.RAP_percentage_of_landscape_LUT24],
                ['LUT25', self.RAP_allocated_pixels_LUT25, self.RAP_percentage_of_landscape_LUT25]
            ],
            'RAP_total_' + str(Parameters.get_model_scenario()): [
                [self.RAP_total, self.RAP_total_percentage_of_landscape],
            ],
            'RAP_minimum_mitigation_' + str(Parameters.get_model_scenario()): [
                ['LUT22', self.maptotal_potential_minimum_LUT22],
                ['LUT23', self.maptotal_potential_minimum_LUT23],
                ['LUT24', self.maptotal_potential_minimum_LUT24],
                ['LUT25', self.maptotal_potential_minimum_LUT25]
            ],
            'RAP_potential_AGB_Carbon_' + str(Parameters.get_model_scenario()): [
                ['LUT21', self.RAP_AGB_mean_agroforestry, self.RAP_AGB_agroforestry_mean_maptotal, self.RAP_AGB_agroforestry_mean_Carbon],
                ['LUT22', self.RAP_AGB_mean_plantation, self.RAP_AGB_plantation_mean_maptotal, self.RAP_AGB_plantation_mean_Carbon],
                ['LUT23', self.RAP_AGB_mean_reforestation, self.RAP_AGB_reforestation_mean_maptotal, self.RAP_AGB_reforestation_mean_Carbon]
            ],
            'RAP_potential_total_AGB_Carbon_' + str(Parameters.get_model_scenario()): [
                [self.RAP_AGB_maptotal, self.RAP_AGB_Carbon]
            ],
            'RAP_targeted_net_forest_' + str(Parameters.get_model_scenario()): [
                ['targeted_net_forest', self.RAP_targeted_total_net_forest_area, self.RAP_targeted_net_forest_percentage_of_landscape],
                ['total_possible_net_forest', self.RAP_total_possible_net_forest, self.RAP_net_forest_possible_area_percentage_of_landscape]
            ]
        }

        if Parameters.get_fragmentation_mplc_RAP_analysis_choice() == True:
            fragmentation_output_dict = {
                'RAP_fragmentation_' + str(Parameters.get_model_scenario()): [
                    ['maximum_patch_number', self.maximum_number_of_patches],
                    ['total_area_of_patches', self.total_area_of_patches]
                ]
            }
            output_files_data.update(fragmentation_output_dict)

        for output_file, column_headers in self.tidy_output_files_definitions.items():

            with open(os.path.join(Filepaths.folder_RAP_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file)

                for data_of_row in output_files_data[output_file]:
                    # add time step
                    data_of_row.insert(0, self.time_step)

                    assert len(column_headers) == len(
                        data_of_row), f'headers: {column_headers}, row data: {data_of_row}'

                    csv_file_writer.writerow(data_of_row)

    def postdynamic(self):
        print('\n>>> running postdynamic ...')

        print('\nno statistics to be calculated')

        # make all the movies
        print('\nmaking 3 movies for RAP - each for', Parameters.get_number_of_time_steps(), 'time steps ...')

        movies_start_time = datetime.now()

        # clean up the dictionary for windows with ast

        # possible land use

        # 1
        # TEST FOR WINDOWS APPLICATION
        print('In LULCC_RAP.py::')
        print('RAP_population_and_LUTs_shares_dictionary:')
        print(RAP_population_and_LUTs_shares_dictionary)
        print('json.dumps(RAP_population_and_LUTs_shares_dictionary:)')
        print(json.dumps(RAP_population_and_LUTs_shares_dictionary))
        print('\n making RAP_movie_01 of land use for the possible landscape configuration ...')
        command = "python RAP_movie_01_LULCC_possible_landscape_configuration.py %r" % json.dumps(RAP_population_and_LUTs_shares_dictionary) #
        # subprocess.run(command.split(), check=True)
        os.system(command)
        print('making movie of land use for the possible landscape configuration done')

        # 2
        print('\nmaking RAP_movie_02 of land use for the possible landscape configuration VIRIDIS ACCESSIBLE...')
        command = "python RAP_movie_02_LULCC_possible_landscape_configuration_VA.py %r" % json.dumps(RAP_population_and_LUTs_shares_dictionary)  #
        # subprocess.run(command.split(), check=True)
        os.system(command)
        print('making movie of land use for the possible landscape configuration VIRDIS ACCESSIBLE done')

        # 3
        print('\nmaking RAP_movie_03 of potential minimum restoration area VIRIDIS ACCESSIBLE...')
        command = "python RAP_movie_03_LULCC_potential_minimum_restoration_VA.py %r" % json.dumps(RAP_potential_minimum_restoration_dictionary)
        # subprocess.run(command.split(), check=True)
        os.system(command)
        print('making movie of potential minimum restoration area VIRIDIS ACCESSIBLE done')

        movies_end_time = datetime.now()
        print('making movies done')
        print('time elapsed for movie production: {}'.format(movies_end_time - movies_start_time))

        # ONLY 1 SLIDE GIFs for static used data
        print('\nONE SLIDE GIFs ...')

        # 1
        print('\n1. making one slide GIF of targeted net forest ...')
        command = "python RAP_visualization_01_targeted_net_forest_VA.py %r" % json.dumps(targeted_net_forest_dictionary)
        # subprocess.run(command.split(), check=True)
        os.system(command)
        print('making one slide GIF of targeted net forest done')

        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            # makes only sense with policies in place
            # 2
            dictionary_of_restricted_areas = {
                'list_restricted_areas': list_restricted_areas,
                'list_of_LUTs_for_definition_of_potential_restricted_areas': list_of_LUTs_for_definition_of_potential_restricted_areas
            }
            print('\n2. making one slide GIF of existing and potential restricted areas VIRIDIS ACCESSIBLE...')
            command = "python RAP_visualization_02_existing_and_suggested_restricted_areas_VA.py  %r" % json.dumps(dictionary_of_restricted_areas)
            #subprocess.run(command.split(), check=True)
            os.system(command)
            print('making one slide GIF of existing and potential restricted areas VIRIDIS ACCESSIBLE done')

        print('\nONE SLIDE GIFs done')


        print('\nrunning postdynamic done')
        self.end_time = datetime.now()
        print('time elapsed for LPB-RAP execution: {}'.format(self.end_time - self.start_time))


###################################################################################################


number_of_time_steps = Parameters.get_number_of_time_steps()
my_model = PossibleLandscapeConfiguration()
dynamic_model = DynamicFramework(my_model, number_of_time_steps)
dynamic_model.run()
my_model.postdynamic()

