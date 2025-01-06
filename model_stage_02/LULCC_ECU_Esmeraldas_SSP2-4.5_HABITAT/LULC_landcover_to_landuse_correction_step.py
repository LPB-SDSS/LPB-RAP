#!--columntable

"""LAFORET-PLUC-BE-RAP/SFM - LULC - from land cover to land use correction step
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK),
2021 Q2/Q3/Q4

This procedure (a deterministic singular simulation step) is needed in regions where Copernicus land cover information overestimates forest. The steps applied are:

  - distribution of:
   a) anthropogenic features (cities, settlements and streets are added)
   b) agriculture land use (LUT02:cropland-annual; LUT03:pasture, LUT04:agroforestry) based on demand in relation to streets, cities and settlements proximity etc allocated.

   If exceptional LUTs in Parameters are declared, no allocation will occur on those.

    For the agricultural types the mean distance from household/settlement to LUT is used in

  ATTENTION: This is basically a shorter LULCC_basic.py for one time step with only one output map, which is placed in an INPUT folder:
  file_initial_LULC_input = os.path.join(Filepaths.folder_inputs_initial, 'initial_LULC_simulated_input').

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
import pandas as pd
from datetime import datetime
from operator import itemgetter
from pcraster import *
from pcraster.framework import *
from pcraster.multicore import *
from pcraster.multicore._operations import *
import Filepaths
import Parameters
import Formulas
import generate_PCRaster_conform_output_name

###################################################################################################
# For testing, debugging and submission: set random seed to make the results consistent (1)
# set random seed 0 = every time new results
seed = int(Parameters.get_random_seed())
setrandomseed(seed)
# dann kannst Du in allen Scripten alle auftreten von numpy.random ersetzen durch Parameters.get_rng(). uniform bleibt gleich, randint muss dann integers werden.
# Das Modul random wuerde ich dann ganz rausnehmen und dafuer auch Parameters.get_rng() verwenden, dann sind nur zwei Optionen im Script (NumPy und PCRaster)
# Parameters.get_rng()

###################################################################################################
# SH: For the correction step the number of samples is 1!

number_of_samples_set = 1

###################################################################################################
# SH: LPB alternation - initiate log files for LPB correction step

with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB_correction-step_log-file.csv')), 'w') as LPB_correction_step_log_file:
    LPB_writer = csv.writer(LPB_correction_step_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Create a title for the CSV
    LPB_correction_step_log_file_title = ['LPB correction step log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                                          Parameters.get_model_scenario() + ' scenario']
    LPB_writer.writerow(LPB_correction_step_log_file_title)
    # indicate the first data of the initial map
    LPB_writer.writerow(['INITIAL MAP BEFORE CORRECTION STEP'])
    # Create the header
    LPB_writer = csv.writer(LPB_correction_step_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_writer = csv.DictWriter(LPB_correction_step_log_file, fieldnames=['YEAR',
                                                                          'population',
                                                                          'singular cities pixels',
                                                                          'singular settlements pixels',
                                                                          'singular streets pixels',
                                                                          'with a share of ' + str(Parameters.get_regional_share_smallholders_of_population()) + ' % population that is smallholder',
                                                                          Parameters.get_pixel_size() + ' demand ' + Parameters.LUT02,
                                                                          Parameters.get_pixel_size() + ' demand ' + Parameters.LUT03,
                                                                          Parameters.get_pixel_size() + ' demand ' + Parameters.LUT04,
                                                                          'initial pixels of ' + Parameters.LUT01,
                                                                          'initial pixels of ' + Parameters.LUT02,
                                                                          'initial pixels of ' + Parameters.LUT03,
                                                                          'initial pixels of ' + Parameters.LUT04,
                                                                          'initial pixels of ' + Parameters.LUT05,
                                                                          'initial pixels of ' + Parameters.LUT06,
                                                                          'initial pixels of ' + Parameters.LUT07,
                                                                          'initial pixels of ' + Parameters.LUT08,
                                                                          'initial pixels of ' + Parameters.LUT09,
                                                                          'initial pixels of ' + Parameters.LUT10,
                                                                          'initial pixels of ' + Parameters.LUT11,
                                                                          'initial pixels of ' + Parameters.LUT12,
                                                                          'initial pixels of ' + Parameters.LUT13,
                                                                          'initial pixels of ' + Parameters.LUT14,
                                                                          'initial pixels of ' + Parameters.LUT15,
                                                                          'initial pixels of ' + Parameters.LUT16,
                                                                          'initial pixels of ' + Parameters.LUT17,
                                                                          'initial pixels of ' + Parameters.LUT18,
                                                                          'initial pixels of ' + Parameters.LUT19])
    LPB_writer.writeheader()
    print('\nfiling LPB_correction-step_log-file.csv initiated ...')

###################################################################################################

# SH: LPB alternation - initiate nan values log files for LPB basic
# this tracks nan values within the cascading allocation in _add (no more suitable cells available)

with open((os.path.join(os.getcwd(), Filepaths.folder_outputs, 'LPB', 'CSVs', 'LPB_correction-step-nan_log-file.csv')), 'w', newline='') as LPB_log_file:
    LPB_writer = csv.writer(LPB_log_file, delimiter=' ',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Create a title for the CSV
    LPB_log_file_title = ['LPB_correction-step-nan log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                          Parameters.get_model_scenario() + ' scenario']
    LPB_writer.writerow(LPB_log_file_title)
    # Create the header
    LPB_writer = csv.writer(LPB_log_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_writer = csv.DictWriter(LPB_log_file, fieldnames=['Sample', 'Time_step', 'Year', 'LUT', 'Degree_of_Limitation'])
    LPB_writer.writeheader()
    # data is filled in the _add procedure if nan values occur (meaning no more cells available in the suitability map)
    print('\nfiling LPB_correction-step-nan_log-file.csv initiated ...')

###################################################################################################

class LandUseType:
    def __init__(self, type_number, environment_map, related_types_list, suitability_factors_list,
                 weights_list, variables_dictionary, noise, null_mask_map, window_length_realization, initial_environment_map,
                 LUT02_sampled_distance_for_this_sample, LUT03_sampled_distance_for_this_sample, LUT04_sampled_distance_for_this_sample,
                 static_areas_on_which_no_allocation_occurs_map,
                 static_LUTs_on_which_no_allocation_occurs_list,
                 difficult_terrain_slope_restriction_dictionary,
                 slope_map):
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

        # plantations # TODO this must be dynamic
        self.new_plantations_map = None

        # TODO this must be from LandUseChangeModel premcloop
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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print('CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:', correction_step_list_of_immutable_LUTs)
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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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
            # JV: Check the lists with immutable land uses
            if self.static_LUTs_on_which_no_allocation_occurs_list is not None:
                for a_number in self.static_LUTs_on_which_no_allocation_occurs_list:
                    boolean_static_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_static_LUT_map)  # now it contains the static LUTs
            correction_step_list_of_immutable_LUTs = Parameters.get_correction_step_list_of_immutable_LUTs()
            if correction_step_list_of_immutable_LUTs is not None:
                for a_number in correction_step_list_of_immutable_LUTs:
                    boolean_immutable_LUT_map = pcreq(self.environment_map, a_number)
                    self.excluded_areas_from_allocation_map = pcror(self.excluded_areas_from_allocation_map,
                                                                    boolean_immutable_LUT_map)  # now it contains the static LUTs
            print(
                'CORRECTION STEP: self.excluded_areas_from_allocation_map contains here additionally correction_step_list_of_immutable_LUTs:',
                correction_step_list_of_immutable_LUTs)

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

        # get areas, that are probably sanctioned land use in restricted areas
        sanctioned_LUTs_list = [2, 3, 4, 14, 15, 16]
        sanctioned_land_use_map = boolean(self.null_mask_map)
        for a_LUT in sanctioned_LUTs_list:
            sanctioned_land_use_map = ifthenelse(scalar(self.environment_map) == scalar(a_LUT),
                                                 boolean(1),
                                                 boolean(sanctioned_land_use_map))
        # extract those areas from the immutable map
        self.favorable_terrain_in_restricted_areas_mask_map = ifthenelse(
            boolean(sanctioned_land_use_map) == boolean(1),
            boolean(0),
            boolean(self.favorable_terrain_in_restricted_areas_mask_map))

        print('updated self.favorable_terrain_in_restricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_difficult_terrain_in_restricted_areas_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask includes areas of difficult terrain in restricted areas."""
        self.difficult_terrain_in_restricted_areas_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.difficult_terrain_in_restricted_areas_mask_map = pcror(
                self.difficult_terrain_in_restricted_areas_mask_map, slope_dependent_areas_of_no_allocation_map)

        # get areas, that are probably sanctioned land use in restricted areas
        sanctioned_LUTs_list = [2, 3, 4, 14, 15, 16]
        sanctioned_land_use_map = boolean(self.null_mask_map)
        for a_LUT in sanctioned_LUTs_list:
            sanctioned_land_use_map = ifthenelse(scalar(self.environment_map) == scalar(a_LUT),
                                                 boolean(1),
                                                 boolean(sanctioned_land_use_map))
        # extract those areas from the immutable map
        self.difficult_terrain_in_restricted_areas_mask_map = ifthenelse(
            boolean(sanctioned_land_use_map) == boolean(1),
            boolean(0),
            boolean(self.difficult_terrain_in_restricted_areas_mask_map))
        print('updated self.difficult_terrain_in_restricted_areas_mask_map')

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_favorable_terrain_landscape_wide_mask(self, excluded_areas_from_allocation_map, slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask is used for the worst-case scenario and includes all available favorable areas."""
        self.favorable_terrain_landscape_wide_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.favorable_terrain_landscape_wide_map = pcror(
                self.favorable_terrain_landscape_wide_mask_map, slope_dependent_areas_of_no_allocation_map)

    # SH: LPB alternation - DELIVERS A MASK OF A NEGATIVE TYPE
    def create_difficult_terrain_landscape_wide_mask(self, excluded_areas_from_allocation_map,slope_dependent_areas_of_no_allocation_map):
        """ SH: this mask is used for the worst case scenario and includes all difficult areas."""
        self.difficult_terrain_landscape_wide_mask_map = excluded_areas_from_allocation_map
        if slope_dependent_areas_of_no_allocation_map is not None:
            self.difficult_terrain_landscape_wide_mask_map = pcror(
                self.difficult_terrain_landscape_wide_mask_map, slope_dependent_areas_of_no_allocation_map)

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
        ## JV:   report(neighbor_suitability, 'neighbor_suitability')
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
        ## JV:   report(road_suitability, 'streetsuit' + str(self.type_number))
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
        ## JV:    report(water_suitability, 'waterSuit' + str(self.type_number))
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
        ## JV:   report(city_suitability, 'citySuit' + str(self.type_number))
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
        ## JV:   report(city_suitability, 'citySuit' + str(self.type_number))
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
        ## JV:   report(population_suitability_map, 'popSuit' + str(self.type_number))
        print('population-suitability for LUT', self.type_number, 'calculated')
        return population_suitability_map

    # SH: LPB alternation to net forest edge (7)
    ## JV: 8
    # SH: LPB alternation - net forest edge, net forest is based on national maps declared land surface of "native forest"
    def _get_net_forest_edge_suitability(self, net_forest_map):
        not_net_forest_environment_map = ifthenelse(net_forest_map,
                                                    nominal(0),
                                                    nominal(self.environment_map)) # landscape with all LUTs where current net forest is 0
        not_the_current_LUT_map = pcrne(not_net_forest_environment_map, self.type_number) # a map with all other LUTs within the cut out map
        distances_to_net_forest_edge_map = spread(not_the_current_LUT_map, 1, 1)
        net_forest_edge_suitability_map = self._normalize_map(-1 / distances_to_net_forest_edge_map)
        # report(net_forest_edge_suitability_map, os.path.join(Filepaths.folder_TEST,
        #                                                      'net_forest_edge_suitability_map_' + str(
        #                                                          self.current_sample_number) + '_' + str(
        #                                                          self.year) + '.map'))
        #  all good in a 40 year run
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
    # TODO for model stage 3
    def _get_yield_suitability(self):
        """ JV: Return suitability map based on yield for crops or cattle."""
        ##    self.yieldFrac = self._normalize_map(yieldFrac)
        variables_list = self.variables_dictionary.get(5) # TODO you would have to add this again
        friction = variables_list[0]
        yieldRelation = exp(friction * self.yieldFrac)
        yieldSuitability = self._normalize_map(yieldRelation)
        ##    report(yieldSuitability, 'yieldSuit')
        return yieldSuitability

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

    ## JV:   report(self.initial_suitability_map, 'iniSuit' + str(self.type_number))

    # SH: LPB alternation
    def get_total_suitability_map(self, environment_map, distances_to_settlements_map, population_map, net_forest_map):
        """ JV: Return the total suitability map for the land use type.
        Uses a lists and two dictionaries:
        factors -- the names (numbers) of the suitability factors (methods) needed
        parameters -- the input parameters for those factors
        weights -- the weights that belong to those factors (how they're combined). """

        # TODO - Judith wrote to eliminate the initial-suitability-map and weight calculation from this method - but should'nt we use it as the initial suitability map and weight?
        # Does this then need appending to a list instead of self?

        print('LUT', self.type_number, 'suitability factors list in dynamic suitability: ', self.suitability_factors_list)

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
        print('\ncalculating dynamic suitabilities for LUT', self.type_number, 'initiated ...')
        for a_factor in self.suitability_factors_list:
            if a_factor == 1:  # suitability factor = number of neighbors same class
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
            elif a_factor in (2, 3, 4):
                # JV: Static factors already captured in the initial suitability map
                # SH: static factors are now only:
                # 2 = street distance
                # 3 = freshwater distance
                # 4 = city distance
                pass
            else:
                print('\nERROR: unknown suitability factor for land use',
                      self.type_number)
            iteration += 1
        # SH: new code self.total_suitability_map (inaccessible is subtracted in _add)
        suitability_map += self.initial_suitability_map
        suitability_map += self.small_noise_map
        self.total_suitability_map = self._normalize_map(suitability_map)
        print('maximum suitability map for LUT', self.type_number, 'calculated')
        return self.total_suitability_map #self.only_inaccessible_excluded_suitability_map  # former self.total_suitability_map

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
    def set_maximum_yield(self, maximum_yield):
        """ JV: Set the maximum yield in this time step using the input from the tss."""
        converted_maximum_yield_map = (maximum_yield / self.to_square_meters) * cellarea()
        own_maximum_yield_map = ifthen(self.environment_map == self.type_number, converted_maximum_yield_map)
        ## maximum yield PER CELL
        self.maximum_yield = float(mapmaximum(own_maximum_yield_map))
        self.yield_map = self.yield_fraction * self.maximum_yield

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
        
        In the correction step only the BAU[restricted areas used when necessary] or BAU(+)[restricted areas flat excluded by additional dataset] allocation is conducted"""

        # set the path for the land use types
        self.set_environment(temporal_environment_map)
        self._update_current_area_occupied_by_LUT(temporal_environment_map)
        # SH: LPB alternation
        self.demand = demand[self.type_number]  # DK: suggestion
        print('\nland use type number is:', self.type_number)
        if self.type_number == 1:
            print('that is:', Parameters.LUT01)
        elif self.type_number == 2:
            print('that is:', Parameters.LUT02)
        elif self.type_number == 3:
            print('that is:', Parameters.LUT03)
        elif self.type_number == 4:
            print('that is:', Parameters.LUT04)
        elif self.type_number == 5:
            print('that is:', Parameters.LUT05)
        print('\ndemand is:', self.demand, Parameters.get_pixel_size())
        # SH: LPB alternation
        number_of_to_be_added_cells, only_new_pixels_map = None, None
        if self.type_number == 1:
            print('total built-up area stays as prior corrected:', self.current_area_occupied_by_LUT, Parameters.get_pixel_size())

        elif self.type_number in [2, 3, 4]:
            print('total area/acreage currently occupied is:', self.current_area_occupied_by_LUT, Parameters.get_pixel_size())
            area_occupied = self.current_area_occupied_by_LUT
            if self.demand > area_occupied:
                print('CORRECTION STEP: agriculturual LUT area must be increased for time step 1, so allocate more area/acreage according to demand')
                number_of_to_be_added_cells, only_new_pixels_map, immutables_map = self._add(immutables_map)
            if self.demand < area_occupied:
                print('CORRECTION STEP: agriculturual LUT area must be decreased for time step 1, so allocate less area/acreage according to demand')
                self._remove()


        # SH: LPB alternation - Plantations
        elif self.type_number == 5:
            print('plantation area stays as is:', self.current_area_occupied_by_LUT, Parameters.get_pixel_size())

        immutables_map = ifthenelse(self.environment_map == self.type_number,
                                        boolean(1),
                                        immutables_map)
        return self.environment_map, immutables_map, number_of_to_be_added_cells, only_new_pixels_map, temporal_succession_age_map

    # SH: LPB alternation - cascade BAU add allocation
    def _add(self, immutables_map):
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

        print('\nallocation of LUT', self.type_number, 'of demand:', self.demand, Parameters.get_pixel_size())

        suitabilities_without_immutables_map = ifthen(pcrnot(immutables_map),
                                                      scalar(self.total_suitability_map))

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
            if area_after_addition == self.demand:
                print('-> demand of', self.demand, Parameters.get_pixel_size(), 'by LUT', self.type_number,
                      'was satisfied by', area_after_addition, Parameters.get_pixel_size(),
                      'in available favorable unrestricted landscape area, no allocation in difficult terrain and no conflict')
        if map_maximum_NaN == True:
            sample = self.current_sample_number
            time_step = self.time_step
            year = self.year
            LUT = self.type_number
            degree_of_limitation = "favorable_terrain_in_unrestricted_areas"
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB_correction-step-nan_log-file.csv'), 'a',
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
                                                          scalar(self.total_suitability_map))

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
                with open(os.path.join(Filepaths.folder_CSVs, 'LPB_correction-step-nan_log-file.csv'), 'a',
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
                                                              scalar(self.total_suitability_map))

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
                    area_after_addition = int(
                        maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
                    print('area_after_addition:', area_after_addition)
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
                    with open(os.path.join(Filepaths.folder_CSVs, 'LPB_correction-step-nan_log-file.csv'), 'a',
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
                                                                  scalar(self.total_suitability_map))

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
                        self.current_area_occupied_by_LUT = self._update_current_area_occupied_by_LUT(
                            self.environment_map)
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
                        area_after_addition = int(
                            maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
                        print('area_after_addition:', area_after_addition)
                        if area_after_addition == self.demand:
                            print('-> demand was satisfied in difficult terrain in restricted areas => conflict')
                    if map_maximum_NaN == True:
                        # write the data into the log file ['Sample', 'Time step', 'Year', 'LUT', 'Degree of Limitation']
                        sample = self.current_sample_number
                        time_step = self.time_step
                        year = self.year
                        LUT = self.type_number
                        degree_of_limitation = "difficult_terrain_in_restricted_areas"
                        with open(os.path.join(Filepaths.folder_CSVs, 'LPB_correction-step-nan_log-file.csv'), 'a',
                                  newline='') as LPB_log_file:
                            # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                            writer = csv.writer(LPB_log_file)
                            LPB_log_file_data = [sample, time_step, year, LUT, degree_of_limitation]
                            writer.writerow(LPB_log_file_data)
                    if map_maximum_NaN == True or area_after_addition != self.demand:
                        print('-> demand could not be satisfied  => trans-regional leakage likely')
        return number_of_to_be_added_cells, only_new_pixels_map, immutables_map

# SH: LPB alternation - define the singular abandoned land use types
    def _remove(self):
        """ JV: remove cells of this land use type until demand is full filled."""
        # JV: Only cells already occupied by this land use can be removed
        # SH: LPB alternation: declare the singular LUTs cells with lowest suitability with the according abandoned LUT if demand is lower than current area occupied.
        """ abandoned agriculture LUTs are:
        LUT14 = 'cropland-annual - - abandoned'
        LUT15 = 'pasture - - abandoned'
        LUT16 = 'agroforestry - - abandoned' """

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
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        elif self.type_number == 3:  # LUT03 = pasture
            temporal_environment_map = ifthen(ordered_map < ordered_minimum_plus_difference,
                                              nominal(15))  # turns into pasture - - abandoned
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        elif self.type_number == 4:  # LUT04 = agroforestry
            temporal_environment_map = ifthen(ordered_map < ordered_minimum_plus_difference,
                                              nominal(16))  # turns into agroforestry - - abandoned
            temp_environment_map = cover(temporal_environment_map, self.environment_map)
        self.set_environment(temp_environment_map)
        area_after_subtraction = int(maptotal(scalar(boolean(scalar(temp_environment_map) == self.type_number))))
        print('end result of area occupied by LUT', self.type_number, 'after abandoning area of',
              int(number_of_to_be_subtracted_cells), Parameters.get_pixel_size(), 'is:',
              area_after_subtraction, Parameters.get_pixel_size())




###################################################################################################

class LandUse:
    def __init__(self,
                 types,
                 initial_environment_map,
                 environment_map,
                 null_mask_map,
                 year,
                 spatially_explicit_population_maps_dictionary,
                 settlements_map,
                 net_forest_map,
                 dem_map,
                 static_restricted_areas_map,
                 streets_map,
                 cities_map,
                 static_areas_on_which_no_allocation_occurs_map,
                 static_LUTs_on_which_no_allocation_occurs_list,
                 difficult_terrain_slope_restriction_dictionary,
                 LUT02_sampled_distance_for_this_sample,
                 LUT03_sampled_distance_for_this_sample,
                 LUT04_sampled_distance_for_this_sample):

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

        self.new_plantations_deforested_map = None
        self.new_plantations_map = None

        # environment variables:
        # net forest is forest area according to national maps
        self.net_forest_map = net_forest_map

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
        print(
                'creating the missing initial population file by calculation of linear development between gridded data points if needed ...')

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
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2020:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2020_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2030:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2030_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2040:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2040_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2050:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2050_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2060:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2060_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2070:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2070_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2080:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2080_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2090:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2090_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))
            elif self.year == 2100:
                self.spatially_explicit_population_map = self.spatially_explicit_population_maps_dictionary['file_projection_decadal_population_2100_input']
                self.population_map = cover(self.spatially_explicit_population_map, scalar(self.null_mask_map))
                self.population = math.ceil(maptotal(self.population_map))
                print('year:', self.year, 'population:', self.population)
                # report(self.population_map, os.path.join(folder_TEST, 'population_' + str(self.current_sample_number) + '_' + str(self.year) + '.map'))

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


    # END OF METHODS RUN PRE ALLOCATION

    # METHODS RUN FOR ALLOCATION

    # SH: LPB alternation - Demand is now derived from the annual population development
    def update_demand(self):
        print('\nCORRECTION STEP DEMAND CALUCLATION')
        print('\ncalculating demand initiated ...')
        # SH: LPB alternation - DYNAMIC DISCRETE DEMAND BASED ON POPULATION (OR STATIC IN CASE OF PLANTATIONS)

        demand_AGB = 0
        print('CORRECTION STEP demand in AGB in Mg is: ', demand_AGB, 'since this step does not simulate deforestation yet')

        # demand in LUT01 = built-up is determined by a rule of three approach per time step and rounded up for determination of maximum impact
        built_up_map = ifthenelse(self.environment_map == 1,
                                  boolean(1),
                                  boolean(self.null_mask_map))
        demand_LUT01 = math.ceil(maptotal(scalar(built_up_map)))
        print('CORRECTION STEP demand in built-up stays as is:', demand_LUT01, Parameters.get_pixel_size())

        # demand in agriculture in LPB is the demand of the smallholder share of the population and its applied LaForeT demand in LUTs
        demand_agriculture_dictionary = Parameters.get_regional_agriculture_ha_demand_per_LUT_per_person()
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

        demand = {
            1: demand_LUT01, # built-up
            2: demand_LUT02, # cropland-annual
            3: demand_LUT03, # pasture
            4: demand_LUT04, # agroforestry
            5: demand_LUT05  # plantation
        }
        print('calculating demand done')

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
                                                   self.slope_map
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

        # get areas, that are probably sanctioned land use in restricted areas
        sanctioned_LUTs_list = [2, 3, 4]
        sanctioned_land_use_map = boolean(self.null_mask_map)
        for a_LUT in sanctioned_LUTs_list:
            sanctioned_land_use_map = ifthenelse(scalar(self.environment_map) == scalar(a_LUT),
                                                 boolean(1),
                                                 boolean(sanctioned_land_use_map))
        # extract those areas from the immutable map
        self.immutable_excluded_areas_from_allocation_map = ifthenelse(boolean(sanctioned_land_use_map) == boolean(1),
                                                                       boolean(0),
                                                                       boolean(self.immutable_excluded_areas_from_allocation_map))

    # SH: original PLUC method
    def determine_distance_to_streets(self, boolean_map_streets):
        """ JV: Create map with distance to streets, given a boolean map with streets."""
        self.distances_to_streets_map = spread(boolean_map_streets, 0, 1)
    ## JV:   report(self.distances_to_streets, 'distances_to_streets')

    # SH: original PLUC method
    def determine_distance_to_freshwater(self, boolean_map_freshwater):
        """ JV: Create map with distance to freshwater, given a boolean map with freshwater."""
        self.distances_to_freshwater_map = spread(boolean_map_freshwater, 0, 1)
    ##  JV:  report(self.distances_to_freshwater, 'distances_to_freshwater')

    # SH: original PLUC method
    def determine_distance_to_cities(self, boolean_map_cities):
        """ JV: Create map with distance to cities, using a boolean map with cities."""
        self.distances_to_cities_map = spread(boolean_map_cities, 0, 1)
    ##  JV:  report(self.distances_to_cities, 'distances_to_cities')

    # SH: LPB alternation
    def determine_distance_to_settlements(self, settlements_map):
        """ SH: Create map with distance to settlements, using a boolean map with settlements.
        Settlements are calculated dynamically in LandUse."""
        self.distances_to_settlements_map = spread(settlements_map, 0, 1)

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


    # SH: LPB alternation - deleted maxYield, adjusted immutables map, DK added plantation
    def allocate(self, demand):
        """ SH: Allocate as much of a land use type as calculated demand is based on population development in the range of suitability."""
        temporal_environment_map = self.environment_map
        temporal_succession_age_map = self.null_mask_map # CORRECTION STEP, NO SUCCESSION REQUIRED
        immutables_map = self.immutable_excluded_areas_from_allocation_map
        if Parameters.get_dynamic_LUTs_on_which_no_allocation_occurs() is not None:
            dynamic_LUTs_on_which_no_allocation_occurs_list = Parameters.get_dynamic_LUTs_on_which_no_allocation_occurs()
            for a_number in dynamic_LUTs_on_which_no_allocation_occurs_list:
                boolean_dynamic_LUT_map = pcreq(self.environment_map, a_number)
                immutables_map = pcror(boolean(immutables_map), boolean(boolean_dynamic_LUT_map))
        # allocate the active land use types
        for a_type in self.land_use_types:
            temporal_environment_map, immutables_map, number_of_to_be_added_cells, only_new_pixels_map, temporal_succession_age_map = a_type.allocate(demand, temporal_environment_map, immutables_map, temporal_succession_age_map)
            # CORRECTION STEP: NO CALCULATIONS FOR PLANTATION
            if a_type.type_number == 5:
                pass
        self.succession_age_map = temporal_succession_age_map
        self.set_environment(temporal_environment_map)

    # END OF ALLOCATION METHODS PLUC/LPB

    # POST ALLOCATION METHODS:

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


    # SH: original PLUC method
    def get_environment(self):
        """Return the current land use map."""
        print('current environment map returned')
        return self.environment_map

###################################################################################################

class LandUseChangeModel(DynamicModel):
    def __init__(self):
        DynamicModel.__init__(self)
        setclone(f"{Filepaths.file_static_null_mask_input}.map")

    def initial(self):
        print('\n>>> running initial ...')

        #### prepare tidy data ######
        self.tidy_output_folder, self.tidy_output_files_definitions = self._prepare_tidy_output()
        print('\nprepared tidy data output')

        # SH: LPB alternation - management variables
        self.time_step = None
        self.current_sample_number = None
        self.year = Parameters.get_initial_simulation_year()


        # ORIGINAL PLUC VARIABLES
        # SH: a map depicting the study area with only zeros and missing values, for calculation purposes
        self.null_mask_map = self.readmap(Filepaths.file_static_null_mask_input)
        # dem
        self.dem_map = self.readmap(Filepaths.file_static_dem_input)
        # streets (former roads, finer level in LPB)
        if Parameters.get_dynamic_street_network_simulation_decision() == False:
            streets_map = self.readmap(Filepaths.file_initial_streets_input)
        else:
            streets_map = self.readmap(Filepaths.file_static_streets_input)
        self.streets_map = cover(streets_map, boolean(self.null_mask_map))
        # water (here called freshwater, as we depict only freshwater and not the sea with this file)
        freshwater_map = self.readmap(Filepaths.file_static_freshwater_input)
        self.freshwater_map = cover(freshwater_map, boolean(self.null_mask_map))
        # cities
        cities_map = self.readmap(Filepaths.file_static_cities_input)
        self.cities_map = cover(cities_map, boolean(self.null_mask_map))
        # HINT: SH: in LPB we do not use static excluded areas, but static restricted areas which can be overwritten in a second allocation search,
        # substitute the nullmask with a map for the BAU(+) scenario if you want to simulate permanently excluded areas
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

        # CORRECTION STEP VARIABLES
        self.initial_environment_map = self.readmap(Filepaths.file_initial_LULC_input)
        net_forest_map = self.readmap(Filepaths.file_initial_net_forest_input)
        self.net_forest_map = cover(net_forest_map, boolean(self.null_mask_map))
        # we added settlements for a finer level in LPB
        settlements_map = self.readmap(Filepaths.file_initial_settlements_input)
        self.settlements_map = cover(settlements_map, boolean(self.null_mask_map))
        # the restricted areas are used for derivation of forest land use conflict
        static_restricted_areas_map = self.readmap(Filepaths.file_static_restricted_areas_input)
        self.static_restricted_areas_map = cover(boolean(static_restricted_areas_map), boolean(self.null_mask_map))

        # regional_distances_for_agricultural_land_use_dictionary
        self.regional_distance_values_for_agricultural_land_use_dictionary = Parameters.get_regional_distance_values_for_agricultural_land_use_dictionary()
        # pre data setting:
        self.LUT02_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[2][0]
        self.LUT03_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[3][0]
        self.LUT04_mean_distance_to_settlements = self.regional_distance_values_for_agricultural_land_use_dictionary[4][0]


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

        # SH LPB PRE CORRECTION STEP ALTERNATION:
        self.environment_map = self.initial_environment_map

        # SH PRE CORRECTION STEP ALTERNATION: GET THE DATA ON THE INITIAL INPUT MAPS FOR THE CSV OUTPUT
        self.cities_pixels = int(maptotal(scalar(self.cities_map)))
        self.settlements_pixels = int(maptotal(scalar(self.settlements_map)))
        self.streets_pixels = int(maptotal((scalar(self.streets_map))))
        self.initial_pixels_LUT01 = int(maptotal(scalar(boolean(self.environment_map == 1))))
        self.initial_pixels_LUT02 = int(maptotal(scalar(boolean(self.environment_map == 2))))
        self.initial_pixels_LUT03 = int(maptotal(scalar(boolean(self.environment_map == 3))))
        self.initial_pixels_LUT04 = int(maptotal(scalar(boolean(self.environment_map == 4))))
        self.initial_pixels_LUT05 = int(maptotal(scalar(boolean(self.environment_map == 5))))
        self.initial_pixels_LUT06 = int(maptotal(scalar(boolean(self.environment_map == 6))))
        self.initial_pixels_LUT07 = int(maptotal(scalar(boolean(self.environment_map == 7))))
        self.initial_pixels_LUT08 = int(maptotal(scalar(boolean(self.environment_map == 8))))
        self.initial_pixels_LUT09 = int(maptotal(scalar(boolean(self.environment_map == 9))))
        self.initial_pixels_LUT10 = int(maptotal(scalar(boolean(self.environment_map == 10))))
        self.initial_pixels_LUT11 = int(maptotal(scalar(boolean(self.environment_map == 11))))
        self.initial_pixels_LUT12 = int(maptotal(scalar(boolean(self.environment_map == 12))))
        self.initial_pixels_LUT13 = int(maptotal(scalar(boolean(self.environment_map == 13))))
        self.initial_pixels_LUT14 = int(maptotal(scalar(boolean(self.environment_map == 14))))
        self.initial_pixels_LUT15 = int(maptotal(scalar(boolean(self.environment_map == 15))))
        self.initial_pixels_LUT16 = int(maptotal(scalar(boolean(self.environment_map == 16))))
        self.initial_pixels_LUT17 = int(maptotal(scalar(boolean(self.environment_map == 17))))
        self.initial_pixels_LUT18 = int(maptotal(scalar(boolean(self.environment_map == 18))))
        self.initial_pixels_LUT19 = int(maptotal(scalar(boolean(self.environment_map == 19))))

        # Correct the landscape only to anthropogenic features until a cell edge length of 100 m, above would be unproportional
        if Parameters.get_cell_length_in_m() <= 100:
            print('\nCORRECTION STEP: updating self.environment_map by anthropogenic features initialized ...')
            self.environment_map = ifthenelse(self.cities_map,  # we incorporate aggregated built-up information from cities
                                              nominal(1),
                                              nominal(self.environment_map))
            print('CORRECTION STEP: adding cities done')
            self.environment_map = ifthenelse(self.settlements_map,
                                              # we incorporate aggregated built-up information from settlements
                                              nominal(1),
                                              nominal(self.environment_map))
            print('CORRECTION STEP: adding settlements done')
            self.environment_map = ifthenelse(self.streets_map,
                                              # we incorporate aggregated built-up information from streets
                                              nominal(1),
                                              nominal(self.environment_map))
            print('CORRECTION STEP: adding streets done')
            print('CORRECTION STEP: updating self.environment_map by anthropogenic features done')

        # SAMPLING DISTANCE FOR THE SAMPLE IF SAMPLES > 1 IF THIS APPROACH IS TO BE USED
        self.LUT02_sampled_distance_for_this_sample = self.LUT02_mean_distance_to_settlements
        self.LUT03_sampled_distance_for_this_sample = self.LUT03_mean_distance_to_settlements
        self.LUT04_sampled_distance_for_this_sample = self.LUT04_mean_distance_to_settlements

        print('\nself.LUT02_sampled_distance_for_this_sample', self.LUT02_sampled_distance_for_this_sample)
        print('self.LUT03_sampled_distance_for_this_sample', self.LUT03_sampled_distance_for_this_sample)
        print('self.LUT04_sampled_distance_for_this_sample', self.LUT04_sampled_distance_for_this_sample)


        # JV: Create the 'overall' land use class
        self.land_use = LandUse(types=self.active_land_use_types_list,
                                initial_environment_map=self.initial_environment_map,
                                environment_map=self.environment_map,
                                null_mask_map=self.null_mask_map ,
                                year=self.year,
                                spatially_explicit_population_maps_dictionary=self.spatially_explicit_population_maps_dictionary,
                                settlements_map=self.settlements_map,
                                net_forest_map=self.net_forest_map,
                                dem_map=self.dem_map,
                                static_restricted_areas_map=self.static_restricted_areas_map,
                                streets_map=self.streets_map,
                                cities_map = self.cities_map,
                                static_areas_on_which_no_allocation_occurs_map=self.static_areas_on_which_no_allocation_occurs_map,
                                static_LUTs_on_which_no_allocation_occurs_list=self.static_LUTs_on_which_no_allocation_occurs_list,
                                difficult_terrain_slope_restriction_dictionary=self.difficult_terrain_slope_restriction_dictionary,
                                LUT02_sampled_distance_for_this_sample=self.LUT02_sampled_distance_for_this_sample,
                                LUT03_sampled_distance_for_this_sample=self.LUT03_sampled_distance_for_this_sample,
                                LUT04_sampled_distance_for_this_sample=self.LUT04_sampled_distance_for_this_sample
                                )
        self.land_use.update_time_step_and_sample_number_and_year(time_step=self.currentTimeStep(), current_sample_number=self.current_sample_number, year=self.year)

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
        self.land_use.determine_distance_to_settlements(self.settlements_map)  # calculate in initial for the initial simulation year
        self.land_use.calculate_static_suitability_maps()

        print('running initial done')

    def _prepare_tidy_output(self):
        output_folder = Filepaths.folder_LPB_tidy_data

        # define output files and column headers
        output_files_definitions = {
            'LPB_correction_step_' + str(Parameters.get_model_scenario()): ['LUT_code', 'initial_pixels', 'simulated_pixels',
                                                                            'to_LUT01', 'to_LUT02', 'to_LUT03', 'to_LUT04', 'to_LUT05', 'to_LUT08'],
        }

        for file_name, header_columns in output_files_definitions.items():
            header_columns.insert(0, 'time_step')

            with open((os.path.join(output_folder, file_name + '.csv')), 'w', newline='') as csv_file:
                csv_file_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_file_writer.writerow(header_columns)

        return output_folder, output_files_definitions



    def dynamic(self):
        # SH: LPB alternation - global available data from LandUseChangeModel
        self.time_step = self.currentTimeStep()
        if self.time_step == 1:
            self.year = Parameters.get_initial_simulation_year()
        else:
            self.year += 1


        # DK: update LandUse and LandUseType needed variables
        self.land_use.update_time_step_and_sample_number_and_year(time_step=self.time_step,
                                                                      current_sample_number=self.current_sample_number,
                                                                      year=self.year)
        # user information
        print('\nTO BE CALCULATED TIME STEP PRIOR SIMULATION')
        print('simulated year is:', self.year)

        # SH: LPB alternation - EXTENDED PLUC
        # calculate the simulation year, its according spatially explicit population and derived demand,
        # the accompanying maps prior and posterior the central time step calculations, get the CSV input variables

        # SH: LPB alternation - update_accompanying_maps_and_values_prior_time_step
        print('\nupdating accompanying maps prior time step initialized ...')
        self.land_use.update_environment_map_last_time_step()
        self.population, self.population_map, self.population_per_year_list = self.land_use.update_population()
        self.land_use.update_anthropogenic_impact_buffer()
        print('updating accompanying maps prior time step done')

        print('\nupdating demand and according land use change by active land use types initiated ...')
        demand, self.population_number_of_smallholders, demand_AGB = self.land_use.update_demand()
        self.land_use.calculate_suitability_maps()
        self.land_use.allocate(demand)
        print('updating demand and according land use change by active land use types done')

        # SH: LPB alternation - update_accompanying_maps_and_values_posterior_time_step
        print('\nupdating self.environment and accompanying maps posterior allocation initialized ...')
        self.land_use.update_forest_fringe_disturbed()
        print('updating self.environment and accompanying maps posterior allocation done')

        print('\ndraw the complete new self.environment_map ...')
        self.environment_map = self.land_use.get_environment()
        print('\ndraw the complete new self.environment_map done')

        # SH: LPB alternation POST CORRECTION STEP: GET THE SIMULATED MAP DATA FOR THE CSV
        self.cities_pixels = int(maptotal(scalar(self.cities_map)))
        self.settlements_pixels = int(maptotal(scalar(self.settlements_map)))
        self.streets_pixels = int(maptotal((scalar(self.streets_map))))
        self.simulated_pixels_LUT01 = int(maptotal(scalar(boolean(self.environment_map == 1))))
        self.simulated_pixels_LUT02 = int(maptotal(scalar(boolean(self.environment_map == 2))))
        self.simulated_pixels_LUT03 = int(maptotal(scalar(boolean(self.environment_map == 3))))
        self.simulated_pixels_LUT04 = int(maptotal(scalar(boolean(self.environment_map == 4))))
        self.simulated_pixels_LUT05 = int(maptotal(scalar(boolean(self.environment_map == 5))))
        self.simulated_pixels_LUT06 = int(maptotal(scalar(boolean(self.environment_map == 6))))
        self.simulated_pixels_LUT07 = int(maptotal(scalar(boolean(self.environment_map == 7))))
        self.simulated_pixels_LUT08 = int(maptotal(scalar(boolean(self.environment_map == 8))))
        self.simulated_pixels_LUT09 = int(maptotal(scalar(boolean(self.environment_map == 9))))
        self.simulated_pixels_LUT10 = int(maptotal(scalar(boolean(self.environment_map == 10))))
        self.simulated_pixels_LUT11 = int(maptotal(scalar(boolean(self.environment_map == 11))))
        self.simulated_pixels_LUT12 = int(maptotal(scalar(boolean(self.environment_map == 12))))
        self.simulated_pixels_LUT13 = int(maptotal(scalar(boolean(self.environment_map == 13))))
        self.simulated_pixels_LUT14 = int(maptotal(scalar(boolean(self.environment_map == 14))))
        self.simulated_pixels_LUT15 = int(maptotal(scalar(boolean(self.environment_map == 15))))
        self.simulated_pixels_LUT16 = int(maptotal(scalar(boolean(self.environment_map == 16))))
        self.simulated_pixels_LUT17 = int(maptotal(scalar(boolean(self.environment_map == 17))))
        self.simulated_pixels_LUT18 = int(maptotal(scalar(boolean(self.environment_map == 18))))
        self.simulated_pixels_LUT19 = int(maptotal(scalar(boolean(self.environment_map == 19))))

        print('\nstoring INITIAL LULC SIMULATED INPUT MAP initialized ...')
        report(self.environment_map, os.path.join(Filepaths.folder_inputs_initial, 'initial_LULC_simulated_input.map'))
        print('storing INITIAL LULC SIMULATED INPUT MAP done')

        # Analyze the change for a Sankey-diagram
        initial_LUTs = [1,2,5,6,7,8,9,10,11,12,13,19]

        simulation_LUTs = [1,2,3,4,5,8]

        # for each of the initial LUTs draw a singular map and find out how much flow was allocated to the simulated LUTs
        for an_initial_LUT in initial_LUTs:
            a_LUTs_initial_map = ifthen (self.initial_environment_map == an_initial_LUT,
                                         scalar(1))
            for a_simulation_LUT in simulation_LUTs:
                a_simulated_LUT_map = ifthen(self.environment_map == a_simulation_LUT,
                                             scalar(1))
                comparison_map = ifthen(a_LUTs_initial_map == a_simulated_LUT_map,
                                        scalar(1))
                flow_maptotal = int(maptotal(comparison_map))
                # set the variables
                # LUT01
                if an_initial_LUT == 1 and a_simulation_LUT == 1:
                    self.LUT01_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 1 and a_simulation_LUT == 2:
                    self.LUT01_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 1 and a_simulation_LUT == 3:
                    self.LUT01_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 1 and a_simulation_LUT == 4:
                    self.LUT01_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 1 and a_simulation_LUT == 5:
                    self.LUT01_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 1 and a_simulation_LUT == 8:
                    self.LUT01_to_LUT08 = flow_maptotal

                # LUT02
                elif an_initial_LUT == 2 and a_simulation_LUT == 1:
                    self.LUT02_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 2 and a_simulation_LUT == 2:
                    self.LUT02_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 2 and a_simulation_LUT == 3:
                    self.LUT02_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 2 and a_simulation_LUT == 4:
                    self.LUT02_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 2 and a_simulation_LUT == 5:
                    self.LUT02_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 2 and a_simulation_LUT == 8:
                    self.LUT02_to_LUT08 = flow_maptotal

                # LUT05
                elif an_initial_LUT == 5 and a_simulation_LUT == 1:
                    self.LUT05_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 5 and a_simulation_LUT == 2:
                    self.LUT05_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 5 and a_simulation_LUT == 3:
                    self.LUT05_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 5 and a_simulation_LUT == 4:
                    self.LUT05_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 5 and a_simulation_LUT == 5:
                    self.LUT05_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 5 and a_simulation_LUT == 8:
                    self.LUT05_to_LUT08 = flow_maptotal

                # LUT06
                elif an_initial_LUT == 6 and a_simulation_LUT == 1:
                    self.LUT06_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 6 and a_simulation_LUT == 2:
                    self.LUT06_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 6 and a_simulation_LUT == 3:
                    self.LUT06_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 6 and a_simulation_LUT == 4:
                    self.LUT06_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 6 and a_simulation_LUT == 5:
                    self.LUT06_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 6 and a_simulation_LUT == 8:
                    self.LUT06_to_LUT08 = flow_maptotal

                # LUT07
                elif an_initial_LUT == 7 and a_simulation_LUT == 1:
                    self.LUT07_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 7 and a_simulation_LUT == 2:
                    self.LUT07_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 7 and a_simulation_LUT == 3:
                    self.LUT07_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 7 and a_simulation_LUT == 4:
                    self.LUT07_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 7 and a_simulation_LUT == 5:
                    self.LUT07_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 7 and a_simulation_LUT == 8:
                    self.LUT07_to_LUT08 = flow_maptotal

                # LUT08
                elif an_initial_LUT == 8 and a_simulation_LUT == 1:
                    self.LUT08_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 8 and a_simulation_LUT == 2:
                    self.LUT08_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 8 and a_simulation_LUT == 3:
                    self.LUT08_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 8 and a_simulation_LUT == 4:
                    self.LUT08_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 8 and a_simulation_LUT == 5:
                    self.LUT08_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 8 and a_simulation_LUT == 8:
                    self.LUT08_to_LUT08 = flow_maptotal

                # LUT09
                elif an_initial_LUT == 9 and a_simulation_LUT == 1:
                    self.LUT09_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 9 and a_simulation_LUT == 2:
                    self.LUT09_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 9 and a_simulation_LUT == 3:
                    self.LUT09_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 9 and a_simulation_LUT == 4:
                    self.LUT09_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 9 and a_simulation_LUT == 5:
                    self.LUT09_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 9 and a_simulation_LUT == 8:
                    self.LUT09_to_LUT08 = flow_maptotal

                # LUT10
                elif an_initial_LUT == 10 and a_simulation_LUT == 1:
                    self.LUT10_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 10 and a_simulation_LUT == 2:
                    self.LUT10_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 10 and a_simulation_LUT == 3:
                    self.LUT10_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 10 and a_simulation_LUT == 4:
                    self.LUT10_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 10 and a_simulation_LUT == 5:
                    self.LUT10_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 10 and a_simulation_LUT == 8:
                    self.LUT10_to_LUT08 = flow_maptotal

                # LUT11
                elif an_initial_LUT == 11 and a_simulation_LUT == 1:
                    self.LUT11_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 11 and a_simulation_LUT == 2:
                    self.LUT11_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 11 and a_simulation_LUT == 3:
                    self.LUT11_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 11 and a_simulation_LUT == 4:
                    self.LUT11_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 11 and a_simulation_LUT == 5:
                    self.LUT11_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 11 and a_simulation_LUT == 8:
                    self.LUT11_to_LUT08 = flow_maptotal

                # LUT12
                elif an_initial_LUT == 12 and a_simulation_LUT == 1:
                    self.LUT12_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 12 and a_simulation_LUT == 2:
                    self.LUT12_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 12 and a_simulation_LUT == 3:
                    self.LUT12_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 12 and a_simulation_LUT == 4:
                    self.LUT12_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 12 and a_simulation_LUT == 5:
                    self.LUT12_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 12 and a_simulation_LUT == 8:
                    self.LUT12_to_LUT08 = flow_maptotal

                # LUT13
                elif an_initial_LUT == 13 and a_simulation_LUT == 1:
                    self.LUT13_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 13 and a_simulation_LUT == 2:
                    self.LUT13_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 13 and a_simulation_LUT == 3:
                    self.LUT13_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 13 and a_simulation_LUT == 4:
                    self.LUT13_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 13 and a_simulation_LUT == 5:
                    self.LUT13_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 13 and a_simulation_LUT == 8:
                    self.LUT13_to_LUT08 = flow_maptotal

                # LUT19
                elif an_initial_LUT == 19 and a_simulation_LUT == 1:
                    self.LUT19_to_LUT01 = flow_maptotal
                elif an_initial_LUT == 19 and a_simulation_LUT == 2:
                    self.LUT19_to_LUT02 = flow_maptotal
                elif an_initial_LUT == 19 and a_simulation_LUT == 3:
                    self.LUT19_to_LUT03 = flow_maptotal
                elif an_initial_LUT == 19 and a_simulation_LUT == 4:
                    self.LUT19_to_LUT04 = flow_maptotal
                elif an_initial_LUT == 19 and a_simulation_LUT == 5:
                    self.LUT19_to_LUT05 = flow_maptotal
                elif an_initial_LUT == 19 and a_simulation_LUT == 8:
                    self.LUT19_to_LUT08 = flow_maptotal





        # TODO Melvin: do you need this?

        # os.system('legend --clone LPBLULCC.map -f \"Legend_LULC.txt\" %s '
        #               % generateNameST('LPBLULCC',
        #                                # Filepaths.folder_dynamic_environment_map_probabilistic, # TEST TypeError: generateNameST() takes 3 positional arguments but 4 were given
        #                                self.currentSampleNumber(),
        #                                self.time_step))
        #     # legend version: 4.3.1 (darwin/x86_64)

        # SH: LPB alternation - CSV OUTPUT (note the deterministic output of the LPB basic run - this will be needed in subsequent modules)
        if self.time_step == 1:
            with open(os.path.join(Filepaths.folder_CSVs, 'LPB_correction-step_log-file.csv'), 'a',
                      newline='') as LPB_correction_step_log_file:
                # HINT: the 'a' opens the CSV with a line to append to the existing CSV
                writer = csv.writer(LPB_correction_step_log_file)
                LPB_correction_step_log_file_initial_map_data = [self.year,
                                                                 self.population,
                                                                 self.cities_pixels,
                                                                 self.settlements_pixels,
                                                                 self.streets_pixels,
                                                                 self.population_number_of_smallholders,
                                                                 demand[2],
                                                                 demand[3],
                                                                 demand[4],
                                                                 self.initial_pixels_LUT01,
                                                                 self.initial_pixels_LUT02,
                                                                 self.initial_pixels_LUT03,
                                                                 self.initial_pixels_LUT04,
                                                                 self.initial_pixels_LUT05,
                                                                 self.initial_pixels_LUT06,
                                                                 self.initial_pixels_LUT07,
                                                                 self.initial_pixels_LUT08,
                                                                 self.initial_pixels_LUT09,
                                                                 self.initial_pixels_LUT10,
                                                                 self.initial_pixels_LUT11,
                                                                 self.initial_pixels_LUT12,
                                                                 self.initial_pixels_LUT13,
                                                                 self.initial_pixels_LUT14,
                                                                 self.initial_pixels_LUT15,
                                                                 self.initial_pixels_LUT16,
                                                                 self.initial_pixels_LUT17,
                                                                 self.initial_pixels_LUT18,
                                                                 self.initial_pixels_LUT19]
                writer.writerow(LPB_correction_step_log_file_initial_map_data)
                print('\nadded data of initial map to LPB_correction_step_log-file')
                # put in one empty line
                writer.writerow([])
                # indicate the simulated data of the new initial map
                writer.writerow(['INITIAL SIMULATED MAP AFTER CORRECTION STEP'])
                # Create the header
                LPB_writer = csv.writer(LPB_correction_step_log_file, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                LPB_writer = csv.DictWriter(LPB_correction_step_log_file, fieldnames=['YEAR',
                                                                                      'population',
                                                                                      'singular cities pixels',
                                                                                      'singular settlements pixels',
                                                                                      'singular streets pixels',
                                                                                      'with a share of ' + str(
                                                                                          Parameters.get_regional_share_smallholders_of_population()) + ' % population that is smallholder',
                                                                                      Parameters.get_pixel_size() + ' demand ' + Parameters.LUT02,
                                                                                      Parameters.get_pixel_size() + ' demand ' + Parameters.LUT03,
                                                                                      Parameters.get_pixel_size() + ' demand ' + Parameters.LUT04,
                                                                                      'simulated pixels of ' + Parameters.LUT01,
                                                                                      'simulated pixels of ' + Parameters.LUT02,
                                                                                      'simulated pixels of ' + Parameters.LUT03,
                                                                                      'simulated pixels of ' + Parameters.LUT04,
                                                                                      'simulated pixels of ' + Parameters.LUT05,
                                                                                      'simulated pixels of ' + Parameters.LUT06,
                                                                                      'simulated pixels of ' + Parameters.LUT07,
                                                                                      'simulated pixels of ' + Parameters.LUT08,
                                                                                      'simulated pixels of ' + Parameters.LUT09,
                                                                                      'simulated pixels of ' + Parameters.LUT10,
                                                                                      'simulated pixels of ' + Parameters.LUT11,
                                                                                      'simulated pixels of ' + Parameters.LUT12,
                                                                                      'simulated pixels of ' + Parameters.LUT13,
                                                                                      'simulated pixels of ' + Parameters.LUT14,
                                                                                      'simulated pixels of ' + Parameters.LUT15,
                                                                                      'simulated pixels of ' + Parameters.LUT16,
                                                                                      'simulated pixels of ' + Parameters.LUT17,
                                                                                      'simulated pixels of ' + Parameters.LUT18,
                                                                                      'simulated pixels of ' + Parameters.LUT19
                                                                                      ])
                LPB_writer.writeheader()
                writer = csv.writer(LPB_correction_step_log_file)
                LPB_correction_step_log_file_simulated_map_data = [self.year,
                                                                   self.population,
                                                                   self.cities_pixels,
                                                                   self.settlements_pixels,
                                                                   self.streets_pixels,
                                                                   self.population_number_of_smallholders,
                                                                   demand[2],
                                                                   demand[3],
                                                                   demand[4],
                                                                   self.simulated_pixels_LUT01,
                                                                   self.simulated_pixels_LUT02,
                                                                   self.simulated_pixels_LUT03,
                                                                   self.simulated_pixels_LUT04,
                                                                   self.simulated_pixels_LUT05,
                                                                   self.simulated_pixels_LUT06,
                                                                   self.simulated_pixels_LUT07,
                                                                   self.simulated_pixels_LUT08,
                                                                   self.simulated_pixels_LUT09,
                                                                   self.simulated_pixels_LUT10,
                                                                   self.simulated_pixels_LUT11,
                                                                   self.simulated_pixels_LUT12,
                                                                   self.simulated_pixels_LUT13,
                                                                   self.simulated_pixels_LUT14,
                                                                   self.simulated_pixels_LUT15,
                                                                   self.simulated_pixels_LUT16,
                                                                   self.simulated_pixels_LUT17,
                                                                   self.simulated_pixels_LUT18,
                                                                   self.simulated_pixels_LUT19
                                                                   ]
                writer.writerow(LPB_correction_step_log_file_simulated_map_data)
                writer.writerow([])
                writer.writerow(['PLEASE NOTE:'])
                writer.writerow(['Only anthropogenic features (cities, settlements and streets),'])
                writer.writerow(['agriculture demand (cropland-annual, pasture and agroforestry) distribution and'])
                writer.writerow(['anthropogenic impact on forest (change from undisturbed to disturbed)'])
                writer.writerow(['are implemented in the correction step.'])

                print('added data of simulated initial map to LPB_correction_step_log-file')

        self.export_data_to_tidy_data_folder()
        self.export_data_to_tidy_data_folder_v2()

    print('\nrunning dynamic done')

    def export_data_to_tidy_data_folder(self):
        """machine readable output files by category"""

        # add 'to_LUT01', 'to_LUT02', 'to_LUT03', 'to_LUT04', 'to_LUT05', 'to_LUT08'
        output_files_data = {
            'LPB_correction_step_' + str(Parameters.get_model_scenario()): [
                ['LUT01', self.initial_pixels_LUT01, self.simulated_pixels_LUT01,
                 self.LUT01_to_LUT01, self.LUT01_to_LUT02, self.LUT01_to_LUT03, self.LUT01_to_LUT04, self.LUT01_to_LUT05, self.LUT01_to_LUT08],
                ['LUT02', self.initial_pixels_LUT02, self.simulated_pixels_LUT02,
                 self.LUT02_to_LUT01, self.LUT02_to_LUT02, self.LUT02_to_LUT03, self.LUT02_to_LUT04, self.LUT02_to_LUT05, self.LUT02_to_LUT08],
                ['LUT03', self.initial_pixels_LUT03, self.simulated_pixels_LUT03,
                 None, None, None, None, None, None],
                ['LUT04', self.initial_pixels_LUT04, self.simulated_pixels_LUT04,
                 None, None, None, None, None, None],
                ['LUT05', self.initial_pixels_LUT05, self.simulated_pixels_LUT05,
                 self.LUT05_to_LUT01, self.LUT05_to_LUT02, self.LUT05_to_LUT03, self.LUT05_to_LUT04, self.LUT05_to_LUT05, self.LUT05_to_LUT08],
                ['LUT06', self.initial_pixels_LUT06, self.simulated_pixels_LUT06,
                 self.LUT06_to_LUT01, self.LUT06_to_LUT02, self.LUT06_to_LUT03, self.LUT06_to_LUT04, self.LUT06_to_LUT05, self.LUT06_to_LUT08],
                ['LUT07', self.initial_pixels_LUT07, self.simulated_pixels_LUT07,
                 self.LUT07_to_LUT01, self.LUT07_to_LUT02, self.LUT07_to_LUT03, self.LUT07_to_LUT04, self.LUT07_to_LUT05, self.LUT07_to_LUT08],
                ['LUT08', self.initial_pixels_LUT08, self.simulated_pixels_LUT08,
                 self.LUT08_to_LUT01, self.LUT08_to_LUT02, self.LUT08_to_LUT03, self.LUT08_to_LUT04, self.LUT08_to_LUT05, self.LUT08_to_LUT08],
                ['LUT09', self.initial_pixels_LUT09, self.simulated_pixels_LUT09,
                 self.LUT09_to_LUT01, self.LUT09_to_LUT02, self.LUT09_to_LUT03, self.LUT09_to_LUT04, self.LUT09_to_LUT05, self.LUT09_to_LUT08],
                ['LUT10', self.initial_pixels_LUT10, self.simulated_pixels_LUT10,
                 self.LUT10_to_LUT01, self.LUT10_to_LUT02, self.LUT10_to_LUT03, self.LUT10_to_LUT04, self.LUT10_to_LUT05, self.LUT10_to_LUT08],
                ['LUT11', self.initial_pixels_LUT11, self.simulated_pixels_LUT11,
                 self.LUT11_to_LUT01, self.LUT11_to_LUT02, self.LUT11_to_LUT03, self.LUT11_to_LUT04, self.LUT11_to_LUT05, self.LUT11_to_LUT08],
                ['LUT12', self.initial_pixels_LUT12, self.simulated_pixels_LUT12,
                 self.LUT12_to_LUT01, self.LUT12_to_LUT02, self.LUT12_to_LUT03, self.LUT12_to_LUT04, self.LUT12_to_LUT05, self.LUT12_to_LUT08],
                ['LUT13', self.initial_pixels_LUT13, self.simulated_pixels_LUT13,
                 self.LUT13_to_LUT01, self.LUT13_to_LUT02, self.LUT13_to_LUT03, self.LUT13_to_LUT04, self.LUT13_to_LUT05, self.LUT13_to_LUT08],
                ['LUT19', self.initial_pixels_LUT19, self.simulated_pixels_LUT19,
                 self.LUT19_to_LUT01, self.LUT19_to_LUT02, self.LUT19_to_LUT03, self.LUT19_to_LUT04,
                 self.LUT19_to_LUT05, self.LUT19_to_LUT08]
            ],
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

    def export_data_to_tidy_data_folder_v2(self):

        before = pcr_as_numpy(self.initial_environment_map)
        after = pcr_as_numpy(self.environment_map)

        trans_matrix = pd.crosstab(before.ravel(), after.ravel())
        trans_matrix = trans_matrix.drop(columns=trans_matrix.columns[0])
        trans_matrix = trans_matrix.drop(trans_matrix.index[0])
        trans_matrix.to_csv(os.path.join(Filepaths.folder_LPB_tidy_data, 'LPB_correction_step_transition_matrix_' + str(Parameters.get_model_scenario()) + '.csv'))

###################################################################################################

number_of_time_steps = 1
my_model = LandUseChangeModel()
dynamic_model = DynamicFramework(my_model, number_of_time_steps)
dynamic_model.run()


