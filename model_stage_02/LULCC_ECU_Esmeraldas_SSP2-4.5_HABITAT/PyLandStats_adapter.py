# 2023/03 OS & SH:

import tempfile
import pathlib
import pylandstats as pls
import pcraster as pcr
import Parameters
import Filepaths
import os, sys
import time

module_start = time.time()

# get the arguments from command
time_step = sys.argv[1]
module = sys.argv[2]

# catch the main output-folder-path for the module
if module == 'mplc':
    main_outputfolder_path = os.path.join(Filepaths.folder_landscape_metrics_mplc, 'PyLandStats_CSVs')
if module == 'RAP':
    main_outputfolder_path = os.path.join(Filepaths.folder_landscape_metrics_RAP, 'PyLandStats_CSVs')

# get PCRaster conform time step suffix for output generation
length_of_time_step = len(str(time_step))
if length_of_time_step == 1:
    time_step_suffix = '.00' + str(time_step)
elif length_of_time_step == 2:
    time_step_suffix = '.0' + str(time_step)
elif length_of_time_step == 3:
    time_step_suffix = '.' + str(time_step)

time_step_pure = time_step_suffix.strip('.')

if module == 'mplc':
    clump_map = os.path.join(Filepaths.folder_ecosystem_fragmentation_PatchID_mplc, 'umbrella_species_ecosystem_fragmentation_PatchID.' + time_step_pure)
if module == 'RAP':
    clump_map = os.path.join(Filepaths.folder_ecosystem_fragmentation_PatchID_RAP, 'umbrella_species_ecosystem_fragmentation_PatchID.' + time_step_pure)


# calculate on singular patches
# always calculate fragmentation
metrics = ['fractal_dimension_am']
print('fragmentation is calculated as PyLandStats function:', metrics )
# get p.r.n. user-defined further metrics
# test if list is empty:
additional_landstats_metrics = list(Parameters.get_PyLandStats_metrics())
if len(additional_landstats_metrics) != 0:
    print('user-defined additional PyLandStats metrics are:', additional_landstats_metrics)
    metrics.extend(additional_landstats_metrics)
    print('total list of metrics:', metrics)

print('calculating with PyLandStats, this may take a while ...')
ls = pls.Landscape(clump_map)
class_metrics_df = ls.compute_class_metrics_df(metrics=metrics)
print('calculating with PyLandStats done')

for metric in metrics:
    print('creating output for metric:', metric, 'in module:', module, 'in folder:', main_outputfolder_path, '...')
    # define for each metric the subfolder in the main outputfolder
    output_subfolder_metric = os.path.join(main_outputfolder_path, str(metric))
    os.makedirs(output_subfolder_metric, exist_ok=True)

    # write CSV per metric per time step
    if module == 'mplc':
        # write to mplc output
        tblpath = str(pathlib.Path(output_subfolder_metric, f"mplc_{metric}_{time_step_pure}.csv")) # report CSVs in order
        class_metrics_df.to_csv(tblpath, columns=[metric], header=False, sep=" ")
    if module == 'RAP':
        # write to RAP output
        tblpath = str(pathlib.Path(output_subfolder_metric, f"RAP_{metric}_{time_step_pure}.csv")) # report CSVs in order
        class_metrics_df.to_csv(tblpath, columns=[metric], header=False, sep=" ")

    print('creating output for', tblpath , 'done')

module_end = time.time()
print('module calculation time in minutes:', ((module_end - module_start)/60))