import numpy as np
numpy_rng = None

"""LAFORET-PLUC-BE-RAP/OC/SFM - PARAMETERS
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK), 
LPB-RAP (SH) model stage 1 2021/Q2 - 2023/Q3
LPB-RAP (SH) model stage 2 2022/3 - 2024/Q1
model stage 3 preparations 2022/11-12 (re-implementation of demand/yield in conjunction with footprint)
LPB-OC (ML) model stage 3 2022/11 - 2023/2024
LPB-SFM (DK) model stage 3 tentative in 2024
(Re-)written according to PEP 8 descriptive_snake_style and modified original file.
Based on:

Land use change model, designed for Mozambique
Judith Verstegen, 2011-01-11
Parameters.py https://github.com/JudithVerstegen/PLUC_Mozambique/blob/master/model/LU_Moz.py"""

# Changes to PLUC for LPB-RAP/OC/SFM model stage 1 to 3 made by:
# JV: original commented/out-commented by Judith Verstegen
# SH: commented/out-commented by Sonja Holler
# ML: commented/out-commented by Melvin Lippe
# DK: commented/out-commented by Daniel Kuebler


#######################################
# DK & SH:
# For model development model stage 2 (RAP) and 3(OC/SFM) in parallel choose here which configuration to run, all other parameters stay the same.
# Just set SETUP_DICT = experimental_setups['yield_units'] or SETUP_DICT = experimental_setups['footprint'].

# # define experimental setups
experimental_setups = {
    'footprint':
        {
            'overall_method': 'footprint',
            'internal_or_external': 'external',
            # next line only required if above is 'external'
            'list_columns_for_tss': ['smallholder_share', 2, 3, 4, 5,
                                     'regional_AGB_demand_per_population_total']

        },
    'yield_units':
        {
            'overall_method': 'yield_units',
            'deterministic_or_stochastic': 'stochastic',
            'list_columns_for_tss': [2, 3, 4, 5, 'regional_AGB_demand_per_population_total', 'regional_smallholder_share_in_percent'],  # maximum choices: [2, 3, 4, 5, 'regional_AGB_demand_per_population_total', 'regional_smallholder_share_in_percent']
            'LUTs_with_demand_and_yield': [2, 3, 4]  # maximum choices: [2, 3, 4]
        }
}
# setup to use
SETUP_DICT = experimental_setups['footprint']



#######################################

# TODO - CHECK ALL PARAMETERS MARKED TODO BEFORE MODEL RUN FOR THE REGION
# Structure is:
# 1) TECHNICAL OPTIONS
# 2) LPB - PARAMETERS
# 2.1) Info on model basics
# 2.2) Info on simulation choices => LPB/PLUC adapter to simulate partially with demand/yield instead of footprint
# 2.3) Info on study area(s) (LAFORET - descriptive)
# 2.4) Info on regional parameters 1 (LAFORET input - primary data)
# 2.5) Further parameters
# 2.6) Info on stochastic parameters
# 2.7) PLUC/LPB dictionaries, lists and values to simulate land use patterns
# 3) RAP - PARAMETERS
# 4) OC - PARAMETERS
# 5) SFM - PARAMETERS

#######################################
#region 1) T E C H N I C A L  O P T I O N S

#######################################
# DK: LPB alternation for LPB-SFM

def get_debug_flag():
    """Usage for model development = True. Set to False if no printing and reporting is required."""
    debug_flag = True
    return debug_flag


#######################################
# SH: LPB alternation
# TODO
def get_random_seed():
    """For coding, debugging and submission use 1 to always produce the same results. Otherwise set to 0 to use the coincidence elemnt of stoachstic funtions."""
    random_seed = 1
    return random_seed


def get_rng():
    """ Returns NumPy random number generator """
    seed = None if get_random_seed() == 0 else get_random_seed()

    global numpy_rng
    if numpy_rng == None:
        numpy_rng = np.random.default_rng(seed)
    return numpy_rng


# TODO
def get_number_of_threads_to_be_used():
    """ To make the model faster increase the number of worker threads (PCRaster automatically tries to use all cores available).
    Increase can be seen with 2 to 4 threads. Otherwise set to 1"""

    number_of_threads_to_be_used = 4
    return number_of_threads_to_be_used


def get_LPB_basic_probabilistic_output_options():
    """Decide on one or multiple output options for the probabilistic maps depending on you hard drive space with True and False.
    If you put down false the according function in LPB-mplc is disabled (decrease in analytic output).
    Check the excel file TB_Calculation_LPB-RAP_Esmeraldas to see how much TB is produced."""

    probabilistic_output_options_dictionary = {
        'deforested_net_forest_map': True,  # needed in mplc to calculate probabilistic distribution (+ GIF)
        'conflict_maps': True,  # needed in mplc to calculate probabilistic distribution (+ GIF)
        'AGB_map': True,  # needed in mplc and RAP for evaluation and calculation
        'net_forest_map': True,  # needed in mplc and RAP for evaluation and calculation - essential for RAP
        'degradation_regeneration_maps': True,  # needed in mplc to calculate probabilistic distribution (+ GIF)
        'yield_maps': False,  # model stage 3 additition - only produced in the yield_units approach for the user-defined selected agricultural LUTs, basis for OC
        'succession_age_map': True # optional if you want to have the GIF for your user-defined succession to undisturbed forest
    }
    return probabilistic_output_options_dictionary

#endregion

#######################################
## 2) L P B  -  P A R A M E T E R S ##


# SH: LPB alternation
"""Define land use types (LUTs) once for console and csv output purposes"""
LUT01 = 'built-up'  # summarizes all kinds of soil compacting alternations which are not agriculture based
LUT02 = 'cropland-annual'  # initial distribution is based on MAE 2018 agriculture coastal patch (this might be a 1% error in the map) and Copernicus
LUT03 = 'pasture'  # only allocated by demand
LUT04 = 'agroforestry'  # only allocated by demand
LUT05 = 'plantation'  # TMF based, might be an overestimation compared to the MAE 2018 map
LUT06 = 'herbaceous vegetation'  # Copernicus LUT
LUT07 = 'shrubs'  # Copernicus LUT
LUT08 = 'disturbed forest'  # Copernicus LUT aggregated forest
LUT09 = 'undisturbed forest'  # TMF based
LUT10 = 'moss, lichen, bare, sparse vegetation'  # Copernicus LUT merged
LUT11 = 'herbaceous wetland'  # Copernicus LUT
LUT12 = 'water'  # Copernicus LUT aggregated
LUT13 = 'no input'  # Copernicus LUT
LUT14 = 'cropland-annual - - abandoned'  # only simulated
LUT15 = 'pasture - - abandoned'  # only simulated
LUT16 = 'agroforestry - - abandoned'  # only simulated
LUT17 = 'net forest - - deforested'  # only simulated
LUT18 = 'plantation - - harvested'  # only simulated


###############################################################################
### 2.1) Info on model basics ###

# SH: LPB alternation
# TODO (change for policy scenario)
def get_presimulation_correction_step_needed():
    """Set this parameter to 'True' if the hybrid input map needs to get adjusted to land use information prior to the Monte Carlo Simulation,
    'False' if not required or if you run the no conservation scenario."""

    correction_needed = True
    return correction_needed


# if the above variable is set to true define the LUTs that shall not be altered:
# TODO
def get_correction_step_list_of_immutable_LUTs():
    """Non-ambiguous types like 10, 11 should be excluded, others are case specific approximations:"""

    correction_step_list_of_immutable_LUTs = [1,5,6,7,8,9,10,11,12,13] # in this case the agricultural demands are only allowed to be allocated on the random agriculture area
    return correction_step_list_of_immutable_LUTs


# SH: LPB alternation
# TODO
def get_model_version():
    """Return the model version for the chosen outputs:

      'LPB-basic' calculates the deterministic and probabilistic scenario development (restoration not implemented)

      'LPB-mplc' calculates the deterministic and  probabilistic scenario development (restoration not implemented) plus aggregation to the most probable landscape configuration

      'LPB-RAP' calculates additionally the Restoration Area Potential (RAP) for the whole landscape for each time step (restoration not implemented dynamically, but the potential for each calculated LPB timestep given)

      'LPB-SFM' calculates the potential development if Sustainable Forest Management (SFM) would be implemented"""

    model_version = 'LPB-RAP'
    return model_version

#TODO Sonja: further model versions when clarified (RAP+) OC with Melvin

# SH: LPB alternation
# TODO
def get_model_baseline_scenario():
    """Note which baseline scenario is applied - for print results (population and climate input maps basis)"""
    model_baseline_scenario = 'SSP2-4.5'
    return model_baseline_scenario


# SH: LPB alternation
# TODO (change for policy scenario)
def get_model_scenario():
    """ Return the forest policy guideline scenario chosen for this model run: LPB model stage 1 can be run for

    'weak_conservation' scenario, which delivers the reference scenario, by use of static restricted areas, which will be used if needed,
    or
    'enforced_conservation' if you provided a dataset of excluded areas congruent with restricted areas,
    or
    'no_conservation' scenario, which delivers a simulation under repeal of all restricted areas starting with weak or enforced conservation 2025 (default) input"""

    model_scenario = 'weak_conservation'
    return model_scenario


# SH: LPB alternation
# TODO (change for policy scenario)
def get_initial_simulation_year():
    """ SH: Return the initial simulation year: 2018 for weak and enforced conservation scenarios, e.g. 2025 for the no conservation scenario"""

    initial_simulation_year = 2018
    return initial_simulation_year


# SH: LPB alternation
# TODO (change for policy scenario)
def get_worst_case_scenario_decision():
    """Choose True or False, if True, needed input will be produced by LPB-basic and LPB-mplc.

    Set to False if you run the no conservation scenario."""

    worst_case_scenario_planned = True
    return worst_case_scenario_planned


# SH: LPB alternation
# TODO
def get_the_initial_simulation_year_for_the_worst_case_scenario():
    """ For the year defined here LPB-basic and LPB-mplc in the weak or enforced conservation scenario run will file a new "initial" folder
    to be implemented in the worst case scenario run in "inputs"."""

    initial_simulation_year_for_the_worst_case_scenario = 2025
    return initial_simulation_year_for_the_worst_case_scenario


# TODO (change for policy scenario)
def get_number_of_time_steps():
    """JV: Return number of time steps.

    e.g. 2005 to 2030 is 26 time steps."""

    time_steps = 83  ##SH: (2018 standard 83, 2025 -> 76)
    return time_steps


# TODO
def get_number_of_samples():
    """ JV: Return number of Monte Carlo samples required.

    If Monte Carlo is not required fill in 1.

    SH: IN LPB the number of samples goes hand in hand with stratified sampling of distances to depict land use patterns.

    Please note the distances used (mean, min, max) in the function: get_regional_distance_values_for_agricultural_land_use_dictionary"""

    """For the footprint approach: 
    Option A) if set to None the required sample number for pseudo random sampling based on cell-edge-length will be calculated model internally.
    Option B) if set to 1 (no MC) the mean values for distance will be used
    Option C) set to a number you want to simulate, distances will be calculated accordingly"""
    samples = None  ##SH: 3 for testing code (most probable landscape configuration), Simulate finally with None
    return samples


# SH: LPB alternation
# TODO
def get_pixel_size():
    """SH: note the unit of a singular pixel, e.g. 'ha' or 'km2'. """

    area_unit = 'ha'
    return area_unit


# SH: LPB alternation
# TODO
def get_cell_length_in_m():
    """SH: note the cell edge length for one edge."""

    cell_length_in_m = 100  # meter
    return cell_length_in_m


# JV: original PLUC
# not used in LPB-RAP with the footprint approach on the ha scale
def get_conversion_unit():
    """ JV: Return conversion unit for max yield unit to square meters.

    e.g. when max yield in ton/ha fill in 10000."""

    to_square_meters = 10000
    return to_square_meters


# SH: LPB alternation
# TODO
def get_total_number_of_land_use_types():
    """The total number of land use types is used for console output and for the calculation of the MC average dictionary"""
    total_number_of_land_use_types = 18
    return total_number_of_land_use_types


## SH: LPB alternation
# HINT the land use list is set once globally for all LaForeT regions due to Copernicus input classes
# TODO
def get_active_land_use_types_list():
    # SH: ALLOCATION ORDER
    """ JV: Return list of land use types in ORDER of 'who gets to choose first'.

    SH: SSP2-4.5 Assumptions:
      1 = LUT01 built-up needs to come first in a moderate worst case scenario and a 100m resolution
      2 = LUT02 cropland-annual will be allocated next using prime locations
      3 = LUT03 pasture and 4 = LUT04 agroforestry complete the smallholder local landscape configuration
      5 = LUT05 plantation depict economic interest but not subsistence, therefore they are coming last in the demand based allocation order """

    active_land_use_types_list = [1, 2, 3, 4, 5]  # the 5 active LUTs are already in the right allocation order
    return active_land_use_types_list


## SH: LPB alternation - forest types list instead of forest number - not needed until now
# TODO
def get_gross_forest_LUTs_list():
    """ SH: List of forest types (gross forest) used in the model as land use types."""

    # 4 = agroforestry
    # 5 = plantation IF TIMBER
    # 8 = disturbed forest
    # 9 = undisturbed forest

    forest_types_list = [4, 8, 9]  # this depicts gross forest in LPB (here species on plantations are oil palm, i.e. not a forest type)
    return forest_types_list


###############################################################################
### 2.2) Info on simulation choices ###

# SH: LPB alternation
# TODO
def get_streets_input_decision_for_calculation_of_built_up():
    """ If streets are to be used as input the amount of built-up is naturally drastically higher, depicting urbanization patterns as a result.
    On the other hand this might be an approximation of true built-up coverage in the landscape.
    Decide if streets should be used as an input into the rule of three built up calculation with True or False."""

    use_streets = True
    return use_streets


# SH: LPB alternation
# TODO
def get_dynamic_settlements_simulation_decision():
    """ Decide how dynamic settlements shall be simulated. Both options will only simulate new settlements if the population is larger than in the last time step.
    Option a) only one new settlement per year? Then set the option to True, required households will be ignored and the settlement simulated at the mapmaximum of remaining population outside existing settlements draw areas.
    Option b) growth in relation to population development. Then the number of required households for a new settlement is needed (and the first option must be set to False)."""

    only_one_new_settlement_per_year = False
    required_households_for_a_new_settlement_threshold = 100  # should be a strong signal, otherwise the map will be full of new settlements.
    return only_one_new_settlement_per_year, required_households_for_a_new_settlement_threshold


# SH: LPB alternation
# TODO
def get_order_of_forest_deforestation_and_conversion():
    """Returns the True or False value for the order of forest conversion and deforestation.
    Set to False if you want to simulate conversion before deforestation."""
    deforestation_before_conversion = True
    return deforestation_before_conversion


# SH: LPB alternation
# TODO
def get_annual_AGB_increment_simulation_decision():
    """This methods lets you chose between spatially-explicit map inputs for annual AGB increment (disturbed, undisturbed, plantation) for the climate periods or
    the stochastic modelling with a min, max value range (see: get_AGB_annual_increment_ranges_dictionary())."""

    # For model stage 1 the spatially-explicit option is not available, since with the ESA version 2 AGB 2018-2017 data no menaingful regression with climate data could be derived.

    # Choose between 'stochastic' or 'spatially-explicit'

    simulate_AGB_increment = 'stochastic'
    return simulate_AGB_increment

# model stage 2
# SH: LPB alternation
# TODO
def get_local_wood_consumption_simulation_choice():
    """Set to True if you want to simulate local wood consumption and thereby potential degradation patterns (can result in RAP-LUT25,
    which would otherwise not be simulated).
    This simulation uses the smallholder share of the population (footprint approach) and the local wood consumption distance to determine the local AGB demand."""

    simulate_local_wood_consumption = True
    return simulate_local_wood_consumption

# model stage 2:
# SH: LPB alternation
# TODO to simulate model stage 2
def get_fragmentation_mplc_RAP_analysis_choice():
    """This method is optional, but required as input for potential habitat corridors.
    If set to True, you have to configure the fragmentation methods for mplc and RAP below.
    The model will write maps and tables for each time step to disk and analyze in R the impact of potential restoration
    measures on fragmentation (before/after maximum number of patches, significant fragmentation values).
    ATTENTION: calculation takes time for the large raster files"""

    analyze_fragmentation_in_mplc_and_RAP = False
    return analyze_fragmentation_in_mplc_and_RAP

# model stage 2:
# SH: LPB alternation
# TODO to simulate model stage 2
def get_PyLandStats_metrics():
    """Define here which metrics of PyLandStats you may want to additionally apply besides fragmentation
    (this is always run, if above method is set to true).
    See the provided "PyLandStats_documentation_V2.pdf in the model main folder for function names.
    ATTENTION: Calculations are quite time intensive"""

    PyLandStats_additional_metrics = ['proportion_of_landscape', 'edge_density']
    return PyLandStats_additional_metrics

# model stage 2:
# SH: LPB alternation
# TODO to simulate model stage 2
def get_potential_habitat_corridors_simulation_choice():
    """Define here if you wish at all to simulate Potential Habitat Corridors (PHCs) for your defined regional umbrella species and if so,
     if only in the mplc ('mplc') landscape or the RAP landscape ('RAP') or both ('mplc+RAP').
     You will have to configure umbrella species requirements further down below.
     ATTENTION: calculation takes time for larger raster files.
     NOTE: Simulation is applied in Circuitscape and thereby fits here potential partial forest dwellers umbrella species,
     which exibit explorative behavior."""

    PHCs_simulation_dictionary = {
        'simulate_PHCs': False,
        'simulation_in': 'mplc'
    }
    return PHCs_simulation_dictionary


# ====== LPB / PLUC adapter ========#
# DK & SH LPB alternation:
# TODO - CHECK THE MODEL FRAMEWORK DEMAND CONFIGURATION
# SH: The demand_configuration dictionary sets the framework for your simulation.
# in model stage 3 you are provided with choices to simulate demand:
# in the footprint approach or partially in the PLUC demand/yield approach
# for the footprint approach: internally or externally (timeseries CSVs),
# for the demand/yield approach: deterministic or stochastic,
# you can read all the columns you configured in the external time series documents or only a selection of them.
# you can simulate in the demand/yield approach for one, two or at maximum three LUTs.

# You therefore have to configure the LPB/PLUC adapter parameters to tell the model which configuration to use.
demand_configuration = {
    # Overall method, use either 'yield_units' or 'footprint' - use 'yield_units' if you want to simulate at least one LUT with this approach
    'overall_method': SETUP_DICT['overall_method']
}

# if 'footprint', the following additional setting are required (has no effect for demand/yield method):
if demand_configuration['overall_method'] == 'footprint':
    demand_configuration['internal_or_external'] = SETUP_DICT['internal_or_external']

# if 'yield_units', the following additional settings are required (has no effect for footprint method):
if demand_configuration['overall_method'] == 'yield_units':
    demand_configuration['deterministic_or_stochastic'] = SETUP_DICT['deterministic_or_stochastic']
    demand_configuration['LUTs_with_demand_and_yield'] = SETUP_DICT['LUTs_with_demand_and_yield']

# this setting depends on the overall method and is automatically set:
# In the folder "inputs > timeseries" you may have provided external time series CSVs. Note here which columns shall be read from the model by noting the column name.
# This way, you need to provide a CSV only once but can simulate different scenarios on it by the combination of columns used externally and model internal simulation.
# The columns/parameters/LUTs you do NOT provide here will be simulated model internally with the footprint approach.
# 1) for the footprint approach the maximum choices are: ['smallholder_share', 2, 3, 4, 5, 'regional_AGB_demand_per_population_total']
if demand_configuration['overall_method'] == 'footprint':
    demand_configuration['list_columns_for_tss'] = SETUP_DICT['list_columns_for_tss']
# 2) in the demand/yield approach the maximum of choices are [2, 3, 4, 5, 'regional_AGB_demand_per_population_total', 'regional_smallholder_share_in_percent]
if demand_configuration['overall_method'] == 'yield_units':
    demand_configuration['list_columns_for_tss'] = SETUP_DICT['list_columns_for_tss']

# SH LPB yield_units alternation:
# TODO if you simulate with yields
def get_yield_simulation_basis_decision():
    """Note here if you simulate with yield on what basis you want to simulate:"""

    # 'original_potential_yield' uses your input maps as is (maximum potential per cell)
    # 'potential_yield_fraction' executes one operation and reduces thereby the potential per cell: potential_yield_map / mapmaximum(potential_yield_map)

    yield_simulation_based_on = 'original_potential_yield'
    return yield_simulation_based_on
# ==============================#

# SH: LPB alternation
# TODO
def get_mplc_with_maximum_anthropogenic_impact_simulation_decision():
    """If this parameter is turned to 'True', the LULCC_mplc module will simulate the maximum anthropogenic impact by an additional allocation
    of the active land use types plus deforestation to allocate the deterministic demand completely in the landscape as long as space is available based on the calculated probabilities and allocation order.
    All subsequent derived variables are then based on this landscape configuration of the narrative: in the future demand must be satisified locally to regionally.
    If set to 'False' the most probable landscape configuration is solely based on probabilities, which means that not all simulated demand is allocated.
    This is also a plausible scenario but pursues another narrative (demand must not be satisfied locally to regionally)."""

    mplc_with_maximum_anthropogenic_impact_simulation = True
    return mplc_with_maximum_anthropogenic_impact_simulation


###############################################################################
### 2.3) Info on study area ###

# SH: LPB alternation
# TODO
def get_country():
    """ Note the country that the region is located in:"""

    country = 'ECUADOR'
    return country


# SH: LPB alternation
# TODO
def get_region():
    """ Note the simulated region:"""

    region = 'Esmeraldas'
    return region


# SH: LPB alternation
# TODO
def get_tiles_identifier():  # (the maps must be numbered in the order of the tiles dictionary 1 to 8)
    """LaForeT tiles handled in the model run depicting original study areas. 3 to 8 depending on the chosen region.
    Only used for cut-outs - project internal output."""

    tiles_dictionary = {}
    tiles_dictionary[1] = {'E09': 'San-Francisco-de-Onzole'}
    tiles_dictionary[2] = {'E10': 'Santo-Domingo-de-Onzole'}
    tiles_dictionary[3] = {'E11': 'Cube'}
    tiles_dictionary[4] = {'E12': 'Tabiazo'}
    tiles_dictionary[5] = None
    tiles_dictionary[6] = None
    tiles_dictionary[7] = None
    tiles_dictionary[8] = None

    return tiles_dictionary


###############################################################################
### 2.4) Info on regional parameters 1 ###

# SH: LPB alternation
# TODO
def get_regional_mean_household_size():
    """Regional mean household size (persons per household) derived from LaForeT data. Needed for dynamic settlements calculation."""

    regional_mean_household_size = 4
    return regional_mean_household_size


# SH: LPB alternation
# TODO
def get_regional_share_smallholders_of_population():
    """Calculated share of smallholders with SSP2 projection data and LaForeT demand agriculture derived from national map agriculture."""

    population_share_smallholders = 53.87# 57.03  # calculated with MAE 2018 from which the overlap with TMF plantation is subtracted and SSP2 population 2018 (67.78)
    return population_share_smallholders


# SH: LPB alternation
# TODO - required for correction step and internal footprint simulation
def get_regional_agriculture_ha_demand_per_LUT_per_person():
    """Returns ha demand per smallholder per active agricultural land use type (LUT02=cropland_annual; LUT03=pasture, LUT04=agroforestry),
    which is allocated based on demand in the area. Discrete values based on regional LaForeT data.
    SSP2 assumption: these values do NOT change over the modelled time frame.
    The final result for each time step based on population values will be rounded via integer() for allocation.
    Demand in plantations is an external time series and demand in Mg input biomass for fuelwood and charcoal an additional parameter."""

    demand_agriculture_dictionary = {}
    demand_agriculture_dictionary[2] = 0.04735  # demand in LUT02 'cropland-annual' in ha per smallholder per year
    demand_agriculture_dictionary[3] = 1.23802  # demand in LUT03 'pasture' in ha per smallholder per year
    demand_agriculture_dictionary[4] = 1.16852  # demand in LUT04 'agroforestry' in ha per smallholder per year
    return demand_agriculture_dictionary


# SH: LPB alternation
# TODO
def get_regional_distance_values_for_agricultural_land_use_dictionary():
    """ To depict the range of human behavior regarding allocation of agricultural land use around settlements fill in the following variables:"""

    regional_distance_values_for_agricultural_land_use_dictionary = {
        2: [791, 10, 2200],  # cropland-annual: mean, minimum and maximum distance in m
        3: [906, 5, 3600],  # pasture: mean, minimum and maximum distance in m
        4: [1184, 5, 4850]  # agroforestry: mean, minimum and maximum distance in m
    }
    return regional_distance_values_for_agricultural_land_use_dictionary


# SH: LPB alternation
# TODO
def get_regional_AGB_demand_per_person():
    """ Regional AGB demand per person consists of demand in Mg input biomass for timber, fuelwood and charcoal,
    calculated with regional forest inventory data for to be applied wood densities and UN fuelwood per household per country data.
    SSP2 assumption: these values do NOT change over the modelled time frame."""

    AGB_demand_timber_in_Mg_per_person_per_year = 0  # timber demand is unclear in LaForeT, but should be considered if data is available
    AGB_demand_fuelwood_in_Mg_per_person_per_year = 0.025898  # derived from UN data
    AGB_demand_charcoal_in_Mg_per_person_per_year = 0  # only relevant in Zambia

    AGB_total_demand_in_Mg_per_person_per_year = AGB_demand_timber_in_Mg_per_person_per_year \
                                                 + AGB_demand_fuelwood_in_Mg_per_person_per_year \
                                                 + AGB_demand_charcoal_in_Mg_per_person_per_year
    return AGB_total_demand_in_Mg_per_person_per_year, AGB_demand_timber_in_Mg_per_person_per_year, AGB_demand_fuelwood_in_Mg_per_person_per_year, AGB_demand_charcoal_in_Mg_per_person_per_year


# SH: LPB alternation
# TODO
# ATTENTION: STDs are not always useable
def get_regional_top_crops_yields_in_Mg_per_ha():
    """LaForeT determined 5 top crops per country for which the regional mean yields snapshot data are given.
    Potential simulated yields based on available ha are a downstream calculation for which the annual outputs are given in the 'LPB_log-file'."""

    top_crops_yields_dictionary = {}
    # given is [name, mean yield, standard deviation yield, percentage of acreage for LUT02(cropland-annual) or LUT04(agroforestry) for the region]
    top_crops_yields_dictionary[1] = ['Cacao', 0.90, 0.70, 82.03, LUT04]
    top_crops_yields_dictionary[2] = ['Coffee', 0.14, 0.01, 0.07, LUT04]  # adjusted STD, only 1 observation
    top_crops_yields_dictionary[3] = ['Plantano', 4.82, 4.81, 12.89, LUT04]  # adjusted from STD 6.10
    top_crops_yields_dictionary[4] = ['Maize', 1.03, 0.89, 51.77, LUT02]
    top_crops_yields_dictionary[5] = ['Cassava', 5.99, 5.98, 10.77, LUT02]  # adjusted from STD 7.04
    return top_crops_yields_dictionary


# SH: LPB alternation
# TODO (change for policy scenario - used for no_conservation in internal footprint only!)
# ATTENTION: set according to prior scenario run
def get_plantation_demand_for_the_worst_case_scenario():
    plantation_demand_for_the_worst_case_scenario = 119725
    return plantation_demand_for_the_worst_case_scenario


# SH: LPB alternation
# TODO
def get_regional_mean_impact_of_settlements_distance_in_m():
    """LaForeT walking distance distance averaged for all LUTs per region"""

    mean_impact_of_settlements_distance_in_m = 1710  # meter
    return mean_impact_of_settlements_distance_in_m


###############################################################################
### 2.5) Further parameters - secondary data ### THESE SHOULD BE GLOBAL TO NATIONAL AND IF POSSIBLE CONSTANT THROUGHOUT THE STUDIES

# SH: LPB alternation
# TODO
def get_mean_plantation_rotation_period_end():
    """A mean plantation rotation period end of XX years for plantations (in LPB mostly commodities of Oil palm, Coconut and Rubber) is set."""

    mean_plantation_rotation_period_end = 25  # years as a global average for oil palm plantations
    return mean_plantation_rotation_period_end


# SH: LPB alternation
# HINT the parameter is set once globally for all LaForeT regions
def get_anthropogenic_impact_distance_in_m():
    """Returns a distance in meter for the in the moderate worst case scenario narrative assumed impact of anthropogenic
    landscape features (cities, settlements, streets) which denote a disturbance of forest in quality in the form of
    fringe effects etc.. Depicts only a rough approximation, since it aggregates all kinds of effects."""

    anthropogenic_impact_distance_in_m = 2000  # meter
    return anthropogenic_impact_distance_in_m


## SH: LPB alternation SUCCESSION AGE inputs
"""For the stochastic simulation of succession age define the maximum ages in accordance to the succession txt files:"""


# TODO
def get_maximum_age_herbaceous_vegetation():
    """In accordance with the succession.txt file for the country the maximum age for herbaceous vegetation pixels is set."""

    maximum_age_herbaceous_vegetation = 3  # years
    return maximum_age_herbaceous_vegetation


# TODO
def get_maximum_age_shrubs():
    """In accordance with the succession.txt file for the country the maximum age for herbaceous vegetation pixels is set."""

    maximum_age_shrubs = 5  # years
    return maximum_age_shrubs


# TODO (change for policy scenario)
def get_maximum_age_forest():
    """In accordance with YOUR GIS INPUT DATA set the known maximum age for (un)disturbed forest.
    Disturbed forest will be simulated in the range below, undisturbed forest with this value."""

    maximum_age_forest = 36  # years (36 for 2018, 44 for 2025)
    return maximum_age_forest


# TODO
def get_user_defined_undisturbed_succession_age_forest():
    """In accordance with YOUR SET SUCCESSION FILE set the age of forest when disturbed forest
    will be simulated as undisturbed if no anthropogenic impact."""

    succession_to_undisturbed_age = 100  # MUST BE SAME VALUE AS IN YOUR SUCCESSION FILE
    return succession_to_undisturbed_age


# TODO
def get_mean_succession_to_disturbed_forest_timeframe_for_the_country():
    """In accordance with the succession.txt file for the country the value for AGB calculation for a new disturbed forest pixel is set."""

    mean_succession_to_disturbed_forest_timeframe_for_the_country = 10  # years
    return mean_succession_to_disturbed_forest_timeframe_for_the_country


# TODO
def get_plantation_age_stochastic_alteration():
    """If your remote sensing data goes only back so far for plantation age, you can simulate a stochastic variation for the earliest date"""

    stochastic_oldest_plantations = True
    return stochastic_oldest_plantations


## SH: LPB alternation
# TODO
def get_AGB_annual_increment_ranges_dictionary():
    """If not spatially-explicit available, this dictionary is used instead to depict a stochastic development in the given range
    (climate change cannot be incorporated as a factor):"""

    AGB_annual_increment_ranges_in_Mg_per_ha_dictionary = {
        'disturbed_forest': [0.4, 5.9],  # disturbed forest in LPB can also apply to quality, therefore max AGB can be present)
        'undisturbed_forest': [0.4, 5.9],
        'agroforestry': [0.1, 12.5],  # due to cultivation broader range
        'plantation': [0, 0]  # Oil palm for Esmeraldas, no forest AGB
    }
    return AGB_annual_increment_ranges_in_Mg_per_ha_dictionary


## SH: LPB alternation
def get_biomass_to_carbon_IPCC_conversion_factor():
    """For calculation of biomass carbon sequestration potential use the current IPCC factor."""

    biomass_to_carbon_IPCC_conversion_factor = 0.5
    return biomass_to_carbon_IPCC_conversion_factor


###############################################################################
### 2.6) Info on stochastic parameters  ###
## TODO only if you re-implement original PLUC, at the moment disabled
# JV: original PLUC method - not to be used in LPB-RAP
def get_stochastic_yield():
    """ JV: Return 1 when the yield map should have a random error, 0 otherwise.

    standardDeviationMap will be used on top of the yield fraction maps
    standardDeviationMaxYield will be used for the time series."""

    stochastic = 1
    standardDeviationMap = 0.2
    standardDeviationMaxYield = 0.1
    return [stochastic, standardDeviationMap, standardDeviationMaxYield]


# JV: original PLUC method - not to be used in LPB-RAP
def get_stochastic_population_density():
    """ JV: Return 1 when the population density map should have a random error + sd."""
    stochastic = 0
    standard_deviation = 0.1
    return [stochastic, standard_deviation]


# JV: original PLUC method - not to be used in LPB-RAP
def get_stochastic_dem():
    """ JV: Return 1 when the dem should have a random error + sd."""
    stochastic = 0
    standard_deviation = 1
    return [stochastic, standard_deviation]


# JV: original PLUC method - not to be used in LPB-RAP
def get_stochastic_distance():
    """ JV: Return 1 when the max distance should have a random error.
    When 1 the maximum distance for the suitability factors 2 (distance to raods), 3(distance to water) and 4(distance to cities)
    varies uniformly between 1 celllength and 2 * max distance,
    e.g. with cellsize of 1 km2 and max distance 5000
    max distance varies between 1000 and 10000 m"""

    stochastic = 0
    return stochastic


# JV: original PLUC method - not to be used in LPB-RAP
def get_stochastic_window():
    """ JV: Return 1 when the window length in suit factor 1(number of neighbors same class) should have an error."""
    stochastic = 0
    return stochastic


###############################################################################
### 2.7) PLUC/LPB dictionaries, lists and values to simulate land use patterns  ###
## TODO only for new scenarios or regions
## SH: LPB alternation
## SH: ADAPT - These values are set globally for all LaForeT domains.
def get_related_land_use_types_dictionary():
    """ JV: Return dictionary which type (key) is related to which others (items).

    e.g. related_land_use_types_dictionary[3] = [1, 2, 3, 7] means:
    land use type 3 is related to types 1, 2, 3 and 7.
    This is used in suitability factor 1 about neighbors
    of the same or a related type."""

    # SH: LPB alternation
    related_land_use_types_dictionary = {}
    related_land_use_types_dictionary[1] = [1]
    # LUT01 = built-up, related to: built-up
    related_land_use_types_dictionary[2] = [2, 3, 4]
    # LUT02 = cropland-annual, related to: cropland-annual, pasture, agroforestry (agriculture LUTs)
    related_land_use_types_dictionary[3] = [2, 3, 4]
    # LUT03 = pasture, related to: cropland-annual, pasture, agroforestry (agriculture LUTs)
    related_land_use_types_dictionary[4] = [2, 3, 4]
    # LUT04 = agroforestry, related to: cropland-annual, pasture, agroforestry (agriculture LUTs)
    related_land_use_types_dictionary[5] = [5]
    # LUT05 = plantation, related to: plantation
    return related_land_use_types_dictionary


## SH: LPB alternation - These values are set globally for all LaForeT domains.
def get_suitability_factors_dictionary():
    """ JV: Return dictionary which type (key) has which suit factors (items).

    e.g. suitability_factors_dictionary[1] = [1, 2, 4, 5, 6, 9] means:
    land use type 1 uses suitability factors 1, 2, 4, 5, 6 and 9.

    SH: suitability factors in LPB are:

      1 = number of neighbors in same class
      2 = distance to streets
      3 = distance to water
      4 = distance to cities
      5 = distance to settlements (NEW)
      6 = population density
      7 = distance to net forest edge (ADAPTED)
      8 = current land use """

    # SH: LPB alternation
    suitability_factors_dictionary = {}
    # LUT 01 = built-up:
    suitability_factors_dictionary[1] = [1, 2, 4, 5, 6, 8]
    # LUT02 = cropland-annual:
    suitability_factors_dictionary[2] = [1, 2, 3, 4, 5, 6, 8]
    # LUT03 = pasture:
    suitability_factors_dictionary[3] = [1, 2, 3, 4, 5, 6, 8]
    # LUT04 = agroforestry
    suitability_factors_dictionary[4] = [2, 5, 7, 8]
    # LUT05 = plantation
    suitability_factors_dictionary[5] = [1, 2, 6, 8]

    if demand_configuration['overall_method'] == 'yield_units':
        suitability_factors_dictionary = get_suitability_factors_yields_dictionary(suitability_factors_dictionary)

    return suitability_factors_dictionary


# SH & DK LPB/PLUC adapter potential yields dictionary
# TODO
# SH LPB/PLUC adapter potential yields dict
def get_suitability_factors_yields_dictionary(suitability_factors_dictionary):
    """SH: If you chose to simulate selected LUTs with yields in the PLUC demand/yield approach, this dictionary will be
    appended in the model to the suitability_factors_dictionary.

    SH: extended suitability factors are:

    9 = potential yield of cropland-annual crops (simulated with friction)
    10 = potential yield of livestock density (simulated with direction)
    11 = potential yield of agroforestry crops (may get extended in the future to 12: agroforestry meat and 13: agroforestry wood) (simulated with friction)
    [may get extended in the future to potential yields for timber plantations, SFM and forests]

    Choose one or all three LUTs to be extended to demand/yield simulation. If you want to still simulate with the footprint approach
    for one or two LUTs leave it/them empty ( = []) """

    # LUT02 = cropland_annual
    if 2 in demand_configuration['LUTs_with_demand_and_yield']: suitability_factors_dictionary[2].extend([9])
    # LUT03 = pasture:
    if 3 in demand_configuration['LUTs_with_demand_and_yield']: suitability_factors_dictionary[3].extend([10])
    # LUT04 = agroforestry
    if 4 in demand_configuration['LUTs_with_demand_and_yield']: suitability_factors_dictionary[4].extend([11])
    return suitability_factors_dictionary


## SH: LPB alternation
## SH: ADAPT - These values are set globally for all LaForeT domains.
# SH LPB/PLUC adapter potential yields weights dict

# comment dk: more compact implementation (and clearer, IMO)
# SH & DK LPB/PLUC adapter potential yields weights dict
def get_weights_dictionary():
    # SH: ATTENTION: This dict will be used in the footprint and the user-defined PLUC demand/yield approach.
    # THEREFORE, alter and extend here your chosen LUTs to include the weight of yield if you want to simulate this way
    """ JV: Return dictionary how a type (key) weights (items) its suit factors.

    e.g. weights_dictionary[1] = [0.3, 0.1, 0.2, 0.1, 0.2, 0.1] means:
    land use type 1 has suitability factor - weight:
    1 - 0.3
    2 - 0.1
    4 - 0.2
    5 - 0.1
    6 - 0.2
    9 - 0.1

    Note that the number and order of weights has to correspond to the
    suitability factors in the previous method."""

    # SH: LPB alternation
    weights_dictionary = {
        ## JV: A list with weights in the same order as the suit factors above

        # LUT01 built-up: can only be simulated in the footprint approach
        # suitability_factors_dictionary[1] = [1, 2, 4, 5, 6, 8]
        1: {
            'footprint': [0.15, 0.1, 0.2, 0.2, 0.2, 0.15]
        },
        # LUT02 = cropland-annual:
        2: {  # LUT02 = cropland-annual footprint:
            # suitability_factors_dictionary[2] = [1, 2, 3, 4, 5, 6, 8]
            'footprint': [0.2, 0.1, 0.1, 0.1, 0.2, 0.2, 0.1],
            # LUT02 = cropland-annual with yield:
            # suitability_factors_dictionary[2] = [1, 2, 3, 4, 5, 6, 8] + 9! => weight of yield for cropland-annual crops
            'yield_units': [0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.1, 0.1]
        },
        # LUT03 = pasture:
        3: {  # LUT03 = pasture footprint:
            # suitability_factors_dictionary[3] = [1, 2, 3, 4, 5, 6, 8]
            'footprint': [0.2, 0.1, 0.1, 0.1, 0.2, 0.2, 0.1],
            # LUT03 = pasture with yield:
            # suitability_factors_dictionary[3] = [1, 2, 3, 4, 5, 6, 8] + 10! => pasture meat
            'yield_units': [0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.1, 0.1]
        },
        # LUT04 = agroforestry:
        4: {  # LUT04 = agroforestry footprint:
            # suitability_factors_dictionary[4] = [2, 5, 7, 8]
            'footprint': [0.25, 0.5, 0, 0.25],
            # LUT04 = agroforestry with yield:
            # suitability_factors_dictionary[4] = [2, 5, 7, 8] + 11! => agroforestry crops
            'yield_units': [0.15, 0.5, 0, 0.25, 0.1]
        },
        # LUT05 plantation: can only be simulated in the footprint approach
        # suitability_factors_dictionary[5] = [1, 2, 6, 8]
        5: {
            'footprint': [0.5, 0.05, 0.25, 0.2]
        }
    }

    weights_to_use = {}
    for lut_key, lut_dict in weights_dictionary.items():
        weights_to_use[lut_key] = lut_dict['yield_units'] if demand_configuration['overall_method'] == 'yield_units' and lut_key in demand_configuration['LUTs_with_demand_and_yield'] else lut_dict['footprint']

    return weights_to_use


## SH: LPB alternation
## SH: ADAPT - These values are set globally for all LaForeT domains.
def get_variables_super_dictionary():
    """ JV: Return nested dictionary for which type (key1) which factor (item1
    and key2) uses which parameters (items2; a list).

    e.g. variables_dictionary1[2] = [-1, 10000, 1, 2] means:
    land use type 1 uses in suitability factor 2 the parameters:
    -1 for direction of the relation (decreasing)
    10000 for the maximum distance of influence
    1 for friction
    and relation type 'inversely proportional' (=2).

    An explanation of which parameters are required for which suitability
    factor is given in the manual of the model."""

    # SH: Suitability factors (SF) and their parameters(P):
    # SF1 neighbors = P1: window length
    # SF2 distance streets = P1: direction; P2: maximum distance effect; P3: friction, P4: relation type
    # SF3 distance water = P1: direction; P2: maximum distance effect; P3: friction, P4: relation type
    # SF4 distance cities = P1: direction; P2: maximum distance effect; P3: friction, P4: relation type
    # SF5 distance settlements = P1: direction; P2: maximum distance effect; P3: friction, P4: relation type
    # SF6 population density = P1: direction
    # SF7 distance to net forest edge = none
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type

    # SH: LPB alternation
    variables_super_dictionary = {}

    # HINT: ALL DISTANCES ARE GIVEN IN METERS

    variables_dictionary1 = {}  # LUT01 = built-up
    # suitability_factors_dictionary[1] = [1, 2, 4, 5, 6, 8]
    # Parameters
    variables_dictionary1[1] = [300]
    # window length for a 3x3 window with a cell length of 100m
    variables_dictionary1[2] = [-1, 5000, 1, 2]
    # SF2 distance streets = P1: negative direction; P2: 5000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary1[4] = [-1, 50000, 1, 2]
    # SF4 distance cities = P1: negative direction; P2: 50000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary1[5] = [-1, 10000, 1, 2]
    # SF5 distance settlements = P1: negative direction; P2: 10000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary1[6] = [1]
    # SF6 population density = P1: positive direction
    variables_dictionary1[8] = {1: 1, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0, 6: 0.75, 7: 0.75, 8: 0.4, 9: 0.4, 10: 0.3, 11: 0.3,
                                12: 0, 13: 0, 14: 0.5, 15: 0.5, 16: 0.5, 17: 0.5, 18: 0.5}
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type
    variables_super_dictionary[1] = variables_dictionary1

    variables_dictionary2 = {}  # LUT02 = cropland-annual
    # suitability_factors_dictionary[2] = [1, 2, 3, 4, 5, 6, 8]
    # Parameters
    variables_dictionary2[1] = [300]
    # window length for a 3x3 window with a cell length of 100m
    variables_dictionary2[2] = [-1, 5000, 1, 2]
    # SF2 distance streets = P1: negative direction; P2: 5000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary2[3] = [-1, 10000, 1, 2]
    # SF3 distance water = P1: negative direction; P2: 10000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary2[4] = [-1, 50000, 1, 2]
    # SF4 distance cities = P1: negative direction; P2: 50000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary2[5] = [-1, 2200, 1,
                                2]  # TODO put down LaForeT max distance settlement to cropland annual (Esmeraldas is set)
    # SF5 distance settlements = P1: negative direction; P2: LAFORET maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary2[6] = [1]
    # SF6 population density = P1: positive direction
    variables_dictionary2[8] = {1: 0, 2: 1, 3: 0.5, 4: 0.5, 5: 0, 6: 0.75, 7: 0.75, 8: 0.4, 9: 0.4, 10: 0.3, 11: 0.3,
                                12: 0, 13: 0, 14: 0.75, 15: 0.5, 16: 0.5, 17: 0.5, 18: 0.5}
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type


    # if demand/yield add SF
    # comment dk: Yes, but also has to check for overall method:
    if demand_configuration['overall_method'] == 'yield_units':
        if 2 in demand_configuration['LUTs_with_demand_and_yield']:
            variables_dictionary2[9] = [1]
            # SF9 potential yield crops cropland_annual = P1: friction unknown or not exponential

    variables_super_dictionary[2] = variables_dictionary2

    variables_dictionary3 = {}  # LUT03 = pasture
    # suitability_factors_dictionary[3] = [1, 2, 3, 4, 5, 6, 8]
    # Parameters
    variables_dictionary3[1] = [300]
    # window length for a 3x3 window with a cell length of 100m
    variables_dictionary3[2] = [-1, 5000, 1, 2]
    # SF2 distance streets = P1: negative direction; P2: 5000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary3[3] = [-1, 10000, 1, 2]
    # SF3 distance water = P1: negative direction; P2: 10000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary3[4] = [-1, 50000, 1, 2]
    # SF4 distance cities = P1: negative direction; P2: 50000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary3[5] = [-1, 3600, 1,
                                2]  # TODO put down LaForeT max distance settlement to pasture (Esmeraldas is set)
    # SF5 distance settlements = P1: negative direction; P2: LAFORET maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary3[6] = [1]
    # SF6 population density = P1: positive direction
    variables_dictionary3[8] = {1: 0, 2: 0.5, 3: 1, 4: 0.5, 5: 0, 6: 0.75, 7: 0.75, 8: 0.4, 9: 0.4, 10: 0.3, 11: 0.3,
                                12: 0, 13: 0, 14: 0.5, 15: 0.75, 16: 0.5, 17: 0.5, 18: 0.5}
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type


    # if demand/yield add SF
    # comment dk: Yes, but also has to check for overall method:
    if demand_configuration['overall_method'] == 'yield_units':
        if 3 in demand_configuration['LUTs_with_demand_and_yield']:
            variables_dictionary3[10] = [1]
            # SF10 potential yield livestock density = P1: positive direction

    variables_super_dictionary[3] = variables_dictionary3

    variables_dictionary4 = {}  # LUT04 = agroforestry
    # suitability_factors_dictionary[4] = [2, 5, 7, 8]
    # Parameters
    variables_dictionary4[2] = [-1, 5000, 1, 2]
    # SF2 distance streets = P1: negative direction; P2: 5000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary4[5] = [-1, 4850, 1,
                                2]  # TODO: put down LaForeT max distance settlement to agroforestry (Esmeraldas is set)
    # SF5 distance settlements = P1: negative direction; P2: LAFORET maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary4[7] = [0]  # TODO: decide per landscape
    # SF7 distance to net forest edge = none
    variables_dictionary4[8] = {1: 0, 2: 0.5, 3: 0.5, 4: 1, 5: 0, 6: 0.75, 7: 0.75, 8: 0.4, 9: 0.4, 10: 0.3, 11: 0.3,
                                12: 0, 13: 0, 14: 0.5, 15: 0.5, 16: 0.75, 17: 0.5, 18: 0.5}
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type


    # if demand/yield add SF
    # comment dk: Yes, but also has to check for overall method:
    if demand_configuration['overall_method'] == 'yield_units':
        if 4 in demand_configuration['LUTs_with_demand_and_yield']:
            variables_dictionary4[11] = [1]
            # SF11 potential yield crops agroforetry = P1: friction unknown or not exponential

    variables_super_dictionary[4] = variables_dictionary4

    variables_dictionary5 = {}  # LUT05 = plantation
    # suitability_factors_dictionary[5] = [1, 2, 6, 8]
    # Parameters
    variables_dictionary5[1] = [300]
    # window length for a 3x3 window with a cell length of 100m
    variables_dictionary5[2] = [-1, 5000, 1, 2]
    # SF2 distance streets = P1: negative direction; P2: 5000m maximum distance effect; P3: unknown or not exponential friction, P4: inversely proportional relation type
    variables_dictionary5[6] = [-1]
    # SF6 population density = P1: negative direction
    variables_dictionary5[8] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 0.75, 7: 0.75, 8: 0.4, 9: 0.4, 10: 0.3, 11: 0.3,
                                12: 0, 13: 0, 14: 0.5, 15: 0.5, 16: 0.5, 17: 0.5, 18: 1}
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type
    variables_super_dictionary[5] = variables_dictionary5

    return variables_super_dictionary


# SH: LPB alternation
# HINT - These values are set globally for all LaForeT domains.
def get_static_LUTs_on_which_no_allocation_occurs():  # former: get_nogo_land_use_types():
    """ JV: Return a list of land use types that cannot be changed.
        SH: This map is calculated once at the beginning of the run."""

    static_LUTs_on_which_no_allocation_occurs = [12,  # water stays as is
                                                 13]  # no input stays as is
    return static_LUTs_on_which_no_allocation_occurs


# SH: LPB alternation
def get_dynamic_LUTs_on_which_no_allocation_occurs():
    """Excludes allocation during simulation on the named land use types in the list. Set to 'None' if not required."""

    dynamic_LUTs_on_which_no_allocation_occurs = [1,  # built-up is a final land use type
                                                  4,  # we assume for agroforestry, that plots are cultivated for long-term use
                                                  5]  # plantation is a quasi final land use type
    return dynamic_LUTs_on_which_no_allocation_occurs


def get_difficult_terrain_slope_restriction_dictionary():
    """SH: Returns a dictionary of a LUT's (key) range of slope which is considered difficult terrain and therefore here is only allocated,
    if no other cell in walking distance is available.
    Below minimum value a LUT can always be allocated.
    Above the maximum value a LUT can never be allocated, as the slope is indeed to steep.
    SSP2-4.5 assumption: People will overcome hurdles of terrain in case of (local) land shortage.

    e.g. difficult_terrain_slope_restriction_dictionary[2] = range(0.17, 0.45) # LUT02 = cropland-annual
    means:
      LUT02 = cropland-annual can always allocate until < 17 % slope,
      17 to 45 % slope is considered difficult terrain which will only be used if no alternative cell is available
      and above 45 % slope this LUT won't be allocated."""
    # TODO
    difficult_terrain_slope_restriction_dictionary = {
        1: [0.45, 0.90],  # LUT01 = minimum and maximum of difficult terrain value built-up
        2: [0.17, 0.45],  # LUT02 = minimum and maximum of difficult terrain value cropland-annual
        3: [0.17, 0.45],  # LUT03 = minimum and maximum of difficult terrain value pasture
        4: [0.17, 0.45],  # LUT04 = minimum and maximum of difficult terrain value agroforestry
        5: [0.17, 0.45]  # LUT05 = minimum and maximum of difficult terrain value plantation
    }
    return difficult_terrain_slope_restriction_dictionary


def get_maximum_slope_deforestation_value():
    """Set the value in slope percent until which deforestation for input biomass will be modelled."""

    maximum_slope_deforestation_value = 0.45
    return maximum_slope_deforestation_value

# model stage 2
# SH: LPB alternation
# TODO
def get_maximum_distance_for_local_wood_consumption():
    """Put down the distance in m for which wood consumption on LUT08 and LUT09 pixels shall be simulated around settlements.
    Acknowledge, that this distance likely is higher due to use of motorized vehicles"""

    maximum_distance_for_local_wood_consumption = 5000
    return maximum_distance_for_local_wood_consumption

# model stage 2
# SH : LPB alternation
# TODO
def get_forest_degradation_regeneration_AGB_content_in_percent_thresholds():
    """Note AGB content percent values per cell in relation to the per climate period modelled provided potential maximum undisturbed AGB
    as thresholds for simulation of approximated forest degradation/regeneration.
    The current AGB per cell is at the end of a simulated time step evaluated as (1) lower than the last time step (degradation) or on the contrary
    (2) equal or higher than last time step (regeneration). Note that approximated degradation stages based on AGB values > 0 Mg per cell
    are only simulated in the context of local wood consumption."""

    forest_degradation_regeneration_AGB_content_in_percent_thresholds = {
        # degradation absolute is simulated where 0 AGB is the new status on a LUT17 pixel
        'degradation_severe_regeneration_low': 37.77, # 37.77
        # degradation_moderate and regeneration_medium are automatically simulated in the span between these values
        'degradation_low_regeneration_high': 80.3 # 80.3
        # regeneration full is simulated where the new AGB value is equal to the potential maximum undisturbed AGB pixel value
    }
    return forest_degradation_regeneration_AGB_content_in_percent_thresholds

# model stage 2
# SH: LPB alternation
# TODO for simulation of model stage 2
def get_fragmentation_mplc():
    """This method delivers input for a forest/habitat/ecosystem fragmentation analysis on LUT(s) in mplc.
    Note the LUT(s) you want to investigate as coherent patches in the list. The noted LUT(s) will be extracted as one boolean
    map and analyzed in the simulated mplc landscape BEFORE restoration measures.
    The LUT choice should reflect species habitat fragmentation analysis regarding accessibility or core habitat."""

    fragmentation_mplc_input_list = [8,
                                     9] # we here investigate general forest, it could also be reduced to only undisturbed forest
    return fragmentation_mplc_input_list



#######################################
## 3) R A P  -  P A R A M E T E R S ##

# note the RAP LUTs once - leave room until 20 if someone might need an additional LUTs in other areas (ice?)
LUT21 = 'RAP agroforestry'  # cropland-annual and pasture transformation
LUT22 = 'RAP plantation'  # multifunctional mixed timber long-term rotation plantation outside national net forest 2018 + 3 % + potential natural vegetation - other ecosystems
LUT23 = 'RAP reforestation'  # goal of primary forest development inside net forest 2018 + 3 % + potential natural vegetation - other ecosystems
LUT24 = 'RAP other ecosystems'  # in Copernicus specifically: herbaceous wetland and moss, lichen, bare, sparse vegetation
# model stage 2
LUT25 = 'RAP restoration of degraded forest' # will only occur if local wood consumption is simulated


def get_list_of_RAP_land_use_types():
    """Note the RAP LUTs to be recognized by the model."""

    list_of_RAP_land_use_types = [21,  # RAP agroforestry
                                  22,  # RAP plantation
                                  23,  # RAP reforestation
                                  24]  # RAP other ecosystems
    if get_local_wood_consumption_simulation_choice() == True:
        list_of_RAP_land_use_types.append(25) # only simulated when local wood consumption is applied: RAP restoration of degraded forest
    return list_of_RAP_land_use_types


# TODO (change for policy scenario)
def get_net_forest_percentage_increment_goal():
    """Set the targeted increment percentage for net forest area (LUT disturbed and undisturbed forest).
    Set to the UN 2017 goal of globally 3 % more forest area."""

    percentage_increment_net_forest_area = 3  # % (UN, 2017: 3 or calculated for no conservation scenario: see weak or enforced conservation output RAP CSV output) 13.734
    return percentage_increment_net_forest_area


def get_weights_list_net_forest():
    # SH: LPB alternation
    # suitability_factors_dictionary[net forest] = [1, 7, 8]
    weights_list_net_forest = [0.4, 0.3, 0.3]  # stress weight for cells in a 3x3 window
    return weights_list_net_forest


def get_targeted_additional_net_forest_allocation_dictionary():
    # SH: LPB alternation
    # HINT: ALL DISTANCES ARE GIVEN IN METERS

    variables_dictionary = {}  # for net forest additional target area allocation
    # suitability_factors = [1, 7, 8]
    # Parameters
    variables_dictionary[1] = [300]
    # window length for a 3x3 window with a cell length of 100m
    variables_dictionary[7] = [1]
    # SF7 P1 distance to net forest edge = positive direction
    variables_dictionary[8] = {0: 1, 1: 0}  # based on a boolean map where only cells with type 0 shall become new cells
    # SF8 current land use = P1: suitability of current land use to become this dictionary land use type

    return variables_dictionary


def get_list_of_LUTs_for_definition_of_potential_restricted_areas():
    """This list is used to identify the remaining potential additional areas suitable for restriction programs
    in the landscape at the population peak maximum anthropogenic impact (maximum extent of land use).
    These areas might serve to define additional restricted areas short-term."""

    list_of_LUTs_for_definition_of_potential_restricted_areas = [8,  # disturbed forest
                                                                 9,  # undisturbed forest
                                                                 10,  # moss, lichen, bare, sparse vegetation
                                                                 11,  # herbaceous wetland
                                                                 12,  # water
                                                                 23,  # reforested for target of primary/net forest
                                                                 24]  # other ecosystems

    return list_of_LUTs_for_definition_of_potential_restricted_areas

# model stage 2
# SH: user-defined RAP-LUT25 simulation
# TODO
def get_user_defined_RAPLUT25_input_degradation_stages():
    """Define here, how many degradation stages shall be integrated into RAP-LUT25 RAP restoration of degraded forest.
    Set the according classes to True."""

    user_defined_RAPLUT25_input_degradation_stages = {
        # degradation absolute is covered in RAP reforestation or plantation
        'degradation_severe': True,
        'degradation_moderate': True,
        'degradation_low': False
    }
    return user_defined_RAPLUT25_input_degradation_stages


# model stage 2
# SH: LPB alternation
# TODO for simulation of model stage 2
def get_fragmentation_RAP():
    """This method delivers input for a forest/habitat/ecosystem fragmentation analysis on LUT(s) in RAP.
    Note the LUT(s) you want to investigate as coherent patches in the list. The noted LUT(s) will be extracted as one boolean
    map and analyzed in the simulated RAP landscape AFTER restoration measures."""

    fragmentation_RAP_input_list = [8,
                                    9,
                                    22,
                                    23,
                                    25]  # we here investigate general potential forest after restoration measures, it could also be reduced to only LUTs 9, 23 and 25
    return fragmentation_RAP_input_list

#######################################
## 4) OC  -  P A R A M E T E R S ##



#######################################
## 5) S F M  -  P A R A M E T E R S ##
