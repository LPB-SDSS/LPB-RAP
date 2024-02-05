#!--columntable

"""LAFORET-PLUC-BE-RAP/SFM/OC
Sonja Holler (SH, RAP), Melvin Lippe (ML, OC) and Daniel Kuebler (DK, SFM), 2021/Q2 - 2023/Q3
AIM: LOCAL IMPACT ASSESSMENT OF SMALLHOLDER LAND USE DECISIONS IN A REGIONAL CONTEXT
(LAND USE CHANGE AND ACCORDING RESTORATION AND SUSTAINABLE FOREST MANAGEMENT OPPORTUNITIES AND OPPORTUNITY COSTS)
BASIC ASSUMPTION: anthropogenic need is superior and must be satisfied locally per time step as long as plausible.
(Re-)written according to PEP 8 descriptive snake style (some violations due to readability) and "child of 10" rule,
modified original model.

Developed in Python 3.9+ and PCRaster 4.3.1+ and PyCharm CE 2021.2+

model stage 1 includes up to now:
Filepaths.py by SH
Formulas.py by SH&DK
LULC_landcover_to_landuse_correction_step.py by SH
nested input and output folder structure by SH
regional theme and additional maps by SH
descriptive snake style by SH
Python 3.9 format by SH&DK
supra-structure by DK&SH
spatially explicit linear population development by SH
succession by SH
singular declared abandoned and deforested LUTs by SH
footprint approach and according faster def _add and def _remove methods by SH
cascade allocation in def _add according to scenario
smallholder share of population by SH
demand according to population development or static (plantations) by SH
built-up rule of three approach according to population development
accompanying maps prior and posterior time step land use change calculations by SH, e.g.:
- settlements development
- anthropogenic impact buffer
- plantation age, plantation rotation period
- succession age, succession
- AGB development
- forest degradation and regeneration
- forest land use conflict in restricted areas also in worst case
slope depended and restricted areas masks to derive conflict and development of difficult terrain
filed multiprocessing

completed LULCC_mplc.py by DK&SH

completed RAP.py by SH

model stage 3 preparations include:
- incorporation of internal/external, deterministic or stochastic, user-defined time series in the footprint and yield_units approach
- incorporation of potential yield maps per LUT and climate period for LUTs 2,3 and 4


Based on:

Land use change model of Mozambique
Judith Verstegen, 2011-01-27
https://github.com/JudithVerstegen/PLUC_Mozambique/blob/master/model/LU_Moz.py """

# Changes to PLUC for LPB-RAP/SFM model stage 1 made by:
# JV: original commented/out-commented by Judith Verstegen
# SH: commented/out-commented by Sonja Holler
# ML: commented/out-commented by Melvin Lippe
# DK: commented/out-commented by Daniel Kuebler

#######################################
# report on to be probabilistic handled outputs is limited to 4 characters, due to the -ave suffix of the Monte Carlo method
# report on deterministic output is reported with up to 8 charcters and without sample folders since it can be overwritten from each sample, only the timestep suffix is needed afterwards

# all spatial files are indicated by the "_map" suffix, files lacking this suffix denote values
# demand in AGB Mg and AGB in Mg are rounded to 3 digits: round(X, 3)
# demand and population is rounded up to full values: math.ceil()
# area outputs are given with 2 digits: round(X, 2)
# percentage is given with 2 digits: round(X, 2)
# distances are given in meter

#######################################
# SH: LPB alternation - IMPORT
# SH: import os, csv, random, platform, psutil, builtins, datetime, itemgetter, Filepaths, Formulas, SFM
import gc
import sys, os
import csv
import builtins
import platform

import linecache
import tracemalloc

import pcraster
import psutil
import subprocess
import numpy
import multiprocessing
import json
from datetime import datetime
from operator import itemgetter
from pcraster import *
from pcraster.framework import *
from pcraster.multicore import *
from pcraster.multicore._operations import *
from technical_logging_module import logger
import Filepaths
import Parameters
import Formulas
import generate_PCRaster_conform_output_name
from generate_PCRaster_conform_timeseries import TssGenerator

###################################################################################################
# For testing, debugging and submission: set random seed to make the results consistent (1)
# set random seed 0 = every time new results
seed = int(Parameters.get_random_seed())
setrandomseed(seed)

###################################################################################################
# tracing potential memory leak
def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    logger.debug("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        logger.debug("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            logger.debug('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        logger.debug("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    logger.debug("Total allocated size: %.1f KiB" % (total / 1024))

tracemalloc.start()

####
# test with Python garbage collector
gc.enable()

###################################################################################################
# SH&DK: LPB alternation - initiate multicore use on the provided operating system

# https://pcraster.geo.uu.nl/pcraster/4.3.1/documentation/pcraster_project/multicore.html?highlight=cores

def set_number_of_worker_threads():
    logger.info('\nadapting CPU usage to user requirements initiated ...')

    logger.info(f'current number of PCRaster worker threads: {pcraster.multicore.nr_worker_threads()}')
    nr_threads = int(Parameters.get_number_of_threads_to_be_used()) # convert the function into an int object
    pcraster.multicore.set_nr_worker_threads(nr_threads)
    logger.info(f'new number of PCRaster worker threads: {pcraster.multicore.nr_worker_threads()}')

    logger.info('adapting CPU usage to user requirements done')

###################################################################################################
# SH: LPB alternation - initiate paths to input files and output folders

def get_filepaths():
    # is already imported, only print of user information
    print('\nfiling of input and output paths and folders initiated ...')
    print('filing of input and output paths and folders done')

###################################################################################################
# SH: Calculate sample number leaning on 'Latin Hypercube sampling' (minimum sample number to depict the maximum range of possible landscape configurations)
# if calculating with the deterministic demand approach, in that case, the uncertainty of human behavior is depicted by the range of distances where
# smallholder allocate the agricultural land use types.

number_of_samples_set = None

def get_required_number_of_samples():
    global number_of_samples_set
    print('\ndrawing required sample number initiated ...')
    # if the Parameters value is set for probabilistic modelling with a random number of samples or to a deterministic setting with 1 use this value
    if Parameters.get_number_of_samples() is not None:
        number_of_required_samples = Parameters.get_number_of_samples()
        print('set sample number is:', number_of_required_samples)
        number_of_samples_set = number_of_required_samples
    else:
        # first get the distance ranges to be depicted from the dictionary in Parameters.py:
        regional_distance_values_for_agricultural_land_use_dictionary = Parameters.get_regional_distance_values_for_agricultural_land_use_dictionary()

        # get the minimum values
        LUT02_minimum_distance = regional_distance_values_for_agricultural_land_use_dictionary[2][1]
        LUT03_minimum_distance = regional_distance_values_for_agricultural_land_use_dictionary[3][1]
        LUT04_minimum_distance = regional_distance_values_for_agricultural_land_use_dictionary[4][1]

        # get the minimum within this range
        minimum_distance = min(LUT02_minimum_distance, LUT03_minimum_distance, LUT04_minimum_distance)

        # get the maximum values
        LUT02_maximum_distance = regional_distance_values_for_agricultural_land_use_dictionary[2][2]
        LUT03_maximum_distance = regional_distance_values_for_agricultural_land_use_dictionary[3][2]
        LUT04_maximum_distance = regional_distance_values_for_agricultural_land_use_dictionary[4][2]

        # get the maximum within this range
        maximum_distance = max(LUT02_maximum_distance, LUT03_maximum_distance, LUT04_maximum_distance)

        # get the range to be covered
        distance_to_be_covered = maximum_distance - minimum_distance

        # devide it by the available cell length
        cell_range = distance_to_be_covered / Parameters.get_cell_length_in_m()

        # round up to a full sample number
        number_of_required_samples = math.ceil(cell_range)
        print('set required sample number is:', number_of_required_samples)
        number_of_samples_set = number_of_required_samples

        return number_of_samples_set

###################################################################################################
# SH: LPB alternation
# this dictionary is used to control the TB output of the model in a probabilistic run with high sample numbers.
# Options set to false in Parameters.py will decrease needed hard drive space but also analytical output in LPB-mplc.

probabilistic_output_options_dictionary = Parameters.get_LPB_basic_probabilistic_output_options()

###################################################################################################
# SH: LPB alternation
# this dictionary is needed to calculate mean area of forest for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_forest = {}

def initialize_global_dictionary_for_forest():
    global dictionary_of_samples_dictionaries_values_forest
    dictionary_of_samples_dictionaries_values_forest = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_forest[a_sample] = {}
        for a_time_step in range_of_time_steps:
            dictionary_of_samples_dictionaries_values_forest[a_sample][a_time_step] = 0

# this dictionary is needed to calculate max area of forest conversion for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_forest_conversion = {}

def initialize_global_dictionary_for_forest_conversion():
    global dictionary_of_samples_dictionaries_values_forest_conversion
    dictionary_of_samples_dictionaries_values_forest_conversion = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_forest_conversion[a_sample] = {}
        for a_time_step in range_of_time_steps:
            dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step] = {}
            for a_LUT in ['total', 'LUT01', 'LUT02', 'LUT03', 'LUT04', 'LUT05']:
                dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][a_LUT] = 0

# SH: LPB alternation
# this dictionary is needed to calculate mean, min und max area with built-up for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_LUT01 = {}

def initialize_global_dictionary_for_LUT01():
    global dictionary_of_samples_dictionaries_values_LUT01
    dictionary_of_samples_dictionaries_values_LUT01 = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_LUT01[a_sample] = {}

# this dictionary is needed to calculate mean, min und max area of plantations for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_LUT05 = {}

def initialize_global_dictionary_for_LUT05():
    global dictionary_of_samples_dictionaries_values_LUT05
    dictionary_of_samples_dictionaries_values_LUT05 = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_LUT05[a_sample] = {}

# this dictionary is needed to calculate mean area of abanoned types for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_abandoned_types = {}

def initialize_global_dictionary_for_abandoned_types():
    global dictionary_of_samples_dictionaries_values_abandoned_types
    dictionary_of_samples_dictionaries_values_abandoned_types = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_abandoned_types[a_sample] = {}
        for a_time_step in range_of_time_steps:
            dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step] = {}
            for a_LUT in ['LUT14', 'LUT15', 'LUT16', 'LUT18']:
                dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step][a_LUT] = 0

# this dictionary is needed to calculate mean area of abanoned types for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_agricultural_types = {}

def initialize_global_dictionary_for_agricultural_types():
    global dictionary_of_samples_dictionaries_values_agricultural_types
    dictionary_of_samples_dictionaries_values_agricultural_types = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_agricultural_types[a_sample] = {}
        for a_time_step in range_of_time_steps:
            dictionary_of_samples_dictionaries_values_agricultural_types[a_sample][a_time_step] = {}
            for a_LUT in ['LUT02', 'LUT03', 'LUT04']:
                dictionary_of_samples_dictionaries_values_agricultural_types[a_sample][a_time_step][a_LUT] = 0

# this dictionary is needed to calculate mean, min und max area deforested for the run from the samples.
# It ends in an additional csv
dictionary_of_samples_dictionaries_values_LUT17 = {}

def initialize_global_dictionary_for_LUT17():
    global dictionary_of_samples_dictionaries_values_LUT17
    dictionary_of_samples_dictionaries_values_LUT17 = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_LUT17[a_sample] = {}


# this dictionary tracks for external time series the mean demand and mean unallocated demand per time step:
dictionary_of_samples_dictionaries_values_unallocated_demands = {}
def initialize_global_dictionary_of_unallocated_demands():
    global dictionary_of_samples_dictionaries_values_unallocated_demands
    dictionary_of_samples_dictionaries_values_unallocated_demands = {}

    range_of_samples = range(1, number_of_samples_set + 1)
    range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
    for a_sample in range_of_samples:
        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample] = {}
        for a_time_step in range_of_time_steps:
            dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step] = {}
            for a_category in ['demand', 'unallocated_demand']:
                dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category] = {}
                for a_demand_type in ['LUT02', 'LUT03', 'LUT04', 'LUT05', 'AGB']:
                    dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category][a_demand_type] = 0



###################################################################################################
# SH: LPB alternation - user information model settings for this run

def give_user_information_model_settings():
    print('\nMODEL SETTINGS SUMMARY:')

    year = Parameters.get_initial_simulation_year()
    logger.info(f'\ninitial simulation year is:  {year}')
    time_steps = Parameters.get_number_of_time_steps()
    logger.info(f'number of time steps is: {time_steps}')
    last_simulated_year = year + time_steps - 1
    logger.info(f'last simulated year will be: {last_simulated_year}')
    logger.info(f'number of samples is: {number_of_samples_set}')

    allocation_order = Parameters.get_active_land_use_types_list()
    print('\nThe model is set to the following ALLOCATION ORDER for this run: ', allocation_order)

    print('\nThe model is set to the following SYSTEMIC CHOICES for this run:')
    correction_step = Parameters.get_presimulation_correction_step_needed()
    print('modelling with CORRECTION STEP to adjust from Land Cover to Land Use: ', correction_step)
    streets = Parameters.get_streets_input_decision_for_calculation_of_built_up()
    print('modelling with STREETS to calculate built up: ', streets)
    only_one_new_settlement_per_year, required_households_for_a_new_settlement_threshold = Parameters.get_dynamic_settlements_simulation_decision()
    print('modelling dynamic SETTLEMENTS with only one new per year: ', only_one_new_settlement_per_year)
    print('p.r.n. modelling dynamic SETTLEMENTS with required households number of: ', required_households_for_a_new_settlement_threshold)
    deforestation_before_conversion = Parameters.get_order_of_forest_deforestation_and_conversion()
    print('modelling DEFORESTATION BEFORE CONVERSION: ', deforestation_before_conversion)
    AGB_increment = Parameters.get_annual_AGB_increment_simulation_decision()
    print('modelling AGB INCREMENT as: ', AGB_increment)
    overall_simulation = Parameters.demand_configuration['overall_method']
    print('modelling OVERALL METHOD as a basis of dynamic simulation: ', overall_simulation)
    anthropogenic_impact = Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision()
    print('p.r.n. modelling MAXIMUM ANTHROPOGENIC IMPACT in mplc module: ', anthropogenic_impact)

    logger.info(f'\nThe model is set to the following OUTPUT OPTIONS for additional probabilistic files for this run: ')
    output_deforested = probabilistic_output_options_dictionary['deforested_net_forest_map']
    logger.info(f'net forest deforested map output is produced: {output_deforested}')
    output_conflict = probabilistic_output_options_dictionary['conflict_maps']
    logger.info(f'forest land use conflict and land use conflict maps output are produced: {output_conflict}')
    output_AGB = probabilistic_output_options_dictionary['AGB_map']
    logger.info(f'AGB map output is produced: {output_AGB}')
    output_net_forest = probabilistic_output_options_dictionary['net_forest_map']
    logger.info(f'net forest output is produced:  {output_net_forest}')
    output_degradation_regeneration = probabilistic_output_options_dictionary['degradation_regeneration_maps']
    logger.info(f'forest degradation/regeneration output is produced: {output_degradation_regeneration}')


###################################################################################################
# SH: LPB alternation - run pre Monte Carlo land cover to land use correction step if need be

def get_pre_simulation_map_correction_step_decision():
    print('\ndoes the input map need correction before probabilistic modelling?')
    if Parameters.get_presimulation_correction_step_needed() is True:
        print('##############################################################')
        print('YES, correction initialized ...')
        command = "python LULC_landcover_to_landuse_correction_step.py"
        subprocess.run(command.split(), check=True)
        # os.system(command)
        print('\ncorrection executed, new simulated initial LULC map to be used for simulation')
        print('##############################################################')
    else:
        print('NO, initial LULC map will be used for simulation')
        pass

###################################################################################################
# SH: LPB alternation - initiate log files for LPB basic

def initiate_LPB_log_file_csv():
    with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic_log-file.csv')), 'w', newline='') as LPB_log_file:
        LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Create a title for the CSV
        LPB_log_file_title = ['LPB-basic log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                          Parameters.get_model_scenario() + ' scenario']
        LPB_writer.writerow(LPB_log_file_title)
        # Create the header
        LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if Parameters.demand_configuration['overall_method'] == 'footprint':
            smallholder_share = 'with a share of ' + str(Parameters.get_regional_share_smallholders_of_population()) + ' % population that is smallholder',
            if Parameters.demand_configuration['internal_or_external'] == 'external':
                if 'smallholder_share' in Parameters.demand_configuration['list_columns_for_tss']:
                    smallholder_share = 'smallholder population based on external time series'
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['YEAR',
                                                              'population',
                                                              'settlements',
                                                              smallholder_share,
                                                              Parameters.get_pixel_size() + ' demand ' + Parameters.LUT01,
                                                              Parameters.get_pixel_size() + ' demand ' + Parameters.LUT02,
                                                              Parameters.get_pixel_size() + ' demand ' + Parameters.LUT03,
                                                              Parameters.get_pixel_size() + ' demand ' + Parameters.LUT04,
                                                              Parameters.get_pixel_size() + ' demand ' + Parameters.LUT05,
                                                              'demand AGB in Mg'])
        if Parameters.demand_configuration['overall_method'] == 'yield_units':
            smallholder_share = str('smallholder population is irrelevant in this approach')
            demand_unit_LUT02 = str(Parameters.get_pixel_size() + ' demand ' + Parameters.LUT02)
            demand_unit_LUT03 = str(Parameters.get_pixel_size() + ' demand ' + Parameters.LUT03)
            demand_unit_LUT04 = str(Parameters.get_pixel_size() + ' demand ' + Parameters.LUT04)
            if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                if Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
                    demand_unit_LUT02 = str('deterministic YIELD UNITS demand ' + Parameters.LUT02)
                else:
                    demand_unit_LUT02 = str('stochastic YIELD UNITS demand ' + Parameters.LUT02 + ' 1st sample')
            if 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                if Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
                    demand_unit_LUT03 = str('deterministic YIELD UNITS demand ' + Parameters.LUT03)
                else:
                    demand_unit_LUT03 = str('stochastic YIELD UNITS demand ' + Parameters.LUT03 + ' 1st sample')
            if 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                if Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
                    demand_unit_LUT04 = str('deterministic YIELD UNITS demand ' + Parameters.LUT04)
                else:
                    demand_unit_LUT04 = str('stochastic YIELD UNITS demand ' + Parameters.LUT04 + ' 1st sample')
            demand_simulation_type_LUT05 = str(Parameters.get_pixel_size() + ' demand ' + Parameters.LUT05)
            demand_simulation_type_AGB = str('demand AGB in Mg')
            if Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
                if 5 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_simulation_type_LUT05 = str('stochastic ' + Parameters.get_pixel_size() + ' demand ' + Parameters.LUT05 + ' 1st sample')
                if 'regional_AGB_demand_per_population_total' in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_simulation_type_AGB = str('stochastic demand AGB in Mg 1st sample')
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['YEAR',
                                                                  'population',
                                                                  'settlements',
                                                                  smallholder_share,
                                                                  Parameters.get_pixel_size() + ' demand ' + Parameters.LUT01,
                                                                  demand_unit_LUT02,
                                                                  demand_unit_LUT03,
                                                                  demand_unit_LUT04,
                                                                  demand_simulation_type_LUT05,
                                                                  demand_simulation_type_AGB])





        LPB_writer.writeheader()
        # data is filled at the end of dynamic for each timestep once (only for the first sample, since this data is deterministic
        # and with the final population peak information in the last sample of the last time step)
        print('\nfiling LPB-basic_log-file.csv initiated ...')

###################################################################################################
# SH: LPB alternation - initiate nan values log files for LPB basic
# this tracks nan values within the cascading allocation in _add (no more suitable cells available)

def initiate_LPB_nan_log_file_csv():
    with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-nan_log-file.csv')), 'w', newline='') as LPB_log_file:
        LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Create a title for the CSV
        LPB_log_file_title = ['LPB-basic-nan log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                          Parameters.get_model_scenario() + ' scenario']
        LPB_writer.writerow(LPB_log_file_title)
        # Create the header
        LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['Sample', 'Time_step', 'Year', 'LUT', 'Degree_of_Limitation'])
        LPB_writer.writeheader()
        # data is filled in the _add procedure if nan values occur (meaning no more cells available in the suitability map)
        print('\nfiling LPB-basic-nan_log-file.csv initiated ...')

###################################################################################################
# SH: LPB alternation - initiate deforestation nan values log files for LPB basic
# this tracks nan values within the cascading allocation in _add (no more suitable cells available)

def initiate_LPB_deforestation_nan_log_file_csv():
    with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-deforestation-nan_log-file.csv')), 'w', newline='') as LPB_log_file:
        LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Create a title for the CSV
        LPB_log_file_title = ['LPB-basic-deforestation-nan log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                          Parameters.get_model_scenario() + ' scenario']
        LPB_writer.writerow(LPB_log_file_title)
        # Create the header
        LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['Sample', 'Time_step', 'Year', 'Factor'])
        LPB_writer.writeheader()
        # data is filled in the _add procedure if nan values occur (meaning no more cells available in the suitability map)
        print('\nfiling LPB-basic-deforestation-nan_log-file.csv initiated ...')

###################################################################################################
# SH if yield units are simulated, this csv tracks unallocated demand

def initiate_LPB_basic_unallocated_demand_yield_units_log_file():
    with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-unallocated-demand-yield-units_log-file.csv')), 'w', newline='') as LPB_log_file:
        LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Create a title for the CSV
        LPB_log_file_title = ['LPB-basic-unallocated-demand-yield-units_log-file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                          Parameters.get_model_scenario() + ' scenario']
        LPB_writer.writerow(LPB_log_file_title)
        # Create the header
        LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['Sample', 'Time_step', 'Year', 'LUT', 'Unallocated_demand_in_yield_units'])
        LPB_writer.writeheader()
        # data is filled in the _add procedure if nan values occur (meaning no more cells available in the suitability map)
        print('\nfiling LPB-basic-unallocated-demand-yield-units_log-file.csv initiated ...')


###################################################################################################
# SH: LPB alternation - delete the false PCRaster generated sample files in the working directory
# THIS METHODS RUNS LAST IN THE MODEL RUN

def delete_false_sample_folders():

    print('\n###################################################################')

    print('\nremoving false generated PCRaster sample folders in current working directory:')
    # get the current working directory
    current_working_directory = os.getcwd()

    # get the rang of false sample folders to delete
    range_of_false_sample_folders_to_delete = range(1, number_of_samples_set + 1)

    # delete the false folders from the current working directory
    for a_false_sample_folder in range_of_false_sample_folders_to_delete:
        # built the path to the empty folder
        a_folder_path = os.path.join(current_working_directory, str(a_false_sample_folder))
        try:
            # try to remove it
            os.rmdir(str(a_folder_path))
            print('deleted false sample folder:', a_folder_path)
        except OSError as e:
            print("Error: %s : %s" % (a_folder_path, e.strerror))

    print('\n###################################################################')

###################################################################################################

class LandUseType:
    def __init__(self, type_number, environment_map, related_types_list, suitability_factors_list,
                 weights_list, variables_dictionary, noise, null_mask_map, window_length_realization, initial_environment_map,
                 LUT02_sampled_distance_for_this_sample, LUT03_sampled_distance_for_this_sample, LUT04_sampled_distance_for_this_sample,
                 static_areas_on_which_no_allocation_occurs_map,
                 static_LUTs_on_which_no_allocation_occurs_list,
                 difficult_terrain_slope_restriction_dictionary,
                 slope_map,external_demands_generated_tss_dictionary, climate_period_inputs_dictionary):
        """JV: Create LandUseType object that represents a class on the land use map.

        SH: LPB alternation
        Takes eight instead of ten arguments:
        type_number -- class number of the land use type on the land use map
        environment -- global land use map that will evolve
        related_types_list -- list with land use type next to which growth is preferred
        suitability_factors_list -- list of suitability factors the type takes into account
        weights_list -- list of relative weights for those factors
        variables_dictionary -- dictionary in which inputs for factors are found
        noise -- very small random noise to ensure cells can't get same suitability - SH: CHANGE THIS
        null_mask_map -- map with value 0 for study area and No Data outside
        """

        # ORIGINAL PLUC VARIABLES:
        self.type_number = type_number
        self.environment_map = environment_map
        self.related_types_list = related_types_list
        self.suitability_factors_list = suitability_factors_list
        self.weights_list = weights_list
        self.variables_dictionary = variables_dictionary
        self.null_mask_map = null_mask_map
        self.stochastic_distance = Parameters.get_stochastic_distance()
        self.stochastic_window = Parameters.get_stochastic_window()
        self.window_length_realization = window_length_realization
        self.small_noise_map = uniform(1) / 1000000
        self.to_square_meters = Parameters.get_conversion_unit()

        # Relocated PLUC Variables
        self.static_areas_on_which_no_allocation_occurs_map = static_areas_on_which_no_allocation_occurs_map
        self.static_LUTs_on_which_no_allocation_occurs_list = static_LUTs_on_which_no_allocation_occurs_list
        self.difficult_terrain_slope_restriction_dictionary = difficult_terrain_slope_restriction_dictionary
        self.slope_map = slope_map

        # LPB ADDED VARIABLES:
        # management variables
        self.time_step = None
        self.current_sample_number = None
        self.year = None

        # variation of agricultural land use types maximum distance from settlement per sample (calculated in LandUseChangeModel initial)
        self.LUT02_sampled_distance_for_this_sample = LUT02_sampled_distance_for_this_sample
        self.LUT03_sampled_distance_for_this_sample = LUT03_sampled_distance_for_this_sample
        self.LUT04_sampled_distance_for_this_sample = LUT04_sampled_distance_for_this_sample

        # self.external_demands_generated_tss_dictionary, required yield_units approach maximum yield tss information
        self.external_demands_generated_tss_dictionary = external_demands_generated_tss_dictionary

        # self.climate_period_inputs_dictionary, required for yield_units approach potential yields per LUT per climate period
        self.climate_period_inputs_dictionary = climate_period_inputs_dictionary

        # plantations #
        self.new_plantations_map = None

        static_restricted_areas_map = readmap(Filepaths.file_static_restricted_areas_input)
        self.static_restricted_areas_map = cover(boolean(static_restricted_areas_map), boolean(self.null_mask_map))

        self.initial_environment_map = initial_environment_map

    # SH&DK: LPB alternation
    def update_time_step_and_sample_number_and_year(self, time_step, current_sample_number, year):
        self.time_step = time_step
        self.current_sample_number = current_sample_number
        self.year = year

    # SH: original PLUC method
    def set_environment(self, environment_map):
        """ JV: Update the environment (land use map)."""
        self.environment_map = environment_map
        print('\nenvironment map set')


    # SH: LPB alternation - DELIVERS THE MASKS PER TYPE PER SCENARIO WHERE NO ALLOCATION CAN TAKE PLACE
    def determine_areas_of_no_allocation_for_a_type(self, a_type, degree_of_limitation):  # former nogo
        """ This method does not need return statements because the map is changed in LAND USE TYPE by the self. statement

        JV: Create global no-go map, pass it to the types that add own no-go areas.
            SH: produces maps of areas where no allocation can occur depending on type and scenario:
            BAU-scenario:
            - only truly inaccessible
            - favorable terrain unrestricted
            - difficult terrain unrestricted
            - favorable restricted
            - difficult restricted
            worst-case scenario:
            - favorable landscape wide
            - difficult landscape wide"""

        if degree_of_limitation == 'only_truly_inaccessible':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # SH: additional variable for allocation procedure with only the truly excluded cells in the map
            self.immutable_excluded_areas_from_allocation_map = self.excluded_areas_from_allocation_map
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            slope_dependent_areas_of_no_allocation_map = None
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]  # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]  # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrgt(self.slope_map,
                                                                   difficult_slope_maximum)  # for the initial global mask_map only the truly inaccessible terrain is used
            # 3) create the initial mask_map for the singular land use types
            self.create_truly_inaccessible_mask(self.excluded_areas_from_allocation_map,
                                                  slope_dependent_areas_of_no_allocation_map)


        elif degree_of_limitation == 'favorable_terrain_in_unrestricted_areas':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = pcror(self.static_areas_on_which_no_allocation_occurs_map,
                                                            self.static_restricted_areas_map)  # this includes now the self.static_restricted_areas_map
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            slope_dependent_areas_of_no_allocation_map = None
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]
                # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]
                # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrge(self.slope_map,
                                                                   difficult_slope_minimum)  # here only the truly favorable terrain is used
            # 3) create the mask_map leaving only favorable and unrestricted areas for the singular land use type at hand
            self.create_favorable_terrain_in_unrestricted_areas_mask(self.excluded_areas_from_allocation_map,
                                                                       slope_dependent_areas_of_no_allocation_map)

        elif degree_of_limitation == 'difficult_terrain_in_unrestricted_areas':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = pcror(self.static_areas_on_which_no_allocation_occurs_map,
                                                            self.static_restricted_areas_map)  # this includes now the self.static_restricted_areas_map
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            slope_dependent_areas_of_no_allocation_map = None
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]
                # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]
                # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrge(self.slope_map,
                                                                   difficult_slope_maximum)  # here only the difficult terrain is used also
            # 3) create the mask_map leaving only favorable and unrestricted areas for the singular land use type at hand
            self.create_difficult_terrain_in_unrestricted_areas_mask(self.excluded_areas_from_allocation_map,
                                                                       slope_dependent_areas_of_no_allocation_map)

        elif degree_of_limitation == 'favorable_terrain_in_restricted_areas':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            slope_dependent_areas_of_no_allocation_map = None
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]  # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]  # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrgt(self.slope_map,
                                                                   difficult_slope_minimum)  # for this mask_map also the difficult terrain is used
            # 3) create the mask_map for the singular land use types
            self.create_favorable_terrain_in_restricted_areas_mask(self.excluded_areas_from_allocation_map,
                                                                     slope_dependent_areas_of_no_allocation_map)

        elif degree_of_limitation == 'difficult_terrain_in_restricted_areas':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
            slope_dependent_areas_of_no_allocation_map = None
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]  # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]  # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrgt(self.slope_map,
                                                                   difficult_slope_maximum)  # for this mask_map also the difficult terrain is used
            # 3) create the mask_map for the singular land use types
            self.create_difficult_terrain_in_restricted_areas_mask(self.excluded_areas_from_allocation_map,
                                                                     slope_dependent_areas_of_no_allocation_map)

        elif degree_of_limitation == 'favorable_landscape_wide':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
            slope_dependent_areas_of_no_allocation_map = None
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]  # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]  # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrgt(self.slope_map,
                                                                   difficult_slope_minimum)  # for this mask_map also the difficult terrain is used
            # 3) create the mask_map for the singular land use types
            self.create_favorable_terrain_landscape_wide_mask(self.excluded_areas_from_allocation_map,
                                                                slope_dependent_areas_of_no_allocation_map)

        elif degree_of_limitation == 'difficult_landscape_wide':
            # 1) get the predefined areas:
            self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
            slope_dependent_areas_of_no_allocation_map = None
            # JV: Check the list with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            # JV: Get land use type specific no-go areas based on slope from dictionary
            # JV: If not present the variable slope_dependent_areas_of_no_allocation_map is 'None'
            # 2) get the slope dependent areas
            a_slope_list = self.difficult_terrain_slope_restriction_dictionary.get(a_type)
            if a_slope_list is not None:
                # SH:LPB alternation min and max
                difficult_slope_minimum = a_slope_list[0]  # below this value is favorable terrain and can always be allocated
                difficult_slope_maximum = a_slope_list[1]  # in the range up to this value is difficult terrain, above cannot be allocated
                slope_dependent_areas_of_no_allocation_map = pcrgt(self.slope_map,
                                                                   difficult_slope_maximum)  # for this mask_map also the difficult terrain is used
            # 3) create the mask_map for the singular land use types
            self.create_difficult_terrain_landscape_wide_mask(self.excluded_areas_from_allocation_map,
                                                                slope_dependent_areas_of_no_allocation_map)

    # SH: original PLUC method - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_truly_inaccessible_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ JV: Combine the global no-go map with areas unsuitable for this land use.
        SH: LPB alternation: only truly inaccessible mask - this map excludes the static land use types and the slopes above difficult terrain only."""
        self.inaccessible_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.inaccessible_mask_map = pcror(self.inaccessible_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.inaccessible_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_favorable_terrain_in_unrestricted_areas_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask delivers only the areas of favorable land and unrestricted areas."""
        self.favorable_terrain_in_unrestricted_areas_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.favorable_terrain_in_unrestricted_areas_mask_map = pcror(self.favorable_terrain_in_unrestricted_areas_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.favorable_terrain_in_unrestricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_difficult_terrain_in_unrestricted_areas_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask delivers additionally the difficult terrain areas in unrestricted areas."""
        self.difficult_terrain_in_unrestricted_areas_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.difficult_terrain_in_unrestricted_areas_mask_map = pcror(self.difficult_terrain_in_unrestricted_areas_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.difficult_terrain_in_unrestricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_favorable_terrain_in_restricted_areas_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask includes areas of favorable terrain in  restricted areas."""
        self.favorable_terrain_in_restricted_areas_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.favorable_terrain_in_restricted_areas_mask_map = pcror(self.favorable_terrain_in_restricted_areas_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.favorable_terrain_in_restricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_difficult_terrain_in_restricted_areas_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask includes areas of difficult terrain in restricted areas."""
        self.difficult_terrain_in_restricted_areas_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.difficult_terrain_in_restricted_areas_mask_map = pcror(
                self.difficult_terrain_in_restricted_areas_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.difficult_terrain_in_restricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_favorable_terrain_landscape_wide_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask is used for the worst-case scenario and includes all available favorable areas."""
        self.favorable_terrain_landscape_wide_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.favorable_terrain_landscape_wide_mask_map = pcror(
                self.favorable_terrain_landscape_wide_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.favorable_terrain_landscape_wide_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_difficult_terrain_landscape_wide_mask(self, excluded_areas_from_allocation_map,slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask is used for the worst case scenario and includes all difficult areas."""
        self.difficult_terrain_landscape_wide_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.difficult_terrain_landscape_wide_mask_map = pcror(
                self.difficult_terrain_landscape_wide_mask_map, slope_dependent_areas_of_no_allocation_map)
        print('updated self.difficult_terrain_landscape_wide_mask_map')

    # SH: original PLUC method
    def _normalize_map(self, a_map):
        """ JV: Return a normalized version of the input map."""
        map_maximum = mapmaximum(a_map)
        map_minimum = mapminimum(a_map)
        difference = float(map_maximum - map_minimum)
        if difference < 0.000001:
            normalized_map = (a_map - map_minimum) / 0.000001
        else:
            normalized_map = (a_map - map_minimum) / difference
        print('\nnormalized map filed')
        return normalized_map

    # SH: original PLUC method (1)
    # JV 1
    def _get_neighbor_suitability(self, environment_map): # dynamic environment map from LandUse!
        """ JV: Return suitability map based on number of neighbors with a related type."""
        boolean_self = pcreq(environment_map, self.type_number)
        for a_type in self.related_types_list:
            boolean_map = pcreq(environment_map, a_type)
            boolean_self = pcror(boolean_self, boolean_map)
        scalar_self = scalar(boolean_self)
        # JV: Count number of neighbors with 'true' in a window with length from parameters
        # JV: and assign this value to the center cell
        variables_list = self.variables_dictionary.get(1)
        window_length = variables_list[0]
        if self.stochastic_window == 1:
            window_length += (celllength() / 3) * self.window_length_realization
        # JV:     print 'window_length is', float(window_length)
        number_neighbors_same_land_use_type = windowtotal(
            scalar_self, window_length) - scalar_self
        # JV: The number of neighbors are turned into suitability values between 0 and 1
        maximum_number_neighbors = ((window_length / celllength()) ** 2) - 1
        neighbor_suitability = number_neighbors_same_land_use_type / maximum_number_neighbors
        print('\nneighbor-suitability for LUT', self.type_number, 'calculated')
        return neighbor_suitability

    # SH: original PLUC method (2)
    ## JV: 2
    # SH: LPB alternation - road substituted with street (finer level in LPB)
    def _get_distance_street_suitability(self, spread_map_streets):
        """ JV: Return suitability map based on distance to streets."""
        variables_list = self.variables_dictionary.get(2)
        direction = variables_list[0]
        maximum_distance = variables_list[1]
        if self.stochastic_distance == 1:
            maximum_distance = 2 * celllength() + mapuniform() * \
                               (2 * maximum_distance - 2 * celllength())
            print('maximum distance streets is:', int(maximum_distance))
        friction = variables_list[2]
        relation_type = variables_list[3]

        # JV: Influence up to some maximum distance
        cut_off_map = ifthen(spread_map_streets <
                             maximum_distance, spread_map_streets * direction)
        normalized_map = self._normalize_map(cut_off_map)
        # JV: Implement linear (0), exponential (1) or inv. proportional (2) relation
        if relation_type == 0:
            relation_map = normalized_map
        elif relation_type == 1:
            exponential_map = exp(direction * normalized_map)
            relation_map = self._normalize_map(exponential_map)
        elif relation_type == 2:
            inverse_proportional_map = (-1) / (normalized_map + 0.1)
            relation_map = self._normalize_map(inverse_proportional_map)

        street_suitability_map = cover(relation_map, scalar(self.null_mask_map)) # SH: changed null mask_map to scalar
        print('street-suitability for LUT', self.type_number, 'calculated')
        return street_suitability_map

    # SH: original PLUC method (3)
    ## JV: 3
    # SH: LPB alternation - freshwater (finer level in LPB, freshwater explicitly, since the seawater at the coastline is not recognized)
    def _get_distance_freshwater_suitability(self, spread_map_freshwater):
        """ JV: Return suitability map based on distance to freshwater."""
        variables_list = self.variables_dictionary.get(3)
        direction = variables_list[0]
        maximum_distance = variables_list[1]
        if self.stochastic_distance == 1:
            maximum_distance = 2 * celllength() + mapuniform() * \
                               (2 * maximum_distance - 2 * celllength())
            print('maximum distance freshwater is:', int(maximum_distance))
        friction = variables_list[2]
        relation_type = variables_list[3]

        # JV: Influence up to some maximum distance
        cut_off_map = ifthen(
            spread_map_freshwater < maximum_distance, spread_map_freshwater * direction)
        normalized_map = self._normalize_map(cut_off_map)
        # JV: Implement linear (0), exponential (1) or inv. proportional (2) relation
        if relation_type == 0:
            relation_map = normalized_map
        elif relation_type == 1:
            exponential_map = exp(direction * normalized_map)
            relation_map = self._normalize_map(exponential_map)
        elif relation_type == 2:
            inverse_proportional_map = (-1) / (normalized_map + 0.1)
            relation_map = self._normalize_map(inverse_proportional_map)

        freshwater_suitability_map = cover(relation_map, scalar(self.null_mask_map)) # SH: changed null mask_map to scalar
        print('freshwater-suitability for LUT', self.type_number, 'calculated')
        return freshwater_suitability_map

    # SH: original PLUC method (4)
    ## JV: 4
    # SH: LPB alternation - city layer includes towns
    def _get_distance_city_suitability(self, spread_map_cities):
        """ JV: Return suitability map based on distance to large cities."""
        variables_list = self.variables_dictionary.get(4)
        direction = variables_list[0]
        maximum_distance = variables_list[1]
        if self.stochastic_distance == 1:
            maximum_distance = 2 * celllength() + mapuniform() * \
                               (2 * maximum_distance - 2 * celllength())
            print('maximum distance cities is:', int(maximum_distance))
        friction = variables_list[2]
        relation_type = variables_list[3]

        # JV: Influence up to some maximum distance
        cut_off_map = ifthen(spread_map_cities <
                             maximum_distance, spread_map_cities * direction)
        normalized_map = self._normalize_map(cut_off_map)
        # JV: Implement linear (0), exponential (1) or inv. proportional (2) relation
        if relation_type == 0:
            relation_map = normalized_map
        elif relation_type == 1:
            exponential_map = exp(direction * normalized_map)
            relation_map = self._normalize_map(exponential_map)
        elif relation_type == 2:
            inverse_proportional_map = (-1) / (normalized_map + 0.1)
            relation_map = self._normalize_map(inverse_proportional_map)

        city_suitability_map = cover(relation_map, scalar(self.null_mask_map)) # SH: changed null mask_map to scalar
        print('cities-suitability for LUT', self.type_number, 'calculated')
        return city_suitability_map

    # SH: LPB alternation settlements (5)
    # SH: LPB alternation - settlements are hamlets and villages
    def _get_distance_settlement_suitability(self, distances_to_settlements_map):
        """ SH: Return suitability map based on distance to settlements."""
        variables_list = self.variables_dictionary.get(5)
        direction = variables_list[0]
        if self.type_number == 2: # cropland annual
            maximum_distance = self.LUT02_sampled_distance_for_this_sample
        elif self.type_number == 3: # pasture
            maximum_distance = self.LUT03_sampled_distance_for_this_sample
        elif self.type_number == 4: # agroforestry
            maximum_distance = self.LUT04_sampled_distance_for_this_sample
        else:
            maximum_distance = variables_list[1]
            if self.stochastic_distance == 1:
                maximum_distance = 2 * celllength() + mapuniform() * \
                                   (2 * maximum_distance - 2 * celllength())
        print('maximum distance settlements is:', int(maximum_distance))
        friction = variables_list[2]
        relation_type = variables_list[3]

        # JV: Influence up to some maximum distance
        cut_off_map = ifthen(distances_to_settlements_map < maximum_distance,
                             distances_to_settlements_map * direction)
        normalized_map = self._normalize_map(cut_off_map)
        # JV: Implement linear (0), exponential (1) or inv. proportional (2) relation
        if relation_type == 0:
            relation_map = normalized_map
        elif relation_type == 1:
            exponential_map = exp(direction * normalized_map)
            relation_map = self._normalize_map(exponential_map)
        elif relation_type == 2:
            inverse_proportional_map = (-1) / (normalized_map + 0.1)
            relation_map = self._normalize_map(inverse_proportional_map)

        settlement_suitability_map = cover(relation_map, scalar(self.null_mask_map)) # SH: changed null mask_map to scalar
        print('settlements-suitability for LUT', self.type_number, 'calculated')
        return settlement_suitability_map

    # SH: original PLUC method (6)
    ## JV: 6
    # SH: LPB alternation
    def _get_population_suitability(self, population_map):
        """ JV: Return suitability map based on population density."""
        # report(population_density_map, os.path.join(Filepaths.folder_TEST,'population_density_map' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
        variables_list = self.variables_dictionary.get(6)
        direction = variables_list[0]
        population_suitability_map = direction * population_map
        population_suitability_map = self._normalize_map(population_suitability_map)
        print('population-suitability for LUT', self.type_number, 'calculated')
        return population_suitability_map

    # SH: LPB alternation to net forest edge (7)
    ## JV: 8
    # SH: LPB alternation - net forest edge, net forest is based on national maps declared land surface of "native forest"
    def _get_net_forest_edge_suitability(self, net_forest_map):
        not_net_forest_environment_map = ifthenelse(scalar(net_forest_map) == scalar(1),
                                                    nominal(0),
                                                    nominal(self.environment_map)) # landscape with all LUTs where current net forest is 0
        not_the_current_LUT_map = pcrne(not_net_forest_environment_map, self.type_number) # a map with all other LUTs within the cut out map
        distances_to_net_forest_edge_map = spread(not_the_current_LUT_map, 1, 1)
        net_forest_edge_suitability_map = self._normalize_map(-1 / distances_to_net_forest_edge_map)
        print('net_forest_edge-suitability for LUT', self.type_number, 'calculated')
        return net_forest_edge_suitability_map

    # SH: original PLUC method (8)
    ## JV: 9
    # SH: LPB alternation - current land use
    def _get_current_land_use_type_suitability(self, environment_map):
        """ JV: Return suitability map based on current land use type."""
        variables_dictionary = self.variables_dictionary.get(8)
        current_map = self.null_mask_map
        for a_key in variables_dictionary.keys():
            current_map = ifthenelse(pcreq(environment_map, a_key),
                                     variables_dictionary.get(a_key),
                                     scalar(current_map)) # SH: changed to scalar
        current_land_use_type_suitability_map = self._normalize_map(current_map)
        print('current_land_use_type-suitability for LUT', self.type_number, 'calculated')
        return current_land_use_type_suitability_map

    # SH for ML:
    # model stage 3
    def _get_crop_yield_suitability(self):
        """ JV: Return suitability map based on yield for crops or cattle.
        SH: Altered for LPB for use with climate period data and diversified crops (cropland annual and agroforestry).
        Livestock density is in the following method."""

        if self.type_number == 2: # crops in cropland annual
            if self.year >= 2018 and self.year <= 2020:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_cropland_annual_crops_2018_2020_input']
            elif self.year >= 2021 and self.year <= 2040:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_cropland_annual_crops_2021_2040_input']
            elif self.year >= 2041 and self.year <= 2060:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_cropland_annual_crops_2041_2060_input']
            elif self.year >= 2061 and self.year <= 2080:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_cropland_annual_crops_2061_2080_input']
            elif self.year >= 2081 and self.year <= 2100:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_cropland_annual_crops_2081_2100_input']
        if self.type_number == 4: # crops in agroforestry
            if self.year >= 2018 and self.year <= 2020:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_agroforestry_crops_2018_2020_input']
            elif self.year >= 2021 and self.year <= 2040:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_agroforestry_crops_2021_2040_input']
            elif self.year >= 2041 and self.year <= 2060:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_agroforestry_crops_2041_2060_input']
            elif self.year >= 2061 and self.year <= 2080:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_agroforestry_crops_2061_2080_input']
            elif self.year >= 2081 and self.year <= 2100:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_agroforestry_crops_2081_2100_input']

        # user determined simulation of yield
        if Parameters.get_yield_simulation_basis_decision() == 'original_potential_yield':
            self.yield_basis_map = potential_yield_map
        if Parameters.get_yield_simulation_basis_decision() == 'potential_yield_fraction':
            self.yield_basis_map = potential_yield_map / mapmaximum(potential_yield_map)
        if self.type_number == 2:
            variables_list = self.variables_dictionary.get(9)
            friction = variables_list[0]
        if self.type_number == 4:
            variables_list = self.variables_dictionary.get(11)
            friction = variables_list[0]
        yield_relation_map = exp(friction * self.yield_basis_map)
        yield_suitability_map = self._normalize_map(yield_relation_map)
        return yield_suitability_map

    # 7 in PLUC
    # 10 in LPB
    # SH LPB alternation
    def _get_livestock_suitability(self):
        """JV: Return suitability map based on cattle density."""
        if self.type_number == 3: # livestock density on pastures
            if self.year >= 2018 and self.year <= 2020:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_livestock_density_2018_2020_input']
            elif self.year >= 2021 and self.year <= 2040:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_livestock_density_2021_2040_input']
            elif self.year >= 2041 and self.year <= 2060:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_livestock_density_2041_2060_input']
            elif self.year >= 2061 and self.year <= 2080:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_livestock_density_2061_2080_input']
            elif self.year >= 2081 and self.year <= 2100:
                potential_yield_map = self.climate_period_inputs_dictionary['file_projection_potential_yield_livestock_density_2081_2100_input']
        # could be expanded to livestock density in agroforestry

        if self.type_number == 3:
            variables_list = self.variables_dictionary.get(10)
            direction = variables_list[0]
            # user determined simulation of yield
            if Parameters.get_yield_simulation_basis_decision() == 'original_potential_yield':
                self.yield_basis_map = potential_yield_map
            if Parameters.get_yield_simulation_basis_decision() == 'potential_yield_fraction':
                self.yield_basis_map = potential_yield_map / mapmaximum(potential_yield_map)

        livestock_suitability_map = direction * potential_yield_map
        livestock_suitability_map = self._normalize_map(livestock_suitability_map)
        return livestock_suitability_map

# SH placeholder for SFM model stage 3
    def _get_wood_yield_suitability(self):
        """This method might get employed in SFM where potential SFM plots might get calculated by projected wood yield potentials"""
        # Requires new LUTs (31-40) and climate period inputs and adapted tss docs, could maybe also employ PNV, should maybe incoporate agroforestry wood yields


    def create_initial_suitability_map(self, distances_to_streets_map, distances_to_freshwater_map, distances_to_cities_map):
        """ JV: Return the initial suitability map, i.e. for static factors.

        SH: Return the initial suitability map, i.e. for static factors only.
        Uses three maps in LPB:
        1) distances to streets
        2) distances to freshwater
        3) distances to cities
        
        JV: Uses a list and two dictionaries created at construction of the object:
        factors -- the names (numbers) of the suitability factors (methods) needed
        parameters -- the input parameters for those factors
        weights -- the weights that belong to those factors (how they're combined)."""

        print('LUT', self.type_number, 'suitability factors list in initial suitability: ', self.suitability_factors_list)

        self.weight_initial_suitability_map = 0
        self.initial_suitability_map = spatial(scalar(0))
        iteration = 0
        # JV: For every number in the suitability factor list
        # JV: that belongs to a STATIC factor
        # JV: the corresponding function is called providing the necessary parameters
        # JV: and the partial suitability map is added to the total
        # JV: taking into account its relative importance (weight)
        print('\ncalculating static suitabilities for LUT', self.type_number, 'initiated ...')
        for a_factor in self.suitability_factors_list:
            if a_factor == 2:
                # street suitability - static - stays 2
                self.initial_suitability_map += self.weights_list[iteration] * \
                                                self._get_distance_street_suitability(distances_to_streets_map)
                self.weight_initial_suitability_map += self.weights_list[iteration]
                print('static distance to streets suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 3:
                # freshwater suitability - static - stays 3
                self.initial_suitability_map += self.weights_list[iteration] * \
                                                self._get_distance_freshwater_suitability(distances_to_freshwater_map)
                self.weight_initial_suitability_map += self.weights_list[iteration]
                print('static distance to freshwater suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 4:
                # city suitability - static - stays 4
                self.initial_suitability_map += self.weights_list[iteration] * \
                                                self._get_distance_city_suitability(distances_to_cities_map)
                self.weight_initial_suitability_map += self.weights_list[iteration]
                print('static distance to cities suitability for LUT', self.type_number, 'calculated')
            elif a_factor in (1, 5, 6, 7, 8):
                # JV: Dynamic factors are captured in the total suitability map
                # SH: new dynamic factors are:
                # 1 number of neighbors same class
                # 5 distance to settlements
                # 6 population density
                # 7 distance to net forest edge
                # 8 current land use
                pass
            else:
                print('\nERROR: unknown suitability factor for land use',
                      self.type_number)
            iteration += 1
        print('\nweight of initial factor of', self.type_number,
              'is', self.weight_initial_suitability_map)
        print('static suitability map calculated')

    # SH: LPB alternation
    def get_total_suitability_map(self, environment_map, distances_to_settlements_map, population_map, net_forest_map):
        """ JV: Return the total suitability map for the land use type.
        Uses a lists and two dictionaries:
        factors -- the names (numbers) of the suitability factors (methods) needed
        parameters -- the input parameters for those factors
        weights -- the weights that belong to those factors (how they're combined). """

        print('\nLUT', self.type_number, 'suitability factors list in dynamic suitability: ', self.suitability_factors_list)

        suitability_map = spatial(scalar(0))
        iteration = 0
        # JV: For every number in the suitability factor list
        # JV: that belongs to a DYNAMIC factor
        # JV: the corresponding function is called providing the necessary parameters
        # JV: and the partial suitability map is added to the total
        # JV: taking into account its relative importance (weight)
        # LPB alternation
        # SH: new dynamic factors are:
        # 1 number of neighbors same class
        # 5 distance to settlements
        # 6 population density
        # 7 distance to net forest edge
        # 8 current land use
        ## only in model stage 3 in the yield approach:
        # 9 yield potential map crops of cropland annual
        # 10 yield potential map livestock density of pastures
        # 11 yield potential map crops of agroforestry

        print('\ncalculating dynamic suitabilities for LUT', self.type_number, 'initiated ...')
        for a_factor in self.suitability_factors_list:
            if a_factor in (2, 3, 4):
                # JV: Static factors already captured in the initial suitability map
                # SH: static factors are now only:
                # 2 = street distance
                # 3 = freshwater distance
                # 4 = city distance
                pass
            # dynamic maps are attached for the factors 1,5,6,7,8
            elif a_factor == 1:  # suitability factor = number of neighbors same class
                suitability_map += self.weights_list[iteration] * \
                                   self._get_neighbor_suitability(environment_map=environment_map)
                print('dynamic neighbor suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 5:  # suitability factor = distance to settlements
                suitability_map += self.weights_list[iteration] * \
                                   self._get_distance_settlement_suitability(distances_to_settlements_map=distances_to_settlements_map)
                print('dynamic settlement suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 6:  # suitability factor = population density
                suitability_map += self.weights_list[iteration] * \
                                   self._get_population_suitability(population_map=population_map)
                print('dynamic population suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 7:  # suitability factor = distance to net forest edge
                suitability_map += self.weights_list[iteration] * \
                                   self._get_net_forest_edge_suitability(net_forest_map=net_forest_map)
                print('dynamic net forest edge suitability for LUT', self.type_number, 'calculated')
            elif a_factor == 8:  # suitability factor = current land use
                suitability_map += self.weights_list[iteration] * \
                                   self._get_current_land_use_type_suitability(environment_map=environment_map)
                print('dynamic current land use type suitability for LUT', self.type_number, 'calculated')
            # SH for ML:
            elif Parameters.demand_configuration['overall_method'] == 'yield_units':
                # The required (dynamic only per climate period) maps are transported once in init in the climate_period_inputs_dictionary for 9, 10, 11
                if a_factor == 9:  # suitability factor = this is crop yield for cropland_annual
                    suitability_map += self.weights_list[iteration] * \
                                           self._get_crop_yield_suitability()
                    print('dynamic crop yield suitability for LUT cropland-annual calculated')
                if a_factor == 10:  # suitability factor = this is livestock density for pastures
                    suitability_map += self.weights_list[iteration] * \
                                           self._get_livestock_suitability()
                    print('dynamic livestock suitability for LUT pasture calculated')
                if a_factor == 11:  # suitability factor = this is crop yield for agroforestry
                    suitability_map += self.weights_list[iteration] * \
                                           self._get_crop_yield_suitability()
                    print('dynamic crop yield suitability for LUT agroforestry calculated')
            else:
                print('\nERROR: unknown suitability factor for land use',
                      self.type_number)
            iteration += 1
        # SH: new code self.total_suitability_map (inaccessible is subtracted in _add)
        suitability_map += self.initial_suitability_map
        suitability_map += self.small_noise_map
        self.total_suitability_map = self._normalize_map(suitability_map)
        print('maximum suitability map for LUT', self.type_number, 'calculated')
        return self.total_suitability_map

    def _update_current_area_occupied_by_LUT(self, temporal_environment_map): # former _update_yield
        """ JV: Calculate total yield generated by cells occupied by this land use."""
        # JV: Current cells taken by this land use type
        # SH: LPB alternation - count the cells in current environment
        self.current_area_occupied_by_LUT_map = ifthen(temporal_environment_map == self.type_number,
                                                       scalar(1))
        ## JV:   report(self.currentYield, 'currentYield' + str(self.type_number))
        self.current_area_occupied_by_LUT = int(maptotal(self.current_area_occupied_by_LUT_map))
        print('current area occupied by LUT', self.type_number, 'is:', self.current_area_occupied_by_LUT, Parameters.get_pixel_size())
        return self.current_area_occupied_by_LUT

    # SH for ML:
    # TODO for model stage 3
    def set_maximum_yield(self):
        """ JV: Set the maximum yield in this time step using the input from the tss."""
       # SH alteration LPB:
        if Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
            tss_deterministic_maximum_yield = self.external_demands_generated_tss_dictionary['generated_tss_deterministic_maximum_yield']
            maximum_yield = float(tss_deterministic_maximum_yield.value(self.time_step, self.type_number))
        if Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
            tss_stochastic_maximum_yield = self.external_demands_generated_tss_dictionary['generated_tss_stochastic_maximum_yield']
            maximum_yield = float(tss_stochastic_maximum_yield.value(self.time_step, self.type_number))
        converted_maximum_yield = (maximum_yield / self.to_square_meters) * cellarea()
        own_maximum_yield_map = ifthen(self.environment_map == self.type_number, converted_maximum_yield)
        ## maximum yield PER CELL
        self.maximum_yield = float(mapmaximum(own_maximum_yield_map))
        self.yield_map = self.yield_basis_map * self.maximum_yield



    # SH for ML:
    # TODO for model stage 3
    def _update_yield(self, env):
        """ JV: Calculate total yield generated by cells occupied by this land use."""
        ## JV: Current cells taken by this land use type
        self.current_yield_map = ifthen(env == self.type_number, self.yield_map)
        ##    report(self.currentYield, 'currentYield' + str(self.type_number))
        self.total_yield = float(maptotal(self.current_yield_map))


    def allocate(self, demand, temporal_environment_map, immutables_map, temporal_succession_age_map):
        """ JV: Assess total yield, compare with demand and add or remove difference."""
        """SH: Allocation of the five active land use types only in the form of existing current_area_occupied_by_LUT vs demand 
        or in case of plantations according to rotation period end. 
        
        Contradicting to PLUC forest LUT08 (disturbed forest) is grown via succession and net_forest only indirectly removed via demand_AGB.
        
        Contradicting to PLUC the allocation cascades and differs in-between BAU and worst case scenario!"""

        # get the allocation based on the current policy guideline scenario
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            _add = self._add_BAU_scenario
            _add_with_yield = self._add_with_yield_BAU_scenario  # NEW model stage 3
        elif Parameters.get_model_scenario() == 'no_conservation':
            _add = self._add_worst_case_scenario
            _add_with_yield = self._add_with_yield_worst_case_scenario  # NEW model stage 3

        # set the path for the land use types
        self.set_environment(temporal_environment_map)
        self._update_current_area_occupied_by_LUT(temporal_environment_map)
        # SH alteration model stage 3:
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and self.type_number in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            self._update_yield(temporal_environment_map)
        # SH: LPB alternation
        self.demand = demand[self.type_number]  # DK: suggestion
        print('\nland use type number is:', self.type_number)
        if self.type_number == 1:
            print('that is:', Parameters.LUT01)
            print('\ndemand is:', self.demand, Parameters.get_pixel_size())
        elif self.type_number == 2:
            print('that is:', Parameters.LUT02)
            print('\ndemand is:', self.demand, Parameters.get_pixel_size(), 'or user-defined yield unit')
        elif self.type_number == 3:
            print('that is:', Parameters.LUT03)
            print('\ndemand is:', self.demand, Parameters.get_pixel_size(), 'or user-defined yield unit')
        elif self.type_number == 4:
            print('that is:', Parameters.LUT04)
            print('\ndemand is:', self.demand, Parameters.get_pixel_size(), 'or user-defined yield unit')
        elif self.type_number == 5:
            print('that is:', Parameters.LUT05)
            print('\ndemand is:', self.demand, Parameters.get_pixel_size())

        # SH: LPB alternation
        number_of_to_be_added_cells, only_new_pixels_map = None, None
        if self.type_number == 1:
            print('total built-up area from last time step is:', self.current_area_occupied_by_LUT,
                  Parameters.get_pixel_size())
            if self.current_area_occupied_by_LUT > self.demand:
                print('demand in built-up decreased, so built-up area stays as is (built-up is a final land use type)')
            elif self.current_area_occupied_by_LUT < self.demand:
                print('demand in built-up area increased, so allocate more', Parameters.get_pixel_size())
                number_of_to_be_added_cells, only_new_pixels_map, immutables_map = _add(immutables_map)
            else:
                print('demand equals existing built-up area, nothing changes for this land use type')
        elif self.type_number in [2, 3, 4]:
            # NEW CODE:
            if Parameters.demand_configuration['overall_method'] == 'footprint' or self.type_number not in Parameters.demand_configuration['LUTs_with_demand_and_yield']:  # this applies to all LUTs to be simulated with the LPB footprint approach
                print('total area/acreage from last time step is:', self.current_area_occupied_by_LUT,
                      Parameters.get_pixel_size())
                if self.current_area_occupied_by_LUT > self.demand:
                    print('demand decreased, so abandon area/acreage')
                    temporal_succession_age_map = self._remove(temporal_succession_age_map)
                elif self.current_area_occupied_by_LUT < self.demand:
                    print('demand increased, so allocate more area/acreage')
                    number_of_to_be_added_cells, only_new_pixels_map, immutables_map = _add(immutables_map)
                else:
                    print('demand equals area, nothing changes for this land use type')
            else:  # this is only for the LUTs for which a yield is provided, up to now this is only conceptualized for agricultural LUTs (selection of LUTs is user-defined)
                print('total yield is:', self.total_yield)
                if self.total_yield > self.demand:
                    print('demand decreased, so abandon area/acreage')
                    temporal_succession_age_map = self._remove_with_yield(temporal_succession_age_map)
                elif self.total_yield < self.demand:
                    print('demand increased, so allocate more area/acreage')
                    number_of_to_be_added_cells, only_new_pixels_map, immutables_map = _add_with_yield(immutables_map)
                else:
                    print('demand equals area, nothing changes for this land use type')
        # SH: LPB alternation - Plantations
        elif self.type_number == 5:
            print('total area of plantations from last time step is:', self.current_area_occupied_by_LUT,
                  Parameters.get_pixel_size())
            if self.current_area_occupied_by_LUT > self.demand:
                print('demand in plantation area decreased, no changes if not harvest')
            elif self.current_area_occupied_by_LUT == self.demand:
                print('demand in plantation area covers current extent, no changes if not harvest')
            elif self.current_area_occupied_by_LUT < self.demand:
                print('demand in plantation area is higher than current extent, so allocate more area')
                number_of_to_be_added_cells, only_new_pixels_map, immutables_map = _add(immutables_map)

        # in case of _remove() calculate the immutables here
        immutables_map = ifthenelse(self.environment_map == self.type_number,
                                    boolean(1),
                                    boolean(immutables_map))

        return self.environment_map, immutables_map, number_of_to_be_added_cells, only_new_pixels_map, temporal_succession_age_map


    # SH: LPB alternation - cascade BAU add allocation
    def _add_BAU_scenario(self, immutables_map):
        """Takes the total suitability mask and subtracts masks for each step demand can be allocated:
        - Initialization: subtract only truly inaccessible and immutables from total suitability
        - Allocation 1: minus current occupied cells in favorable terrain unrestricted
        - Allocation 2: minus current occupied cells in difficult terrain unrestricted - if demand could not be satisfied prior
        - Allocation 3: minus current occupied cells in favorable restricted - if demand could not be satisfied prior
        - Allocation 4: minus current occupied cells in difficult restricted - if demand could not be satisfied prior
        """

        # initialize the variables to be returned
        number_of_to_be_added_cells = 0
        only_new_pixels_map = spatial(scalar(0))

        # initialize the cascade variable
        area_after_addition = 0

        # initialize the tracking variable for unallocated demands
        unallocated_demand = self.demand

        print('\nallocation of LUT', self.type_number, 'of demand:', self.demand, Parameters.get_pixel_size())

        # INITIALIZATION:
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='only_truly_inaccessible')

        # exclude the inaccessible land use area
        suitabilities_only_inaccessible_excluded_map = ifthen(pcrnot(self.inaccessible_mask_map),
                                                              scalar(self.total_suitability_map))

        # JV: remove cells from immutables_map (already changed)
        suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                      scalar(suitabilities_only_inaccessible_excluded_map))

        # ALLOCATION 1
        print('allocating in favorable terrain in unrestricted areas')
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='favorable_terrain_in_unrestricted_areas')

        # JV: remove cells already occupied by this land use
        suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                     suitabilities_without_immutables_map)

        # get the adjusted map
        suitabilities_favorable_terrain_in_unrestricted_areas_map = ifthen(
            pcrnot(self.favorable_terrain_in_unrestricted_areas_mask_map),
            scalar(suitabilities_without_own_cells_map))

        # JV: Determine maximum suitability and allocate new cells there
        map_maximum = float(mapmaximum(suitabilities_favorable_terrain_in_unrestricted_areas_map))
        print('map_maximum (maximum suitability in suitabilities_favorable_terrain_in_unrestricted_areas_map) =', float(map_maximum))
        # SH: code alteration
        map_maximum_NaN = numpy.isnan(map_maximum) # check if there are still available cells
        if map_maximum_NaN == False: # if yes do the calculation
            ordered_map = order(suitabilities_favorable_terrain_in_unrestricted_areas_map)
            maximum_index = mapmaximum(ordered_map)
            self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
            difference = float(self.demand - self.current_area_occupied_by_LUT)
            # SH: new code start
            ordered_maximum_minus_difference = int(
                maximum_index - difference)  # determines initially the number of cells to be changed (top value)
            if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                ordered_allocation_minimum_value = ordered_maximum_minus_difference
            else:
                ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
            number_of_to_be_added_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
            only_new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                         # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                         nominal(self.type_number))
            # SH: new code end
            temp_environment_map = cover(only_new_pixels_map, self.environment_map)
            self.set_environment(temp_environment_map)
            # SH: new code start
            immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                        boolean(1),
                                        boolean(immutables_map))
            area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
            print('area_after_addition:', area_after_addition)
            unallocated_demand = self.demand - area_after_addition
            if area_after_addition == self.demand:
                print('-> demand of', self.demand, Parameters.get_pixel_size(), 'by LUT', self.type_number,
                      'was satisfied by', area_after_addition, Parameters.get_pixel_size(),
                      'in available favorable unrestricted landscape area, no allocation in difficult terrain and no conflict')
        if map_maximum_NaN == True:
            # # TEST
            # report(suitabilities_favorable_terrain_in_unrestricted_areas_map, os.path.join(Filepaths.folder_TEST,
            #                                                                                'suitabilities_favorable_terrain_in_unrestricted_areas_map_S'+str(self.current_sample_number) +
            #                                                                                '_TS' + str(self.time_step) +
            #                                                                                '_Y' + str(self.year) +
            #                                                                                '_LUT' + str(self.type_number) +
            #                                                                                '.map'))
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            degree_of_limitation = "favorable_terrain_in_unrestricted_areas"
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                writer.writerow(LPB_log_file_data)
        # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
        if map_maximum_NaN == True or area_after_addition != self.demand:
            # ALLOCATION 2
            print('allocating in difficult terrain in unrestricted areas')
            # trigger the method so that the according map for the type gets updated
            self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                             degree_of_limitation='difficult_terrain_in_unrestricted_areas')

            # JV: remove cells from immutables_map (already changed)
            suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                          scalar(suitabilities_only_inaccessible_excluded_map))

            # JV: remove cells already occupied by this land use
            suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                         suitabilities_without_immutables_map)

            # get the adjusted map
            suitabilities_difficult_terrain_in_unrestricted_areas_map = ifthen(
                pcrnot(self.difficult_terrain_in_unrestricted_areas_mask_map),
                scalar(suitabilities_without_own_cells_map))

            # JV: Determine maximum suitability and allocate new cells there
            map_maximum = float(mapmaximum(suitabilities_difficult_terrain_in_unrestricted_areas_map))
            print('map_maximum (maximum suitability in suitabilities_difficult_terrain_in_unrestricted_areas_map) =',
                  float(map_maximum))
            map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
            if map_maximum_NaN == False:  # if yes do the calculation
                ordered_map = order(suitabilities_difficult_terrain_in_unrestricted_areas_map)
                maximum_index = int(mapmaximum(ordered_map))
                self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
                difference = float(self.demand - self.current_area_occupied_by_LUT)
                # SH: new code start
                ordered_maximum_minus_difference = int(
                    maximum_index - difference)  # determines initially the number of cells to be changed (top value)
                if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                    ordered_allocation_minimum_value = ordered_maximum_minus_difference
                else:
                    ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
                new_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
                number_of_to_be_added_cells = number_of_to_be_added_cells + new_cells
                new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                             # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                             nominal(self.type_number))
                only_new_pixels_map = cover(nominal(new_pixels_map), nominal(only_new_pixels_map))
                # SH: new code end
                temp_environment_map = cover(new_pixels_map, self.environment_map)
                self.set_environment(temp_environment_map)
                # SH: new code start
                immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                            boolean(1),
                                            boolean(immutables_map))
                area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
                print('area_after_addition:', area_after_addition)
                unallocated_demand = self.demand - area_after_addition
                if area_after_addition == self.demand:
                    print(
                        '-> demand was satisfied in available difficult unrestricted landscape area, no conflict')
            if map_maximum_NaN == True:
                # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                sample = self.current_sample_number
                time_step = self.time_step
                year = self.year
                LUT = self.type_number
                degree_of_limitation = "difficult_terrain_in_unrestricted_areas"
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                          newline='') as LPB_log_file:
                    # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                    writer = csv.writer(LPB_log_file)
                    LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                    writer.writerow(LPB_log_file_data)
            # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
            if map_maximum_NaN == True or area_after_addition != self.demand:
                # ALLOCATION 3
                print('allocating in favorable terrain in restricted areas')
                # trigger the method so that the according map for the type gets updated
                self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                                 degree_of_limitation='favorable_terrain_in_restricted_areas')

                # JV: remove cells from immutables_map (already changed)
                suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                              scalar(suitabilities_only_inaccessible_excluded_map))

                # JV: remove cells already occupied by this land use
                suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                             suitabilities_without_immutables_map)

                # get the adjusted map
                suitabilities_favorable_terrain_in_restricted_areas_map = ifthen(
                    pcrnot(self.favorable_terrain_in_restricted_areas_mask_map),
                    scalar(suitabilities_without_own_cells_map))

                # JV: Determine maximum suitability and allocate new cells there
                map_maximum = float(mapmaximum(suitabilities_favorable_terrain_in_restricted_areas_map))
                print('map_maximum (maximum suitability in suitabilities_favorable_terrain_in_restricted_areas_map) =',
                      float(map_maximum))
                map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
                if map_maximum_NaN == False:  # if yes do the calculation
                    ordered_map = order(suitabilities_favorable_terrain_in_restricted_areas_map)
                    maximum_index = int(mapmaximum(ordered_map))
                    self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
                    difference = float(self.demand - self.current_area_occupied_by_LUT)
                    # SH: new code start
                    ordered_maximum_minus_difference = int(
                        maximum_index - difference)  # determines initially the number of cells to be changed (top value)
                    if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                        ordered_allocation_minimum_value = ordered_maximum_minus_difference
                    else:
                        ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
                    new_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
                    number_of_to_be_added_cells = number_of_to_be_added_cells + new_cells
                    new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                            # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                            nominal(self.type_number))
                    only_new_pixels_map = cover(nominal(new_pixels_map), nominal(only_new_pixels_map))
                    # SH: new code end
                    temp_environment_map = cover(new_pixels_map, self.environment_map)
                    self.set_environment(temp_environment_map)
                    # SH: new code start
                    immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                                boolean(1),
                                                boolean(immutables_map))
                    area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
                    print('area_after_addition:', area_after_addition)
                    unallocated_demand = self.demand - area_after_addition
                    if area_after_addition == self.demand:
                        print(
                            '-> demand was satisfied in favorable terrain in restricted areas => conflict')
                if map_maximum_NaN == True:
                    # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                    sample = self.current_sample_number
                    time_step = self.time_step
                    year = self.year
                    LUT = self.type_number
                    degree_of_limitation = "favorable_terrain_in_restricted_areas"
                    with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                              newline='') as LPB_log_file:
                        # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                        writer = csv.writer(LPB_log_file)
                        LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                        writer.writerow(LPB_log_file_data)
                # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
                if map_maximum_NaN == True or area_after_addition != self.demand:
                    # ALLOCATION 4
                    print('allocating in difficult terrain in restricted areas')
                    # trigger the method so that the according map for the type gets updated
                    self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                                     degree_of_limitation='difficult_terrain_in_restricted_areas')

                    # JV: remove cells from immutables_map (already changed)
                    suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                                  scalar(suitabilities_only_inaccessible_excluded_map))

                    # JV: remove cells already occupied by this land use
                    suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                                 suitabilities_without_immutables_map)

                    # get the adjusted map
                    suitabilities_difficult_terrain_in_restricted_areas_map = ifthen(
                        pcrnot(self.difficult_terrain_in_restricted_areas_mask_map),
                        scalar(suitabilities_without_own_cells_map))

                    # JV: Determine maximum suitability and allocate new cells there
                    map_maximum = float(mapmaximum(suitabilities_difficult_terrain_in_restricted_areas_map))
                    print('map_maximum (maximum suitability in suitabilities_difficult_terrain_in_restricted_areas_map) =',
                          float(map_maximum))
                    map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
                    if map_maximum_NaN == False:  # if yes do the calculation
                        ordered_map = order(suitabilities_difficult_terrain_in_restricted_areas_map)
                        maximum_index = int(mapmaximum(ordered_map))
                        self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
                        difference = float(self.demand - self.current_area_occupied_by_LUT)
                        # SH: new code start
                        ordered_maximum_minus_difference = int(
                            maximum_index - difference)  # determines initially the number of cells to be changed (top value)
                        if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                            ordered_allocation_minimum_value = ordered_maximum_minus_difference
                        else:
                            ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
                        new_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
                        number_of_to_be_added_cells = number_of_to_be_added_cells + new_cells
                        new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                                # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                                nominal(self.type_number))
                        only_new_pixels_map = cover(nominal(new_pixels_map), nominal(only_new_pixels_map))
                        # SH: new code end
                        temp_environment_map = cover(new_pixels_map, self.environment_map)
                        self.set_environment(temp_environment_map)
                        # SH: new code start
                        immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                                    boolean(1),
                                                    boolean(immutables_map))
                        area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
                        print('area_after_addition:', area_after_addition)
                        unallocated_demand = self.demand - area_after_addition
                        if area_after_addition == self.demand:
                            print('-> demand was satisfied in difficult terrain in restricted areas => conflict')
                    if map_maximum_NaN == True:
                        # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                        sample = self.current_sample_number
                        time_step = self.time_step
                        year = self.year
                        LUT = self.type_number
                        degree_of_limitation = "difficult_terrain_in_restricted_areas"
                        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                                  newline='') as LPB_log_file:
                            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                            writer = csv.writer(LPB_log_file)
                            LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                            writer.writerow(LPB_log_file_data)
                    if map_maximum_NaN == True or area_after_addition != self.demand:
                        print('-> demand could not be satisfied  => trans-regional leakage likely')

        # Note the unallocated demands for the calculation of mean demand and mean unallocated demands in the postmcloop
        if self.type_number == 2:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                    self.time_step]['unallocated_demand']['LUT02'] = unallocated_demand
        if self.type_number == 3:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                    self.time_step]['unallocated_demand']['LUT03'] = unallocated_demand
        if self.type_number == 4:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                    self.time_step]['unallocated_demand']['LUT04'] = unallocated_demand
        if self.type_number == 5:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                    self.time_step]['unallocated_demand']['LUT05'] = unallocated_demand

        return number_of_to_be_added_cells, only_new_pixels_map, immutables_map


    # SH: LPB - alternation - cascade worst case allocation
    def _add_worst_case_scenario(self, immutables_map):
        """ Takes the total suitability map and subtracts three masks for each step demand can be allocated:
        - only truly inaccessible
        - favorable terrain landscape wide
        - difficult terrain landscape wide
        """

        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                            degree_of_limitation='difficult_landscape_wide')

        ########################

        # initialize the variables to be returned
        number_of_to_be_added_cells = 0
        only_new_pixels_map = spatial(scalar(0))

        # initialize the cascade variable
        area_after_addition = 0

        # initalize the tracking variable
        unallocated_demand = self.demand

        print('\nallocation of LUT', self.type_number, 'of demand:', self.demand, Parameters.get_pixel_size())

        # INITIALIZATION:
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='only_truly_inaccessible')

        # exclude the inaccessible land use area
        suitabilities_only_inaccessible_excluded_map = ifthen(pcrnot(self.inaccessible_mask_map),
                                                              scalar(self.total_suitability_map))

        # JV: remove cells from immutables_map (already changed)
        suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                      scalar(suitabilities_only_inaccessible_excluded_map))

        # ALLOCATION 1
        print('allocating in favorable terrain landscape wide')
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='favorable_landscape_wide')

        # JV: remove cells already occupied by this land use
        suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                     suitabilities_without_immutables_map)

        # get the adjusted map
        suitabilities_favorable_terrain_landscape_wide_map = ifthen(
            pcrnot(self.favorable_terrain_landscape_wide_mask_map),
            scalar(suitabilities_without_own_cells_map))

        # JV: Determine maximum suitability and allocate new cells there
        map_maximum = float(mapmaximum(suitabilities_favorable_terrain_landscape_wide_map))
        print('map_maximum (maximum suitability in suitabilities_favorable_terrain_landscape_wide_map) =',
              float(map_maximum))
        map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
        if map_maximum_NaN == False:  # if yes do the calculation
            ordered_map = order(suitabilities_favorable_terrain_landscape_wide_map)
            maximum_index = int(mapmaximum(ordered_map))
            self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
            difference = float(self.demand - self.current_area_occupied_by_LUT)
            # SH: new code start
            ordered_maximum_minus_difference = int(
                maximum_index - difference)  # determines initially the number of cells to be changed (top value)
            if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                ordered_allocation_minimum_value = ordered_maximum_minus_difference
            else:
                ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
            number_of_to_be_added_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
            only_new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                         # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                         nominal(self.type_number))
            # SH: new code end
            temp_environment_map = cover(only_new_pixels_map, self.environment_map)
            self.set_environment(temp_environment_map)
            # SH: new code start
            immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                        boolean(1),
                                        boolean(immutables_map))
            area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
            unallocated_demand = self.demand - area_after_addition
            if area_after_addition >= self.demand:
                print(
                    '-> demand was satisfied in available favorable landscape area, no allocation in difficult terrain')
        if map_maximum_NaN == True:
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            degree_of_limitation = "favorable_terrain_landscape_wide"
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                writer.writerow(LPB_log_file_data)
        if map_maximum_NaN == True or area_after_addition != self.demand:
            # ALLOCATION 2
            print('allocating in difficult terrain landscape wide')
            # trigger the method so that the according map for the type gets updated
            self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                             degree_of_limitation='difficult_landscape_wide')

            # JV: remove cells from immutables_map (already changed)
            suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                          scalar(suitabilities_only_inaccessible_excluded_map))

            # JV: remove cells already occupied by this land use
            suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                         suitabilities_without_immutables_map)

            # get the adjusted map
            suitabilities_difficult_terrain_landscape_wide_map = ifthen(
                pcrnot(self.difficult_terrain_landscape_wide_mask_map),
                scalar(suitabilities_without_own_cells_map))

            # JV: Determine maximum suitability and allocate new cells there
            map_maximum = float(mapmaximum(suitabilities_difficult_terrain_landscape_wide_map))
            print('map_maximum (maximum suitability in suitabilities_difficult_terrain_in_unrestricted_areas_map) =',
                  float(map_maximum))
            ordered_map = order(suitabilities_difficult_terrain_landscape_wide_map)
            maximum_index = int(mapmaximum(ordered_map))
            self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(self.environment_map)
            difference = float(self.demand - self.current_area_occupied_by_LUT)
            # SH: new code start
            ordered_maximum_minus_difference = int(
                maximum_index - difference)  # determines initially the number of cells to be changed (top value)
            if ordered_maximum_minus_difference > 0:  # determines bottom value of range
                ordered_allocation_minimum_value = ordered_maximum_minus_difference
            else:
                ordered_allocation_minimum_value = 1  # only the number of cells that can be allocated determines the minimum
            new_cells = int(abs(maximum_index - ordered_allocation_minimum_value))
            number_of_to_be_added_cells = number_of_to_be_added_cells + new_cells
            new_pixels_map = ifthen(ordered_map > scalar(ordered_allocation_minimum_value),
                                    # THE DIFFERENCE TO PLUC: CHANGE ALL THE CELLS IN ONE STEP
                                    nominal(self.type_number))
            only_new_pixels_map = cover(scalar(new_pixels_map), scalar(only_new_pixels_map))
            # SH: new code end
            temp_environment_map = cover(new_pixels_map, self.environment_map)
            self.set_environment(temp_environment_map)
            # SH: new code start
            immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                        boolean(1),
                                        boolean(immutables_map))
            area_after_addition = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
            unallocated_demand = self.demand - area_after_addition
            if area_after_addition >= self.demand:
                print('-> demand was satisfied in available difficult landscape area')
            else:
                print('-> demand could not be satisfied in available landscape area, trans-regional leakage likely')

        # Note the unallocated demands for the calculation of mean demand and mean unallocated demands in the postmcloop
        if self.type_number == 2:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT02'] = unallocated_demand
        if self.type_number == 3:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT03'] = unallocated_demand
        if self.type_number == 4:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT04'] = unallocated_demand
        if self.type_number == 5:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT05'] = unallocated_demand

        return number_of_to_be_added_cells, only_new_pixels_map, immutables_map


    # SH: LPB alternation - define the singular abandoned land use types
    def _remove(self, temporal_succession_age_map):
        """ JV: remove cells of this land use type until demand is full filled."""
        # JV: Only cells already occupied by this land use can be removed
        # SH: LPB alternation: declare the singular LUTs cells with lowest suitability with the according abandoned LUT if demand is lower than current area occupied.
        """ abandoned agriculture LUTs are:
        LUT14 = 'cropland-annual - - abandoned'
        LUT15 = 'pasture - - abandoned'
        LUT16 = 'agroforestry - - abandoned' """

        # ORIGINAL PLUC
        self.LUT_specific_suitability_map = ifthen(self.environment_map == self.type_number, self.total_suitability_map)
        ordered_map = order(self.LUT_specific_suitability_map)
        map_minimum = mapminimum(self.LUT_specific_suitability_map)
        print('start map_minimum (minimum suitability in the total suitability map)=', float(map_minimum))
        difference = float(self.current_area_occupied_by_LUT - self.demand)
        # LPB alternation:
        minimum_index = int(mapminimum(ordered_map))
        ordered_minimum_plus_difference = int(minimum_index + difference)
        number_of_to_be_subtracted_cells = int(abs(minimum_index - difference))
        if self.type_number == 2:  # LUT02 = cropland-annual
            temporal_environment_map = ifthen(ordered_map < ordered_minimum_plus_difference,
                                              nominal(14))  # turns into cropland-annual - - abandoned
            temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(14),
                                             scalar(1)) # initiate the pixels for succession
            temporal_succession_age_map = cover(scalar(temp_succession_age_map), scalar(temporal_succession_age_map))
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        elif self.type_number == 3:  # LUT03 = pasture
            temporal_environment_map = ifthen(ordered_map < ordered_minimum_plus_difference,
                                              nominal(15))  # turns into pasture - - abandoned
            temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(15),
                                             scalar(1)) # initiate the pixels for succession
            temporal_succession_age_map = cover(scalar(temp_succession_age_map), scalar(temporal_succession_age_map))
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        elif self.type_number == 4:  # LUT04 = agroforestry
            temporal_environment_map = ifthen(ordered_map < ordered_minimum_plus_difference,
                                              nominal(16))  # turns into agroforestry - - abandoned
            temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(16),
                                             scalar(1)) # initiate the pixels for succession
            temporal_succession_age_map = cover(scalar(temp_succession_age_map), scalar(temporal_succession_age_map))
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        self.set_environment(temp_environment_map)
        area_after_subtraction = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
        print('end result of area occupied by LUT', self.type_number, 'after abandoning area of',
              int(number_of_to_be_subtracted_cells), Parameters.get_pixel_size(), 'is:',
              area_after_subtraction, Parameters.get_pixel_size())

        return temporal_succession_age_map

    # SH for ML:
    # model stage 3
    def _add_with_yield_BAU_scenario(self, immutables_map):
        """ JV: add cells of this land use type until demand is full filled.
        SH: Takes the total suitability mask and subtracts masks for each step demand can be allocated:
                - Initialization: subtract only truly inaccessible and immutables from total suitability
                - Allocation 1: minus current occupied cells in favorable terrain unrestricted
                - Allocation 2: minus current occupied cells in difficult terrain unrestricted - if demand could not be satisfied prior
                - Allocation 3: minus current occupied cells in favorable restricted - if demand could not be satisfied prior
                - Allocation 4: minus current occupied cells in difficult restricted - if demand could not be satisfied prior
        """

        # initialize the variables to be returned
        number_of_to_be_added_cells = 0
        only_new_pixels_map = None

        # initialize the cascade variable
        yield_after_addition = 0

        # initialize the tracking variable
        unallocated_demand = self.demand

        print('\nallocation of LUT', self.type_number, 'of demand:', self.demand, 'in yield units')

        # INITIALIZATION:
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='only_truly_inaccessible')

        # exclude the inaccessible land use area
        suitabilities_only_inaccessible_excluded_map = ifthen(pcrnot(self.inaccessible_mask_map),
                                                              scalar(self.total_suitability_map))

        # JV: remove cells from immutables_map (already changed)
        suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                      scalar(suitabilities_only_inaccessible_excluded_map))

        # ALLOCATION 1
        print('allocating in favorable terrain in unrestricted areas')
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='favorable_terrain_in_unrestricted_areas')

        # JV: remove cells already occupied by this land use
        suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                     suitabilities_without_immutables_map)

        # get the adjusted map
        suitabilities_favorable_terrain_in_unrestricted_areas_map = ifthen(
            pcrnot(self.favorable_terrain_in_unrestricted_areas_mask_map),
            scalar(suitabilities_without_own_cells_map))

        # JV: Determine maximum suitability and allocate new cells there
        map_maximum = float(mapmaximum(suitabilities_favorable_terrain_in_unrestricted_areas_map))
        print('map_maximum (maximum suitability in suitabilities_favorable_terrain_in_unrestricted_areas_map) =',
              float(map_maximum))
        # SH: code alteration
        map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
        if map_maximum_NaN == False:  # if yes do the calculation
            ordered_map = order(suitabilities_favorable_terrain_in_unrestricted_areas_map)
            maximum_index = int(mapmaximum(ordered_map))
            difference = float(self.demand - self.total_yield)
            threshold = int(maximum_index - difference / self.maximum_yield)
            threshold_previously = maximum_index
            iteration = 0
            temp_environment_map = self.environment_map
            while difference > 0 and threshold_previously > threshold:
                print('cells to add', int(maximum_index - threshold))
                if threshold < 0:
                    print('No space left for LUT', self.type_number, 'in favorable_terrain_in_unrestricted_areas')
                    break
                else:
                    ## JV: The key: cells with maximum suitability are turned into THIS type
                    temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                    temp_environment_map = cover(temporal_environment, self.environment_map)
                    ## JV: Check the yield of the land use type now that more land is occupied
                    self._update_yield(temp_environment_map)
                    iteration += 1
                    threshold_previously = threshold
                    ## Number of cells to be allocated
                    difference = float(self.demand - self.total_yield)
                    threshold -= int(difference / self.maximum_yield)
            self.set_environment(temp_environment_map)
            print('iterations', iteration, 'end yield is', self.total_yield)
            # SH: new code start
            immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                        boolean(1),
                                        boolean(immutables_map))
            yield_after_addition = self.total_yield
            unallocated_demand = self.demand - yield_after_addition
            if yield_after_addition >= self.demand:
                print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                      'was satisfied by', self.total_yield, 'yield units',
                      'in available favorable unrestricted landscape area, no allocation in difficult terrain and no conflict')
        if map_maximum_NaN == True:
            # # TEST
            # report(suitabilities_favorable_terrain_in_unrestricted_areas_map, os.path.join(Filepaths.folder_TEST,
            #                                                                                'suitabilities_favorable_terrain_in_unrestricted_areas_map_S'+str(self.current_sample_number) +
            #                                                                                '_TS' + str(self.time_step) +
            #                                                                                '_Y' + str(self.year) +
            #                                                                                '_LUT' + str(self.type_number) +
            #                                                                                '.map'))
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            degree_of_limitation = "favorable_terrain_in_unrestricted_areas"
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                writer.writerow(LPB_log_file_data)
        # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
        if map_maximum_NaN == True or yield_after_addition < self.demand:
            # ALLOCATION 2
            print('allocating in difficult terrain in unrestricted areas')
            # trigger the method so that the according map for the type gets updated
            self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                             degree_of_limitation='difficult_terrain_in_unrestricted_areas')

            # JV: remove cells from immutables_map (already changed)
            suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                          scalar(suitabilities_only_inaccessible_excluded_map))

            # JV: remove cells already occupied by this land use
            suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                         suitabilities_without_immutables_map)

            # get the adjusted map
            suitabilities_difficult_terrain_in_unrestricted_areas_map = ifthen(
                pcrnot(self.difficult_terrain_in_unrestricted_areas_mask_map),
                scalar(suitabilities_without_own_cells_map))

            # JV: Determine maximum suitability and allocate new cells there
            map_maximum = float(mapmaximum(suitabilities_difficult_terrain_in_unrestricted_areas_map))
            print('map_maximum (maximum suitability in suitabilities_difficult_terrain_in_unrestricted_areas_map) =',
                  float(map_maximum))
            map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
            if map_maximum_NaN == False:  # if yes do the calculation
                ordered_map = order(suitabilities_difficult_terrain_in_unrestricted_areas_map)
                maximum_index = int(mapmaximum(ordered_map))
                difference = float(self.demand - yield_after_addition)
                threshold = int(maximum_index - difference / self.maximum_yield)
                threshold_previously = maximum_index
                iteration = 0
                temp_environment_map = self.environment_map
                while difference > 0 and threshold_previously > threshold:
                    print('cells to add', int(maximum_index - threshold))
                    if threshold < 0:
                        print('No space left for LUT', self.type_number, 'in difficult_terrain_in_unrestricted_areas')
                        break
                    else:
                        ## JV: The key: cells with maximum suitability are turned into THIS type
                        temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                        temp_environment_map = cover(temporal_environment, self.environment_map)
                        ## JV: Check the yield of the land use type now that more land is occupied
                        self._update_yield(temp_environment_map)
                        iteration += 1
                        threshold_previously = threshold
                        ## Number of cells to be allocated
                        difference = float(self.demand - self.total_yield)
                        threshold -= int(difference / self.maximum_yield)
                self.set_environment(temp_environment_map)
                print('iterations', iteration, 'end yield is', self.total_yield)
                # SH: new code start
                immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                            boolean(1),
                                            boolean(immutables_map))
                yield_after_addition = self.total_yield
                unallocated_demand = self.demand - yield_after_addition
                if yield_after_addition >= self.demand:
                    print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                      'was satisfied by', self.total_yield, 'yield units',
                        'demand was satisfied in available difficult unrestricted landscape area, no conflict')
            if map_maximum_NaN == True:
                # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                sample = self.current_sample_number
                time_step = self.time_step
                year = self.year
                LUT = self.type_number
                degree_of_limitation = "difficult_terrain_in_unrestricted_areas"
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                          newline='') as LPB_log_file:
                    # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                    writer = csv.writer(LPB_log_file)
                    LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                    writer.writerow(LPB_log_file_data)
            # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
            if map_maximum_NaN == True or yield_after_addition < self.demand:
                # ALLOCATION 3
                print('allocating in favorable terrain in restricted areas')
                # trigger the method so that the according map for the type gets updated
                self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                                 degree_of_limitation='favorable_terrain_in_restricted_areas')

                # JV: remove cells from immutables_map (already changed)
                suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                              scalar(suitabilities_only_inaccessible_excluded_map))

                # JV: remove cells already occupied by this land use
                suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                             suitabilities_without_immutables_map)

                # get the adjusted map
                suitabilities_favorable_terrain_in_restricted_areas_map = ifthen(
                    pcrnot(self.favorable_terrain_in_restricted_areas_mask_map),
                    scalar(suitabilities_without_own_cells_map))

                # JV: Determine maximum suitability and allocate new cells there
                map_maximum = float(mapmaximum(suitabilities_favorable_terrain_in_restricted_areas_map))
                print('map_maximum (maximum suitability in suitabilities_favorable_terrain_in_restricted_areas_map) =',
                      float(map_maximum))
                map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
                if map_maximum_NaN == False:  # if yes do the calculation
                    ordered_map = order(suitabilities_favorable_terrain_in_restricted_areas_map)
                    maximum_index = int(mapmaximum(ordered_map))
                    difference = float(self.demand - yield_after_addition)
                    threshold = int(maximum_index - difference / self.maximum_yield)
                    threshold_previously = maximum_index
                    iteration = 0
                    temp_environment_map = self.environment_map
                    while difference > 0 and threshold_previously > threshold:
                        print('cells to add', int(maximum_index - threshold))
                        if threshold < 0:
                            print('No space left for LUT', self.type_number, 'in favorable_terrain_in_restricted_areas')
                            break
                        else:
                            ## JV: The key: cells with maximum suitability are turned into THIS type
                            temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                            temp_environment_map = cover(temporal_environment, self.environment_map)
                            ## JV: Check the yield of the land use type now that more land is occupied
                            self._update_yield(temp_environment_map)
                            iteration += 1
                            threshold_previously = threshold
                            ## Number of cells to be allocated
                            difference = float(self.demand - self.total_yield)
                            threshold -= int(difference / self.maximum_yield)
                    self.set_environment(temp_environment_map)
                    print('iterations', iteration, 'end yield is', self.total_yield)
                    # SH: new code start
                    immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                                boolean(1),
                                                boolean(immutables_map))
                    yield_after_addition = self.total_yield
                    unallocated_demand = self.demand - yield_after_addition
                    if yield_after_addition >= self.demand:
                        print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                      'was satisfied by', self.total_yield, 'yield units',
                            'demand was satisfied in favorable terrain in restricted areas => conflict')
                if map_maximum_NaN == True:
                    # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                    sample = self.current_sample_number
                    time_step = self.time_step
                    year = self.year
                    LUT = self.type_number
                    degree_of_limitation = "favorable_terrain_in_restricted_areas"
                    with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                              newline='') as LPB_log_file:
                        # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                        writer = csv.writer(LPB_log_file)
                        LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                        writer.writerow(LPB_log_file_data)
                # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
                if map_maximum_NaN == True or yield_after_addition < self.demand:
                    # ALLOCATION 4
                    print('allocating in difficult terrain in restricted areas')
                    # trigger the method so that the according map for the type gets updated
                    self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                                     degree_of_limitation='difficult_terrain_in_restricted_areas')

                    # JV: remove cells from immutables_map (already changed)
                    suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                                  scalar(suitabilities_only_inaccessible_excluded_map))

                    # JV: remove cells already occupied by this land use
                    suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                                 suitabilities_without_immutables_map)

                    # get the adjusted map
                    suitabilities_difficult_terrain_in_restricted_areas_map = ifthen(
                        pcrnot(self.difficult_terrain_in_restricted_areas_mask_map),
                        scalar(suitabilities_without_own_cells_map))

                    # JV: Determine maximum suitability and allocate new cells there
                    map_maximum = float(mapmaximum(suitabilities_difficult_terrain_in_restricted_areas_map))
                    print(
                        'map_maximum (maximum suitability in suitabilities_difficult_terrain_in_restricted_areas_map) =',
                        float(map_maximum))
                    map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
                    if map_maximum_NaN == False:  # if yes do the calculation
                        ordered_map = order(suitabilities_difficult_terrain_in_restricted_areas_map)
                        maximum_index = int(mapmaximum(ordered_map))
                        difference = float(self.demand - yield_after_addition)
                        threshold = int(maximum_index - difference / self.maximum_yield)
                        threshold_previously = maximum_index
                        iteration = 0
                        temp_environment_map = self.environment_map
                        while difference > 0 and threshold_previously > threshold:
                            print('cells to add', int(maximum_index - threshold))
                            if threshold < 0:
                                print('No space left for LUT', self.type_number, 'in difficult_terrain_in_restricted_areas')
                                break
                            else:
                                ## JV: The key: cells with maximum suitability are turned into THIS type
                                temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                                temp_environment_map = cover(temporal_environment, self.environment_map)
                                ## JV: Check the yield of the land use type now that more land is occupied
                                self._update_yield(temp_environment_map)
                                iteration += 1
                                threshold_previously = threshold
                                ## Number of cells to be allocated
                                difference = float(self.demand - self.total_yield)
                                threshold -= int(difference / self.maximum_yield)
                        self.set_environment(temp_environment_map)
                        print('iterations', iteration, 'end yield is', self.total_yield)
                        # SH: new code start
                        immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                                    boolean(1),
                                                    boolean(immutables_map))
                        yield_after_addition = self.total_yield
                        unallocated_demand = self.demand - yield_after_addition
                        if yield_after_addition >= self.demand:
                            print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                      'was satisfied by', self.total_yield, 'yield units','demand was satisfied in difficult terrain in restricted areas => conflict')
                    if map_maximum_NaN == True:
                        # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                        sample = self.current_sample_number
                        time_step = self.time_step
                        year = self.year
                        LUT = self.type_number
                        degree_of_limitation = "difficult_terrain_in_restricted_areas"
                        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                                  newline='') as LPB_log_file:
                            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                            writer = csv.writer(LPB_log_file)
                            LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                            writer.writerow(LPB_log_file_data)
                    if map_maximum_NaN == True or yield_after_addition < self.demand:
                        print('-> demand could not be satisfied  => trans-regional leakage likely')

        area_after_addition = int(maptotal(scalar(boolean(scalar(self.environment_map) == self.type_number))))
        print('end result of area occupied by LUT', self.type_number, 'after (partial) allocation of demand of',
              self.demand, 'is:', area_after_addition, Parameters.get_pixel_size())

        if yield_after_addition < self.demand:
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Unallocated_demand_in_yield_units']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            unallocated_demand = self.demand - yield_after_addition
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-unallocated-demand-yield-units_log-file.csv'), 'a',
                                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, unallocated_demand]
                writer.writerow(LPB_log_file_data)

        # Export the new yield map for documentation and MC average production and later use, e.g. in OC
        if probabilistic_output_options_dictionary['yield_maps'] == True:
            # store output
            time_step = self.time_step
            if self.type_number == 2 and 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L2yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT02_cropland_annual_crop_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L2yi to: ',
                      Filepaths.folder_LUT02_cropland_annual_crop_yields)
            if self.type_number == 3 and 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L3yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT03_pasture_livestock_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L3yi to: ',
                      Filepaths.folder_LUT03_pasture_livestock_yields)
            if self.type_number == 4 and 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L4yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT04_agroforestry_crop_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L4yi to: ',
                      Filepaths.folder_LUT04_agroforestry_crop_yields)

        # Note the unallocated demands for the calculation of mean demand and mean unallocated demands in the postmcloop
        if self.type_number == 2:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT02'] = unallocated_demand
        if self.type_number == 3:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT03'] = unallocated_demand
        if self.type_number == 4:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT04'] = unallocated_demand
        if self.type_number == 5:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT05'] = unallocated_demand

        return number_of_to_be_added_cells, only_new_pixels_map, immutables_map


    # SH for ML:
    # model stage 3
    def _add_with_yield_worst_case_scenario(self, immutables_map):
        """ Takes the total suitability map and subtracts three masks for each step demand can be allocated:
                - only truly inaccessible
                - favorable terrain landscape wide
                - difficult terrain landscape wide
        """

        # initialize the variables to be returned
        number_of_to_be_added_cells = 0
        only_new_pixels_map = None

        # initialize the cascade variable
        yield_after_addition = 0

        # initialize the tracking variable
        unallocated_demand = self.demand

        print('\nallocation of LUT', self.type_number, 'of demand:', self.demand, 'in yield units')

        # INITIALIZATION:
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                                 degree_of_limitation='only_truly_inaccessible')

        # exclude the inaccessible land use area
        suitabilities_only_inaccessible_excluded_map = ifthen(pcrnot(self.inaccessible_mask_map),
                                                                      scalar(self.total_suitability_map))

        # JV: remove cells from immutables_map (already changed)
        suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                              scalar(suitabilities_only_inaccessible_excluded_map))

        # ALLOCATION 1
        print('allocating in favorable terrain landscape wide')
        # trigger the method so that the according map for the type gets updated
        self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                         degree_of_limitation='favorable_landscape_wide')

        # JV: remove cells already occupied by this land use
        suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                     suitabilities_without_immutables_map)

        # get the adjusted map
        suitabilities_favorable_terrain_landscape_wide_map = ifthen(
            pcrnot(self.favorable_terrain_landscape_wide_mask_map),
            scalar(suitabilities_without_own_cells_map))

        # JV: Determine maximum suitability and allocate new cells there
        map_maximum = float(mapmaximum(suitabilities_favorable_terrain_landscape_wide_map))
        print('map_maximum (maximum suitability in suitabilities_favorable_terrain_landscape_wide_map) =',
              float(map_maximum))
        # SH: code alteration
        map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
        if map_maximum_NaN == False:  # if yes do the calculation
            ordered_map = order(suitabilities_favorable_terrain_landscape_wide_map)
            maximum_index = int(mapmaximum(ordered_map))
            difference = float(self.demand - self.total_yield)
            threshold = int(maximum_index - difference / self.maximum_yield)
            threshold_previously = maximum_index
            iteration = 0
            temp_environment_map = self.environment_map
            while difference > 0 and threshold_previously > threshold:
                print('cells to add', int(maximum_index - threshold))
                if threshold < 0:
                    print('No space left for LUT', self.type_number, 'in favorable_terrain_landscape_wide')
                    break
                else:
                    ## JV: The key: cells with maximum suitability are turned into THIS type
                    temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                    temp_environment_map = cover(temporal_environment, self.environment_map)
                    ## JV: Check the yield of the land use type now that more land is occupied
                    self._update_yield(temp_environment_map)
                    iteration += 1
                    threshold_previously = threshold
                    ## Number of cells to be allocated
                    difference = float(self.demand - self.total_yield)
                    threshold -= int(difference / self.maximum_yield)
            self.set_environment(temp_environment_map)
            print('iterations', iteration, 'end yield is', self.total_yield)
            # SH: new code start
            immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                        boolean(1),
                                        boolean(immutables_map))
            yield_after_addition = self.total_yield
            unallocated_demand = self.demand - yield_after_addition
            if yield_after_addition >= self.demand:
                print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                      'was satisfied by', self.total_yield, 'yield units',
                      'in available favorable landscape area, no allocation in difficult terrain and no conflict')
        if map_maximum_NaN == True:
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            degree_of_limitation = "favorable_terrain_landscape_wide"
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                writer.writerow(LPB_log_file_data)
        # if no cells are left in the suitability map and demand is not satisfied yet go to the next pool of cells ...
        if map_maximum_NaN == True or yield_after_addition < self.demand:
            # ALLOCATION 2
            print('allocating in difficult terrain landscape wide')
            # trigger the method so that the according map for the type gets updated
            self.determine_areas_of_no_allocation_for_a_type(a_type=self.type_number,
                                                             degree_of_limitation='difficult_landscape_wide')

            # JV: remove cells from immutables_map (already changed)
            suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                          scalar(suitabilities_only_inaccessible_excluded_map))

            # JV: remove cells already occupied by this land use
            suitabilities_without_own_cells_map = ifthen(self.environment_map != self.type_number,
                                                         suitabilities_without_immutables_map)

            # get the adjusted map
            suitabilities_difficult_terrain_landscape_wide_map = ifthen(
                pcrnot(self.difficult_terrain_landscape_wide_mask_map),
                scalar(suitabilities_without_own_cells_map))

            # JV: Determine maximum suitability and allocate new cells there
            map_maximum = float(mapmaximum(suitabilities_difficult_terrain_landscape_wide_map))
            print('map_maximum (maximum suitability in suitabilities_difficult_terrain_landscape_wide_map) =',
                  float(map_maximum))
            map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
            if map_maximum_NaN == False:  # if yes do the calculation
                ordered_map = order(suitabilities_difficult_terrain_landscape_wide_map)
                maximum_index = int(mapmaximum(ordered_map))
                difference = float(self.demand - yield_after_addition)
                threshold = int(maximum_index - difference / self.maximum_yield)
                threshold_previously = maximum_index
                iteration = 0
                temp_environment_map = self.environment_map
                while difference > 0 and threshold_previously > threshold:
                    print('cells to add', int(maximum_index - threshold))
                    if threshold < 0:
                        print('No space left for LUT', self.type_number, 'in difficult_terrain_landscape_wide')
                        break
                    else:
                        ## JV: The key: cells with maximum suitability are turned into THIS type
                        temporal_environment = ifthen(ordered_map > threshold, nominal(self.type_number))
                        temp_environment_map = cover(temporal_environment, self.environment_map)
                        ## JV: Check the yield of the land use type now that more land is occupied
                        self._update_yield(temp_environment_map)
                        iteration += 1
                        threshold_previously = threshold
                        ## Number of cells to be allocated
                        difference = float(self.demand - self.total_yield)
                        threshold -= int(difference / self.maximum_yield)
                self.set_environment(temp_environment_map)
                print('iterations', iteration, 'end yield is', self.total_yield)
                # SH: new code start
                immutables_map = ifthenelse(scalar(temp_environment_map) == scalar(self.type_number),
                                            boolean(1),
                                            boolean(immutables_map))
                yield_after_addition = self.total_yield
                unallocated_demand = self.demand - yield_after_addition
                if yield_after_addition >= self.demand:
                    print('-> demand of', self.demand, 'in yield units by LUT', self.type_number,
                          'was satisfied by', self.total_yield, 'yield units',
                          'demand was satisfied in available difficult landscape area, no conflict')
                else:
                    print('-> demand could not be satisfied in available landscape area, trans-regional leakage likely')
            if map_maximum_NaN == True:
                # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                sample = self.current_sample_number
                time_step = self.time_step
                year = self.year
                LUT = self.type_number
                degree_of_limitation = "difficult_terrain_landscape_wide"
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-nan_log-file.csv'), 'a',
                          newline='') as LPB_log_file:
                    # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                    writer = csv.writer(LPB_log_file)
                    LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                    writer.writerow(LPB_log_file_data)


        area_after_addition = int(maptotal(scalar(boolean(scalar(self.environment_map) == self.type_number))))
        print('end result of area occupied by LUT', self.type_number, 'after (partial) allocation of demand of',
              self.demand, 'is:', area_after_addition, Parameters.get_pixel_size())

        if yield_after_addition < self.demand:
            # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Unallocated_demand_in_yield_units']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            unallocated_demand = self.demand - yield_after_addition
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-unallocated-demand-yield-units_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, LUT, unallocated_demand]
                writer.writerow(LPB_log_file_data)


        # Export the new yield map for documentation and MC average production and later use, e.g. in OC
        if probabilistic_output_options_dictionary['yield_maps'] == True:
            # store output
            time_step = self.time_step
            if self.type_number == 2 and 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L2yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT02_cropland_annual_crop_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L2yi to: ',
                      Filepaths.folder_LUT02_cropland_annual_crop_yields)
            if self.type_number == 3 and 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L3yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT03_pasture_livestock_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L3yi to: ',
                      Filepaths.folder_LUT03_pasture_livestock_yields)
            if self.type_number == 4 and 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L4yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT04_agroforestry_crop_yields,
                                    str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L4yi to: ',
                      Filepaths.folder_LUT04_agroforestry_crop_yields)

        # Note the unallocated demands for the calculation of mean demand and mean unallocated demands in the postmcloop
        if self.type_number == 2:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT02'] = unallocated_demand
        if self.type_number == 3:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT03'] = unallocated_demand
        if self.type_number == 4:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT04'] = unallocated_demand
        if self.type_number == 5:
            dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
                self.time_step]['unallocated_demand']['LUT05'] = unallocated_demand

        return number_of_to_be_added_cells, only_new_pixels_map, immutables_map

# SH for ML:
    # model stage 3
    def _remove_with_yield(self, temporal_succession_age_map):
        """ JV: _remove cells of this land use type until demand is full filled.
        SH: LPB alternation to diversified LUTs and incorporation of succession age map."""

        # ORIGINAL PLUC
        self.LUT_specific_suitability_map = ifthen(self.environment_map == self.type_number, self.total_suitability_map)
        ordered_map = order(self.LUT_specific_suitability_map)
        map_minimum = mapminimum(self.LUT_specific_suitability_map)
        print('start map_minimum (minimum suitability in the total suitability map)=', float(map_minimum))
        initial_yield_demand_difference = float(self.total_yield - self.demand)
        difference = float(self.total_yield - self.demand)
        threshold = int(difference / (self.maximum_yield * 0.8))
        threshold_previously = 0
        iteration = 0
        while difference > 0 and threshold_previously < threshold and iteration < 100:
            print('cells to remove', threshold)
            ## JV: The key: cells with minimum suitability are turned into 'abandoned'
            if self.type_number == 2:  # LUT02 = cropland-annual
                temporal_environment_map = ifthen(ordered_map < threshold,
                                                  nominal(14))  # turns into cropland-annual - - abandoned
                temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(14),
                                                 scalar(1))  # initiate the pixels for succession
                temporal_succession_age_map = cover(scalar(temp_succession_age_map),
                                                    scalar(temporal_succession_age_map))
                temp_environment_map = cover(temporal_environment_map, self.environment_map)
            elif self.type_number == 3:  # LUT03 = pasture
                temporal_environment_map = ifthen(ordered_map < threshold,
                                                  nominal(15))  # turns into pasture - - abandoned
                temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(15),
                                                 scalar(1))  # initiate the pixels for succession
                temporal_succession_age_map = cover(scalar(temp_succession_age_map),
                                                    scalar(temporal_succession_age_map))
                temp_environment_map = cover(temporal_environment_map, self.environment_map)
            elif self.type_number == 4:  # LUT04 = agroforestry
                temporal_environment_map = ifthen(ordered_map < threshold,
                                                  nominal(16))  # turns into agroforestry - - abandoned
                temp_succession_age_map = ifthen(scalar(temporal_environment_map) == scalar(16),
                                                 scalar(1))  # initiate the pixels for succession
                temporal_succession_age_map = cover(scalar(temp_succession_age_map),
                                                    scalar(temporal_succession_age_map))
                temp_environment_map = cover(temporal_environment_map, self.environment_map)

            ## JV: Check the yield of the land use type now that less land is occupied
            self._update_yield(temp_environment_map)
            iteration += 1
            threshold_previously = threshold
            difference = float(self.total_yield - self.demand)
            if math.fmod(iteration, 40) == 0:
                print('NOT getting there...')
                ## Number of cells to be allocated
                threshold = 2 * (threshold + int(difference / self.maximum_yield))
            else:
                ## Number of cells to be allocated
                threshold += int(difference / self.maximum_yield)
        self.set_environment(temp_environment_map)
        print('iterations', iteration, 'end yield is', self.total_yield)
        area_after_subtraction = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
        print('end result of area occupied by LUT', self.type_number, 'after reducing yield of',
              initial_yield_demand_difference, 'is:', area_after_subtraction, Parameters.get_pixel_size())

        # Export the new yield map for documentation and MC average production and later use, e.g. in OC
        if probabilistic_output_options_dictionary['yield_maps'] == True:
            # store output
            time_step = self.time_step
            if self.type_number == 2 and 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L2yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT02_cropland_annual_crop_yields, str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L2yi to: ', Filepaths.folder_LUT02_cropland_annual_crop_yields)
            if self.type_number == 3 and 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L3yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT03_pasture_livestock_yields, str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L3yi to: ', Filepaths.folder_LUT03_pasture_livestock_yields)
            if self.type_number == 4 and 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                pcraster_conform_map_name = 'L4yi'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                    pcraster_conform_map_name, time_step)
                report(scalar(self.current_yield_map),
                       os.path.join(Filepaths.folder_LUT04_agroforestry_crop_yields, str(self.current_sample_number),
                                    output_map_name))
                print('reported self.current_yield_map as L4yi to: ', Filepaths.folder_LUT04_agroforestry_crop_yields)

        return temporal_succession_age_map


###################################################################################################

class LandUse:
    #SH + DK alteration LPB
    def __init__(self,
                 types,
                 initial_environment_map,
                 environment_map,
                 null_mask_map,
                 plantation_age_map,
                 year,
                 spatially_explicit_population_maps_dictionary,
                 climate_period_inputs_dictionary,
                 AGB_annual_increment_ranges_in_Mg_per_ha_dictionary,
                 settlements_map,
                 net_forest_map,
                 dem_map,
                 static_restricted_areas_map,
                 AGB_map,
                 streets_map,
                 cities_map,
                 static_areas_on_which_no_allocation_occurs_map,
                 static_LUTs_on_which_no_allocation_occurs_list,
                 difficult_terrain_slope_restriction_dictionary,
                 LUT02_sampled_distance_for_this_sample,
                 LUT03_sampled_distance_for_this_sample,
                 LUT04_sampled_distance_for_this_sample,
                 external_demands_generated_tss_dictionary):

        """ JV: Construct a land use object with a number of types and an environment.
            SH: Calculate accompanying maps prior and posterior land use change by active land use types."""

        # ORIGINAL PLUC VARIABLES
        self.types = types
        self.number_of_types = len(types)
        print('\nnumber of active land use types is:', self.number_of_types)

        self.environment_map = environment_map
        # JV: List with the land use type OBJECTS
        self.land_use_types = []
        # JV: Map with 0 in study area and No Data outside, used for cover() functions
        self.null_mask_map = scalar(null_mask_map)

        # MODIFIED PLUC VARIABLES
        # general excluded areas are not used in LPB, but kept for other model purposes (filled dynamically)
        self.excluded_areas_from_allocation_map = null_mask_map
        # dem is used in PLUC but added in LandUse in LPB
        self.dem_map = scalar(dem_map)
        self.slope_map = slope(self.dem_map)
        # former indirectly passed variables, that are now needed each time step
        self.static_areas_on_which_no_allocation_occurs_map = static_areas_on_which_no_allocation_occurs_map
        self.static_LUTs_on_which_no_allocation_occurs_list = static_LUTs_on_which_no_allocation_occurs_list
        self.difficult_terrain_slope_restriction_dictionary = difficult_terrain_slope_restriction_dictionary
        self.external_demands_generated_tss_dictionary = external_demands_generated_tss_dictionary
        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'external':
            self.generated_tss_deterministic_demand_footprint = self.external_demands_generated_tss_dictionary['generated_tss_deterministic_demand_footprint']
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
            self.generated_tss_deterministic_demand_yield_units = self.external_demands_generated_tss_dictionary['generated_tss_deterministic_demand_yield_units']
            self.generated_tss_deterministic_maximum_yield = self.external_demands_generated_tss_dictionary['generated_tss_deterministic_maximum_yield']
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
            self.generated_tss_stochastic_demand_yield_units_HIGH = self.external_demands_generated_tss_dictionary['generated_tss_stochastic_demand_yield_units_HIGH']
            self.generated_tss_stochastic_demand_yield_units_LOW = self.external_demands_generated_tss_dictionary['generated_tss_stochastic_demand_yield_units_LOW']
            self.generated_tss_stochastic_maximum_yield = self.external_demands_generated_tss_dictionary['generated_tss_stochastic_maximum_yield']


        # SH: LPB ADDITIONAL VARIABLES
        total_number_of_land_use_types = Parameters.get_total_number_of_land_use_types()
        print('total number of land use types is:', total_number_of_land_use_types)
        # management variables
        self.time_step = None
        self.current_sample_number = None
        self.year = year
        # initial environment
        self.initial_environment_map = initial_environment_map
        # population variables
        self.spatially_explicit_population_maps_dictionary = spatially_explicit_population_maps_dictionary
        self.population_map = None
        self.population = None
        self.settlements_map = settlements_map
        # stochastic distances for samples
        self.LUT02_sampled_distance_for_this_sample = LUT02_sampled_distance_for_this_sample
        self.LUT03_sampled_distance_for_this_sample = LUT03_sampled_distance_for_this_sample
        self.LUT04_sampled_distance_for_this_sample = LUT04_sampled_distance_for_this_sample

        # the restricted areas are used in LPB for simulation of forest land use conflict in a second allocation of demand
        self.static_restricted_areas_map = cover(boolean(static_restricted_areas_map), boolean(self.null_mask_map))
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            # the initial plantation age map serves for the derivation of the initial plantation rotation period end map
            self.initial_plantation_age_map = readmap(Filepaths.file_initial_plantation_age_input)
            # Variate the oldest plantation age if user required:
            if Parameters.get_plantation_age_stochastic_alteration() == True:
                # plantation_age_without_zeros_map
                pure_plantation_age_map = ifthen(scalar(self.initial_plantation_age_map) > scalar(0),
                                                 scalar(self.initial_plantation_age_map))
                # find the earliest date in the map
                minimum_in_plantation_age_map = int(mapminimum(scalar(pure_plantation_age_map)))

                # map it
                to_be_varied_plantation_age_map = ifthen(scalar(pure_plantation_age_map) == scalar(minimum_in_plantation_age_map),
                                                         scalar(1))

                # code a stochastic variation with the rotation period:
                ncols = clone().nrCols()
                nrows = clone().nrRows()
                np_array = Parameters.get_rng().integers(
                    low=(minimum_in_plantation_age_map - Parameters.get_mean_plantation_rotation_period_end()),
                    high=minimum_in_plantation_age_map,
                    size=(nrows, ncols))
                numpy2pcr(pcraster.Scalar, np_array, 9999)
                a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

                # set the substitute in the original map
                self.initial_plantation_age_map = ifthenelse(scalar(self.initial_plantation_age_map) == scalar(minimum_in_plantation_age_map),
                                                             scalar(a_map),
                                                             scalar(self.initial_plantation_age_map))
            # initialize the plantation rotation period based on the initial plantation age input
            self.plantation_rotation_period_end_map = ifthenelse(self.initial_plantation_age_map > scalar(0),
                                                                 self.initial_plantation_age_map + Parameters.get_mean_plantation_rotation_period_end(),
                                                                 scalar(self.null_mask_map))

            if Parameters.get_plantation_age_stochastic_alteration() == True:
                # correct it to the substituted varied information, multiply plantion period by 2, so that all plantations will be simulated as harvested:
                plantation_rotation_period_end_map_varied = ifthen(scalar(to_be_varied_plantation_age_map) == scalar(1),
                                                                   scalar(self.initial_plantation_age_map) + (2 * Parameters.get_mean_plantation_rotation_period_end()))
                self.plantation_rotation_period_end_map = cover(scalar(plantation_rotation_period_end_map_varied),
                                                                scalar(self.plantation_rotation_period_end_map))

            # the plantation age map tracks the cells per year, if overlap between plantation_age_map and plantation_rotation_period_end_map harvest is conducted
            self.plantation_age_map = plantation_age_map # identical to initial_plantation_age_map
            self.plantation_age_map = ifthenelse(scalar(self.plantation_age_map) > scalar(0),
                                                 scalar(self.year), # initialization of simulation year start count-up
                                                 scalar(self.null_mask_map))
        if Parameters.get_model_scenario() == 'no_conservation':

            self.plantation_age_map = ifthenelse(scalar(self.environment_map) == scalar(5),
                                                 scalar(self.year),
                                                 scalar(self.null_mask_map))

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().integers(low=self.year - Parameters.get_mean_plantation_rotation_period_end(), high=self.year, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            self.plantation_rotation_period_end_map = ifthenelse(self.plantation_age_map > 0,
                                                                 a_map + Parameters.get_mean_plantation_rotation_period_end(),
                                                                 scalar(self.null_mask_map))

        self.new_plantations_deforested_map = None
        self.new_plantations_map = None

        # environment variables:
        # the climate variables determine where and how forest growths, in model stage 3 additionally yield potentials in the yield approach
        self.climate_period_inputs_dictionary = climate_period_inputs_dictionary
        # if no spatially-explicit varaibles are available use stochastic modelling with the given potential ranges for the annual increment
        self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary = AGB_annual_increment_ranges_in_Mg_per_ha_dictionary
        # net forest is forest area according to national maps
        self.net_forest_map = net_forest_map
        # Succession age map initialization:
        # Herbaceous vegetation:
        initial_herbaceous_vegetation_map = ifthenelse(self.environment_map == 6,  # extract herbaceous vegetation
                                                       scalar(1),
                                                       scalar(self.null_mask_map))
        ncols = clone().nrCols()
        nrows = clone().nrRows()
        maximum_age = Parameters.get_maximum_age_herbaceous_vegetation()
        np_array = Parameters.get_rng().integers(int(maximum_age), size=(nrows, ncols))
        numpy2pcr(pcraster.Scalar, np_array, 9999)
        a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)
        herbaceous_vegetation_age_map = ifthenelse(initial_herbaceous_vegetation_map == 1,
                                                   scalar(a_map),
                                                   scalar(self.null_mask_map))

        # Shrubs
        initial_shrubs_map = ifthenelse(self.environment_map == 7,  # extract shrubs
                                        scalar(1),  # or TMF 36
                                        scalar(self.null_mask_map))
        ncols = clone().nrCols()
        nrows = clone().nrRows()
        maximum_age = Parameters.get_maximum_age_shrubs()
        np_array = Parameters.get_rng().integers(int(maximum_age), size=(nrows, ncols))
        numpy2pcr(pcraster.Scalar, np_array, 9999)
        a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)
        shrubs_age_map = ifthenelse(initial_shrubs_map == 1,
                                    scalar(a_map),
                                    scalar(self.null_mask_map))

        # disturbed forest
        initial_disturbed_forest_map = ifthenelse(self.environment_map == 8,  # extract disturbed forest
                                         scalar(1),
                                         scalar(self.null_mask_map))
        ncols = clone().nrCols()
        nrows = clone().nrRows()
        maximum_age = Parameters.get_maximum_age_forest()
        np_array = Parameters.get_rng().integers(int(maximum_age), size=(nrows, ncols))
        numpy2pcr(pcraster.Scalar, np_array, 9999)
        a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)
        disturbed_forest_age_map = ifthenelse(initial_disturbed_forest_map == 1,
                                              scalar(a_map),
                                              scalar(self.null_mask_map))

        # undisturbed forest
        maximum_age = Parameters.get_maximum_age_forest()
        undisturbed_forest_age_map = ifthenelse(self.environment_map == 9,  # extract undisturbed forest
                                                scalar(maximum_age),
                                                scalar(self.null_mask_map))

        self.succession_age_map = ifthenelse(herbaceous_vegetation_age_map == 0,
                                             scalar(shrubs_age_map),
                                             scalar(herbaceous_vegetation_age_map))
        self.succession_age_map = ifthenelse(self.succession_age_map == 0,
                                             scalar(disturbed_forest_age_map),
                                             scalar(self.succession_age_map))
        self.succession_age_map = ifthenelse(self.succession_age_map == 0,
                                             scalar(undisturbed_forest_age_map),
                                             scalar(self.succession_age_map))  # all 4 combined, starting counting

        self.AGB_map = scalar(AGB_map)

        # correct the initial AGB_map: AGB shall be only calculated where forest types are located.
        # Define which land use types depict gross forest in Parameters.py
        gross_forest_LUTs_list = Parameters.get_gross_forest_LUTs_list()

        gross_forest_types_map = self.null_mask_map
        for a_LUT in gross_forest_LUTs_list:
            gross_forest_types_map = ifthenelse(scalar(initial_environment_map) == scalar(a_LUT),
                                                scalar(1),
                                                scalar(gross_forest_types_map))

        self.AGB_map = ifthenelse(scalar(gross_forest_types_map) == scalar(1),
                                  scalar(self.AGB_map),
                                  scalar(self.null_mask_map))

        self.initial_AGB_map = scalar(self.AGB_map)

        self.local_demand_AGB_remaining = 0
        self.demand_AGB_remaining = 0

        self.streets_map = streets_map

        self.cities_map = cities_map



    """The incorporated methods are given in the chronological order as they are used in dynamic"""

    # METHODS RUN PRE ALLOCATION:

    # DK: LPB alternation - MANAGEMENT
    def update_time_step_and_sample_number_and_year(self, time_step, current_sample_number, year):
        """ Make LandUseChangeModel variables available for calculations. """
        self.time_step = time_step
        self.current_sample_number = current_sample_number
        self.year = year
        for a_type in self.land_use_types:
            a_type.update_time_step_and_sample_number_and_year(time_step, current_sample_number, year)

    # SH: LPB alternation - save the environment for calculations in the new time step
    def update_environment_map_last_time_step(self):
        if self.time_step == 1:
            self.environment_map_last_timestep = self.initial_environment_map
        else:
            self.environment_map_last_timestep = self.environment_map
        print('updating environment_map_last_timestep done')

    # SH: LPB alternation - SUCCESSION
    def update_succession_age_map(self):
        """ Add one year of age to the existing succession pixels. """
        if self.time_step == 1:
            # only collect abandoned cells that might have been produced in the correction step, otherwise display initial starting year conditions
            abandoned_LUTs = [14, 15, 16]
            for a_LUT in abandoned_LUTs:
                temp_succession_age_map = ifthen(scalar(self.environment_map) == scalar(a_LUT),
                                             scalar(1))  # initiate the pixels for succession
                self.succession_age_map = cover(scalar(temp_succession_age_map), scalar(self.succession_age_map))
        else:
            self.succession_age_map = ifthenelse(scalar(self.succession_age_map) > scalar(0),
                                                 scalar(self.succession_age_map) + scalar(1), # we add 1 year of age to all cells that are subject to forest succession
                                                 scalar(self.null_mask_map))
            print('updated succession age map')

    # SH: LPB alternation - DYNAMIC LINEAR POPULATION DEVELOPMENT
    def update_population(self):
        """ Calculate the spatially explicit population and total number of persons for the time step. """
        # Preparation
        if self.year == Parameters.get_initial_simulation_year():
            pass
        else:
            self.population_last_time_step = self.population  # fill the variable before the new population is calculated

        # DYNAMIC LINEAR POPULATION DEVELOPMENT
        # create yearly population maps from decadal input projections (not in advance, but for the simulated year)
        print('creating the missing initial population file by calculation of linear development between gridded data points if needed ...')

        # First Step: get the last number of the year:
        year_string = str(self.year)

        calculation_start_map = self.null_mask_map
        calculation_end_map = self.null_mask_map

        # Second Step:
        if year_string[-1] == str(0):
            # for the decadal gridded data points take the original input files
            if self.year == 2010:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2010_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2020:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2020_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2030:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2030_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2040:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2040_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2050:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2050_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2060:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2060_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2070:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2070_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2080:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2080_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2090:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2090_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
            elif self.year == 2100:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2100_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)

        # for all other years draw the according input data
        elif year_string[-1] != str(0):
            # to calculate the missing years determine first the gridded data points for the calculation for each year
            if self.year >= 2010 and self.year <= 2019:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2010_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2020_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2021 and self.year <= 2029:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2020_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2030_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2031 and self.year <= 2039:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2030_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2040_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2041 and self.year <= 2049:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2040_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2050_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2051 and self.year <= 2059:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2050_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2060_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2061 and self.year <= 2069:
                input_calculation_start_map =self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2060_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2070_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2071 and self.year <= 2079:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2070_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2080_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2081 and self.year <= 2089:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2080_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2090_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))
            elif self.year >= 2091 and self.year <= 2099:
                input_calculation_start_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2090_input']
                calculation_start_map = cover(input_calculation_start_map, scalar(self.null_mask_map))
                input_calculation_end_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2100_input']
                calculation_end_map = cover(input_calculation_end_map, scalar(self.null_mask_map))

            # note the calculation start and end point coordinates
            calculation_start_year = 0
            calculation_end_year = 0
            if self.year < 2020:
                calculation_start_year = 2010
                calculation_end_year = 2020
            elif self.year >2020 and self.year < 2030:
                calculation_start_year = 2020
                calculation_end_year = 2030
            elif self.year >2030 and self.year < 2040:
                calculation_start_year = 2030
                calculation_end_year = 2040
            elif self.year >2040 and self.year < 2050:
                calculation_start_year = 2040
                calculation_end_year = 2050
            elif self.year >2050 and self.year < 2060:
                calculation_start_year = 2050
                calculation_end_year = 2060
            elif self.year >2060 and self.year < 2070:
                calculation_start_year = 2060
                calculation_end_year = 2070
            elif self.year >2070 and self.year < 2080:
                calculation_start_year = 2070
                calculation_end_year = 2080
            elif self.year >2080 and self.year < 2090:
                calculation_start_year = 2080
                calculation_end_year = 2090
            elif self.year >2090 and self.year < 2100:
                calculation_start_year = 2090
                calculation_end_year = 2100


            # Third step: calculate the actual annual change

            # linear interpolation
            # y = y1+(((x-x1)/(x2-x1))*(y2-y1))

            # y = population at self.year i (searched)
            # x = self.year (known)
            # x1 = calculation start year (known)
            # x2 = calculation end year (known)
            # y1 = cell value calculation start map (known)
            # y2 = cell value calculation end map (known)

            self.population_map = calculation_start_map + (((self.year - calculation_start_year) / (calculation_end_year - calculation_start_year)) * (calculation_end_map - calculation_start_map))
            # for further calculations round up to a full person
            self.population = math.ceil(maptotal(self.population_map))
            print('year:', self.year, 'population:', self.population)


        # to get the population peak in the log files printed, note each year and let it search before closing the file for the maximum population and according year
        if self.year == Parameters.get_initial_simulation_year():
            self.population_per_year_list = []
            self.population_per_year_tuple = (self.year, self.population)
            self.population_per_year_list.append(self.population_per_year_tuple)
        else:
            self.population_per_year_tuple = (self.year, self.population)
            self.population_per_year_list.append(self.population_per_year_tuple)

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'populus'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
        report(self.population_map,
                   os.path.join(Filepaths.folder_dynamic_population_deterministic, output_map_name))

        return self.population, self.population_map, self.population_per_year_list

    # SH: LPB alternation - DYNAMIC SETTLEMENTS
    def update_settlements(self):
        """ Calculate new settlements based on population development. Once created, they are a final LUT built-up pixel. """

        # create new settlements according to population development after the first time step
        if self.time_step == 1:
            self.settlements_map = self.settlements_map
            self.settlements = int(maptotal(scalar(self.settlements_map)))
            self.settlements_last_time_step = self.settlements
        else:
            self.settlements_map_last_timestep = self.settlements_map

            only_one_new_settlement_per_year, required_households_for_a_new_settlement_threshold = Parameters.get_dynamic_settlements_simulation_decision()

            if self.population > self.population_last_time_step:
                # first make sure existing settlements with their draw area are excluded
                spread_map = spreadmaxzone(boolean(self.settlements_map), 0, 1, Parameters.get_regional_mean_impact_of_settlements_distance_in_m())
                existing_settlements_buffer_map = ifthenelse(scalar(spread_map) > scalar(0),
                                                             boolean(1),
                                                             boolean(self.null_mask_map))
                # calculate the remaining population
                remaining_population_map = ifthenelse(scalar(existing_settlements_buffer_map) > scalar(0),
                                                      scalar(self.null_mask_map),
                                                      self.population_map)
                # to derive the population hotspots first derive the regional adapted window length
                # 1) get the distance from Parameters.py
                input_length = Parameters.get_regional_mean_impact_of_settlements_distance_in_m() # PCRaster default is measured in true length
                # 2) round up to a full cell size
                cellsize_input_length = int(math.ceil(input_length/Parameters.get_cell_length_in_m())) * Parameters.get_cell_length_in_m() # rounds up to the next full cell size
                # 3) make it an odd number for windowtotal if not already so
                if (cellsize_input_length / Parameters.get_cell_length_in_m()) % 2 == 0:
                    window_length = cellsize_input_length + Parameters.get_cell_length_in_m()  # an odd number is needed to find the central cell value
                else:
                    window_length = cellsize_input_length
                # check the remaining population map in a window of the adjusted regional settlement impact distance for population hotspots
                check_for_population_hotspots_map = windowtotal(remaining_population_map, window_length) # 19x19 window for Esmeraldas

                # OPTION A) ONE NEW SETTLEMENT PER YEAR
                if only_one_new_settlement_per_year is True:
                    # order the map and filter the maximum, at this point the new settlement will be located
                    ordered_map = order(check_for_population_hotspots_map)
                    mapmaximum_of_ordered_map = mapmaximum(ordered_map)
                    new_settlement_map = ifthenelse(ordered_map == mapmaximum_of_ordered_map,
                                                     scalar(1),
                                                     scalar(self.null_mask_map))
                    # combine the new and the old settlements
                    self.settlements_map = ifthenelse(new_settlement_map == scalar(1),
                                                      scalar(1),
                                                      scalar(self.settlements_map))

                # OPTION B) GET A PROPORTIONAL GROWTH IN THE NUMBER OF SETTLEMENTS
                else:
                    # first calculate the proportional new demand in settlements by population growth
                    demand_settlements_per_person = (self.settlements_last_time_step/ self.population_last_time_step)
                    proportional_demand_in_new_settlements = math.ceil(self.population * demand_settlements_per_person)

                    # then get the map according to households
                    households_map = check_for_population_hotspots_map / Parameters.get_regional_mean_household_size()

                    # calculate all potential new settlements
                    potential_new_settlements_map = ifthenelse(households_map > required_households_for_a_new_settlement_threshold,
                                                               scalar(households_map),
                                                               scalar(self.null_mask_map))

                    # order this map
                    ordered_map = order(potential_new_settlements_map)
                    map_maximum_ordered = mapmaximum(ordered_map)

                    # get the actual number of settlements to be set in this time step
                    actual_demand_in_new_settlements = proportional_demand_in_new_settlements - self.settlements
                    threshold_value = map_maximum_ordered - actual_demand_in_new_settlements

                    # now simulate the actual new settlements:
                    new_settlements_map = ifthenelse(ordered_map >= threshold_value,
                                                     scalar(1),
                                                     scalar(self.null_mask_map))

                    # combine the new and the old settlements
                    self.settlements_map = ifthenelse(new_settlements_map == scalar(1),
                                                      scalar(1),
                                                      scalar(self.settlements_map))

                # update the environment map
                self.environment_map = ifthenelse(scalar(self.settlements_map) == scalar(1),
                                                  nominal(1),# for each settlement at least one pixel of built up is assumed as an approximation
                                                  nominal(self.environment_map))
            else:
                # if population did not grow, take the last settlements map with growth
                self.settlements_map = self.settlements_map_last_timestep

        # count settlements for the log-file output
        self.settlements = math.ceil(maptotal(scalar(self.settlements_map)))
        print('number of settlements for the population of', self.population, 'in the year', self.year, 'is:', self.settlements)

        # note settlements for next time step
        self.settlements_last_time_step = self.settlements

        # calculate the spread map distance for the suitabilities calculation
        self.distances_to_settlements_map = spread(boolean(self.settlements_map), 0, 1)

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'settlmts'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.settlements_map, os.path.join(Filepaths.folder_dynamic_settlements_deterministic, output_map_name))

        # p.r.n. store output for the worst case scenario
        if Parameters.get_worst_case_scenario_decision() is True:
            if self.year == Parameters.get_the_initial_simulation_year_for_the_worst_case_scenario():
                report(self.settlements_map, os.path.join(Filepaths.folder_inputs_initial_worst_case_scenario, 'initial_settlements_simulated_for_worst_case_scenario_input.map'))

        return self.settlements

    # SH: LPB alternation - DYNAMIC ANTROPOGENIC IMPACT BUFFER after last time step and settlements creation for determination of disturbed forest
    def update_anthropogenic_impact_buffer(self):
        """The boolean anthropogenic impact buffer determines loss in quality of forest plots by anthropogenic impact
        and is therefore calculated each time step new based on the new settlements.
        Where this buffer to built-up including cities, streets and settlements overlaps with the "undisturbed" structural TMF information (LUT09),
        forest is hence reassigned to the disturbed forest class (LUT08).
        After land use allocation the method update_forest_fringe_disturbed() calculates additional fringe effects."""

        # extract all deterministic built-up features from the landscape (streets, cities and settlements)
        anthropogenic_landscape_features_map = pcror(self.cities_map, self.streets_map)
        anthropogenic_landscape_features_map = pcror(anthropogenic_landscape_features_map, boolean(self.settlements_map))

        spread_map = spreadmaxzone(anthropogenic_landscape_features_map, 0, 1, Parameters.get_anthropogenic_impact_distance_in_m())

        anthropogenic_impact_buffer_map = ifthenelse(scalar(spread_map) > scalar(0),
                                                     boolean(1),
                                                     boolean(self.null_mask_map))
        anthropogenic_impact_area_total = maptotal(scalar(anthropogenic_impact_buffer_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'an_impct'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(anthropogenic_impact_buffer_map, os.path.join(Filepaths.folder_dynamic_anthropogenic_impact_buffer_deterministic, output_map_name))

        # further information
        print('with a buffer of', Parameters.get_anthropogenic_impact_distance_in_m(), 'meter to anthropogenic landscape features, '
            'the total area impacted by anthropogenic landscape features is:', round(float(anthropogenic_impact_area_total), 2), Parameters.get_pixel_size())
        # filter the undisturbed forest which is impacted by anthropogenic landscape features and combine with null mask_map
        affected_undisturbed_forest_map = ifthenelse(anthropogenic_impact_buffer_map,
                                                     boolean(self.environment_map == 9),
                                                     boolean(self.null_mask_map))
        affected_undisturbed_forest_area = round(float(maptotal(scalar(affected_undisturbed_forest_map))), 2)
        print('former area of undisturbed forest now declared disturbed forest is:', affected_undisturbed_forest_area, Parameters.get_pixel_size() )
        # correct the information from undisturbed (9) to disturbed (8) in the environment_map
        self.environment_map = ifthenelse(affected_undisturbed_forest_map,
                                          nominal(8),
                                          nominal(self.environment_map))
        # calculate now the net forest area impacted by anthropogenic landscape features (all forest is now 8 in that distance)
        net_forest_overlapping_anthropogenic_impact_buffer_map = ifthenelse(anthropogenic_impact_buffer_map,
                                                                            boolean(self.net_forest_map),
                                                                            boolean(self.null_mask_map))
        net_forest_effected_by_anthropogenic_impact_map = ifthenelse(net_forest_overlapping_anthropogenic_impact_buffer_map,
                                                                     boolean(self.environment_map == 8),
                                                                     boolean(self.null_mask_map))
        net_forest_effected_by_anthropogenic_impact_area = round(float(maptotal(scalar(net_forest_effected_by_anthropogenic_impact_map))), 2)
        print('remaining net forest area effected by anthropogenic impact is:', net_forest_effected_by_anthropogenic_impact_area, Parameters.get_pixel_size())

    # SH: LPB alternation - Forest growths pre-conditions
    def update_climate_period_input_maps(self):
        """ For the time step use the according data from the 5 climate periods for the provided datasets:
        1) projection_potential_natural_vegetation_distribution
        2) projection_potential_annual_AGB_increment_map for undisturbed, disturbed and plantation
        3) projection_potential_maximum_undisturbed_AGB_map """

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

            # increments
            input_projection_potential_annual_undisturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                'file_projection_potential_annual_undisturbed_AGB_increment_2018_2020_input']
            self.projection_potential_annual_undisturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_undisturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_disturbed_AGB_increment_map = \
            self.climate_period_inputs_dictionary[
                'file_projection_potential_annual_disturbed_AGB_increment_2018_2020_input']
            self.projection_potential_annual_disturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_disturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_plantation_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_plantation_AGB_increment_2018_2020_input']
            self.projection_potential_annual_plantation_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_plantation_AGB_increment_map),
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

            # increments
            input_projection_potential_annual_undisturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_undisturbed_AGB_increment_2021_2040_input']
            self.projection_potential_annual_undisturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_undisturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_disturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_disturbed_AGB_increment_2021_2040_input']
            self.projection_potential_annual_disturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_disturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_plantation_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_plantation_AGB_increment_2021_2040_input']
            self.projection_potential_annual_plantation_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_plantation_AGB_increment_map),
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

            # increments
            input_projection_potential_annual_undisturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_undisturbed_AGB_increment_2041_2060_input']
            self.projection_potential_annual_undisturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_undisturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_disturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_disturbed_AGB_increment_2041_2060_input']
            self.projection_potential_annual_disturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_disturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_plantation_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_plantation_AGB_increment_2041_2060_input']
            self.projection_potential_annual_plantation_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_plantation_AGB_increment_map),
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

            # increments
            input_projection_potential_annual_undisturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_undisturbed_AGB_increment_2061_2080_input']
            self.projection_potential_annual_undisturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_undisturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_disturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_disturbed_AGB_increment_2061_2080_input']
            self.projection_potential_annual_disturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_disturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_plantation_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_plantation_AGB_increment_2061_2080_input']
            self.projection_potential_annual_plantation_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_plantation_AGB_increment_map),
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

            # increments
            input_projection_potential_annual_undisturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_undisturbed_AGB_increment_2081_2100_input']
            self.projection_potential_annual_undisturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_undisturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_disturbed_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_disturbed_AGB_increment_2081_2100_input']
            self.projection_potential_annual_disturbed_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_disturbed_AGB_increment_map),
                scalar(self.null_mask_map))

            input_projection_potential_annual_plantation_AGB_increment_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_annual_plantation_AGB_increment_2081_2100_input']
            self.projection_potential_annual_plantation_AGB_increment_map = cover(
                scalar(input_projection_potential_annual_plantation_AGB_increment_map),
                scalar(self.null_mask_map))

            # maximum
            input_projection_potential_maximum_undisturbed_AGB_map = \
                self.climate_period_inputs_dictionary[
                    'file_projection_potential_maximum_undisturbed_AGB_2081_2100_input']
            self.projection_potential_maximum_undisturbed_AGB_map = cover(
                scalar(input_projection_potential_maximum_undisturbed_AGB_map),
                scalar(self.null_mask_map))


        print('reading climate period input data for the time step done')



    # SH: LPB alternation
    def update_AGB_map_last_time_step(self):
        """ Safe the AGB map from last time step for comparison after this time step (degradation/regeneration)"""
        # SH: LPB alternation - get AGB last time step
        if self.time_step == 1:
            self.AGB_map_last_time_step = self.initial_AGB_map
        else:
            self.AGB_map_last_time_step = self.AGB_map # create this reference map before the new AGB_map is calculated

    # SH: LPB alternation
    def update_AGB(self):
        """ Calculate the maximum AGB growth for this time step.
        1) IN LPB-RAP with a spatially explicit map of potential increment and potential maximum or stochastic input
        2) In LPB-SFM with a formula. """
        # SH: LPB alternation - grow forest types AGB for the timestep until climax stadium, subtraction is placed in allocation of demand in Mg input biomass


        if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit':
            self.AGB_map = Formulas.get_AGB_growth_formula(AGB_map=self.AGB_map,
                                                           projection_potential_annual_undisturbed_AGB_increment_map=self.projection_potential_annual_undisturbed_AGB_increment_map,
                                                           projection_potential_annual_disturbed_AGB_increment_map=self.projection_potential_annual_disturbed_AGB_increment_map,
                                                           projection_potential_annual_plantation_AGB_increment_map=self.projection_potential_annual_plantation_AGB_increment_map,
                                                           environment_map=self.environment_map,
                                                           null_mask_map=self.null_mask_map)
        elif Parameters.get_annual_AGB_increment_simulation_decision() == 'stochastic':
            self.AGB_map = Formulas.get_AGB_growth_formula(AGB_map=self.AGB_map,
                                                           projection_potential_maximum_undisturbed_AGB_map=self.projection_potential_maximum_undisturbed_AGB_map,
                                                           AGB_annual_increment_ranges_in_Mg_per_ha_dictionary=self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary,
                                                           environment_map=self.environment_map,
                                                           null_mask_map=self.null_mask_map)
        print('current forest types AGB calculated with annual increment and spatially explicit climax stadium')
        self.AGB_total_Mg = round(float(maptotal(self.AGB_map)), 3)
        print('total forest types AGB in Mg in the landscape is:', self.AGB_total_Mg)

    # SH: LPB alternation - Plantations
    def update_plantation_age_map(self):
        """ Add 1 year to existing plantation pixels."""
        if self.time_step == 1:
            pass  # 2018 is already in the map
        elif self.time_step > 1:
            self.plantation_age_map = ifthenelse(self.plantation_age_map > scalar(0),
                                                 scalar(self.plantation_age_map) + scalar(1),  # add 1 year of age
                                                 scalar(self.null_mask_map))
            print('updating plantation age map done')


    # END OF METHODS RUN PRE ALLOCATION

    # METHODS RUN FOR ALLOCATION

    # SH: LPB alternation - Demand is now derived from the annual population development
    def update_demand(self):
        print('\ncalculating demand initiated ...')

        # SH Combination of model stage 1 (internal footprint approach) and 3 (external demand series for user-defined parameters):
        # let the model calculate first internally all values, check demand_configuartion dictionary before dictionary compilation so only by the user provided and chosen values get overwritten

        # SH: LPB alternation model stage 1 - DYNAMIC DISCRETE DEMAND BASED ON POPULATION (OR STATIC IN CASE OF PLANTATIONS)

        # demand in AGB is calculated for the whole population
        AGB_data = Parameters.get_regional_AGB_demand_per_person() # delivers a tuple with the combined and all three singular demands in AGB
        total_demand_AGB_per_person = float(AGB_data[0]) # selects the total demand per person
        demand_AGB = round((total_demand_AGB_per_person * self.population), 3)
        print('demand in AGB in Mg is: ', demand_AGB)

        # demand in LUT01 = built-up is determined by a rule of three approach per time step and rounded up for determination of maximum impact
        if self.year == Parameters.get_initial_simulation_year():
            if Parameters.get_streets_input_decision_for_calculation_of_built_up() is True:
                built_up_map = ifthenelse(self.environment_map == 1,
                                          boolean(1),
                                          boolean(self.null_mask_map))
                demand_LUT01 = math.ceil(maptotal(scalar(built_up_map)))
            else:
                built_up_map = ifthenelse(self.environment_map == 1,
                                          boolean(1),
                                          boolean(self.null_mask_map))
                built_up_minus_streets_map = ifthenelse(scalar(self.streets_map) == scalar(1),
                                                        boolean(0),
                                                        boolean(built_up_map))
                demand_LUT01 = math.ceil(maptotal(scalar(built_up_minus_streets_map)))
        else:
            demand_LUT01_per_person = (self.built_up_area_last_time_step / self.population_last_time_step)
            demand_LUT01 = math.ceil(self.population * demand_LUT01_per_person)  # built-up
            print('demand for the year', self.year, 'in built-up by a population of', self.population, 'is:', demand_LUT01, Parameters.get_pixel_size())

        # save the demand for the output log file to be simulated in mplc
        # SH: LPB alternation LUT01
        print('\nadding for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_LUT01')

        # append it to the nested dictionary (sample number is key, time step is key, value is maptotal)
        dictionary_of_samples_dictionaries_values_LUT01[self.current_sample_number][self.time_step] = demand_LUT01

        print('added for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_LUT01')



        # demand in agriculture in LPB is the demand of the smallholder share of the population and its applied LaForeT demand in LUTs
        demand_agriculture_dictionary = Parameters.get_regional_agriculture_ha_demand_per_LUT_per_person()
        self.smallholder_share = Parameters.get_regional_share_smallholders_of_population()
        self.population_number_of_smallholders = math.ceil(
            (self.population / 100) * Parameters.get_regional_share_smallholders_of_population())
        print('with a share of', Parameters.get_regional_share_smallholders_of_population(), '% population that is smallholder:', self.population_number_of_smallholders)
        # calculate a variable for each agricultural LUT and round up for determination of maximum impact
        demand_LUT02 = math.ceil(
            demand_agriculture_dictionary[2] * self.population_number_of_smallholders)  # cropland-annual
        print('their demand in cropland-annual is:', demand_LUT02, Parameters.get_pixel_size())
        demand_LUT03 = math.ceil(demand_agriculture_dictionary[3] * self.population_number_of_smallholders)  # pasture
        print('their demand in pasture is:', demand_LUT03, Parameters.get_pixel_size())
        demand_LUT04 = math.ceil(
            demand_agriculture_dictionary[4] * self.population_number_of_smallholders)  # agroforestry
        print('their demand in agroforestry is:', demand_LUT04, Parameters.get_pixel_size())

        # NO PROJECTION OF PLANTATION DEMAND COULD BE DERIVED, STATIC DEMAND IMPLEMENTED
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            if self.year == Parameters.get_initial_simulation_year():
                plantations_map = ifthenelse(self.environment_map == 5,
                                             boolean(1),
                                             boolean(self.null_mask_map))
                demand_active_plantations = math.ceil(maptotal(scalar(plantations_map)))
                deforested_plantations_map = ifthenelse(self.environment_map == 18,
                                                        boolean(1),
                                                        boolean(self.null_mask_map))
                demand_deforested_plantations = math.ceil(maptotal(scalar(deforested_plantations_map)))
                demand_LUT05 =  demand_active_plantations + demand_deforested_plantations # this alternation is necessary in case the worst case simulation year starts in a year where plantations are already deforested
                self.stored_demand_LUT05_initial_simulation_year = demand_LUT05
            else:
                demand_LUT05 = self.stored_demand_LUT05_initial_simulation_year
            print('tentative demand in plantation is:', demand_LUT05, Parameters.get_pixel_size())
        if Parameters.get_model_scenario() == 'no_conservation':
            demand_LUT05 = int(Parameters.get_plantation_demand_for_the_worst_case_scenario())
            print('tentative demand in plantation is:', demand_LUT05, Parameters.get_pixel_size())

        print('\nModel internal demands in the internal footprint approach and scenario of persistent patterns are:',
              '\n smallholder_share:', Parameters.get_regional_share_smallholders_of_population(),
              '\n demand built-up:', demand_LUT01,
              '\n demand cropland-annual:', demand_LUT02,
              '\n demand pasture:', demand_LUT03,
              '\n demand agroforestry:', demand_LUT04,
              '\n demand plantation:', demand_LUT05,
              '\n demand AGB:', demand_AGB)

        # SH model stage 3 alteration: check the demand_configuration dictionary in Parameters.py and apply the
        # user-defined parameters for a run to overwrite the initial model internally calculated values

        # FOOTPRINT APPROACH EXTERNAL
        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration[
            'internal_or_external'] == 'external':

            print('Calculating demands based on user-defined external time series for footprint approach:')

            # check if the user has gotten the right options, otherwise end the run with an error message
            # TODO: CHANGE THIS LIST IF YOU EXTEND THE MODELLING APPROACH
            list_of_current_available_footprint_options = ['smallholder_share', 2, 3, 4, 5,
                                                           'regional_AGB_demand_per_population_total']
            assert all([a_type in list_of_current_available_footprint_options for a_type in
                        Parameters.demand_configuration[
                            'list_columns_for_tss']]), f'\nERROR: \nYour list (list_columns_for_tss) of choices contains at least one option \nfor which an externally based allocation in the footprint approach is not yet incorporated. \nRefigure your choices to the currently at maximum available options:\n{list_of_current_available_footprint_options}'

            # get the values for analysis and footprint simulation to transport to csv and allocation method
            if 'smallholder_share' in Parameters.demand_configuration['list_columns_for_tss']:
                self.smallholder_share = float(
                    self.generated_tss_deterministic_demand_footprint.value(self.time_step, 'smallholder_share'))
                self.population_number_of_smallholders = math.ceil(
                    (self.population / 100) * self.smallholder_share)
                print('New smallholder_share:', self.smallholder_share, 'Concluding population number of smallholders:',
                      self.population_number_of_smallholders)
            if 2 in Parameters.demand_configuration['list_columns_for_tss']:
                demand_LUT02_per_smallholder = float(
                    self.generated_tss_deterministic_demand_footprint.value(self.time_step, 2))
                demand_LUT02 = math.ceil(self.population_number_of_smallholders * demand_LUT02_per_smallholder)
                print('New demand cropland-annual:', demand_LUT02)
            if 3 in Parameters.demand_configuration['list_columns_for_tss']:
                demand_LUT03_per_smallholder = float(
                    self.generated_tss_deterministic_demand_footprint.value(self.time_step, 3))
                demand_LUT03 = math.ceil(self.population_number_of_smallholders * demand_LUT03_per_smallholder)
                print('New demand pasture:', demand_LUT03)
            if 4 in Parameters.demand_configuration['list_columns_for_tss']:
                demand_LUT04_per_smallholder = float(
                    self.generated_tss_deterministic_demand_footprint.value(self.time_step, 4))
                demand_LUT04 = math.ceil(self.population_number_of_smallholders * demand_LUT04_per_smallholder)
                print('New demand agroforestry:', demand_LUT04)
            if 5 in Parameters.demand_configuration['list_columns_for_tss']:
                demand_LUT05 = int(self.generated_tss_deterministic_demand_footprint.value(self.time_step, 5))
                print('New demand plantation:', demand_LUT05)
            if 'regional_AGB_demand_per_population_total' in Parameters.demand_configuration['list_columns_for_tss']:
                demand_AGB = float(self.generated_tss_deterministic_demand_footprint.value(self.time_step,
                                                                                 'regional_AGB_demand_per_population_total'))
                print('New demand AGB:', demand_AGB)


        # DEMAND YIELD APPROACH, user-defined LUTs with YIELDS plus rest footprint
        if Parameters.demand_configuration['overall_method'] == 'yield_units':

            # DEMANDS
            print('Drawing demands based on user-defined external time series for yield_units approach for ...')

            # check if the user has gotten the right options, otherwise end the run with an error message
            # TODO: CHANGE THIS LIST IF YOU EXTEND THE MODELLING APPROACH
            list_of_current_available_yield_units_options = [2, 3, 4, 5, 'regional_AGB_demand_per_population_total', 'regional_smallholder_share_in_percent']

            # 1a) deterministic file
            if Parameters.demand_configuration['deterministic_or_stochastic'] == 'deterministic':
                print('deterministic file')
                assert all([a_type in list_of_current_available_yield_units_options for a_type in
                            Parameters.demand_configuration[
                                'list_columns_for_tss']]), f'\nERROR: \nYour list (list_columns_for_tss) of choices contains at least one option \nfor which an externally based allocation in the demand/yield+footprint approach is not yet incorporated. \nRefigure your choices to the currently at maximum available options:\n{list_of_current_available_yield_units_options}'
                if 2 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT02 = int(self.generated_tss_deterministic_demand_yield_units.value(self.time_step, 2))
                    print('New demand cropland-annual:', demand_LUT02)
                if 3 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT03 = int(self.generated_tss_deterministic_demand_yield_units.value(self.time_step, 3))
                    print('New demand pasture:', demand_LUT03)
                if 4 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT04 = int(self.generated_tss_deterministic_demand_yield_units.value(self.time_step, 4))
                    print('New demand agroforestry:', demand_LUT04)
                if 5 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT05 = int(self.generated_tss_deterministic_demand_yield_units.value(self.time_step, 5))
                    print('New demand plantation:', demand_LUT05)
                if 'regional_AGB_demand_per_population_total' in Parameters.demand_configuration[
                    'list_columns_for_tss']:
                    demand_AGB = float(self.generated_tss_deterministic_demand_yield_units.value(self.time_step,
                                                                                       'regional_AGB_demand_per_population_total'))
                    print('New demand AGB:', demand_AGB)
                if Parameters.get_local_wood_consumption_simulation_choice() == True:
                    if 'regional_smallholder_share_in_percent' in Parameters.demand_configuration['list_columns_for_tss']:
                        self.smallholder_share = float(self.generated_tss_deterministic_demand_yield_units.value(self.time_step,
                                                                                       'regional_smallholder_share_in_percent'))
            # 1b) stochastic files
            if Parameters.demand_configuration['deterministic_or_stochastic'] == 'stochastic':
                print('stochastic files')
                assert all([a_type in list_of_current_available_yield_units_options for a_type in
                            Parameters.demand_configuration[
                                'list_columns_for_tss']]), f'\nERROR: \nYour list (list_columns_for_tss) of choices contains at least one option \nfor which an externally based allocation in the demand/yield+footprint approach is not yet incorporated. \nRefigure your choices to the currently at maximum available options:\n{list_of_current_available_yield_units_options}'
                if 2 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT02_HIGH = int(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step, 2))
                    demand_LUT02_LOW = int(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step, 2))
                    demand_LUT02 = int(numpy.random.uniform(low=demand_LUT02_LOW, high=demand_LUT02_HIGH, size=None))
                    print('New demand cropland-annual:', demand_LUT02)
                if 3 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT03_HIGH = int(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step, 3))
                    demand_LUT03_LOW = int(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step, 3))
                    demand_LUT03 = int(numpy.random.uniform(low=demand_LUT03_LOW, high=demand_LUT03_HIGH, size=None))
                    print('New demand pasture:', demand_LUT03)
                if 4 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT04_HIGH = int(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step, 4))
                    demand_LUT04_LOW = int(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step, 4))
                    demand_LUT04 = int(numpy.random.uniform(low=demand_LUT04_LOW, high=demand_LUT04_HIGH, size=None))
                    print('New demand agroforestry:', demand_LUT04)
                if 5 in Parameters.demand_configuration['list_columns_for_tss']:
                    demand_LUT05_HIGH = int(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step, 5))
                    demand_LUT05_LOW = int(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step, 5))
                    demand_LUT05 = int(numpy.random.uniform(low=demand_LUT05_LOW, high=demand_LUT05_HIGH, size=None))
                    print('New demand plantation:', demand_LUT05)
                if 'regional_AGB_demand_per_population_total' in Parameters.demand_configuration[
                    'list_columns_for_tss']:
                    demand_AGB_HIGH = float(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step,
                                                                                              'regional_AGB_demand_per_population_total'))
                    demand_AGB_LOW = float(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step,
                                                                                            'regional_AGB_demand_per_population_total'))
                    demand_AGB = round(numpy.random.uniform(low=demand_AGB_LOW, high=demand_AGB_HIGH, size=None), 3)
                    print('New demand AGB:', demand_AGB)
                if Parameters.get_local_wood_consumption_simulation_choice() == True:
                    if 'regional_smallholder_share_in_percent' in Parameters.demand_configuration['list_columns_for_tss']:
                        smallholder_share_HIGH = float(self.generated_tss_stochastic_demand_yield_units_HIGH.value(self.time_step,
                                                                                              'regional_smallholder_share_in_percent'))
                        smallholder_share_LOW = float(self.generated_tss_stochastic_demand_yield_units_LOW.value(self.time_step,
                                                                                        'regional_smallholder_share_in_percent'))
                        self.smallholder_share = round(numpy.random.uniform(low=smallholder_share_LOW, high=smallholder_share_HIGH, size=None), 2)

        # TODO DELETE WHEN REALISTIC DEMANDS IN YIELD APPROACH OR self.yield_fraction clarified:
        if Parameters.demand_configuration['overall_method'] == 'yield_units':
            demand_LUT02 = (demand_LUT02 / 40)
            demand_LUT03 = (demand_LUT03 / 5)
            demand_LUT04 = (demand_LUT04 / 5)

        # Final dict to be transported to allocate
        demand = {
            1: demand_LUT01, # built-up
            2: demand_LUT02, # cropland-annual
            3: demand_LUT03, # pasture
            4: demand_LUT04, # agroforestry
            5: demand_LUT05  # plantation
        }

        print('Final demands to be simulated in this time step are:',
              '\n demand built-up (always model internally calculated):', demand_LUT01,
              '\n demand cropland-annual:', demand_LUT02,
              '\n demand pasture:', demand_LUT03,
              '\n demand agroforestry:', demand_LUT04,
              '\n demand plantation:', demand_LUT05,
              '\n demand AGB:', demand_AGB)

        print('\nCalculating demand done')

        # Note the demands for the calculation of mean demand and mean unallocated demands in the postmcloop
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][self.time_step][
            'demand']['LUT02'] = demand_LUT02
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][self.time_step][
            'demand']['LUT03'] = demand_LUT03
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][self.time_step][
            'demand']['LUT04'] = demand_LUT04
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][self.time_step][
            'demand']['LUT05'] = demand_LUT05
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][self.time_step][
            'demand']['AGB'] = demand_AGB

        return demand, self.population_number_of_smallholders, demand_AGB


    # SH: original PLUC method
    def set_environment(self, environment_map):
        """ JV: Update environment of the 'overall' class and separate land use types."""
        self.environment_map = environment_map
        for a_type in self.land_use_types:
            a_type.set_environment(self.environment_map)

    # SH: original PLUC method
    def create_land_use_types_objects(self, related_land_use_types_dictionary, suitabilities_dictionary,
                                      weights_dictionary, variables_super_dictionary, noise):
        """ JV: Generate an object for every dynamic land use type.

        Make objects with:
        type_number -- class number in land use map
        environment -- global land use map
        related_land_use_types -- list with land use types next to which growth is preferred
        suitability_factors -- list with numbers of the needed suitability factors
        weights -- list with relative weights for those factors
        variables -- dictionary with inputs for those factors
        noise -- small random noise that determines order when same suitability

        """
        window_length_realization = float(mapnormal())

        for a_type in self.types:
            # JV: Get the list that states which types the current type relates to
            related_types_list = related_land_use_types_dictionary.get(a_type)
            # JV: Get the right list of suitability factors out of the dictionary
            suitabilities_list = suitabilities_dictionary.get(a_type)
            # JV: Get the weights and variables out of the weight dictionary
            weights_list = weights_dictionary.get(a_type)
            variables_dictionary = variables_super_dictionary.get(a_type)
            # JV: Parameter list is not included yet
            # SH: LPB alternation: deleted from self.land_use_types.append: self.yieldFrac, self.forestYieldFrac,
            self.land_use_types.append(LandUseType(a_type,
                                                   self.environment_map,
                                                   related_types_list,
                                                   suitabilities_list,
                                                   weights_list,
                                                   variables_dictionary,
                                                   noise,
                                                   self.null_mask_map,
                                                   window_length_realization,
                                                   self.initial_environment_map,
                                                   self.LUT02_sampled_distance_for_this_sample,
                                                   self.LUT03_sampled_distance_for_this_sample,
                                                   self.LUT04_sampled_distance_for_this_sample,
                                                   self.static_areas_on_which_no_allocation_occurs_map,
                                                   self.static_LUTs_on_which_no_allocation_occurs_list,
                                                   self.difficult_terrain_slope_restriction_dictionary,
                                                   self.slope_map,
                                                   self.external_demands_generated_tss_dictionary,
                                                   self.climate_period_inputs_dictionary
                                                   ))


    def determine_immutable_excluded_areas_from_allocation_map(self):
        self.slope_map = slope(scalar(self.dem_map))
        self.excluded_areas_from_allocation_map = self.static_areas_on_which_no_allocation_occurs_map  # this is initially only a null mask_map map in LPB
        slope_dependent_areas_of_no_allocation_map = None
        # JV: Check the list with immutable land uses
        if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
            for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                boolean_static_LUT_map)  # now it contains the static LUTs
        # SH: additional variable for allocation procedure with only the truly excluded cells in the map
        self.immutable_excluded_areas_from_allocation_map = self.excluded_areas_from_allocation_map


    # SH: original PLUC method
    def determine_distance_to_streets(self, boolean_map_streets):
        """ JV: Create map with distance to streets, given a boolean map with streets."""
        self.distances_to_streets_map = spread(boolean_map_streets, 0, 1)

    # SH: original PLUC method
    def determine_distance_to_freshwater(self, boolean_map_freshwater):
        """ JV: Create map with distance to freshwater, given a boolean map with freshwater."""
        self.distances_to_freshwater_map = spread(boolean_map_freshwater, 0, 1)

    # SH: original PLUC method
    def determine_distance_to_cities(self, boolean_map_cities):
        """ JV: Create map with distance to cities, using a boolean map with cities."""
        self.distances_to_cities_map = spread(boolean_map_cities, 0, 1)

    # SH: original PLUC method
    def calculate_static_suitability_maps(self):
        """ JV: Get the part of the suitability maps that remains the same."""
        for a_type in self.land_use_types:
            # JV: Check whether the type has static suitability factors
            # JV: Those have to be calculated only once (in initial)
            # SH: LPB alternation - deleted self.populationDensity, self.cattleDensity
            a_type.create_initial_suitability_map(self.distances_to_streets_map,
                                                  self.distances_to_freshwater_map,
                                                  self.distances_to_cities_map)


    # SH: original PLUC method
    def calculate_suitability_maps(self):
        """ JV: Get the total suitability maps (static plus dynamic part)."""
        suitability_maps = []
        for a_type in self.land_use_types:
            suitability_map = a_type.get_total_suitability_map(environment_map=self.environment_map,
                                                                                    distances_to_settlements_map=self.distances_to_settlements_map,
                                                                                    population_map=self.population_map,
                                                                                    net_forest_map=self.net_forest_map)
            suitability_maps.append(suitability_map)


    # SH: LPB alternation
    def allocate_AGB_demand(self, demand_AGB):
        """SH: Allocate demand in input biomass prior or posterior to the allocation of the active land use types according to Parameters.get_order_of_forest_deforestation_and_conversion()."""

        # get the current environment map to pass along
        temporal_environment_map = self.environment_map

        if demand_AGB > 0:
            print('\ndemand for input biomass (timber, fuelwood, charcoal) is not zero. AGB will be subtracted from local and/or net_forest pixels.')

            # LOCAL AGB EXTRACTION
            if Parameters.get_local_wood_consumption_simulation_choice() == True:
                # the allocation recognizes restricted areas in BAU and BAU(+)
                temporal_environment_map, rest_demand_AGB, no_more_local_forest, no_more_local_suitable_slopes, not_enough_local_AGB = self._remove_local_forest_AGB(
                    demand_AGB, temporal_environment_map)
                # info
                if no_more_local_forest == True:
                    print('NO MORE LOCAL FOREST TO EXTRACT LOCAL WOOD DEMAND, CALCULATED IN NET FOREST')
                if no_more_local_suitable_slopes == True:
                    print('NO MORE LOCAL SUITABLE FOREST SLOPES TO EXTRACT LOCAL WOOD DEMAND, CALCULATED IN NET FOREST')
                if not_enough_local_AGB == True:
                    print('NOT ENOUGH LOCAL FOREST AGB TO EXTRACT LOCAL WOOD DEMAND, CALCULATED IN NET FOREST')
                # if this method is applied, note the new value demand AGB for net forest extraction
                demand_AGB = rest_demand_AGB

            # NET FOREST AGB EXTRACTION
            # the first allocation recognizes restricted areas
            temporal_environment_map, demand_AGB_remaining, no_more_net_forest, no_more_suitable_slopes = self._remove_net_forest_AGB(demand_AGB,
                                                                                                             temporal_environment_map)
            # loop the method as long as demand remains or until no more net forest or suitable slope is available, no more restricted areas recognized
            while demand_AGB_remaining > 0 and no_more_net_forest is False and no_more_suitable_slopes is False:
                temporal_environment_map, demand_AGB_remaining, no_more_net_forest, no_more_suitable_slopes = self._remove_net_forest_AGB(
                    demand_AGB, temporal_environment_map)
            if demand_AGB_remaining > 0 and no_more_net_forest is True:
                print('NO MORE NET FOREST LEFT TO REMOVE, demand remaining for the time step is:', demand_AGB_remaining)
            if demand_AGB_remaining > 0 and no_more_suitable_slopes is True:
                print('NO MORE SUITABLE SLOPES, demand remaining for the time step is:', demand_AGB_remaining)
        else:
            print('\nno (more) demand in input AGB, no (more) AGB of net_forest will be removed due to wood demand')

        self.set_environment(temporal_environment_map)

        # Note the unallocated demand for the calculation in the postmcloop
        dictionary_of_samples_dictionaries_values_unallocated_demands[self.current_sample_number][
            self.time_step]['unallocated_demand']['AGB'] = demand_AGB_remaining

    # SH: LPB alternation - deleted maxYield, adjusted immutables map, DK added plantation
    def allocate(self, demand):
        """ SH: Allocate as much of a land use type as calculated demand is based on population development in the range of suitability."""
        temporal_environment_map = self.environment_map
        temporal_succession_age_map = self.succession_age_map
        immutables_map = self.immutable_excluded_areas_from_allocation_map
        if Parameters.get_dynamic_LUTs_on_which_no_allocation_occurs() is not None:
            dynamic_LUTs_on_which_no_allocation_occurs_list = Parameters.get_dynamic_LUTs_on_which_no_allocation_occurs()
            for a_number in dynamic_LUTs_on_which_no_allocation_occurs_list:
                boolean_dynamic_LUT_map = pcreq(self.environment_map, a_number)
                immutables_map = pcror(boolean(immutables_map), boolean(boolean_dynamic_LUT_map))
        # allocate the active land use types
        for a_type in self.land_use_types:
            if Parameters.demand_configuration['overall_method'] == 'yield_units' and (a_type.type_number in Parameters.demand_configuration['LUTs_with_demand_and_yield']):
                a_type.set_maximum_yield()
            temporal_environment_map, immutables_map, number_of_to_be_added_cells, only_new_pixels_map, temporal_succession_age_map = a_type.allocate(
                demand, temporal_environment_map, immutables_map, temporal_succession_age_map)
            if a_type.type_number == 5:
                temporal_environment_map, temporal_succession_age_map = self._update_plantation_new_and_plantation_harvest_information(
                    temporal_environment_map, only_new_pixels_map, immutables_map, number_of_to_be_added_cells,
                    temporal_succession_age_map)
        self.succession_age_map = temporal_succession_age_map
        self.set_environment(temporal_environment_map)


        # SH & DK: LPB alternation - consider new plantation pixels and possible harvest of plantations
    def _update_plantation_new_and_plantation_harvest_information(self, temporal_environment_map, only_new_pixels_map, immutables_map, number_of_to_be_added_cells, temporal_succession_age_map):
        """ Incorporate new plantation pixels if available and look if plantation pixels are ready for harvest."""

        # to be incorporated new plantation pixels
        if number_of_to_be_added_cells is not None and number_of_to_be_added_cells >= 1:

            only_new_pixels_map = cover(scalar(only_new_pixels_map), scalar(self.null_mask_map))
            self.new_plantations_map = ifthenelse(scalar(only_new_pixels_map) == scalar(5),
                                                  scalar(1),
                                                  scalar(self.null_mask_map))

            temporal_environment_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                                  nominal(5),
                                                  nominal(temporal_environment_map))

            self.new_plantations_map = cover(self.new_plantations_map, scalar(self.null_mask_map))

            immutables_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                        boolean(1),
                                        boolean(immutables_map))

        elif number_of_to_be_added_cells is None or number_of_to_be_added_cells == 0:
            self.new_plantations_map = None

        # to be harvested plantation pixels
        self.plantation_harvest_ready_map = ifthenelse(self.plantation_rotation_period_end_map == self.year, # only cells for the year that are ready are selected
                                                           scalar(1),
                                                           scalar(self.null_mask_map))

        self.plantation_harvest_ready_map = ifthenelse(temporal_environment_map == 5, # make sure only standing plantations are selected
                                                       self.plantation_harvest_ready_map,
                                                       self.null_mask_map)

        self.plantation_harvest_ready_area = int(maptotal(self.plantation_harvest_ready_map))

        if self.plantation_harvest_ready_area > 0:
            print('\nplantations reached harvest age, so harvest:', self.plantation_harvest_ready_area, Parameters.get_pixel_size() )
            # removes cells based on age and rotation period and changes these cells to LUT18 plantation - - deforested
            temporal_environment_map, temporal_succession_age_map = self._harvest_plantation(temporal_environment_map, temporal_succession_age_map)
        elif self.plantation_harvest_ready_area == 0:
            self.new_plantations_deforested_map = None
            print('\nplantations not ready for harvest yet')
        return temporal_environment_map, temporal_succession_age_map



    # SH: LPB alternation - consider harvest of plantations
    def _harvest_plantation(self, temporal_environment_map, temporal_succession_age_map):
        """ Harvest prior indicated pixels and change to LUT18 "plantation - - deforested". """

        self.new_plantations_deforested_map = self.plantation_harvest_ready_map

        # correct the plantation age map
        self.plantation_age_map = ifthenelse(scalar(self.plantation_harvest_ready_map) == scalar(1),
                                             scalar(0),
                                             scalar(self.plantation_age_map))

        # correct the plantation rotation period end map
        self.plantation_rotation_period_end_map = ifthenelse(self.plantation_age_map == scalar(0),
                                                             scalar(0),
                                                             scalar(self.plantation_rotation_period_end_map))

        # correct the succession age map
        temporal_succession_age_map = ifthenelse(scalar(self.plantation_harvest_ready_map) == scalar(1),
                                                 scalar(1),
                                                 scalar(temporal_succession_age_map))

        # and subtract the AGB from the AGB_map
        self.AGB_map = ifthenelse(scalar(self.plantation_harvest_ready_map) == scalar(1),
                                  scalar(0),
                                  scalar(self.AGB_map))

        temporal_environment_map = ifthenelse(scalar(self.plantation_harvest_ready_map) == scalar(1),
                                              # the selected cells ...
                                              nominal(18),  # ... turn into plantation - - harvested
                                              nominal(temporal_environment_map))

        print('harvested ready plantations')

        return temporal_environment_map, temporal_succession_age_map

    # SH LPB-RAP model stage 2 alternation
    def _remove_local_forest_AGB(self, demand_AGB, temporal_environment_map):
        """SH: This method is applied on user-defined demand. It simulates the approximation of local wood consumption using the smallholder share.
        Thereby local degradation modelling is enabled. This method uses fractions, therefore all local forest pixels are considered,
        with the exception of restricted areas in the BAU or BAU(+) scenario.
        ATTENTION: This method does not simulate total deforestation (0 Mg AGB)."""

        print('\nharvesting local demand in input biomass from settlements surrounding forest pixels:')

        # get the settlements map and all related forest pixels in the local maximum wood consumption distance
        spread_map = spreadmaxzone(boolean(self.settlements_map), 0, 1,
                                   Parameters.get_maximum_distance_for_local_wood_consumption())
        existing_settlements_buffer_map = ifthenelse(scalar(spread_map) > scalar(0),
                                                     boolean(1),
                                                     boolean(self.null_mask_map))
        environment_in_buffer_map = ifthenelse(boolean(existing_settlements_buffer_map) == boolean(1),
                                               scalar(temporal_environment_map),
                                               scalar(self.null_mask_map))
        local_forest_pixels_map = ifthenelse(scalar(environment_in_buffer_map) == scalar(8), # get disturbed forest pixels
                                             boolean(1),
                                             boolean(self.null_mask_map))
        local_forest_pixels_map = ifthenelse(scalar(environment_in_buffer_map) == scalar(9), # get until now undisturbed forest pixels
                                             boolean(1),
                                             boolean(local_forest_pixels_map))

        # subtract restricted areas in BAU and BAU(+)
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            local_forest_pixels_map = ifthenelse(scalar(self.static_restricted_areas_map) == scalar(1),
                                                 boolean(0),
                                                 boolean(local_forest_pixels_map))

        # get the number of pixels
        number_of_local_forest_pixels = maptotal(scalar(boolean(local_forest_pixels_map)))

        # break if no more local forest available
        if number_of_local_forest_pixels == 0:
            rest_demand_AGB = demand_AGB
            no_more_local_forest = True
        # otherwise continue
        else:
            no_more_local_forest = False
            # extract slopes for wood consumption
            # only slopes below or equal to the maximum value will be recognized
            slope_dependent_areas_of_wood_consumption_map = pcrle(self.slope_map, Parameters.get_maximum_slope_deforestation_value())
            local_forest_pixels_minus_slopes_map = ifthen(slope_dependent_areas_of_wood_consumption_map,
                                                          boolean(local_forest_pixels_map))
            test_slopes_maptotal = maptotal(scalar(boolean(local_forest_pixels_minus_slopes_map)))
            # break if no more suitable slopes for wood consumption
            if test_slopes_maptotal == 0:
                rest_demand_AGB = demand_AGB
                no_more_local_suitable_slopes = True
            # otherwise continue
            else:
                no_more_local_suitable_slopes = False
                # get AGB in that pixels (singular and maptotal)
                local_AGB_map = ifthen(boolean(local_forest_pixels_minus_slopes_map) == boolean(1),
                                   scalar(self.AGB_map))
                total_local_AGB = maptotal(scalar(local_AGB_map))

                # get the number of pixels from which can AGB get extracted
                number_of_AGB_extraction_pixels = maptotal(scalar(boolean(local_AGB_map)))

                # calculate the smallholder share of wood demand
                print('regional smallholder share in percent:', self.smallholder_share)
                smallholder_local_AGB_demand = (demand_AGB / 100) * self.smallholder_share

                # test if demand can be satisfied
                if total_local_AGB < smallholder_local_AGB_demand:
                    rest_demand_AGB = demand_AGB
                    not_enough_local_AGB = True
                # otherwise continue
                else:
                    not_enough_local_AGB = False
                    # save the initial AGB information
                    initial_AGB_map = self.AGB_map
                    # calculate the rest demand
                    rest_demand_AGB = demand_AGB - smallholder_local_AGB_demand
                    # start iteration
                    iteration = 0
                    # perform looping over potential extraction pixels
                    while smallholder_local_AGB_demand > 1 and iteration < 100: # NOTE: 1 = 1 Mg AGB; endless iterations with exact 0
                        print('extract smallholder local AGB demand of:', smallholder_local_AGB_demand)
                        # calculate the loop value to be extracted from a cell
                        AGB_extraction_value = smallholder_local_AGB_demand / number_of_AGB_extraction_pixels
                        # filter the AGB cells that can accomodate this value, determine their number
                        AGB_extraction_cells_map = ifthen(scalar(local_AGB_map) > scalar(AGB_extraction_value),
                                                          scalar(local_AGB_map))
                        AGB_extraction_cells_in_this_harvesting = maptotal(scalar(boolean(AGB_extraction_cells_map)))
                        # extract AGB
                        local_AGB_map = local_AGB_map - AGB_extraction_cells_map
                        # update demand
                        smallholder_local_AGB_demand = smallholder_local_AGB_demand - (AGB_extraction_value * AGB_extraction_cells_in_this_harvesting)
                        # info
                        print('iteration of local AGB extraction:', iteration, '| remaining local AGB demand:', float(smallholder_local_AGB_demand))
                        iteration += 1


                    # cover AGB map with new local AGB map
                    self.AGB_map = cover(scalar(local_AGB_map), scalar(initial_AGB_map))

                    # Adjust to LUT08 where AGB was extracted
                    impacted_forest_map = ifthen(scalar(self.AGB_map) < scalar(initial_AGB_map),
                                                 nominal(8))

                    temporal_environment_map = cover(nominal(impacted_forest_map), nominal(temporal_environment_map))

                    # adjust the succession age to prevent transformation to undisturbed forest
                    disturbed_forest_around_settlements_age_map = ifthen(scalar(impacted_forest_map) > scalar(0),
                                                                         scalar(1))

                    self.succession_age_map = cover(scalar(disturbed_forest_around_settlements_age_map), scalar(self.succession_age_map))  # set back the clock for impacted forest cells

        return temporal_environment_map, rest_demand_AGB, no_more_local_forest, no_more_local_suitable_slopes, not_enough_local_AGB

    def _remove_net_forest_AGB(self, demand_AGB, temporal_environment_map):
        """ SH: remove Mg net forest biomass as calculated by demand of population.
        Where new AGB is 0 and net forest was true, change to LUT17.
        This methods searches in the current net forest fringe (and suitable slopes), it will repeat until demand is satisfied or no more net forest available."""

        print('\nharvesting demand in input biomass from net forest fringe:')

        # SH: the net forest map needs to get updated (when the 5 active LUTs are through with allocation), only where LUT08 and LUT09 remain is still net forest which can be deforested
        environment_in_net_forest_map = ifthenelse(scalar(self.net_forest_map) == scalar(1),
                                                   scalar(self.environment_map),
                                                   scalar(self.null_mask_map))

        self.net_forest_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(8),  # get disturbed pixels
                                         boolean(1),
                                         boolean(self.null_mask_map))
        self.net_forest_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(9), # get undisturbed pixels
                                         boolean(1),
                                         boolean(self.net_forest_map))

        # TODO transfer
        net_forest_maptotal = int(maptotal(scalar(boolean(self.net_forest_map))))
        test_net_forest_map = ifthen(scalar(self.net_forest_map) > scalar(0),
                                     self.net_forest_map)
        map_maximum = float(mapmaximum(scalar(test_net_forest_map)))
        map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
        no_more_net_forest = True if (net_forest_maptotal == 0 or map_maximum_NaN == True) else False
        # TODO Stop transfer
        if no_more_net_forest is True:
            print('no more net forest available for subtraction of demand in input biomass')
            temporal_environment_map = temporal_environment_map
            if self.demand_AGB_remaining > 0:
                self.demand_AGB_remaining = self.demand_AGB_remaining
            else:
                self.demand_AGB_remaining = demand_AGB
            no_more_net_forest = True
            # write the data into the log file ['Sample', 'Time step', 'Year', 'Factor']
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            factor = 'no_more_net_forest_available'
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-deforestation-nan_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [sample, time_step, year, factor]
                writer.writerow(LPB_log_file_data)
        else:
            # Step 1a - Forest Fringe Suitability (a.k.a. accessibility)
            """ SH: Return a suitability map based on number of neighbors for the net forest fringe."""
            pure_net_forest_map = ifthen(scalar(self.net_forest_map) == scalar(1),
                                         scalar(self.net_forest_map))
            scalar_self = scalar(pure_net_forest_map)
            # SH: Count cells within a 3x3 window to determine the forest fringe cells
            window_length = 3 * Parameters.get_cell_length_in_m() # 9(-1) cells if not forest fringe
            number_neighbors_net_forest_map = windowtotal(scalar_self, window_length) - scalar_self

            net_forest_fringe_map = ifthen(scalar(number_neighbors_net_forest_map) < scalar(8), #forest fringes are determined by missing pixels in the window (less than 9 (-1) present)
                                           scalar(number_neighbors_net_forest_map))

            # JV: The number of neighbors are turned into suitability values between 0 and 1
            maximum_number_neighbors = ((window_length / celllength()) ** 2) - 1

            net_forest_fringe_suitability_map = scalar(maximum_number_neighbors) / (net_forest_fringe_map + 1)
            # depicts the minimum value with the highest suitability
            # + 1 is used since devision by 0 would result in a missing value and this map does not need to be combined with further suitabilities

            # correction step since self.AGB_map can contain pixels of 0 AGB
            corrected_net_forest_fringe_suitability_map = ifthen(pcrnot(boolean(scalar(self.AGB_map) == scalar(0))),
                                                                 net_forest_fringe_suitability_map)

            # exclude the user-defined areas of no allocation
            corrected_net_forest_fringe_suitability_map = ifthen(scalar(self.static_areas_on_which_no_allocation_occurs_map) == scalar(0),
                                                                 corrected_net_forest_fringe_suitability_map)

            # in the following two cases subtract the restricted areas before the for loop:
            if Parameters.get_model_scenario() != 'no_conservation' or self.demand_AGB_remaining == 0:
                corrected_net_forest_fringe_suitability_map = ifthen(pcrnot(self.static_restricted_areas_map),
                                                                     corrected_net_forest_fringe_suitability_map)

            """ SH: Now subtract unsuitable slopes for deforestation"""
            # only slopes below or equal to the maximum value will be recognized
            slope_dependent_areas_of_deforestation_map = pcrle(self.slope_map, Parameters.get_maximum_slope_deforestation_value())

            forest_fringe_minus_slopes_map = ifthen(slope_dependent_areas_of_deforestation_map,
                                                    corrected_net_forest_fringe_suitability_map)

            """ SH: Now calculate the actual deforestation"""
            # get the AGB values in this area
            AGB_in_forest_fringe_minus_slope_suitability_map = ifthen(
                scalar(forest_fringe_minus_slopes_map) > scalar(0),
                self.AGB_map)

            # TODO transfer
            test_slopes_map = ifthen(scalar(AGB_in_forest_fringe_minus_slope_suitability_map) > scalar(0),
                                     AGB_in_forest_fringe_minus_slope_suitability_map)
            map_maximum = float(mapmaximum(scalar(test_slopes_map)))
            map_maximum_NaN = numpy.isnan(map_maximum)  # check if there are still available cells
            no_more_suitable_slopes = True if map_maximum_NaN == True else False
            if no_more_suitable_slopes is True:
                print('no more suitable slopes available for subtraction of demand in input biomass')
                temporal_environment_map = temporal_environment_map
                # write the data into the log file ['Sample', 'Time step', 'Year', 'Factor']
                sample = self.current_sample_number
                time_step = self.time_step
                year = self.year
                factor = 'no_more_suitable_slopes_with_biomass_available_at_forest_fringe'
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-deforestation-nan_log-file.csv'), 'a',
                          newline='') as LPB_log_file:
                    # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                    writer = csv.writer(LPB_log_file)
                    LPB_log_file_data = [sample, time_step, year, factor]
                    writer.writerow(LPB_log_file_data)
            else:
                # subtract the demand in AGB from the suitable pixels according to the amount of AGB in the cells
                ordered_map = order(forest_fringe_minus_slopes_map)
                map_maximum_ordered = int(mapmaximum(ordered_map))
                map_minimum_ordered = int(mapminimum(ordered_map))
                range_in_ordered = range(map_maximum_ordered, map_minimum_ordered, -1) # highest suitability is highest number, go down from there
                if self.demand_AGB_remaining == 0:
                    print('demand Mg input biomass to be removed from net forest fringe:', demand_AGB)
                else:
                    print('remaining demand in Mg input biomass to remove from net forest fringe is:', self.demand_AGB_remaining)

                if self.demand_AGB_remaining == 0:
                    demand_AGB_remaining_in_this_harvesting = demand_AGB
                else:
                    demand_AGB_remaining_in_this_harvesting = self.demand_AGB_remaining

                list_of_AGB_values_in_top_down_order_of_ordered_map = []
                current_sum_AGB = 0

                if self.demand_AGB_remaining == 0:
                    for a_suitable_cell in range_in_ordered:
                        if demand_AGB_remaining_in_this_harvesting <= 0:
                            break
                        AGB_value_to_append = float(maptotal(ifthen(ordered_map == a_suitable_cell,
                                                                    scalar(AGB_in_forest_fringe_minus_slope_suitability_map)))) # checks the different pixels with different productivity/status
                        # print(' - AGB_value_to_append:', AGB_value_to_append)
                        list_of_AGB_values_in_top_down_order_of_ordered_map.append(AGB_value_to_append)
                        # print(' - list_of_AGB_values_in_top_down_order_of_ordered_map:', list_of_AGB_values_in_top_down_order_of_ordered_map)
                        current_sum_AGB = round(sum(list_of_AGB_values_in_top_down_order_of_ordered_map), 3)
                        demand_AGB_remaining_in_this_harvesting = round((demand_AGB - current_sum_AGB), 3)
                        self.demand_AGB_remaining = demand_AGB_remaining_in_this_harvesting
                else:
                    for a_suitable_cell in range_in_ordered:
                        if demand_AGB_remaining_in_this_harvesting <= 0:
                            break
                        AGB_value_to_append = float(maptotal(ifthen(ordered_map == a_suitable_cell,
                                                                    scalar(AGB_in_forest_fringe_minus_slope_suitability_map)))) # checks the different pixels with different productivity/status
                        # print(' - AGB_value_to_append:', AGB_value_to_append)
                        list_of_AGB_values_in_top_down_order_of_ordered_map.append(AGB_value_to_append)
                        # print(' - list_of_AGB_values_in_top_down_order_of_ordered_map:', list_of_AGB_values_in_top_down_order_of_ordered_map)
                        current_sum_AGB = round(sum(list_of_AGB_values_in_top_down_order_of_ordered_map), 3)
                        demand_AGB_remaining_in_this_harvesting = round((self.demand_AGB_remaining - current_sum_AGB), 3) # TODO will this work for the 2nd loop?
                        self.demand_AGB_remaining = demand_AGB_remaining_in_this_harvesting




                # if the needed demand is reached, calculate the position for ordered
                length_of_AGB_values_list = len(list_of_AGB_values_in_top_down_order_of_ordered_map)

                # determine the threshold value for the map
                threshold_value = map_maximum_ordered - length_of_AGB_values_list

                # now change the map(s)
                # correct the environment_map
                temp_environment_map = ifthen(ordered_map >= threshold_value,
                                              nominal(17))  # define the deforested pixel in the land use map

                temporal_environment_map = cover(nominal(temp_environment_map), nominal(temporal_environment_map)) # combine it with the self.environment_map

                deforested_net_forest_area = int(maptotal(scalar(boolean(scalar(temporal_environment_map) == scalar(17)))))

                # correct the net forest map
                self.net_forest_map = ifthenelse(scalar(temporal_environment_map) != scalar(17),
                                                 scalar(self.net_forest_map),
                                                 scalar(self.null_mask_map))

                # correct the succession_age_map
                succession_age_LUT17_map = ifthen(scalar(temp_environment_map) == scalar(17),
                                                  scalar(1))
                self.succession_age_map =  cover(scalar(succession_age_LUT17_map), scalar(self.succession_age_map))

                # correct the main AGB map
                self.AGB_map = ifthenelse(boolean(scalar(temporal_environment_map) == scalar(17)),
                                          scalar(0),
                                          scalar(self.AGB_map))

                print('initial AGB demand of', demand_AGB, 'could be satisfied with', current_sum_AGB, '; remaining demand is:', self.demand_AGB_remaining)
                print('deforested net forest area is:', deforested_net_forest_area, Parameters.get_pixel_size())

                if self.demand_AGB_remaining <= 0:
                    self.demand_AGB_remaining = 0

        # report the ha deforested for demand in input biomass, since they might not show up in the final map
        if Parameters.get_order_of_forest_deforestation_and_conversion() is True: # deforestation_before_conversion
            if probabilistic_output_options_dictionary['deforested_net_forest_map'] == True:
                # built a map
                deforested_net_forest_map = ifthenelse(scalar(temporal_environment_map) == scalar(17),
                                                       scalar(1),
                                                       scalar(self.null_mask_map))

                # store output
                time_step = self.time_step
                pcraster_conform_map_name = 'defo'
                output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step)
                report(deforested_net_forest_map, os.path.join(Filepaths.folder_deforested_before_conversion, str(self.current_sample_number), output_map_name))

        return temporal_environment_map, self.demand_AGB_remaining, no_more_net_forest, no_more_suitable_slopes

    # END OF ALLOCATION METHODS PLUC/LPB

    # POST ALLOCATION METHODS:

    # SH: LPB alternation
    def correct_AGB_map_after_allocation(self):
        """ First step of the AGB_map correction after allocation of active land use types:
        set AGB to 0 where no longer forest (types) remain(s)."""

        current_gross_forest_map = ifthenelse(scalar(self.environment_map) == scalar(4), # type agroforestry
                                              scalar(1),
                                              scalar(self.null_mask_map))
        current_gross_forest_map = ifthenelse(scalar(self.environment_map) == scalar(5), # type plantations
                                              scalar(1),
                                              scalar(current_gross_forest_map))
        current_gross_forest_map = ifthenelse(scalar(self.environment_map) == scalar(8),  # type disturbed forest
                                              scalar(1),
                                              scalar(current_gross_forest_map))
        current_gross_forest_map = ifthenelse(scalar(self.environment_map) == scalar(9),  # type undisturbed forest
                                              scalar(1),
                                              scalar(current_gross_forest_map))

        self.AGB_map = ifthenelse(scalar(current_gross_forest_map) != scalar(1), # where no gross forest ...
                                  scalar(0), # ... there 0 AGB
                                  scalar(self.AGB_map)) # else stay the same


    # SH: LPB alternation - determine (forest) land use conflict in restricted areas
    def determine_areas_of_forest_land_use_conflict_in_restricted_areas(self):
        """ Determine the pixels of all LUTs except 08 and 09 (forest) which are now allocated in restricted areas and
        map them on a conflict map.
        AND
        Determine all from forest to active land use converted pixels in restricted areas."""
        print('DERIVING CONFLICT IN RESTRICTED AREAS ...')

        # TYPE 1) All new land use that is not forest and takes place in restricted areas is declared conflict (assumption is, that restricted areas are also always forest protection zones)
        # determine changed cells in the whole map (so to get only the active land use cells)
        changed_environment_map = ifthenelse(scalar(self.environment_map_last_timestep) != scalar(self.environment_map),
                                             scalar(self.environment_map), # this contains only pixels of the dynamic land use types or of succession
                                             scalar(self.null_mask_map))
        # now determine only changed cells in the restricted areas
        all_new_land_use_in_restricted_areas_map = ifthenelse(scalar(self.static_restricted_areas_map) == scalar(1),
                                                              scalar(changed_environment_map),
                                                              scalar(self.null_mask_map))
        # select only the five active land use types
        new_LUT01_in_restricted_areas_map = ifthenelse(scalar(all_new_land_use_in_restricted_areas_map) == scalar(1),
                                                       boolean(1),
                                                       boolean(self.null_mask_map))
        new_LUT02_in_restricted_areas_map = ifthenelse(scalar(all_new_land_use_in_restricted_areas_map) == scalar(2),
                                                       boolean(1),
                                                       boolean(self.null_mask_map))
        new_LUT03_in_restricted_areas_map = ifthenelse(scalar(all_new_land_use_in_restricted_areas_map) == scalar(3),
                                                       boolean(1),
                                                       boolean(self.null_mask_map))
        new_LUT04_in_restricted_areas_map = ifthenelse(scalar(all_new_land_use_in_restricted_areas_map) == scalar(4),
                                                       boolean(1),
                                                       boolean(self.null_mask_map))
        new_LUT05_in_restricted_areas_map = ifthenelse(scalar(all_new_land_use_in_restricted_areas_map) == scalar(5),
                                                       boolean(1),
                                                       boolean(self.null_mask_map))
        # incorporate all 5 into one boolean map
        boolean_conflict_map_land_use_in_restricted_areas = pcror(new_LUT01_in_restricted_areas_map, new_LUT02_in_restricted_areas_map)
        boolean_conflict_map_land_use_in_restricted_areas = pcror(boolean_conflict_map_land_use_in_restricted_areas, new_LUT03_in_restricted_areas_map)
        boolean_conflict_map_land_use_in_restricted_areas = pcror(boolean_conflict_map_land_use_in_restricted_areas, new_LUT04_in_restricted_areas_map)
        boolean_conflict_map_land_use_in_restricted_areas = pcror(boolean_conflict_map_land_use_in_restricted_areas, new_LUT05_in_restricted_areas_map)

        # now count the pixels and save the
        all_new_active_land_use_pixels_in_restricted_areas = int(maptotal(scalar(boolean_conflict_map_land_use_in_restricted_areas)))
        print('all_new_active_land_use_pixels_in_restricted_areas:', all_new_active_land_use_pixels_in_restricted_areas)
        scalar_boolean_conflict_map_land_use_in_restricted_areas = scalar(boolean_conflict_map_land_use_in_restricted_areas)

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'luc'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar_boolean_conflict_map_land_use_in_restricted_areas,
               os.path.join(Filepaths.folder_land_use_conflict, str(self.current_sample_number),output_map_name))


        # TYPE 2) Only converted pixels of forest to other land use in restricted areas are declared conflict (assumption is, that only additional conversion of forest is prohibited)
        # first extract the restricted areas in the last environment map
        restricted_areas_last_environment_map = ifthenelse(scalar(self.static_restricted_areas_map) == scalar(1),
                                                           nominal(self.environment_map_last_timestep),
                                                           nominal(self.null_mask_map))
        # then determine the forest pixels in the last environment
        forest_in_restricted_areas_last_environment_map = ifthenelse(scalar(restricted_areas_last_environment_map) == scalar(8), # extract the disturbed forest
                                                                     boolean(1),
                                                                     boolean(self.null_mask_map))
        forest_in_restricted_areas_last_environment_map = ifthenelse(scalar(restricted_areas_last_environment_map) == scalar(9), # extract the undisturbed forest
                                                                     boolean(1),
                                                                     boolean(forest_in_restricted_areas_last_environment_map))
        # now extract the current environment in restricted areas only for the former existing forest pixels
        current_environment_on_forest_pixels_in_last_environment_map = ifthenelse(forest_in_restricted_areas_last_environment_map,
                                                                                  scalar(self.environment_map),
                                                                                  scalar(self.null_mask_map))
        # if they are not forest any longer, map them on the conflict map
        boolean_disturbed_pixels_map = ifthenelse(scalar(current_environment_on_forest_pixels_in_last_environment_map) == scalar(8),
                                                  boolean(1),
                                                  boolean(self.null_mask_map))
        boolean_disturbed_and_undisturbed_pixels_map = ifthenelse(scalar(current_environment_on_forest_pixels_in_last_environment_map) == scalar(9),
                                                                  boolean(1),
                                                                  boolean(boolean_disturbed_pixels_map))
        boolean_conflict_map_land_use_on_former_forest_in_restricted_areas = ifthenelse(pcrnot(boolean_disturbed_and_undisturbed_pixels_map),
                                                                                        boolean(current_environment_on_forest_pixels_in_last_environment_map),
                                                                                        boolean(self.null_mask_map))
        # now count the pixels and save the conflict pixels in the according sub-folder
        all_new_active_land_use_pixels_on_former_forest_in_restricted_areas = int(maptotal(scalar(boolean_conflict_map_land_use_on_former_forest_in_restricted_areas)))
        print('all_new_active_land_use_pixels_on_former_forest_in_restricted_areas:', all_new_active_land_use_pixels_on_former_forest_in_restricted_areas)
        scalar_boolean_conflict_map_land_use_on_former_forest_in_restricted_areas = scalar(boolean_conflict_map_land_use_on_former_forest_in_restricted_areas)

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'fluc'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar_boolean_conflict_map_land_use_on_former_forest_in_restricted_areas,
               os.path.join(Filepaths.folder_forest_land_use_conflict, str(self.current_sample_number), output_map_name))

        print('DERIVING CONFLICT IN RESTRICTED AREAS DONE')




    # SH: LPB alternation - for demand in built up rule of three approach grab the last extent
    def update_built_up_area_last_time_step(self):
        """ Update the information for built-up area to be used in the next time step for demand in new built-up area.
        Depends on the scenario chosen in Parameters.get_streets_input_decision_for_calculation_of_built_up()."""

        if Parameters.get_streets_input_decision_for_calculation_of_built_up() is True:
            LUT01_scalar_map = ifthenelse(self.environment_map == 1,
                                          scalar(1),
                                          scalar(self.null_mask_map))
            self.built_up_area_last_time_step = math.ceil(maptotal(LUT01_scalar_map))
        else:
            LUT01_scalar_map = ifthenelse(self.environment_map == 1,
                                          scalar(1),
                                          scalar(self.null_mask_map))
            built_up_minus_streets_map = ifthenelse(scalar(self.streets_map) == scalar(1),
                                                    scalar(0),
                                                    scalar(LUT01_scalar_map))
            self.built_up_area_last_time_step = math.ceil(maptotal(built_up_minus_streets_map))

        print('updating built-up area last time step done')

    # SH: LPB alternation - plantation depended changes
    def update_plantation_information(self):
        """ Updates the on new plantation plots or deforested plantation plots depending maps."""
        print('updating information from new or deforested plantations initialized ...')

        # First, get the new deforested plantation plots if something changed and correct the succession map
        if self.new_plantations_deforested_map is not None:
            self.succession_age_map = ifthenelse(scalar(self.new_plantations_deforested_map) == scalar(1),
                                             scalar(1),
                                             scalar(self.succession_age_map))

            self.AGB_map = ifthenelse(scalar(self.new_plantations_deforested_map) == scalar(1),
                                      scalar(0),
                                      scalar(self.AGB_map))
        else:
            pass

        # Secondly, get the new plantation plots if something changed and correct the plantation age map, the rotation period map, the succession map and the AGB map
        if self.new_plantations_map is not None:

            self.plantation_age_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                                     scalar(self.year),  # add the new plantation pixels to the map
                                                     scalar(self.plantation_age_map))

            self.plantation_rotation_period_end_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                                                 scalar(self.year) + scalar(
                                                                     Parameters.get_mean_plantation_rotation_period_end()),
                                                                 # add the new harvest year to the map
                                                                 scalar(self.plantation_rotation_period_end_map))

            # self.succession_age_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
            #                                      scalar(0),
            #                                      scalar(self.succession_age_map))

            # correct the AGB_map where a new plantation pixel is located
            if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit':
                self.AGB_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                          scalar(self.projection_potential_annual_plantation_AGB_increment_map),
                                          scalar(self.AGB_map))

            elif Parameters.get_annual_AGB_increment_simulation_decision() == 'stochastic':
                plantation_AGB_increment_minimum = \
                    self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['plantation'][0]
                plantation_AGB_increment_maximum = \
                    self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['plantation'][1]

                stochastic_plantation_AGB_increment_value = Parameters.get_rng().uniform(plantation_AGB_increment_minimum,
                                                                            plantation_AGB_increment_maximum)

                self.AGB_map = ifthenelse(scalar(self.new_plantations_map) == scalar(1),
                                          scalar(stochastic_plantation_AGB_increment_value),
                                          scalar(self.AGB_map))
        else:
            pass
        print('updating information from new or deforested plantations done')

    # SH&ML: LPB alternation - incorporated forest succession
    def update_succession(self):
        """ Implement succession of LUTs depending on type and age."""
        print('calculating succession initialized ...')

        # Succession of LUTs is based on available LUTs, location and time passed by. In LPB based on Copernicus the succession is:
        # from (source LUT to) herbaceous vegetation (LUT06) to shrubs(LUT07) to disturbed forest(LUT08) to undisturbed forest(LUT09)
        # (based on TMF: remaining cells of disturbed forest (LUT08) plus TMF undisturbed forest(LUT09)) where a potential forest pixel is situated.
        # access lookuptable and according LUTs age map and change environment accordingly

        herbaceous_vegetation_succession_rules = Filepaths.file_static_succession_herbaceous_vegetation_input  # imports the timely succession rules from the plain text lookup table
        shrubs_succession_rules = Filepaths.file_static_succession_shrubs_input  # imports the timely succession rules from the plain text lookup table
        forest_succession_rules = Filepaths.file_static_succession_forest_input  # imports the timely succession rules from the plain text lookup table

        succession_land_use_types_list = [6,  # herbaceous vegetation (succession stage 1)
                                          7,  # shrubs (succession stage 2)
                                          8,  # disturbed forest (succession stage 3)
                                          9,  # undisturbed forest (succession stage 4 - hypothetical in a run < 100 years for new disturbed cells, only for existing TMF undisturbed cells as upgrade to "primary")
                                          14,  # cropland-annual - - abandoned (source LUT)
                                          15,  # pasture - - abandoned (source LUT)
                                          16,  # agroforestry - - abandoned (source LUT)
                                          17,  # net forest - - deforested (source LUT)
                                          18]  # plantation - - deforested (source LUT)

        # correct the succession_age_map (cells may got overwritten by land use change)
        current_distribution_of_succession_LUTs_and_their_age_map = self.null_mask_map
        for a_type in succession_land_use_types_list:
            a_types_map = ifthenelse(scalar(self.environment_map) == scalar(a_type), # only pick the currently still present cells for the LUTs
                                     scalar(self.succession_age_map), # note their age
                                     scalar(self.null_mask_map)) # else set to 0
            current_distribution_of_succession_LUTs_and_their_age_map += a_types_map # combine them all in one map

        self.succession_age_map = current_distribution_of_succession_LUTs_and_their_age_map # re-assign the current map

        # check prior to change the amount of cells for a succession LUT
        for a_type in succession_land_use_types_list:
            prior_succession_number = int(maptotal(scalar(boolean(self.environment_map == a_type))))
            print('LUT:', a_type, 'prior succession:', prior_succession_number, Parameters.get_pixel_size())

        # draw the current map for later comparison
        prior_succession_environment_map = self.environment_map

        # PNV = herbaceous vegetation (class 1); do the change according to age - on herbaceous vegetation cells
        temporal_environment_herbaceous_vegetation_succession_map = lookupscalar(herbaceous_vegetation_succession_rules,
                                                                                 scalar(self.environment_map),
                                                                                 scalar(self.succession_age_map),
                                                                                 scalar(self.projection_potential_natural_vegetation_distribution_map))

        self.environment_map = cover(nominal(temporal_environment_herbaceous_vegetation_succession_map), nominal(self.environment_map))

        # PNV = shrubs (class 2); do the change according to age - on potential shrubs cells
        temporal_environment_shrubs_succession_map = lookupscalar(shrubs_succession_rules,
                                                                  scalar(self.environment_map),
                                                                  scalar(self.succession_age_map),
                                                                  scalar(self.projection_potential_natural_vegetation_distribution_map))

        self.environment_map = cover(nominal(temporal_environment_shrubs_succession_map), nominal(self.environment_map))

        # PNV = forest (class 3); do the change according to age - on potential forest cells

        temporal_environment_forest_succession_map = lookupscalar(forest_succession_rules,
                                                                  scalar(self.environment_map),
                                                                  scalar(self.succession_age_map),
                                                                  scalar(self.projection_potential_natural_vegetation_distribution_map))


        self.environment_map = cover(nominal(temporal_environment_forest_succession_map), nominal(self.environment_map)) # apply the change to the LULC map

        # draw the map for comparison
        post_succession_environment_map = self.environment_map

        # check the impact of change
        for a_type in succession_land_use_types_list:
            post_succession_number = int(maptotal(scalar(boolean(self.environment_map == a_type))))
            print('LUT:', a_type, 'post succession:', post_succession_number, Parameters.get_pixel_size())

        # update the succession age now that the environment has changed
        self.succession_age_map = ifthenelse(post_succession_environment_map != prior_succession_environment_map, # where the map changed
                                             scalar(1),  # initialize the new pixels
                                             scalar(self.succession_age_map))  # else keep the age information as is

        print('calculating succession done')


    # SH: LPB alternation - AGB post succession
    def update_AGB_map_new_agroforestry_and_disturbed_pixels(self):
        """This methods sets the initial AGB value for new forest type cells (plantation cells are handled in the plantation method)."""

        # NEW AGROFORESTRY PIXELS
        # filter the environment_maps
        all_agroforestry_pixels_map = ifthenelse(scalar(self.environment_map) == scalar(4),
                                                 scalar(1),
                                                 scalar(self.null_mask_map))

        old_agroforestry_pixels_map = ifthenelse(scalar(self.environment_map_last_timestep) == (4),
                                                 scalar(1),
                                                 scalar(self.null_mask_map))

        new_agroforestry_pixels_map = ifthenelse(all_agroforestry_pixels_map == old_agroforestry_pixels_map,
                                                 scalar(0),
                                                 scalar(all_agroforestry_pixels_map))

        # correct the AGB_map where a new agroforestry pixel is located
        if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit':
            self.AGB_map = ifthenelse(scalar(new_agroforestry_pixels_map) == scalar(1),
                                      scalar(
                                          self.projection_potential_annual_disturbed_AGB_increment_map), # we assume, that agroforestry might have same ranges as disturbed forest
                                      scalar(self.AGB_map))
        elif Parameters.get_annual_AGB_increment_simulation_decision() == 'stochastic':
            agroforestry_AGB_increment_minimum = \
            self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['agroforestry'][0]
            agroforestry_AGB_increment_maximum = \
            self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['agroforestry'][1]

            stochastic_agroforestry_AGB_increment_value = Parameters.get_rng().uniform(agroforestry_AGB_increment_minimum,
                                                                        agroforestry_AGB_increment_maximum)

            self.AGB_map = ifthenelse(scalar(new_agroforestry_pixels_map) == scalar(1),
                                      scalar(stochastic_agroforestry_AGB_increment_value),
                                      scalar(self.AGB_map))

        # NEW DISTURBED FOREST PIXELS
        # filter the disturbed pixels after succession
        all_disturbed_forest_pixels_map = ifthenelse(scalar(self.environment_map) == scalar(8),
                                                     scalar(1),
                                                     scalar(self.null_mask_map))

        old_disturbed_forest_pixels_map = ifthenelse(scalar(self.environment_map_last_timestep) == (8),
                                                     scalar(1),
                                                     scalar(self.null_mask_map))

        new_disturbed_forest_pixels_map = ifthenelse(all_disturbed_forest_pixels_map == old_disturbed_forest_pixels_map,
                                                     scalar(0),
                                                     scalar(all_disturbed_forest_pixels_map))

        # correct the AGB_map where a new disturbed pixel is located
        if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit':
            self.AGB_map = ifthenelse(scalar(new_disturbed_forest_pixels_map) == scalar(1),
                                      scalar(self.projection_potential_annual_disturbed_AGB_increment_map * Parameters.get_mean_succession_to_disturbed_forest_timeframe_for_the_country()), # approximation: years of AGB accumulated
                                      scalar(self.AGB_map))
        elif Parameters.get_annual_AGB_increment_simulation_decision() == 'stochastic':
            disturbed_AGB_increment_minimum = self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['disturbed_forest'][0]
            disturbed_AGB_increment_maximum = self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['disturbed_forest'][1]

            stochastic_disturbed_AGB_increment_value = Parameters.get_rng().uniform(disturbed_AGB_increment_minimum, disturbed_AGB_increment_maximum)
            # Parameters.get_rng().integers

            self.AGB_map = ifthenelse(scalar(new_disturbed_forest_pixels_map) == scalar(1),
                                      scalar(stochastic_disturbed_AGB_increment_value * Parameters.get_mean_succession_to_disturbed_forest_timeframe_for_the_country()), # approximation: years of AGB accumulated
                                      scalar(self.AGB_map))

        if probabilistic_output_options_dictionary['AGB_map'] == True:
            # store output
            time_step = self.time_step
            pcraster_conform_map_name = 'AGB'
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(scalar(self.AGB_map),
                   os.path.join(Filepaths.folder_AGB, str(self.current_sample_number),
                                output_map_name))

    # SH: LPB alternation - update status new forest fringe
    def update_forest_fringe_disturbed(self):
        """All forest fringe cells are declared disturbed due to peripheral zone effects."""

        all_forest_cells_map = ifthenelse(self.environment_map == 8, # disturbed forest
                                          scalar(1),
                                          scalar(self.null_mask_map))

        all_forest_cells_map = ifthenelse(self.environment_map == 9,  # undisturbed forest
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

        self.environment_map = cover(nominal(new_disturbed_forest_fringe), nominal(self.environment_map))

        # adjust the succession age to prevent transformation to undisturbed forest
        disturbed_forest_fringe_age_map = ifthen(scalar(forest_fringe_map) > scalar(0),
                                                 scalar(1))

        self.succession_age_map = cover(scalar(disturbed_forest_fringe_age_map), scalar(self.succession_age_map)) # set back the clock for impacted forest cells

        # now store the succession age map if desired for the MC average use in mplc for the GIF
        if probabilistic_output_options_dictionary['succession_age_map'] == True:
            # store output
            time_step = self.time_step
            pcraster_conform_map_name = 'suag'
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(scalar(self.succession_age_map),
                   os.path.join(Filepaths.folder_succession_age, str(self.current_sample_number),
                                output_map_name))

    # SH: LPB alternation - net forest correction
    def update_net_forest_map(self):
        """subtract converted, succession and deforested pixels from the net forest map, only disturbed and undisturbed forest pixels stay.
        For the time after the population peak add new pixels of disturbed and undisturbed forest at the fringe"""

        # First clean out all pixels that are no longer forest
        environment_in_net_forest_map = ifthenelse(scalar(self.net_forest_map) == scalar(1),
                                                   scalar(self.environment_map),
                                                   scalar(self.null_mask_map))

        self.net_forest_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(8),  # get disturbed pixels
                                         boolean(1),
                                         boolean(self.null_mask_map))

        self.net_forest_map = ifthenelse(scalar(environment_in_net_forest_map) == scalar(9),  # get undisturbed pixels
                                         boolean(1),
                                         boolean(self.net_forest_map))

        # Secondly, check for new pixels in the immediate surrounding pixels

        # 2.1 define the forest fringe again
        scalar_self = scalar(self.net_forest_map)
        # SH: Count cells within a 3x3 window to determine the forest fringe cells
        window_length = 3 * Parameters.get_cell_length_in_m()  # 9(-1) cells if not forest fringe
        number_neighbors_net_forest_map = windowtotal(scalar_self, window_length) - scalar_self

        net_forest_fringe_map = ifthen(scalar(number_neighbors_net_forest_map) < scalar(8),
                                       # forest fringes are determined by missing pixels in the window (less than 9 (-1) present)
                                       scalar(1))

        boolean_net_forest_fringe_map = boolean(net_forest_fringe_map)

        # 2.2. built a buffer around it
        spread_map = spreadmaxzone(boolean_net_forest_fringe_map, 0, 1, Parameters.get_cell_length_in_m() * 2)

        boolean_net_forest_fringe_buffer_map = ifthenelse(scalar(spread_map) > scalar(0),
                                                          scalar(1),
                                                          scalar(self.null_mask_map))

        # 2.3 get the disturbed and undisturbed pixels in this area and add them to net forest
        environment_in_net_forest_fringe_buffer_map = ifthenelse(scalar(boolean_net_forest_fringe_buffer_map) == scalar(1),
                                                                 scalar(self.environment_map),
                                                                 scalar(self.null_mask_map))

        disturbed_pixels_in_buffer_map = ifthenelse(scalar(environment_in_net_forest_fringe_buffer_map) == scalar(8),
                                                    scalar(1),
                                                    scalar(self.null_mask_map))
        disturbed_and_undisturbed_pixels_in_buffer_map = ifthenelse(scalar(environment_in_net_forest_fringe_buffer_map) == scalar(9),
                                                                    scalar(1),
                                                                    scalar(disturbed_pixels_in_buffer_map))
        temporal_net_forest_map = ifthen(scalar(disturbed_and_undisturbed_pixels_in_buffer_map) == scalar(1),
                                         scalar(1))

        self.net_forest_map = cover(scalar(temporal_net_forest_map), scalar(self.net_forest_map))

        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            # store output
            time_step = self.time_step
            pcraster_conform_map_name = 'netf'
            output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
                pcraster_conform_map_name, time_step)
            report(scalar(self.net_forest_map),
                   os.path.join(Filepaths.folder_net_forest, str(self.current_sample_number),
                                output_map_name))

        print('updating net forest map done')

    # already implemented for model stage 2 (expansion of degradation by local wood consumption)
    # SH: LPB alternation - calculate forest degradation and regeneration
    def update_forest_degradation_and_regeneration(self):
        """SH: INNOVATION degradation and regeneration based on AGB after the time step:
        increment has been applied and p.r.n. anthropogenic outtake subtracted in relation to the cells relative spatially-explicit potential maximum"""

        print('updating forest degradation and regeneration initiated ...')

        print('calculating user-defined AGB content in percent maps')
        user_defined_dictionary_of_thresholds_in_percent = Parameters.get_forest_degradation_regeneration_AGB_content_in_percent_thresholds()

        lower_AGB_content_in_percent_threshold = user_defined_dictionary_of_thresholds_in_percent['degradation_severe_regeneration_low']
        user_defined_lower_AGB_threshold_map = (self.projection_potential_maximum_undisturbed_AGB_map / 100) * lower_AGB_content_in_percent_threshold

        higher_AGB_content_in_percent_threshold = user_defined_dictionary_of_thresholds_in_percent['degradation_low_regeneration_high']
        user_defined_higher_AGB_threshold_map = (self.projection_potential_maximum_undisturbed_AGB_map / 100) * higher_AGB_content_in_percent_threshold
        print('calculating user-defined AGB content in percent maps done')


        # FOREST MAP
        forest_map = ifthenelse(self.environment_map == 8,
                                scalar(1),
                                scalar(self.null_mask_map))
        forest_map = ifthenelse(self.environment_map == 9,
                                scalar(1),
                                scalar(forest_map))

        # REGENERATION (more or equal AGB>0 than last time step)
        basic_regeneration_map = ifthen(scalar(self.AGB_map) >= scalar(self.AGB_map_last_time_step),
                                        scalar(self.AGB_map))
        basic_regeneration_map = ifthen(scalar(basic_regeneration_map) > scalar(0),
                                        scalar(basic_regeneration_map))
        basic_regeneration_map = ifthen(scalar(forest_map) == scalar(1),
                                        basic_regeneration_map)

        # > 0 to 1/3 = low regeneration
        self.forest_regeneration_low_map = ifthen(basic_regeneration_map <= user_defined_lower_AGB_threshold_map,
                                                  boolean(1))

        self.forest_regeneration_low_map = cover(boolean(self.forest_regeneration_low_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Rlow'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_regeneration_low_map),
               os.path.join(Filepaths.folder_regeneration_low, str(self.current_sample_number),
                            output_map_name))

        # > 1/3 to 2/3 = medium regeneration
        self.forest_regeneration_medium_map = ifthen(basic_regeneration_map > user_defined_lower_AGB_threshold_map,
                                                     scalar(basic_regeneration_map))

        self.forest_regeneration_medium_map = ifthen(self.forest_regeneration_medium_map <= user_defined_higher_AGB_threshold_map,
                                                     scalar(self.forest_regeneration_medium_map))

        self.forest_regeneration_medium_map = cover(boolean(self.forest_regeneration_medium_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Rmed'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_regeneration_medium_map),
               os.path.join(Filepaths.folder_regeneration_medium, str(self.current_sample_number),
                            output_map_name))

        # > 2/3 to < max = high regeneration
        self.forest_regeneration_high_map = ifthen(basic_regeneration_map > user_defined_higher_AGB_threshold_map,
                                                   scalar(basic_regeneration_map))

        self.forest_regeneration_high_map = ifthen(self.forest_regeneration_high_map < self.projection_potential_maximum_undisturbed_AGB_map,
                                                   scalar(self.forest_regeneration_high_map))

        self.forest_regeneration_high_map = cover(boolean(self.forest_regeneration_high_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Rhig'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_regeneration_high_map),
               os.path.join(Filepaths.folder_regeneration_high, str(self.current_sample_number),
                            output_map_name))

        # max = full regeneration (still not all primary traits given)
        self.forest_regeneration_full_map = ifthen(basic_regeneration_map >= self.projection_potential_maximum_undisturbed_AGB_map,
                                                   boolean(1))

        self.forest_regeneration_full_map = cover(boolean(self.forest_regeneration_full_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Rful'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_regeneration_full_map),
               os.path.join(Filepaths.folder_regeneration_full, str(self.current_sample_number),
                            output_map_name))



        # DEGRADATION (less AGB than last time step)
        basic_degradation_map = ifthen(scalar(self.AGB_map) < scalar(self.AGB_map_last_time_step),
                                       scalar(self.AGB_map))
        basic_degradation_map = ifthen(scalar(forest_map) == scalar(1),
                                        basic_degradation_map)

        # < max to > 2/3 = low degradation
        self.forest_degradation_low_map = ifthen(basic_degradation_map < self.projection_potential_maximum_undisturbed_AGB_map,
                                                 scalar(basic_degradation_map))

        self.forest_degradation_low_map = ifthen (self.forest_degradation_low_map > user_defined_higher_AGB_threshold_map,
                                                  boolean(1))

        self.forest_degradation_low_map = cover(boolean(self.forest_degradation_low_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Dlow'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_degradation_low_map),
               os.path.join(Filepaths.folder_degradation_low, str(self.current_sample_number),
                            output_map_name))

        # 2/3 to > 1/3 = moderate degradation
        self.forest_degradation_moderate_map = ifthen(basic_degradation_map <= user_defined_higher_AGB_threshold_map,
                                                      scalar(basic_degradation_map))

        self.forest_degradation_moderate_map = ifthen(self.forest_degradation_moderate_map > user_defined_lower_AGB_threshold_map,
                                                      boolean(1))

        self.forest_degradation_moderate_map = cover(boolean(self.forest_degradation_moderate_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Dmod'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_degradation_moderate_map),
               os.path.join(Filepaths.folder_degradation_moderate, str(self.current_sample_number),
                            output_map_name))

        # 1/3 to > 0 = severe degradation
        self.forest_degradation_severe_map = ifthen(basic_degradation_map <= user_defined_lower_AGB_threshold_map,
                                                    scalar(basic_degradation_map))

        self.forest_degradation_severe_map = ifthen(scalar(self.forest_degradation_severe_map) > scalar(0),
                                                    boolean(1))

        self.forest_degradation_severe_map = cover(boolean(self.forest_degradation_severe_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Dsev'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_degradation_severe_map),
               os.path.join(Filepaths.folder_degradation_severe, str(self.current_sample_number),
                            output_map_name))

        # if AGB is now = 0 because of allocation of LUT17, i.e. absolute degradation, the plot is completely deforested
        self.forest_degradation_absolute_map = ifthen(scalar(self.environment_map) == scalar(17),
                                                      boolean(1))

        self.forest_degradation_absolute_map = cover(boolean(self.forest_degradation_absolute_map), boolean(self.null_mask_map))

        # store output
        time_step = self.time_step
        pcraster_conform_map_name = 'Dabs'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(scalar(self.forest_degradation_absolute_map),
               os.path.join(Filepaths.folder_degradation_absolute, str(self.current_sample_number),
                            output_map_name))

        print('updating degradation/regeneration maps done')

    # SH: original PLUC method
    def get_environment(self):
        """Return the current land use map."""
        print('current environment map returned')
        return self.environment_map

###################################################################################################

class LandUseChangeModel(DynamicModel, MonteCarloModel):
    def __init__(self):
        DynamicModel.__init__(self)
        MonteCarloModel.__init__(self)
        setclone(f"{Filepaths.file_static_null_mask_input}.map")

    def premcloop(self):
        print('\n>>> running premcloop ...')

        # SH:LPB alternation: for each sample create a folder in the according subfolder where probabilistic information shall be stored
        # for those folders also implement the MC-average folder for intermediate results
        probabilistic_output_folders_list = [Filepaths.folder_dynamic_environment_map_probabilistic]
        if Parameters.get_order_of_forest_deforestation_and_conversion() is True:
            if probabilistic_output_options_dictionary['deforested_net_forest_map'] == True:
                probabilistic_output_folders_list.append(Filepaths.folder_deforested_before_conversion)
        if probabilistic_output_options_dictionary['conflict_maps'] == True:
            probabilistic_output_folders_list.append(Filepaths.folder_land_use_conflict)
            probabilistic_output_folders_list.append(Filepaths.folder_forest_land_use_conflict)
        if probabilistic_output_options_dictionary['AGB_map'] == True:
            probabilistic_output_folders_list.append(Filepaths.folder_AGB)
        if probabilistic_output_options_dictionary['net_forest_map'] == True:
            probabilistic_output_folders_list.append(Filepaths.folder_net_forest)
        if probabilistic_output_options_dictionary['degradation_regeneration_maps'] == True:
            probabilistic_output_folders_list.append(Filepaths.folder_degradation_low)
            probabilistic_output_folders_list.append(Filepaths.folder_degradation_moderate)
            probabilistic_output_folders_list.append(Filepaths.folder_degradation_severe)
            probabilistic_output_folders_list.append(Filepaths.folder_degradation_absolute)
            probabilistic_output_folders_list.append(Filepaths.folder_regeneration_low)
            probabilistic_output_folders_list.append(Filepaths.folder_regeneration_medium)
            probabilistic_output_folders_list.append(Filepaths.folder_regeneration_high)
            probabilistic_output_folders_list.append(Filepaths.folder_regeneration_full)
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and probabilistic_output_options_dictionary['yield_maps'] == True:
            if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                probabilistic_output_folders_list.append(Filepaths.folder_LUT02_cropland_annual_crop_yields)
            if 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                probabilistic_output_folders_list.append(Filepaths.folder_LUT03_pasture_livestock_yields)
            if 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                probabilistic_output_folders_list.append(Filepaths.folder_LUT04_agroforestry_crop_yields)
        if probabilistic_output_options_dictionary['succession_age_map'] == True:
            probabilistic_output_folders_list.append(Filepaths.folder_succession_age)

        maximum_sample_number = number_of_samples_set
        range_of_samples = range(1, (maximum_sample_number + 1))
        for a_folder in probabilistic_output_folders_list:
            for a_sample in range_of_samples:
                sample_folder_in_subfolder = os.path.join(a_folder, str(a_sample))
                os.makedirs(sample_folder_in_subfolder, exist_ok=True)

        # SH: LPB alternation - management variables
        self.time_step = None
        self.current_sample_number = None
        self.year = Parameters.get_initial_simulation_year()


        # ORIGINAL PLUC VARIABLES
        # SH: a map depicting the study area with only zeros and missing values, for calculation purposes
        self.null_mask_map = self.readmap(Filepaths.file_static_null_mask_input)
        # dem
        self.dem_map = self.readmap(Filepaths.file_static_dem_input)
        # export the model internal slope map
        slope_map = slope(scalar(self.dem_map))
        report(slope_map,
               os.path.join(Filepaths.folder_slope, 'model_internal_slope_map_in_percent.map'))
        print('model_internal_slope_map_in_percent produced and stored in:',
              Filepaths.folder_slope)
        # streets (former roads, finer level in LPB)
        streets_map = self.readmap(Filepaths.file_static_streets_input)
        self.streets_map = cover(streets_map, boolean(self.null_mask_map))
        # water (here called freshwater, as we depict only freshwater and not the sea with this file)
        freshwater_map = self.readmap(Filepaths.file_static_freshwater_input)
        self.freshwater_map = cover(freshwater_map, boolean(self.null_mask_map))
        # cities
        cities_map = self.readmap(Filepaths.file_static_cities_input)
        self.cities_map = cover(cities_map, boolean(self.null_mask_map))
        # HINT: SH: in LPB we do not use static excluded areas, but static restricted areas which can be overwritten in a second allocation search,
        # substitute the nullmask with a map if you want to simulate permanently excluded areas
        static_areas_on_which_no_allocation_occurs_map = self.readmap(Filepaths.file_static_excluded_areas_input)
        self.static_areas_on_which_no_allocation_occurs_map = cover(
            boolean(static_areas_on_which_no_allocation_occurs_map), boolean(self.null_mask_map))
        self.noise_map = uniform(1) / 10000
        # JV: Check which maps should get random noise (population)
        # JV: List of land use types in order of 'who gets to choose first'
        self.active_land_use_types_list = Parameters.get_active_land_use_types_list()
        # JV: Input values from Parameters file
        self.related_land_use_types_dictionary = Parameters.get_related_land_use_types_dictionary()
        self.suitability_factors_dictionary = Parameters.get_suitability_factors_dictionary()
        self.weights_dictionary = Parameters.get_weights_dictionary()
        self.variables_super_dictionary = Parameters.get_variables_super_dictionary()
        self.static_LUTs_on_which_no_allocation_occurs_list = Parameters.get_static_LUTs_on_which_no_allocation_occurs() #SH: renamed nogo
        self.difficult_terrain_slope_restriction_dictionary = Parameters.get_difficult_terrain_slope_restriction_dictionary() # this is alternated in LPB

        # SH: LPB ALTERED PER SCENARIO RUN AND ADDITIONAL VARIABLES
        # SH: LPB alternation:
        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            # AGB map depicts the spatially explicit distribution of AGB in the study area
            self.AGB_map = readmap(Filepaths.file_initial_AGB_input)
            self.AGB_map = cover(scalar(self.AGB_map), scalar(self.null_mask_map))
            if Parameters.get_worst_case_scenario_decision() == True:
                # if the worst case scenario is to be simulated within LPB-RAP, the module needs the original AGB information additionally
                report(self.AGB_map, os.path.join(Filepaths.folder_inputs_initial_worst_case_scenario, 'initial_AGB_input.map'))
            # net forest is forest according to national maps
            net_forest_map = self.readmap(Filepaths.file_initial_net_forest_input)
            self.net_forest_map = cover(net_forest_map, boolean(self.null_mask_map))
            if Parameters.get_worst_case_scenario_decision() == True:
                # if the worst case scenario is to be simulated within LPB-RAP, the module needs the original net forest information additionally
                report(self.net_forest_map, os.path.join(Filepaths.folder_inputs_initial_worst_case_scenario, 'initial_net_forest_input.map'))
            # we added settlements for a finer level in LPB
            settlements_map = self.readmap(Filepaths.file_initial_settlements_input)
            self.settlements_map = cover(settlements_map, boolean(self.null_mask_map))
            if Parameters.get_presimulation_correction_step_needed() is True:
                self.initial_environment_map = self.readmap(Filepaths.file_initial_LULC_simulated_input)
            else:
                self.initial_environment_map = self.readmap(Filepaths.file_initial_LULC_input)
            if Parameters.get_worst_case_scenario_decision() == True:
                # if the worst case scenario is to be simulated within LPB-RAP, the module needs the original LULC information additionally
                initial_LULC_map = self.readmap(Filepaths.file_initial_LULC_input)
                report(initial_LULC_map, os.path.join(Filepaths.folder_inputs_initial_worst_case_scenario, 'initial_LULC_input.map'))
        elif Parameters.get_model_scenario() == 'no_conservation':
            self.initial_environment_map = self.readmap(
                Filepaths.file_initial_LULC_simulated_for_worst_case_scenario_input)
            # AGB map depicts the spatially explicit distribution of AGB in the study area
            self.AGB_map = readmap(Filepaths.file_initial_AGB_simulated_for_worst_case_scenario_input)
            self.AGB_map = cover(scalar(self.AGB_map), scalar(self.null_mask_map))
            # net forest is forest according to national maps
            self.net_forest_map = self.readmap(Filepaths.file_initial_net_forest_simulated_for_worst_case_scenario_input)
            self.net_forest_map = cover(boolean(self.net_forest_map), boolean(self.null_mask_map))
            # we added settlements for a finer level in LPB
            self.settlements_map = self.readmap(Filepaths.file_initial_settlements_simulated_for_worst_case_scenario_input)
            self.settlements_map = cover(boolean(self.settlements_map), boolean(self.null_mask_map))


        # the restricted areas are used for derivation of forest land use conflict
        static_restricted_areas_map = self.readmap(Filepaths.file_static_restricted_areas_input)
        self.static_restricted_areas_map = cover(boolean(static_restricted_areas_map), boolean(self.null_mask_map))

        if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
            # plantation age depicts until here the year of origin of the current crop
            plantation_age_map = readmap(Filepaths.file_initial_plantation_age_input)
            self.plantation_age_map = cover(scalar(plantation_age_map), scalar(self.null_mask_map))
        elif Parameters.get_model_scenario() == 'no_conservation':
            self.plantation_age_map = self.null_mask_map # this map needs only transportation to LandUse, since it is there modelled stochastically
        self.succession_age_map = self.null_mask_map # (initial status)

        # regional_distances_for_agricultural_land_use_dictionary
        self.regional_distance_values_for_agricultural_land_use_dictionary = Parameters.get_regional_distance_values_for_agricultural_land_use_dictionary()
        # pre data setting:
        self.LUT02_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[2][0]
        self.LUT03_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[3][0]
        self.LUT04_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[4][0]

        self.LUT02_minimum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[2][1]
        self.LUT03_minimum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[3][1]
        self.LUT04_minimum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[4][1]

        self.LUT02_maximum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[2][2]
        self.LUT03_maximum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[3][2]
        self.LUT04_maximum_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[4][2]

        # population maps dictionary
        self.spatially_explicit_population_maps_dictionary = {
            'file_projection_decadal_population_2010_input': readmap(Filepaths.file_projection_decadal_population_2010_input),
            'file_projection_decadal_population_2020_input': readmap(Filepaths.file_projection_decadal_population_2020_input),
            'file_projection_decadal_population_2030_input': readmap(Filepaths.file_projection_decadal_population_2030_input),
            'file_projection_decadal_population_2040_input': readmap(Filepaths.file_projection_decadal_population_2040_input),
            'file_projection_decadal_population_2050_input': readmap(Filepaths.file_projection_decadal_population_2050_input),
            'file_projection_decadal_population_2060_input': readmap(Filepaths.file_projection_decadal_population_2060_input),
            'file_projection_decadal_population_2070_input': readmap(Filepaths.file_projection_decadal_population_2070_input),
            'file_projection_decadal_population_2080_input': readmap(Filepaths.file_projection_decadal_population_2080_input),
            'file_projection_decadal_population_2090_input': readmap(Filepaths.file_projection_decadal_population_2090_input),
            'file_projection_decadal_population_2100_input': readmap(Filepaths.file_projection_decadal_population_2100_input),
        }




        # climate period inputs dictionary
        self.climate_period_inputs_dictionary = {
            # projections in time and/or space for:

            # potential forest distribution
            'file_projection_potential_natural_vegetation_distribution_2018_2020_input': readmap(Filepaths.file_projection_potential_natural_vegetation_distribution_2018_2020_input),
            'file_projection_potential_natural_vegetation_distribution_2021_2040_input': readmap(Filepaths.file_projection_potential_natural_vegetation_distribution_2021_2040_input),
            'file_projection_potential_natural_vegetation_distribution_2041_2060_input': readmap(Filepaths.file_projection_potential_natural_vegetation_distribution_2041_2060_input),
            'file_projection_potential_natural_vegetation_distribution_2061_2080_input': readmap(Filepaths.file_projection_potential_natural_vegetation_distribution_2061_2080_input),
            'file_projection_potential_natural_vegetation_distribution_2081_2100_input': readmap(Filepaths.file_projection_potential_natural_vegetation_distribution_2081_2100_input),

            # potential maximum AGB
            'file_projection_potential_maximum_undisturbed_AGB_2018_2020_input': readmap(Filepaths.file_projection_potential_maximum_undisturbed_AGB_2018_2020_input),
            'file_projection_potential_maximum_undisturbed_AGB_2021_2040_input': readmap(Filepaths.file_projection_potential_maximum_undisturbed_AGB_2021_2040_input),
            'file_projection_potential_maximum_undisturbed_AGB_2041_2060_input': readmap(Filepaths.file_projection_potential_maximum_undisturbed_AGB_2041_2060_input),
            'file_projection_potential_maximum_undisturbed_AGB_2061_2080_input': readmap(Filepaths.file_projection_potential_maximum_undisturbed_AGB_2061_2080_input),
            'file_projection_potential_maximum_undisturbed_AGB_2081_2100_input': readmap(Filepaths.file_projection_potential_maximum_undisturbed_AGB_2081_2100_input),

            # INCREMENTS FOR MODEL STAGE 1 are stochastic values, these are just pre-coded dummy_maps for model stage 2 or 3 - if ESA AGB version 3 is suitable
            # could not be realized for Esmeraldas
            # potential AGB increment for undisturbed forest
            'file_projection_potential_annual_undisturbed_AGB_increment_2018_2020_input': self.null_mask_map,
            'file_projection_potential_annual_undisturbed_AGB_increment_2021_2040_input': self.null_mask_map,
            'file_projection_potential_annual_undisturbed_AGB_increment_2041_2060_input': self.null_mask_map,
            'file_projection_potential_annual_undisturbed_AGB_increment_2061_2080_input': self.null_mask_map,
            'file_projection_potential_annual_undisturbed_AGB_increment_2081_2100_input': self.null_mask_map,

            # potential AGB increment for disturbed forest
            'file_projection_potential_annual_disturbed_AGB_increment_2018_2020_input': self.null_mask_map,
            'file_projection_potential_annual_disturbed_AGB_increment_2021_2040_input': self.null_mask_map,
            'file_projection_potential_annual_disturbed_AGB_increment_2041_2060_input': self.null_mask_map,
            'file_projection_potential_annual_disturbed_AGB_increment_2061_2080_input': self.null_mask_map,
            'file_projection_potential_annual_disturbed_AGB_increment_2081_2100_input': self.null_mask_map,

            # potential AGB increment for plantation
            'file_projection_potential_annual_plantation_AGB_increment_2018_2020_input': self.null_mask_map,
            'file_projection_potential_annual_plantation_AGB_increment_2021_2040_input': self.null_mask_map,
            'file_projection_potential_annual_plantation_AGB_increment_2041_2060_input': self.null_mask_map,
            'file_projection_potential_annual_plantation_AGB_increment_2061_2080_input': self.null_mask_map,
            'file_projection_potential_annual_plantation_AGB_increment_2081_2100_input': self.null_mask_map
        }

        if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit':
            self.climate_period_inputs_dictionary.update({
                # INCREMENTS FOR MODEL STAGE 2 - if with ESA AGB version 3 data a sptially-explicit increment with meaningful regression can be derived
                # potential AGB increment for undisturbed forest
                'file_projection_potential_annual_undisturbed_AGB_increment_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_annual_undisturbed_AGB_increment_2018_2020_input),
                'file_projection_potential_annual_undisturbed_AGB_increment_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_annual_undisturbed_AGB_increment_2021_2040_input),
                'file_projection_potential_annual_undisturbed_AGB_increment_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_annual_undisturbed_AGB_increment_2041_2060_input),
                'file_projection_potential_annual_undisturbed_AGB_increment_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_annual_undisturbed_AGB_increment_2061_2080_input),
                'file_projection_potential_annual_undisturbed_AGB_increment_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_annual_undisturbed_AGB_increment_2081_2100_input),

                # potential AGB increment for disturbed forest
                'file_projection_potential_annual_disturbed_AGB_increment_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_annual_disturbed_AGB_increment_2018_2020_input),
                'file_projection_potential_annual_disturbed_AGB_increment_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_annual_disturbed_AGB_increment_2021_2040_input),
                'file_projection_potential_annual_disturbed_AGB_increment_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_annual_disturbed_AGB_increment_2041_2060_input),
                'file_projection_potential_annual_disturbed_AGB_increment_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_annual_disturbed_AGB_increment_2061_2080_input),
                'file_projection_potential_annual_disturbed_AGB_increment_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_annual_disturbed_AGB_increment_2081_2100_input),

                # potential AGB increment for plantation
                'file_projection_potential_annual_plantation_AGB_increment_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_annual_plantation_AGB_increment_2018_2020_input),
                'file_projection_potential_annual_plantation_AGB_increment_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_annual_plantation_AGB_increment_2021_2040_input),
                'file_projection_potential_annual_plantation_AGB_increment_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_annual_plantation_AGB_increment_2041_2060_input),
                'file_projection_potential_annual_plantation_AGB_increment_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_annual_plantation_AGB_increment_2061_2080_input),
                'file_projection_potential_annual_plantation_AGB_increment_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_annual_plantation_AGB_increment_2081_2100_input)
            })

        self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary = Parameters.get_AGB_annual_increment_ranges_dictionary()

        # Update the self.climate_period_inputs_dictionary for user-defined potential yields
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            self.climate_period_inputs_dictionary.update({
                # potential yield cropland-annual crops:
                'file_projection_potential_yield_cropland_annual_crops_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_yield_cropland_annual_crops_2018_2020_input),
                'file_projection_potential_yield_cropland_annual_crops_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_yield_cropland_annual_crops_2021_2040_input),
                'file_projection_potential_yield_cropland_annual_crops_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_yield_cropland_annual_crops_2041_2060_input),
                'file_projection_potential_yield_cropland_annual_crops_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_yield_cropland_annual_crops_2061_2080_input),
                'file_projection_potential_yield_cropland_annual_crops_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_yield_cropland_annual_crops_2081_2100_input)
            })
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            self.climate_period_inputs_dictionary.update({
                # potential yield pasture livestock density:
                'file_projection_potential_yield_livestock_density_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_yield_livestock_density_2018_2020_input),
                'file_projection_potential_yield_livestock_density_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_yield_livestock_density_2021_2040_input),
                'file_projection_potential_yield_livestock_density_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_yield_livestock_density_2041_2060_input),
                'file_projection_potential_yield_livestock_density_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_yield_livestock_density_2061_2080_input),
                'file_projection_potential_yield_livestock_density_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_yield_livestock_density_2081_2100_input)
            })
        if Parameters.demand_configuration['overall_method'] == 'yield_units' and 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
            self.climate_period_inputs_dictionary.update({
                # potential yield agroforestry crops:
                'file_projection_potential_yield_agroforestry_crops_2018_2020_input': readmap(
                    Filepaths.file_projection_potential_yield_agroforestry_crops_2018_2020_input),
                'file_projection_potential_yield_agroforestry_crops_2021_2040_input': readmap(
                    Filepaths.file_projection_potential_yield_agroforestry_crops_2021_2040_input),
                'file_projection_potential_yield_agroforestry_crops_2041_2060_input': readmap(
                    Filepaths.file_projection_potential_yield_agroforestry_crops_2041_2060_input),
                'file_projection_potential_yield_agroforestry_crops_2061_2080_input': readmap(
                    Filepaths.file_projection_potential_yield_agroforestry_crops_2061_2080_input),
                'file_projection_potential_yield_agroforestry_crops_2081_2100_input': readmap(
                    Filepaths.file_projection_potential_yield_agroforestry_crops_2081_2100_input)
            })


        # IMPORT EXTERNAL TIME SERIES DEMANDS IF USER-DEFINED TO GENERATE THE TSS FOR THE RUN:
        if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal':
            self.external_demands_generated_tss_dictionary = None
        if Parameters.demand_configuration['overall_method'] == 'yield_units' or (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'external'):
            self.external_demands_generated_tss_dictionary = {}

            # 1) DETERMINISTIC
            # 1a) deterministic footprint
            if Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration[
                'internal_or_external'] == 'external':
                columns_to_be_read = Parameters.demand_configuration['list_columns_for_tss']
                generated_tss_deterministic_demand_footprint = TssGenerator(columns_to_be_read,
                                                                       Filepaths.file_deterministic_demand_footprint_input)
                self.external_demands_generated_tss_dictionary.update({
                    'generated_tss_deterministic_demand_footprint': generated_tss_deterministic_demand_footprint
                })
            # 1b) deterministic demand yield units
            if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration[
                'deterministic_or_stochastic'] == 'deterministic':
                columns_to_be_read = Parameters.demand_configuration['list_columns_for_tss']
                generated_tss_deterministic_demand_yield_units = TssGenerator(columns_to_be_read,
                                                                         Filepaths.file_deterministic_demand_yield_units_input)
                columns_to_be_read = Parameters.demand_configuration['LUTs_with_demand_and_yield']
                generated_tss_deterministic_maximum_yield = TssGenerator(columns_to_be_read,
                                                                    Filepaths.file_deterministic_maximum_yield_input)
                self.external_demands_generated_tss_dictionary.update({
                    'generated_tss_deterministic_demand_yield_units': generated_tss_deterministic_demand_yield_units,
                    'generated_tss_deterministic_maximum_yield': generated_tss_deterministic_maximum_yield
                })

            # 2) or STOCHASTIC - only for demand yield approach
            if Parameters.demand_configuration['overall_method'] == 'yield_units' and Parameters.demand_configuration[
                'deterministic_or_stochastic'] == 'stochastic':
                columns_to_be_read = Parameters.demand_configuration['list_columns_for_tss']
                generated_tss_stochastic_demand_yield_units_HIGH = TssGenerator(columns_to_be_read,
                                                                           Filepaths.file_stochastic_demand_yield_units_HIGH_input)
                columns_to_be_read = Parameters.demand_configuration['list_columns_for_tss']
                generated_tss_stochastic_demand_yield_units_LOW = TssGenerator(columns_to_be_read,
                                                                          Filepaths.file_stochastic_demand_yield_units_LOW_input)
                columns_to_be_read = Parameters.demand_configuration['LUTs_with_demand_and_yield']
                generated_tss_stochastic_maximum_yield = TssGenerator(columns_to_be_read,
                                                                 Filepaths.file_stochastic_maximum_yield_input)
                self.external_demands_generated_tss_dictionary.update({
                    'generated_tss_stochastic_demand_yield_units_HIGH': generated_tss_stochastic_demand_yield_units_HIGH,
                    'generated_tss_stochastic_demand_yield_units_LOW': generated_tss_stochastic_demand_yield_units_LOW,
                    'generated_tss_stochastic_maximum_yield': generated_tss_stochastic_maximum_yield
                })

        #### prepare tidy data ######
        self.tidy_output_folder, self.tidy_output_files_definitions = self._prepare_tidy_output()
        self.tidy_probabilistic_output_folder, self.tidy_probabilistic_output_files_definitions = self._prepare_tidy_output_probabilistic()
        print('\nprepared tidy data output')

        print('\nrunning premcloop done')

    def _prepare_tidy_output(self):
        output_folder = Filepaths.folder_LPB_tidy_data

        # define output files and column headers
        output_files_definitions = {
            'LPB_scenario_years_' + str(Parameters.get_model_scenario()): ['year'],
            'LPB_deterministic_population_' + str(Parameters.get_model_scenario()): ['population'],
            'LPB_deterministic_smallholder_share_' + str(Parameters.get_model_scenario()): ['smallholder_share']
        }

        for file_name, header_columns in output_files_definitions.items():
            header_columns.insert(0, 'time_step')

            with open((os.path.join(output_folder, file_name + '.csv')), 'w', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_file_writer.writerow(header_columns)

        return output_folder, output_files_definitions

    def _prepare_tidy_output_probabilistic(self):
        probabilistic_output_folder = Filepaths.folder_LPB_tidy_data

        # define output files and column headers
        probabilistic_output_files_definitions = {
            'LPB_probabilistic_max_forest_conversion_' + str(Parameters.get_model_scenario()): ['LUT_code', 'pixels'],
            'LPB_probabilistic_mean_forest_' + str(Parameters.get_model_scenario()): ['Aspect', 'pixels'],
            'LPB_basic_mean_demand_and_mean_unallocated_demand_' + str(Parameters.get_model_scenario()): ['demand_type', 'mean_demand', 'mean_unallocated_demand']
        }

        for file_name, header_columns in probabilistic_output_files_definitions.items():
            header_columns.insert(0, 'time_step')

            with open((os.path.join(probabilistic_output_folder, file_name + '.csv')), 'w', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_file_writer.writerow(header_columns)

        return probabilistic_output_folder, probabilistic_output_files_definitions


    def initial(self):
        print('\n>>> running initial for sample number:', self.currentSampleNumber(), '...')

        self.year = Parameters.get_initial_simulation_year()

        # SAMPLING DISTANCE FOR THE SAMPLE IF SAMPLES > 1 IF THIS APPROACH IS TO BE USED
        if number_of_samples_set == 1:
            self.LUT02_sampled_distance_for_this_sample = self.LUT02_mean_distance_to_settlements
            self.LUT03_sampled_distance_for_this_sample = self.LUT03_mean_distance_to_settlements
            self.LUT04_sampled_distance_for_this_sample = self.LUT04_mean_distance_to_settlements
        else:
            # calculate the distance for this sample (full range to be covered by the simulation)
            if self.currentSampleNumber() == 1:
                self.LUT02_sampled_distance_for_this_sample = self.LUT02_minimum_distance_to_settlements
                self.LUT03_sampled_distance_for_this_sample = self.LUT03_minimum_distance_to_settlements
                self.LUT04_sampled_distance_for_this_sample = self.LUT04_minimum_distance_to_settlements
            elif self.currentSampleNumber() > 1 and self.currentSampleNumber() < number_of_samples_set:
                self.LUT02_sampled_distance_for_this_sample = self.LUT02_minimum_distance_to_settlements + (((self.LUT02_maximum_distance_to_settlements - self.LUT02_minimum_distance_to_settlements) / number_of_samples_set) * self.currentSampleNumber())
                self.LUT03_sampled_distance_for_this_sample = self.LUT03_minimum_distance_to_settlements + (((self.LUT03_maximum_distance_to_settlements - self.LUT03_minimum_distance_to_settlements) / number_of_samples_set) * self.currentSampleNumber())
                self.LUT04_sampled_distance_for_this_sample = self.LUT04_minimum_distance_to_settlements + (((self.LUT04_maximum_distance_to_settlements - self.LUT04_minimum_distance_to_settlements) / number_of_samples_set) * self.currentSampleNumber())
            elif self.currentSampleNumber() == number_of_samples_set:
                self.LUT02_sampled_distance_for_this_sample = self.LUT02_maximum_distance_to_settlements
                self.LUT03_sampled_distance_for_this_sample = self.LUT03_maximum_distance_to_settlements
                self.LUT04_sampled_distance_for_this_sample = self.LUT04_maximum_distance_to_settlements

        print('\nself.LUT02_sampled_distance_for_this_sample', self.LUT02_sampled_distance_for_this_sample)
        print('self.LUT03_sampled_distance_for_this_sample', self.LUT03_sampled_distance_for_this_sample)
        print('self.LUT04_sampled_distance_for_this_sample', self.LUT04_sampled_distance_for_this_sample)


        # JV: Create the 'overall' land use class
        self.environment_map = self.initial_environment_map
        self.land_use = LandUse(types=self.active_land_use_types_list,
                                initial_environment_map=self.initial_environment_map,
                                environment_map=self.environment_map,
                                null_mask_map=self.null_mask_map,
                                plantation_age_map=self.plantation_age_map,
                                year=self.year,
                                spatially_explicit_population_maps_dictionary=self.spatially_explicit_population_maps_dictionary,
                                climate_period_inputs_dictionary=self.climate_period_inputs_dictionary,
                                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary=self.AGB_annual_increment_ranges_in_Mg_per_ha_dictionary,
                                settlements_map=self.settlements_map,
                                net_forest_map=self.net_forest_map,
                                dem_map=self.dem_map,
                                static_restricted_areas_map=self.static_restricted_areas_map,
                                AGB_map=self.AGB_map,
                                streets_map=self.streets_map,
                                cities_map=self.cities_map,
                                static_areas_on_which_no_allocation_occurs_map=self.static_areas_on_which_no_allocation_occurs_map,
                                static_LUTs_on_which_no_allocation_occurs_list=self.static_LUTs_on_which_no_allocation_occurs_list,
                                difficult_terrain_slope_restriction_dictionary=self.difficult_terrain_slope_restriction_dictionary,
                                LUT02_sampled_distance_for_this_sample=self.LUT02_sampled_distance_for_this_sample,
                                LUT03_sampled_distance_for_this_sample=self.LUT03_sampled_distance_for_this_sample,
                                LUT04_sampled_distance_for_this_sample=self.LUT04_sampled_distance_for_this_sample,
                                external_demands_generated_tss_dictionary=self.external_demands_generated_tss_dictionary
                                )

        self.land_use.update_time_step_and_sample_number_and_year(time_step=self.currentTimeStep(), current_sample_number=int(self.currentSampleNumber()), year=self.year)

        # JV: Create an object for every land use type in the list
        self.land_use.create_land_use_types_objects(self.related_land_use_types_dictionary,
                                                    self.suitability_factors_dictionary,
                                                    self.weights_dictionary,
                                                    self.variables_super_dictionary,
                                                    self.noise_map)

        self.land_use.determine_immutable_excluded_areas_from_allocation_map()

        self.land_use.determine_distance_to_streets(self.streets_map)
        self.land_use.determine_distance_to_freshwater(self.freshwater_map)
        self.land_use.determine_distance_to_cities(self.cities_map)
        self.land_use.calculate_static_suitability_maps()



        print('running initial done')

    def dynamic(self):
        # SH: LPB alternation - global available data from LandUseChangeModel
        self.time_step = self.currentTimeStep()
        self.current_sample_number = int(self.currentSampleNumber())
        if self.time_step == 1:
            self.year = Parameters.get_initial_simulation_year()
        else:
            self.year += 1

        logger.info(f'\n>>> running dynamic for sample number {self.current_sample_number}, time step {self.time_step} ...')

        logger.debug('\nCPU and RAM usage:')
        # CPU
        # CPU_to_be_used = Parameters.get_number_of_cores_to_be_used()
        # print('CPU to be used according to Parameters.py:', CPU_to_be_used)
        # Return the number of logical CPUs in the system (same as os.cpu_count in Python 3.4) or None if undetermined.
        # “logical CPUs” means the number of physical cores multiplied by the number of threads that can run on each core (this is known as Hyper Threading).
        logical_cores_in_use = psutil.cpu_count(logical=True)
        logger.debug(f'CPU logical: {logical_cores_in_use}')
        # If logical is False return the number of physical cores only, or None if undetermined
        physical_cores_in_use = psutil.cpu_count(logical=False)
        logger.debug(f'CPU physical: {physical_cores_in_use}')
        # The number of usable CPUs can be obtained with:
        if platform.system() != 'Darwin': # Darwin is macOS
            useable_CPUs = len(psutil.Process().cpu_affinity())
            logger.debug(f'CPU useable: {useable_CPUs}')
            CPU_percent = psutil.cpu_percent()
            logger.debug(f'CPU % used: {CPU_percent}')
            logger.debug("CPU Usage Per Core:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
                logger.debug(f"Core {i}: {percentage}%")
            logger.debug(f"Total CPU Usage: {psutil.cpu_percent()}%")
        else:
            useable_CPUs = multiprocessing.cpu_count()
            logger.debug(f'CPU useable: {useable_CPUs}')
            # CPU_in_use = len(os.sched_getaffinity(0))
            # CPU_in_use = len(os.sched_affinity(0))
            # print('CPU in use:', CPU_in_use)
            CPU_percent = psutil.cpu_percent()
            logger.debug(f'CPU % used: {CPU_percent}')
            logger.debug("CPU Usage Per Core:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
                logger.debug(f"Core {i}: {percentage}%")
            logger.debug(f"Total CPU Usage: {psutil.cpu_percent()}%")
        # RAM
        RAM_total = int(psutil.virtual_memory().total / 1073741274) # Bytes in a GB
        logger.debug(f'RAM total ca. GB: {RAM_total}')
        RAM_available = int(psutil.virtual_memory().available / 1073741274)
        logger.debug(f'RAM available ca. GB: {RAM_available}')
        RAM_used_percent = psutil.virtual_memory().percent
        logger.debug(f'% of RAM used: {RAM_used_percent}')
        # you can calculate percentage of available memory
        RAM_available_percent = round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 2)
        logger.debug(f'% of RAM available: {RAM_available_percent}')

        # search for memory leak
        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot)

        # Python garbage collector display list
        # A list of objects which the collector found to be unreachable but could not be freed (uncollectable objects).
        # Starting with Python 3.4, this list should be empty most of the time, except when using instances of C extension types with a non-NULL tp_del slot.
        logger.debug(f'\n Python garbage that is not collectable: {gc.garbage}')


        # DK: update LandUse and LandUseType needed variables
        self.land_use.update_time_step_and_sample_number_and_year(time_step=self.time_step,
                                                                      current_sample_number=self.current_sample_number,
                                                                      year=self.year)
        # user information
        print('\nNEW TIME STEP IS:', self.time_step, 'OF', Parameters.get_number_of_time_steps(),
              'IN SAMPLE NUMBER:', int(self.currentSampleNumber()), 'OF',
              number_of_samples_set)
        print('current simulation year is:', self.year)

        # SH: LPB alternation - EXTENDED PLUC
        # calculate the simulation year, its according spatially explicit population and derived demand,
        # the accompanying maps prior and posterior the central time step calculations, get the CSV input variables

        # SH: LPB alternation - update_accompanying_maps_and_values_prior_time_step
        print('\nupdating accompanying maps prior time step initialized ...')
        self.land_use.update_environment_map_last_time_step()
        self.land_use.update_succession_age_map()
        self.population, self.population_map, self.population_per_year_list = self.land_use.update_population()
        self.settlements = self.land_use.update_settlements()
        self.land_use.update_anthropogenic_impact_buffer()
        self.land_use.update_climate_period_input_maps()
        self.land_use.update_AGB_map_last_time_step()
        self.land_use.update_AGB()
        self.land_use.update_plantation_age_map()
        print('\nupdating accompanying maps prior time step done')

        print('\nupdating demand and according land use change by active land use types initiated ...')
        demand, self.population_number_of_smallholders, demand_AGB = self.land_use.update_demand()
        if Parameters.get_order_of_forest_deforestation_and_conversion() is True: # == deforestation_before_conversion
            self.land_use.allocate_AGB_demand(demand_AGB) # calculates suitability for forest fringe harvesting as often as required to satisfy demand
            self.land_use.calculate_suitability_maps() # suitability maps need to get calculated after allocation of demand in AGB to determine forest fringe and deforested cells
            self.land_use.allocate(demand)
        else:
            self.land_use.calculate_suitability_maps()
            self.land_use.allocate(demand)
            self.land_use.allocate_AGB_demand(demand_AGB) # LUT17 is definitely in the map, since not overwritten
        print('\nupdating demand and according land use change by active land use types done')

        # SH: LPB alternation - update_accompanying_maps_and_values_posterior_time_step
        print('\nupdating self.environment and accompanying maps posterior allocation initialized ...')
        self.land_use.correct_AGB_map_after_allocation()
        if probabilistic_output_options_dictionary['conflict_maps'] == True:
            self.land_use.determine_areas_of_forest_land_use_conflict_in_restricted_areas()
        self.land_use.update_built_up_area_last_time_step()
        self.land_use.update_plantation_information()
        self.land_use.update_succession()
        self.land_use.update_AGB_map_new_agroforestry_and_disturbed_pixels()
        self.land_use.update_forest_fringe_disturbed()
        self.land_use.update_net_forest_map()
        if probabilistic_output_options_dictionary['degradation_regeneration_maps'] == True:
            self.land_use.update_forest_degradation_and_regeneration()
        print('\nupdating self.environment and accompanying maps posterior allocation done')

        print('\ndraw the complete new self.environment_map ...')
        self.environment_map = self.land_use.get_environment()
        print('\ndraw the complete new self.environment_map done')

        print('\nstoring maps initialized ...')

        # define once time_step variable for all output files generated by generate_PCRaster_conform_output_name.py
        time_step = self.time_step

        # now store the data needed
        print('storing self.environment map as LPBLULCC in folder outputs/LPB/LULCC_simulation/dynamic_environment_map_probabilistic ...')
        pcraster_conform_map_name = 'LPBLULCC'
        output_map_name = generate_PCRaster_conform_output_name.generate_PCRaster_conform_output_for_subfolder(
            pcraster_conform_map_name, time_step)
        report(self.environment_map, os.path.join(Filepaths.folder_dynamic_environment_map_probabilistic,
                                                       str(self.current_sample_number), output_map_name))
        print('storing self.environment map as LPBLULCC in folder outputs/LPB/LULCC_simulation/dynamic_environment_map_probabilistic done')

        # In model stage 1 not needed, leave for model stage 2+:

        # os.system('legend --clone LPBLULCC.map -f \"Legend_LULC.txt\" %s '
        #               % generateNameST('LPBLULCC',
        #                                # Filepaths.folder_dynamic_environment_map_probabilistic, # TEST TypeError: generateNameST() takes 3 positional arguments but 4 were given
        #                                self.currentSampleNumber(),
        #                                self.time_step))
        #     # legend version: 4.3.1 (darwin/x86_64)

        print('storing maps done')

        ##################################################
        # ANALYSIS

        # forest current time step (to derive mean of all samples)
        # built the forest map of the time step
        forest_timestep_map = ifthenelse(self.environment_map == 8,
                                              scalar(1),
                                              scalar(self.null_mask_map))

        forest_timestep_map = ifthenelse(self.environment_map == 9,
                                              scalar(1),
                                              scalar(forest_timestep_map))

        forest_timestep_map = ifthen(scalar(forest_timestep_map) == scalar(1),  # eliminate the zeros
                                          scalar(1))

        forest_maptotal = int(maptotal(scalar(forest_timestep_map)))

        dictionary_of_samples_dictionaries_values_forest[self.current_sample_number][self.time_step] = forest_maptotal

        # forest conversion to other land use basic - USE THE MAXIMUM OVER ALL SAMPLES
        if self.time_step == 1:
            if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
                if Parameters.get_presimulation_correction_step_needed() is True:
                    environment_last_time_step_map = readmap(Filepaths.file_initial_LULC_simulated_input)
                else:
                    environment_last_time_step_map = readmap(Filepaths.file_initial_LULC_input)
            elif Parameters.get_model_scenario() == 'no_conservation':
                environment_last_time_step_map = readmap(
                    Filepaths.file_initial_LULC_simulated_for_worst_case_scenario_input)
        else:
            environment_last_time_step_map = self.environment_last_time_step_map

        # built the forest map of last time step
        forest_last_timestep_map = ifthenelse(environment_last_time_step_map == 8,
                                              scalar(1),
                                              scalar(self.null_mask_map))

        forest_last_timestep_map = ifthenelse(environment_last_time_step_map == 9,
                                              scalar(1),
                                              scalar(forest_last_timestep_map))

        forest_last_timestep_map = ifthen(scalar(forest_last_timestep_map) == scalar(1),  # eliminate the zeros
                                          scalar(1))

        # built the current active land use types map
        active_land_use_now_map = scalar(self.null_mask_map)
        for a_LUT in Parameters.get_active_land_use_types_list():  # Parameters.get_active_land_use_types_list()
            active_land_use_now_map = ifthenelse(
                scalar(self.environment_map) == scalar(a_LUT),
                scalar(1),
                scalar(active_land_use_now_map))

        active_land_use_now_map = ifthen(scalar(active_land_use_now_map) != scalar(0),  # eliminate the zeros
                                         scalar(1))

        # only where both maps match is forest converted from the last time step
        converted_forest_map = ifthen(active_land_use_now_map == forest_last_timestep_map,
                                      scalar(1))  # show the forest that is converted

        converted_forest_area = int(maptotal(converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'total'] = converted_forest_area

        # show the singular LUTs
        LUT01_converted_forest_map = ifthen(
            boolean(self.environment_map == 1) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        LUT01_converted_forest_area = int(maptotal(LUT01_converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'LUT01'] = LUT01_converted_forest_area

        LUT02_converted_forest_map = ifthen(
            boolean(self.environment_map == 2) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        LUT02_converted_forest_area = int(maptotal(LUT02_converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'LUT02'] = LUT02_converted_forest_area

        LUT03_converted_forest_map = ifthen(
            boolean(self.environment_map == 3) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        LUT03_converted_forest_area = int(maptotal(LUT03_converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'LUT03'] = LUT03_converted_forest_area

        LUT04_converted_forest_map = ifthen(
            boolean(self.environment_map == 4) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        LUT04_converted_forest_area = int(maptotal(LUT04_converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'LUT04'] = LUT04_converted_forest_area

        LUT05_converted_forest_map = ifthen(
            boolean(self.environment_map == 5) == boolean(forest_last_timestep_map == 1),
            scalar(1))
        LUT05_converted_forest_area = int(maptotal(LUT05_converted_forest_map))
        dictionary_of_samples_dictionaries_values_forest_conversion[self.current_sample_number][self.time_step][
            'LUT05'] = LUT05_converted_forest_area

        self.environment_last_time_step_map = self.environment_map

        ##################################################

        # SH: LPB alternation
        # IF THE MODELLING APPROACH IS OTHER THAN FOOTPRINT INTERNAL,
        # COLLECT VALUES OF ACTUAL ALLOCATED DEMANDS OVER ALL SAMPLES TO DERIVE MAX AND MEAN FOR MPLC

        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):

            # SH: LUT05
            print('\nadding for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_LUT05')
            # collect number of cells allocated for LUT05
            LUT05_maptotal = int(maptotal(scalar(boolean(self.environment_map == 5))))
            # append it to the nested dictionary (sample number is key, time step is key, value is maptotal)
            dictionary_of_samples_dictionaries_values_LUT05[self.current_sample_number][self.time_step] = LUT05_maptotal
            print('added for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_LUT05')

            # SH: LPB agricultural types
            print('\nadding for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_agricultural_types')
            # collect number of cells allocated for LUTs
            LUT02_maptotal = int(maptotal(scalar(boolean(self.environment_map == 2))))
            dictionary_of_samples_dictionaries_values_agricultural_types[self.current_sample_number][self.time_step]['LUT02'] = LUT02_maptotal
            LUT03_maptotal = int(maptotal(scalar(boolean(self.environment_map == 3))))
            dictionary_of_samples_dictionaries_values_agricultural_types[self.current_sample_number][self.time_step]['LUT03'] = LUT03_maptotal
            LUT04_maptotal = int(maptotal(scalar(boolean(self.environment_map == 4))))
            dictionary_of_samples_dictionaries_values_agricultural_types[self.current_sample_number][self.time_step]['LUT04'] = LUT04_maptotal
            print('added for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_agricultural_types')

            # SH: abandoned types
            print('\nadding for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_abandoned_types')
            # collect number of cells allocated for LUTs
            LUT14_maptotal = int(maptotal(scalar(boolean(self.environment_map == 14))))
            dictionary_of_samples_dictionaries_values_abandoned_types[self.current_sample_number][self.time_step][
                'LUT14'] = LUT14_maptotal
            LUT15_maptotal = int(maptotal(scalar(boolean(self.environment_map == 15))))
            dictionary_of_samples_dictionaries_values_abandoned_types[self.current_sample_number][self.time_step][
                'LUT15'] = LUT15_maptotal
            LUT16_maptotal = int(maptotal(scalar(boolean(self.environment_map == 16))))
            dictionary_of_samples_dictionaries_values_abandoned_types[self.current_sample_number][self.time_step][
                'LUT16'] = LUT16_maptotal
            LUT18_maptotal = int(maptotal(scalar(boolean(self.environment_map == 18))))
            dictionary_of_samples_dictionaries_values_abandoned_types[self.current_sample_number][self.time_step][
                'LUT18'] = LUT18_maptotal
            print('added for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_abandoned_types')

        # IN ANY MODELLING APPROACH NOTE LUT17 AND LUT01

        # SH: LUT17
        print('\nadding for sample number', self.current_sample_number, 'time step', self.year,
                  'data to dictionary_of_samples_dictionaries_values_LUT17')
        # collect number of cells allocated for LUT17
        LUT17_maptotal = int(maptotal(scalar(boolean(self.environment_map == 17))))
        # append it to the nested dictionary (sample number is key, time step is key, value is maptotal)
        dictionary_of_samples_dictionaries_values_LUT17[self.current_sample_number][self.time_step] = LUT17_maptotal
        print('added for sample number', self.current_sample_number, 'time step', self.year,
              'data to dictionary_of_samples_dictionaries_values_LUT17')

        # SH: LPB alternation - CSV OUTPUT (note the deterministic output of the LPB basic run - this will be needed in subsequent modules)
        # point out maximum demand LUT01:
        maximum_demand_LUT01 = str('maximum demand noted in LUT01 log-file')
        if self.currentSampleNumber() == 1:
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic_log-file.csv'),'a', newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                LPB_log_file_data = [self.year, self.population, self.settlements, self.population_number_of_smallholders,
                                     maximum_demand_LUT01, demand[2], demand[3], demand[4], demand[5], demand_AGB]
                writer.writerow(LPB_log_file_data)
        print('\nadded time step', self.year, 'data to LPB-basic_log-file')

        if (self.currentSampleNumber() == number_of_samples_set and self.time_step == Parameters.get_number_of_time_steps()):
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic_log-file.csv'), 'a', newline='') as LPB_log_file:
                writer = csv.writer(LPB_log_file)
                population_peak_year_and_number = builtins.max(self.population_per_year_list, key=itemgetter(1))
                writer.writerow([])
                writer.writerow(['Population peak:', population_peak_year_and_number])
                print('\nPopulation peak was:', population_peak_year_and_number)
                print('added population peak data to LPB-basic_log-file')
                writer.writerow([])
                if Parameters.get_number_of_samples() == 1:
                    writer.writerow(['LPB-basic deterministic modelling with # of samples:', number_of_samples_set])
                elif Parameters.get_number_of_samples() is not None and Parameters.get_number_of_samples() > 1:
                    writer.writerow(['LPB-basic Monte Carlo modelling with # of samples:', number_of_samples_set])
                elif Parameters.get_number_of_samples() == None:
                    writer.writerow(['LPB-basic modelling based on pseudo random sampling with # of samples:', number_of_samples_set])
                print('\nadded simulation type and number of samples to LPB-basic_log-file')

        if self.currentSampleNumber() == 1:
            self.export_data_to_tidy_data_folder()

        print('\nrunning dynamic done')

    def export_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        output_files_data = {
            'LPB_scenario_years_' + str(Parameters.get_model_scenario()): [
                [self.year]
            ],
            'LPB_deterministic_population_' + str(Parameters.get_model_scenario()): [
                [self.population]
            ],
            'LPB_deterministic_smallholder_share_' + str(Parameters.get_model_scenario()): [
                [self.population_number_of_smallholders]
            ]
        }

        for output_file, column_headers in self.tidy_output_files_definitions.items():

            with open(os.path.join(Filepaths.folder_LPB_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file)

                for data_of_row in output_files_data[output_file]:
                    # add time step
                    data_of_row.insert(0, self.time_step)

                    assert len(column_headers) == len(
                        data_of_row), f'headers: {column_headers}, row data: {data_of_row}'

                    csv_file_writer.writerow(data_of_row)

    def postmcloop(self):
        print('\n>>> running postmcloop ...')

        # SH: LPB alternation
        print('\ncalculating max forest conversion from samples for time steps initialized ...')

        # create the CSV for the data to be transported into LPB-mplc
        with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-forest-conversion_log-file.csv')),
                  'w',
                  newline='') as LPB_log_file:
            LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-basic-forest-conversion log file', Parameters.get_country(), Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                  'year',
                                                                  'total',
                                                                  'LUT01', 'LUT02', 'LUT03', 'LUT04', 'LUT05'])
            LPB_writer.writeheader()

        # get the data out of the nested dictionary for LUT01 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        year = int(Parameters.get_initial_simulation_year()) - 1
        for a_time_step in range_of_time_steps:
            LUTs_total_values_time_step_list = []
            LUT01_values_time_step_list = []
            LUT02_values_time_step_list = []
            LUT03_values_time_step_list = []
            LUT04_values_time_step_list = []
            LUT05_values_time_step_list = []
            for a_sample in range_of_samples:
                LUTs_total_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step]['total']
                LUTs_total_values_time_step_list.append(LUTs_total_values)
                LUT01_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][
                    'LUT01']
                LUT01_values_time_step_list.append(LUT01_values)
                LUT02_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][
                    'LUT02']
                LUT02_values_time_step_list.append(LUT02_values)
                LUT03_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][
                    'LUT03']
                LUT03_values_time_step_list.append(LUT03_values)
                LUT04_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][
                    'LUT04']
                LUT04_values_time_step_list.append(LUT04_values)
                LUT05_values = dictionary_of_samples_dictionaries_values_forest_conversion[a_sample][a_time_step][
                    'LUT05']
                LUT05_values_time_step_list.append(LUT05_values)

            year += 1
            self.LUTs_total_maximum_value = builtins.max(LUTs_total_values_time_step_list)
            self.LUT01_maximum_value = builtins.max(LUT01_values_time_step_list)
            self.LUT02_maximum_value = builtins.max(LUT02_values_time_step_list)
            self.LUT03_maximum_value = builtins.max(LUT03_values_time_step_list)
            self.LUT04_maximum_value = builtins.max(LUT04_values_time_step_list)
            self.LUT05_maximum_value = builtins.max(LUT05_values_time_step_list)
            self.a_time_step = a_time_step
            self.export_probabilistic_forest_conversion_data_to_tidy_data_folder()
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-forest-conversion_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [a_time_step, year, self.LUTs_total_maximum_value,
                                     self.LUT01_maximum_value, self.LUT02_maximum_value, self.LUT03_maximum_value, self.LUT04_maximum_value, self.LUT05_maximum_value]
                writer.writerow(LPB_log_file_data)
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-forest-conversion_log-file.csv'), 'a', newline='') as LPB_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_log_file)
            writer.writerow([])
            writer.writerow(['PLEASE NOTE:'])
            writer.writerow(['LPB-basic maximum forest conversion over number of samples.'])
            writer.writerow(
                ['Only for comparison to mplc module extracted.'])

        print('calculating max forest conversion from samples for time steps done')


        # SH: LPB alternation
        print('\ncalculating mean value of abandoned types from samples for time steps initialized ...')

        # create the CSV for the data to be transported into LPB-mplc
        with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs',
                                'LPB-basic-abandoned-types_log-file.csv')),
                  'w',
                  newline='') as LPB_log_file:
            LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-basic-abandoned-types log file', Parameters.get_country(),
                                  Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                  'year',
                                                                  'mean LUT14', 'mean LUT15', 'mean LUT16', 'mean LUT18'])
            LPB_writer.writeheader()

        # get the data out of the nested dictionary for LUT01 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        year = int(Parameters.get_initial_simulation_year()) - 1
        for a_time_step in range_of_time_steps:
            LUT14_values_time_step_list = []
            LUT15_values_time_step_list = []
            LUT16_values_time_step_list = []
            LUT18_values_time_step_list = []
            for a_sample in range_of_samples:
                LUT14_values = dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step][
                    'LUT14']
                LUT14_values_time_step_list.append(LUT14_values)
                LUT15_values = dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step][
                    'LUT15']
                LUT15_values_time_step_list.append(LUT15_values)
                LUT16_values = dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step][
                    'LUT16']
                LUT16_values_time_step_list.append(LUT16_values)
                LUT18_values = dictionary_of_samples_dictionaries_values_abandoned_types[a_sample][a_time_step][
                    'LUT18']
                LUT18_values_time_step_list.append(LUT18_values)
            year += 1
            LUT14_mean_value = math.ceil(sum(LUT14_values_time_step_list) / len(LUT14_values_time_step_list))
            LUT15_mean_value = math.ceil(sum(LUT15_values_time_step_list) / len(LUT15_values_time_step_list))
            LUT16_mean_value = math.ceil(sum(LUT16_values_time_step_list) / len(LUT16_values_time_step_list))
            LUT18_mean_value = math.ceil(sum(LUT18_values_time_step_list) / len(LUT18_values_time_step_list))
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-abandoned-types_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [a_time_step, year, LUT14_mean_value, LUT15_mean_value, LUT16_mean_value, LUT18_mean_value]
                writer.writerow(LPB_log_file_data)
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-abandoned-types_log-file.csv'), 'a',
                  newline='') as LPB_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_log_file)
            writer.writerow([])
            writer.writerow(['PLEASE NOTE:'])
            writer.writerow(['LPB-basic mean abandoned types value over number of samples.'])
            writer.writerow(
                ['Used in mplc module for simulation of abandoned types in corrective allocation.'])

        print('calculating mean value of abandoned types from samples for time steps done')

        ##########

        # SH: LPB alternation
        print('\ncalculating min, max, mean LUT01 from samples for time steps initialized ...')

        # create the CSV for the data to be transported into LPB-mplc
        with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-LUT01_log-file.csv')), 'w',
                  newline='') as LPB_log_file:
            LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-basic-LUT01 log file', Parameters.get_country(), Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                  'year',
                                                                  'minimum area built-up demand',
                                                                  'mean area built-up demand',
                                                                  'maximum area built-up demand'])
            LPB_writer.writeheader()

        # get the data out of the nested dictionary for LUT01 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        year = int(Parameters.get_initial_simulation_year()) -1
        for a_time_step in range_of_time_steps:
            LUT01_values_time_step_list = []
            for a_sample in range_of_samples:
                LUT01_value = dictionary_of_samples_dictionaries_values_LUT01[a_sample][a_time_step]
                LUT01_values_time_step_list.append(LUT01_value)
            year += 1
            LUT01_minimum_value = builtins.min(LUT01_values_time_step_list)
            LUT01_mean_value = math.ceil(sum(LUT01_values_time_step_list) / len(LUT01_values_time_step_list))
            LUT01_maximum_value = builtins.max(LUT01_values_time_step_list)
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT01_log-file.csv'),'a', newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [a_time_step, year, LUT01_minimum_value, LUT01_mean_value, LUT01_maximum_value]
                writer.writerow(LPB_log_file_data)
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT01_log-file.csv'), 'a', newline='') as LPB_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_log_file)
            writer.writerow([])
            writer.writerow(['PLEASE NOTE:'])
            writer.writerow(['LPB-basic demand built-up pixels range over number of samples.' ])
            writer.writerow(['Only the maximum value will be applied in mplc to depict potential maximum anthropogenic impact.'])

        print('calculating min, max, mean LUT01 from samples for time steps done')

        # SH: LPB alternation
        print('\ncalculating min, max, mean LUT05 from samples for time steps initialized ...')

        # create the CSV for the data to be transported into LPB-mplc
        with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-LUT05_log-file.csv')),
                  'w',
                  newline='') as LPB_log_file:
            LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-basic-LUT05 log file', Parameters.get_country(), Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                  'year',
                                                                  'minimum area plantation',
                                                                  'mean area plantation',
                                                                  'maximum area plantation'])
            LPB_writer.writeheader()

        # get the data out of the nested dictionary for LUT05 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        year = int(Parameters.get_initial_simulation_year()) - 1
        for a_time_step in range_of_time_steps:
            LUT05_values_time_step_list = []
            for a_sample in range_of_samples:
                LUT05_value = dictionary_of_samples_dictionaries_values_LUT05[a_sample][a_time_step]
                LUT05_values_time_step_list.append(LUT05_value)
            year += 1
            LUT05_minimum_value = builtins.min(LUT05_values_time_step_list)
            LUT05_mean_value = math.ceil(sum(LUT05_values_time_step_list) / len(LUT05_values_time_step_list))
            LUT05_maximum_value = builtins.max(LUT05_values_time_step_list)
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT05_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [a_time_step, year, LUT05_minimum_value, LUT05_mean_value, LUT05_maximum_value]
                writer.writerow(LPB_log_file_data)
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT05_log-file.csv'), 'a', newline='') as LPB_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_log_file)
            writer.writerow([])
            writer.writerow(['PLEASE NOTE:'])
            writer.writerow(['LPB-basic plantation pixels range over number of samples.'])
            writer.writerow(
                ['Only the maximum value will be applied in mplc to depict potential maximum anthropogenic impact.'])

        print('calculating min, max, mean LUT05 from samples for time steps done')

        # SH: LPB alternation
        print('\ncalculating min, max, mean LUT17 from samples for time steps initialized ...')

        # create the CSV for the data to be transported into LPB-mplc
        with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB-basic-LUT17_log-file.csv')), 'w',
                  newline='') as LPB_log_file:
            LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Create a title for the CSV
            LPB_log_file_title = ['LPB-basic-LUT17 log file', Parameters.get_country(), Parameters.get_region(),
                                  Parameters.get_model_baseline_scenario(),
                                  Parameters.get_model_scenario() + ' scenario']
            LPB_writer.writerow(LPB_log_file_title)
            # Create the header
            LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                  'year',
                                                                  'minimum area deforested due to demand in input biomass',
                                                                  'mean area deforested due to demand in input biomass',
                                                                  'maximum area deforested due to demand in input biomass'])
            LPB_writer.writeheader()

        # get the data out of the nested dictionary for LUT17 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        year = int(Parameters.get_initial_simulation_year()) - 1
        for a_time_step in range_of_time_steps:
            LUT17_values_time_step_list = []
            for a_sample in range_of_samples:
                LUT17_value = dictionary_of_samples_dictionaries_values_LUT17[a_sample][a_time_step]
                LUT17_values_time_step_list.append(LUT17_value)
            year += 1
            LUT17_minimum_value = builtins.min(LUT17_values_time_step_list)
            LUT17_mean_value = math.ceil(sum(LUT17_values_time_step_list) / len(LUT17_values_time_step_list))
            LUT17_maximum_value = builtins.max(LUT17_values_time_step_list)
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT17_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                LPB_log_file_data = [a_time_step, year, LUT17_minimum_value, LUT17_mean_value, LUT17_maximum_value]
                writer.writerow(LPB_log_file_data)
        with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-LUT17_log-file.csv'), 'a', newline='') as LPB_log_file:
            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
            writer = csv.writer(LPB_log_file)
            writer.writerow([])
            writer.writerow(['PLEASE NOTE:'])
            if Parameters.get_order_of_forest_deforestation_and_conversion() == True:
                writer.writerow([
                                    'LPB-basic modelled deforestation BEFORE conversion, these are values for the REMAINING deforested plots in the environment'])
            elif Parameters.get_order_of_forest_deforestation_and_conversion() == False:
                writer.writerow([
                                    'LPB-basic modelled deforestation AFTER conversion, these are values for the ALL deforested plots in the environment'])

        print('calculating min, max, mean LUT17 from samples for time steps done')


        print('\ncalculating mean forest over all samples initialized ...')
        # get the data out of the nested dictionary for LUT01 and write it to the CSV
        range_of_samples = range(1, int(number_of_samples_set) + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        for a_time_step in range_of_time_steps:
            forest_values_time_step_list = []
            for a_sample in range_of_samples:
                forest_value = dictionary_of_samples_dictionaries_values_forest[a_sample][a_time_step]
                forest_values_time_step_list.append(forest_value)
            self.mean_forest_pixels = math.ceil(sum(forest_values_time_step_list) / len(forest_values_time_step_list))
            self.a_time_step = a_time_step
            self.export_probabilistic_mean_forest_data_to_tidy_data_folder()
        print('calculating mean forest over all samples done')

        # MPLC adapter in the external time series approach
        if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
            # SH: LPB alternation
            print('\ncalculating maximum value of agricultural types from samples for time steps initialized ...')

            # create the CSV for the data to be transported into LPB-mplc
            with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs',
                                    'LPB-basic-agricultural-types_log-file.csv')),
                      'w',
                      newline='') as LPB_log_file:
                LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # Create a title for the CSV
                LPB_log_file_title = ['LPB-basic-agricultural-types log file', Parameters.get_country(),
                                      Parameters.get_region(),
                                      Parameters.get_model_baseline_scenario(),
                                      Parameters.get_model_scenario() + ' scenario']
                LPB_writer.writerow(LPB_log_file_title)
                # Create the header
                LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['time step',
                                                                      'year',
                                                                      'maximum LUT02', 'maximum LUT03', 'maximum LUT04'])
                LPB_writer.writeheader()

            # get the data out of the nested dictionary for agricultural LUTs and write it to the LPB-basic-agricultural-types_log-file.csv to be used as an mplc adapter
            range_of_samples = range(1, int(number_of_samples_set) + 1)
            range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
            year = int(Parameters.get_initial_simulation_year()) - 1
            for a_time_step in range_of_time_steps:
                LUT02_values_time_step_list = []
                LUT03_values_time_step_list = []
                LUT04_values_time_step_list = []
                for a_sample in range_of_samples:
                    LUT02_values = dictionary_of_samples_dictionaries_values_agricultural_types[a_sample][a_time_step][
                        'LUT02']
                    LUT02_values_time_step_list.append(LUT02_values)
                    LUT03_values = dictionary_of_samples_dictionaries_values_agricultural_types[a_sample][a_time_step][
                        'LUT03']
                    LUT03_values_time_step_list.append(LUT03_values)
                    LUT04_values = dictionary_of_samples_dictionaries_values_agricultural_types[a_sample][a_time_step][
                        'LUT04']
                    LUT04_values_time_step_list.append(LUT04_values)
                year += 1
                LUT02_maximum_value = builtins.max(LUT02_values_time_step_list)
                LUT03_maximum_value = builtins.max(LUT03_values_time_step_list)
                LUT04_maximum_value = builtins.max(LUT04_values_time_step_list)
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-agricultural-types_log-file.csv'), 'a',
                          newline='') as LPB_log_file:
                    # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                    writer = csv.writer(LPB_log_file)
                    LPB_log_file_data = [a_time_step, year, LUT02_maximum_value, LUT03_maximum_value, LUT04_maximum_value]
                    writer.writerow(LPB_log_file_data)
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB-basic-agricultural-types_log-file.csv'), 'a',
                      newline='') as LPB_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_log_file)
                writer.writerow([])
                writer.writerow(['PLEASE NOTE:'])
                writer.writerow(['LPB-basic maximum agricultural types value over number of samples.'])
                writer.writerow(
                    ['Used only in the yield approach in mplc module for simulation of agricultrual types in corrective allocation.'])

            print('calculating maximum value of agricultural types from samples for time steps done')

        # TODO
        print('calculating mean demands and mean unallocated demands ...')
        self.dictionary_of_mean_demands_and_mean_unallocated_demands = {}

        range_of_samples = range(1, number_of_samples_set + 1)
        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        categories = ['demand', 'unallocated_demand']
        demand_types = ['LUT02', 'LUT03', 'LUT04', 'LUT05', 'AGB']

        for a_time_step in range_of_time_steps:
            self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step] = {}
            for a_category in categories:
                self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category] = {}
                for a_demand_type in demand_types:
                    self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][a_demand_type] = 0

        for a_time_step in range_of_time_steps:
            for a_category in categories:
                LUT02_values_time_step_list = []
                LUT03_values_time_step_list = []
                LUT04_values_time_step_list = []
                LUT05_values_time_step_list = []
                AGB_values_time_step_list = []
                for a_sample in range_of_samples:
                    LUT02_value = \
                        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category]['LUT02']
                    LUT02_values_time_step_list.append(LUT02_value)
                    LUT03_value = \
                        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category]['LUT03']
                    LUT03_values_time_step_list.append(LUT03_value)
                    LUT04_value = \
                        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category]['LUT04']
                    LUT04_values_time_step_list.append(LUT04_value)
                    LUT05_value = \
                        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category]['LUT05']
                    LUT05_values_time_step_list.append(LUT05_value)
                    AGB_value = \
                        dictionary_of_samples_dictionaries_values_unallocated_demands[a_sample][a_time_step][a_category]['AGB']
                    AGB_values_time_step_list.append(AGB_value)
                LUT02_mean_value = (sum(LUT02_values_time_step_list) / len(LUT02_values_time_step_list))
                LUT03_mean_value = (sum(LUT03_values_time_step_list) / len(LUT03_values_time_step_list))
                LUT04_mean_value = (sum(LUT04_values_time_step_list) / len(LUT04_values_time_step_list))
                LUT05_mean_value = (sum(LUT05_values_time_step_list) / len(LUT05_values_time_step_list))
                AGB_mean_value = (sum(AGB_values_time_step_list) / len(AGB_values_time_step_list))
                for a_demand_type in demand_types:
                    if a_demand_type == 'LUT02':
                        self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][
                            a_demand_type] = LUT02_mean_value
                    if a_demand_type == 'LUT03':
                        self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][
                            a_demand_type] = LUT03_mean_value
                    if a_demand_type == 'LUT04':
                        self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][
                            a_demand_type] = LUT04_mean_value
                    if a_demand_type == 'LUT05':
                        self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][
                            a_demand_type] = LUT05_mean_value
                    if a_demand_type == 'AGB':
                        self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step][a_category][
                            a_demand_type] = AGB_mean_value

        self.export_mean_demand_and_mean_unallocated_demand_data_to_tidy_data_folder()
        print('calculating mean demands and mean unallocated demands done')

        # DK&SH: LPB alternation - calculate only the Monte Carlo average and place it in an according sub-folder
        if int(self.nrSamples()) > 1:
            # SH: calculate the MC average for the indicated needed probabilistic variables
            statistics_start_time = datetime.now()
            print('\ncalculating statistics initialized ...',
                  '\n THIS MAY TAKE A WHILE (UP TO HOURS)')

            sample_numbers = self.sampleNumbers()
            time_steps = self.timeSteps()

            # first create the singular MC averages for each land use type
            range_of_land_use_types = range(1, (Parameters.get_total_number_of_land_use_types() + 1))

            # alternative MC calculation for LUTs
            def MCaverage_LPB_for_LUTs(input_maps, output_file_name):
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

            for a_land_use_type in range_of_land_use_types:
                a_land_use_type_path = os.path.join(Filepaths.folder_dynamic_singular_LUTs_probabilistic,
                                                    f'LUT{a_land_use_type:0>2}')
                os.makedirs(a_land_use_type_path, exist_ok=True)

                for time_step in time_steps:

                    # create the time_step_suffix
                    time_step_suffix = str(0)
                    length_of_time_step = len(str(time_step))
                    if length_of_time_step == 1:
                        time_step_suffix = '00' + str(time_step)
                    elif length_of_time_step == 2:
                        time_step_suffix = '0' + str(time_step)
                    elif length_of_time_step == 3:
                        time_step_suffix = str(time_step)


                    # create input maps
                    boolean_maps = []

                    for sample_number in sample_numbers:
                        file_path_of_environmental_map_time_step_sample_number = os.path.join(Filepaths.folder_dynamic_environment_map_probabilistic, str(sample_number), 'LPBLULCC.' + str(time_step_suffix))
                        environment_map = readmap(file_path_of_environmental_map_time_step_sample_number)

                        boolean_map_of_time_step = scalar(boolean(environment_map == a_land_use_type))
                        boolean_maps.append(boolean_map_of_time_step)

                    output_file_path = os.path.join(a_land_use_type_path, 'MC-averages')
                    os.makedirs(output_file_path, exist_ok=True)
                    output_file_name = f'{a_land_use_type}-ave.{time_step:03}'

                    MCaverage_LPB_for_LUTs(input_maps=boolean_maps,
                                           output_file_name=os.path.join(output_file_path, output_file_name))

            print('MC averages for singular land use types calculated')

            # secondly get the other files for which an MC average is needed:
            def MCaverage_LPB(input_files, output_file_name):
                # calculate average
                sum = scalar(0)
                count = scalar(0)
                for filename in input_files:
                    raster = readmap(filename)
                    sum = sum + raster
                    count = ifthen(defined(raster), count + 1)
                mean = sum / count
                # export result
                report(mean, output_file_name)

            # 2.1 create a dictionary of the to be calculated files and their paths
            dictionary_of_to_be_calculated_files = {}

            if Parameters.get_order_of_forest_deforestation_and_conversion() is True: # deforestation_before_conversion
                if probabilistic_output_options_dictionary['deforested_net_forest_map'] == True:
                    dictionary_of_to_be_calculated_files.update({'defo': Filepaths.folder_deforested_before_conversion})

            if probabilistic_output_options_dictionary['conflict_maps'] == True:
                dictionary_of_to_be_calculated_files.update({'fluc': Filepaths.folder_forest_land_use_conflict}) # 0,1
                dictionary_of_to_be_calculated_files.update({'luc': Filepaths.folder_land_use_conflict}) # 0,1

            if probabilistic_output_options_dictionary['AGB_map'] == True:
                dictionary_of_to_be_calculated_files.update({'AGB': Filepaths.folder_AGB}) # scalar mit 0?

            if probabilistic_output_options_dictionary['net_forest_map'] == True:
                dictionary_of_to_be_calculated_files.update({'netf': Filepaths.folder_net_forest}) # 0,1

            if probabilistic_output_options_dictionary['degradation_regeneration_maps'] == True: # 0,1
                dictionary_of_to_be_calculated_files.update({'Dlow': Filepaths.folder_degradation_low})
                dictionary_of_to_be_calculated_files.update({'Dmod': Filepaths.folder_degradation_moderate})
                dictionary_of_to_be_calculated_files.update({'Dsev': Filepaths.folder_degradation_severe})
                dictionary_of_to_be_calculated_files.update({'Dabs': Filepaths.folder_degradation_absolute})
                dictionary_of_to_be_calculated_files.update({'Rlow': Filepaths.folder_regeneration_low})
                dictionary_of_to_be_calculated_files.update({'Rmed': Filepaths.folder_regeneration_medium})
                dictionary_of_to_be_calculated_files.update({'Rhig': Filepaths.folder_regeneration_high})
                dictionary_of_to_be_calculated_files.update({'Rful': Filepaths.folder_regeneration_full})

            # if user-defined, calculate also MCaverages for the yield LUTs
            if Parameters.demand_configuration['overall_method'] == 'yield_units' and probabilistic_output_options_dictionary['yield_maps'] == True:
                if 2 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                    dictionary_of_to_be_calculated_files.update({'L2yi': Filepaths.folder_LUT02_cropland_annual_crop_yields})
                if 3 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                    dictionary_of_to_be_calculated_files.update({'L3yi': Filepaths.folder_LUT03_pasture_livestock_yields})
                if 4 in Parameters.demand_configuration['LUTs_with_demand_and_yield']:
                    dictionary_of_to_be_calculated_files.update({'L4yi': Filepaths.folder_LUT04_agroforestry_crop_yields})

            if probabilistic_output_options_dictionary['succession_age_map'] == True:
                dictionary_of_to_be_calculated_files.update({'suag': Filepaths.folder_succession_age}) # scalar

            # Test if the dictionary has content, if True, calculate the MC averages
            if bool(dictionary_of_to_be_calculated_files):
                # 2.2 channel them one by one through the generic code
                for file_abbreviation, folder_path in dictionary_of_to_be_calculated_files.items():
                    # create the input list for the MC average
                    def create_input_files_list(a_file_name, time_step):
                        file_list = []
                        file_name = generateNameT(a_file_name, time_step)
                        for sample_number in sample_numbers:
                            file_list.append(os.path.join(folder_path, str(sample_number), file_name))
                        return file_list

                    # apply MC average for each time step
                    for time_step in time_steps:
                        file_list_input = create_input_files_list(file_abbreviation, time_step)
                        output_file_path = os.path.join(folder_path, 'MC-averages')
                        os.makedirs(output_file_path, exist_ok=True)
                        output_file_name = f'{file_abbreviation}-ave.{time_step:03}'  # generate a PCRaster conform output
                        MCaverage_LPB(input_files=file_list_input,
                                      output_file_name=os.path.join(output_file_path, output_file_name))

                print('MC averages for additional probabilistic file(s) calculated')

            statistics_end_time = datetime.now()
            print('calculating statistics done')
            print('time elapsed for calculating statistics: {}'.format(statistics_end_time - statistics_start_time))


        print('\nrunning postmcloop done')

        # SH: LPB alternation  movies: non color blind version and accessible viridis version
        movies_start_time = datetime.now()
        print('\nmaking LPB_movies 01 and 02 of the first and last sample for', Parameters.get_number_of_time_steps(),
              'time steps ...')
        command = f'python LPB_movie_01_and_02_LULCC_samples.py {number_of_samples_set}'
        # subprocess.run(command.split(), check=True)
        os.system(command)
        print('making movies of the first and last sample done')

        print('\nmaking VIRIDIS ACCESSIBLE LPB_movies 03 and 04 of the first and last sample for',
              Parameters.get_number_of_time_steps(), 'time steps ...')
        command = f'python LPB_movie_03_and_04_LULCC_samples_VA.py {number_of_samples_set}'
        # subprocess.run(command.split(), check=True)
        os.system(command)
        movies_end_time = datetime.now()
        print('making VIRIDIS ACCESSIBLE movies of the first and last sample done')
        print('time elapsed for movie production: {}'.format(movies_end_time - movies_start_time))

    def export_probabilistic_forest_conversion_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        output_files_data = {
            'LPB_probabilistic_max_forest_conversion_' + str(Parameters.get_model_scenario()): [
                ['total', self.LUTs_total_maximum_value],
                ['LUT01', self.LUT01_maximum_value],
                ['LUT02', self.LUT02_maximum_value],
                ['LUT03', self.LUT03_maximum_value],
                ['LUT04', self.LUT04_maximum_value],
                ['LUT05', self.LUT05_maximum_value]
            ]
        }

        output_file = 'LPB_probabilistic_max_forest_conversion_' + str(Parameters.get_model_scenario())

        with open(os.path.join(Filepaths.folder_LPB_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
            csv_file_writer = csv.writer(csv_file)

            for data_of_row in output_files_data[output_file]:
                    # add time step
                data_of_row.insert(0, self.a_time_step)

                csv_file_writer.writerow(data_of_row)

    def export_probabilistic_mean_forest_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        output_files_data = {
            'LPB_probabilistic_mean_forest_' + str(Parameters.get_model_scenario()): [
                ['mean of probabilistically simulated forest', self.mean_forest_pixels]
            ]
        }

        output_file = 'LPB_probabilistic_mean_forest_' + str(Parameters.get_model_scenario())

        with open(os.path.join(Filepaths.folder_LPB_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
            csv_file_writer = csv.writer(csv_file)

            for data_of_row in output_files_data[output_file]:
                # add time step
                data_of_row.insert(0, self.a_time_step)

                csv_file_writer.writerow(data_of_row)


    def export_mean_demand_and_mean_unallocated_demand_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        range_of_time_steps = range(1, int(Parameters.get_number_of_time_steps()) + 1)
        demand_types = ['LUT02', 'LUT03', 'LUT04', 'LUT05', 'AGB']

        for a_time_step in range_of_time_steps:
            for a_demand_type in demand_types:
                mean_demand = self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step]['demand'][a_demand_type]
                mean_unallocated_demand = self.dictionary_of_mean_demands_and_mean_unallocated_demands[a_time_step]['unallocated_demand'][a_demand_type]
                output_files_data = {
                    'LPB_basic_mean_demand_and_mean_unallocated_demand_' + str(Parameters.get_model_scenario()): [
                        [a_demand_type, mean_demand, mean_unallocated_demand]
                    ]
                }

                output_file = 'LPB_basic_mean_demand_and_mean_unallocated_demand_' + str(Parameters.get_model_scenario())

                with open(os.path.join(Filepaths.folder_LPB_tidy_data, output_file + '.csv'), 'a', newline='') as csv_file:
                    csv_file_writer = csv.writer(csv_file)

                    for data_of_row in output_files_data[output_file]:
                        # add time step
                        data_of_row.insert(0, a_time_step)

                        csv_file_writer.writerow(data_of_row)


        # 'LPB-basic_mean_demand_and_mean_unallocated_demand_' + str(Parameters.get_model_scenario()): ['mean_demand', 'mean_unallocated_demand']


###################################################################################################
# SH: execute LPB - most probable landscape configuration simulation

def get_LPB_most_probable_landscape_configuration():

    print('\n##############################################################')
    command = "python LULCC_mplc.py"
    # subprocess.run(command.split(), check=True)
    # subprocess.call(command)
    # subprocess.run(command)
    subprocess.run(command.split())
    # os.system(command)
    print('\n##############################################################')

###################################################################################################
# SH: execute LPB - possible landscape configuration simulation

def get_LPB_RAP_landscape_configuration():
    print('\n##############################################################')
    command = "python LULCC_RAP.py"
    # subprocess.run(command.split(), check=True)
    # subprocess.call(command)
    # subprocess.run(command)
    subprocess.run(command.split())
    #os.system(command)
    print('\n##############################################################')

###################################################################################################
# DK: suggested supra structure of the model, DK&SH: co-implementation

def run_LPB_basic_framework():
    # import additional methods
    get_filepaths()
    set_number_of_worker_threads()
    get_required_number_of_samples()
    initialize_global_dictionary_for_forest()
    initialize_global_dictionary_for_forest_conversion()
    initialize_global_dictionary_for_LUT01()
    initialize_global_dictionary_for_LUT05()
    initialize_global_dictionary_for_abandoned_types()
    initialize_global_dictionary_for_agricultural_types()
    initialize_global_dictionary_for_LUT17()
    if not (Parameters.demand_configuration['overall_method'] == 'footprint' and Parameters.demand_configuration['internal_or_external'] == 'internal'):
        initialize_global_dictionary_of_unallocated_demands()
    give_user_information_model_settings()
    get_pre_simulation_map_correction_step_decision()
    initiate_LPB_log_file_csv()
    initiate_LPB_nan_log_file_csv()
    initiate_LPB_deforestation_nan_log_file_csv()
    if Parameters.demand_configuration['overall_method'] == 'yield_units': initiate_LPB_basic_unallocated_demand_yield_units_log_file()
    # run the MonteCarlo model
    number_of_time_steps = Parameters.get_number_of_time_steps()
    number_of_samples = number_of_samples_set
    my_model = LandUseChangeModel()
    dynamic_model = DynamicFramework(my_model, number_of_time_steps)
    monte_carlo_model = MonteCarloFramework(dynamic_model, number_of_samples)
    monte_carlo_model.run()
    delete_false_sample_folders()
    return run_LPB_basic_framework

def run_LPB_mplc_framework():
    get_LPB_most_probable_landscape_configuration()
    return run_LPB_mplc_framework

def run_RAP_framework():
    get_LPB_RAP_landscape_configuration()
    return run_RAP_framework

def run_SFM_framework():
    return run_SFM_framework

def run_OC_framework():
    return run_SFM_framework


if __name__ == "__main__":

    # start counting time of model execution
    start_time = datetime.now()

    # user information
    print('\nINITIALIZING', Parameters.get_model_version(), 'RUNNING FOR THE', Parameters.get_model_baseline_scenario(), Parameters.get_model_scenario(),
          'SCENARIO in:', Parameters.get_country(), Parameters.get_region())

    if Parameters.get_model_version() == 'LPB-basic':
        print('\nINITIALIZING LPB - BASIC PROBABILISTIC MODELLING ...')
        run_LPB_basic_framework()
        print('\nLPB-BASIC DONE')

    elif Parameters.get_model_version() == 'LPB-mplc':
        print('\nINITIALIZING LPB - BASIC PROBABILISTIC MODELLING ...')
        run_LPB_basic_framework()
        print('\nLPB-BASIC DONE')
        print('\nINITIALIZING LPB - MOST PROBABLE LANDSCAPE CONFIGURATION MODELLING ...')
        run_LPB_mplc_framework()
        print('\nLPB - MOST PROBABLE LANDSCAPE CONFIGURATION MODELLING DONE')

    elif Parameters.get_model_version() == 'LPB-RAP':
        print('\nINITIALIZING LPB - BASIC PROBABILISTIC MODELLING ...')
        run_LPB_basic_framework()
        print('\nLPB-BASIC DONE')
        print('\nINITIALIZING LPB - MOST PROBABLE LANDSCAPE CONFIGURATION MODELLING ...')
        run_LPB_mplc_framework()
        print('\nLPB - MOST PROBABLE LANDSCAPE CONFIGURATION MODELLING DONE')
        print('\nINITIALIZING LPB - RESTORATION AREAS POTENTIALS MODELLING ...')
        run_RAP_framework()
        print('\nLPB - RESTORATION AREAS POTENTIALS MODELLING DONE')

    elif Parameters.get_model_scenario() == 'LPB-SFM':
        print('\nINITIALIZING LPB - SUSTAINABLE FOREST MANAGEMENT MODELLING ...')
        run_SFM_framework()
        print('\nLPB - SUSTAINABLE FOREST MANAGEMENT MODELLING DONE')

    elif Parameters.get_model_scenario() == 'LPB-OC':
        print('\nINITIALIZING LPB - OPPORTUNITY COSTS MODELLING ...')
        run_OC_framework()
        print('\nLPB - OPPORTUNITY COSTS MODELLING DONE')

    # end counting time of model execution
    end_time = datetime.now()

    print('\nMODEL RUN FULLY EXECUTED')
    print('Time elapsed for model execution: {}'.format(end_time - start_time))