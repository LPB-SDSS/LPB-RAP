"""LAFORET-PLUC-BE-RAP/SFM - Create LPB-mplc log-file
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK),
2021 Q2/Q3

This module initiates the extensive LPB-mplc_log_file"""

# SH: execute module

import Filepaths
import Parameters
import csv
import os

# run pre calculation for input in the category names for the 5 top crops
# dictionary of top crops yields
dictionary_of_top_crops_yields = Parameters.get_regional_top_crops_yields_in_Mg_per_ha()

# 5 top crops per country were selected, number is key, values are a list of:
# [name[0], mean yield[1], standard deviation yield[2], percentage of acreage[3] for [4] LUT02(cropland-annual) or LUT04(agroforestry) for the region]
top_crops_data_lists_dictionary = {}

for a_top_crop in dictionary_of_top_crops_yields:
    singular_top_crop_dictionary = {
        'a_top_crop_name': dictionary_of_top_crops_yields[a_top_crop][0],
        'a_top_crop_mean_yield': dictionary_of_top_crops_yields[a_top_crop][1],
        'a_top_crop_standard_deviation_yield': dictionary_of_top_crops_yields[a_top_crop][2],
        'a_top_crop_percentage_of_acreage': dictionary_of_top_crops_yields[a_top_crop][3],
        'a_top_crop_source_LUT': dictionary_of_top_crops_yields[a_top_crop][4]
    }

    top_crops_data_lists_dictionary[a_top_crop] = singular_top_crop_dictionary

# AGB data:
regional_AGB_demand_per_person_per_year = Parameters.get_regional_AGB_demand_per_person()
AGB_total_demand_in_Mg_per_person_per_year = regional_AGB_demand_per_person_per_year[0]
AGB_demand_timber_in_Mg_per_person_per_year = regional_AGB_demand_per_person_per_year[1]
AGB_demand_fuelwood_in_Mg_per_person_per_year = regional_AGB_demand_per_person_per_year[2]
AGB_demand_charcoal_in_Mg_per_person_per_year = regional_AGB_demand_per_person_per_year[3]

# SWITCH DECLARATIONS FOR RESTRICTED AREAS DEPENDING ON SCENARIOS ('current' or 'former' restricted areas)
if Parameters.get_model_scenario() == 'weak_conservation' or Parameters.get_model_scenario() == 'enforced_conservation':
    status = str('CURRENT')
elif Parameters.get_model_scenario() == 'no_conservation':
    status = str('FORMER')

# NOTE GROSS FOREST LIST
gross_forest_list = Parameters.get_gross_forest_LUTs_list()

# open the CSV for LPB-mplc
with open((os.path.join(Filepaths.folder_CSVs, 'LPB-mplc_log-file.csv')),
          'w', newline='') as LPB_mplc_log_file:
    LPB_mplc_writer = csv.writer(LPB_mplc_log_file, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Create a title for the CSV
    LPB_mplc_log_file_title = ['LPB-mplc log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                               Parameters.get_model_scenario() + ' scenario']
    LPB_mplc_writer.writerow(LPB_mplc_log_file_title)

    # 1) Create the header for the ultra- categories
    LPB_mplc_writer = csv.writer(LPB_mplc_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_mplc_writer = csv.DictWriter(LPB_mplc_log_file, fieldnames=[' ',
                                                                    'ULTRA-CATEGORY:',
                                                                    'POPULATION',
                                                                    'ANTHROPOGENIC FEATURES',' ', ' ', ' ',
                                                                    'ANTHROPOGENIC IMPACT BUFFER',' ',
                                                                    'LAND USE TYPES',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ',' ',' ',' ', ' ',' ',
                                                                    'POSSIBLY HIDDEN DEFORESTATION FOR DEMAND IN INPUT BIOMASS', ' ',
                                                                    'FOREST CONVERSION = DEFORESTATION FOR AREA DEMAND', ' ',
                                                                    'LANDSCAPE MODELLING PROBABILITY / UNCERTAINTY',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ',
                                                                    'LAND USE IN ' + status + ' RESTRICTED AREAS',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',' ',
                                                                    'FOREST NET/GROSS DISTURBED/UNDISTURBED',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ',
                                                                    'FOREST IMPACTED BY ANTRHOPOGENIC FEATURES (only disturbed and undisturbed)',
                                                                    ' ', ' ', ' ', ' ', ' ',
                                                                    'FOREST DEGRADATION/REGENERATION (only disturbed and undisturbed)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    'FOREST TYPES AGB in Mg -> Mg Carbon',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ',
                                                                    'FOREST REMAINING WITHOUT DIRECT ANTHROPOGENIC IMPACT (only disturbed and undisturbed)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ',
                                                                    'FOREST 100 years without anthropogenic impact (potential primary stadium)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ',
                                                                    'FOREST HABITAT DISTURBED AND UNDISTURBED', ' ',' ', ' ',
                                                                    '5 TOP CROPS [SELECTED PER COUNTRY] POTENTIAL YIELDS in Mg'
                                                                    ])
    LPB_mplc_writer.writeheader()

    # 2) Create the header for the supra - categories (ALL CAPITAL)
    LPB_mplc_writer = csv.writer(LPB_mplc_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_mplc_writer = csv.DictWriter(LPB_mplc_log_file, fieldnames=[' ',
                                                                    'SUPRA-CATEGORY:',
                                                                    'POPULATION',
                                                                    'CITIES',
                                                                    'SETTLEMENTS',
                                                                    'STREET NETWORK AREA',
                                                                    'ADDITIONAL BUILT-UP',
                                                                    'ANTHROPOGENIC IMPACT BUFFER',' ',
                                                                    'LUT01', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    'LUT02', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    'LUT03', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    'LUT04', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    'LUT05', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    'LUT06', ' ',
                                                                    'LUT07', ' ',
                                                                    'LUT08', ' ',
                                                                    'LUT09', ' ',
                                                                    'LUT10', ' ',
                                                                    'LUT11', ' ',
                                                                    'LUT12', ' ',
                                                                    'LUT13', ' ',
                                                                    'LUT14', ' ',
                                                                    'LUT15', ' ',
                                                                    'LUT16', ' ',
                                                                    'LUT17', ' ', ' ',' ',' ',' ',
                                                                    'LUT18', ' ',
                                                                    'LUT19', ' ',
                                                                    'only calculated if deforestation for demand in input biomass comes before deforestation due to land conversion', ' ',
                                                                    'FOREST CONVERSION (deforestation due to demand in land)', ' ',
                                                                    'LANDSCAPE MODELLING PROBABILITY / UNCERTAINTY',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    'LAND USE IN ' + status + ' RESTRICTED AREAS',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    'FOREST NET/GROSS DISTURBED/UNDISTURBED',
                                                                    ' ',
                                                                    ' ',
                                                                     ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',' ',
                                                                    ' ', ' ', ' ', ' ',
                                                                    'FOREST IMPACTED BY ANTHROPOGENIC FEATURES',
                                                                    ' ', ' ', ' ', ' ', ' ',
                                                                    'DEGRADATION (less AGB than last time step)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ',
                                                                    'REGENERATION (more or equal AGB to last time step)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ', ' ', ' ',
                                                                    'POTENTIAL MAXIMUM UNDISTURBED AGB', ' ',
                                                                    'INITIAL AGB SIMULATION START', ' ', ' ',
                                                                    'DEMAND IN INPUT BIOMASS IN Mg FOR THE TIME STEP (SUBSISTENCE)', ' ', ' ', ' ',
                                                                    'FINAL TOTAL AGB FOR THE TIME STEP', ' ', ' ', ' ', ' ', ' ',
                                                                    'FINAL TOTAL AGB AGROFORESTRY', ' ',
                                                                    'FINAL TOTAL AGB PLANTATION', ' ',
                                                                    'FINAL AGB DISTURBED FOREST FOR THE TIME STEP', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    'FINAL AGB UNDISTURBED FOREST FOR THE TIME STEP', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    # FOREST REMAINING WITHOUT DIRECT ANTHROPOGENIC IMPACT
                                                                    'GROSS FOREST', ' ', ' ', ' ',
                                                                    'NET FOREST', ' ', ' ', ' ',
                                                                    'GROSS MINUS NET FOREST', ' ', ' ', ' ',
                                                                    # FOREST 100 years
                                                                    'FORMER DISTURBED FOREST', ' ', ' ', ' ', ' ', ' ',
                                                                    'INITIAL UNDISTURBED FOREST', ' ', ' ', ' ', ' ', ' ',
                                                                    # FOREST HABITAT DISTURBED AND UNDISTURBED
                                                                    'DISTURBED HABITAT', ' ',
                                                                    'UNDISTURBED HABITAT', ' ',
                                                                    top_crops_data_lists_dictionary[1][
                                                                        'a_top_crop_name'], ' ',' ', ' ',
                                                                    top_crops_data_lists_dictionary[2][
                                                                        'a_top_crop_name'], ' ',' ', ' ',
                                                                    top_crops_data_lists_dictionary[3][
                                                                        'a_top_crop_name'], ' ',' ', ' ',
                                                                    top_crops_data_lists_dictionary[4][
                                                                        'a_top_crop_name'], ' ',' ', ' ',
                                                                    top_crops_data_lists_dictionary[5][
                                                                        'a_top_crop_name']
                                                                    ])
    LPB_mplc_writer.writeheader()

    # 3) Create the header for the categories (FIRST CHARACTER CAPITAL)
    LPB_mplc_writer = csv.writer(LPB_mplc_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_mplc_writer = csv.DictWriter(LPB_mplc_log_file, fieldnames=[' ',
                                                                    'CATEGORY:',
                                                                    'Population',
                                                                    'Cities (static)',
                                                                    'Settlements (dynamic)',
                                                                    'Street Network Area (static)',
                                                                    'Additional built-up (dynamic)',
                                                                    'Anthropogenic Impact Buffer based on cities, settlements and streets (deterministic)', ' ',
                                                                    Parameters.LUT01, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    Parameters.LUT02, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    Parameters.LUT03, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    Parameters.LUT04, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    Parameters.LUT05, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                    Parameters.LUT06, ' ',
                                                                    Parameters.LUT07, ' ',
                                                                    Parameters.LUT08, ' ',
                                                                    Parameters.LUT09, ' ',
                                                                    Parameters.LUT10, ' ',
                                                                    Parameters.LUT11, ' ',
                                                                    Parameters.LUT12, ' ',
                                                                    Parameters.LUT13, ' ',
                                                                    Parameters.LUT14, ' ',
                                                                    Parameters.LUT15, ' ',
                                                                    Parameters.LUT16, ' ',
                                                                    Parameters.LUT17, ' ', ' ',' ',' ',' ',
                                                                    Parameters.LUT18, ' ',
                                                                    Parameters.LUT19, ' ',
                                                                    # HIDDEN DEFORESTATION FOR INPUT BIOMASS
                                                                    'forest deforested for demand in input biomass maximum area based on probabilities > 0', ' ',
                                                                    # CONVERTED FOREST
                                                                    'forest converted to other land use types (not deforestation LUT17)', ' ',
                                                                    # PROBABILITY
                                                                    '0 %', ' ',
                                                                    '>0 - 20 %', ' ',
                                                                    '>20 - 40 %', ' ',
                                                                    '>40 - 60 %', ' ',
                                                                    '>60 - 80 %', ' ',
                                                                    '>80 - <100 %', ' ',
                                                                    '100 %', ' ',
                                                                    # LAND USE IN RESTRICTED AREAS
                                                                    'area', ' ',
                                                                    'total', ' ',
                                                                    'total new ', ' ',
                                                                    'total on former forest ', ' ',
                                                                    'disturbed forest ', ' ',
                                                                    'undisturbed forest ', ' ',
                                                                    # FOREST net gross disturbed undisturbed
                                                                    'gross forest mplc - includes user-defined forest types '+str(gross_forest_list), ' ',
                                                                    'net forest mplc - only disturbed and undisturbed in net forest areas', ' ',
                                                                    'gross disturbed forest mplc', ' ',
                                                                    'gross undisturbed forest mplc', ' ',
                                                                    'net disturbed forest mplc', ' ',
                                                                    'net undisturbed forest mplc', ' ',
                                                                    'gross minus net disturbed forest mplc', ' ',
                                                                    'gross minus net undisturbed forest mplc', ' ',
                                                                    # TRUE FOREST IMPACTED BY ANTHROPOGENIC FEATURES (LUT08)
                                                                    'gross forest mplc (disturbed+undisturbed)', ' ',
                                                                    'net forest mplc (disturbed+undisturbed)', ' ',
                                                                    'gross minus net forest mplc (disturbed+undisturbed)', ' ',
                                                                    # FOREST DEGRADATION/REGENERATION
                                                                    'degradation low net forest', ' ',
                                                                    'degradation low gross forest', ' ',
                                                                    'degradation low gross minus net forest', ' ',
                                                                    'degradation moderate net forest', ' ',
                                                                    'degradation moderate gross forest', ' ',
                                                                    'degradation moderate gross minus net forest', ' ',
                                                                    'degradation severe net forest', ' ',
                                                                    'degradation severe gross forest', ' ',
                                                                    'degradation severe gross minus net forest', ' ',
                                                                    'degradation absolute net forest', ' ',
                                                                    'degradation absolute net disturbed forest', ' ',
                                                                    'degradation absolute net undisturbed forest', ' ',
                                                                    'regeneration low net forest', ' ',
                                                                    'regeneration low gross forest', ' ',
                                                                    'regeneration low gross minus net forest', ' ',
                                                                    'regeneration medium net forest', ' ',
                                                                    'regeneration medium gross forest', ' ',
                                                                    'regeneration medium gross minus net forest', ' ',
                                                                    'regeneration high net forest', ' ',
                                                                    'regeneration high gross forest', ' ',
                                                                    'regeneration high gross minus net forest', ' ',
                                                                    'regeneration full net forest',' ',
                                                                    'regeneration full gross forest', ' ',
                                                                    'regeneration full disturbed net forest', ' ',
                                                                    'regeneration full disturbed gross forest', ' ',
                                                                    'regeneration full disturbed gross minus net forest', ' ',
                                                                    'regeneration full undisturbed net forest', ' ',
                                                                    'regeneration full undisturbed gross forest', ' ',
                                                                    'regeneration full undisturbed gross minus net forest', ' ',
                                                                    # FOREST AGB in Mg -> tC
                                                                    'what if all potential forest pixels would also have reached a climax stadium:',' ',
                                                                    'initial AGB for user-defined gross forest (including p.r.n. agroforestry and planatations)',
                                                                    'Mg Carbon is derived from Mg AGB with the IPCC conversion factor of: ' + str(Parameters.get_biomass_to_carbon_IPCC_conversion_factor()),
                                                                    ' ',
                                                                    'input biomass demand_timber per person: ' + str(AGB_demand_timber_in_Mg_per_person_per_year),
                                                                    'input biomass demand_fuelwood per person: ' + str(AGB_demand_fuelwood_in_Mg_per_person_per_year),
                                                                    'input biomass demand_charcoal per person: ' + str(AGB_demand_charcoal_in_Mg_per_person_per_year),
                                                                    'input biomass total demand_AGB per person: ' + str(AGB_total_demand_in_Mg_per_person_per_year),
                                                                    'gross forest', ' ',
                                                                    'net forest', ' ',
                                                                    'gross minus net forest', ' ',
                                                                    'gross agroforestry', ' ',
                                                                    'gross plantation', ' ',
                                                                    'gross disturbed forest', ' ',
                                                                    'net disturbed forest', ' ', ' ',
                                                                    'gross minus net disturbed forest', ' ', ' ',
                                                                    'gross undisturbed forest', ' ',
                                                                    'net undisturbed forest', ' ', ' ',
                                                                    'gross minus net undisturbed forest', ' ', ' ',
                                                                    # FOREST REMAINING WITHOUT DIRECT ANTHROPOGENIC IMPACT
                                                                    # gross forest
                                                                    'undisturbed forest', ' ',
                                                                    'disturbed forest', ' ',
                                                                    # net forest
                                                                    'undisturbed forest', ' ',
                                                                    'disturbed forest', ' ',
                                                                    # gross minus net
                                                                    'undisturbed forest', ' ',
                                                                    'disturbed forest', ' ',
                                                                    # FOREST 100 years without anthropogenic impact (potential primary stadium)
                                                                    'gross forest', ' ',
                                                                    'net forest', ' ',
                                                                    'gross minus net forest', ' ',
                                                                    'gross forest', ' ',
                                                                    'net forest', ' ',
                                                                    'gross minus net forest', ' ',
                                                                    # FOREST HABITAT DISTURBED AND UNDISTURBED
                                                                    'mplc disturbed forest fringe habitat', ' ',
                                                                    'mplc undisturbed forest habitat', ' ',
                                                                    # TOP CROPS YIELDS
                                                                    # top crop 1
                                                                    'mean yield per '+str(Parameters.get_pixel_size()) + str(': ') + str(
                                                                        top_crops_data_lists_dictionary[1][
                                                                            'a_top_crop_mean_yield'])
                                                                    + ', yield standard deviation: ' + str(
                                                                        top_crops_data_lists_dictionary[1][
                                                                            'a_top_crop_standard_deviation_yield'])
                                                                    + ', % of LUT acreage: ' + str(
                                                                        top_crops_data_lists_dictionary[1][
                                                                            'a_top_crop_percentage_of_acreage'])
                                                                    + ', source LUT: ' + str(
                                                                        top_crops_data_lists_dictionary[1][
                                                                            'a_top_crop_source_LUT']),
                                                                    ' ',' ', ' ',
                                                                    # top crop 1
                                                                    'mean yield per ' + str(
                                                                        Parameters.get_pixel_size()) + str(': ') + str(
                                                                        top_crops_data_lists_dictionary[2][
                                                                            'a_top_crop_mean_yield'])
                                                                    + ', yield standard deviation: ' + str(
                                                                        top_crops_data_lists_dictionary[2][
                                                                            'a_top_crop_standard_deviation_yield'])
                                                                    + ', % of LUT acreage: ' + str(
                                                                        top_crops_data_lists_dictionary[2][
                                                                            'a_top_crop_percentage_of_acreage'])
                                                                    + ', source LUT: ' + str(
                                                                        top_crops_data_lists_dictionary[2][
                                                                            'a_top_crop_source_LUT']),
                                                                    ' ',' ', ' ',
                                                                    # top crop 1
                                                                    'mean yield per ' + str(
                                                                        Parameters.get_pixel_size()) + str(': ') + str(
                                                                        top_crops_data_lists_dictionary[3][
                                                                            'a_top_crop_mean_yield'])
                                                                    + ', yield standard deviation: ' + str(
                                                                        top_crops_data_lists_dictionary[3][
                                                                            'a_top_crop_standard_deviation_yield'])
                                                                    + ', % of LUT acreage: ' + str(
                                                                        top_crops_data_lists_dictionary[3][
                                                                            'a_top_crop_percentage_of_acreage'])
                                                                    + ', source LUT: ' + str(
                                                                        top_crops_data_lists_dictionary[3][
                                                                            'a_top_crop_source_LUT']),
                                                                    ' ',' ', ' ',
                                                                    # top crop 1
                                                                    'mean yield per ' + str(
                                                                        Parameters.get_pixel_size()) + str(': ') + str(
                                                                        top_crops_data_lists_dictionary[4][
                                                                            'a_top_crop_mean_yield'])
                                                                    + ', yield standard deviation: ' + str(
                                                                        top_crops_data_lists_dictionary[4][
                                                                            'a_top_crop_standard_deviation_yield'])
                                                                    + ', % of LUT acreage: ' + str(
                                                                        top_crops_data_lists_dictionary[4][
                                                                            'a_top_crop_percentage_of_acreage'])
                                                                    + ', source LUT: ' + str(
                                                                        top_crops_data_lists_dictionary[4][
                                                                            'a_top_crop_source_LUT']),
                                                                    ' ',' ', ' ',
                                                                    # top crop 5
                                                                    'mean yield per ' + str(
                                                                        Parameters.get_pixel_size()) + str(': ') + str(
                                                                        top_crops_data_lists_dictionary[5][
                                                                            'a_top_crop_mean_yield'])
                                                                    + ', yield standard deviation: ' + str(
                                                                        top_crops_data_lists_dictionary[5][
                                                                            'a_top_crop_standard_deviation_yield'])
                                                                    + ', % of LUT acreage: ' + str(
                                                                        top_crops_data_lists_dictionary[5][
                                                                            'a_top_crop_percentage_of_acreage'])
                                                                    + ', source LUT: ' + str(
                                                                        top_crops_data_lists_dictionary[5][
                                                                            'a_top_crop_source_LUT'])
                                                                    ])
    LPB_mplc_writer.writeheader()

    # 4) Create the header for the SINGULAR SUB-CATEGORIES (all lower case except time step and year for orientation)
    LPB_mplc_writer = csv.writer(LPB_mplc_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_mplc_writer = csv.DictWriter(LPB_mplc_log_file, fieldnames=['TIME STEP',
                                                                    'YEAR',
                                                                    'population',
                                                                    # anthropogenic features
                                                                    'pixels (singular points)',
                                                                    'pixels (singular points)',
                                                                    'pixels',
                                                                    'pixels',
                                                                    # anthropogenic impact buffer
                                                                    'pixel', '%',
                                                                    # LUT01
                                                                    'maximum demand',
                                                                    'allocated','%',
                                                                    'difficult terrain','%',
                                                                    'accumulated in ' + status + ' restricted areas','%',
                                                                    'new in ' + status + ' restricted areas',
                                                                    'new on former forest pixel in ' + status + ' restricted areas',
                                                                    'locally allocated','%',
                                                                    'regional excess','%',
                                                                    'unallocated - built up is a final land use type and is not subject to contraction',
                                                                    # LUT02
                                                                    'demand',
                                                                    'allocated','%',
                                                                    'difficult terrain','%',
                                                                    'accumulated in ' + status + ' restricted areas','%',
                                                                    'new in ' + status + ' restricted areas',
                                                                    'new on former forest pixel in ' + status + ' restricted areas',
                                                                    'locally allocated','%',
                                                                    'regional excess','%',
                                                                    'unallocated',
                                                                    # LUT03
                                                                    'demand',
                                                                    'allocated','%',
                                                                    'difficult terrain','%',
                                                                    'accumulated in ' + status + ' restricted areas','%',
                                                                    'new in ' + status + ' restricted areas',
                                                                    'new on former forest pixel in ' + status + ' restricted areas',
                                                                    'locally allocated','%',
                                                                    'regional excess','%',
                                                                    'unallocated',
                                                                    # LUT04
                                                                    'demand',
                                                                    'allocated','%',
                                                                    'difficult terrain','%',
                                                                    'accumulated in ' + status + ' restricted areas','%',
                                                                    'new in ' + status + ' restricted areas',
                                                                    'new on former forest pixel in ' + status + ' restricted areas',
                                                                    'locally allocated','%',
                                                                    'regional excess','%',
                                                                    'unallocated',
                                                                    # LUT05
                                                                    'demand',
                                                                    'allocated','%',
                                                                    'difficult terrain','%',
                                                                    'accumulated in ' + status + ' restricted areas','%',
                                                                    'new in ' + status + ' restricted areas',
                                                                    'new on former forest pixel in ' + status + ' restricted areas',
                                                                    'locally allocated','%',
                                                                    'regional excess','%',
                                                                    'unallocated - plantations demand from harvested plantations is met in the next year',
                                                                    # LUT06
                                                                    'allocated','%',
                                                                    # LUT07
                                                                    'allocated','%',
                                                                    # LUT08
                                                                    'allocated','%',
                                                                    # LUT09
                                                                    'allocated','%',
                                                                    # LUT10
                                                                    'allocated','%',
                                                                    # LUT11
                                                                    'allocated','%',
                                                                    # LUT12
                                                                    'allocated','%',
                                                                    # LUT13
                                                                    'allocated','%',
                                                                    # LUT14
                                                                    'allocated','%',
                                                                    # LUT15
                                                                    'allocated','%',
                                                                    # LUT16
                                                                    'allocated','%',
                                                                    # LUT17
                                                                    'demand AGB in Mg',
                                                                    'minimum area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'mean area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'maximum area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'allocated','%',
                                                                    # LUT18
                                                                    'allocated','%',
                                                                    # LUT19
                                                                    'allocated', '%',
                                                                    # HIDDEN DEFORESTATION FOR DEMAND IN INPUT BIOMASS
                                                                    'area', ' %',
                                                                    # CONVERTED FOREST
                                                                    'area', ' % ',
                                                                    # PROBABILITY
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    'pixel', '%',
                                                                    # LAND USE IN RESTRICTED AREAS:
                                                                    status + ' restricted areas area', '%',
                                                                    'total of active land use in ' + status + ' restricted areas', '% of ' + status + ' restricted areas',
                                                                    'total of new active land use in ' + status + ' restricted areas', '% of ' + status + ' restricted areas',
                                                                    'total of new active land use on former forest cells in ' + status + ' restricted areas', ' % of ' + status + ' restricted areas',
                                                                    'total of disturbed forest in ' + status + ' restricted areas', ' % of ' + status + ' restricted areas',
                                                                    'total of undisturbed forest in ' + status + ' restricted areas',' % of ' + status + ' restricted areas',
                                                                    # FOREST net gross disturbed undisturbed
                                                                    'area','%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    # TRUE FOREST IMPACTED BY ANTHROPOGENIC FEATURES (LUT08)
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    # FOREST DEGRADATION/REGENERATION
                                                                    # 1) degradation
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    # 2) regeneration
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    'area', '%',
                                                                    # FOREST AGB in Mg -> tC
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC', '% of potential maximum undisturbed AGB',
                                                                    'population total demand_timber', 'population total demand_fuelwood', 'population total demand_charcoal', 'population total demand_AGB',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC', '% of gross disturbed forest AGB',
                                                                    'AGB maptotal', 'MgC', '% of gross disturbed forest AGB',
                                                                    'AGB maptotal', 'MgC',
                                                                    'AGB maptotal', 'MgC', '% of gross undisturbed forest AGB',
                                                                    'AGB maptotal', 'MgC', '% of gross undisturbed forest AGB',
                                                                    
                                                                    # FOREST REMAINING WITHOUT DIRECT ANTHROPOGENIC IMPACT
                                                                    # gross forest
                                                                    # undisturbed
                                                                    'area', '%',
                                                                     # disturbed
                                                                    'area', '%',
                                                                     # net forest
                                                                     # undisturbed
                                                                    'area', '%',
                                                                    # disturbed
                                                                    'area', '%',
                                                                     # gross minus net
                                                                     # undisturbed
                                                                    'area', '%',
                                                                    # disturbed
                                                                    'area', '%',

                                                                    # FOREST 100 years without anthropogenic impact (potential primary stadium)
                                                                    # former disturbed forest
                                                                    'area', '%',
                                                                    'area', ' % ',
                                                                    'area', ' % ',
                                                                    # initial undisturbed forest
                                                                    'area', ' % ',
                                                                    'area', ' % ',
                                                                    'area', ' % ',

                                                                    # FOREST HABITAT DISTURBED AND UNDISTURBED
                                                                    'area', ' % ',
                                                                    'area', ' % ',

                                                                    # TOP CROPS YIELDS
                                                                    # top crop 1
                                                                    'share in cultivation area of the source LUT in ' + str(Parameters.get_pixel_size()),
                                                                    'regional yield minimum',
                                                                    'regional yield mean',
                                                                    'regional yield maximum',
                                                                    # top crop 2
                                                                    'share in cultivation area of the source LUT in ' + str(Parameters.get_pixel_size()),
                                                                    'regional yield minimum',
                                                                    'regional yield mean',
                                                                    'regional yield maximum',
                                                                    # top crop 3
                                                                    'share in cultivation area of the source LUT in ' + str(Parameters.get_pixel_size()),
                                                                    'regional yield minimum',
                                                                    'regional yield mean',
                                                                    'regional yield maximum',
                                                                    # top crop 4
                                                                    'share in cultivation area of the source LUT in ' + str(Parameters.get_pixel_size()),
                                                                    'regional yield minimum',
                                                                    'regional yield mean',
                                                                    'regional yield maximum',
                                                                    # top crop 5
                                                                    'share in cultivation area of the source LUT in ' + str(Parameters.get_pixel_size()),
                                                                    'regional yield minimum',
                                                                    'regional yield mean',
                                                                    'regional yield maximum',
                                                                    ])
    LPB_mplc_writer.writeheader()