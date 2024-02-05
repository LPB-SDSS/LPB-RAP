# 2023/03 OS & SH:

import tempfile
import pathlib
import pylandstats as pls
import pcraster as pcr
import Parameters
import Filepaths
import os


def analysis(raster, time_step, module):
    assert raster.dataType() == pcr.VALUESCALE.Boolean

    # catch the main output-folder-path for the module
    if module == 'mplc':
        main_outputfolder_path = Filepaths.folder_PylandStats_mplc
    if module == 'RAP':
        main_outputfolder_path = Filepaths.folder_PylandStats_RAP

    # get PCRaster conform time step suffix for output generation
    length_of_time_step = len(str(time_step))
    if length_of_time_step == 1:
        time_step_suffix = '.00' + str(time_step)
    elif length_of_time_step == 2:
        time_step_suffix = '.0' + str(time_step)
    elif length_of_time_step == 3:
        time_step_suffix = '.' + str(time_step)

    time_step_pure = time_step_suffix.strip('.')

    # create subfolder
    subfolder_Patch_IDs = os.path.join(main_outputfolder_path, 'Patch-IDs_maps')
    os.makedirs(subfolder_Patch_IDs, exist_ok=True)

    # create the Patch-ID map as input for PyLandStats
    rasterpath = os.path.join(subfolder_Patch_IDs, f"Patch-IDs_map_{time_step_pure}.map")
    clump = pcr.clump(raster)
    pcr.report(clump, str(rasterpath))
    print('created Patch-IDs map:', rasterpath)

    # Insertion: get the maximum number of patches and their total area
    maximum_number_of_patches = int(pcr.mapmaximum(pcr.scalar(clump)))
    total_area_patches = int(pcr.maptotal(pcr.scalar(pcr.boolean(clump))))

    # # calculate on singular patches
    # # always calculate fragmentation
    # metrics = ['fractal_dimension_am']
    # print('fragmentation is calculated as PyLandStats function:', metrics )
    # # get p.r.n. user-defined further metrics
    # additional_landstats_metrics = list(Parameters.get_PyLandStats_metrics())
    # print('user-defined additional metrics are:', additional_landstats_metrics)
    # metrics.extend(additional_landstats_metrics)
    # print('total list of metrics:', metrics)
    #
    # print('calculating with PyLandStats, this may take a while ...')
    # ls = pls.Landscape(rasterpath)
    # class_metrics_df = ls.compute_class_metrics_df(metrics=metrics)
    # print('calculating with PyLandStats done')
    #
    # for metric in metrics:
    #     print('creating output for metric:', metric, '...')
    #     # define for each metric the subfolder in the main outputfolder
    #     output_subfolder_metric = os.path.join(main_outputfolder_path, str(metric))
    #     os.makedirs(output_subfolder_metric, exist_ok=True)
    #     # create the subsubfolder CSV or MAP
    #     output_subsubfolder_csv = os.path.join(output_subfolder_metric, 'CSVs')
    #     os.makedirs(output_subsubfolder_csv, exist_ok=True)
    #     output_subsubfolder_map = os.path.join(output_subfolder_metric, 'MAPs')
    #     os.makedirs(output_subsubfolder_map, exist_ok=True)
    #
    #
    #     # write CSV per time step
    #     if module == 'mplc':
    #         # write to mplc output
    #         tblpath = str(pathlib.Path(output_subsubfolder_csv, f"mplc_{metric}_{time_step_pure}.csv")) # report CSVs in order
    #         class_metrics_df.to_csv(tblpath, columns=[metric], header=False, sep=" ")
    #     if module == 'RAP':
    #         # write to RAP output
    #         tblpath = str(pathlib.Path(output_subsubfolder_csv, f"RAP_{metric}_{time_step_pure}.csv")) # report CSVs in order
    #         class_metrics_df.to_csv(tblpath, columns=[metric], header=False, sep=" ")
    #
    #     r = pcr.lookupscalar(tblpath, clump)
    #     # specifiy the output
    #     if module == 'mplc':
    #         path_metric_mplc = str(pathlib.Path(output_subsubfolder_map, f"mplc_{metric}{time_step_suffix}")) # user PCRaster time step suffix with 3 digits: .001
    #     if module == 'RAP':
    #         path_metric_RAP = str(pathlib.Path(output_subsubfolder_map, f"RAP_{metric}{time_step_suffix}"))  # user PCRaster time step suffix with 3 digits: .001
    #
    #     # report to specified output folder
    #     if module == 'mplc':
    #         pcr.report(r, path_metric_mplc)
    #     if module == 'RAP':
    #         pcr.report(r, path_metric_RAP)
    #
    #     print('creating output for metric:', metric, 'done')

    return maximum_number_of_patches, total_area_patches
