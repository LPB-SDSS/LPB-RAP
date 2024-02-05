library(tidyverse)
library(ggplot2)
library(lubridate)
library(viridis)  
library(magrittr)
library(tidyr)
library(ggnewscale)
library(ggrepel)
library(ggridges)
library(cowplot)
#install.packages("remotes")
remotes::install_github("davidsjoberg/ggsankey")
library(ggsankey)
library(dplyr)
library(patchwork)
library(hrbrthemes)
library(circlize)
library(networkD3)
library(webshot)
#webshot::install_phantomjs()
library(png)
library(ggpubr)


# Model stage 1 (MS1) authors: DK & SH, 2022/Q2
# Model stage 2 (MS2) authors: DK & SH, 2023/Q2


### User required preparations MS1: ############################################
# for settings delivering results as in in Holler et al., 2023a:
# run all three policy scenarios for one region in one baseline scenario within the accordingly named main model folder
# create two empty folders for inputs (e.g. "R_inputs") and outputs (e.g. "R_outputs") within this folder
# Adjust the 'user-defined settings' section below to your model, your liking or study (area) and install required packages.
# Run script (inputs will be loaded automatically from your main model policy scenario output folders)

### User required preparations MS2: ############################################
# for settings delivering results as in in Holler et al., 2023b:
# for MS2 the code has been slightly altered, so that it can be run on one policy scenario (weak_conservation) only 
# if you simulated with an external demand series note the peak demands year of the run you just ended (see CSVs)
# define if you simulated with MS2 options for the specified variables
# additional new diagrams are placed in the new MS2 Code section

############################################################################################################################
### MS1: R SCRIPT for LPB-RAP forest policy scenarios and mplc/RAP comparison on one baseline scenario for one region ######
### MS2: R SCRIPT for LPB-RAP for one forest policy scenarios and mplc/RAP comparison on one baseline scenario for one region and additional simulation options ######
############################################################################################################################


# user-defined settings (SH) ---------------------------------------------------------------------------------------------------------------------------------------------

# MS: define here if you simulated in MS1 or MS2
model_stage <- 'MS1'

# => define the main model folder for which analysis shall be run (separate by baseline scenario and region)
main_model_folder <- "LULCC_ECU_Esmeraldas_SSP2-4.5" # "LULCC_ECU_Esmeraldas_SSP2-4.5"

# => define here which demand configuration you used: 'footprint_internal', 'footprint_external', 'yield_units_deterministic' or 'yield_units_stochastic'
demand_configuration <- "footprint_external"

# define here if you simulated demands with an 'internal' or 'external' time series
time_series_input <- 'external'

# define the R_inputs folder you use
input_folder <- "R_inputs"

# => define the basic output settings:
# define output folder
output_folder <- "R_outputs"

# define graphs output format
output_format <- ".png"

# define output height and width and unit ("in", "cm", "mm", "px") A4 portrait: 21 x 29.7 cm resp. 2480 x 3508 pixels (print resolution)
output_height <- 6.69 * 2.54 # (A4 landscape with fringe; for Portrait format small: 3.94 inch * factor to -> 10 cm)
output_width <- 10.12 * 2.54 # (A4 landscape with fringe; for Portrait format small: 6.69 inch * factor to > 17 cm)
output_unit <- "cm"  # default unit is "in". If "cm", simply transform height and width from inches to cm

# define output dpi, "retina" (320), "print" (300), or "screen" (72). Applies only to raster output types.
output_dpi = 320

# => define the output appearance:
# define the ggplot basic theme (theme_light() used for development)
ggplot_base_theme <- theme_light()
ggpubr_table_theme <- ttheme("light")

# => Define theme alterations:
# choose the font to be used out of sans, serif and mono (universal fonts)
user_defined_font <- "sans"

# choose the font size to be used for main information
user_defined_fontsize <- 11

# choose by which degree less important information should be displayed (e.g. 2 if you want font size 9 contrasting 11)
user_defined_fontsize_factor <- 2

# define the smallest used font size, only applied to annotation labels in plots - ATTENTION THIS IS IN mm
user_defined_annotation_label_size <- 2.5

# for annotation labels the plot require additional space. Fill in the dates:
user_defined_xlim_annotation_labels <- c(as.Date(c("2105-12-31", "2110-12-31"))) # in between which years shall annotation labels be displayed
user_defined_x_axis_expansion_for_lables <- as.Date(c("2018-12-31", "2110-12-31")) # adjust the plot x limits accordingly

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
user_defined_rotation_angle <- 45

# define the baseline color for graphics labels
user_defined_baseline_color <- "grey30"

# choose an accessible color spectrum to be used for the graphs (viridis, magma, plasma, inferno, cividis, mako, rocket, turbo)
user_defined_color_spectrum <- "viridis"

# choose how the population peak is indicated by a geom_vline in the graphs (blank, solid, dotted, dashed, dotdash, longdash, twodash)
user_defined_linetype <- "dashed"

# MS2: choose how the peak demand year is indicated by a geom_vline in the graphs (blank, solid, dotted, dashed, dotdash, longdash, twodash)
user_defined_linetype_peak_demand_year <- "dotted"

# for the sankey diagram define the maximum number of LUTs simulated in the correction step
user_defined_maximum_number_of_LUTs_in_correction_step <- 18

# => give study  and study area information:
# define the probing dates and population peak year (a simulation year is depicted logically by the forgone time via a years last day (12.31.))
years_for_plotting = list(
  'weak_conservation' = ymd(paste(c(2018, 2030, 2050, 2060, 2080, 2100), 12, 31, sep = '-')),
  'enforced_conservation' = ymd(paste(c(2018, 2030, 2050, 2060, 2080, 2100), 12, 31, sep = '-')),
  'no_conservation' = ymd(paste(c(2025, 2030, 2050, 2060, 2080, 2100), 12, 31, sep = '-')),
  'combined' = ymd(paste(c(2018, 2025, 2030, 2050, 2060, 2080, 2100), 12, 31, sep = '-')),
  'population_peak' = ymd(paste(2060, 12, 31, sep = '-'))
)

# MS1: define the peak demands year for each policy scenario run (see output CSVs)
peak_demands_year_scenarios <- tibble(
  scenario = c('weak_conservation', 'enforced_conservation', 'no_conservation'),
  peak_demands_year = ymd(paste(c(2100, 2100, 2100), 12, 31, sep = '-'))
)

# if you used an external time series for simulation, note the peak demands year (can be new after each run)
peak_demands_year <- list('peak_demands_year' = ymd(paste(2100, 12, 31, sep = '-')))

# define here the y axis title for unallocated demands that are not AGB demand, i.e. if demand [ha] or demand [Mg]
user_defined_unallocated_demands_y_axis_title <- 'demand [ha]'

# define here if LUT05 plantation depicts a forest type (timber plantations)
LUT05_depicts_a_forest_type <- FALSE

# if you simulated with local wood consumption / degradation / RAP-LUT25 set the variable to true
local_degradation_simulated <- TRUE

# MS2: if you simulated fragmentation set the variable to true
ms2_fragmentation_simulated <- FALSE

# MS2: if you simulated potential habitat corridors set the variable to true
ms2_potential_habitat_corridors_simulated <- FALSE

# define your used climate periods
climate_periods <- tibble(
  start_date = ymd(c('2018-12-31', '2021-01-01', '2041-01-01', '2061-01-01', '2081-01-01')),
  end_date = ymd(paste(c(2020, 2040, 2060, 2080, 2100), 12, 31, sep = '-')),
  description = c('climate reference period (<=2020)', 
                  'climate period 2021 - 2040', 
                  'climate period 2041 - 2060', 
                  'climate period 2061 - 2080', 
                  'climate period 2081 - 2100')
)

# define your used initial simulation year for weak and/or enforced conservation
initial_simulation_year <- 2018

# define until which length numbers will be written and not given in scientific notation:
options(scipen = 999999)

# give the total simulated landscape area and unit (graphs refer to percentages of total simulated landscape mainly)
landscape_area <- 1678488
landscape_area_unit <- "ha"

# give the applied baseline scenario information
baseline_scenario <- "SSP2-4.5"

# give the country
country <- "ECUADOR"

# give the region
region <- "Esmeraldas"

# define the prefix for outputs selected for publication, this variable must be set manually in the ggsave statements by you
publication_indicator <- "Publication"

# alternate according to user setting (SH) ---------------------------------------------------------------------------------------------------------------------------------------------

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

# MS2 append peak demands year for singular scenario
if (model_stage == 'MS2' & time_series_input == 'external') {
  years_for_plotting <- append(years_for_plotting, peak_demands_year)
}


# import data (DK + SH) ---------------------------------------------------------------------------------------------------------------------------------------------

# COPY FILES
if (model_stage == 'MS1') {
  scenarios <- tibble(
    scenario_name = factor(c('weak_conservation', 'enforced_conservation', 'no_conservation')),
    scenario_name_output = factor(c('weak conservation', 'enforced conservation', 'no conservation'), 
                                  levels = c('weak conservation', 'enforced conservation', 'no conservation'))
  ) %>%
    mutate(scenario_output_folder = file.path(
      '..',
      paste(main_model_folder), 
      paste(demand_configuration_outputs_folder),
      paste('outputs', scenario_name, sep = '_')
    ))
}

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
files_to_copy = scenarios %>%
  pmap(~ list.files(..3, pattern = '.csv', recursive = TRUE, full.names = TRUE)) %>%
  flatten()
# only include tidy data (i.e. not log files)
files_to_copy <- files_to_copy[str_detect(files_to_copy, 'tidy_data')]
targetdir <- input_folder
for (file_to_copy in files_to_copy) {
  file.copy(from=file_to_copy, to=targetdir, overwrite = TRUE)
}

# IMPORT DATA
# now get the inputs
import_folder <- input_folder


RAP_LUTs_lookup_table <- read_csv(file.path(import_folder, 'RAP_LUTs_lookup_table.csv'), col_names = c('LUT_code', 'LUT_name')) %>%
  unite('LUT_name', c('LUT_code', 'LUT_name'), sep = ' = ', remove = FALSE)

correction_step_transition_matrix_weak_conservation <- read_csv(file.path(import_folder, 'LPB_correction_step_transition_matrix_weak_conservation.csv'), col_names = TRUE)
if (model_stage == 'MS1') {
  correction_step_transition_matrix_enforced_conservation <- read_csv(file.path(import_folder, 'LPB_correction_step_transition_matrix_enforced_conservation.csv'), col_names = TRUE)
}


# get all file names of data sets (but not the ones that are universal)
if (model_stage == 'MS1') {
  input_data <- tibble(file_name = list.files(import_folder, pattern = '.csv')) %>%
    filter(
      !file_name %in% c(
        # note here the universal files:
        'RAP_LUTs_lookup_table.csv',
        'mplc_LUTs_lookup_table.csv',
        'LPB_correction_step_transition_matrix_weak_conservation.csv',
        'LPB_correction_step_transition_matrix_enforced_conservation.csv'
      )
    )
}

if (model_stage == 'MS2') {
  input_data <- tibble(file_name = list.files(import_folder, pattern = '.csv')) %>%
    filter(
      !file_name %in% c(
        # note here the universal files:
        'RAP_LUTs_lookup_table.csv',
        'mplc_LUTs_lookup_table.csv',
        'LPB_correction_step_transition_matrix_weak_conservation.csv'
      )
    )
}


## separate data set names and scenario names
input_data <- input_data %>%
  mutate(
    scenario_name_start = str_locate(file_name, paste(scenarios$scenario_name, collapse = '|')),
    data_set_name = str_sub(file_name, 1, scenario_name_start[,1] - 2),
    scenario = str_sub(file_name, scenario_name_start[,1], scenario_name_start[,2])
  ) %>%
  select(-scenario_name_start)

## load content of files 
input_data <- input_data %>%
  mutate(file_contents = map(file_name, ~read_csv(file.path(import_folder, .)))) %>%
  mutate(file_contents = map2(scenario, file_contents, ~ tibble(.y, scenario = .x))) %>% # add scenario name as column
  select(-file_name, -scenario)

# remove empty data sets
input_data <- input_data %>%
  rowwise() %>%
  mutate(dataset_rows = nrow(file_contents)) %>%
  filter(dataset_rows > 0)

# bind data sets 
input_data <- input_data %>%
  group_by(data_set_name) %>%
  nest() %>%
  mutate(file_contents = map(data, ~bind_rows(.$file_contents))) %>%
  select(-data) 

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
    file_contents = map(file_contents, ~left_join(., time_steps_years_lookup_table[[1]]))
  )

# add scenario output name
input_data <- input_data %>%
  mutate(file_contents = map_if(file_contents, ~'scenario' %in% colnames(.), ~left_join(., scenarios, by = join_by(scenario == scenario_name))))

# append peak demands year ####
if (time_series_input == 'external') {
  input_data <- input_data %>%
    mutate(
      file_contents = map_if(file_contents, ~'scenario' %in% colnames(.), ~left_join(., peak_demands_year_scenarios))
    )
}

# transform to pivot wider
input_data <- pivot_wider(input_data, names_from = data_set_name, values_from = file_contents)

### >>> show data ##############################################################
### Access files for input data from tibble (lists, starting at position 1)
RAP_LUTs_lookup_table
## 2 scenarios (worst-case does not require a correction step) 
input_data$LPB_correction_step[[1]]
input_data$LPB_correction_step_transition_matrix[[1]]
## 3 scenarios
input_data$LPB_deterministic_population[[1]] # can vary in worst-case due to time frame
input_data$LPB_deterministic_smallholder_share[[1]] # can vary in worst-case due to time frame
input_data$LPB_AGB_demand[[1]] # can vary in worst-case due to time frame
input_data$LPB_scenario_years[[1]] # can vary in worst-case due to time frame
input_data$LPB_area_demands[[1]] # LUT01 can vary over scenarios
input_data$LPB_anthropogenic_features[[1]] # LUT01 can vary over scenarios
input_data$LPB_land_use_mplc[[1]]
input_data$LPB_land_use_mplc_difficult_terrain[[1]]
input_data$LPB_land_use_mplc_restricted_areas_accumulated[[1]]
input_data$LPB_land_use_mplc_restricted_areas_new[[1]]
input_data$LPB_land_use_mplc_restricted_areas_new_on_former_forest_pixels[[1]]
input_data$LPB_land_use_mplc_restricted_areas_remaining_forest[[1]]
input_data$LPB_land_use_mplc_allocated_locally[[1]]
input_data$LPB_land_use_mplc_allocated_regionally[[1]]
input_data$LPB_land_use_mplc_unallocated[[1]]
input_data$LPB_possibly_hidden_deforestation[[1]]
input_data$LPB_forest_conversion[[1]]
input_data$LPB_landscape_modelling_probabilities[[1]]
input_data$LPB_land_use_in_restricted_areas[[1]]
input_data$LPB_forest_net_gross_disturbed_undisturbed[[1]]
input_data$LPB_forest_impacted_by_anthropogenic_features[[1]]
input_data$LPB_forest_remaining_without_anthropogenic_impact[[1]]

# make some corrections for machine operations
input_data$LPB_forest_degradation_regeneration[[1]] <- input_data$LPB_forest_degradation_regeneration[[1]] %>%
  mutate(pixels = as.numeric(pixels),
         percentage = as.numeric(percentage)) 

input_data$LPB_forest_types_AGB_Carbon[[1]] <- input_data$LPB_forest_types_AGB_Carbon[[1]] %>%
  mutate(AGB = as.numeric(AGB),
         Carbon = as.numeric(Carbon)) 


input_data$LPB_forest_100years_without_anthropogenic_impact[[1]]
input_data$LPB_forest_habitat[[1]]
input_data$LPB_yields[[1]]
input_data$RAP_land_use[[1]]
input_data$RAP_total[[1]]
input_data$RAP_minimum_mitigation[[1]]
input_data$RAP_potential_AGB_Carbon[[1]]
input_data$RAP_potential_total_AGB_Carbon[[1]]
input_data$RAP_targeted_net_forest[[1]]
input_data$LPB_probabilistic_mean_forest[[1]]
input_data$LPB_probabilistic_max_forest_conversion[[1]]
input_data$LPB_basic_mean_demand_and_mean_unallocated_demand[[1]]

### DELETE LATER ON - HOW TO GET ACCESS:
input_data$LPB_land_use_mplc[[1]] %>%
  pull(time_step)

# is the same as
pull(input_data$LPB_land_use_mplc[[1]], time_step)

temp <- input_data$LPB_forest_net_gross_disturbed_undisturbed[[1]] %>%
  filter(class %in% c('gross_disturbed_forest', 'net_disturbed_forest'))

# MS2:
input_data$LPB_fragmentation[[1]]
input_data$RAP_fragmentation[[1]]



# create plots (SH + DK)--------------------------------------------------------------------------------------------------------------------------------------------

### PREPARATIONS (SH) #################################################################################################################

# set plots margins to give space for rotated x labels, the x axis title and the caption 
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


# create subtitle prefix
subtitle_prefix <- paste(country, region, baseline_scenario)

# create the caption for landscape-share graphics
caption_landscape_share <-paste('100 % equals', landscape_area, landscape_area_unit)

# create the caption for pixel-value graphics
caption_pixel_value <- paste('1 pixel equals 1', landscape_area_unit)

# define once the function to be used for facet_wrap scenario comparison plots to display the correct probing dates per scenario
scenario_x_dates <- function(x) {
  # Daniel:
  if (min(x) < ymd(initial_simulation_year, truncated = 2L)) years_for_plotting['weak_conservation'][[1]] else years_for_plotting['no_conservation'][[1]] 
}

# create the climate periods background plot
climate_periods$description = factor(climate_periods$description, unique(climate_periods$description))

climate_periods_gglayers = list(
  geom_rect(data = climate_periods, aes(xmin = start_date, xmax = end_date, ymin = -Inf, ymax = Inf, fill = description), alpha = 0.2),
  scale_fill_brewer()
)
  
### 1) BAR DIAGRAMS #################################################################################################################
# LPB pressure aspect land use in difficult terrain scenario comparison (bar) ########
# => STATUS: work in progress
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use in difficult terrain scenario comparison (bar)"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use in difficult terrain (bar)"
}

legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

data_probing_dates <- input_data$LPB_land_use_mplc_difficult_terrain[[1]] %>%
  filter(year_date %in% years_for_plotting[[first(.$scenario)]]) 

pl <- ggplot(data_probing_dates, aes(x = year_date, y = pixels, fill = LUT_name))
pl <- pl + geom_bar(aes(fill = LUT_name), stat = "identity", position = position_dodge()) + scale_fill_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
if (model_stage == 'MS2' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['peak_demands_year']], linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}

# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 fill = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
pl
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# => STATUS: DONE
### LPB correction step scenario comparison ###################################
if (model_stage == 'MS1') {
  plot_title <- "LPB correction step scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB correction step"
}

legend_title <- "Land Use Types"
# create the three sections
df <- pivot_longer(input_data$LPB_correction_step[[1]], initial_pixels:simulated_pixels, names_to = c('section')) %>%
  mutate(section = case_when(section == 'simulated_pixels' ~ scenario,
                             section == 'initial_pixels' ~ 'initial'),
         section = fct_relevel(section, 'initial', 'weak conservation', 'enforced conservation')) %>%
  select(-scenario) %>%
  distinct()
# plot the data
ggplot(df, aes(x = section, y = value)) +
  geom_bar(aes(fill = LUT_name), stat = "identity", position = position_dodge()) +
  scale_fill_viridis_d(option = user_defined_color_spectrum) +
  theme_LPB_RAP +
  theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust),
        axis.ticks.x = element_blank()) +
  theme(panel.grid.major.x = element_blank(),
        panel.grid.minor.y = element_blank()) +
  facet_grid(~LUT_code) +
  labs(y = paste("Landscape area in", landscape_area_unit),
       x = NULL) +
  labs(title = plot_title,
       subtitle = subtitle_prefix,
       fill = legend_title)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### LPB landscape modelling probabilities ######################################
# => STATUS: DONE
plot_title <- "LPB landscape modelling probabilities" 
legend_title <- "Probability classes"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
input_data$LPB_landscape_modelling_probabilities[[1]] %>%
group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage))
    pl <- pl + geom_bar(aes(fill = class), stat = "identity", position = position_dodge())
    pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, ' ', first(.$scenario)),
                     fill = legend_title,
                     linetype = "Population Peak year",
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  }) 






# LPB forest 100 years without anthropogenic impact scenario comparison bar ########
input_data$LPB_forest_100years_without_anthropogenic_impact[[1]]

subset_data <- input_data$LPB_forest_100years_without_anthropogenic_impact[[1]] %>%
  filter(class %in% c('former_disturbed_forest_gross', 
                      'former_disturbed_forest_net',
                      'initial_undisturbed_forest_gross',
                      'initial_undisturbed_forest_net'))


# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest 100 years without anthropogenic impact scenario comparison (bar)"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest 100 years without anthropogenic impact (bar)"
}

legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_data, aes(x = year_date, y = percentage))
pl <- pl + geom_bar(aes(fill = class), stat = "identity", position = position_dodge())
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 fill = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### 2) LINE DIAGRAMS ################################################################################################################
### >>> BASELINE ###################################################################
# => STATUS: DONE
### LPB deterministic population and smallholder share development #############
plot_title <- "LPB deterministic population and smallholder share development"
legend_title <- "Population aspects"
x_axis_title <- "Year"
y_axis_title <- "Population"

temp = input_data$LPB_deterministic_population[[1]] %>%
  left_join(input_data$LPB_deterministic_smallholder_share[[1]]) %>%
  pivot_longer(cols = c(population, smallholder_share), names_to = 'key') %>%
  filter(scenario == 'weak_conservation')

temp_only_for_probing_dates <- temp %>%
  filter(year_date %in% years_for_plotting[['combined']])

pl <- ggplot(data = temp, aes(x = year_date, y = value, color = key)) 
pl <- pl + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl <- pl + geom_point(data = temp_only_for_probing_dates)
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                          linetype = "Population peak year"),
                      color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
        subtitle = subtitle_prefix,
        color = legend_title,
        linetype = "Population peak year",
        x = x_axis_title,
        y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']]) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


## LPB demands in area and woody biomass #######################################
# => STATUS: DONE
# additional built-up can theoretically vary across scenarios
plot_title <- "LPB demands in area and woody biomass"
legend_title <- "Anthropogenic demands"
x_axis_title <- "Year"
first_y_axis_title <- paste("Population area demand resp. smallholder area demand in", landscape_area_unit)
second_y_axis_title <- "Population demand in woody biomass (AGB) [Mg]"

temp_area_demands <- input_data$LPB_area_demands[[1]] %>%
  rename(anthro_demands = LUT_name) %>%
  mutate(demand_type = 'area_demand')
temp_area_demands

# temp_agb_demands <- input_data$LPB_AGB_demand[[1]] %>%
#   mutate(demand_type = 'agb_demand',
#          anthro_demands = 'AGB')

temp_agb_demands <- input_data$LPB_basic_mean_demand_and_mean_unallocated_demand[[1]] %>%
  select(., -c('mean_unallocated_demand')) %>%
  rename(demand = 'mean_demand') %>%
  filter(., demand_type=='AGB') %>%
  mutate(demand_type = 'agb_demand',
         anthro_demands = 'AGB')
temp_agb_demands

temp_all_demands <- temp_area_demands %>%
  bind_rows(temp_agb_demands) %>%
  mutate(across(demand_type, factor, levels=c('area_demand', 'agb_demand'))) 

temp_all_demands %>% 
  group_by(scenario) %>%
  do({
    pl <- ggplot(.) 
    pl <- pl + geom_line(aes(x = year_date, y = demand, color = anthro_demands)) 
    temp_only_for_probing_dates <- .%>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = temp_only_for_probing_dates,
                          aes(x = year_date,
                              y = demand,
                              color = anthro_demands))
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~ demand_type, scales = 'free', 
                          strip.position = 'left',
                          labeller = as_labeller(c(area_demand = first_y_axis_title, 
                                                   agb_demand = second_y_axis_title))) 
    pl <- pl + theme_LPB_RAP  
    pl <- pl + theme(strip.text = element_text(family = user_defined_font,
                                               color = user_defined_baseline_color,
                                               size = user_defined_fontsize - user_defined_fontsize_factor,
                                               face = user_defined_other_face))
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(strip.background = element_blank(), strip.placement = "outside")
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     color = legend_title,
                     fill = legend_title,
                     new_scale = legend_title,
                     x = x_axis_title,
                     y = NULL,
                     caption = caption_pixel_value)
    pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })



### LPB anthropogenic features #################################################
# => STATUS: DONE
plot_title <- "LPB anthropogenic features"
legend_title <- "Anthropogenic features"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)
input_data$LPB_anthropogenic_features[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(data = ., aes(x = year_date, y = pixels, color = type)) 
    pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE)
    subset_only_for_probing_dates <- . %>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = subset_only_for_probing_dates)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     x = x_axis_title,
                     y = y_axis_title)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })


### >>> LAND USE ###################################################################
### >> LPB: #######################################################################

# LPB land use types panels scenario comparison ##################################
if (model_stage == 'MS1') {
  plot_title <- "LPB land use types panels scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB land use types panels"
}

legend_title <- "Scenarios"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

input_data$LPB_land_use_mplc[[1]]

pl <- ggplot(input_data$LPB_land_use_mplc[[1]], aes(x = year_date, y = pixels, color = scenario))
pl <- pl + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~LUT_code, scales = 'free_x') 
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) # first(.$scenario) ~scenario scenario
pl
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB land use scenario comparison #############################################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB land use scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB land use"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

glimpse(input_data$LPB_land_use_mplc[[1]])
input_data$LPB_land_use_mplc[[1]]$scenario_name_output
levels(input_data$LPB_land_use_mplc[[1]]$scenario_name_output)

pl <- ggplot(input_data$LPB_land_use_mplc[[1]], aes(x = year_date, y = percentage, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x') 
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) # first(.$scenario) ~scenario scenario
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB land use mplc (probable) gridded ###############################################
# => STATUS: WORK IN PROGRESS
# one plot for each scenario


plot_title <- "LPB land use mplc (probable) gridded"
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

# define LUT_groups to be displayed in singular grids: LUT17 in active or indirect active???

LUT_group_lookup_table <- tibble(
  LUT_code = c("LUT01", "LUT02", "LUT03", "LUT04", "LUT05", "LUT17",
               "LUT14", "LUT15", "LUT16", "LUT18",
               "LUT06", "LUT07", "LUT08", "LUT09",
               "LUT10", "LUT11", "LUT12", "LUT13"
               ),              
  LUT_group = c("1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs",
                "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs",
                "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", 
                "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs"
                )
)

LUT_group_data = input_data$LPB_land_use_mplc[[1]] %>%
  left_join(LUT_group_lookup_table)

LUT_group_data %>% 
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage, color = LUT_name)) 
    pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE)
    pl <- pl + coord_cartesian(clip = 'off')
    pl <- pl + geom_text_repel(data = subset(., year_date == max(year_date)),
                               aes(label = paste0(" ", LUT_code)),
                               family = user_defined_font,
                               size = user_defined_annotation_label_size,
                               min.segment.length = 0,
                               segment.curvature = -0.1,
                               segment.square = TRUE,
                               segment.color = "lightgrey",
                               box.padding = 0.1,
                               point.padding = 0.6,
                               direction = "y",
                               force = 0.5,
                               hjust = -1,
                               nudge_x = 0.15,
                               nudge_y = 1,
                               na.rm = TRUE, 
                               show.legend = FALSE)
    subset_only_for_probing_dates <- . %>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = subset_only_for_probing_dates)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~LUT_group)
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
             height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })

### LPB land use mplc (probable) ###############################################
# => STATUS: DONE
# one plot for each scenario


plot_title <- "LPB land use mplc (probable)"
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
input_data$LPB_land_use_mplc[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage, color = LUT_name)) 
    pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE)
    pl <- pl + coord_cartesian(clip = 'off')
    pl <- pl + geom_text_repel(data = subset(., year_date == max(year_date)),
                               aes(label = paste0(" ", LUT_code)),
                               family = user_defined_font,
                               size = user_defined_annotation_label_size,
                               min.segment.length = 0,
                               segment.curvature = -0.1,
                               segment.square = TRUE,
                               segment.color = "lightgrey",
                               box.padding = 0.1,
                               point.padding = 0.6,
                               direction = "y",
                               force = 0.5,
                               hjust = -1,
                               nudge_x = 0.15,
                               nudge_y = 1,
                               na.rm = TRUE, 
                               show.legend = FALSE)
    
    subset_only_for_probing_dates <- . %>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = subset_only_for_probing_dates)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })
  
### LPB land use mplc (probable) stacked #######################################
# => STATUS: DONE
plot_title <- "LPB land use mplc (probable) stacked" 
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
input_data$LPB_land_use_mplc[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage))
    pl <- pl + geom_area(aes(fill = LUT_name), color = user_defined_baseline_color) + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              colour = "Population peak year"),
                          linetype = user_defined_linetype,)
    pl <- pl + scale_color_manual(name = element_blank(), values = c("Population peak year" = user_defined_baseline_color))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, ' ', first(.$scenario)),
                     fill = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
 })  


### >> RAP: ########################################################################
# RAP land use scenario comparison #############################################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "RAP land use scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "RAP land use"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(input_data$RAP_land_use[[1]], aes(x = year_date, y = percentage, color = LUT_name))
pl <- pl + guides(color = guide_legend(ncol=1))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### RAP land use (possible) gridded ###############################################
# => STATUS: DONE
# one plot for each scenario
plot_title <- "RAP land use (possible) gridded"
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

# define LUT_groups to be displayed in singular grids
if (local_degradation_simulated == FALSE) {
  LUT_group_lookup_table <- tibble(
    LUT_code = c("LUT01", "LUT02", "LUT03", "LUT04", "LUT05", "LUT17",
                 "LUT14", "LUT15", "LUT16", "LUT18",
                 "LUT06", "LUT07", "LUT08", "LUT09",
                 "LUT10", "LUT11", "LUT12", "LUT13",
                 "LUT21", "LUT22", "LUT23", "LUT24"
    ),              
    LUT_group = c("1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs",
                  "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs",
                  "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", 
                  "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs",
                  "5. RAP LUTs", "5. RAP LUTs", "5. RAP LUTs", "5. RAP LUTs"
    )
  )
}

# define LUT_groups to be displayed in singular grids
if (local_degradation_simulated == TRUE) {
  LUT_group_lookup_table <- tibble(
    LUT_code = c("LUT01", "LUT02", "LUT03", "LUT04", "LUT05", "LUT17",
                 "LUT14", "LUT15", "LUT16", "LUT18",
                 "LUT06", "LUT07", "LUT08", "LUT09",
                 "LUT10", "LUT11", "LUT12", "LUT13",
                 "LUT21", "LUT22", "LUT23", "LUT24", "LUT25"
    ),              
    LUT_group = c("1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs", "1. Primary active LUTs",
                  "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs", "2. Secondary active LUTs",
                  "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", "3. Succession LUTs", 
                  "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs", "4. Passive and static LUTs",
                  "5. RAP LUTs", "5. RAP LUTs", "5. RAP LUTs", "5. RAP LUTs", "5. RAP LUTs" 
    )
  )
}


LUT_group_data = input_data$RAP_land_use[[1]] %>%
  left_join(LUT_group_lookup_table)

LUT_group_data %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage, color = LUT_name)) 
    pl <- pl + guides(color = guide_legend(ncol=1))
    pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE)
    pl <- pl + coord_cartesian(clip = 'off')
    pl <- pl + geom_text_repel(data = subset(., year_date == max(year_date)),
                               aes(label = paste0(" ", LUT_code)),
                               family = user_defined_font,
                               size = user_defined_annotation_label_size,
                               min.segment.length = 0,
                               segment.curvature = -0.1,
                               segment.square = TRUE,
                               segment.color = "lightgrey",
                               box.padding = 0.1,
                               point.padding = 0.6,
                               direction = "y",
                               force = 0.5,
                               hjust = -1,
                               nudge_x = 0.15,
                               nudge_y = 1,
                               na.rm = TRUE, 
                               show.legend = FALSE)
    subset_only_for_probing_dates <- . %>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = subset_only_for_probing_dates)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~LUT_group)
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })

### RAP land use (possible) ###############################################
# => STATUS: DONE
# one plot for each scenario
plot_title <- "RAP land use (possible)"
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
input_data$RAP_land_use[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage, color = LUT_name)) 
    pl <- pl + guides(color = guide_legend(ncol=1))
    pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE)
    pl <- pl + coord_cartesian(clip = 'off')
    pl <- pl + geom_text_repel(data = subset(., year_date == max(year_date)),
                               aes(label = paste0(" ", LUT_code)),
                               family = user_defined_font,
                               size = user_defined_annotation_label_size,
                               min.segment.length = 0,
                               segment.curvature = -0.1,
                               segment.square = TRUE,
                               segment.color = "lightgrey",
                               box.padding = 0.1,
                               point.padding = 0.6,
                               direction = "y",
                               force = 0.5,
                               hjust = -1,
                               nudge_x = 0.15,
                               nudge_y = 1,
                               na.rm = TRUE, 
                               show.legend = FALSE)
    subset_only_for_probing_dates <- . %>%
      filter(year_date %in% years_for_plotting[[first(.$scenario)]])
    pl <- pl + geom_point(data = subset_only_for_probing_dates)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     color = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })


### RAP land use (possible) stacked #######################################
# => STATUS: DONE
plot_title <- "RAP land use (possible) stacked" 
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
input_data$RAP_land_use[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = percentage))
    pl <- pl + geom_area(aes(fill = LUT_name), color = user_defined_baseline_color) + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              colour = "Population peak year"),
                          linetype = user_defined_linetype,)
    pl <- pl + scale_color_manual(name = element_blank(), values = c("Population peak year" = user_defined_baseline_color))
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, ' ', first(.$scenario)),
                     fill = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })  




### >>> LPB PRESSURE ASPECTS: ######################################################
# all pressure aspects as scenario comparison with pixels

# LPB pressure aspect land use in difficult terrain scenario comparison ########
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use in difficult terrain scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use in difficult terrain"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_difficult_terrain[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB pressure aspect land use in restricted areas accumulated scenario comparison ####
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use in restricted areas accumulated scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use in restricted areas accumulated"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_restricted_areas_accumulated[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



# LPB pressure aspect land use in restricted areas new for time step scenario comparison ####
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use in restricted areas new for time step scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use in restricted areas new for time step"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_restricted_areas_new[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB pressure aspect land use in restricted areas new on former forest pixels scenario comparison ####
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use in restricted areas new on former forest pixels scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use in restricted areas new on former forest pixels"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_restricted_areas_new_on_former_forest_pixels[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



# LPB pressure aspect land use allocated locally to settlements scenario comparison ################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use allocated locally to settlements scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use allocated locally to settlements"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_allocated_locally[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# LPB pressure aspect land use allocated regionally to settlements scenario comparison #############
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use allocated regionally to settlements scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use allocated regionally to settlements"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_allocated_regionally[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB-mplc pressure aspect land use unallocated scenario comparison #################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB-mplc pressure aspect land use unallocated scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB-mplc pressure aspect land use unallocated"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_unallocated[[1]], aes(x = year_date, y = area, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB-basic pressure aspect land use unallocated (mean value) scenario comparison #################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB-basic pressure aspect land use unallocated (mean value) scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB-basic pressure aspect land use unallocated (mean value)"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste(user_defined_unallocated_demands_y_axis_title)

# select the data out of the file (eliminate mean_demand and AGB)
clean_data_unallocated_demands <- input_data$LPB_basic_mean_demand_and_mean_unallocated_demand[[1]] %>%
  select(., -c('mean_demand')) %>%
  filter(., demand_type !='AGB') %>%
  rename(., LUT_code = demand_type) %>%
  left_join(., RAP_LUTs_lookup_table)
clean_data_unallocated_demands

pl <- ggplot(clean_data_unallocated_demands, aes(x = year_date, y = mean_unallocated_demand, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# LPB-basic pressure aspect AGB demand unallocated (mean value) scenario comparison #################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB-basic pressure aspect AGB demand unallocated (mean value) scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB-basic pressure aspect AGB demand unallocated (mean value)"
}
legend_title <- "Aspect"
x_axis_title <- "Year"
y_axis_title <- paste('unallocated demand AGB [Mg]')

# select the data out of the file (eliminate mean_demand and all other LUTs)
clean_data_unallocated_demands <- input_data$LPB_basic_mean_demand_and_mean_unallocated_demand[[1]] %>%
  select(., -c('mean_demand')) %>%
  filter(., demand_type=='AGB')
clean_data_unallocated_demands

pl <- ggplot(clean_data_unallocated_demands, aes(x = year_date, y = mean_unallocated_demand, color = demand_type))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)




# LPB pressure aspect possibly hidden deforestation (probabilistic) scenario comparison #############
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect possibly hidden deforestation (probabilistic) scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect possibly hidden deforestation (probabilistic)"
}
legend_title <- "Probabilistic deforestation"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_possibly_hidden_deforestation[[1]], aes(x = year_date, y = pixels, color = 'deforested pixel'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB pressure aspect forest conversion scenario comparison ####################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect forest conversion scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect forest conversion"
}
legend_title <- "Converted forest"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

clean_data <- input_data$LPB_forest_conversion[[1]] 

pl <- ggplot(clean_data, aes(x = year_date, y = pixels, color = 'converted forest pixel'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
# pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + facet_grid(Aspect ~ scenario_name_output, scales = 'free')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB basic pressure aspect forest conversion by type scenario comparison ####################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect forest conversion (basic) by singular LUT scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect forest conversion (basic) by singular LUT"
}
legend_title <- "Converted forest"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

clean_data <- input_data$LPB_probabilistic_max_forest_conversion[[1]]
  
clean_data_without_NA <- clean_data %>%
  dplyr::mutate(LUT_name = replace_na(LUT_name, "total"))

pl <- ggplot(clean_data_without_NA, aes(x = year_date, y = pixels, color = 'converted forest pixel'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE, name="") 
# pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
#pl <- pl + facet_grid(~fct_rev(LUT_name)~scenario, scales = 'free', labeller = label_wrap_gen(width = 25))
pl <- pl + facet_grid(LUT_name ~ scenario_name_output, scales = 'free_x', labeller = label_wrap_gen(width = 25))
#pl <- pl + facet_grid(LUT_code ~ scenario, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + theme(strip.text.y = element_text(angle = 360, hjust = 0, vjust = 1))
pl <- pl + theme(legend.position="bottom")
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB mplc pressure aspect forest conversion by type scenario comparison ####################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect forest conversion (mplc) by singular LUT scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect forest conversion (mplc) by singular LUT"
}
legend_title <- "Converted forest"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

clean_data <- input_data$LPB_forest_conversion_by_type[[1]] 

pl <- ggplot(clean_data, aes(x = year_date, y = pixels, color = 'converted forest pixel'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE, name="") 
# pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
#pl <- pl + facet_grid(LUT_code ~ scenario, scales = 'free_x')
pl <- pl + facet_grid(LUT_name ~ scenario_name_output, scales = 'free_x', labeller = label_wrap_gen(width = 25))
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + theme(strip.text.y = element_text(angle = 360, hjust = 0, vjust = 1))
pl <- pl + theme(legend.position="bottom")
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB pressure aspect deforestation scenario comparison ####################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect deforestation scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect deforestation"
}
legend_title <- "Deforested area"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

clean_data <- input_data$LPB_forest_deforestation[[1]] 

pl <- ggplot(clean_data, aes(x = year_date, y = pixels, color = 'deforested pixel'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
# pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + facet_grid(Aspect ~ scenario_name_output, scales = 'free')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### LPB pressure aspect remaining forest in restricted areas quality aspect ####
input_data$LPB_land_use_mplc_restricted_areas_remaining_forest[[1]]

if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect quality of remaining forest in restricted areas scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect quality of remaining forest in restricted areas"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_mplc_restricted_areas_remaining_forest[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### >>> LAND USE IN RESTRICTED AREAS: ##########################################

# LPB land use in restricted areas scenario comparison #########################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB land use in restricted areas scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB land use in restricted areas"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$LPB_land_use_in_restricted_areas[[1]], aes(x = year_date, y = pixels, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### >>> FOREST ASPECTS: ########################################################
# all plots as percentage (landscape share)

### LPB forest net gross disturbed undisturbed scenario comparison #############
input_data$LPB_forest_net_gross_disturbed_undisturbed[[1]]
subset_data <- input_data$LPB_forest_net_gross_disturbed_undisturbed[[1]] %>%
  filter(class %in% c('gross_forest_all_forest_types', 
                      'net_forest_total_disturbed_undisturbed',
                      'gross_disturbed_forest',
                      'net_disturbed_forest'))
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest net gross disturbed undisturbed scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest net gross disturbed undisturbed"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_data, aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### LPB forest impacted by anthropogenic features ##############################
input_data$LPB_forest_impacted_by_anthropogenic_features[[1]]
subset_data <- input_data$LPB_forest_impacted_by_anthropogenic_features[[1]] %>%
  filter(class %in% c('impacted_gross_forest_disturbed_undisturbed', 
                      'impacted_net_forest_disturbed_undisturbed'))
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest net gross disturbed undisturbed impacted by anthropogenic features scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest net gross disturbed undisturbed impacted by anthropogenic features"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_data, aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### LPB forest remaining without anthropogenic impact: ##########################
input_data$LPB_forest_remaining_without_anthropogenic_impact[[1]]
subset_data <- input_data$LPB_forest_remaining_without_anthropogenic_impact[[1]] %>%
  filter(class %in% c('gross_undisturbed_forest', 
                      'gross_disturbed_forest',
                      'net_undisturbed_forest',
                      'net_disturbed_forest'))
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest net gross remaining without antropogenic impact scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest net gross remaining without antropogenic impact"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_data, aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB forest degradation regeneration net gross: ##############################
input_data$LPB_forest_degradation_regeneration[[1]]
### LPB forest gross degradation regeneration scenario comparison ######
subset_data <- input_data$LPB_forest_degradation_regeneration[[1]] %>%
  filter(class %in% c('degradation_low_gross_forest', 
                      'degradation_moderate_gross_forest',
                      'degradation_severe_gross_forest',
                      'degradation_absolute_gross_forest',
                      'regeneration_low_gross_forest',
                      'regeneration_medium_gross_forest',
                      'regeneration_high_gross_forest',
                      'regeneration_full_gross_forest'))

# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest gross degradation regeneration scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest gross degradation regeneration"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"
climate_title <- "Climate periods"

pl <- ggplot(data = subset_data)
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = subset_data, aes(x = year_date, y = percentage, color = class)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB forest net degradation regeneration scenario comparison ######
subset_data <- input_data$LPB_forest_degradation_regeneration[[1]] %>%
  filter(class %in% c('degradation_low_net_forest', 
                      'degradation_moderate_net_forest',
                      'degradation_severe_net_forest',
                      'degradation_absolute_net_forest',
                      'regeneration_low_net_forest',
                      'regeneration_medium_net_forest',
                      'regeneration_high_net_forest',
                      'regeneration_full_net_forest'))

# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest net degradation regeneration scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest net degradation regeneration"
}
legend_title <- "Aspects"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(data = subset_data)
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = subset_data, aes(x = year_date, y = percentage, color = class)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB forest net regeneration full disturbed undisturbed scenario comparison ######
subset_data <- input_data$LPB_forest_degradation_regeneration[[1]] %>%
  filter(class %in% c('regeneration_full_disturbed_net_forest',
                      'regeneration_full_undisturbed_net_forest'))

# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest net regeneration full disturbed undisturbed scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest net regeneration full disturbed undisturbed"
}
legend_title <- "Aspects"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(data = subset_data)
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = subset_data, aes(x = year_date, y = percentage, color = class)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



### LPB forest types AGB scenario comparison ##################################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest types AGB scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest types AGB"
}
legend_title <- "Aspects"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "AGB [Mg]"

AGB_group_lookup_table <- tibble (
  type = c("potential_maximum_undisturbed_AGB",
               "initial_AGB_gross_forest_simulation_start",
               "final_total_AGB_gross_forest",
               "final_total_AGB_gross_disturbed_forest",
               "final_total_AGB_gross_undisturbed_forest",
               "final_total_AGB_net_forest",
               "final_total_AGB_net_disturbed_forest",
               "final_total_AGB_net_undisturbed_forest",
               "final_total_AGB_gross_minus_net_forest",
               "final_total_AGB_gross_minus_net_disturbed_forest",
               "final_total_AGB_gross_minus_net_undisturbed_forest",
               "final_total_AGB_agroforestry",
               "final_total_AGB_plantation"),
  group = c("basis","basis",
            "forest_gross", "forest_gross", "forest_gross",
            "forest_net", "forest_net", "forest_net",
            "gross_minus_net", "gross_minus_net","gross_minus_net",
            "agroforestry",
            "plantation")
)

input_data$LPB_forest_types_AGB_Carbon[[1]]

sorted_data <- input_data$LPB_forest_types_AGB_Carbon[[1]] %>%
  left_join(AGB_group_lookup_table) %>%
  mutate(type = fct_relevel(type, c("potential_maximum_undisturbed_AGB",
                                                 "initial_AGB_gross_forest_simulation_start",
                                                 "final_total_AGB_gross_forest",
                                                 "final_total_AGB_gross_disturbed_forest",
                                                 "final_total_AGB_gross_undisturbed_forest",
                                                 "final_total_AGB_net_forest",
                                                 "final_total_AGB_net_disturbed_forest",
                                                 "final_total_AGB_net_undisturbed_forest",
                                                 "final_total_AGB_gross_minus_net_forest",
                                                 "final_total_AGB_gross_minus_net_disturbed_forest",
                                                 "final_total_AGB_gross_minus_net_undisturbed_forest",
                                                 "final_total_AGB_agroforestry",
                                                 "final_total_AGB_plantation"))) %>%
  drop_na

sorted_data

pl <- ggplot(data = sorted_data)
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = sorted_data, aes(x = year_date, y = AGB, color = type)) #, linetype = type #, linetype = group
pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum, direction = -1) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 linetype = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
pl <- pl + guides(colour = guide_legend(order = 2),
                  linetype = guide_legend(order = 2),
                  fill = guide_legend(order = 1))
pl
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### LPB forest types Carbon scenario comparison ###################################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest types Carbon scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest types Carbon"
}
legend_title <- "Aspects"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "Carbon [Mg]"

pl <- ggplot(data = input_data$LPB_forest_types_AGB_Carbon[[1]])
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = input_data$LPB_forest_types_AGB_Carbon[[1]], aes(x = year_date, y = Carbon, color = type)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# LPB forest 100 years without anthropogenic impact scenario comparison line ########
input_data$LPB_forest_100years_without_anthropogenic_impact[[1]]

subset_data <- input_data$LPB_forest_100years_without_anthropogenic_impact[[1]] %>%
  filter(class %in% c('former_disturbed_forest_gross', 
                      'former_disturbed_forest_net',
                      'initial_undisturbed_forest_gross',
                      'initial_undisturbed_forest_net'))


# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest 100 years without anthropogenic impact scenario comparison (line)"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest 100 years without anthropogenic impact (line)"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_data, aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



# LPB forest habitat scenario comparison #######################################
# => STATUS: DONE
if (model_stage == 'MS1') {
  plot_title <- "LPB forest habitat scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB forest habitat"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(input_data$LPB_forest_habitat[[1]], aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### >>> LPB YIELDS: ############################################################
# LPB potential regional top crop yields [Mg] ##################################
# => STATUS: DONE
plot_title <- "LPB potential regional top crop yields [Mg]" 
legend_title <- "LaForeT national top crops"
x_axis_title <- "Year"
y_axis_title <- "Potential regional total yield [Mg]"
#### todo: check this graph
input_data$LPB_yields[[1]] %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = yield_maximum, color = crop))
    pl <- pl + geom_ribbon(aes(ymin = yield_minimum, 
                               ymax = yield_maximum, 
                               fill = crop),
                           alpha = 0.5) 
    pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_line(aes(x = year_date, 
                             y = yield_mean, 
                             fill = crop)) 
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype)) 
    pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum)
    if (model_stage == 'MS1' & time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~ crop, scales = 'free') 
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, ' ', first(.$scenario)),
                     color = legend_title,
                     fill = legend_title,
                     x = x_axis_title,
                     y = y_axis_title)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]])
    ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })  


### >>> RAP FURTHER ASPECTS: ###################################################

### RAP total (LUTs 21 to 24) ##################################################
input_data$RAP_total[[1]]
# => STATUS: DONE
plot_title <- "RAP total of LUTs 21 to 24 (formerly converted areas)"
legend_title <- "RAP allocated per time step"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(input_data$RAP_total[[1]], aes(x = year_date, y = percentage, color = 'RAP total'))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
# save in RAP List
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



### RAP minimum mitigation #####################################################
input_data$RAP_minimum_mitigation[[1]]
# => STATUS: DONE
plot_title <- "RAP minimum mitigation"
legend_title <- "RAP allocated per time step"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

pl <- ggplot(input_data$RAP_minimum_mitigation[[1]], aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
# save in RAP list
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### RAP potential AGB ##########################################################
input_data$RAP_potential_AGB_Carbon[[1]]
# => STATUS: DONE
plot_title <- "RAP potential AGB"
legend_title <- "RAP Land Use Types"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "AGB [Mg]"

pl <- ggplot(data = input_data$RAP_potential_AGB_Carbon[[1]])
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = input_data$RAP_potential_AGB_Carbon[[1]], aes(x = year_date, y = potential_AGB, color = LUT_name)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### RAP potential Carbon #######################################################
input_data$RAP_potential_AGB_Carbon[[1]]
# => STATUS: DONE
plot_title <- "RAP potential Carbon"
legend_title <- "RAP Land Use Types"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "Carbon [Mg]"

pl <- ggplot(data = input_data$RAP_potential_AGB_Carbon[[1]])
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = input_data$RAP_potential_AGB_Carbon[[1]], aes(x = year_date, y = potential_Carbon, color = LUT_name)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### RAP total AGB Carbon #######################################################
input_data$RAP_potential_total_AGB_Carbon[[1]]

temp = input_data$RAP_potential_total_AGB_Carbon[[1]] %>%
  pivot_longer(cols = c(potential_AGB, potential_Carbon), names_to = 'category') %>%
  mutate(across(category, factor, levels=c('potential_AGB', 'potential_Carbon'))) 

# => STATUS: DONE
plot_title <- "RAP potential total AGB and Carbon [Mg]"
legend_title <- "Category"
climate_title <- "Climate periods"
x_axis_title <- "Year"
y_axis_title <- "Mg"

pl <- ggplot(data = temp)
pl <- pl + climate_periods_gglayers
pl <- pl + geom_line(data = temp, aes(x = year_date, y = value, color = category)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 fill = climate_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### RAP targeted net forest ####################################################
input_data$RAP_targeted_net_forest[[1]]
# => STATUS: DONE
plot_title <- "RAP targeted net forest and possible net forest including reforestation"
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(input_data$RAP_targeted_net_forest[[1]], aes(x = year_date, y = percentage, color = category))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
# save in RAP list
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### >>> MPLC AND RAP JUXTAPOSITION PER SCENARIO ###########################
# define info
info <- "mplc RAP juxtaposition no FLR vs. potential FLR"
# agb carbon

### mplc RAP juxtaposition probable and possible forested area #################
# => STATUS: DONE
# plot_title <- paste(info, "forested area" )
# legend_title <- "Land Use Types"
# x_axis_title <- "Year"
# y_axis_title <- "Percentage of simulated landscape"
# 
# # use two groups: mplc = LUT  4, 5, 8, 9, + RAP = LUT  4, 5, 8, 9, 21, 22, 23, 25
# temp_selected_data <- input_data$RAP_land_use[[1]] %>%
#   filter(LUT_code %in% c("LUT04", "LUT05", "LUT08", "LUT09", "LUT21", "LUT22", "LUT23", "LUT25"))
# 
# ## TODO CHECK ERROR - Diagram not significant #############################
# mplc_forest_lookup_table <- tibble (
#   LUT_code = c("LUT04", "LUT05, LUT08", "LUT09"),
#   group_mplc = c("mplc", "mplc", "mplc", "mplc")
# )
# 
# RAP_forest_lookup_table <- tibble (
#   LUT_code = c("LUT04", "LUT05", "LUT08", "LUT09",
#                "LUT21", "LUT22", "LUT23", "LUT25"),
#   group_RAP = c("RAP", "RAP", "RAP", "RAP", 
#                 "RAP", "RAP", "RAP", "RAP")
# )
# 
# temp = temp_selected_data %>%
#   left_join(mplc_forest_lookup_table) %>% 
#   left_join(RAP_forest_lookup_table) %>%
#   pivot_longer(cols = c(group_mplc, group_RAP), names_to = 'group') 
# 
# temp_clean <- na.omit(temp)
# 
# temp_clean
# 
# temp_clean %>%
#   group_by(scenario) %>%
#   do({
#     pl <- ggplot(., aes(x = year_date, y = percentage, fill = LUT_name)) 
#     pl <- pl + geom_area(position = position_stack(reverse = TRUE))
#     pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
#     pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
#                               linetype = "Population peak year"),
#                           color = user_defined_baseline_color,)
#     pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
#     if (model_stage == 'MS2') {
#       pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['peak_demands_year']], linetype = "Peak demands year"), color = user_defined_baseline_color)
#       pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
#     }
#     pl <- pl + facet_wrap(~value)
#     pl <- pl + theme_LPB_RAP
#     pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
#     pl <- pl + theme(panel.grid.minor.y = element_blank(),
#                      panel.grid.minor.x = element_blank())
#     pl <- pl + labs (title = plot_title,
#                      subtitle = paste(subtitle_prefix, first(.$scenario)),
#                      fill = legend_title,
#                      x = x_axis_title,
#                      y = y_axis_title,
#                      caption = caption_landscape_share)
#     pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
#     ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
#            height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
#     invisible(.)
#   })

### mplc RAP juxtaposition probable and possible AGB ###########################
# => STATUS: DONE
plot_title <- paste(info, "potential AGB" )
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "AGB [Mg]"

# use two groups AGB of : mplc = LUT  4, 5, 8, 9, + RAP = LUT  4, 5, 8, 9, 21, 22, 23
temp_selected_mplc_data <- input_data$LPB_forest_types_AGB_Carbon[[1]] %>%
  filter(type %in% c("final_total_AGB_agroforestry",
                     "final_total_AGB_plantation",
                     "final_total_AGB_gross_disturbed_forest",
                     "final_total_AGB_gross_undisturbed_forest"))

temp_renamed_selcted_mplc_data <- temp_selected_mplc_data %>%
  select(time_step, type, AGB, scenario, year_date) %>%
  rename(LUT_code = type) %>%
  mutate(LUT_code = case_when(LUT_code == "final_total_AGB_agroforestry" ~ "LUT04",
                              LUT_code == "final_total_AGB_plantation" ~ "LUT05",
                              LUT_code == "final_total_AGB_gross_disturbed_forest" ~ "LUT08",
                              LUT_code == "final_total_AGB_gross_undisturbed_forest" ~ "LUT09"),
         group = 'mplc')


temp_RAP <- input_data$RAP_potential_AGB_Carbon[[1]] %>%
  select(time_step, LUT_code, potential_AGB, scenario, year_date) %>%
  rename(AGB = potential_AGB) %>%
  mutate(group = 'RAP')

temp_mplc_to_RAP <- temp_renamed_selcted_mplc_data %>%
  mutate(group = 'RAP')
  
temp = temp_renamed_selcted_mplc_data %>%
  bind_rows(temp_RAP, temp_mplc_to_RAP) %>%
  left_join(RAP_LUTs_lookup_table) %>%
  na.omit()


temp %>%
  group_by(scenario) %>%
  do({
    # pl <- ggplot(., aes(x = year_date, y = factor(LUT_code), height = AGB, fill = LUT_name)) 
    pl <- ggplot(., aes(x = year_date, y = AGB, fill = LUT_name))
    # pl <- pl + geom_ridgeline(scale = 0.00000001, size = 0.1, color = user_defined_baseline_color)
    pl <- pl + geom_area(position = position_stack(reverse = TRUE))
    pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year[[1]], linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~group)
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     fill = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })

### mplc RAP juxtaposition probable and possible Carbon ########################
# => STATUS: DONE
plot_title <- paste(info, "potential Carbon" )
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Carbon [Mg]"

input_data$LPB_forest_types_AGB_Carbon[[1]]

# use two groups AGB of : mplc = LUT  4, 5, 8, 9, + RAP = LUT  4, 5, 8, 9, 21, 22, 23
temp_selected_mplc_data <- input_data$LPB_forest_types_AGB_Carbon[[1]] %>%
  filter(type %in% c("final_total_AGB_agroforestry",
                     "final_total_AGB_plantation",
                     "final_total_AGB_gross_disturbed_forest",
                     "final_total_AGB_gross_undisturbed_forest"))

temp_renamed_selcted_mplc_data <- temp_selected_mplc_data %>%
  select(time_step, type, Carbon, scenario, year_date) %>%
  rename(LUT_code = type) %>%
  mutate(LUT_code = case_when(LUT_code == "final_total_AGB_agroforestry" ~ "LUT04",
                              LUT_code == "final_total_AGB_plantation" ~ "LUT05",
                              LUT_code == "final_total_AGB_gross_disturbed_forest" ~ "LUT08",
                              LUT_code == "final_total_AGB_gross_undisturbed_forest" ~ "LUT09"),
         group = 'mplc')

input_data$RAP_potential_AGB_Carbon[[1]]

temp_RAP <- input_data$RAP_potential_AGB_Carbon[[1]] %>%
  select(time_step, LUT_code, potential_Carbon, scenario, year_date) %>%
  rename(Carbon = potential_Carbon) %>%
  mutate(group = 'RAP')

temp_mplc_to_RAP <- temp_renamed_selcted_mplc_data %>%
  mutate(group = 'RAP')

temp = temp_renamed_selcted_mplc_data %>%
  bind_rows(temp_RAP, temp_mplc_to_RAP) %>%
  left_join(RAP_LUTs_lookup_table) %>%
  na.omit()

temp %>%
  group_by(scenario) %>%
  do({
    pl <- ggplot(., aes(x = year_date, y = Carbon, fill = LUT_name)) 
    pl <- pl + geom_area(position = position_stack(reverse = TRUE))
    pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
    pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                              linetype = "Population peak year"),
                          color = user_defined_baseline_color,)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
    if (time_series_input == 'external') {
      pl <- pl + geom_vline(aes(xintercept = peak_demands_year[[1]], linetype = "Peak demands year"), color = user_defined_baseline_color)
      pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
    }
    pl <- pl + facet_wrap(~group)
    pl <- pl + theme_LPB_RAP
    pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
    pl <- pl + theme(panel.grid.minor.y = element_blank(),
                     panel.grid.minor.x = element_blank())
    pl <- pl + labs (title = plot_title,
                     subtitle = paste(subtitle_prefix, first(.$scenario)),
                     fill = legend_title,
                     x = x_axis_title,
                     y = y_axis_title,
                     caption = caption_landscape_share)
    pl <- pl + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[[first(.$scenario)]], limits = user_defined_x_axis_expansion_for_lables)
    ggsave(file.path(output_folder, paste(plot_title, ' ',subtitle_prefix, ' ', first(.$scenario), output_format, sep = '')), 
           height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
    invisible(.)
  })


### >>> COMBINED FACETED PLOTS FOR PUBLICATION ############################

### Access files for input data from tibble (lists, starting at position 1)
input_data$LPB_land_use_mplc_difficult_terrain[[1]]
input_data$LPB_land_use_mplc_restricted_areas_accumulated[[1]]
input_data$LPB_land_use_mplc_restricted_areas_new[[1]]
input_data$LPB_land_use_mplc_restricted_areas_new_on_former_forest_pixels[[1]]
input_data$LPB_land_use_mplc_allocated_locally[[1]]
input_data$LPB_land_use_mplc_allocated_regionally[[1]]
input_data$LPB_land_use_mplc_unallocated[[1]]
input_data$LPB_possibly_hidden_deforestation[[1]]
input_data$LPB_land_use_in_restricted_areas[[1]]
input_data$LPB_forest_net_gross_disturbed_undisturbed[[1]]
input_data$LPB_forest_impacted_by_anthropogenic_features[[1]]
input_data$LPB_forest_remaining_without_anthropogenic_impact[[1]]
input_data$LPB_forest_degradation_regeneration[[1]]
input_data$LPB_forest_types_AGB_Carbon[[1]]
input_data$LPB_forest_100years_without_anthropogenic_impact[[1]]
input_data$LPB_forest_habitat[[1]]
input_data$LPB_yields[[1]]
input_data$RAP_total[[1]]
input_data$RAP_minimum_mitigation[[1]]
input_data$RAP_potential_AGB_Carbon[[1]]
input_data$RAP_potential_total_AGB_Carbon[[1]]
input_data$RAP_targeted_net_forest[[1]]

# LPB basic mean forest and mplc forest in corrective allocation scenario comparison ####################
# => STATUS: WIP
if (model_stage == 'MS1') {
  plot_title <- "LPB basic mean forest and mplc forest in corrective allocation scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB basic mean forest and mplc forest in corrective allocation"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

clean_data <- input_data$LPB_forest_corrective_allocation[[1]] %>%
  full_join(input_data$LPB_probabilistic_mean_forest[[1]]) %>%
  mutate(Aspect = fct_relevel(Aspect, c('mean of probabilistically simulated forest',
                                        'prior corrective allocation',
                                        'post corrective allocation')))

pl <- ggplot(clean_data, aes(x = year_date, y = pixels, color = Aspect))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# PLOT COMBINATIONS:
# Population and demands #####################################

super_plot_title <- "Population and demands" 
x_axis_title <- "Year"

# PLOT 1 population and smallholder
y_axis_title <- "Population and\nsmallholder share"

temp = input_data$LPB_deterministic_population[[1]] %>%
  left_join(input_data$LPB_deterministic_smallholder_share[[1]]) %>%
  pivot_longer(cols = c(population, smallholder_share), names_to = 'key') %>%
  filter(scenario == 'weak_conservation')

temp

pl1 <- ggplot(data = temp, aes(x = year_date, y = value, color = key)) 
pl1 <- pl1 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl1 <- pl1 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], color = "Population peak year"),
                        linetype = user_defined_linetype,
                        color = user_defined_baseline_color)
pl1 <- pl1 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype), guide = "none")
if (time_series_input == 'external') {
  pl1 <- pl1 + new_scale('linetype')
  pl1 <- pl1 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl1 <- pl1 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype), guide = "none")
}
pl1 <- pl1 + theme_LPB_RAP
pl1 <- pl1 + theme(legend.position = "bottom", legend.direction="vertical", legend.box="vertical", legend.margin=margin(), legend.text.align = 0, legend.justification = c(0,0.5))
pl1 <- pl1 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl1 <- pl1 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl1 <- pl1 + labs (color = "Aspect:",
                   x = x_axis_title,
                   y = y_axis_title)
pl1 <- pl1 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])

# PLOT 2 area demands deterministic
y_axis_title <- paste("Deterministic area\ndemands in", landscape_area_unit)

subset_area_demands_deterministic <- input_data$LPB_area_demands[[1]] %>%
  filter(scenario %in% c('weak_conservation')) %>%
  filter(LUT_code %in% c('LUT02', 'LUT03', 'LUT04', 'LUT05'))

pl2 <- ggplot(data = subset_area_demands_deterministic, aes(x = year_date, y = demand, color = LUT_name)) 
pl2 <- pl2 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl2 <- pl2 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']]),
                        linetype = user_defined_linetype,
                        color = user_defined_baseline_color)
pl2 <- pl2 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype), guide = "none")
if (time_series_input == 'external') {
  pl2 <- pl2 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl2 <- pl2 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype), guide = "none")
}
pl2 <- pl2 + theme_LPB_RAP
pl2 <- pl2 + theme(legend.position = "bottom", legend.direction="vertical", legend.box="vertical", legend.margin=margin(), legend.text.align = 0, legend.justification = c(0,0.5))
pl2 <- pl2 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl2 <- pl2 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl2 <- pl2 + labs (color = "LUT:",
                   x = x_axis_title,
                   y = y_axis_title)
pl2 <- pl2 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])
pl2 <- pl2 + guides(color = guide_legend(nrow=2, byrow=TRUE))



# PLOT 3 area demands additional built-up scenario
y_axis_title <- paste("Demand in additional\nbuilt-up area in", landscape_area_unit)

subset_area_demands_scenarios <- input_data$LPB_area_demands[[1]] %>%
  filter(LUT_code %in% c('LUT01'))

pl3 <- ggplot(data = subset_area_demands_scenarios, aes(x = year_date, y = demand, color = scenario)) 
pl3 <- pl3 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl3 <- pl3 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']]),
                        linetype = user_defined_linetype,
                        color = user_defined_baseline_color)
pl3 <- pl3 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype), guide = "none")
if (time_series_input == 'external') {
  pl3 <- pl3 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl3 <- pl3 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype), guide = "none")
}
pl3 <- pl3 + theme_LPB_RAP
pl3 <- pl3 + theme(legend.position = "bottom", legend.direction="vertical", legend.box="vertical", legend.margin=margin(), legend.text.align = 0, legend.justification = c(0,0.5))
pl3 <- pl3 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl3 <- pl3 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl3 <- pl3 + labs (color = "Scenario:",
                   x = x_axis_title,
                   y = y_axis_title)
pl3 <- pl3 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])


# PLOT 4 woody biomass AGB demand
y_axis_title <- "Demand in woody biomass\n(AGB) [Mg]"
subset_AGB <- input_data$LPB_basic_mean_demand_and_mean_unallocated_demand[[1]] %>%
  select(., -c('mean_unallocated_demand')) %>%
  filter(., demand_type=='AGB') %>%
  filter(scenario %in% c('weak_conservation'))

pl4 <- ggplot(data = subset_AGB, aes(x = year_date, y = mean_demand, color='AGB demand total population')) 
pl4 <- pl4 + geom_line()
pl4 <- pl4 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                            linetype = "Population peak year"),
                        color = user_defined_baseline_color)
pl4 <- pl4 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype), guide = "none")
if (time_series_input == 'external') {
  pl4 <- pl4 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl4 <- pl4 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype), guide = "none")
}
pl4 <- pl4 + theme_LPB_RAP
pl4 <- pl4 + theme(legend.position = "bottom", legend.direction="vertical", legend.box="vertical", legend.margin=margin(), legend.text.align = 0, legend.justification = c(0,0.5))  
pl4 <- pl4 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl4 <- pl4 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl4 <- pl4 + labs (color = "AGB demand:",
                   x = x_axis_title,
                   y = y_axis_title)
pl4 <- pl4 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])

# PLOT JOINED
# create legend for peaks
temp_df_peaks <- tibble(
  peak_name = factor(c('Population peak', 'Demand peak'), levels = c('Population peak', 'Demand peak')),
  dates = c(years_for_plotting[['population_peak']], peak_demands_year),
  linetypes = c(user_defined_linetype, user_defined_linetype_peak_demand_year)
)
pl_peaks <- ggplot() 
pl_peaks <- pl_peaks + geom_vline(data = temp_df_peaks, aes(xintercept = dates, linetype = peak_name))
pl_peaks <- pl_peaks + scale_linetype_manual(name = element_blank(), values = temp_df_peaks$linetypes)
pl_peaks <- pl_peaks + theme(legend.position = "bottom", legend.direction="horizontal", legend.justification='left') 
pl_peaks
peak_legends <- get_legend(pl_peaks)


# create title
title <- ggdraw() + 
  draw_label("Population and demands",
             fontfamily = user_defined_font, size = user_defined_fontsize, fontface = 'bold', color = user_defined_baseline_color,
             x = 0, hjust = 0) 
# plot
pl_joined <-
  plot_grid(
    title,
    NULL,
    peak_legends,
    NULL,
    pl1,
    pl2,
    pl3,
    pl4,
    nrow = 4,
    ncol = 2,
    align = 'hv',
    axis = 't',
    labels = c('', '', '', '', 'A', 'B', 'C', 'D'),
    scale = 0.95,
    rel_heights = c(0.25, 0.25, 3, 3),
    rel_widths = c(1.5, 1.5)
  ) + theme(plot.background = element_rect(fill = "white", colour = NA))

# save cowplot
save_plot(file.path(output_folder, paste(super_plot_title, ' ', subtitle_prefix, ' ', output_format, sep = '')),
          plot = pl_joined, 
          base_height = 1.2 * output_height, base_width = output_width, dpi = output_dpi, units = output_unit)


# Anthropogenic features #####################################
input_data$LPB_anthropogenic_features[[1]]

plot_title <- "Anthropogenic features"
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area\nbuilt-up in", landscape_area_unit)

# plot deterministic features
subset_deterministic <- input_data$LPB_anthropogenic_features[[1]] %>%
  filter(scenario %in% c('weak_conservation')) %>%
  filter(type %in% c('cities', 'settlements', 'streets'))

subset_deterministic

# plot the three scenario curves for additional built up 
subset_scenario <- input_data$LPB_anthropogenic_features[[1]] %>%
  filter(type %in% c('additional_built-up'))

# PLOT 1
pl1 <- ggplot(subset_deterministic, aes(x = year_date, y = pixels, color = type))
pl1 <- pl1 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
# pl1 <- pl1 + facet_wrap(~ scenario, scales = 'free_x')
pl1 <- pl1 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], 
                            linetype = "Population peak year"), 
                        color = user_defined_baseline_color)
pl1 <- pl1 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (time_series_input == 'external') {
  pl1 <- pl1 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl1 <- pl1 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl1 <- pl1 + theme_LPB_RAP 
pl1 <- pl1 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl1 <- pl1 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl1 <- pl1 + labs (x = x_axis_title,
                   y = y_axis_title,
                   color = legend_title)
pl1 <- pl1 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['weak_conservation']])

# PLOT 2
legend_title <- "Additional built-up"
pl2 <- ggplot(subset_scenario, aes(x = year_date, y = pixels, color = scenario))
pl2 <- pl2 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum, direction = -1)
#pl2 <- pl2 + facet_wrap(~ scenario, scales = 'free_x')
pl2 <- pl2 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], 
                            linetype = "Population peak year"), 
                        color = user_defined_baseline_color)
pl2 <- pl2 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (time_series_input == 'external') {
  pl2 <- pl2 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl2 <- pl2 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl2 <- pl2 + theme_LPB_RAP 
pl2 <- pl2 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl2 <- pl2 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl2 <- pl2 + labs (x = x_axis_title,
                   y = y_axis_title,
                   color = legend_title)
pl2 <- pl2 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])
pl2 <- pl2 + guides(colour = guide_legend(order = 1),
                    line = guide_legend(order = 2))

# PLOT 3 total built-up
subset_total_built_up_scenario <- input_data$LPB_land_use_mplc[[1]] %>%
  filter(LUT_code %in% c('LUT01'))

legend_title <- "Total built-up"
pl3 <- ggplot(subset_total_built_up_scenario, aes(x = year_date, y = pixels, color = scenario))
pl3 <- pl3 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum, direction = -1)
#pl2 <- pl2 + facet_wrap(~ scenario, scales = 'free_x')
pl3 <- pl3 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], 
                            linetype = "Population peak year"), 
                        color = user_defined_baseline_color)
pl3 <- pl3 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (time_series_input == 'external') {
  pl3 <- pl3 + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl3 <- pl3 + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl3 <- pl3 + theme_LPB_RAP 
pl3 <- pl3 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl3 <- pl3 + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
pl3 <- pl3 + labs (x = x_axis_title,
                   y = y_axis_title,
                   color = legend_title)
pl3 <- pl3 + scale_x_date(date_labels = "%Y", breaks = years_for_plotting[['combined']])
pl3 <- pl3 + guides(colour = guide_legend(order = 1),
                    line = guide_legend(order = 2))

# PLOT Joined
title <- ggdraw() + 
  draw_label("Anthropogenic features",
             fontfamily = user_defined_font, size = user_defined_fontsize, fontface = 'bold', color = user_defined_baseline_color,
             x = 0, hjust = 0) 

pl_joined <- plot_grid(title, pl1, pl2, pl3, nrow = 4, ncol = 1, align = 'hv', axis = 'l', labels = c('', 'A', 'B', 'C', scale = 0.75), 
                       rel_heights = c(0.4,1,1,1)) 
pl_joined
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LAND USE mplc RAP juxtaposition scenario comparison ########
if (model_stage == 'MS1') {
  plot_title <- "Land use mplc RAP juxtaposition scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "Land use mplc RAP juxtaposition"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

temp_mplc <- input_data$LPB_land_use_mplc[[1]] %>%
  mutate(type = 'mplc')

temp_rap <- input_data$RAP_land_use[[1]] %>%
  mutate(type = 'RAP')

temp <- temp_mplc %>%
  bind_rows(temp_rap)

pl <- ggplot(temp, aes(x = year_date, y = percentage, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl <- pl + guides(color = guide_legend(ncol=1))
pl <- pl + geom_text_repel(data = subset(temp, year_date == max(year_date)),
                           aes(label = paste0(" ", LUT_code)),
                           family = user_defined_font,
                           size = user_defined_annotation_label_size,
                           min.segment.length = 0,
                           segment.curvature = -0.1,
                           segment.square = TRUE,
                           segment.color = "lightgrey",
                           box.padding = 0.1,
                           point.padding = 0.6,
                           direction = "y",
                           force = 0.5,
                           hjust = -1,
                           nudge_x = 0.15,
                           nudge_y = 1,
                           na.rm = TRUE, 
                           show.legend = FALSE)
pl <- pl + facet_grid(type ~ scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates, limits = user_defined_x_axis_expansion_for_lables)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# Land use mplc RAP juxtaposition selected Land Use Types scenario comparison ###############
# compare only selected LUTs
if (model_stage == 'MS1') {
  plot_title <- "Land use mplc RAP juxtaposition selected Land Use Types scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "Land use mplc RAP juxtaposition selected Land Use Types"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

input_data$LPB_land_use_mplc[[1]]

temp_mplc <- input_data$LPB_land_use_mplc[[1]] %>%
  filter(LUT_code %in% c("LUT01", "LUT02", "LUT03", "LUT04", "LUT05", "LUT17")) %>%
  mutate(type = 'mplc') 

if (local_degradation_simulated == FALSE) {
  temp_rap <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT01", "LUT04", "LUT05", "LUT21", "LUT22", "LUT23", "LUT24")) %>%
    mutate(type = 'RAP')
}

if (local_degradation_simulated == TRUE) {
  temp_rap <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT01", "LUT04", "LUT05", "LUT21", "LUT22", "LUT23", "LUT24", "LUT25")) %>%
    mutate(type = 'RAP')
}
 


temp <- temp_mplc %>%
  bind_rows(temp_rap)

pl <- ggplot(temp, aes(x = year_date, y = percentage, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
pl <- pl + guides(color = guide_legend(ncol=1))
pl <- pl + geom_text_repel(data = subset(temp, year_date == max(year_date)),
                           aes(label = paste0(" ", LUT_code)),
                           family = user_defined_font,
                           size = user_defined_annotation_label_size,
                           min.segment.length = 0,
                           segment.curvature = -0.1,
                           segment.square = TRUE,
                           segment.color = "lightgrey",
                           box.padding = 0.1,
                           point.padding = 0.6,
                           direction = "y",
                           force = 0.5,
                           hjust = -1,
                           nudge_x = 0.15,
                           nudge_y = 1,
                           na.rm = TRUE, 
                           show.legend = FALSE)
pl <- pl + facet_grid(type ~ scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates, limits = user_defined_x_axis_expansion_for_lables)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# LPB landscape modelling probabilities scenario comparison ##############
# plot_title <- "LPB landscape modelling probabilities scenario comparison (bar)" 
# legend_title <- "Probability classes"
# x_axis_title <- "Year"
# y_axis_title <- "Percentage of simulated landscape"
# 
# sorted_data <- input_data$LPB_landscape_modelling_probabilities[[1]] %>%
#   mutate(class = fct_inorder(class))
# 
# pl <- ggplot(sorted_data, aes(x = year_date, y = percentage, fill = class))
# pl <- pl + geom_bar(aes(fill = class), stat = "identity", position = position_dodge())
# pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
# pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
#                           linetype = "Population peak year"),
#                       color = user_defined_baseline_color)
# pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
# pl <- pl + facet_wrap(~ scenario, scales = 'free_x', dir = "v")
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
# pl <- pl + theme(panel.grid.minor.y = element_blank(),
#                  panel.grid.minor.x = element_blank())
# pl <- pl + labs (title = plot_title,
#                  subtitle = paste(subtitle_prefix),
#                  fill = legend_title,
#                  linetype = "Population Peak year",
#                  x = x_axis_title,
#                  y = y_axis_title,
#                  caption = caption_landscape_share)
# pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


if (model_stage == 'MS1') {
  plot_title <- "LPB landscape modelling probabilities scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB landscape modelling probabilities"
}
legend_title <- "Probability classes"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

sorted_data <- input_data$LPB_landscape_modelling_probabilities[[1]] %>%
  mutate(class = fct_inorder(class))

pl <- ggplot(sorted_data, aes(x = year_date, y = percentage, color = class))
pl <- pl + geom_line()
pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum)
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                          linetype = "Population peak year"),
                      color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
pl <- pl + facet_wrap(~ scenario_name_output, scales = 'free_x', dir = "v")
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = paste(subtitle_prefix),
                 color = legend_title,
                 linetype = "Population Peak year",
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
pl
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# # reorder: factor levels
# plot_title <- "LPB landscape modelling probabilities scenario comparison (stacked area)" 
# legend_title <- "Probability classes"
# x_axis_title <- "Year"
# y_axis_title <- "Percentage of simulated landscape"
#
# temp <- input_data$LPB_landscape_modelling_probabilities[[1]] %>%
#   mutate(class = fct_inorder(class))
# 
# pl <- ggplot(temp, aes(x = year_date, y = percentage, fill = class))
# pl <- pl + geom_area(aes(fill = class), stat = "identity", position = position_stack())
# pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
# pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
#                           linetype = "Population peak year"),
#                       color = user_defined_baseline_color)
# pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
# pl <- pl + facet_wrap(~ scenario, scales = 'free_x', dir = "v")
# pl <- pl + theme_LPB_RAP
# pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
# pl <- pl + theme(panel.grid.minor.y = element_blank(),
#                  panel.grid.minor.x = element_blank())
# pl <- pl + labs (title = plot_title,
#                  subtitle = paste(subtitle_prefix),
#                  fill = legend_title,
#                  linetype = "Population Peak year",
#                  x = x_axis_title,
#                  y = y_axis_title,
#                  caption = caption_landscape_share)
# pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)




# Land cover to land use approximation correction step #######
# input_data$LPB_correction_step[[1]]
# View(input_data$LPB_correction_step_transition_matrix[[1]])
# 
# #### modif dk:
# trans_matrix <- read_csv('R_inputs/LPB_correction_step_transition_matrix_weak_conservation.csv') %>%
#   rename(from = 'row_0')
# 
# trans_matrix_long <- trans_matrix %>%
#   pivot_longer(!from, names_to = 'to', values_to = 'n_pixels') %>%
#   filter(n_pixels != 0) %>%
#   mutate(from = paste('LUT', str_pad(from, 2, pad = 0), sep = ''),
#          to = paste('LUT', str_pad(to, 2, pad = 0), sep = '')) %>%
#   left_join(RAP_LUTs_lookup_table, by = c('from' = 'LUT_code')) %>%
#   rename(from_name = LUT_name) %>%
#   left_join(RAP_LUTs_lookup_table, by = c('to' = 'LUT_code')) %>%
#   rename(to_name = LUT_name)
# 
# 
# df <- trans_matrix_long %>%
#   make_long(from_name, to_name, value = 'n_pixels')
# 
# pl <- ggplot(df, aes(x = x, value = value, next_x = next_x, node = node, next_node = next_node, fill = factor(node), label = node)) 
# pl <- pl + geom_sankey(flow.alpha = .6, node.color = "gray30")
# pl <- pl + geom_sankey_label(size = 2, color = "black")
# #scale_fill_viridis_d() 
# pl <- pl + theme_sankey(base_size = 18) 
# pl <- pl + labs(x = NULL) 
# pl <- pl + theme(legend.position = "none",
#                  plot.title = element_text(hjust = .5)) 
# pl <- pl + ggtitle("Car features")
# ggsave('sankey_ggsankey.png', pl, width = 10, height = 10)


# GGSANKEY weak conservation DK + SH #########################################################
plot_title <- "Land cover to land use approximation correction step weak conservation"
legend_title <- "Land Use Types"
#### modif dk:
# trans_matrix <- read_csv('R_inputs/LPB_correction_step_transition_matrix_weak_conservation.csv') %>%
#   rename(from = 'row_0')

trans_matrix <- correction_step_transition_matrix_weak_conservation %>%
  rename(from = 'row_0')

trans_matrix_long <- trans_matrix %>%
  pivot_longer(!from, names_to = 'to', values_to = 'n_pixels') %>%
  filter(n_pixels != 0) %>%
  mutate(from = paste('LUT', str_pad(from, 2, pad = 0), sep = ''),
         to = paste('LUT', str_pad(to, 2, pad = 0), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table, by = c('from' = 'LUT_code')) %>%
  rename(from_name = LUT_name) %>%
  left_join(RAP_LUTs_lookup_table, by = c('to' = 'LUT_code')) %>%
  rename(to_name = LUT_name)

trans_matrix_long

df <- trans_matrix_long %>%
  make_long(from_name, to_name, value = 'n_pixels')

df

pl <- ggplot(df, aes(x = x,
                     value = value,
                     next_x = next_x, 
                     node = node, 
                     next_node = next_node,
                     fill = factor(node),
                     label = node)) 
pl <- pl + geom_sankey(flow.alpha = 0.75, node.color = user_defined_baseline_color)
pl <- pl + geom_sankey_label(size = 2, color = 1, fill = "white") 
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + theme_sankey(base_size = 16)
pl <- pl + theme_LPB_RAP
pl <- pl + theme(panel.grid = element_blank(),
                 panel.border = element_blank(),
                 panel.background = element_blank(),
                 axis.title.x = element_blank(),
                 axis.title.y = element_blank(),
                 axis.text = element_blank(),
                 axis.ticks = element_blank(),
                 axis.text.x = element_blank(),
                 axis.text.y = element_blank(),
                 legend.position = "none")
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 x = NULL,
                 y = NULL)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)



# GGSANKEY enforced conservation DK + SH #########################################################
plot_title <- "Land cover to land use approximation correction step enforced conservation"
legend_title <- "Land Use Types"

trans_matrix <- correction_step_transition_matrix_enforced_conservation %>%
  rename(from = 'row_0')

trans_matrix_long <- trans_matrix %>%
  pivot_longer(!from, names_to = 'to', values_to = 'n_pixels') %>%
  filter(n_pixels != 0) %>%
  mutate(from = paste('LUT', str_pad(from, 2, pad = 0), sep = ''),
         to = paste('LUT', str_pad(to, 2, pad = 0), sep = '')) %>%
  left_join(RAP_LUTs_lookup_table, by = c('from' = 'LUT_code')) %>%
  rename(from_name = LUT_name) %>%
  left_join(RAP_LUTs_lookup_table, by = c('to' = 'LUT_code')) %>%
  rename(to_name = LUT_name)

df <- trans_matrix_long %>%
  make_long(from_name, to_name, value = 'n_pixels')

pl <- ggplot(df, aes(x = x,
                     value = value,
                     next_x = next_x,
                     node = node,
                     next_node = next_node,
                     fill = factor(node),
                     label = node))
pl <- pl + geom_sankey(flow.alpha = 0.75, node.color = user_defined_baseline_color)
pl <- pl + geom_sankey_label(size = 2, color = 1, fill = "white")
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + theme_sankey(base_size = 16)
pl <- pl + theme_LPB_RAP
pl <- pl + theme(panel.grid = element_blank(),
                 panel.border = element_blank(),
                 panel.background = element_blank(),
                 axis.title.x = element_blank(),
                 axis.title.y = element_blank(),
                 axis.text = element_blank(),
                 axis.ticks = element_blank(),
                 axis.text.x = element_blank(),
                 axis.text.y = element_blank(),
                 legend.position = "none")
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 x = NULL,
                 y = NULL)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, ' ', output_format, sep = '')),
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


# Complete Forested areas mplc RAP juxtaposition scenario comparison ###########
input_data$LPB_land_use_mplc[[1]] # LUT 04, 05, 08, 09
input_data$RAP_land_use[[1]] # LUT 04, 05, 08, 09, 21, 22, 23, 25

if (model_stage == 'MS1') {
  plot_title <- "Forested area mplc RAP juxtaposition scenario comparison complete"
}
if (model_stage == 'MS2') {
  plot_title <- "Forested area mplc RAP juxtaposition"
}
legend_title <- "Scenario no FLR vs. potential FLR"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

if (LUT05_depicts_a_forest_type == TRUE & local_degradation_simulated == TRUE) {
  temp_selected_data <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT04", "LUT05", "LUT08", "LUT09", "LUT21", "LUT22", "LUT23", "LUT25")) %>%
    mutate(type = case_when(LUT_code %in% c("LUT04", "LUT05", "LUT08", "LUT09") ~ "mplc\n(probable forested area with no FLR)",
                            LUT_code %in% c("LUT21", "LUT22", "LUT23", "LUT25") ~ "RAP\n(possible additional forested area to mplc\nwith potential FLR)")) 
}

if (LUT05_depicts_a_forest_type == TRUE & local_degradation_simulated == FALSE) {
  temp_selected_data <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT04", "LUT05", "LUT08", "LUT09", "LUT21", "LUT22", "LUT23")) %>%
    mutate(type = case_when(LUT_code %in% c("LUT04", "LUT05", "LUT08", "LUT09") ~ "mplc\n(probable forested area with no FLR)",
                            LUT_code %in% c("LUT21", "LUT22", "LUT23") ~ "RAP\n(possible additional forested area to mplc\nwith potential FLR)"))
}

# Study scenario Holler et al., 2023
if (LUT05_depicts_a_forest_type == FALSE & local_degradation_simulated == TRUE) {
  temp_selected_data <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT04", "LUT08", "LUT09", "LUT21", "LUT22", "LUT23", "LUT25")) %>%
    mutate(type = case_when(LUT_code %in% c("LUT04", "LUT08", "LUT09") ~ "mplc\n(probable forested area with no FLR)",
                            LUT_code %in% c("LUT21", "LUT22", "LUT23", "LUT25") ~ "RAP\n(possible additional forested area to mplc\nwith potential FLR)")) 
}

if (LUT05_depicts_a_forest_type == FALSE & local_degradation_simulated == FALSE) {
  temp_selected_data <- input_data$RAP_land_use[[1]] %>%
    filter(LUT_code %in% c("LUT04", "LUT08", "LUT09", "LUT21", "LUT22", "LUT23")) %>%
    mutate(type = case_when(LUT_code %in% c("LUT04", "LUT08", "LUT09") ~ "mplc\n(probable forested area with no FLR)",
                            LUT_code %in% c("LUT21", "LUT22", "LUT23") ~ "RAP\n(possible additional forested area to mplc\nwith potential FLR)")) 
}


pl <- ggplot(temp_selected_data, aes(x = year_date, y = pixels))
pl <- pl + geom_area(aes(fill = type))
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum)
pl <- pl + facet_grid(~fct_rev(LUT_name)~scenario_name_output, scales = 'free', labeller = label_wrap_gen(width = 25)) # , strip.position = 'right'
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                         linetype = "Population peak year"),
                      color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + theme(legend.key.height = unit(1, "cm"))
pl <- pl + theme(axis.text.x = element_text(size = 6))
pl <- pl + theme(strip.text.y = element_text(angle = 360, hjust = 0, vjust = 1))
pl <- pl + labs (title = plot_title,
                 subtitle = paste(subtitle_prefix),
                 fill = legend_title,
                 linetype = "Population Peak year",
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# Publication Forested areas mplc RAP juxtaposition scenario comparison no and enforced conservation ###########
if (model_stage == 'MS1') {
  plot_title <- "Forested area mplc RAP juxtaposition scenario comparison "
}

legend_title <- "Scenario no FLR vs. potential FLR"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

temp_selected_data <- temp_selected_data %>%
  filter(scenario %in% c("enforced_conservation", "no_conservation"))

pl <- ggplot(temp_selected_data, aes(x = year_date, y = pixels))
pl <- pl + geom_area(aes(fill = type))
pl <- pl + scale_fill_viridis_d(option = user_defined_color_spectrum, guide = guide_legend(order = 1))
pl <- pl + facet_grid(~fct_rev(LUT_name)~scenario_name_output, scales = 'free', labeller = label_wrap_gen(width = 25)) # , strip.position = 'right'
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']],
                          linetype = "Population peak year"),
                      color = '#fc8961',
                      lwd = 1)
pl <- pl + scale_linetype_manual(name = element_blank(), 
                                 values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + new_scale("linetype")
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, 
                            linetype = "Peak demands year"), 
                        color = '#b73779',
                        lwd = 1)
  pl <- pl + scale_linetype_manual(name = element_blank(),
                                   values = c("Peak demands year" = user_defined_linetype_peak_demand_year))
  # pl <- pl + scale_linetype_manual(name = element_blank(), 
  #                                  values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
  # pl <- pl + scale_color_manual(values = c('Peak demands year', 'Population peak year'), guide = guide_legend(override.aes = list(colour = c('#b73779', '#fc8961'))))
}
pl <- pl + theme_LPB_RAP
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + theme(legend.key.height = unit(1, "cm"))
pl <- pl + theme(axis.text.x = element_text(size = 6))
pl <- pl + theme(strip.text.y = element_text(angle = 360, hjust = 0, vjust = 1))
pl <- pl + labs (title = plot_title,
                 subtitle = paste(subtitle_prefix),
                 fill = legend_title,
                 #linetype = "Population Peak year",
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
pl
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

# # WIP: Publication Population driver and forest conversion scenario comparison
# input_data$LPB_deterministic_population[[1]]
# input_data$LPB_forest_conversion[[1]]
# 
# 
# # COWPLOT
# plot_title <- "Population driver and forest conversion scenario comparison"
# legend_title <- "Aspect"
# 
# # PLOT 1
# x_axis_title <- "Year"
# y_axis_title <- "Population"
# pl1 <- ggplot(input_data$LPB_deterministic_population[[1]], aes(x = year_date, y = population, color = "Population"))
# pl1 <- pl1 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum)
# pl1 <- pl1 + facet_wrap(~ scenario, scales = 'free_x')
# pl1 <- pl1 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
# pl1 <- pl1 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
# # subset_only_for_probing_dates <- . %>%
# #   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# # pl <- pl + geom_point(data = subset_only_for_probing_dates)
# pl1 <- pl1 + theme_LPB_RAP 
# pl1 <- pl1 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
# pl1 <- pl1 + theme(panel.grid.minor.y = element_blank(),
#                    panel.grid.minor.x = element_blank())
# pl1 <- pl1 + labs (x = x_axis_title,
#                    y = y_axis_title,
#                    color = legend_title)
# pl1 <- pl1 + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
# 
# # PLOT 2
# x_axis_title <- "Year"
# y_axis_title <- paste("Landscape area in", landscape_area_unit)
# pl2 <- ggplot(input_data$LPB_forest_conversion[[1]], aes(x = year_date, y = pixels, color = "Converted forest"))
# pl2 <- pl2 + geom_line() + scale_color_viridis_d(option = user_defined_color_spectrum, direction = -1)
# pl2 <- pl2 + facet_wrap(~ scenario, scales = 'free_x')
# pl2 <- pl2 + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
# pl2 <- pl2 + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
# # subset_only_for_probing_dates <- . %>%
# #   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# # pl <- pl + geom_point(data = subset_only_for_probing_dates)
# pl2 <- pl2 + theme_LPB_RAP 
# pl2 <- pl2 + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
# pl2 <- pl2 + theme(panel.grid.minor.y = element_blank(),
#                    panel.grid.minor.x = element_blank())
# pl2 <- pl2 + labs (x = x_axis_title,
#                    y = y_axis_title,
#                    color = legend_title)
# pl2 <- pl2 + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates)
# 
# # PLOT Joined
# labels <- ggplot() + labs (title = plot_title,
#                            subtitle = subtitle_prefix) + theme_LPB_RAP + theme(panel.border = element_blank())
# # dk: -> grey outline removed
# 
# # legend: no common legend with cowplot
# pl_joined <- plot_grid(labels, pl1, pl2, nrow = 3, ncol = 1, align = 'hv', axis = 'l', rel_heights = c(0.1, 0.5, 0.5)) 
# 
# ggsave(file.path(output_folder, paste(publication_indicator, ' ', plot_title, ' ', subtitle_prefix, ' ', output_format, sep = '')), 
#        height = output_height, width = output_width, dpi = output_dpi, units = output_unit)


### Land use undisturbed, disturbed forest in the region #######################
subset_regional_forest <- input_data$LPB_land_use_mplc[[1]] %>%
  filter(LUT_code %in% c('LUT08', 'LUT09'))

if (model_stage == 'MS1') {
  plot_title <- "LPB regional forest disturbed undisturbed scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB regional forest disturbed undisturbed"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- "Percentage of simulated landscape"

pl <- ggplot(subset_regional_forest, aes(x = year_date, y = percentage))
pl <- pl + geom_line(aes(color = LUT_name))
pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title,
                 caption = caption_landscape_share)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB pressure aspect land use allocated locally and regionally #######################
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect land use allocated locally and regionally to settlements scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect land use allocated locally and regionally to settlements"
}
legend_title <- "Land Use Types"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

temp_locally <- input_data$LPB_land_use_mplc_allocated_locally[[1]] %>%
  mutate(Aspect = 'locally allocated')
temp_regionally <- input_data$LPB_land_use_mplc_allocated_regionally[[1]] %>%
  mutate(Aspect = 'regionally allocated')

temp <- temp_locally %>%
  bind_rows(temp_regionally)

pl <- ggplot(temp, aes(x = year_date, y = pixels, color = LUT_name))
pl <- pl + geom_line() + scale_color_viridis(option = user_defined_color_spectrum, discrete = TRUE) 
pl <- pl + facet_grid(~Aspect ~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### LPB pressure aspect quality of remaining forest regionally and in restricted areas ##################
if (model_stage == 'MS1') {
  plot_title <- "LPB pressure aspect quality of remaining forest regionally and in restricted areas scenario comparison"
}
if (model_stage == 'MS2') {
  plot_title <- "LPB pressure aspect quality of remaining forest regionally and in restricted areas"
}
legend_title <- "Aspects"
x_axis_title <- "Year"
y_axis_title <- paste("Landscape area in", landscape_area_unit)

subset_regional_forest <- input_data$LPB_land_use_mplc[[1]] %>%
  filter(LUT_code %in% c('LUT08', 'LUT09'))

temp_region <- subset_regional_forest %>%
  mutate(Aspect = "total regional forest")

temp_restricted_areas <- input_data$LPB_land_use_mplc_restricted_areas_remaining_forest[[1]] %>%
  mutate(Aspect = "forest in restricted areas")

temp <- temp_region %>%
  bind_rows(temp_restricted_areas)

pl <- ggplot(temp, aes(x = year_date, y = pixels))
pl <- pl + geom_line(aes(color = LUT_name))
pl <- pl + scale_color_viridis_d(option = user_defined_color_spectrum) 
pl <- pl + facet_grid(~Aspect ~scenario_name_output, scales = 'free_x')
pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
if (model_stage == 'MS1' & time_series_input == 'external') {
  pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
}
# subset_only_for_probing_dates <- . %>%
#   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
# pl <- pl + geom_point(data = subset_only_for_probing_dates)
pl <- pl + theme_LPB_RAP 
pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
pl <- pl + theme(panel.grid.minor.y = element_blank(),
                 panel.grid.minor.x = element_blank())
pl <- pl + labs (title = plot_title,
                 subtitle = subtitle_prefix,
                 color = legend_title,
                 x = x_axis_title,
                 y = y_axis_title)
pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
       height = output_height, width = output_width, dpi = output_dpi, units = output_unit)

### RAP-LUT25 diagram #####################################################
if (local_degradation_simulated == TRUE) {
  # => STATUS: WIP
  input_data$RAP_land_use[[1]]
  
  plot_title <- 'RAP-LUT25 restoration of degraded forest per time step against climate periods'
  legend_title <- "RAP Land Use Type 25"
  climate_title <- "Climate periods"
  x_axis_title <- "Year"
  y_axis_title <- paste("Landscape area in", landscape_area_unit)
  
  temp_rap <- input_data$RAP_land_use[[1]] %>%
    mutate(type = 'RAP')
  
  subset_LUT25 <- temp_rap %>%
    filter(LUT_code %in% c('LUT25'))
  
  pl <- ggplot(data = subset_LUT25)
  pl <- pl + climate_periods_gglayers
  pl <- pl + geom_line(data = subset_LUT25, aes(x = year_date, y = pixels, color = LUT_name)) + scale_color_viridis_d(option = user_defined_color_spectrum) 
  pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
  pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
  if (time_series_input == 'external') {
    pl <- pl + geom_vline(aes(xintercept = peak_demands_year[[1]], linetype = "Peak demands year"), color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
  }
  # subset_only_for_probing_dates <- . %>%
  #   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
  # pl <- pl + geom_point(data = subset_only_for_probing_dates)
  pl <- pl + theme_LPB_RAP 
  pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
  pl <- pl + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
  pl <- pl + labs (title = plot_title,
                   subtitle = subtitle_prefix,
                   color = legend_title,
                   fill = climate_title,
                   x = x_axis_title,
                   y = y_axis_title)
  pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
  pl
  ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}




##################################################################################################################################
### END CODE Model Stage 1 #######################################################################################################
##################################################################################################################################

##################################################################################################################################
### START CODE Model Stage 2 #####################################################################################################
##################################################################################################################################


### MS2 TODO (linetypes in legend): fragmentation mplc RAP juxtaposition diagram #####################
# Status => WIP
if (model_stage == 'MS2' & ms2_fragmentation_simulated == TRUE) {
  plot_title <- 'Fragmentation mplc RAP juxtaposition prior to and post initial FLR measures (user-defined)'
  # code entire diagram in brackets and for scenario use
  
  legend_mplc_title <- "mplc fragmentation prior FLR measures"
  legend_RAP_title <- "RAP fragmentation post initial FLR measures"
  x_axis_title <- "Year"
  y_axis_title <- paste("Value")
  
  mplc <- input_data$LPB_fragmentation[[1]]
  mplc_number_of_patches <- input_data$LPB_fragmentation[[1]] %>%
    filter(Aspect == 'maximum_patch_number')
  mplc_total_area <- input_data$LPB_fragmentation[[1]] %>%
    filter(Aspect == 'total_area_of_patches') %>%
    mutate(across(value, ~. / 100))
  
  RAP<- input_data$RAP_fragmentation[[1]]
  RAP_number_of_patches <- input_data$RAP_fragmentation[[1]] %>%
    filter(Aspect == 'maximum_patch_number')
  RAP_total_area <- input_data$RAP_fragmentation[[1]] %>%
    filter(Aspect == 'total_area_of_patches')%>%
    mutate(across(value, ~. / 100))

  # linetypes = # (blank, solid, dotted, dashed, dotdash, longdash, twodash)
  
  pl <- ggplot()
  # plot the mplc values
  pl <- pl + geom_line(data = mplc_number_of_patches, aes(x = year_date, y = value, color = "Number of patches", linetype = "Number of patches"))
  pl <- pl + geom_line(data = mplc_total_area, aes(x = year_date, y = value, color = "Total area of patches in km2", linetype = "Total area of patches in km2"))
  # pl <- pl + geom_line(data = mplc, aes(x = year_date, y = value, color = c("Number of patches", "Total area of patches in km2"), linetype = c("Number of patches", "Total area of patches in km2")))
  pl <- pl + scale_color_manual(values = c("#3b528b", "#3b528b"), name = legend_mplc_title) # blue lines 
  pl <- pl + scale_linetype_manual(values = c("Number of patches" = 'solid', "Total area of patches in km2" = 'longdash'), name = legend_mplc_title)
  # plot the RAP values
  pl <- pl + new_scale(new_aes = c('color', 'linetype'))
  pl <- pl + geom_line(data = RAP_number_of_patches, aes(x = year_date, y = value, color = "Number of patches", linetype = "Number of patches"))
  pl <- pl + geom_line(data = RAP_total_area, aes(x = year_date, y = value, color = "Total area of patches in km2", linetype = "Total area of patches in km2"))
  #pl <- pl + geom_line(data = RAP, aes(x = year_date, y = value, color = c("Number of patches", "Total area of patches in km2"), linetype = c("Number of patches", "Total area of patches in km2")))
  pl <- pl + scale_color_manual(values = c("#21918c", "#21918c"), name = legend_RAP_title) # petrol lines
  pl <- pl + scale_linetype_manual(values = c("Number of patches" = 'solid', "Total area of patches in km2" = 'longdash'), name = legend_RAP_title)
  # apply scenarios
  pl <- pl + facet_wrap(~scenario_name_output, scales = 'free_x')
  # plot orientation lines
  pl <- pl + new_scale('linetype')
  pl <- pl + geom_vline(aes(xintercept = years_for_plotting[['population_peak']], linetype = "Population peak year"), color = user_defined_baseline_color)
  pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Population peak year" = user_defined_linetype))
  if (model_stage == 'MS1' & time_series_input == 'external') {
    pl <- pl + geom_vline(aes(xintercept = peak_demands_year, linetype = "Peak demands year"), color = user_defined_baseline_color)
    pl <- pl + scale_linetype_manual(name = element_blank(), values = c("Peak demands year" = user_defined_linetype_peak_demand_year, "Population peak year" = user_defined_linetype))
  }
  # subset_only_for_probing_dates <- . %>%
  #   filter(year_date %in% years_for_plotting[[first(.$scenario)]])
  # pl <- pl + geom_point(data = subset_only_for_probing_dates)
  pl <- pl + theme_LPB_RAP 
  pl <- pl + theme(axis.text.x = element_text(angle = user_defined_rotation_angle, hjust = user_defined_x_hjust, vjust = user_defined_x_vjust))
  pl <- pl + theme(panel.grid.minor.y = element_blank(),
                   panel.grid.minor.x = element_blank())
  pl <- pl + labs (title = plot_title,
                   subtitle = subtitle_prefix,
                   color = legend_title,
                   fill = climate_title,
                   x = x_axis_title,
                   y = y_axis_title,
                   caption = "Analysis based on user-defined input Land Use Types")
  pl <- pl + scale_x_date(date_labels = "%Y", breaks = scenario_x_dates) 
  pl
  ggsave(file.path(output_folder, paste(plot_title, ' ', subtitle_prefix, output_format, sep = '')), 
         height = output_height, width = output_width, dpi = output_dpi, units = output_unit)
}

### MS2 TODO: PHC conflict pixels diagram ######################################
if (model_stage == 'MS2' & ms2_potential_habitat_corridors_simulated == TRUE) {
  plot_title <- 'Potential Habitat Corrdiors conflict pixels'
  # code entire diagram in brackets and for scenario use
}

##################################################################################################################################
### END CODE Model Stage 2 #######################################################################################################
##################################################################################################################################

### TODO CITATIONS #############################################################




