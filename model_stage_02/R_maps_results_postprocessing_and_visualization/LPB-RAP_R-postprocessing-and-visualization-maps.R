# general plotting
library(tidyverse)
library(dplyr)
library(purrr)
library(ggplot2)
library(lubridate)
library(viridis)  
library(magrittr)
library(tidyr)
library(ggnewscale)
library(cowplot)
library(ggpubr)
# install.packages("devtools")
# devtools::install_github("eliocamp/ggnewscale@dev")
library(ggrepel) # out?
library(ggridges) # out?
library(ggthemes)

# data processing
library(foreign) # for reading dbfs
library(dplyr)
library(gridExtra) # to arrange grid plots

# spatial and raster processing
library(stars)
library(raster)
library(rasterVis)
library(rgdal)
library(dismo) #map raster on Google Map
library(ggspatial)
library(sf)
library(sp)
library(ggmap)
library(scales)
library(elevatr)
#library(GISTools)
library(maps)
#install.packages("rnaturalearthhires", repos = "http://packages.ropensci.org", type = "source")
library(rnaturalearth)
library(rosm)


library(readxl)
library(rlang)
library(ggtext)

# Test for PCRaster driver auf Windows - if this driver is not present you need to transform maps manually to .tif
gdalDrivers() 
# MAC: position 99

# Model stage 1 (MS1) authors: DK & SH, 2022/Q2
# Model stage 2 (MS2) authors: DK & SH, 2023/Q2


### MS1 / MS2 User required preparations: ################################################
# All OS:
# run all three policy scenarios for one region in one baseline scenario within the accordingly named main model folder
# create two empty folders for inputs (e.g. "R_maps_inputs") and outputs (e.g. "R_maps_outputs") within this folder
# UNIX (macOS and Linux) users: 
# Adjust the 'user-defined settings' section below to your model, your liking or study (area) and install required packages.
# Run script (inputs will be loaded and transformed to .tif automatically from your main model policy scenario input and output folders)
# Windows users: 
# Run model ones with error messages, then you need to transform the selected .maps and .time_steps maps manually to .tif in a GIS 
# and paste them into the encoded generated folder structure.
# Adjust the 'user-defined settings' section below to your model, your liking or study (area) and install required packages.
# MS2 set the ms2 variables to True if simulated with external demand series and MS2 simulation options
# Run script again


############################################################################################################################
### R SCRIPT for LPB-RAP maps visualization ################################################################################
############################################################################################################################


# user-defined settings (SH) ---------------------------------------------------------------------------------------------------------------------------------------------

# => define here which demand configuration you used: 'footprint_internal', 'footprint_external', 'yield_units_deterministic' or 'yield_units_stochastic'
demand_configuration <- "footprint_external"

# define here if you simulated demands with an 'internal' or 'external' time series
time_series_input <- 'external'

# define here if you simulated in MS1 or MS2
model_stage <- 'MS2'

# define here if you simulated demands with an 'internal' or 'external' time series
time_series_input <- 'external'

# => define the main model folder for which analysis shall be run (separate by baseline scenario and region)
main_model_folder <- "LULCC_ECU_Esmeraldas_SSP2-4.5_HABITAT" # "LULCC_ECU_Esmeraldas_SSP2-4.5"

# define the R_inputs folder you use
input_folder <- "R_maps_inputs"

# => define the basic output settings:
# define output folder
output_folder <- "R_maps_outputs"

# define maps output format
output_format <- ".png"

# define output height and width and unit ("in", "cm", "mm", "px") A4 portrait: 21 x 29.7 cm resp. 2480 x 3508 pixels (print resolution)
output_height <-  6.69 * 2.54 # (A4 landscape with fringe; for Portrait format small: 3.94 inch * factor to -> 10 cm)
output_width <- 10.12 * 2.54 # (A4 landscape with fringe; for Portrait format small: 6.69 inch * factor to > 17 cm)
output_unit <- "cm"  # default unit is "in". If "cm", simply transform height and width from inches to cm

# define output dpi, "retina" (320), "print" (300), or "screen" (72). Applies only to raster output types.
output_dpi = 320

# => define the output appearance:
# define the ggplot basic theme (theme_light() used for development)
ggplot_base_theme <- theme_light()

# => Define theme alterations:
# choose the font to be used out of sans, serif and mono (universal fonts)
user_defined_font <- "sans"

# choose the font size to be used for main information
user_defined_fontsize <- 11

# choose by which degree less important information should be displayed (e.g. 2 if you want font size 9 contrasting 11)
user_defined_fontsize_factor <- 2

# # define the smallest used font size, only applied to annotation labels in plots - ATTENTION THIS IS IN mm
# user_defined_annotation_label_size <- 2.5
# 
# # for annotation labels the plot require additional space. Fill in the dates:
# user_defined_xlim_annotation_labels <- c(as.Date(c("2105-12-31", "2110-12-31"))) # in between which years shall annotation labels be displayed
# user_defined_x_axis_expansion_for_lables <- as.Date(c("2018-12-31", "2110-12-31")) # adjust the plot x limits accordingly

# choose if labels should be left, centered or right (hjust = 0, 0.5, or 1)
user_defined_hjust <- 0

# define where x axis labels (years) should be
user_defined_x_hjust <- 1
user_defined_x_vjust <- 1

# choose the face (plain, bold or italic) for title and subtitle and all other labels
user_defined_title_face <- "bold" # will also be applied to legend title
user_defined_subtitle_face <- "italic" # only applied to subtitles
user_defined_other_face <- "plain" # all other labels

# choose the rotation angle for x axis labels (years)
user_defined_rotation_angle <- 0

# define the baseline color for graphics labels
user_defined_baseline_color <- "grey30"

# choose an accessible color spectrum to be used for the maps (viridis, magma, plasma, inferno, cividis, mako, rocket, turbo) - not applied to all maps
user_defined_color_spectrum <- "viridis"

# # choose how the population peak is indicated by a geom_vline in the graphs (blank, solid, dotted, dashed, dotdash, longdash, twodash)
# user_defined_linetype <- "dashed"

# define the EPSG for the region
user_defined_EPSG <- 32717

# define attributes position (top/bottom left/right combinations):
user_defined_north_arrow_location <- "br"
user_defined_north_arrow_pad_x <- 1
user_defined_north_arrow_pad_y <- 1
user_defined_north_arrow_unit <- "cm"
user_defined_map_scale_location <- "br"

# => give study  and study area information:
# define the probing dates including the population peak year
# MS2: add population peak and if simulated with external time series the peak demands year
years_for_plotting = list(
  'weak_conservation' = c(2024, 2070),
  'enforced_conservation' = c(2024, 2070),
  'no_conservation' = c(2024, 2070)
)

# MS2: define which scenario you used for simulation
ms2_policy_scenario_used <- 'weak_conservation'

# MS2: note the population peak year singularly
population_peak_year <- 2060

# MS2: note the peak demands year accordingly to the conducted run
peak_demands_year <- 2100

# define your used initial simulation year for weak and enforced conservation
initial_simulation_year_BAUs <- 2018

# define your used initial simulation year for no conservation
initial_simulation_year_worst_case <- 2025

# define the last simulation year
last_simulation_year <- 2100

# define your probing dates as years:
probing_dates_years = c(2024, 2070)

# define your used climate periods
climate_periods <- tibble(
  start_date = c(2018, 2021, 2041, 2061, 2081),
  description = c('Climate reference period (<=2020)', 
                  'Climate period 2021 - 2040', 
                  'Climate period 2041 - 2060', 
                  'Climate period 2061 - 2080', 
                  'Climate period 2081 - 2100')
)

# define the names of the provided subset study area tiles (up to 8 can be handled by the model)
tiles_description <- tibble(
  tile = c('tile_1', 'tile_2', 'tile_3', 'tile_4', 'tile_5', 'tile_6', 'tile_7', 'tile_8'),
  tile_indicator = c("E09", "E10", "E11", "E12", NA, NA, NA, NA),
  tile_name = c('E09 = San Francisco de Onzole',
                'E10 = Santo Domingo de Onzole',
                'E11 = Cube',
                'E12 = Tabiazo',
                NA, NA, NA, NA)
)
### ATTENTION: if you have more than 4 you need to set a new color spectrum in the according lines of the Initial conditions plot:
# Here used "magma": https://waldyrious.net/viridis-palette-generator/
# pl <- pl + scale_fill_manual(name = tiles_legend_title,
#                              values = c("#fcfdbf", "#fc8961", "#b73779", "#51127c"))

# if you simulated with local wood consumption / degradation / RAP-LUT25 set the variable to true
local_degradation_simulated <- TRUE

# MS2: if you incoporated habitat analysis for a regional umbrella species, name it here
umbrella_species_name <- 'Panthera onca'

# MS2: if you have presence data, note the path
umbrella_species_presence_data_provided <- TRUE
umbrella_species_presence_data_path <- file.path('LULCC_Esmeraldas', 'inputs_weak_conservation', 'presence_data', 'umbrella_species_presence.xlsx')

# MS2: note which threshold value for patch selection used
umbrella_species_minimum_patch_size_in_km2 <- 50

# MS2: if you simulated fragmentation set the variable to true
fragmentation_simulated <- TRUE

# MS2: if you simulated habitat analysis the ecosystem fragmentation maps for the umbrella species for the probing dates will be drawn from mplc and RAP
performed_habitat_analysis <- TRUE

# MS2: define if you employed the Omniscape analysis in mplc
performed_Omniscape_analysis_mplc <- TRUE
# draws the following maps for the probing dates:
# Omniscape - normalized
# Omniscape - cumulative
# Omniscape - flow

# MS2: define if you employed the Circuitscape analysis ADVANCED in mplc
performed_Circuitscape_analysis_advanced_mplc <- FALSE
# draws the following maps for the probing dates:
# Circuitscape - curmap
# Circuitscape - voltmap

# MS2: define if you employed the Circuitscape analysis PAIRWISE in mplc
performed_Circuitscape_analysis_pairwise_mplc <- TRUE
# draws the following maps for the probing dates:
# Circuitscape - cumulative curmap


# MS2: define if you employed the Omniscape analysis in RAP
performed_Omniscape_analysis_RAP <- TRUE
# draws the following maps for the probing dates:
# Omniscape - normalized
# Omniscape - cumulative
# Omniscape - flow

# MS2: define if you employed the Circuitscape analysis ADVANCED in RAP
performed_Circuitscape_analysis_advanced_RAP <- FALSE
# draws the following maps for the probing dates:
# Circuitscape - curmap
# Circuitscape - voltmap

# MS2: define if you employed the Circuitscape analysis PAIRWISE in RAP
performed_Circuitscape_analysis_pairwise_RAP <- TRUE
# draws the following maps for the probing dates:
# Circuitscape - cumulative curmap

# MS2: define if you averaged habitat analysis results
user_defined_averaging_of_habitat_analysis_results_applied <- FALSE


# define the colors you want to be displayed for Land Use Types (so far 18/19 + 4/5)
# http://www.stat.columbia.edu/~tzheng/files/Rcolor.pdf
# current list of land use types:
# LUT01	built-up (active LUT, firebrick)
# LUT02	cropland-annual (active LUT, gold)
# LUT03	pasture (active LUT, palegreen)
# LUT04	agroforestry (active LUT, olivedrab)
# LUT05	plantation (active LUT, cadetblue4)
# LUT06	herbaceous vegetation (succession LUT, moccasin)
# LUT07	shrubs (succession LUT, chocolate)
# LUT08	disturbed forest (succession LUT, limegreen)
# LUT09	undisturbed forest (succession LUT, darkgreen)
# LUT10	moss, lichen, bare, sparse vegetation (passive LUT, powderblue)
# LUT11	herbaceous wetland (passive LUT, lavender)
# LUT12	water -> MS2 = permanent waterbodies (static LUT, steelblue)
# LUT13	no input (static LUT, slategrey)
# LUT14	cropland-annual - - abandoned (indirect active LUT, orange) - supposed to pop out
# LUT15	pasture - - abandoned (indirect active LUT, chartreuse) - supposed to pop out
# LUT16	agroforestry - - abandoned (indirect active LUT, blueviolet) - supposed to pop out
# LUT17	net forest - - deforested (indirect active LUT, deeppink) - supposed to pop out
# LUT18	plantation - - deforested (indirect active LUT, deeppink3) - supposed to pop out
# LUT19 ocean (static LUT, mediumblue)
# LUT21	RAP agroforestry for traditional farming systems (RAP LUT, greenyellow) - indicates more forest cover
# LUT22	RAP plantation (RAP LUT, springgreen) - indicates more forest cover
# LUT23	RAP reforestation (RAP LUT, lawngreen) - indicates more forest cover
# LUT24	RAP other ecosystems (RAP LUT, azure) - indicates mainly ecosystems related to the "blue section"
# LUT25 RAP restoration of degraded forest (RAP LUT, palegreen) - indicates restored forest cover
# MS2: Only if you simulated local wood consumption / degradation: LUT25 (RAP LUT, palegreen is added automatically)

# create named vector that links lut values and lut colors for the base configuration - LUT25 is added below based on user-defined setting for degratation simulation 
LUT_colors <- tibble(
  lut_value = c(1,2,3,4,5, 6,7,8,9, 10,11,12,13, 14,15,16,17,18,19, 21,22,23,24),
  colors = c("firebrick", "gold", "palegreen", "olivedrab", "cadetblue4",
            "moccasin", "chocolate", "limegreen", "darkgreen",
            "powderblue", "lavender", "steelblue", "slategrey",
            "orange", "chartreuse","blueviolet", "deeppink","deeppink3","mediumblue",
            "greenyellow", "springgreen", "lawngreen", "azure")
) %>%
  mutate(LUT_code = paste('LUT', str_pad(lut_value, 2, 'left', '0'), sep = ''))

# for your personal regional landscape slope categories depiction define here the slope values, note: the model output is e.g. 0.1 for 10%
user_defined_slope_category_breaks = c(-0.1, 0.05, 0.15, 0.30, 0.45, 2) # note segments +1, 20 -> 200% maximum % value
user_defined_slope_category_names = c("0 - 5", ">5 - 15", ">15 - 30", ">30 - 45", ">45")

# define until which length numbers will be written and not given in scientific notation:
options(scipen = 999999)

# give the total simulated landscape area and unit 
landscape_area <-  scales::label_comma(accuracy= 1) (1678488)
landscape_area_numeric <-  1678488
landscape_division_threshold <- 1000
landscape_area_unit <- "ha"

# give the applied baseline scenario information
baseline_scenario <- "SSP2-4.5"

# give the country
country <- "ECUADOR"

# give the region
region <- "Esmeraldas"

# give your project name used to sample the subset tiles
project <- "LaForeT"

# define the Publication indicator prefix for outputs, ATTENTION: this must be set manually in the ggsave statements
publication_indicator <- "Publication"

# define that no aux.xml files get produced
rgdal::setCPLConfigOption("GDAL_PAM_ENABLED", "FALSE")

# MS1 + MS2 alternate according to user setting (SH) ---------------------------------------------------------------------------------------------------------------------------------------------

### Translate years to time steps
# get the sequence
simulation_time_frame_years_conservation = seq.int(initial_simulation_year_BAUs, last_simulation_year)
simulation_time_frame_years_no_conservation = seq.int(initial_simulation_year_worst_case, last_simulation_year)
# get the index positions
conservation = which(simulation_time_frame_years_conservation %in% probing_dates_years)
no_conservation = which(simulation_time_frame_years_no_conservation %in% probing_dates_years)
# translate to time steps
probing_dates_time_steps = list(
  'weak_conservation' = as.vector(conservation),
  'enforced_conservation' = as.vector(conservation),
  'no_conservation' = as.vector(no_conservation)
)

# get the outputs folder per demand configuration
demand_configuration_outputs_folder <- 'empty'
if (demand_configuration == "footprint_internal") {
  demand_configuration_outputs_folder <- 'outputs_footprint_internal'
}
if (demand_configuration == "footprint_external") {
  demand_configuration_outputs_folder <- 'outputs_footprint_external'
}
if (demand_configuration == "yield_units_deterministic") {
  demand_configuration_outputs_folder <- 'outputs_yield_units_deterministic'
}
if (demand_configuration == "yield_units_stochastic") {
  demand_configuration_outputs_folder <- 'outputs_yield_units_stochastic'
}

# adjust color scheme
if (local_degradation_simulated == TRUE) {
  LUT_colors <- tibble(
    lut_value = c(1,2,3,4,5, 6,7,8,9, 10,11,12,13, 14,15,16,17,18,19, 21,22,23,24,25),
    colors = c("firebrick", "gold", "palegreen", "olivedrab", "cadetblue4",
               "moccasin", "chocolate", "limegreen", "darkgreen",
               "powderblue", "lavender", "steelblue", "slategrey",
               "orange", "chartreuse","blueviolet", "deeppink","deeppink3", "mediumblue",
               "greenyellow", "springgreen", "lawngreen", "azure", "palegreen")
  ) %>%
    mutate(LUT_code = paste('LUT', str_pad(lut_value, 2, 'left', '0'), sep = ''))
  print.data.frame(LUT_colors)
}

# p.r.n. adjust scenarios used
if (model_stage == 'MS2') {
  probing_dates_time_steps <- probing_dates_time_steps[names(probing_dates_time_steps) == ms2_policy_scenario_used]
  print(probing_dates_time_steps)
  
  years_for_plotting <- years_for_plotting[names(years_for_plotting) == ms2_policy_scenario_used]
  print(years_for_plotting)
}


# import RAP LUTs lookup table (SH) ----------------------------------------------------------------------------------------------------------------------------------
path_to_file <- file.path('..', main_model_folder, demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'tidy_data')

RAP_LUTs_lookup_table <- read_csv(file.path(path_to_file, 'RAP_LUTs_lookup_table.csv'), col_names = c('LUT_code', 'LUT_name')) %>%
  unite('LUT_name', c('LUT_code', 'LUT_name'), sep = ' = ', remove = FALSE)

# load and transform maps (DK + SH) ----------------------------------------------------------------------------------------------------------------------------------
# Base code:
model_output_folder <- file.path('..', main_model_folder)
maps_info <- tibble(
  'dataset_name' = character(),
  'from_folder' = character(),
  'to_folder' = character(),
  'file_names' = character()
)

add_dataset <- function(dataset_name, from_folder, to_folder, file_names, maps = maps_info){
  maps <- maps %>%
    add_row(
      dataset_name = dataset_name,
      from_folder = from_folder,
      to_folder = to_folder,
      file_names = file_names
    )
  return(maps)
}

filter_for_probing_dates <- function(probing_dates, list_of_files){
  list_of_files[str_sub(list_of_files, start= -3) %in% str_pad(probing_dates, width=3, pad='0')]
}

# > MS1 IMPORT MAPS ####
# Define NAMES, FOLDERs AND PATHs
# singular maps: [FOLDER "deterministic"]

# ATTENTION: SCALAR
# slope
maps_info <- add_dataset(
  'model_internal_slope_map_in_percent',
  file.path(model_output_folder, demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'model_internal_slope_map'),
  file.path(input_folder, 'deterministic', 'Slope'),
  'model_internal_slope_map_in_percent.map'
)


# streets 
maps_info <- add_dataset(
  'streets',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'Streets'),
  'static_streets_input.map'
)

# cities 
maps_info <- add_dataset(
  'cities',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'Cities'),
  'static_cities_input.map'
)

# settlements
maps_info <- add_dataset(
  'settlements',
  file.path(model_output_folder, 'inputs_weak_conservation', 'initial'),
  file.path(input_folder, 'deterministic', 'Settlements'),
  'initial_settlements_input.map'
)

# null mask 
maps_info <- add_dataset(
  'null_mask',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'Null_mask'),
  'static_null_mask_input.map'
)

# net forest 
maps_info <- add_dataset(
  'net_forest',
  file.path(model_output_folder, 'inputs_weak_conservation', 'initial'),
  file.path(input_folder, 'deterministic', 'Net_forest'),
  'initial_net_forest_input.map'
)

# ATTENTION: SCALAR
# - DEM -> Hillshade map (preparations, define ggplot once to built in the following plots)
# PATH: inputs_BAU > static > 'static_dem_input_map'
maps_info <- add_dataset(
  'dem',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'DEM'),
  'static_dem_input.map'
)

# tiles
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'static')

maps_info <- add_dataset(
  'tiles',
  source_folder,
  file.path(input_folder, 'deterministic', 'Tiles'),
  list.files(source_folder, pattern = 'tile')
)

# ATTENTION: SCALAR
# - population maps (continuous scale) + population initial simulation year BAU and worst case (folder deterministic also)

# PATH: inputs_BAU > projection > contains the string: "projection_decadal_population" (.map format) => muß in deterministic folder
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'projection')

maps_info <- add_dataset(
  'population',
  source_folder,
  file.path(input_folder, 'deterministic', 'Population'),
  list.files(source_folder, pattern = 'decadal_population')
)

# ATTENTION: SCALAR
# PATH: outputs_BAU > LPB > LULCC_Simulation > dynamic_population_deterministic > 'populus0.001' (time step suffix) => muß in den deterministic subfolder initial_population_BAUs 
source_folder <- file.path(model_output_folder, demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'LULCC_Simulation', 'dynamic_population_deterministic')
list.files(source_folder, pattern = 'populus0.001')

maps_info <- add_dataset(
  'population',
  source_folder,
  file.path(input_folder, 'deterministic', 'Population', 'initial_population_BAUs'),
  list.files(source_folder, pattern = 'populus0.001')
)

# ATTENTION: SCALAR
# PATH: outputs_worst-case > LPB > LULCC_Simulation > dynamic_population_deterministic > 'populus0.001' (time step suffix) => muß in den deterministic subfolder initial_population_worst-case 
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder,'outputs_no_conservation', 'LPB', 'LULCC_Simulation', 'dynamic_population_deterministic')
list.files(source_folder, pattern = 'populus0.001')

maps_info <- add_dataset(
  'population',
  source_folder,
  file.path(input_folder, 'deterministic', 'Population', 'initial_population_worst-case'),
  list.files(source_folder, pattern = 'populus0.001')
)

# - PNV maps (discrete scale)
# PATH: inputs_BAU > projection > contains the string: "projection_potential_natural_vegetation_distribution" (.map format)
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'projection')

maps_info <- add_dataset(
  'potential_natural_vegetation',
  source_folder,
  file.path(input_folder, 'deterministic', 'PNV'),
  list.files(source_folder, pattern = 'projection_potential_natural_vegetation_distribution')
)


# ATTENTION: SCALAR
# - maximum undisturbed AGB (continuous scale)
# PATH: inputs_BAU > projection > contains the string: "projection_potential_maximum_undisturbed_AGB" (.map format)
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'projection')

maps_info <- add_dataset(
  'potential_maximum_undisturbed_AGB',
  source_folder,
  file.path(input_folder, 'deterministic', 'AGB_maximum_undisturbed'),
  list.files(source_folder, pattern = 'projection_potential_maximum_undisturbed_AGB')
)

# ATTENTION: SCALAR
# - initial AGB (continuous scale)
# PATH: inputs_BAU > initial > initial_AGB_input.map
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'initial')

maps_info <- add_dataset(
  'initial_AGB',
  source_folder,
  file.path(input_folder, 'deterministic', 'AGB_initial'),
  list.files(source_folder, pattern = 'initial_AGB_input.map')
)


# - initial LULCC (discrete scale)
# PATH: inputs_BAU > initial > initial_LULC_input.map
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'initial')

maps_info <- add_dataset(
  'initial_LULC',
  source_folder,
  file.path(input_folder, 'deterministic', 'LULC_initial'),
  list.files(source_folder, pattern = 'initial_LULC_input.map')
)
# - initial LULC worst case scenario
# inputs_worst-case > initial > initial_LULC_simulated_for_worst_case_scenario_input.map
source_folder <- file.path(model_output_folder, 'inputs_no_conservation', 'initial')

maps_info <- add_dataset(
  'initial_LULC_worst_case',
  source_folder,
  file.path(input_folder, 'deterministic', 'LULC_initial_worst-case'),
  list.files(source_folder, pattern = 'initial_LULC_simulated_for_worst_case_scenario_input.map')
)

# - correction step BAU BAU(+) (discrete scale)
# PATH: inputs_BAU > initial > initial_LULC_simulated_input.map
source_folder <- file.path(model_output_folder, 'inputs_weak_conservation', 'initial')

maps_info <- add_dataset(
  'initial_LULC_simulated_weak_conservation',
  source_folder,
  file.path(input_folder, 'deterministic', 'LULC_initial_simulated_weak_conservation'),
  list.files(source_folder, pattern = 'initial_LULC_simulated_input.map')
)

# PATH: inputs_BAU(+) > initial > initial_LULC_simulated_input.map
source_folder <- file.path(model_output_folder, 'inputs_enforced_conservation', 'initial')

maps_info <- add_dataset(
  'initial_LULC_simulated_enforced_conservation',
  source_folder,
  file.path(input_folder, 'deterministic', 'LULC_initial_simulated_enforced_conservation'),
  list.files(source_folder, pattern = 'initial_LULC_simulated_input.map')
)
# - p.r.n.: freshwater distribution (discrete scale)
# PATH: inputs_BAU > static > static_freshwater_input.map
maps_info <- add_dataset(
  'freshwater',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'Freshwater'),
  'static_freshwater_input.map'
)

# - restricted areas map (discrete scale)
# PATH: inputs_BAU > static > static_de-jure_restricted-areas_input.map
maps_info <- add_dataset(
  'restricted_areas',
  file.path(model_output_folder, 'inputs_weak_conservation', 'static'),
  file.path(input_folder, 'deterministic', 'Restricted_areas'),
  'static_de-jure_restricted-areas_input.map'
)

# ATTENTION: SCALAR
# all three scenarios probing dates: [FOLDERS PER SCENARIO] 
# - landscape modelling probabilities (discrete scale)
# BAU
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration_probabilities_classified > name contains string "mplcclpr" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration_probabilities_classified')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                 list.files(source_folder))
maps_info <- add_dataset(
  'landscape_modelling_probabilities',
  source_folder,
  file.path(input_folder, 'weak_conservation', 'Landscape_modelling_probabilities'),
  # list.files(source_folder, pattern = 'mplcclpr')
  list_of_source_files
)

# BAU(+)
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration_probabilities_classified > name contains string "mplcclpr" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration_probabilities_classified')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['enforced_conservation']],
                                                 list.files(source_folder))
maps_info <- add_dataset(
  'landscape_modelling_probabilities',
  source_folder,
  file.path(input_folder, 'enforced_conservation', 'Landscape_modelling_probabilities'),
  # list.files(source_folder, pattern = 'mplcclpr')
  list_of_source_files
)

# worst-case
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration_probabilities_classified > name contains string "mplcclpr" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration_probabilities_classified')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['no_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_modelling_probabilities',
  source_folder,
  file.path(input_folder, 'no_conservation', 'Landscape_modelling_probabilities'),
  # list.files(source_folder, pattern = 'mplcclpr')
  list_of_source_files
)

# - scenarios LULCC mplc RAP (discrete scale)
# BAU
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration > name contains string "mplc0000" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_mplc',
  source_folder,
  file.path(input_folder, 'weak_conservation', 'Landscape_configuration_mplc'),
  # list.files(source_folder, pattern = 'mplc0000')
  list_of_source_files
)

# BAU(+)
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration > name contains string "mplc0000" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['enforced_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_mplc',
  source_folder,
  file.path(input_folder, 'enforced_conservation', 'Landscape_configuration_mplc'),
  # list.files(source_folder, pattern = 'mplc0000')
  list_of_source_files
)

# worst-case
# PATH: outputs_(scenario-folder) > LPB > LULCC_most_probable_landscape_configuration > most_probable_landscape_configuration > name contains string "mplc0000" + time step suffix
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'LPB', 'LULCC_most_probable_landscape_configuration', 'most_probable_landscape_configuration')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['no_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_mplc',
  source_folder,
  file.path(input_folder, 'no_conservation', 'Landscape_configuration_mplc'),
  # list.files(source_folder, pattern = 'mplc0000')
  list_of_source_files
)

# PATH: outputs_(scenario-folder) > RAP > POSSIBLE_LANDSCAPE_CONFIGURATION > name contains string: "RAP00000" + time step suffix
# BAU
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'POSSIBLE_LANDSCAPE_CONFIGURATION')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_RAP',
  source_folder,
  file.path(input_folder, 'weak_conservation', 'Landscape_configuration_RAP'),
  # list.files(source_folder, pattern = 'RAP00000')
  list_of_source_files
)

# BAU(+)
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'RAP', 'POSSIBLE_LANDSCAPE_CONFIGURATION')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['enforced_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_RAP',
  source_folder,
  file.path(input_folder, 'enforced_conservation', 'Landscape_configuration_RAP'),
  # list.files(source_folder, pattern = 'RAP00000')
  list_of_source_files
)

# worst-case
source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'RAP', 'POSSIBLE_LANDSCAPE_CONFIGURATION')

list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['no_conservation']],
                                                 list.files(source_folder))

maps_info <- add_dataset(
  'landscape_configuration_RAP',
  source_folder,
  file.path(input_folder, 'no_conservation', 'Landscape_configuration_RAP'),
  # list.files(source_folder, pattern = 'RAP00000')
  list_of_source_files
)

# all three scenarios no probing dates: [FOLDERS PER SCENARIO]
# - targeted net forest scenarios (discrete scale) 
# PATH: outputs_(scenario-folder) > RAP > targeted_net_forest > RAP_tnf0.001
# BAU
maps_info <- add_dataset(
  'targeted_net_forest',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'targeted_net_forest'),
  file.path(input_folder, 'weak_conservation', 'Targeted_net_forest'),
  'RAP_tnf0.001'
)

# # BAU(+)
# maps_info <- add_dataset(
#   'targeted_net_forest',
#   file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'RAP', 'targeted_net_forest'),
#   file.path(input_folder, 'enforced_conservation', 'Targeted_net_forest'),
#   'RAP_tnf0.001'
# )
# 
# # worst-case
# maps_info <- add_dataset(
#   'targeted_net_forest',
#   file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'RAP', 'targeted_net_forest'),
#   file.path(input_folder, 'no_conservation', 'Targeted_net_forest'),
#   'RAP_tnf0.001'
# )

# - potential additional restricted areas BAU BAU(+) (discrete scale)
# PATH: outputs_(scenario-folder) > RAP > restricted_areas > RAP_restricted_areas.map
# BAU
maps_info <- add_dataset(
  'potential_restricted_areas',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'restricted_areas'),
  file.path(input_folder, 'weak_conservation', 'Potential_restricted_areas'),
  'RAP_restricted_areas.map'
)

# # BAU(+)
# maps_info <- add_dataset(
#   'potential_restricted_areas',
#   file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'RAP', 'restricted_areas'),
#   file.path(input_folder, 'enforced_conservation', 'Potential_restricted_areas'),
#   'RAP_restricted_areas.map'
# )

# mplc forest degradation/regeneration files (discrete scale)
# PATH: outputs_(scenario-folder) > LPB > FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration > forest_degradation_and_regeneration > mplcfdrn.001
if (local_degradation_simulated == TRUE) {
  # BAU
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_degradation_and_regeneration')
  
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_forest_degradation_and_regeneration',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'MPLC_forest_degradation_and_regeneration'),
    # list.files(source_folder, pattern = 'RAP00000')
    list_of_source_files
  )
  
  # BAU(+)
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_degradation_and_regeneration')
  
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['enforced_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_forest_degradation_and_regeneration',
    source_folder,
    file.path(input_folder, 'enforced_conservation', 'MPLC_forest_degradation_and_regeneration'),
    # list.files(source_folder, pattern = 'RAP00000')
    list_of_source_files
  )
  
  # worst-case
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'LPB', 'FOREST_PROBABILITY_MAPS_most_probable_landscape_configuration', 'forest_degradation_and_regeneration')
  
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['no_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_forest_degradation_and_regeneration',
    source_folder,
    file.path(input_folder, 'no_conservation', 'MPLC_forest_degradation_and_regeneration'),
    # list.files(source_folder, pattern = 'RAP00000')
    list_of_source_files
  )
}
#> MS2 additional IMPORT MAPS ####
# Attention: add additional scenario output enforced_conservation and no_conservation if required, the visualization is already automated ####
# Habitat analysis inputs

if (performed_habitat_analysis == TRUE) {
  filter_for_probing_dates_extended <- function(probing_dates, list_of_files){
    list_of_files[str_sub(list_of_files, start= -7, end= -5) %in% str_pad(probing_dates, width=3, pad='0')]
  }
  # MPLC
  # Resistance
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'resistance_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_mplc_resistance',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'resistances'),
    list_of_source_files
  )
  # Sources
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'sources_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_mplc_sources',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'sources'),
    list_of_source_files
  )
  # Grounds
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'grounds_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_mplc_grounds',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'grounds'),
    list_of_source_files
  )
  # Polygons
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'polygons_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_mplc_polygons',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'polygons'),
    list_of_source_files
  )
  # Points
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'points_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_mplc_points',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'points'),
    list_of_source_files
  )
  # RAP
  # Resistance
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'resistance_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_RAP_resistance',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'resistances'),
    list_of_source_files
  )
  # Sources
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'sources_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_RAP_sources',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'sources'),
    list_of_source_files
  )
  # Grounds
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'grounds_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_RAP_grounds',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'grounds'),
    list_of_source_files
  )
  # Polygons
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'polygons_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_RAP_polygons',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'polygons'),
    list_of_source_files
  )
  # Points
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'points_files_map')
  list_of_source_files <- filter_for_probing_dates_extended(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'habitat_analysis_RAP_points',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'points'),
    list_of_source_files
  )
}

if (performed_habitat_analysis == TRUE) {
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 'ecosystem_fragmentation')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'ecosystem_fragmentation_mplc',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'ecosystem_fragmentation'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 'ecosystem_fragmentation')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'ecosystem_fragmentation_RAP',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'ecosystem_fragmentation'),
    list_of_source_files
  )
}

### mplc
## Omniscape
# Omniscape - normalized
# Omniscape - cumulative
# Omiscape - flow
# Omniscape -transformed
if (performed_Omniscape_analysis_mplc == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'normalized_cumulative_current')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  maps_info <- add_dataset(
    'mplc_Omniscape_normalized',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'normalized_cumulative_current'),
    list_of_source_files
  )
  
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'cumulative_current')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_Omniscape_cumulative',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'cumulative_current'),
    list_of_source_files
  )
  
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'flow_potential')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_Omniscape_flow_potential',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential'),
    list_of_source_files,
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Omniscape_transformed', 'normalized_reclassified')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_Omniscape_transformed_normalized_reclassified',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified'),
    list_of_source_files,
  )
}


## Circuitscape
if (performed_Circuitscape_analysis_advanced_mplc == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'curmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  maps_info <- add_dataset(
    'mplc_Ciruitscape_curmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'curmap'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'voltmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'mplc_Ciruitscape_voltmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'voltmap'),
    list_of_source_files
  )
}

if (performed_Circuitscape_analysis_pairwise_mplc == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'cum_curmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  maps_info <- add_dataset(
    'mplc_Ciruitscape_cum_curmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'cum_curmap'),
    list_of_source_files
  )
}



### RAP
## Omniscape
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'normalized_cumulative_current')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'RAP_Omniscape_normalized',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'normalized_cumulative_current'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'cumulative_current')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  maps_info <- add_dataset(
    'RAP_Omniscape_cumulative',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'cumulative_current'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Omniscape_to_PCRaster', 'flow_potential')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'RAP_Omniscape_flow_potential',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'flow_potential'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Omniscape_transformed', 'normalized_reclassified')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'RAP_Omniscape_transformed_normalized_reclassified',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Omniscape_transformed', 'normalized_reclassified'),
    list_of_source_files,
  )
}


## Circuitscape
if (performed_Circuitscape_analysis_advanced_RAP == TRUE) {
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'curmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'RAP_Ciruitscape_curmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'curmap'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'voltmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  
  maps_info <- add_dataset(
    'RAP_Ciruitscape_voltmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'voltmap'),
    list_of_source_files
  )
}

if (performed_Circuitscape_analysis_pairwise_RAP == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'Circuitscape_to_PCRaster', 'cum_curmap')
  list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['weak_conservation']],
                                                   list.files(source_folder))
  maps_info <- add_dataset(
    'RAP_Ciruitscape_cum_curmap',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'cum_curmap'),
    list_of_source_files
  )
}


# averaged maps
if (user_defined_averaging_of_habitat_analysis_results_applied == TRUE) {
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'LPB', 'HABITAT_ANALYSIS_MPLC', 
                             'OUTPUTS', 'LPB-RAP_averaged_results')
  list_of_source_files <- list.files(source_folder)
  
  maps_info <- add_dataset(
    'LPBRAP_averaged_results_mplc',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_MPLC', 'LPB-RAP_averaged_results'),
    list_of_source_files
  )
  
  source_folder <- file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'HABITAT_ANALYSIS_RAP', 
                             'OUTPUTS', 'LPB-RAP_averaged_results')
  list_of_source_files <- list.files(source_folder)
  
  maps_info <- add_dataset(
    'LPBRAP_averaged_results_RAP',
    source_folder,
    file.path(input_folder, 'weak_conservation', 'HABITAT_ANALYSIS_RAP', 'LPB-RAP_averaged_results'),
    list_of_source_files
  )

}



#>>> automated on UNIX systems: copy files to .tif ####
### ATTENTION WINDOWS USERS: THIS IS NOT APPLICABLE ON WINDOWS OS, 
### you need to transform maps to tifs manually in a GIS #####
### AND PLACE THEM IN THE PROVIDED FOLDER STRUCTURE #####

packageVersion('raster')

maps_info %>%
  mutate(file_extension = str_sub(file_names, -3)) %>%
  filter(file_extension != 'xml') %>%
  rowwise() %>%
  do({
    print(paste('converting files for', .$dataset_name))
    
    # create copy-to paths 
    dir.create(.$to_folder, showWarnings = TRUE, recursive = TRUE)
    
    if(version$os != 'mingw32') {
      
      raster_file <- raster(file.path(.$from_folder, .$file_names))
      
      file_name_no_extension <- str_sub(.$file_names, 1, nchar(.$file_names) - 4)
      
      if(.$file_extension != 'map') {
        output_file_name <- paste(file_name_no_extension, .$file_extension, sep = '_')
      } else {
        output_file_name <- file_name_no_extension
      }
      
      # CODE CRS ####
      crs(raster_file) <- ("+init=epsg:32717 +datum=WGS84")
      # write the raster
      writeRaster(raster_file, file.path(.$to_folder, output_file_name), format = "GTiff", overwrite=TRUE, options="COMPRESS=LZW")
    }
    
    tibble()
  }
  )



# import singular files as projected raster (DK + SH) ---------------------------------------------------------------------------------------------------------------------------------------------
import_folder <- input_folder



# 1 x net forest
raster_map_net_forest <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Net_forest'), full.names = TRUE))
raster::crs(raster_map_net_forest) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 1 x AGB initial
raster_map_AGB_initial <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'AGB_initial'), full.names = TRUE))
raster::crs(raster_map_AGB_initial) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 5 x AGB maximum undisturbed climate periods 
raster_maps_AGB_max_climate <- tibble(
  file_location = list.files(file.path(import_folder, 'deterministic', 'AGB_maximum_undisturbed'), full.names = TRUE),
  raster_files = purrr::map(file_location, raster)
) %>%
  mutate(period = str_sub(file_location, -19, -11)) %>%
  dplyr::select(!file_location) 

# 1 x null mask
raster_map_null_mask <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Null_mask'), full.names = TRUE))
raster::crs(raster_map_null_mask) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 1 x DEM
raster_map_dem <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'DEM'), full.names = TRUE))
raster::crs(raster_map_dem) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 1 x Freshwater
raster_map_freshwater <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Freshwater'), full.names = TRUE))
raster::crs(raster_map_freshwater) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 1 x LULC initial
raster_map_initial_LULC <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial'), full.names = TRUE))
raster::crs(raster_map_initial_LULC) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 3 x LULC simulated
raster_map_LULC_simulated_BAU <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial_simulated_weak_conservation'), full.names = TRUE))
raster::crs(raster_map_LULC_simulated_BAU) <- paste("EPSG:", user_defined_EPSG, sep = '')

# raster_map_LULC_simulated_BAUplus <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial_simulated_enforced_conservation'), full.names = TRUE))
# raster::crs(raster_map_LULC_simulated_BAUplus) <- paste("EPSG:", user_defined_EPSG, sep = '')
# 
# raster_map_LULC_simulated_worst_case <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial_worst-case'), full.names = TRUE))
# raster::crs(raster_map_LULC_simulated_worst_case) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 5 x PNV
file_contents = list.files(file.path(import_folder, 'deterministic', 'PNV'), full.names = TRUE)
purrr::map(file_contents, raster)

raster_maps_PNV <- tibble(
  file_location = list.files(file.path(import_folder, 'deterministic', 'PNV'), full.names = TRUE),
  raster_files = purrr::map(file_location, raster)
) %>%
  mutate(period = str_sub(file_location, -19, -11)) %>%
  dplyr::select(!file_location) 


# 9 + 2 Population 
folder_content <- list.files(file.path(import_folder, 'deterministic', 'population'), full.names = TRUE)

# exclude directories
folder_content <- folder_content[!file.info(folder_content)$isdir]

raster_maps_population <- tibble(
  file_location = folder_content,
  raster_files = purrr::map(folder_content, raster)
) %>%
  mutate(year = str_sub(file_location, -14, -11)) %>%
  dplyr::select(!file_location) 

raster_map_initial_pop_BAUs <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Population', 'initial_population_BAUs'), full.names = TRUE))
raster::crs(raster_map_initial_pop_BAUs) <- paste("EPSG:", user_defined_EPSG, sep = '')

# raster_map_initial_pop_worst_case <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Population', 'initial_population_worst-case'), full.names = TRUE))
# raster::crs(raster_map_initial_pop_worst_case) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 1 x Restricted areas
raster_map_restricted_areas <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Restricted_areas'), full.names = TRUE))
raster::crs(raster_map_restricted_areas) <- paste("EPSG:", user_defined_EPSG, sep = '')

# 4(-8) x Tiles
raster_maps_tiles <- tibble(
  file_location = list.files(file.path(import_folder, 'deterministic', 'Tiles'), full.names = TRUE),
  raster_files = purrr::map(file_location, raster)
) %>%
  mutate(tile = str_sub(file_location, -16, -11)) %>% 
  dplyr::select(!file_location) 

# Streets
raster_map_streets <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Streets'), full.names = TRUE))
raster::crs(raster_map_streets) <- paste("EPSG:", user_defined_EPSG, sep = '')

# Cities
raster_map_cities <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Cities'), full.names = TRUE))
raster::crs(raster_map_cities) <- paste("EPSG:", user_defined_EPSG, sep = '')

# Settlements
raster_map_settlements <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Settlements'), full.names = TRUE))
raster::crs(raster_map_settlements) <- paste("EPSG:", user_defined_EPSG, sep = '')

# Model internal slope
raster_map_model_internal_slope_in_percent <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Slope'), full.names = TRUE))
raster::crs(raster_map_model_internal_slope_in_percent) <- paste("EPSG:", user_defined_EPSG, sep = '')


### AGB and PNV import for gridded maps
# AGB
AGB_rasters_climate_locations <- list.files(file.path(import_folder, 'deterministic', 'AGB_maximum_undisturbed'), full.names = TRUE)
AGB_rasters_climate_ids <- str_sub(AGB_rasters_climate_locations, -19, -11)
AGB_rasters_locations <- c(list.files(file.path(import_folder, 'deterministic', 'AGB_initial'), full.names = TRUE),
                           AGB_rasters_climate_locations)
AGB_rasters_ids <- c('Initial', AGB_rasters_climate_ids)

import_one_raster <- function(raster_location, raster_id) {
  raster_i <- raster(raster_location)
  raster_i_df <- as.data.frame(raster_i, xy = TRUE) %>%
    drop_na %>%
    rename(value = 3) %>%
    mutate(raster_id = raster_id)
  raster_i_df
}

# PNV
PNV_rasters_climate_locations <- list.files(file.path(import_folder, 'deterministic', 'PNV'), full.names = TRUE)
PNV_rasters_climate_ids <- str_sub(PNV_rasters_climate_locations, -19, -11)

### import LPB und RAP for gridded plots
# LPB 
LULCC_mplc_BAU_locations <- list.files(file.path(import_folder, 'BAU', 'Landscape_configuration_mplc'), full.names = TRUE)
LULCC_mplc_BAU_ids <- str_sub(LULCC_mplc_BAU_locations, -7, -5)

LULCC_mplc_BAUplus_locations <- list.files(file.path(import_folder, 'BAU(+)', 'Landscape_configuration_mplc'), full.names = TRUE)
LULCC_mplc_BAUplus_ids <- str_sub(LULCC_mplc_BAUplus_locations, -7, -5)

LULCC_mplc_worst_case_locations <- list.files(file.path(import_folder, 'worst_case', 'Landscape_configuration_mplc'), full.names = TRUE)
LULCC_mplc_worst_case_ids <- str_sub(LULCC_mplc_BAU_locations, -7, -5)

LULCC_RAP_BAU_locations <- list.files(file.path(import_folder, 'BAU', 'Landscape_configuration_RAP'), full.names = TRUE)
LULCC_RAP_BAU_ids <- str_sub(LULCC_RAP_BAU_locations, -7, -5)

LULCC_RAP_BAUplus_locations <- list.files(file.path(import_folder, 'BAU(+)', 'Landscape_configuration_RAP'), full.names = TRUE)
LULCC_RAP_BAUplus_ids <- str_sub(LULCC_RAP_BAUplus_locations, -7, -5)

LULCC_RAP_worst_case_locations <- list.files(file.path(import_folder, 'worst_case', 'Landscape_configuration_RAP'), full.names = TRUE)
LULCC_RAP_worst_case_ids <- str_sub(LULCC_RAP_BAU_locations, -7, -5)

#> MS2 additional IMPORT TIDY DATA ####

# COPY FILES
if (model_stage == 'MS2') {
  scenarios <- tibble(
    scenario_name = c('weak_conservation'),
    scenario_name_output = c('weak conservation')
  ) %>%
    mutate(scenario_output_folder = file.path(
      '..',
      paste(main_model_folder),
      paste(demand_configuration_outputs_folder),
      paste('outputs', scenario_name, sep = '_')
    ))
}


### >>> activate copy files ####################################################
# now create import folder if it doesn't exist
if (model_stage == 'MS2') {
  import_folder <- file.path('R_tidy_data_input')
  if (!dir.exists(import_folder)){
    dir.create(import_folder)
  }
  
  # copy
  files_to_copy = scenarios %>%
    pmap(~ list.files(..3, pattern = '.csv', recursive = TRUE, full.names = TRUE)) %>%
    flatten()
  # only include tidy data (i.e. not log files)
  files_to_copy <- files_to_copy[str_detect(files_to_copy, 'tidy_data')]
  targetdir <- import_folder
  for (file_to_copy in files_to_copy) {
    file.copy(from=file_to_copy, to=targetdir, overwrite = TRUE)
  }
  
  # IMPORT DATA INTO SCRIPT
  # get all file names of data sets
  input_data <- tibble(file_name = list.files(import_folder, pattern = '.csv')) %>%
    filter(
      !file_name %in% c(
        # note here the universal files:
        'RAP_LUTs_lookup_table.csv',
        'mplc_LUTs_lookup_table.csv',
        'LPB_correction_step_transition_matrix_weak_conservation.csv'
      )
    ) 

  ## separate data set names and scenario names
  input_data <- input_data %>%
    mutate(
      scenario_name_start = str_locate(file_name, paste(scenarios$scenario_name, collapse = '|')),
      data_set_name = str_sub(file_name, 1, scenario_name_start[,1] - 2),
      scenario = str_sub(file_name, scenario_name_start[,1], scenario_name_start[,2])
    ) %>%
    dplyr::select(-scenario_name_start)
  
  ## load content of files 
  input_data <- input_data %>%
    mutate(file_contents = purrr::map(file_name, ~read_csv(file.path(import_folder, .)))) %>%
    mutate(file_contents = map2(scenario, file_contents, ~ tibble(.y, scenario = .x))) %>% # add scenario name as column
    dplyr::select(-file_name, -scenario) 
  
  # remove empty data sets
  input_data <- input_data %>%
    rowwise() %>%
    mutate(dataset_rows = nrow(file_contents)) %>%
    filter(dataset_rows > 0)
  
  # bind data sets 
  input_data <- input_data %>%
    group_by(data_set_name) %>%
    nest() %>%
    mutate(file_contents = purrr::map(data, ~bind_rows(.$file_contents))) %>%
    dplyr::select(-data) 
  
  # add LUT names to data sets that have a column 'LUT_code'
  input_data <- input_data %>%
    mutate(
      file_contents = map_if(file_contents, ~'LUT_code' %in% colnames(.), ~left_join(., RAP_LUTs_lookup_table))
    )
  
  # add years to all data sets 
  time_steps_years_lookup_table <- input_data %>%
    filter(data_set_name == 'LPB_scenario_years') %>%
    pull
  
  time_steps_years_lookup_table[[1]]$year_date <- ymd(paste(time_steps_years_lookup_table[[1]]$year, 12, 31, sep = '-'))
  
  input_data <- input_data %>%
    filter(data_set_name != 'LPB_scenario_years')
  
  input_data <- input_data %>%
    mutate(
      file_contents = purrr::map(file_contents, ~left_join(., time_steps_years_lookup_table[[1]]))
    )
  
  # add scenario output name
  input_data <- input_data %>%
    mutate(file_contents = map_if(file_contents, ~'scenario' %in% colnames(.), ~left_join(., scenarios, by = join_by(scenario == scenario_name))))
  
  # # append peak demands year ####
  # if (time_series_input == 'external') {
  #   input_data <- input_data %>%
  #     mutate(
  #       file_contents = map_if(file_contents, ~'scenario' %in% colnames(.), ~left_join(., peak_demands_year_scenarios))
  #     )
  # }
  
  # transform to pivot wider
  input_data <- pivot_wider(input_data, names_from = data_set_name, values_from = file_contents)
}

#> MS2 additional IMPORT PRESENCE DATA ####
find_up <- function(path = getwd(), pattern, maxheight = Inf, first = TRUE, ...) {
  level <- 0L
  lf <- NULL
  while (level <= maxheight) {
    lf <- c(lf, list.files(path, pattern, ...))
    if (first && length(lf) || path == dirname(path))
      break
    level <- level + 1L
    path <- dirname(path)
  }
  lf
}
# find the folder for common inputs
umbrella_species_presence_data_folder <- find_up(pattern = 'presence_data', full.names = TRUE)
# find own data
umbrella_species_presence_data_file <- file.path(umbrella_species_presence_data_folder, 'umbrella_species_presence.xlsx')
umbrella_species_presence_data <- st_read(umbrella_species_presence_data_file)
umbrella_species_presence_data <- st_as_sf(umbrella_species_presence_data,
                                           coords = c("longitude", "latitude"),
                                           crs= "+proj=longlat +datum=WGS84 +ellps=WGS84 +towgs84=0,0,0")
umbrella_species_presence_data <- st_transform(umbrella_species_presence_data,
                                               user_defined_EPSG)
#find GBIF data
umbrella_species_presence_data_file_GBIF <- file.path(umbrella_species_presence_data_folder, 'umbrella_species_presence_GBIF.xlsx')
umbrella_species_presence_data_GBIF <- st_read(umbrella_species_presence_data_file_GBIF)
umbrella_species_presence_data_GBIF <- st_as_sf(umbrella_species_presence_data_GBIF,
                                           coords = c("decimalLongitude", "decimalLatitude"),
                                           crs= "+proj=longlat +datum=WGS84 +ellps=WGS84 +towgs84=0,0,0")
umbrella_species_presence_data_GBIF <- st_transform(umbrella_species_presence_data_GBIF,
                                               user_defined_EPSG)

# create plots (SH + DK)--------------------------------------------------------------------------------------------------------------------------------------------

### > preparations (SH + DK): #################################################################################################################

# set plots margins to give space for rotate x labels, the x axis title and the caption 
# (bottom , left, top, right margins => default is c(5,4,4,2) + 0.1)
op <- par(mar = c(8, 4, 4, 2) + 0.1)


# create theme_LPB_RAP: adapts the basic ggplot theme to user defined LPB-RAP settings
theme_LPB_RAP <- ggplot_base_theme +
                 ggplot2::theme(plot.title = element_text(family = user_defined_font, 
                                                          size = user_defined_fontsize, 
                                                          face = user_defined_title_face, 
                                                          hjust = user_defined_hjust,
                                                          colour = user_defined_baseline_color),
                                 plot.subtitle = element_text(family = user_defined_font, 
                                                              size = user_defined_fontsize, 
                                                              face = user_defined_subtitle_face, 
                                                              hjust = user_defined_hjust,
                                                              colour = user_defined_baseline_color),
                                plot.caption = element_text(family = user_defined_font, 
                                                             size = user_defined_fontsize - user_defined_fontsize_factor, 
                                                             face = user_defined_other_face, 
                                                             hjust = user_defined_hjust,
                                                             colour = user_defined_baseline_color,
                                                            line = 7),
                                axis.title.x = element_text(family = user_defined_font, 
                                                            size = user_defined_fontsize, 
                                                            face = user_defined_other_face, 
                                                            hjust = user_defined_hjust,
                                                            colour = user_defined_baseline_color,
                                                            line = 5),
                                axis.title.y = element_text(family = user_defined_font, 
                                                            size = user_defined_fontsize, 
                                                            face = user_defined_other_face, 
                                                            hjust = user_defined_hjust,
                                                            colour = user_defined_baseline_color),
                                axis.text.x = element_text(family = user_defined_font, 
                                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                                           colour = user_defined_baseline_color),
                                axis.text.y = element_text(family = user_defined_font, 
                                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                                           colour = user_defined_baseline_color),
                                legend.title = element_text(family = user_defined_font, 
                                                            size = user_defined_fontsize,
                                                            face = user_defined_title_face,
                                                            colour = user_defined_baseline_color),
                                legend.text = element_text(family = user_defined_font, 
                                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                                           colour = user_defined_baseline_color),
                                strip.background = element_rect(fill=user_defined_baseline_color))

# make climate periods accessible for every possible plotting year
climate_periods_complete <- climate_periods %>%
  complete(start_date = full_seq(c(initial_simulation_year_BAUs, last_simulation_year), 1)) %>%  
  rename(year = start_date) %>%
  fill(description)  

# create subtitle prefix
subtitle_prefix <- paste(country, region, baseline_scenario)

# create caption
caption_landscape <-  paste("LPB-RAP simulated landscape contains", landscape_area, landscape_area_unit)

# create connection raster LUTs to LUT_names
LUT_colors_lookup <- LUT_colors %>%
  left_join(RAP_LUTs_lookup_table) %>%
  pull(colors, LUT_name)


### >>> MAPS VISUALIZATION: ####################################################
# > Terrain: ###################################################################
# Slope (degrees) ####################################################################
plot_title <- "Terrain - Slope [degrees]"
legend_title <- "Slope [degrees]"

dem <- raster_map_dem

# create slope and hillshade
slope = raster::terrain(dem, opt='slope', unit="degrees", neighbors = 8) # neighbors 8 computes slope according to Horn(1981)

dem_spdf <- as(dem, "SpatialPixelsDataFrame")
dem_spdf <- as.data.frame(dem_spdf)
colnames(dem_spdf) <- c("value", "x", "y")

slope_spdf <- as(slope, "SpatialPixelsDataFrame")
slope_spdf <- as.data.frame(slope_spdf) 
colnames(slope_spdf) <- c("value", "x", "y")

aspect = terrain(dem, opt='aspect')
hill = hillShade(slope, aspect, 40, 270)
hill_spdf <- as(hill, "SpatialPixelsDataFrame")
hill_spdf <- as.data.frame(hill_spdf)
colnames(hill_spdf) <- c("value", "x", "y")

# save hillshade as a layer to be used in the subsequent plots:
dem_hillshade_layer <- geom_raster(data = hill_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = FALSE)

pl <- ggplot()
pl <- pl + geom_raster(data = slope_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = TRUE) 
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
pl
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# Slope (percent) ####################################################################
plot_title <- "Terrain - Slope [model internal slope, percent]"
legend_title <- "Slope [%]"

slope <- raster_map_model_internal_slope_in_percent

raster_to_process <- slope

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) %>%
  filter(value < 2) %>%
  mutate(value = value * 100)

pl <- ggplot()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = value), alpha = 1, show.legend = TRUE) 
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)

# safe here for use in overview map
plot_slope_percent <- pl

# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
pl
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# Slope user defined categories (percent) ####################################################################
#user_defined_slope_category_breaks = c(-0.1, 0.05, 0.15, 0.30, 0.45, 2) # note segments +1, 2 -> 200% maximum % value
#user_defined_slope_category_names = c("0 - 5", ">5 - 15", ">15 - 30", ">30 - 45", ">45")

plot_title <- "Terrain - Slope [user-defined categories, percent]"
legend_title <- "Slope categories [%]"

slope <- raster_map_model_internal_slope_in_percent

raster_to_process <- slope

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
  drop_na %>%
  rename(value = 3) %>%
  filter(value < 2) 

raster_dataframe <- raster_dataframe %>%
  mutate(slope_categories = cut(value, breaks = user_defined_slope_category_breaks)) %>%
  drop_na
  # mutate(slope_categories = cut_number(value, 5)) # oder cut_number(value, 5)) für gleich viele Beobachtungen, cut_interval(value, 5)


pl <- ggplot()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = slope_categories), alpha = 1, show.legend = TRUE) 
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum,
                                labels = user_defined_slope_category_names)
pl <- pl + coord_sf(crs = user_defined_EPSG)

# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
pl
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# Hillshade ####################################################################
plot_title <- "Terrain - Hillshade"
legend_title <- "Hillshade"

dem <- raster_map_dem

# create slope and hillshade
slope = raster::terrain(dem, opt='slope')
aspect = raster::terrain(dem, opt='aspect')
hill = raster::hillShade(slope, aspect, 40, 270)

dem_spdf <- as(dem, "SpatialPixelsDataFrame")
dem_spdf <- as.data.frame(dem_spdf)
colnames(dem_spdf) <- c("value", "x", "y")

hill_spdf <- as(hill, "SpatialPixelsDataFrame")
hill_spdf <- as.data.frame(hill_spdf)
colnames(hill_spdf) <- c("value", "x", "y")

# save hillshade as a layer to be used in the subsequent plots:
dem_hillshade_layer <- geom_raster(data = hill_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = FALSE)

pl <- ggplot()
pl <- pl + geom_raster(data = hill_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = TRUE) 
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# Elevation ####################################################################
plot_title <- "Terrain - Elevation"
altitude_title <- "Altitude [m]"

dem <- raster_map_dem

# create slope and hillshade
slope = raster::terrain(dem, opt='slope')
aspect = raster::terrain(dem, opt='aspect')
hill = raster::hillShade(slope, aspect, 40, 270)

dem_spdf <- as(dem, "SpatialPixelsDataFrame")
dem_spdf <- as.data.frame(dem_spdf)
colnames(dem_spdf) <- c("value", "x", "y")

hill_spdf <- as(hill, "SpatialPixelsDataFrame")
hill_spdf <- as.data.frame(hill_spdf)
colnames(hill_spdf) <- c("value", "x", "y")

pl <- ggplot()
pl <- pl + geom_raster(data = hill_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = FALSE) 
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
pl <- pl + geom_raster(data = dem_spdf, aes(x = x, y = y, fill = value), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = altitude_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### Surface freshwater distribution (discrete scale) ###########################
plot_title <- "Terrain - Surface freshwater distribution"
legend_title <- "Aspect"

raster_to_process <- raster_map_freshwater

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# save for subsequent combination plot
freshwater_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = "Surface freshwater areas"), alpha = 0.75)

pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = "Surface freshwater areas"), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_manual(values = c("steelblue"))
pl <- pl + coord_sf(crs = user_defined_EPSG)

# safe here for use in overview map
plot_surface_freshwater <- pl


# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



### > Population #################################################################
legend_title <- "Population"

raster_maps_population %>%
  rowwise() %>%
  do({
    print(paste('plotting for', .$year))
    plot_title <- paste('Population', .$year)
    raster_to_process <- .$raster_files
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot()  
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value),
                           alpha = 0.75,
                           show.legend = TRUE) 
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum)
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    caption = caption_landscape,
                    fill = legend_title)
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    
    tibble()
  })

# Population initial interpolated BAU
plot_title <- paste("Population interpolated for", initial_simulation_year_BAUs)
legend_title <- "Population"

raster_to_process <- raster_map_initial_pop_BAUs

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

pl <- ggplot()
pl <- pl + dem_hillshade_layer 
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = value), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = subtitle_prefix,
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# # Population initial interpolated worst-case
# plot_title <- paste("Population interpolated for", initial_simulation_year_worst_case)
# legend_title <- "Population"
# 
# raster_to_process <- raster_map_initial_pop_worst_case
# 
# raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
#   drop_na %>%
#   rename(value = 3) 
# 
# pl <- ggplot()
# pl <- pl + dem_hillshade_layer 
# pl <- pl + new_scale_fill()
# pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = value), alpha = 0.75, show.legend = TRUE)
# pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
# pl <- pl + coord_sf(crs = user_defined_EPSG)
# # add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.title.x = element_blank(),
#                  axis.title.y = element_blank())
# pl <- pl + theme(panel.grid.minor.x = element_blank(),
#                  panel.grid.minor.y = element_blank())
# pl <- pl + labs(title = plot_title,
#                 subtitle = subtitle_prefix,
#                 caption = caption_landscape,
#                 fill = legend_title)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### > Restricted areas map (discrete scale) ######################################
plot_title <- "Restricted areas"
legend_title <- "Aspect"

raster_to_process <- raster_map_restricted_areas %>%
  as.data.frame(xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# save for subsequent combination plot
restricted_areas_layer <- geom_raster(data = raster_to_process, aes(x = x, y = y, fill = "Restricted areas"), alpha = 0.5, show.legend = TRUE)

pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_to_process, aes(x = x, y = y, fill = "Restricted areas"), alpha = 0.75, show.legend = TRUE)
#pl <- pl + geom_raster(data = rasters_combined, aes(x = x, y = y, fill = class_description), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)

# safe here for use in overview map
plot_restricted_areas <- pl


# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### > Net Forest (discrete scale) ######################################
plot_title <- "Net forest"
legend_title <- "Aspect"

raster_to_process <- raster_map_net_forest %>%
  as.data.frame(xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# save for subsequent combination plot
net_forest_layer <- geom_raster(data = raster_to_process, aes(x = x, y = y, fill = "Net forest"), alpha = 0.5, show.legend = TRUE)

pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_to_process, aes(x = x, y = y, fill = "Net forest"), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### > PNV maps ##############################################################
legend_title <- "PNV in a forest succession context"

PNV <- tibble(
  class = c(0, 1, 2, 3),
  class_description = c("not applicable", "herbaceous vegetation", "shrubs", "forest")
)

raster_maps_PNV %>%
  rowwise() %>%
  do({
    print(paste('plotting for', .$period))
    plot_title <- paste('Potential natural vegetation (PNV)', .$period)
    raster_to_process <- .$raster_files
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
      drop_na %>%
      rename(value = 3) %>%
      full_join(PNV, by = c("value" = "class")) %>%
      mutate(class_description = fct_relevel(class_description, c("not applicable", "herbaceous vegetation", "shrubs", "forest")))
    
    pl <- ggplot()  
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = class_description),
                           alpha = 0.75,
                           show.legend = TRUE) 
    pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    caption = caption_landscape,
                    fill = legend_title)
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    
    tibble()
  })

### > PNV maps (gridded) ##################################################
plot_title <- "Potential natural vegetation (PNV) per climate period"
legend_title <- "PNV in a forest succession context"

PNV <- tibble(
  class = c(0, 1, 2, 3),
  class_description = c("not applicable", "herbaceous vegetation", "shrubs", "forest")
)

PNV_dfs <- map2_dfr(PNV_rasters_climate_locations, PNV_rasters_climate_ids, import_one_raster) %>%
  full_join(PNV, by = c("value" = "class")) %>%
  mutate(class_description = fct_relevel(class_description, c("not applicable", "herbaceous vegetation", "shrubs", "forest")))

pl <- ggplot(PNV_dfs)
pl <- pl + geom_raster(aes(x = x, y = y, fill = class_description)) 
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + facet_wrap(~raster_id)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = subtitle_prefix,
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



###> Maximum undisturbed AGB (continuous scale) ############################
legend_title <- "Potential maximum undisturbed AGB per ha"

raster_maps_AGB_max_climate %>%
  rowwise() %>%
  do({
    print(paste('plotting for', .$period))
    plot_title <- paste('Potential maximum undisturbed AGB', .$period)
    raster_to_process <- .$raster_files
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot()  
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value),
                           alpha = 0.75,
                           show.legend = TRUE) 
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum)
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    caption = caption_landscape,
                    fill = legend_title)
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    
    tibble()
  })

###> Maximum undisturbed AGB (continuous scale) and initial AGB (gridded) ######
plot_title <- "Potential maximum undisturbed AGB per ha and initial AGB"
legend_title <- "AGB [Mg ha-1]"

AGB_dfs <- map2_dfr(AGB_rasters_locations, AGB_rasters_ids, import_one_raster)

pl <- ggplot(AGB_dfs)
pl <- pl + geom_raster(aes(x = x, y = y, fill = value)) 
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + facet_wrap(~raster_id)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = subtitle_prefix,
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



###> Initial AGB (continuous scale) ########################################
plot_title <- "Initial AGB"
legend_title <- "AGB Mg ha-1"

raster_to_process <- raster_map_AGB_initial

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

pl <- ggplot()
pl <- pl + dem_hillshade_layer 
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = value), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


###> Tiles (discrete scale) ################################################
plot_title <- paste(project, "tiles (sampled sub study areas)")
legend_title <- "Tiles"

modify_one_raster_file <- function(input_tibble) {
  output_df <- as.data.frame(input_tibble$raster_files[[1]], xy = TRUE) %>%
    drop_na %>%
    rename(value = 3)
  output_df$tile = input_tibble$tile
  return(output_df)
}

raster_dataframe <- raster_maps_tiles %>%
  split(.$tile) %>%
  map_dfr(modify_one_raster_file) %>%
  left_join(tiles_description)

# save for subsequent combination plot
tiles_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = tile_name), alpha = 0.75)

            
pl <- ggplot()
pl <- pl + dem_hillshade_layer 
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = tile_name), alpha = 0.75, show.legend = TRUE)
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape,
                fill = legend_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



### > LPB initial LULC ###########################################################
plot_title <- "LPB initial LULC"
altitude_title <- "Altitude"
LUT_title <- "Land Use Land Cover Types"

raster_to_process <- raster_map_initial_LULC

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) %>%
  mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table)

# save for subsequent combination plot
initial_LULC_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = LUT_name), alpha = 0.75, show.legend = TRUE) 

pl <- ggplot()  
pl <- pl + dem_hillshade_layer
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe,
                       aes(x = x, y = y, fill = LUT_name),
                       alpha = 0.75,
                       show.legend = TRUE) 
pl <- pl + scale_fill_manual(values = LUT_colors_lookup,
                             limits = force)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())

# safe here for use in overview map
plot_initial_LULC <- pl


pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region, initial_simulation_year_BAUs),
                caption = caption_landscape,
                fill = LUT_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### > Simulated initial LULC BAU, BAU(+), worst-case (discrete scale) ################################
# BAU ######
plot_title <- "LPB simulated LULC after correction step weak conservation"
LUT_title <- "Land Use Types"

raster_to_process <- raster_map_LULC_simulated_BAU

raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) %>%
  mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table)

pl <- ggplot()  
pl <- pl + dem_hillshade_layer
pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe,
                       aes(x = x, y = y, fill = LUT_name),
                       alpha = 0.75,
                       show.legend = TRUE) 
pl <- pl + scale_fill_manual(values = LUT_colors_lookup,
                             limits = force)
pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + labs(title = plot_title,
                subtitle = paste(subtitle_prefix, initial_simulation_year_BAUs),
                caption = caption_landscape,
                fill = LUT_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# ### BAU(+) ####
# plot_title <- "LPB simulated LULC after correction step enforced conservation"
# LUT_title <- "Land Use Types"
# 
# raster_to_process <- raster_map_LULC_simulated_BAUplus
# 
# raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
#   drop_na %>%
#   rename(value = 3) %>%
#   mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
#   left_join(RAP_LUTs_lookup_table)
# 
# pl <- ggplot()  
# pl <- pl + dem_hillshade_layer
# pl <- pl + new_scale_fill()
# pl <- pl + geom_raster(data = raster_dataframe,
#                        aes(x = x, y = y, fill = LUT_name),
#                        alpha = 0.75,
#                        show.legend = TRUE) 
# pl <- pl + scale_fill_manual(values = LUT_colors_lookup,
#                              limits = force)
# pl <- pl + coord_sf(crs = user_defined_EPSG)
# # add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.title.x = element_blank(),
#                  axis.title.y = element_blank())
# pl <- pl + theme(panel.grid.minor.x = element_blank(),
#                  panel.grid.minor.y = element_blank())
# pl <- pl + labs(title = plot_title,
#                 subtitle = paste(subtitle_prefix, initial_simulation_year_BAUs),
#                 caption = caption_landscape,
#                 fill = LUT_title)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
# 
# ### worst-case #################################################################
# plot_title <- "LPB simulated LULC for no conservation"
# LUT_title <- "Land Use Types"
# 
# raster_to_process <- raster_map_LULC_simulated_worst_case
# 
# raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
#   drop_na %>%
#   rename(value = 3) %>%
#   mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
#   left_join(RAP_LUTs_lookup_table)
# 
# pl <- ggplot()  
# pl <- pl + dem_hillshade_layer
# pl <- pl + new_scale_fill()
# pl <- pl + geom_raster(data = raster_dataframe,
#                        aes(x = x, y = y, fill = LUT_name),
#                        alpha = 0.75,
#                        show.legend = TRUE) 
# pl <- pl + scale_fill_manual(values = LUT_colors_lookup,
#                              limits = force)
# pl <- pl + coord_sf(crs = user_defined_EPSG)
# # add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.title.x = element_blank(),
#                  axis.title.y = element_blank())
# pl <- pl + theme(panel.grid.minor.x = element_blank(),
#                  panel.grid.minor.y = element_blank())
# pl <- pl + labs(title = plot_title,
#                 subtitle = paste(subtitle_prefix, initial_simulation_year_worst_case),
#                 caption = caption_landscape,
#                 fill = LUT_title)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### > Overview plots: #########################################################

# ## Study area, Country and Region ##############################################
# rosm::osm.types()
# 
# plot_title <- "Study area"
# 
# # # world country context
# # world_country_dataframe <- ne_countries(scale = "medium", type = "map_units", returnclass = "sf")
# # world_country_layer <- geom_sf(data = world_country_dataframe)
# # 
# # sf::sf_use_s2(FALSE)
# # world_country_cropped <- st_crop(world_country_dataframe,
# #                                        xmin = -95,
# #                                        xmax = -70,
# #                                        ymin = -6,
# #                                        ymax = 2)
# # world_country_cropped
# # world_country_cropped_layer <- geom_sf(data = world_country_cropped, 
# #                                        color = user_defined_baseline_color,
# #                                        fill = "antiquewhite", 
# #                                        inherit.aes = FALSE)
# 
# # country states context
# country_states_dataframe <- ne_states(country = country, returnclass = "sf") 
# country_states_layer <- geom_sf(data = country_states_dataframe, 
#                                 fill = "white", 
#                                 inherit.aes = FALSE)
# 
# # study region
# raster_null_mask_dataframe <- as.data.frame(raster_map_null_mask, xy = TRUE) %>% 
#   drop_na %>%
#   rename (value = static_null_mask_input)
# 
# # plot
# pl <- ggplot(country_states_dataframe)
# pl <- pl + ggspatial::annotation_map_tile(data = country_states_dataframe, 
#                                           type = "http://a.tile.stamen.com/toner/${z}/${x}/${y}.png",
#                                           zoomin = -2)
# pl <- pl + country_states_layer 
# pl <- pl + geom_raster(data = raster_null_mask_dataframe,
#                        aes(x = x, y = y, fill = "firebrick"),
#                        alpha = 0.5,
#                        show.legend = FALSE,
#                        inherit.aes = FALSE)
# pl <- pl + coord_sf(crs = user_defined_EPSG, 
#                     expand = FALSE)
# # add attributes, themes and labs
# pl <- pl + ggspatial::annotation_scale(location = "bl",
#                                        bar_cols = c(user_defined_baseline_color, "white"),
#                                        text_family = user_defined_font)
# pl <- pl + ggspatial::annotation_north_arrow(location = "bl",
#                                              which_north = "true",
#                                              pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
#                                              pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
#                                              style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
#                                                                                                line_col = user_defined_baseline_color,
#                                                                                                text_family = user_defined_font))
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.title.x = element_blank(),
#                  axis.title.y = element_blank())
# pl <- pl + theme(panel.grid.minor.x = element_blank(),
#                  panel.grid.minor.y = element_blank())
# 
# # safe here for use in overview map
# plot_study_area <- pl
# 
# pl <- pl + labs(title = plot_title,
#                 subtitle = paste(country, region),
#                 caption = "Regional study area in the country context | Sources basemaps: rnaturalearth, OSM/Stamen")
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
# 


# Anthropogenic features #######################################################
plot_title <- paste("Anthropogenic features (spatial information) applied for", initial_simulation_year_BAUs)

# streets
raster_to_process_streets <- raster_map_streets

raster_dataframe_streets <- as.data.frame(raster_to_process_streets, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# cities
cities_spdf <- rasterToPoints(raster_map_cities, spatial = TRUE)
cities_spdf <- as.data.frame(cities_spdf) %>%
  drop_na 
colnames(cities_spdf) <- c("value", "x", "y")
cities_spdf <- cities_spdf %>%
  add_column(Aspects = "City")

# settlements
settlements_spdf <- rasterToPoints(raster_map_settlements, spatial = TRUE)
settlements_spdf <- as.data.frame(settlements_spdf) %>%
  drop_na
colnames(settlements_spdf) <- c("value", "x", "y")
settlements_spdf <- settlements_spdf %>%
  add_column(Aspects = "Settlement")

combined_dataframe <- cities_spdf %>%
  bind_rows(settlements_spdf)

combined_dataframe

# plot
pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")

pl <- pl + geom_point(data = combined_dataframe,
                      mapping = aes(x = x, y = y, color = Aspects, size = Aspects, shape = Aspects))
#pl <- pl + scale_shape_identity()
pl <- pl + scale_shape_manual(values = c('City' = 15, 'Settlement' = 16))
pl <- pl + scale_size_manual(values = c('City' = 2.5, 'Settlement' = 1))
pl <- pl + scale_color_manual(values = c("City" = "mediumturquoise", "Settlement" = "blueviolet"))

pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe_streets,
                       mapping = aes(x = x, y = y, fill = "Streets"))
pl <- pl + scale_fill_manual(name = NULL,
                             values = "mediumvioletred")


pl <- pl + coord_sf(crs = user_defined_EPSG)

# safe here for use in overview map
plot_anthropogenic_features <- pl

# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + theme(legend.key = element_rect(fill = NA),
                 legend.spacing.y = unit(0, "cm"))
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = (output_height ), width = output_width, dpi = output_dpi, units = output_unit)


## Combined Initial conditions (spatial information) ###########################
plot_title <- paste("Combined initial conditions (spatial information) applied for", initial_simulation_year_BAUs)
antfeatures_legend_title <- "Anthropogenic features"
other_legend_title <- "Other landscape elements"
policy_elements_title <- "Forest policy elements"
LUTs_legend_title <- "Land Use Land Cover Types"
tiles_legend_title <- paste(project, "- Tiles")


# streets
raster_to_process_streets <- raster_map_streets

raster_dataframe_streets <- as.data.frame(raster_to_process_streets, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# cities
cities_spdf <- rasterToPoints(raster_map_cities, spatial = TRUE)
cities_spdf <- as.data.frame(cities_spdf) %>%
  drop_na
colnames(cities_spdf) <- c("value", "x", "y")

# settlements
settlements_spdf <- rasterToPoints(raster_map_settlements, spatial = TRUE)
settlements_spdf <- as.data.frame(settlements_spdf) %>%
  drop_na
colnames(settlements_spdf) <- c("value", "x", "y")

# >>> create a guide for the legend alphas for each new scale as a fix
guide_setting <- guide_legend(override.aes = list(alpha = 0.1)) # guide_legend(override.aes = list(alpha = 0.1))

# plot
pl <- ggplot()
pl <- pl + new_scale_fill()
pl <- pl + dem_hillshade_layer
# dem_hillshade_layer <- geom_raster(data = hill_spdf, aes(x = x, y = y, fill = value), alpha = 1, show.legend = FALSE)

pl <- pl + new_scale_fill()
pl <- pl + initial_LULC_layer
# initial_LULC_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = LUT_name), alpha = 0.75, show.legend = TRUE) 
pl <- pl + scale_fill_manual(name = LUTs_legend_title,
                             values = LUT_colors_lookup,
                             limits = force,
                             guide = guide_legend(order = 4))

pl <- pl + new_scale_fill()
pl <- pl + restricted_areas_layer
# restricted_areas_layer <- geom_raster(data = raster_to_process, aes(x = x, y = y, fill = "Restricted areas"), alpha = 0.5, show.legend = TRUE)
pl <- pl + scale_fill_manual(name = policy_elements_title,
                             values = c("Restricted areas" = "gray"),
                             guide = guide_legend(order = 6))  # other_legend_title

# pl <- pl + new_scale_fill()
# pl <- pl + tiles_layer
# # tiles_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = tile_name), alpha = 0.75, show.legend = TRUE)
# pl <- pl + scale_fill_manual(name = tiles_legend_title,
#                              values = c("#fcfdbf", "#fc8961", "#b73779", "#51127c"))

pl <- pl + new_scale_fill()
pl <- pl + freshwater_layer
# freshwater_layer <- geom_raster(data = raster_dataframe, aes(x = x, y = y, fill = "Surface freshwater areas"), alpha = 0.75)
pl <- pl + scale_fill_manual(name = other_legend_title,
                             values = c("Surface freshwater areas" = "steelblue"),
                             guide = guide_legend(order = 5)) # other_legend_title

pl <- pl + new_scale_color()
pl <- pl + geom_point(data = cities_spdf,
                      mapping = aes(x = x, y = y, shape = 16, size = 1.5, stroke = 0, color = "Cities (enhanced)"))
pl <- pl + scale_shape_identity()
pl <- pl + scale_color_manual(name = antfeatures_legend_title, # antfeatures_legend_title, NULL
                              values = "mediumturquoise",
                              guide = guide_legend(order = 1,
                                                   override.aes = list(size=1.5, fill=NA)))


pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe_streets,
                       mapping = aes(x = x, y = y, fill = "Streets"))
pl <- pl + scale_fill_manual(name = NULL,
                             values = "mediumvioletred",
                             guide = guide_legend(order = 3)) # antfeatures_legend_title

pl <- pl + new_scale_color()
pl <- pl + geom_point(data = settlements_spdf,
                      mapping = aes(x = x, y = y, size = 1, stroke = 0, color = "Settlements (enhanced)"))
pl <- pl + scale_color_manual(name = NULL, #antfeatures_legend_title
                              values = "lightgrey",
                              guide = guide_legend(order = 2,
                                                   override.aes = list(fill=NA)))

# eliminate some aspects from the legends and order them
pl <- pl + scale_size(guide="none")
# pl <- pl + guides(fill = guide_legend(order = 1),
#                   color = guide_legend(order = 2))


pl <- pl + coord_sf(crs = user_defined_EPSG)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
#pl <- pl + guides(color = guide_legend(override.aes = list(element_rect(fill = 'white'))))
pl <- pl + theme(legend.background = element_rect(fill = 'white'),
                 legend.key = element_rect(colour = NA, fill = "white")) #, element_rect(fill = 'white')) fill = NA
                 #legend.spacing.y = unit(0, "cm"))
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = (output_height ), width = output_width, dpi = output_dpi, units = output_unit)

### Initial forest cover and anthropogenic features ##########################################
plot_title <- paste("Initial forest cover and anthropogenic features applied for", initial_simulation_year_BAUs)

# # study region
raster_null_mask_dataframe <- as.data.frame(raster_map_null_mask, xy = TRUE) %>%
  drop_na %>%
  rename (value = static_null_mask_input)

# initial forest cover
raster_to_process <- raster_map_initial_LULC

raster_dataframe_initial <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) %>%
  mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table) 

initial_potential_forest_types <- filter(raster_dataframe_initial, value == c(5, 8, 9))
initial_non_forest_types <- filter(raster_dataframe_initial, value != c(5, 8, 9))

# streets
raster_to_process_streets <- raster_map_streets

raster_dataframe_streets <- as.data.frame(raster_to_process_streets, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) 

# cities
cities_spdf <- rasterToPoints(raster_map_cities, spatial = TRUE)
cities_spdf <- as.data.frame(cities_spdf) %>%
  drop_na 
colnames(cities_spdf) <- c("value", "x", "y")
cities_spdf <- cities_spdf %>%
  add_column(Aspects = "City")

# settlements
settlements_spdf <- rasterToPoints(raster_map_settlements, spatial = TRUE)
settlements_spdf <- as.data.frame(settlements_spdf) %>%
  drop_na
colnames(settlements_spdf) <- c("value", "x", "y")
settlements_spdf <- settlements_spdf %>%
  add_column(Aspects = "Settlement")

combined_dataframe <- cities_spdf %>%
  bind_rows(settlements_spdf) 

# plot
pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")

# pl <- pl + new_scale_fill()
# pl <- pl + geom_raster(data = raster_null_mask_dataframe,
#                        aes(x = x, y = y, fill = "white"))

pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = initial_potential_forest_types,
                       aes(x = x, y = y, fill = LUT_name))
pl <- pl + scale_fill_manual(name = "Initial potential forest cover types",
                             values = LUT_colors_lookup,
                             limits = force,
                             guide = guide_legend(order = 1))
# 
# pl <- pl + new_scale_fill()
# pl <- pl + geom_raster(data = initial_non_forest_types,
#                        aes(x = x, y = y, fill = NA))
# pl <- pl + scale_fill_manual(name = " Remaining simulated regional landscape",
#                              values = c("Non-forest" = "lightgrey"),
#                              guide = guide_legend(order = 2))

pl <- pl + new_scale_color()
pl <- pl + geom_point(data = combined_dataframe,
                      mapping = aes(x = x, y = y, color = Aspects, size = Aspects, shape = Aspects))
#pl <- pl + scale_shape_identity()
pl <- pl + scale_shape_manual(values = c('City' = 15, 'Settlement' = 16))
pl <- pl + scale_size_manual(values = c('City' = 2.5, 'Settlement' = 1))
pl <- pl + scale_color_manual(values = c("City" = "mediumturquoise", "Settlement" = "blueviolet"),
                              na.value = NA)

pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = raster_dataframe_streets,
                       mapping = aes(x = x, y = y, fill = "Street"))
pl <- pl + scale_fill_manual(name = NULL,
                             values = "mediumvioletred",
                             guide = guide_legend(order = 3))


pl <- pl + coord_sf(crs = user_defined_EPSG)

# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + theme(legend.background = element_rect(fill = "white"),
                 legend.key = element_rect(fill = "white"))
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = (output_height ), width = output_width, dpi = output_dpi, units = output_unit)




### Initial potential forest cover alone #######################################
plot_title <- paste("Initial potential forest cover applied for", initial_simulation_year_BAUs)

# initial forest cover
raster_to_process <- raster_map_initial_LULC

raster_dataframe_initial <- as.data.frame(raster_to_process, xy = TRUE) %>% 
  drop_na %>%
  rename(value = 3) %>%
  mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table) 

initial_potential_forest_types <- filter(raster_dataframe_initial, value == c(5, 8, 9))

# plot
pl <- ggplot()
pl <- pl + dem_hillshade_layer
pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")

pl <- pl + new_scale_fill()
pl <- pl + geom_raster(data = initial_potential_forest_types,
                       aes(x = x, y = y, fill = LUT_name))
pl <- pl + scale_fill_manual(name = "Initial potential forest cover types",
                             values = LUT_colors_lookup,
                             limits = force,
                             guide = guide_legend(order = 1))


pl <- pl + coord_sf(crs = user_defined_EPSG)

# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location, 
                                             which_north = "true",
                                             pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit), 
                                             pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                             style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                               line_col = user_defined_baseline_color,
                                                                                               text_family = user_defined_font))
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.title.x = element_blank(),
                 axis.title.y = element_blank())
pl <- pl + theme(panel.grid.minor.x = element_blank(),
                 panel.grid.minor.y = element_blank())
pl <- pl + theme(legend.background = element_rect(fill = "white"),
                 legend.key = element_rect(fill = "white"),
                 legend.spacing.y = unit(0, "cm"))
pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = caption_landscape)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = (output_height ), width = output_width, dpi = output_dpi, units = output_unit)



### >> LPB landscape modelling probabilities (discrete scale) #####################
plot_title <- "LPB landscape modelling probabilities"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  
  probabilities_title <- "Classified probabilities"
  
  raster_to_process <- raster(raster_file_location)
  
  probability_classes <- tibble(
    class = c(1,2,3,4,5,6,7),
    class_description = c("0 %", ">0 to 20 %", ">20 to 40%", ">40 to 60 %", ">60 to 80 %", ">80 to <100 %","100 %")
  ) 
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    full_join(probability_classes, by = c("value" = "class")) %>%
    mutate(class_description = fct_relevel(class_description, c("0 %", ">0 to 20 %", ">20 to 40%", ">40 to 60 %", ">60 to 80 %", ">80 to <100 %","100 %")))
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = class_description),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = probabilities_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Landscape_modelling_probabilities')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title, 
                                  climate_period = .$description)
      
      tibble()
    }
    )
}


### >> RAP AND MPLC RESULTS: ###################################################

### > RAP targeted net forest scenarios (discrete scale) #########################
plot_title <- "RAP targeted net forest"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title) {
  
  legend_title <- "Aspects"
  
  raster_to_process <- raster(raster_file_location)
  
  probability_classes <- tibble(
    class = c(1,2,3),
    class_description = c("region", "existing net forest", "targeted additional net forest")
  ) 
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    full_join(probability_classes, by = c("value" = "class")) %>%
    mutate(class_description = fct_relevel(class_description, c("region", "existing net forest", "targeted additional net forest")))
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = class_description),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = caption_landscape,
                  fill = legend_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs, initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Targeted_net_forest')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title)
      
      tibble()
    }
    )
}


### > RAP potential additional restricted areas BAU BAU(+) (discrete scale) ######
plot_title <- "RAP potential restricted areas based on population peak land use mask"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title) {
  
  legend_title <- "Aspects"
  
  raster_to_process <- raster(raster_file_location)
  
  probability_classes <- tibble(
    class = c(1,2,3),
    class_description = c("region", "existing restricted areas", "potential additional restricted areas")
  ) 
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    full_join(probability_classes, by = c("value" = "class"))
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = class_description),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum, direction = -1)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = caption_landscape,
                  fill = legend_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Potential_restricted_areas')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(#time_step = as.numeric(str_sub(file_name, -7, -5)),
           plot_title = paste(plot_title, scenario_i)) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title)
      
      tibble()
    }
    )
}

### > LULCC mplc RAP: ##########################################################
# LULCC mplc ###################################################################
plot_title <- "Simulated land use mplc (probable)"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  LUT_title <- "Land Use Types"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
    left_join(RAP_LUTs_lookup_table)
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = LUT_name),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_manual(
    values = LUT_colors_lookup,
    limits = force)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = LUT_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Landscape_configuration_mplc')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title, 
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

### UNFINSIHED LULCC mplc gridded ##############################################
### disregarded - too small
# plot_title <- "Simulated land use mplc (probable) - gridded"
# LUT_title <- "Land Use Types"
# 
# LULCC_mplc_BAU_df <- map2_dfr(LULCC_mplc_BAU_locations, LULCC_mplc_BAU_ids, import_one_raster) %>%
#   mutate(scenario = 'BAU',
#          start_year = initial_simulation_year_BAUs )
# 
# LULCC_mplc_BAUplus_df <- map2_dfr(LULCC_mplc_BAUplus_locations, LULCC_mplc_BAUplus_ids, import_one_raster)%>%
#   mutate(scenario = 'BAU(+)',
#          start_year = initial_simulation_year_BAUs)
# 
# LULCC_mplc_worst_case_df <- map2_dfr(LULCC_mplc_worst_case_locations, LULCC_mplc_worst_case_ids, import_one_raster)%>%
#   mutate(scenario = 'worst-case',
#          start_year = initial_simulation_year_worst_case)
# 
# LULCC_mplc_dfs <- bind_rows(LULCC_mplc_BAU_df, LULCC_mplc_BAUplus_df, LULCC_mplc_worst_case_df) %>%
#   mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = ''),
#          time_step = as.numeric(raster_id),
#          year = time_step + start_year - 1) %>%
#   left_join(RAP_LUTs_lookup_table)
# 
# raster_dataframe <- LULCC_mplc_dfs
# 
# pl <- ggplot()  
# pl <- pl + dem_hillshade_layer
# pl <- pl + new_scale_fill()
# pl <- pl + facet_grid(~year ~scenario)
# pl <- pl + geom_raster(data = raster_dataframe,
#                        aes(x = x, y = y, fill = LUT_name),
#                        alpha = 0.75,
#                        show.legend = TRUE) 
# pl <- pl + scale_fill_manual(values = LUT_colors_lookup,
#                              limits = force)
# pl <- pl + coord_sf(crs = user_defined_EPSG)
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.title.x = element_blank(),
#                  axis.title.y = element_blank())
# pl <- pl + theme(panel.grid.minor.x = element_blank(),
#                  panel.grid.minor.y = element_blank())
# pl <- pl + labs(title = plot_title,
#                 subtitle = paste(subtitle_prefix),
#                 fill = LUT_title)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = 29.7, width = 21, dpi = output_dpi, units = "cm")



# LULCC RAP - Complete Landscape ###############################################
plot_title <- "Simulated land use RAP (possible)"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  LUT_title <- "Land Use Types"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
    left_join(RAP_LUTs_lookup_table)
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = LUT_name),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_manual(
    values = LUT_colors_lookup,
    limits = force)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = LUT_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Landscape_configuration_RAP')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}


# LULCC RAP - RAP LUTS only ###############################################
plot_title <- "Simulated RAP-LUTs distribution"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  LUT_title <- "RAP Land Use Types"
  
  RAP_LUTs <- c(21, 22, 23, 24, 25)
  RAP_LUT_colors <- tibble(
    RAP_LUT_value = c(21, 22, 23, 24, 25),
    colors = c("#440154", "#3b528b", "#21918c", "#5ec962", "#fde725" )
  ) %>%
    mutate(LUT_code = paste('LUT', str_pad(RAP_LUT_value, 2, 'left', '0'), sep = ''))
  
  RAP_LUT_colors_lookup <- RAP_LUT_colors %>%
    left_join(RAP_LUTs_lookup_table) %>%
    pull(colors, LUT_name)
  
  raster_to_process <- raster(raster_file_location)
  
  RAP_raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    mutate(LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
    filter(., value %in% RAP_LUTs) %>% # extract the RAP LUTs to be displayed
    left_join(RAP_LUTs_lookup_table) 
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white", guide = 'none')
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = RAP_raster_dataframe,
                         aes(x = x, y = y, fill = LUT_name),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_manual(values = RAP_LUT_colors_lookup,
                               limits = force)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = LUT_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Landscape_configuration_RAP')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}



### > LPB urbanization patterns (LUT01) - extract this from mplc ###############
plot_title <- "LPB urbanization patterns"

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Aspects"
  
  raster_dataframe <- raster(raster_file_location) %>%
    as.data.frame(xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) %>%
    mutate(urbanization = if_else(value == 1, 'built-up', 'region'),
           LUT_code = paste('LUT', str_pad(value, 2, 'left', '0'), sep = '')) %>%
    left_join(RAP_LUTs_lookup_table)
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = urbanization),
                         alpha = 0.75,
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'Landscape_configuration_mplc')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
           left_join(climate_periods_complete) %>% 
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title, 
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

### >>> Overview plot: ##########################################################

# Combines:
# A Region
# B initial LULC
# C anthropogenic features
# D surface freshwater
# E restricted areas
# F slope in percent

# PLOT Joined
# labels <- ggplot() + labs (title = super_plot_title,
#                            subtitle = subtitle_prefix) +
#   theme_LPB_RAP
# pl_joined <- plot_grid(labels, pl1, pl2, pl3, pl4, nrow = 3, ncol = 3, align = 'hv', axis = 'l', rel_heights = c(0.1, 0.5, 0.5)) 
# pl_joined <- plot_grid(plot_study_area, 
#                        plot_initial_LULC, 
#                        plot_anthropogenic_features, 
#                        plot_surface_freshwater,
#                        plot_restricted_areas,
#                        plot_slope_percent ,
#                        nrow = 2, ncol = 2, 
#                        align = 'hv', 
#                        rel_heights = c(2,1),
#                        rel_widths = c(1,2),
#                        labels = c('A', 'B', 'C', 'D', 'E', 'F'), 
#                        scale = 0.95)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', 'ECU Esmeraldas Overview plot cowplot', output_format, sep = '')), 
#        height = 17, width = 10, dpi = output_dpi, units = output_unit)
# 
# 
# 
# ggarrange(plot_study_area,
#           plot_initial_LULC,
#           ggarrange(plot_anthropogenic_features, plot_surface_freshwater, ncol = 2, labels = c('C', 'D')),
#           ggarrange(plot_restricted_areas, plot_slope_percent, ncol = 2, labels = c('E', 'F')),
#           nrow = 4,
#           labels = c('A', 'B'))
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', 'ECU Esmeraldas Overview plot ggpubr', output_format, sep = '')), 
#        height = 17, width = 10, dpi = output_dpi, units = output_unit)



### TODO (legend alpha value): Forest degradation and regeneration mplc (user-defined) ##########
if (local_degradation_simulated == TRUE) {
  
  plot_title <- 'Forest degradation and regeneration mplc (user-defined)'
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Simulated user-defined\nforest degradation and regeneration stages"
    
    raster_to_process <- raster(raster_file_location)
    
    classes <- tibble(
      # degradation low = 1
      # degradation moderate = 2
      # degradation severe = 3
      # degradation absolute = 4
      
      # regeneration low = 5
      # regeneration medium = 6
      # regeneration high = 7
      # regeneration full = 8
      
      # gross forest = 9
      # region = 10
      class = c(1,2,3,4,5,6,7,8,9,10),
      class_description = c("degradation low", "degradation moderate", "degradation severe", "degradation absolute (pre-defined)", 
                            "regeneration low", "regeneration medium","regeneration high", "regeneration full (pre-defined)",
                            "gross forest", "region")
    ) 
    
    raster_dataframe_stages <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      full_join(classes, by = c('value' = 'class')) %>%
      filter(value %in% c(4,3,2,1,5,6,7,8)) %>%
      mutate(class_description = fct_relevel(class_description, c("degradation absolute (pre-defined)", "degradation severe","degradation moderate", "degradation low",
                                                                  "regeneration low", "regeneration medium","regeneration high", "regeneration full (pre-defined)")))
     
    
    pl <- ggplot() 
    # plot hillshade
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    # plot_all
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe_stages,
                           aes(x = x, y = y, fill = class_description))
    pl <- pl + scale_fill_brewer(palette= 'BrBG', name=legend_title)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)

    raster_type_input_folder <- file.path(input_folder, scenario_i, 'MPLC_forest_degradation_and_regeneration')

    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)

        tibble()
      }
      )
  }
}


##################################################################################################################################
### END CODE Model stage 1 #######################################################################################################
##################################################################################################################################

##################################################################################################################################
### START CODE Model Stage 2 #####################################################################################################
##################################################################################################################################

### MS2: Ecosystem fragmentation mplc maps probing dates #######################
if (fragmentation_simulated == TRUE) {
  plot_title <- paste('Ecosystem fragmentation mplc for umbrella species', umbrella_species_name)
  
  # get the raster file
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period,
                                          raster_scenario, raster_year) {
    
    # select the tag data for annotation
    mplc_number_of_patches <- input_data$LPB_fragmentation[[1]] %>%
      filter(Aspect == 'maximum_patch_number') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    scenario_year_number_patches <- mplc_number_of_patches$value
    
    
    mplc_total_area <- input_data$LPB_fragmentation[[1]] %>%
      filter(Aspect == 'total_area_of_patches') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)

    scenario_year_total_area_km2 <- scales::label_comma(accuracy= .1) (mplc_total_area$value / 100)
    
    # plot info
    legend_title <- paste("Continuous patches of\ncore habitat LUTs\n>=", umbrella_species_minimum_patch_size_in_km2, "km\u00b2")
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(value != 0)
    
    raster <- terra::rast(raster_dataframe)
    polygons = terra::as.polygons(raster)
    outline <- sf::st_as_sf(polygons)
    st_crs(outline) <- user_defined_EPSG
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = 'Singular potential patches'))
    pl <- pl + scale_fill_manual(na.value = NA,
                                 values = '#21918c')
    pl <- pl + geom_sf(data = outline,  
                       size=1, 
                       col=user_defined_baseline_color,
                       fill = NA)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tidy data
    pl <- pl + labs(tag = paste('Number of patches:', scenario_year_number_patches, '<br>Total area [km<sup>2</sup>]:', scenario_year_total_area_km2))
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.80, .1),
                     plot.tag = element_textbox_simple(family = user_defined_font, 
                                                       size = user_defined_fontsize - user_defined_fontsize_factor,
                                                       colour = user_defined_baseline_color,
                                                       face = user_defined_title_face ,
                                                       hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs, initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'ecosystem_fragmentation')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    raster_scenario = scenario_i,
                                    raster_year = .$year)
        
        tibble()
      }
      )
  }
}

### MS2: Ecosystem fragmentation RAP maps probing dates ########################
if (fragmentation_simulated == TRUE) {
  plot_title <- paste('Ecosystem fragmentation RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period,
                                          raster_scenario, raster_year) {
    
    # select the tag data for annotation
    RAP_number_of_patches <- input_data$RAP_fragmentation[[1]] %>%
      filter(Aspect == 'maximum_patch_number') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    scenario_year_number_patches <- RAP_number_of_patches$value
    
    
    RAP_total_area <- input_data$RAP_fragmentation[[1]] %>%
      filter(Aspect == 'total_area_of_patches') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    scenario_year_total_area_km2 <- scales::label_comma(accuracy= .1) (RAP_total_area$value / 100)
    
    # plot info
    legend_title <- paste("Continuous patches of\ncore habitat LUTs\n>=", umbrella_species_minimum_patch_size_in_km2, "km\u00b2")
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(value != 0)
    
    raster <- terra::rast(raster_dataframe)
    polygons = terra::as.polygons(raster)
    outline <- sf::st_as_sf(polygons)
    st_crs(outline) <- user_defined_EPSG
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = 'Singular potential patches'))
    pl <- pl + scale_fill_manual(na.value = NA,
                                 values = '#21918c')
    pl <- pl + geom_sf(data = outline,  
                       size=1, 
                       col=user_defined_baseline_color,
                       fill = NA)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tidy data
    pl <- pl + labs(tag = paste('Number of patches:', scenario_year_number_patches, '<br>Total area [km<sup>2</sup>]:', scenario_year_total_area_km2))
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.80, .1),
                     plot.tag = element_textbox_simple(family = user_defined_font, 
                                                       size = user_defined_fontsize - user_defined_fontsize_factor,
                                                       colour = user_defined_baseline_color,
                                                       face = user_defined_title_face ,
                                                       hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'ecosystem_fragmentation')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    raster_scenario = scenario_i,
                                    raster_year = .$year)
        
        tibble()
      }
      )
  }
}

### MS2: Ecosystem Fragmentation mplc RAP juxtaposition ########################
if (fragmentation_simulated == TRUE) {
  plot_title <- paste('Ecosystem fragmentation mplc RAP juxtaposition for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(mplc_raster_file_location,
                                          RAP_raster_file_location,
                                          plot_title, climate_period,
                                          raster_scenario, raster_year) {
    
    # select the tag data for annotation
    mplc_number_of_patches <- input_data$LPB_fragmentation[[1]] %>%
      filter(Aspect == 'maximum_patch_number') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    mplc_scenario_year_number_patches <- mplc_number_of_patches$value
    
    
    mplc_total_area <- input_data$LPB_fragmentation[[1]] %>%
      filter(Aspect == 'total_area_of_patches') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    mplc_scenario_year_total_area_km2 <- scales::label_comma(accuracy= .1) (mplc_total_area$value / 100)
    
    RAP_number_of_patches <- input_data$RAP_fragmentation[[1]] %>%
      filter(Aspect == 'maximum_patch_number') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    RAP_scenario_year_number_patches <- RAP_number_of_patches$value
    
    
    RAP_total_area <- input_data$RAP_fragmentation[[1]] %>%
      filter(Aspect == 'total_area_of_patches') %>%
      filter(scenario == raster_scenario) %>%
      filter(year == raster_year)
    
    RAP_scenario_year_total_area_km2 <- scales::label_comma(accuracy= .1) (RAP_total_area$value / 100)
    
    # plot info
    legend_title <- paste("Continuous patches of\ncore habitat LUTs\n>=", umbrella_species_minimum_patch_size_in_km2, "km\u00b2")
    
    # plot data
    mplc_raster_to_process <- raster(mplc_raster_file_location)
    
    mplc_raster_dataframe <- as.data.frame(mplc_raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(mplc_value = 3) %>%
      filter(mplc_value != 0)
    
    raster <- terra::rast(mplc_raster_dataframe)
    polygons = terra::as.polygons(raster)
    mplc_outline <- sf::st_as_sf(polygons)
    st_crs(mplc_outline) <- user_defined_EPSG
    
    RAP_raster_to_process <- raster(RAP_raster_file_location)
    
    RAP_raster_dataframe <- as.data.frame(RAP_raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(RAP_value = 3) %>%
      filter(RAP_value != 0)
    
    raster <- terra::rast(RAP_raster_dataframe)
    polygons = terra::as.polygons(raster)
    RAP_outline <- sf::st_as_sf(polygons)
    st_crs(RAP_outline) <- user_defined_EPSG
    
    combined_dataframe <- RAP_raster_dataframe %>%
      full_join(mplc_raster_dataframe, join_by(x,y))
    
    combined_dataframe <- combined_dataframe%>%
      mutate('combined_value' = case_when(
        (is.na(mplc_value)) ~ 2,
        (!is.na(mplc_value)) ~ 1
      ))

    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = combined_dataframe,
                           aes(x = x, y = y, fill = factor(combined_value)))
    pl <- pl + scale_fill_manual(name = legend_title,
                                 na.value = NA,
                                 values = c('1' = '#21918c', '2' = '#5ec962'),
                                 labels = c('no FLR scenario extent', 'FLR scenario extent'))
    # pl <- pl + geom_sf(data = RAP_outline,
    #                    size=1,
    #                    col=user_defined_baseline_color,
    #                    fill = NA)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tidy data mplc
    pl <- pl + labs(tag = paste('No FLR scenario:<br>Number of patches:', mplc_scenario_year_number_patches, '<br>Total area [km<sup>2</sup>]:', mplc_scenario_year_total_area_km2, '<br><br>
                                FLR scenario:<br>Number of patches:', RAP_scenario_year_number_patches, '<br>Total area [km<sup>2</sup>]:', RAP_scenario_year_total_area_km2))
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.80, .2),
                     plot.tag = element_textbox_simple(family = user_defined_font, 
                                                       size = user_defined_fontsize - user_defined_fontsize_factor,
                                                       colour = user_defined_baseline_color,
                                                       face = user_defined_title_face ,
                                                       hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    mplc_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'ecosystem_fragmentation')
    RAP_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'ecosystem_fragmentation')
    
    tibble(
      mplc_file_name = list.files(mplc_input_folder, full.names = TRUE),
      RAP_file_name = list.files(RAP_input_folder, full.names = TRUE)
    ) %>%
      mutate(time_step = as.numeric(str_sub(mplc_file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(mplc_raster_file_location = .$mplc_file_name,
                                    RAP_raster_file_location = .$RAP_file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    raster_scenario = scenario_i,
                                    raster_year = .$year)
        
        tibble()
      }
      )
  }
}





### MS2: Connectivity Omniscape ####
# > Normalized cumulative current - mplc #### 
# Values greater than one indicate areas with channelized/bottlenecked flow. 
# Values around 1 (cumulative current ≈ flow potential) indicate diffuse current. 
# Values less than 1 indicate impeded flow.
if (performed_Omniscape_analysis_mplc == TRUE) {
  
  plot_title <- paste('Habitat connectivity normalized cumulative current mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Normalized cumulative current"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    min_range = signif(min(raster_dataframe$value),d=1)
    max_range = floor(max(raster_dataframe$value)) 
    set_midpoint = 1
    set_breaks = c(min_range, set_midpoint, ceiling(seq(min_range, max_range, (max_range - min_range)/4)), max_range)
    
    n_greyscale <- length(raster_dataframe$value < set_midpoint)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_gradient2(midpoint = set_midpoint,
                                    mid = 'white',
                                    low = grey.colors(n = 10, start = 0, end = 0.9, rev = FALSE), 
                                    high = viridis(n = 10, option = 'viridis', direction = 1),
                                    space = 'Lab',
                                    labels = set_breaks,
                                    breaks = set_breaks)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('Normalized cumulative current:\n>1 == channelized flow\n~ 1 == diffuse flow\n            (cumulative current ≈ flow potential)\n< 1 == impeded flow')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.75, .1),
                     plot.tag = element_text(family = user_defined_font, 
                                             size = user_defined_fontsize - user_defined_fontsize_factor,
                                             colour = user_defined_baseline_color,
                                             face = user_defined_title_face ,
                                             hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'normalized_cumulative_current')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Normalized cumulative current - RAP #### 
# Values greater than one indicate areas with channelized/bottlenecked flow. 
# Values around 1 (cumulative current ≈ flow potential) indicate diffuse current. 
# Values less than 1 indicate impeded flow.
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity normalized cumulative current RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Normalized cumulative current"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    min_range = signif(min(raster_dataframe$value),d=1)
    max_range = floor(max(raster_dataframe$value)) 
    set_midpoint = 1
    set_breaks = c(min_range, set_midpoint, ceiling(seq(min_range, max_range, (max_range - min_range)/4)), max_range)
    
    n_greyscale <- length(raster_dataframe$value < set_midpoint)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_gradient2(midpoint = set_midpoint,
                                    mid = 'white',
                                    low = grey.colors(n = 10, start = 0, end = 0.9, rev = FALSE), 
                                    high = viridis(n = 10, option = 'viridis', direction = 1),
                                    space = 'Lab',
                                    labels = set_breaks,
                                    breaks = set_breaks)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('Normalized cumulative current:\n>1 == channelized flow\n~ 1 == diffuse flow\n            (cumulative current ≈ flow potential)\n< 1 == impeded flow')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.75, .1),
                     plot.tag = element_text(family = user_defined_font, 
                                             size = user_defined_fontsize - user_defined_fontsize_factor,
                                             colour = user_defined_baseline_color,
                                             face = user_defined_title_face ,
                                             hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i,  'HABITAT_ANALYSIS_RAP', 'Omniscape', 'normalized_cumulative_current')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Cumulative current - mplc #### 
if (performed_Omniscape_analysis_mplc == TRUE) {
  
  plot_title <- paste('Habitat connectivity cumulative current mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Cumulative current"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i,  'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'cumulative_current')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Cumulative current - RAP #### 
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity cumulative current RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Cumulative current"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'cumulative_current')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Flow potential - mplc #### 
if (performed_Omniscape_analysis_mplc == TRUE) {
  
  plot_title <- paste('Habitat connectivity flow potential mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Flow potential"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = 'magma')
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Flow potential - RAP #### 
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity flow potential RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Flow potential"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = 'magma')
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'flow_potential')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Normalized reclassified - mplc #### 
if (performed_Omniscape_analysis_mplc == TRUE) {
  
  plot_title <- paste('Habitat connectivity normalized reclassified mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Normalized cumulative current reclassified"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = as.factor(value))#,
                           )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75', 
                                            '4' = '#95d840', 
                                            '5' = '#fed89a',
                                            '6' = '#fcfdbf'
                                            ),
                                 labels = c('1' = 'blocked flow (<= 0.27)\n- no or nearly no movement potential',
                                            '2' = 'impeded flow (> 0.27 - 0.47)\n- limited movement potential',
                                            '3' = 'reduced flow (> 0.47 - 0.7)\n- movement edges in some directions',
                                            '4' = 'diffuse flow (> 0.7 - 1.3)\n- well connected, movement edges in many directions',
                                            '5' = 'intensified flow (> 1.3 - 1.7)\n- edges between well connected and fragmented',
                                            '6' = 'channelized flow (> 1.7)\n- potential habitat corridors and pinch points'  
                                            ))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Normalized reclassified - RAP #### 
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity normalized reclassified RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Normalized cumulative current reclassified"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = as.factor(value))#,
    )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75', 
                                            '4' = '#95d840', 
                                            '5' = '#fed89a',
                                            '6' = '#fcfdbf'
    ),
    labels = c('1' = 'blocked flow (<= 0.27)\n- no or nearly no movement potential',
               '2' = 'impeded flow (> 0.27 - 0.47)\n- limited movement potential',
               '3' = 'reduced flow (> 0.47 - 0.7)\n- movement edges in some directions',
               '4' = 'diffuse flow (> 0.7 - 1.3)\n- well connected, movement edges in many directions',
               '5' = 'intensified flow (> 1.3 - 1.7)\n- edges between well connected and fragmented',
               '6' = 'channelized flow (> 1.7)\n- potential habitat corridors and pinch points'  
    ))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape_transformed', 'normalized_reclassified')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

#POST-PROCESSING OUTPUTS #####
# > Optimized normalized reclassified separated diffuse flow - mplc ####

if (performed_Omniscape_analysis_mplc == TRUE) {
  
  plot_title <- paste('Habitat connectivity optimized normalized reclassified mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period, 
                                          flow_potential, current_year) {
    
    legend_title <- "Optimized normalized cumulative current reclassified"
    
    # get the reclassified data
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    
    # get the flow potential data
    flow_potential_year <- flow_potential %>%
      filter(year == current_year) 
    
    flow_potential_raster_location <- flow_potential_year$file_name
    
    flow_potential_raster = raster(flow_potential_raster_location)
    
    flow_potential_dataframe <- as.data.frame(flow_potential_raster, xy = TRUE) %>%
      drop_na %>%
      rename(fp_value = 3) %>%
      mutate('fp_threshold' = mean(fp_value) - sd(fp_value)) 
    
    # combine data frames and calculate new value
    optimized_dataframe <- raster_dataframe %>%
      left_join(flow_potential_dataframe, join_by(x, y)) %>%
      group_by(value) %>%
      mutate('optimized_value' = case_when(
        (value == 4 & fp_value < fp_threshold) ~ 4,
        (value == 4 & fp_value >= fp_threshold) ~ 5,
        (value == 1 ) ~ 1,
        (value == 2 ) ~ 2,
        (value == 3 ) ~ 3,
        (value == 5 ) ~ 6,
        (value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
  
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = optimized_dataframe,
                           aes(x = x, y = y, fill = as.factor(optimized_value))#,
                           #alpha = 0.75
    )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75',
                                            '4' = '#6e1e81',
                                            '5' = '#95d840', 
                                            '6' = '#fed89a',
                                            '7' = '#fcfdbf'),
    labels = c('1' = 'blocked flow (<= 0.27)\n- no or nearly no movement potential',
               '2' = 'impeded flow (> 0.27 - 0.47)\n- limited movement potential',
               '3' = 'reduced flow (> 0.47 - 0.7)\n- movement edges in some directions',
               '4' = '*pseudo diffuse flow (> 0.7 - 1.3)\n- only mathematical result, de facto between blocked and impeded',
               '5' = 'robust diffuse flow (> 0.7 - 1.3)\n- well connected, movement edges in many directions',
               '6' = 'intensified flow (> 1.3 - 1.7)\n- edges between well connected and fragmented',
               '7' = 'channelized flow (> 1.7)\n- potential habitat corridors and pinch points'  
    ))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('*pseudo diffuse flow:\nArea, where division of flow potential and observed values\nyields values around 1 but flow potential is\nbelow one standard deviation subtracted from the mean.')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.60, .1),
                     plot.tag = element_text(family = user_defined_font, 
                                         size = user_defined_fontsize - user_defined_fontsize_factor,
                                         colour = user_defined_baseline_color,
                                         face = user_defined_other_face ,
                                         hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified')
    flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential')
    
    flow_potential_tibble <- tibble(
      file_name = list.files(flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    flow_potential = flow_potential_tibble,
                                    current_year = .$year)
        
        tibble()
      }
      )
  }
}


# > Optimized normalized reclassified separated diffuse flow - RAP #### 
if (performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity optimized normalized reclassified RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period, 
                                          flow_potential, current_year) {
    
    legend_title <- "Optimized normalized cumulative current reclassified"
    
    # get the reclassified data
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    
    # get the flow potential data
    flow_potential_year <- flow_potential %>%
      filter(year == current_year) 
    
    flow_potential_raster_location <- flow_potential_year$file_name
    
    flow_potential_raster = raster(flow_potential_raster_location)
    
    flow_potential_dataframe <- as.data.frame(flow_potential_raster, xy = TRUE) %>%
      drop_na %>%
      rename(fp_value = 3) %>%
      mutate('fp_threshold' = mean(fp_value) - sd(fp_value)) 
    
    # combine data frames and calculate new value
    optimized_dataframe <- raster_dataframe %>%
      left_join(flow_potential_dataframe, join_by(x, y)) %>%
      group_by(value) %>%
      mutate('optimized_value' = case_when(
        (value == 4 & fp_value < fp_threshold) ~ 4,
        (value == 4 & fp_value >= fp_threshold) ~ 5,
        (value == 1 ) ~ 1,
        (value == 2 ) ~ 2,
        (value == 3 ) ~ 3,
        (value == 5 ) ~ 6,
        (value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = optimized_dataframe,
                           aes(x = x, y = y, fill = as.factor(optimized_value))#,
                           #alpha = 0.75
    )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75',
                                            '4' = '#6e1e81',
                                            '5' = '#95d840', 
                                            '6' = '#fed89a',
                                            '7' = '#fcfdbf'),
                                 labels = c('1' = 'blocked flow (<= 0.27)\n- no or nearly no movement potential',
                                            '2' = 'impeded flow (> 0.27 - 0.47)\n- limited movement potential',
                                            '3' = 'reduced flow (> 0.47 - 0.7)\n- movement edges in some directions',
                                            '4' = '*pseudo diffuse flow (> 0.7 - 1.3)\n- only mathematical result, de facto between blocked and impeded',
                                            '5' = 'robust diffuse flow (> 0.7 - 1.3)\n- well connected, movement edges in many directions',
                                            '6' = 'intensified flow (> 1.3 - 1.7)\n- edges between well connected and fragmented',
                                            '7' = 'channelized flow (> 1.7)\n- potential habitat corridors and pinch points'  
                                 ))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('*pseudo diffuse flow:\nArea, where division of flow potential and observed values\nyields values around 1 but flow potential is\nbelow one standard deviation subtracted from the mean.')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.60, .1),
                     plot.tag = element_text(family = user_defined_font, 
                                             size = user_defined_fontsize - user_defined_fontsize_factor,
                                             colour = user_defined_baseline_color,
                                             face = user_defined_other_face ,
                                             hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape_transformed', 'normalized_reclassified')
    flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'flow_potential')
    
    flow_potential_tibble <- tibble(
      file_name = list.files(flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    flow_potential = flow_potential_tibble,
                                    current_year = .$year)
        
        tibble()
      }
      )
  }
}

# > Change (RAP) mplc to RAP optimized normalized reclassified separated diffuse flow - mplc ####

if (performed_Omniscape_analysis_mplc == TRUE & performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity change mplc to RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(#raster_file_location,
                                          plot_title, climate_period, 
                                          combined_normalized_reclassified_tibble,
                                          combined_flow_potential_tibble, 
                                          current_year) {
    
    legend_title <- "Optimized normalized cumulative current reclassified"
    
    ### get the reclassified data
    normalized_reclassified_year <- combined_normalized_reclassified_tibble %>%
      filter(year == current_year)
    
    # mplc
    mplc_normalized <- normalized_reclassified_year %>%
      filter(scenario == 'mplc')

    raster_location <- mplc_normalized$file_name
    raster_to_process <- raster(raster_location)
    
    mplc_normalized_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(mplc_normalized_value = 3) 
    
    #RAP
    RAP_normalized <- normalized_reclassified_year %>%
      filter(scenario == 'RAP') 
      
    raster_location <- RAP_normalized$file_name
    raster_to_process <- raster(raster_location)
    
    RAP_normalized_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(RAP_normalized_value = 3) 
    
    
    #### get the flow potential data
    flow_potential_year <- combined_flow_potential_tibble %>%
      filter(year == current_year) 
    
    #mplc
    mplc_flow <- flow_potential_year %>%
      filter(scenario == 'mplc')
    
    raster_location <- mplc_flow$file_name
    raster_to_process <- raster(raster_location)
    
    mplc_flow_potential_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(mplc_fp_value = 3) %>%
      mutate('mplc_fp_threshold' = mean(mplc_fp_value) - sd(mplc_fp_value))
    
    # RAP
    RAP_flow <- flow_potential_year %>%
      filter(scenario == 'RAP')
    
    raster_location <- RAP_flow$file_name
    raster_to_process <- raster(raster_location)
    
    RAP_flow_potential_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(RAP_fp_value = 3) %>%
      mutate('RAP_fp_threshold' = mean(RAP_fp_value) - sd(RAP_fp_value))
  
    
    
    # combine data frames per scenario and calculate new value
    mplc_optimized_dataframe <- mplc_normalized_dataframe %>%
      left_join(mplc_flow_potential_dataframe, join_by(x, y)) %>%
      group_by(mplc_normalized_value) %>%
      mutate('mplc_optimized_value' = case_when(
        (mplc_normalized_value == 4 & mplc_fp_value < mplc_fp_threshold) ~ 4,
        (mplc_normalized_value == 4 & mplc_fp_value >= mplc_fp_threshold) ~ 5,
        (mplc_normalized_value == 1 ) ~ 1,
        (mplc_normalized_value == 2 ) ~ 2,
        (mplc_normalized_value == 3 ) ~ 3,
        (mplc_normalized_value == 5 ) ~ 6,
        (mplc_normalized_value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
    RAP_optimized_dataframe <- RAP_normalized_dataframe %>%
      left_join(RAP_flow_potential_dataframe, join_by(x, y)) %>%
      group_by(RAP_normalized_value) %>%
      mutate('RAP_optimized_value' = case_when(
        (RAP_normalized_value == 4 & RAP_fp_value < RAP_fp_threshold) ~ 4,
        (RAP_normalized_value == 4 & RAP_fp_value >= RAP_fp_threshold) ~ 5,
        (RAP_normalized_value == 1 ) ~ 1,
        (RAP_normalized_value == 2 ) ~ 2,
        (RAP_normalized_value == 3 ) ~ 3,
        (RAP_normalized_value == 5 ) ~ 6,
        (RAP_normalized_value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
    # combine and select only changed pixels
    combined_optimized_dataframe <- mplc_optimized_dataframe %>%
      left_join(RAP_optimized_dataframe, join_by(x,y)) %>%
      #rowwise() %>%
      mutate('change' = case_when(
        (RAP_optimized_value != mplc_optimized_value) ~ RAP_optimized_value,
        .default = NA
      )) %>%
      drop_na
    
    RAP_grouped_area <- combined_optimized_dataframe %>%
      mutate('area' = 1) %>%
      group_by(RAP_optimized_value) %>%
      mutate('grouped_area' = sum(area)) %>%
      ungroup() %>%
      group_by(grouped_area)
        
      
    blocked <- RAP_grouped_area %>% filter(RAP_optimized_value == 1) 
    sum_area_blocked_numeric <- unique(blocked$grouped_area)
    sum_area_blocked <- scales::label_comma(accuracy= 1) (unique(blocked$grouped_area))
    
    impeded <- RAP_grouped_area %>% filter(RAP_optimized_value == 2) 
    sum_area_impeded_numeric <- unique(impeded$grouped_area)
    sum_area_impeded <- scales::label_comma(accuracy= 1) (unique(impeded$grouped_area))
    
    reduced <- RAP_grouped_area %>% filter(RAP_optimized_value == 3)
    sum_area_reduced_numeric <- unique(reduced$grouped_area)
    sum_area_reduced <- scales::label_comma(accuracy= 1) (unique(reduced$grouped_area))
    
    pseudo <- RAP_grouped_area %>% filter(RAP_optimized_value == 4) 
    sum_area_pseudo_numeric <- unique(pseudo$grouped_area)
    sum_area_pseudo <- scales::label_comma(accuracy= 1) (unique(pseudo$grouped_area))
    
    diffuse <- RAP_grouped_area %>% filter(RAP_optimized_value == 5)
    sum_area_diffuse_numeric <- unique(diffuse$grouped_area)
    sum_area_diffuse <- scales::label_comma(accuracy= 1) (unique(diffuse$grouped_area))
    
    intensified <- RAP_grouped_area %>% filter(RAP_optimized_value == 6) 
    sum_area_intensified_numeric <- unique(intensified$grouped_area)
    sum_area_intensified <- scales::label_comma(accuracy= 1) (unique(intensified$grouped_area))
    
    channelized <- RAP_grouped_area %>% filter(RAP_optimized_value == 7) 
    sum_area_channelized_numeric <- unique(channelized$grouped_area)
    sum_area_channelized <- scales::label_comma(accuracy= 1) (unique(channelized$grouped_area))
    
    sum_area_all <- sum_area_blocked_numeric + sum_area_impeded_numeric + sum_area_reduced_numeric + sum_area_pseudo_numeric + sum_area_diffuse_numeric + sum_area_intensified_numeric + sum_area_channelized_numeric
    
    total_changed_area <- paste(scales::label_comma(accuracy= 1) (sum_area_all), landscape_area_unit)
    
    total_changed_area_percent <- round((((sum_area_all)/landscape_area_numeric)*100),2)
      
    
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = combined_optimized_dataframe,
                           aes(x = x, y = y, fill = as.factor(change))#,
                           #alpha = 0.75
    )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75', 
                                            '4' = '#6e1e81',
                                            '5' = '#95d840', 
                                            '6' = '#fed89a',
                                            '7' = '#fcfdbf'),
                                 labels = c('1' = paste('blocked flow (<= 0.27) | changed area:', sum_area_blocked, landscape_area_unit, '\n- no or nearly no movement potential'),
                                            '2' = paste('impeded flow (> 0.27 - 0.47) | changed area:', sum_area_impeded, landscape_area_unit, '\n- limited movement potential'),
                                            '3' = paste('reduced flow (> 0.47 - 0.7) | changed area:', sum_area_reduced, landscape_area_unit, '\n- movement edges in some directions'),
                                            '4' = paste('pseudo diffuse flow (> 0.7 - 1.3) | changed area:', sum_area_pseudo, landscape_area_unit, '\n- only mathematical result, de facto between blocked and impeded'),
                                            '5' = paste('robust diffuse flow (> 0.7 - 1.3) | changed area:', sum_area_diffuse, landscape_area_unit, '\n- well connected, movement edges in many directions'),
                                            '6' = paste('intensified flow (> 1.3 - 1.7) | changed area:', sum_area_intensified, landscape_area_unit, '\n- edges between well connected and fragmented'),
                                            '7' = paste('channelized flow (> 1.7) | changed area:', sum_area_channelized, landscape_area_unit, '\n- potential habitat corridors and pinch points')  
                                 ))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('*Changed area [ ∑', total_changed_area, '=', total_changed_area_percent, '% of landscape area]:\nNumber of pixels present that have changed from mplc to RAP')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.60, .1),
                     plot.tag = element_text(family = user_defined_font, 
                                             size = user_defined_fontsize - user_defined_fontsize_factor,
                                             colour = user_defined_baseline_color,
                                             face = user_defined_other_face ,
                                             hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    
    mplc_raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified')
    mplc_flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential')
    
    RAP_raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape_transformed', 'normalized_reclassified')
    RAP_flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'flow_potential')
    
    mplc_flow_potential_tibble <- tibble(
      file_name = list.files(mplc_flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(scenario = 'mplc',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    RAP_flow_potential_tibble <- tibble(
      file_name = list.files(RAP_flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(scenario = 'RAP',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    combined_flow_potential_tibble <- mplc_flow_potential_tibble %>% full_join(RAP_flow_potential_tibble)
    
    mplc_normalized_reclassified_tibble <- tibble(
      file_name = list.files(mplc_raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(scenario = 'mplc',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete)
    
    RAP_normalized_reclassified_tibble <- tibble(
      file_name = list.files(RAP_raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(scenario = 'RAP',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) 
    
    combined_normalized_reclassified_tibble <- mplc_normalized_reclassified_tibble %>% full_join(RAP_normalized_reclassified_tibble)
    
    mplc_normalized_reclassified_tibble %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(#raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    combined_normalized_reclassified_tibble,
                                    combined_flow_potential_tibble,
                                    current_year = .$year)
        
        tibble()
      }
      )
  }
}


# > Change (transition) mplc to RAP optimized normalized reclassified separated diffuse flow - mplc ####
library(RColorBrewer)
if (performed_Omniscape_analysis_mplc == TRUE & performed_Omniscape_analysis_RAP == TRUE) {
  
  plot_title <- paste('Habitat connectivity transition mplc to RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(#raster_file_location,
    plot_title, climate_period, 
    combined_normalized_reclassified_tibble,
    combined_flow_potential_tibble, 
    current_year) {
    
    ### get the reclassified data
    normalized_reclassified_year <- combined_normalized_reclassified_tibble %>%
      filter(year == current_year)
    
    # mplc
    mplc_normalized <- normalized_reclassified_year %>%
      filter(scenario == 'mplc')
    
    raster_location <- mplc_normalized$file_name
    raster_to_process <- raster(raster_location)
    
    mplc_normalized_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(mplc_normalized_value = 3) 
    
    #RAP
    RAP_normalized <- normalized_reclassified_year %>%
      filter(scenario == 'RAP') 
    
    raster_location <- RAP_normalized$file_name
    raster_to_process <- raster(raster_location)
    
    RAP_normalized_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(RAP_normalized_value = 3) 
    
    
    #### get the flow potential data
    flow_potential_year <- combined_flow_potential_tibble %>%
      filter(year == current_year) 
    
    #mplc
    mplc_flow <- flow_potential_year %>%
      filter(scenario == 'mplc')
    
    raster_location <- mplc_flow$file_name
    raster_to_process <- raster(raster_location)
    
    mplc_flow_potential_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(mplc_fp_value = 3) %>%
      mutate('mplc_fp_threshold' = mean(mplc_fp_value) - sd(mplc_fp_value))
    
    # RAP
    RAP_flow <- flow_potential_year %>%
      filter(scenario == 'RAP')
    
    raster_location <- RAP_flow$file_name
    raster_to_process <- raster(raster_location)
    
    RAP_flow_potential_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(RAP_fp_value = 3) %>%
      mutate('RAP_fp_threshold' = mean(RAP_fp_value) - sd(RAP_fp_value))
    
    
    
    # combine data frames per scenario and calculate new value
    mplc_optimized_dataframe <- mplc_normalized_dataframe %>%
      left_join(mplc_flow_potential_dataframe, join_by(x, y)) %>%
      group_by(mplc_normalized_value) %>%
      mutate('mplc_optimized_value' = case_when(
        (mplc_normalized_value == 4 & mplc_fp_value < mplc_fp_threshold) ~ 4,
        (mplc_normalized_value == 4 & mplc_fp_value >= mplc_fp_threshold) ~ 5,
        (mplc_normalized_value == 1 ) ~ 1,
        (mplc_normalized_value == 2 ) ~ 2,
        (mplc_normalized_value == 3 ) ~ 3,
        (mplc_normalized_value == 5 ) ~ 6,
        (mplc_normalized_value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
    RAP_optimized_dataframe <- RAP_normalized_dataframe %>%
      left_join(RAP_flow_potential_dataframe, join_by(x, y)) %>%
      group_by(RAP_normalized_value) %>%
      mutate('RAP_optimized_value' = case_when(
        (RAP_normalized_value == 4 & RAP_fp_value < RAP_fp_threshold) ~ 4,
        (RAP_normalized_value == 4 & RAP_fp_value >= RAP_fp_threshold) ~ 5,
        (RAP_normalized_value == 1 ) ~ 1,
        (RAP_normalized_value == 2 ) ~ 2,
        (RAP_normalized_value == 3 ) ~ 3,
        (RAP_normalized_value == 5 ) ~ 6,
        (RAP_normalized_value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na
    
    # combine and select only changed pixels, map transition
    combined_optimized_dataframe <- mplc_optimized_dataframe %>%
      left_join(RAP_optimized_dataframe, join_by(x,y)) %>%
      mutate('mplc_class' = case_when(
        (mplc_optimized_value == 1) ~ 'blocked',
        (mplc_optimized_value == 2) ~ 'impeded',
        (mplc_optimized_value == 3) ~ 'reduced',
        (mplc_optimized_value == 4) ~ 'pseudo',
        (mplc_optimized_value == 5) ~ 'diffuse',
        (mplc_optimized_value == 6) ~ 'intensified',
        (mplc_optimized_value == 7) ~ 'channelized',
      )) %>%
      mutate('RAP_class' = case_when(
        (RAP_optimized_value == 1) ~ 'blocked',
        (RAP_optimized_value == 2) ~ 'impeded',
        (RAP_optimized_value == 3) ~ 'reduced',
        (RAP_optimized_value == 4) ~ 'pseudo',
        (RAP_optimized_value == 5) ~ 'diffuse',
        (RAP_optimized_value == 6) ~ 'intensified',
        (RAP_optimized_value == 7) ~ 'channelized',
      )) %>%
      filter(mplc_class != RAP_class) %>%
      mutate('change' = case_when(
        (RAP_optimized_value != mplc_optimized_value) ~ RAP_optimized_value,
        .default = NA
      )) %>%
      drop_na %>%
      mutate('area' = 1) %>%
      mutate('mplc_numerical_grade' = mplc_optimized_value - 5,
             'RAP_numerical_grade' = RAP_optimized_value - 5) %>%
      mutate('mplc_class_abs' = abs(mplc_numerical_grade),
             'RAP_class_abs' = abs(RAP_numerical_grade)) %>%
      mutate('temporal_class' = RAP_class_abs - mplc_class_abs) %>%
      mutate('transition_direction' = case_when(
        (temporal_class < 0) ~ 'increase',
        (temporal_class > 0) ~ 'decrease',
        .default = NA
      )) %>%
      drop_na %>%
      mutate('combination' = paste(mplc_class, 'to', RAP_class)) %>%
      group_by(combination) %>%
      mutate('grouped_transition_area' = sum(area)) %>%
      mutate('combination_plus_other' = case_when(
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'increase' & mplc_optimized_value == 4) ~ 'other positive from pseudo transitions',
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'decrease' & mplc_optimized_value == 4) ~ 'other negative from pseudo transitions',
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'increase' & RAP_optimized_value != 4) ~ 'other positive transitions',
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'increase' & RAP_optimized_value == 4) ~ 'other positive to pseudo transitions',
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'decrease' & RAP_optimized_value != 4) ~ 'other negative transitions',
        (grouped_transition_area < (landscape_area_numeric/landscape_division_threshold) & transition_direction == 'decrease' & RAP_optimized_value == 4) ~ 'other negative to pseudo transitions',
        (grouped_transition_area >= (landscape_area_numeric/landscape_division_threshold)) ~ combination
      )) %>%
      group_by(combination_plus_other) %>%
      mutate('total_grouped_area' = sum(area)) %>%
      mutate('plot_label' = paste(combination_plus_other, '| changed area:', scales::label_comma(accuracy= 1) (unique(total_grouped_area)), landscape_area_unit)) %>%
      ungroup() %>%
      ungroup

    
    
    positive_transitions_dataframe <- combined_optimized_dataframe %>%
      filter(transition_direction == 'increase') %>%
      filter(mplc_optimized_value != 4 & RAP_optimized_value != 4) %>%
      mutate('factor' = factor(plot_label))
    positive_transitions_dataframe$factor <- fct_reorder(positive_transitions_dataframe$factor, positive_transitions_dataframe$total_grouped_area)
    sum_positive <- sum(positive_transitions_dataframe$area)
    sum_positive_label <- paste(scales::label_comma(accuracy= 1) (sum_positive), landscape_area_unit)
    
    negative_transitions_dataframe <- combined_optimized_dataframe %>%
      filter(transition_direction == 'decrease') %>%
      filter(mplc_optimized_value != 4 & RAP_optimized_value != 4) %>%
      mutate('factor' = factor(plot_label))
    negative_transitions_dataframe$factor <- fct_reorder(negative_transitions_dataframe$factor, negative_transitions_dataframe$total_grouped_area)
    sum_negative <- sum(negative_transitions_dataframe$area)
    sum_negative_label <- paste(scales::label_comma(accuracy= 1) (sum_negative), landscape_area_unit)
    
    pseudo_transitions_dataframe <- combined_optimized_dataframe %>%
      filter(mplc_optimized_value == 4 | RAP_optimized_value == 4) %>%
      mutate('factor' = factor(plot_label))
    pseudo_transitions_dataframe$factor <- fct_reorder(pseudo_transitions_dataframe$factor, pseudo_transitions_dataframe$total_grouped_area)
    sum_pseudo <- sum(pseudo_transitions_dataframe$area)
    sum_pseudo_label <- paste(scales::label_comma(accuracy= 1) (sum_pseudo), landscape_area_unit)
    
    total_changed_area <- paste(scales::label_comma(accuracy= 1) (sum_positive + sum_negative + sum_pseudo), landscape_area_unit)
    
    total_changed_area_percent <- round((((sum_positive + sum_negative + sum_pseudo)/landscape_area_numeric)*100),2)
    
    magenta_color_ramp <- colorRampPalette(c('#fef3fc', '#b73779'))
    magenta_color_ramp(length(levels(factor(negative_transitions_dataframe$factor))))
  
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = positive_transitions_dataframe,
                           aes(x = x, y = y, fill = factor(factor)))

    pl <- pl + scale_fill_manual(values = rev(brewer.pal(length(levels(factor(positive_transitions_dataframe$factor))), "Greens")),
                                 name = paste("positive transitions > 1 ‰ landscape area [ ∑", sum_positive_label, "]"),
                                 labels = rev(unique(levels(positive_transitions_dataframe$factor))),
                                 breaks = rev(unique(levels(positive_transitions_dataframe$factor))),
                                 guide = guide_legend(order = 1))
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = negative_transitions_dataframe,
                           aes(x = x, y = y, fill = factor(factor)))
    pl <- pl + scale_fill_manual(values = rev(c(magenta_color_ramp(length(levels(factor(negative_transitions_dataframe$factor)))))),
                                 name = paste("negative transitions > 1 ‰ landscape area [ ∑", sum_negative_label, "]"),
                                 labels = rev(unique(levels(negative_transitions_dataframe$factor))),
                                 breaks = rev(unique(levels(negative_transitions_dataframe$factor))),
                                 guide = guide_legend(order = 2))
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = pseudo_transitions_dataframe,
                           aes(x = x, y = y, fill = factor(factor)))
    pl <- pl + scale_fill_manual(values = rev(brewer.pal(length(levels(factor(pseudo_transitions_dataframe$factor))), "Purples")),
                                 name = paste("pseudo transitions > 1 ‰ landscape area [ ∑", sum_pseudo_label, "]"),
                                 labels = rev(unique(levels(pseudo_transitions_dataframe$factor))),
                                 breaks = rev(unique(levels(pseudo_transitions_dataframe$factor))),
                                 guide = guide_legend(order = 3))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    pl <- pl + labs(tag = paste('*Changed area [ ∑', total_changed_area, '=', total_changed_area_percent, '% of landscape area]:\nNumber of pixels present that have changed\nfrom mplc to RAP per transition class.\nExtreme transitions have been excluded.')) 
    pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    pl <- pl + theme(plot.tag.position = c(.6, .001),
                     plot.tag = element_text(family = user_defined_font, 
                                             size = user_defined_fontsize - user_defined_fontsize_factor,
                                             colour = user_defined_baseline_color,
                                             face = user_defined_other_face ,
                                             hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    
    mplc_raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified')
    mplc_flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential')
    
    RAP_raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape_transformed', 'normalized_reclassified')
    RAP_flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Omniscape', 'flow_potential')
    
    mplc_flow_potential_tibble <- tibble(
      file_name = list.files(mplc_flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(scenario = 'mplc',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    RAP_flow_potential_tibble <- tibble(
      file_name = list.files(RAP_flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(scenario = 'RAP',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    combined_flow_potential_tibble <- mplc_flow_potential_tibble %>% full_join(RAP_flow_potential_tibble)
    
    mplc_normalized_reclassified_tibble <- tibble(
      file_name = list.files(mplc_raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(scenario = 'mplc',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete)
    
    RAP_normalized_reclassified_tibble <- tibble(
      file_name = list.files(RAP_raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(scenario = 'RAP',
             time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) 
    
    combined_normalized_reclassified_tibble <- mplc_normalized_reclassified_tibble %>% full_join(RAP_normalized_reclassified_tibble)
    
    mplc_normalized_reclassified_tibble %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(#raster_file_location = .$file_name,
          plot_title = .$plot_title,
          climate_period = .$description,
          combined_normalized_reclassified_tibble,
          combined_flow_potential_tibble,
          current_year = .$year)
        
        tibble()
      }
      )
  }
}

# MS2: map presence with unimpeded flow - mplc #####
if (umbrella_species_presence_data_provided == TRUE) {
  
  plot_title <- paste('Habitat connectivity and presence mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period, 
                                          flow_potential, current_year) {
    
    legend_title <- "Selected flow classes"
    
    # get the reclassified data
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    
    # get the flow potential data
    flow_potential_year <- flow_potential %>%
      filter(year == current_year) 
    
    flow_potential_raster_location <- flow_potential_year$file_name
    
    flow_potential_raster = raster(flow_potential_raster_location)
    
    flow_potential_dataframe <- as.data.frame(flow_potential_raster, xy = TRUE) %>%
      drop_na %>%
      rename(fp_value = 3) %>%
      mutate('fp_threshold' = mean(fp_value) - sd(fp_value)) 
    
    # combine data frames and calculate new value
    optimized_dataframe <- raster_dataframe %>%
      left_join(flow_potential_dataframe, join_by(x, y)) %>%
      group_by(value) %>%
      mutate('optimized_value' = case_when(
        (value == 4 & fp_value < fp_threshold) ~ 4,
        (value == 4 & fp_value >= fp_threshold) ~ 5,
        (value == 1 ) ~ 1,
        (value == 2 ) ~ 2,
        (value == 3 ) ~ 3,
        (value == 5 ) ~ 6,
        (value == 6 ) ~ 7,
      )) %>%
      ungroup() %>%
      drop_na %>%
      filter(optimized_value %in% c(5, 6, 7))
    
    umbrella_species_presence_data <- umbrella_species_presence_data %>%
      mutate('value' = 1)
    sum_umbrella_species_presence_data <- sum(umbrella_species_presence_data$value)
    
    umbrella_species_presence_data_GBIF <- umbrella_species_presence_data_GBIF %>%
      mutate('value' = 1)
    sum_umbrella_species_presence_data_GBIF <- sum(umbrella_species_presence_data_GBIF$value)
    
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = optimized_dataframe,
                           aes(x = x, y = y, fill = as.factor(optimized_value)),
                           guide = guide_legend(order = 3)#,
                           #alpha = 0.75
    )
    pl <- pl + scale_fill_manual(values = c('1' = '#2a115c',
                                            '2' = '#aa337d',
                                            '3' = '#c23b75',
                                            '4' = '#6e1e81',
                                            '5' = '#95d840', 
                                            '6' = '#fed89a',
                                            '7' = '#fcfdbf'),
                                 labels = c('1' = 'blocked flow (<= 0.27)\n- no or nearly no movement potential',
                                            '2' = 'impeded flow (> 0.27 - 0.47)\n- limited movement potential',
                                            '3' = 'reduced flow (> 0.47 - 0.7)\n- movement edges in some directions',
                                            '4' = '*pseudo diffuse flow (> 0.7 - 1.3)\n- only mathematical result, de facto between blocked and impeded',
                                            '5' = 'robust diffuse flow (> 0.7 - 1.3)\n- well connected, movement edges in many directions',
                                            '6' = 'intensified flow (> 1.3 - 1.7)\n- edges between well connected and fragmented',
                                            '7' = 'channelized flow (> 1.7)\n- potential habitat corridors and pinch points'  
                                 ))
    pl <- pl + new_scale_color()
    pl <- pl + geom_sf(data = umbrella_species_presence_data_GBIF,
                       aes(color = paste0('(independent) sightings 2010 to 2024 (', sum_umbrella_species_presence_data_GBIF, ')')),
                       size = 0.5, 
                       shape = 3)
    pl <- pl + scale_color_manual(name = 'Presence points - GBIF',
                                  values = c('black'),
                                  guide = guide_legend(order = 2))
    pl <- pl + new_scale_color()
    pl <- pl + geom_sf(data = umbrella_species_presence_data,
                       aes(color = paste0('independent sightings 2013 (', sum_umbrella_species_presence_data, ')')),
                       size = 0.5)
    pl <- pl + scale_color_manual(name = 'Presence points - own data',
                                  values = c('darkred'),
                                  guide = guide_legend(order = 1))
    
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    #pl <- pl + theme(legend.position = 'bottom')
    pl <- pl + theme(legend.key.height=unit(1, "cm"))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    # add tag
    # pl <- pl + labs(tag = paste('*pseudo diffuse flow:\nArea, where division of flow potential and observed values\nyields values around 1 but flow potential is\nbelow one standard deviation subtracted from the mean.')) 
    # pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
    # pl <- pl + theme(plot.tag.position = c(.60, .1),
    #                  plot.tag = element_text(family = user_defined_font, 
    #                                          size = user_defined_fontsize - user_defined_fontsize_factor,
    #                                          colour = user_defined_baseline_color,
    #                                          face = user_defined_other_face ,
    #                                          hjust = 0))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape_transformed', 'normalized_reclassified')
    flow_potential_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Omniscape', 'flow_potential')
    
    flow_potential_tibble <- tibble(
      file_name = list.files(flow_potential_input_folder, full.names = TRUE)
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,)
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description,
                                    flow_potential = flow_potential_tibble,
                                    current_year = .$year)
        
        tibble()
      }
      )
  }
}

### MS2: Potential Habitat Corridors (PHCs) Circuitscape #######################
# Circuitscape in advanced mode ################################################
# > Curmap - mplc ####
if (performed_Circuitscape_analysis_advanced_mplc == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors curmap mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Current [amps per cell]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    min_floor = signif(min_range, digits = 1) 
    max_floor = floor(max_range)
    set_breaks <- c(min_floor, 0.01, 0.1, 1, max_floor)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum,
                                    breaks = set_breaks, 
                                    labels = set_breaks, 
                                    trans = scales::pseudo_log_trans(sigma = 0.001))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + theme(legend.spacing.y = unit(0.5, 'cm'))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'curmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Curmap - RAP ####
if (performed_Circuitscape_analysis_advanced_RAP == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors curmap RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Current [amps per cell]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    min_floor = signif(min_range, digits = 1) 
    max_floor = floor(max_range)
    set_breaks <- c(min_floor, 0.01, 0.1, 1, max_floor)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum,
                                    breaks = set_breaks, 
                                    labels = set_breaks, 
                                    trans = scales::pseudo_log_trans(sigma = 0.001))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'curmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Voltmap - mplc ####
if (performed_Circuitscape_analysis_advanced_mplc == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors voltmap mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Volt"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    #pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    #pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum, breaks = c(0.9, 1.1, midpoint = 1))
    #pl <- pl + scale_colour_steps2(midpoint = 1)
    pl <- pl + scale_fill_gradient2(midpoint = 1,
                                    low = viridis(n = 10, option = 'mako', direction = -1),
                                    high = viridis(n = 10, option = 'viridis', direction = 1),
                                    mid = 'magenta',
                                    space = 'Lab')
    # pl <- pl + scale_fill_gradientn(colors = c('#21918c','magenta', '#fde725'),
    #                                 values = rescale(c(min_range, 1, max_range)),
    #                                 limits = c(min_range, max_range))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'voltmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Voltmap - RAP ####
if (performed_Circuitscape_analysis_advanced_RAP == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors voltmap RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Volt"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    #pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    #pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum, breaks = c(0.9, 1.1, midpoint = 1))
    #pl <- pl + scale_colour_steps2(midpoint = 1)
    pl <- pl + scale_fill_gradient2(midpoint = 1,
                                    low = viridis(n = 10, option = 'mako', direction = -1),
                                    high = viridis(n = 10, option = 'viridis', direction = 1),
                                    mid = 'magenta',
                                    space = 'Lab')
    # pl <- pl + scale_fill_gradientn(colors = c('#21918c','magenta', '#fde725'),
    #                                 values = rescale(c(min_range, 1, max_range)),
    #                                 limits = c(min_range, max_range))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'voltmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# Circuitscape in pairwise mode ################################################
# > Cumulative curmap - mplc ####
if (performed_Circuitscape_analysis_pairwise_mplc == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors cumulative curmap mplc for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Current [amps per cell]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    min_floor = signif(min_range, digits = 1) 
    max_floor = floor(max_range)
    set_breaks <- c(min_floor, 0.01, 0.1, 1, max_floor)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum,
                                    breaks = set_breaks, 
                                    labels = set_breaks, 
                                    trans = scales::pseudo_log_trans(sigma = 0.001))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + theme(legend.spacing.y = unit(0.5, 'cm'))
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'Circuitscape', 'cum_curmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}

# > Cumulative curmap - RAP ####
if (performed_Circuitscape_analysis_pairwise_RAP == TRUE) {
  
  plot_title <- paste('Potential Habitat Corridors cumulative curmap RAP for umbrella species', umbrella_species_name)
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, climate_period) {
    
    legend_title <- "Current [amps per cell]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    
    min_range = min(raster_dataframe$value)
    max_range = max(raster_dataframe$value)
    min_floor = signif(min_range, digits = 1) 
    max_floor = floor(max_range)
    set_breaks <- c(min_floor, 0.01, 0.1, 1, max_floor)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis_c(option = user_defined_color_spectrum,
                                    breaks = set_breaks, 
                                    labels = set_breaks, 
                                    trans = scales::pseudo_log_trans(sigma = 0.001))
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape, climate_period, sep = ' | '))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
    start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case) 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    start_year_i <- scenarios[i,] %>%
      pull(start_year)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'Circuitscape', 'cum_curmap')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
             year = time_step + start_year_i - 1,
             plot_title = paste(plot_title, scenario_i, year)) %>%
      left_join(climate_periods_complete) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    climate_period = .$description)
        
        tibble()
      }
      )
  }
}



### MS2: averaged maps user-defined simulation time frames #################
# > mplc ####

if (user_defined_averaging_of_habitat_analysis_results_applied == TRUE) {
  
  plot_title <- paste('Averaged rescaled voltmap mplc for umbrella-species', umbrella_species_name, 'for user-defined period')
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title) {
    
    legend_title <- "Voltmap rescaled [volt]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(value != 0)
      
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape))
    pl
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation') 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'LPB-RAP_averaged_results')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(raster_period = str_sub(file_name, -13, -5),
             plot_title = paste(paste(plot_title, raster_period), scenario_i)) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title)
        
        tibble()
      }
      )
  }
}

# > RAP ####
if (user_defined_averaging_of_habitat_analysis_results_applied == TRUE) {
  
  plot_title <- paste('Averaged rescaled voltmap RAP for umbrella-species', umbrella_species_name, 'for user-defined period')
  
  create_plot_for_raster_file <- function(raster_file_location,
                                          plot_title, raster_period) {
    
    legend_title <- "Voltmap rescaled [volt]"
    
    raster_to_process <- raster(raster_file_location)
    
    raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>%
      drop_na %>%
      rename(value = 3) %>%
      filter(., value != 0)
    
    pl <- ggplot() 
    # plot_all
    pl <- pl + dem_hillshade_layer
    pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
    pl <- pl + new_scale_fill()
    pl <- pl + geom_raster(data = raster_dataframe,
                           aes(x = x, y = y, fill = value))
    pl <- pl + scale_fill_viridis(option = user_defined_color_spectrum)
    # transform
    pl <- pl + coord_sf(crs = user_defined_EPSG)
    # # add attributes, themes and labs
    pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                           bar_cols = c(user_defined_baseline_color, "white"),
                                           text_family = user_defined_font)
    pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                                 which_north = "true",
                                                 pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                                 pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                                 style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                   line_col = user_defined_baseline_color,
                                                                                                   text_family = user_defined_font))
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.title.x = element_blank(),
                     axis.title.y = element_blank())
    pl <- pl + theme(panel.grid.minor.x = element_blank(),
                     panel.grid.minor.y = element_blank())
    pl <- pl + labs(title = plot_title,
                    subtitle = paste(subtitle_prefix),
                    fill = legend_title,
                    caption = paste(caption_landscape))
    
    ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
  }
  
  scenarios <- tibble(
    scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation') 
  )
  
  for (i in seq_along(scenarios$scenario_name)) {
    scenario_i <- scenarios[i,] %>%
      pull(scenario_name)
    
    raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'LPB-RAP_averaged_results')
    
    tibble(
      file_name = list.files(raster_type_input_folder, full.names = TRUE),
    ) %>%
      mutate(raster_period = str_sub(file_name, -13, -5),
             plot_title = paste(paste(plot_title, raster_period), scenario_i)) %>%
      rowwise() %>%
      do({
        print(paste('plotting', .$plot_title))
        create_plot_for_raster_file(raster_file_location = .$file_name,
                                    plot_title = .$plot_title,
                                    raster_period = .$raster_period)
        
        tibble()
      }
      )
  }
}

###MS2: Habitat analysis inputs#################################################
## Resistance #####
#>mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- resistances surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Resistance values"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*highest number decimal places\nshows the calculated map average\nif a calculated landscape buffer\nof size radius was used.')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.85, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'resistances')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

#>RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- resistances surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Resistance values"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*highest number decimal places\nshows the calculated map average\nif a calculated landscape buffer\nof size radius was used.')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.85, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'resistances')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

# Source from resistance #####
#> mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- source from resistances surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Source from Resistance values"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  inverted_dataframe = raster_dataframe %>%
    rowwise() %>%
    mutate('inverted_value' = signif((1/value), d = 1 ))
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = inverted_dataframe,
                         aes(x = x, y = y, fill = factor(inverted_value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*calculated source from resistance values\n')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.75, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'resistances')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}
#> RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- source from resistances surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Source from Resistance values"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  inverted_dataframe = raster_dataframe %>%
    rowwise() %>%
    mutate('inverted_value' = signif((1/value), d = 1 ))
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = inverted_dataframe,
                         aes(x = x, y = y, fill = factor(inverted_value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*calculated source from resistance values\n')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.75, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'resistances')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}



# Sources #####
#> mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- sources surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Source values [Amps]"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  # add tag
  pl <- pl + labs(tag = paste('*manually set source values\nas noted in Parameters.py')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.90, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'sources')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

#> RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- sources surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Source values [Amps]"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  # add tag
  pl <- pl + labs(tag = paste('*manually set source values\nas noted in Parameters.py')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.90, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'sources')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}


# Grounds ####
#> mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- grounds surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Grounds values [Ohms]"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'grounds')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

#> RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- grounds surface")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Grounds values [Ohms]"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'grounds')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

# Polygons #####
#> mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- polygons")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Calculated polygons"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*polygons are user-defined derived\nper time step based on\ncore habitat land use types\nand minimum patch size')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.85, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'polygons')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}

#> RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- polygons")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Calculated polygons"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  pl <- pl + new_scale_fill()
  pl <- pl + geom_raster(data = raster_dataframe,
                         aes(x = x, y = y, fill = factor(value)),
                         show.legend = TRUE) 
  pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  
  # add tag
  pl <- pl + labs(tag = paste('*polygons are user-defined derived\nper time step based on\ncore habitat land use types\nand minimum patch size')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.85, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'polygons')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}
# Points ####
#> mplc ####
plot_title <- paste("Habitat analysis input mplc for umbrella species", umbrella_species_name, "- points")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  
  legend_title <- "Derived points from polygons"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  points_sf <- sf::st_as_sf(raster_dataframe, coords = c('x', 'y'), crs = user_defined_EPSG)
  circles_sf <- sf::st_buffer(points_sf, dist = 10000)
  
  # add one random element for the legend
  random_datapoint <- sample_n(raster_dataframe,1)
  random_point_sf <- sf::st_as_sf(random_datapoint, coords = c('x', 'y'), crs = user_defined_EPSG)
  random_circle_sf <- sf::st_buffer(random_point_sf, dist = 10000)
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  
  pl <- pl + new_scale_fill()
  pl <- pl + geom_sf(data = random_circle_sf,
                     aes(color = 'black'),
                     alpha = 0, 
                     show.legend = TRUE,
                     key_glyph = 'point')
  pl <- pl + scale_colour_manual(name = '',
                                 labels = c("pixel buffer highlight of 10 km"),
                                 values = c('black'))
  pl <- pl + guides(colour = guide_legend(override.aes = list(shape = 1, size=7, col='black')))
  
  pl <- pl + new_scale_color()
  pl <- pl + geom_sf(data = circles_sf,
                     color = 'black', 
                     alpha = 0, 
                     inherit.aes = FALSE, 
                     show.legend = FALSE)
  
  pl <- pl + new_scale_color()
  pl <- pl + geom_sf(data = points_sf,
                     aes(color = factor(value)),
                     show.legend = TRUE,
                     inherit.aes = FALSE,
                     key_glyph = "point")
  pl <- pl + scale_color_viridis_d(name = legend_title,
                                   labels = c(factor(points_sf$value)))
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  # add tag
  pl <- pl + labs(tag = paste('*points are automatically randomly derived\nfrom prior calculated polygons\n[1 point per polygon]')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.75, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_MPLC', 'INPUTS', 'points')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}


#> RAP ####
plot_title <- paste("Habitat analysis input RAP for umbrella species", umbrella_species_name, "- points")

create_plot_for_raster_file <- function(raster_file_location,
                                        plot_title, climate_period) {
  legend_title <- "Derived points from polygons"
  
  raster_to_process <- raster(raster_file_location)
  
  raster_dataframe <- as.data.frame(raster_to_process, xy = TRUE) %>% 
    drop_na %>%
    rename(value = 3) 
  
  points_sf <- sf::st_as_sf(raster_dataframe, coords = c('x', 'y'), crs = user_defined_EPSG)
  circles_sf <- sf::st_buffer(points_sf, dist = 10000)
  
  # add one random element for the legend
  random_datapoint <- sample_n(raster_dataframe,1)
  random_point_sf <- sf::st_as_sf(random_datapoint, coords = c('x', 'y'), crs = user_defined_EPSG)
  random_circle_sf <- sf::st_buffer(random_point_sf, dist = 10000)
  
  
  pl <- ggplot()  
  pl <- pl + dem_hillshade_layer
  pl <- pl + scale_fill_gradient(low = "darkgrey", high = "white")
  
  pl <- pl + new_scale_fill()
  pl <- pl + geom_sf(data = random_circle_sf,
                     aes(color = 'black'),
                     alpha = 0, 
                     show.legend = TRUE,
                     key_glyph = 'point')
  pl <- pl + scale_colour_manual(name = '',
                                 labels = c("pixel buffer highlight of 10 km"),
                                 values = c('black'))
  pl <- pl + guides(colour = guide_legend(override.aes = list(shape = 1, size=7, col='black')))
  
  pl <- pl + new_scale_color()
  pl <- pl + geom_sf(data = circles_sf,
                     color = 'black', 
                     alpha = 0, 
                     inherit.aes = FALSE, 
                     show.legend = FALSE)
  
  pl <- pl + new_scale_color()
  pl <- pl + geom_sf(data = points_sf,
                     aes(color = factor(value)),
                     show.legend = TRUE,
                     inherit.aes = FALSE,
                     key_glyph = "point")
  pl <- pl + scale_color_viridis_d(name = legend_title,
                                   labels = c(factor(points_sf$value)))
  pl <- pl + coord_sf(crs = user_defined_EPSG)
  # # add attributes, themes and labs
  pl <- pl + ggspatial::annotation_scale(location = user_defined_map_scale_location,
                                         bar_cols = c(user_defined_baseline_color, "white"),
                                         text_family = user_defined_font)
  pl <- pl + ggspatial::annotation_north_arrow(location = user_defined_north_arrow_location,
                                               which_north = "true",
                                               pad_x = unit(user_defined_north_arrow_pad_x, user_defined_north_arrow_unit),
                                               pad_y = unit(user_defined_north_arrow_pad_y, user_defined_north_arrow_unit),
                                               style = ggspatial::north_arrow_fancy_orienteering(fill = c(user_defined_baseline_color, "white"),
                                                                                                 line_col = user_defined_baseline_color,
                                                                                                 text_family = user_defined_font))
  pl <- pl + theme_LPB_RAP
  pl <- pl + theme(axis.title.x = element_blank(),
                   axis.title.y = element_blank())
  pl <- pl + theme(panel.grid.minor.x = element_blank(),
                   panel.grid.minor.y = element_blank())
  pl <- pl + labs(title = plot_title,
                  subtitle = paste(subtitle_prefix),
                  caption = paste(caption_landscape, climate_period, sep = ' | '),
                  fill = legend_title)
  # add tag
  pl <- pl + labs(tag = paste('*points are automatically randomly derived\nfrom prior calculated polygons\n[1 point per polygon]')) 
  pl <- pl + coord_sf(crs = user_defined_EPSG, clip = "off") 
  pl <- pl + theme(plot.tag.position = c(.75, .1),
                   plot.tag = element_text(family = user_defined_font, 
                                           size = user_defined_fontsize - user_defined_fontsize_factor,
                                           colour = user_defined_baseline_color,
                                           face = user_defined_other_face ,
                                           hjust = 0))
  
  ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

scenarios <- tibble(
  scenario_name = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  start_year = c(initial_simulation_year_BAUs , initial_simulation_year_BAUs, initial_simulation_year_worst_case)
)

for (i in seq_along(scenarios$scenario_name)) {
  scenario_i <- scenarios[i,] %>%
    pull(scenario_name)
  start_year_i <- scenarios[i,] %>%
    pull(start_year)
  
  raster_type_input_folder <- file.path(input_folder, scenario_i, 'HABITAT_ANALYSIS_RAP', 'INPUTS', 'points')
  
  tibble(
    file_name = list.files(raster_type_input_folder, full.names = TRUE),
  ) %>%
    mutate(time_step = as.numeric(str_sub(file_name, -7, -5)),
           year = time_step + start_year_i - 1,
           plot_title = paste(plot_title, scenario_i, year)) %>%
    left_join(climate_periods_complete) %>%
    rowwise() %>%
    do({
      print(paste('plotting', .$plot_title))
      create_plot_for_raster_file(raster_file_location = .$file_name,
                                  plot_title = .$plot_title,
                                  climate_period = .$description)
      
      tibble()
    }
    )
}




##################################################################################################################################
### END CODE Model Stage 2 #######################################################################################################
##################################################################################################################################







