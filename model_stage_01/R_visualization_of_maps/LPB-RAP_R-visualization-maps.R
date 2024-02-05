# general plotting
library(tidyverse)
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
library(GISTools)
library(maps)
#install.packages("rnaturalearthhires", repos = "http://packages.ropensci.org", type = "source")
library(rnaturalearth)
library(rosm)

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
model_stage <- 'MS1'

# define here if you simulated demands with an 'internal' or 'external' time series
time_series_input <- 'external'

# => define the main model folder for which analysis shall be run (separate by baseline scenario and region)
main_model_folder <- "LULCC_ECU_Esmeraldas_SSP2-4.5" # "LULCC_ECU_Esmeraldas_SSP2-4.5"

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
  'weak_conservation' = c(2018, 2030, 2050, 2060, 2080, 2100),
  'enforced_conservation' = c(2018, 2030, 2050, 2060, 2080, 2100),
  'no_conservation' = c(2025, 2030, 2039, 2050, 2060, 2080, 2100)
)

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

# >>> TODO: make this obsolete: define the probing dates in time steps ####
# MS2: add your peak demands year time step
probing_dates_time_steps = list(
  'weak_conservation' = c(1, 13, 33, 43, 63, 83),
  'enforced_conservation' = c(1, 13, 33, 43, 63, 83),
  'no_conservation' = c(1, 6, 26, 36, 56, 76)
)
  
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

# MS2: if you simulated fragmentation set the variable to true
fragmentation_simulated <- TRUE

# MS2: if you simulated potential habitat corridors set the variable to true
potential_habitat_corridors_simulated <- TRUE

# define the colors you want to be displayed for Land Use Types (so far 18 + 4)
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
# LUT12	water (static LUT, steelblue)
# LUT13	no input (static LUT, slategrey)
# LUT14	cropland-annual - - abandoned (indirect active LUT, orange) - supposed to pop out
# LUT15	pasture - - abandoned (indirect active LUT, chartreuse) - supposed to pop out
# LUT16	agroforestry - - abandoned (indirect active LUT, blueviolet) - supposed to pop out
# LUT17	net forest - - deforested (indirect active LUT, deeppink) - supposed to pop out
# LUT18	plantation - - deforested (indirect active LUT, deeppink3) - supposed to pop out
# LUT21	RAP agroforestry for traditional farming systems (RAP LUT, greenyellow) - indicates more forest cover
# LUT22	RAP plantation (RAP LUT, springgreen) - indicates more forest cover
# LUT23	RAP reforestation (RAP LUT, lawngreen) - indicates more forest cover
# LUT24	RAP other ecosystems (RAP LUT, azure) - indicates mainly ecosystems related to the "blue section"
# MS2: Only if you simulated local wood consumption / degradation: LUT25 (RAP LUT, palegreen is added automatically)

# create named vector that links lut values and lut colors 
LUT_colors <- tibble(
  lut_value = c(1,2,3,4,5, 6,7,8,9, 10,11,12,13, 14,15,16,17,18, 21,22,23,24),
  colors = c("firebrick", "gold", "palegreen", "olivedrab", "cadetblue4",
            "moccasin", "chocolate", "limegreen", "darkgreen",
            "powderblue", "lavender", "steelblue", "slategrey",
            "orange", "chartreuse","blueviolet", "deeppink","deeppink3", 
            "greenyellow", "springgreen", "lawngreen", "azure")
) %>%
  mutate(LUT_code = paste('LUT', str_pad(lut_value, 2, 'left', '0'), sep = ''))

# for your personal regional landscape slope categories depiction define here the slope values, note: the model output is e.g. 0.1 for 10%
user_defined_slope_category_breaks = c(-0.1, 0.05, 0.15, 0.30, 0.45, 2) # note segments +1, 20 -> 200% maximum % value
user_defined_slope_category_names = c("0 - 5", ">5 - 15", ">15 - 30", ">30 - 45", ">45")

# define until which length numbers will be written and not given in scientific notation:
options(scipen = 999999)

# give the total simulated landscape area and unit 
landscape_area <- 1678488
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

if (local_degradation_simulated == TRUE) {
  LUT_colors <- tibble(
    lut_value = c(1,2,3,4,5, 6,7,8,9, 10,11,12,13, 14,15,16,17,18, 21,22,23,24,25),
    colors = c("firebrick", "gold", "palegreen", "olivedrab", "cadetblue4",
               "moccasin", "chocolate", "limegreen", "darkgreen",
               "powderblue", "lavender", "steelblue", "slategrey",
               "orange", "chartreuse","blueviolet", "deeppink","deeppink3", 
               "greenyellow", "springgreen", "lawngreen", "azure", "palegreen")
  ) %>%
    mutate(LUT_code = paste('LUT', str_pad(lut_value, 2, 'left', '0'), sep = ''))
  print.data.frame(LUT_colors)
}

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

# # how to use
# source_folder <- file.path(model_output_folder, 'outputs_worst-case', 'LPB', 'LULCC_Simulation', 'dynamic_population_deterministic')
# 
# list_of_source_files <- filter_for_probing_dates(probing_dates = probing_dates_time_steps[['BAU']],
#                          list.files(source_folder))
# 
# maps_info <- add_datamap(
#   'xyz',
#   source_folder,
#   'xyz',
#   list_of_source_files
# )

# ### DK Test tifs ####
# file_path_map <- file.path(model_output_folder, 'outputs_BAU', 'LPB', 'model_internal_slope_map', 'model_internal_slope_map_in_percent.map')
# map_file <- file_path_map
# raster_file <- raster(map_file)
# raster_file

# source_folder <- file.path(model_output_folder, 'outputs_BAU', 'LPB', 'LULCC_most_probable_landscape_configuration', 'initial_most_probable_landscape_configuration')
# 
# list_of_source_files <- list.files(source_folder)
# 
# maps_info <- add_dataset(
#   'initial_most_probable_landscape_configuration',
#   file.path(model_output_folder, 'outputs_BAU', 'LPB', 'LULCC_most_probable_landscape_configuration', 'initial_most_probable_landscape_configuration'),
#   file.path(input_folder, 'BAU', 'initial_most_probable_landscape_configuration'),
#   list_of_source_files
# )

# source_folder <- file.path(model_output_folder, 'outputs_BAU', 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic', '1')
# 
# list_of_source_files <- list.files(source_folder)
# 
# maps_info <- add_dataset(
#   'temp_sankey_dk',
#   source_folder,
#   file.path(input_folder, 'BAU', 'temp_sankey_dk','1'),
#   list_of_source_files
# )
# 
# source_folder <- file.path(model_output_folder, 'outputs_BAU', 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic', '2')
# 
# list_of_source_files <- list.files(source_folder)
# 
# maps_info <- add_dataset(
#   'temp_sankey_dk',
#   source_folder,
#   file.path(input_folder, 'BAU', 'temp_sankey_dk','2'),
#   list_of_source_files
# )
# 
# source_folder <- file.path(model_output_folder, 'outputs_BAU', 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic', '3')
# 
# list_of_source_files <- list.files(source_folder)
# 
# maps_info <- add_dataset(
#   'temp_sankey_dk',
#   source_folder,
#   file.path(input_folder, 'BAU', 'temp_sankey_dk','3'),
#   list_of_source_files
# )

######################


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

# BAU(+)
maps_info <- add_dataset(
  'targeted_net_forest',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'RAP', 'targeted_net_forest'),
  file.path(input_folder, 'enforced_conservation', 'Targeted_net_forest'),
  'RAP_tnf0.001'
)

# worst-case
maps_info <- add_dataset(
  'targeted_net_forest',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_no_conservation', 'RAP', 'targeted_net_forest'),
  file.path(input_folder, 'no_conservation', 'Targeted_net_forest'),
  'RAP_tnf0.001'
)

# - potential additional restricted areas BAU BAU(+) (discrete scale)
# PATH: outputs_(scenario-folder) > RAP > restricted_areas > RAP_restricted_areas.map
# BAU
maps_info <- add_dataset(
  'potential_restricted_areas',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_weak_conservation', 'RAP', 'restricted_areas'),
  file.path(input_folder, 'weak_conservation', 'Potential_restricted_areas'),
  'RAP_restricted_areas.map'
)

# BAU(+)
maps_info <- add_dataset(
  'potential_restricted_areas',
  file.path(model_output_folder,  demand_configuration_outputs_folder, 'outputs_enforced_conservation', 'RAP', 'restricted_areas'),
  file.path(input_folder, 'enforced_conservation', 'Potential_restricted_areas'),
  'RAP_restricted_areas.map'
)

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


# copy files 
### ATTENTION WINDOWS USERS: THIS IS NOT APPLICABLE ON WINDOWS OS, you need to transform maps to tifs manually in a GIS #####
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
      
      # TEST CODE CRS
      #crs(raster_file) <- paste("EPSG:", user_defined_EPSG, sep = '')
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

raster_map_LULC_simulated_BAUplus <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial_simulated_enforced_conservation'), full.names = TRUE))
raster::crs(raster_map_LULC_simulated_BAUplus) <- paste("EPSG:", user_defined_EPSG, sep = '')

raster_map_LULC_simulated_worst_case <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'LULC_initial_worst-case'), full.names = TRUE))
raster::crs(raster_map_LULC_simulated_worst_case) <- paste("EPSG:", user_defined_EPSG, sep = '')

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

raster_map_initial_pop_worst_case <- raster::raster(list.files(file.path(import_folder, 'deterministic', 'Population', 'initial_population_worst-case'), full.names = TRUE))
raster::crs(raster_map_initial_pop_worst_case) <- paste("EPSG:", user_defined_EPSG, sep = '')

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

# Population initial interpolated worst-case
plot_title <- paste("Population interpolated for", initial_simulation_year_worst_case)
legend_title <- "Population"

raster_to_process <- raster_map_initial_pop_worst_case

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

### BAU(+) ####
plot_title <- "LPB simulated LULC after correction step enforced conservation"
LUT_title <- "Land Use Types"

raster_to_process <- raster_map_LULC_simulated_BAUplus

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

### worst-case #################################################################
plot_title <- "LPB simulated LULC for no conservation"
LUT_title <- "Land Use Types"

raster_to_process <- raster_map_LULC_simulated_worst_case

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
                subtitle = paste(subtitle_prefix, initial_simulation_year_worst_case),
                caption = caption_landscape,
                fill = LUT_title)
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### > Overview plots: #########################################################

## Study area, Country and Region ##############################################
rosm::osm.types()

plot_title <- "Study area"

# # world country context
# world_country_dataframe <- ne_countries(scale = "medium", type = "map_units", returnclass = "sf")
# world_country_layer <- geom_sf(data = world_country_dataframe)
# 
# sf::sf_use_s2(FALSE)
# world_country_cropped <- st_crop(world_country_dataframe,
#                                        xmin = -95,
#                                        xmax = -70,
#                                        ymin = -6,
#                                        ymax = 2)
# world_country_cropped
# world_country_cropped_layer <- geom_sf(data = world_country_cropped, 
#                                        color = user_defined_baseline_color,
#                                        fill = "antiquewhite", 
#                                        inherit.aes = FALSE)

# country states context
country_states_dataframe <- ne_states(country = country, returnclass = "sf") 
country_states_layer <- geom_sf(data = country_states_dataframe, 
                                fill = "white", 
                                inherit.aes = FALSE)

# study region
raster_null_mask_dataframe <- as.data.frame(raster_map_null_mask, xy = TRUE) %>% 
  drop_na %>%
  rename (value = static_null_mask_input)

# plot
pl <- ggplot(country_states_dataframe)
pl <- pl + ggspatial::annotation_map_tile(data = country_states_dataframe, 
                                          type = "http://a.tile.stamen.com/toner/${z}/${x}/${y}.png",
                                          zoomin = -2)
pl <- pl + country_states_layer 
pl <- pl + geom_raster(data = raster_null_mask_dataframe,
                       aes(x = x, y = y, fill = "firebrick"),
                       alpha = 0.5,
                       show.legend = FALSE,
                       inherit.aes = FALSE)
pl <- pl + coord_sf(crs = user_defined_EPSG, 
                    expand = FALSE)
# add attributes, themes and labs
pl <- pl + ggspatial::annotation_scale(location = "bl",
                                       bar_cols = c(user_defined_baseline_color, "white"),
                                       text_family = user_defined_font)
pl <- pl + ggspatial::annotation_north_arrow(location = "bl",
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
plot_study_area <- pl

pl <- pl + labs(title = plot_title,
                subtitle = paste(country, region),
                caption = "Regional study area in the country context | Sources basemaps: rnaturalearth, OSM/Stamen")
ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



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
plot_title <- "RAP potential restricted areas based on peak demands land use mask"

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

# ### MS2 TODO: fragmentation mplc RAP maps probing dates ########################
# if (fragmentation_simulated == TRUE) {
#   plot_title <- 'Fragmentation mplc RAP juxtaposition'
#   # code in brackets and for scenario use: fragmentation map mplc and RAP (maybe two in one per probing date)
# }
# 
# ### MS2 TODO: PHC conflict pixels probing dates ################################
# if (potential_habitat_corridors_simulated == TRUE) {
#   plot_title <- 'Potential Habitat Corrdiors conflict pixels'
#   # code in brackets and for scenario use: mplc, RAP probing dates + population peak + peak demands year
# }
# 
# ### MS2 TODO: PHC probability map entire simulation time frame #################
# if (potential_habitat_corridors_simulated == TRUE) {
#   plot_title <- 'Potential Habitat Corrdiors probability map entire simulation time frame'
#   # code in brackets and for scenario use: mplc, RAP probability maps entire simulation time frame
# }
# 
# ### MS2 TODO: PHC probability map population peak year and peak demand year ####
# if (potential_habitat_corridors_simulated == TRUE) {
#   plot_title <- 'Potential Habitat Corrdiors probability map peak demands year'
#   # code in brackets and for scenario use: mplc, RAP probability maps population peak year and peak demands year
# }

##################################################################################################################################
### END CODE Model Stage 2 #######################################################################################################
##################################################################################################################################

### TODO CITATIONS #############################################################
# # general plotting
# library(tidyverse)
# library(ggplot2)
# library(lubridate)
# library(viridis)  
# library(magrittr)
# library(tidyr)
# library(ggnewscale)
# # install.packages("devtools")
# # devtools::install_github("eliocamp/ggnewscale@dev")
# library(ggrepel) # out?
# library(ggridges) # out?
# library(ggthemes)
# 
# # data processing
# library(foreign) # for reading dbfs
# library(dplyr)
# library(gridExtra) # to arrange grid plots
# 
# # spatial and raster processing
# library(stars)
# library(raster)
# library(rasterVis)
# library(rgdal)
# library(dismo) #map raster on Google Map
# library(ggspatial)
# library(sf)
# library(sp)
# library(ggmap)
# library(scales)
# library(elevatr)
# library(GISTools)
# library(maps)
# library(ggsn)

# TODO CITATIONS ####
citation(package = "base", lib.loc = NULL, auto = NULL)
# readCitationFile(file, meta = NULL)
citation(package = "tidyverse", lib.loc = NULL, auto = NULL)








