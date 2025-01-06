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

list_of_LUTs_for_definition_of_potential_restricted_areas = Parameters.get_list_of_LUTs_for_definition_of_potential_restricted_areas()

# open the CSV for LPB-mplc
with open((os.path.join(Filepaths.folder_RAP_CSVs, 'LPB-RAP_log-file.csv')),
          'w', newline='') as LPB_RAP_log_file:
    LPB_RAP_writer = csv.writer(LPB_RAP_log_file, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Create a title for the CSV
    LPB_RAP_log_file_title = ['LPB-RAP log file', Parameters.get_country(), Parameters.get_region(), Parameters.get_model_baseline_scenario(),
                               Parameters.get_model_scenario() + ' scenario']
    LPB_RAP_writer.writerow(LPB_RAP_log_file_title)

    # 1) Create the header for the ultra- categories
    LPB_RAP_writer = csv.writer(LPB_RAP_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_RAP_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=[' ',
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
                                                                    ' ', ' ', ' ', ' ', ' ', ' ',' ',' ',' ',' ',' ',

                                                                  # RAP addition 45
                                                                  ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                  ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                  ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                  ' ', ' ', ' ', ' ', ' ', ' ',' ', ' ',
                                                                  'NEW COMBINED RESTORATION AREA POTENTIAL LAND USE TYPES ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                  'RAP TOTAL (new potentials for FLR)', ' ',
                                                                  # RAP - TARGETED RAP FOREST ACHIEVED?
                                                                  'RAP - targeted net forest achievable? ', ' ', ' ', ' ', ' ',' ',
                                                                  # RAP potential minimum restoration / mitigation
                                                                  'RAP - minimum restoration potential / mitigation', ' ',' ', ' ',
                                                                  # RAP - potential for additional restricted areas
                                                                  'RAP - potential for short-term/long-term additional restricted areas',
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
                                                                    'RAP potential AGB -> Carbon',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    'FOREST REMAINING WITHOUT DIRECT ANTHROPOGENIC IMPACT (only disturbed and undisturbed)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ',
                                                                    'FOREST 100 years without anthropogenic impact (potential primary stadium)',
                                                                    ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                                                    ' ',
                                                                    'FOREST HABITAT DISTURBED AND UNDISTURBED', ' ',' ', ' ',
                                                                    '5 TOP CROPS [SELECTED PER COUNTRY] POTENTIAL YIELDS in Mg'
                                                                    ])
    LPB_RAP_writer.writeheader()

    # 2) Create the header for the supra - categories (ALL CAPITAL)
    LPB_RAP_writer = csv.writer(LPB_RAP_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_RAP_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=[' ',
                                                                    'SUPRA-CATEGORY:',
                                                                    'POPULATION',
                                                                    'CITIES',
                                                                    'SETTLEMENTS',
                                                                    'STREET NETWORK AREA',
                                                                    'ADDITIONAL BUILT-UP',
                                                                    'ANTHROPOGENIC IMPACT BUFFER',' ',
                                                                    'LUT01', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ','LUT01-RAP', ' ',
                                                                    'LUT02', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ','LUT02-RAP',
                                                                    'LUT03', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ','LUT03-RAP',
                                                                    'LUT04', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ','LUT04-RAP', ' ',
                                                                    'LUT05', ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ','LUT05-RAP', ' ',
                                                                    'LUT06', ' ','LUT06-RAP', ' ',
                                                                    'LUT07', ' ','LUT07-RAP', ' ',
                                                                    'LUT08', ' ','LUT08-RAP', ' ',
                                                                    'LUT09', ' ','LUT09-RAP', ' ',
                                                                    'LUT10', ' ','LUT10-RAP', ' ',
                                                                    'LUT11', ' ','LUT11-RAP', ' ',
                                                                    'LUT12', ' ','LUT12-RAP', ' ',
                                                                    'LUT13', ' ','LUT13-RAP', ' ',
                                                                    'LUT14', ' ','LUT14-RAP', ' ',
                                                                    'LUT15', ' ','LUT15-RAP', ' ',
                                                                    'LUT16', ' ','LUT16-RAP', ' ',
                                                                    'LUT17', ' ', ' ',' ',' ',' ','LUT17-RAP', ' ',
                                                                    'LUT18', ' ','LUT18-RAP', ' ',
                                                                    'LUT19', ' ', 'LUT19-RAP', ' ',
                                                                  'LUT21-RAP', ' ',
                                                                  'LUT22-RAP', ' ',
                                                                  'LUT23-RAP', ' ',
                                                                  'LUT24-RAP', ' ',
                                                                  'LUT25-RAP', ' ',
                                                                  # RAP total
                                                                  'combined LUTs 21, 22, 23, 24, 25', ' ',
                                                                  # RAP - TARGETED RAP FOREST ACHIEVED?
                                                                  'RAP - targeted net forest achievable?', ' ', ' ', ' ',' ',' ',
                                                                  # RAP potential minimum restoration / mitigation
                                                                  'calculated based on the peak land use mask resp. entire landscape after population peak',
                                                                  ' ', ' ', ' ',
                                                                  # RAP - potential for additional restricted areas
                                                                  'calculated based on the population peak land use mask',
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
                                                                  # RAP AGB
                                                                  'what if RAP potentials would be fulfilled in the mplc landscape?',
                                                                  ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
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
    LPB_RAP_writer.writeheader()

    # 3) Create the header for the categories (FIRST CHARACTER CAPITAL)
    LPB_RAP_writer = csv.writer(LPB_RAP_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_RAP_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=[' ',
                                                                    'CATEGORY:',
                                                                    'Population',
                                                                    'Cities (static)',
                                                                    'Settlements (dynamic)',
                                                                    'Street Network Area (static)',
                                                                    'Additional built-up (dynamic)',
                                                                    'Anthropogenic Impact Buffer based on cities, settlements and streets (deterministic)', ' ',
                                                                    Parameters.LUT01, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                  # RAP
                                                                    'stays as is (anthropogenic needed space) ', ' ',
                                                                    Parameters.LUT02, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                  # RAP
                                                                    'RAP-LUT21 source LUT',
                                                                    Parameters.LUT03, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                  # RAP
                                                                    'RAP-LUT21 source LUT',
                                                                    Parameters.LUT04, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                  # RAP
                                                                    'stays as is (target already achieved)', ' ',
                                                                    Parameters.LUT05, ' ', ' ', ' ', ' ', ' ',' ', ' ',' ', ' ',' ', ' ',' ', ' ',
                                                                  # RAP
                                                                    'stays as is (anthropogenic needed space) ', ' ',
                                                                    Parameters.LUT06, ' ','FLR-RAP-LUTs 22, 23, 24 source LUT on forest biome pixels', ' ',
                                                                    Parameters.LUT07, ' ','FLR-RAP-LUTs 22, 23, 24 source LUT on forest biome pixels', ' ',
                                                                    Parameters.LUT08, ' ','FLR-RAP-LUT24 source LUT', ' ',
                                                                    Parameters.LUT09, ' ','stays as is (target already achieved) ', ' ',
                                                                    Parameters.LUT10, ' ','other ecosystem - stays as is (can achieve more area in LUT24) ', ' ',
                                                                    Parameters.LUT11, ' ','other ecosystem - stays as is (can achieve more area in LUT24) ', ' ',
                                                                    Parameters.LUT12, ' ','stays as is (can achieve more area in LUT24 by user input)', ' ',
                                                                    Parameters.LUT13, ' ','stays as is (no information) ', ' ',
                                                                    Parameters.LUT14, ' ','FLR-RAP-LUTs 22, 23, 24 source LUT on forest biome pixels',' ',
                                                                    Parameters.LUT15, ' ','FLR-RAP-LUTs 22, 23, 24 source LUT on forest biome pixels',' ',
                                                                    Parameters.LUT16, ' ','FLR-RAP-LUTs 22, 23, 24 source LUT on forest biome pixels',' ',
                                                                    Parameters.LUT17, ' ', ' ',' ',' ',' ','FLR-RAP-LUT23 source LUT on forest biome pixels', ' ',
                                                                    Parameters.LUT18, ' ','stays as is, since it depicts demand ', ' ',
                                                                    Parameters.LUT19, ' ','stays as is, no modeling yet', ' ',
                                                                  # RAP
                                                                  Parameters.LUT21, ' ',
                                                                  Parameters.LUT22, ' ',
                                                                  Parameters.LUT23, ' ',
                                                                  Parameters.LUT24, ' ',
                                                                  Parameters.LUT25, ' ',
                                                                  # RAP TOTAL
                                                                  'FLR-RAP in further agroforestry, plantations, reforestation, other ecosystems and degraded forest', ' ',
                                                                  # RAP - TARGETED RAP FOREST ACHIEVED?
                                                                  'RAP - targeted net forest achievable?', ' ', ' ', ' ',' ',' ',
                                                                  # RAP potential minimum restoration / mitigation
                                                                  'RAP-LUT22 minimum',
                                                                  'RAP-LUT23 minimum',
                                                                  'RAP-LUT24 minimum',
                                                                  'RAP-LUT25 minimum',
                                                                  # RAP - potential for additional restricted areas
                                                                  'based on the LUTs: ' + str(list_of_LUTs_for_definition_of_potential_restricted_areas),
                                                                    # HIDDEN DEFORESTATION FOR INPUT BIOMASS
                                                                    'forest deforested for demand in input biomass probabilistic area based on probabilities > 0', ' ',
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
                                                                  # RAP AGB
                                                                  'RAP AGB mean agroforestry (based on inital AGB map and mplc landscape [LUT4])', 'RAP AGB mean agroforestry maptotal', 'RAP AGB mean agroforestry Carbon',
                                                                  'RAP AGB mean plantation (based on inital AGB map and mplc landscape [LUT8])', 'RAP AGB mean plantation maptotal', 'RAP AGB mean plantation Carbon ',
                                                                  'RAP AGB mean reforestation (based on inital AGB map and mplc landscape [LUT9])', 'RAP AGB mean reforestation maptotal ', 'RAP AGB mean reforestation Carbon ',
                                                                  'RAP AGB maptotal (mplc+RAP) ', 'RAP AGB Carbon (mplc+RAP) ',
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
    LPB_RAP_writer.writeheader()

    # 4) Create the header for the SINGULAR SUB-CATEGORIES (all lower case except time step and year for orientation)
    LPB_RAP_writer = csv.writer(LPB_RAP_log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    LPB_RAP_writer = csv.DictWriter(LPB_RAP_log_file, fieldnames=['TIME STEP',
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
                                                                  # RAP
                                                                  'allocated', '%',
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
                                                                  # RAP
                                                                  'transformed',
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
                                                                  # RAP
                                                                  'transformed',
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
                                                                  # RAP
                                                                  'allocated', '%',
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
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT06
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels', '%',
                                                                    # LUT07
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels', '%',
                                                                    # LUT08
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels', '%',
                                                                    # LUT09
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT10
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT11
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT12
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT13
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                    # LUT14
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels','%',
                                                                    # LUT15
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels','%',
                                                                    # LUT16
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels','%',
                                                                    # LUT17
                                                                    'demand AGB in Mg',
                                                                    'minimum area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'mean area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'maximum area allocated in LPB-basic final environment_map for demand in input biomass',
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'remaining pixels','%',
                                                                    # LUT18
                                                                    'allocated','%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # LUT19
                                                                  'allocated', '%',
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # RAP LUTS
                                                                  # LUT21
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # LUT22
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # LUT23
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # LUT 24
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # LUT 25
                                                                  # RAP
                                                                  'allocated', '%',
                                                                  # RAP total
                                                                  'summarized', '%',
                                                                  # RAP - TARGETED RAP FOREST ACHIEVED?
                                                                  'targeted total net forest area', '%', 'total possible net forest including LUT23', 'possible net forest percentage of landscape', 'area achieved (+) / not achieved (-) by ' + str(Parameters.get_pixel_size()),' target achieved?',
                                                                  # RAP potential minimum restoration / mitigation
                                                                  'area',
                                                                  'area',
                                                                  'area',
                                                                  'area',
                                                                  # RAP - potential for additional restricted areas
                                                                  'area',
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

                                                                  # RAP AGB
                                                                  'AGB Mg',
                                                                  'AGB Mg',
                                                                  'MgC',
                                                                  'AGB Mg',
                                                                  'AGB Mg',
                                                                  'MgC',
                                                                  'AGB Mg',
                                                                  'AGB Mg',
                                                                  'MgC',
                                                                  'AGB Mg',
                                                                  'MgC',
                                                                    
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
    LPB_RAP_writer.writeheader()