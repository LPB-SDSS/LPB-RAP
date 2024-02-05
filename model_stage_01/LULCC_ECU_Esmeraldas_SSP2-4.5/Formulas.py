"""LAFORET-PLUC-BE-RAP/SFM/OC - FORMULAS
Sonja Holler (SH, RAP), Melvin Lippe (ML, OC) and Daniel Kuebler (DK, SFM), 2021/Q2-2022/Q3
This document provides different formulas for the interface variables used in
LULCC for different model versions (RAP or SFM)."""

# Changes to PLUC for LPB-RAP/SFM model stage 1 made by:
# SH: commented/out-commented by Sonja Holler
# ML: commented/out-commented by Melvin Lippe
# DK: commented/out-commented by Daniel Kuebler

from pcraster import *
from pcraster.framework import *
import numpy
import Parameters
import Filepaths

###################################################################################################
# For testing, debugging and submission: set random seed to make the results consistent (1)
# set random seed 0 = every time new results
seed = int(Parameters.get_random_seed())
setrandomseed(seed)

###################################################################################################


# SH: LPB addition
if Parameters.get_annual_AGB_increment_simulation_decision() == 'spatially-explicit': # could not be used for model stage 1 Esmeraldas
    def get_AGB_growth_formula(AGB_map,
                               projection_potential_maximum_undisturbed_AGB_map,
                               projection_potential_annual_undisturbed_AGB_increment_map,
                               projection_potential_annual_disturbed_AGB_increment_map,
                               projection_potential_annual_plantation_AGB_increment_map,
                               environment_map,
                               null_mask_map):
        if Parameters.get_model_version() == 'LPB-basic' or Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
            # SH: add the potential annual increment for the climate period to AGB for all forest type cells (gross_forest)

            # PRE-CALCULATIONS
            # 1) undisturbed
            undisturbed_AGB_map = ifthen(scalar(environment_map) == scalar(9),
                                         scalar(AGB_map) + scalar(projection_potential_annual_undisturbed_AGB_increment_map))

            # 2 ) disturbed
            disturbed_AGB_map = ifthen(scalar(environment_map) == scalar(8),
                                       scalar(AGB_map) + scalar(projection_potential_annual_disturbed_AGB_increment_map))

            # 3) plantation
            plantation_AGB_map = ifthen(scalar(environment_map) == scalar(5),
                                        scalar(AGB_map) + scalar(projection_potential_annual_plantation_AGB_increment_map))

            # 4) agroforestry
            # for agroforestry no spatially explicit increment can be applied, since systems and stadiums can differ widely from cell to cell.
            # Therefore it is modelled stochastically in the range of disturbed forest increment
            boolean_agroforestry_map = ifthen(scalar(environment_map) == scalar(4),
                                              scalar(1))

            agroforestry_AGB_increment_range_start = mapminimum(projection_potential_annual_disturbed_AGB_increment_map)
            agroforestry_AGB_increment_range_end = mapmaximum(projection_potential_annual_disturbed_AGB_increment_map)

            # To get stochastic results for each cell built an numpy array
            setclone(boolean_agroforestry_map)

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().uniform(low=agroforestry_AGB_increment_range_start,high=agroforestry_AGB_increment_range_end, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            agroforestry_AGB_map = ifthen(scalar(boolean_agroforestry_map) == scalar(1),
                                          scalar(AGB_map) + scalar(a_map))

            # now combine all four maps into one AGB_map again
            AGB_map_incl_disturbed_undisturbed = cover(undisturbed_AGB_map, disturbed_AGB_map)
            AGB_map_incl_plantation = cover(plantation_AGB_map, AGB_map_incl_disturbed_undisturbed)
            AGB_map_incl_agroforestry = cover(agroforestry_AGB_map, AGB_map_incl_plantation)

            # TOTAL AGB MAP WITH INCREMENTS
            AGB_map = AGB_map_incl_agroforestry

            # P.R.N. CORRECTED TO POTENTIAL MAXIMUM
            # correct this map again to the potential maximum AGB per climate period per cell
            # (anticipated climax stadium) # HINT: this depicts a regional trend, it will be further developed in model stage 2 for a cell by cell basis
            AGB_map = ifthenelse(scalar(AGB_map) > scalar(projection_potential_maximum_undisturbed_AGB_map),
                                 scalar(projection_potential_maximum_undisturbed_AGB_map),
                                 scalar(AGB_map))

            AGB_map = cover(scalar(AGB_map), scalar(null_mask_map))
            # in LULCC.py this map is taken for the time step as input and anthropogenic outtake subtracted


        # SFM approach by DK:
        elif Parameters.get_model_version() == 'LPB-SFM':
            AGB_map = null_mask_map  # TODO DK
        else:
            pass

        return AGB_map
elif Parameters.get_annual_AGB_increment_simulation_decision() == 'stochastic':
    def get_AGB_growth_formula(AGB_map,
                               projection_potential_maximum_undisturbed_AGB_map,
                               AGB_annual_increment_ranges_in_Mg_per_ha_dictionary,
                               environment_map,
                               null_mask_map):
        if Parameters.get_model_version() == 'LPB-basic' or Parameters.get_model_version() == 'LPB-mplc' or Parameters.get_model_version() == 'LPB-RAP':
            # SH: add the potential annual increment for the climate period to AGB for all forest type cells (gross_forest)
            setclone(f"{Filepaths.file_static_null_mask_input}.map")

            # undisturbed forest
            undisturbed_AGB_increment_range_start = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['undisturbed_forest'][0]
            undisturbed_AGB_increment_range_end = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['undisturbed_forest'][1]

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().uniform(low=undisturbed_AGB_increment_range_start,
                                            high=undisturbed_AGB_increment_range_end, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            undisturbed_AGB_map = ifthen(scalar(environment_map) == scalar(9),
                                          scalar(AGB_map) + scalar(a_map))

            # disturbed forest
            disturbed_AGB_increment_range_start = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['disturbed_forest'][0]
            disturbed_AGB_increment_range_end = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['disturbed_forest'][1]

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().uniform(low=disturbed_AGB_increment_range_start,
                                            high=disturbed_AGB_increment_range_end, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            disturbed_AGB_map = ifthen(scalar(environment_map) == scalar(8),
                                       scalar(AGB_map) + scalar(a_map))

            # plantation
            plantation_AGB_increment_range_start = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['plantation'][0]
            plantation_AGB_increment_range_end = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['plantation'][1]

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().uniform(low=plantation_AGB_increment_range_start,
                                            high=plantation_AGB_increment_range_end, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            plantation_AGB_map = ifthen(scalar(environment_map) == scalar(5),
                                       scalar(AGB_map) + scalar(a_map))

            # agroforestry
            agroforestry_AGB_increment_range_start = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['agroforestry'][0]
            agroforestry_AGB_increment_range_end = \
                AGB_annual_increment_ranges_in_Mg_per_ha_dictionary['agroforestry'][1]

            ncols = clone().nrCols()
            nrows = clone().nrRows()
            np_array = Parameters.get_rng().uniform(low=agroforestry_AGB_increment_range_start,
                                            high=agroforestry_AGB_increment_range_end, size=(nrows, ncols))
            numpy2pcr(pcraster.Scalar, np_array, 9999)
            a_map = numpy2pcr(pcraster.Scalar, np_array, 9999)

            agroforestry_AGB_map = ifthen(scalar(environment_map) == scalar(4),
                                          scalar(AGB_map) + scalar(a_map))

            # now combine all four maps into one AGB_map again
            AGB_map_incl_disturbed_undisturbed = cover(undisturbed_AGB_map, disturbed_AGB_map)
            AGB_map_incl_plantation = cover(plantation_AGB_map, AGB_map_incl_disturbed_undisturbed)
            AGB_map_incl_agroforestry = cover(agroforestry_AGB_map, AGB_map_incl_plantation)

            # TOTAL AGB MAP WITH INCREMENTS
            AGB_map = AGB_map_incl_agroforestry

            # P.R.N. CORRECTED TO POTENTIAL MAXIMUM
            # correct this map again to the potential maximum AGB per climate period per cell
            # (anticipated climax stadium) # HINT: this depicts a regional trend, it might be further developed in model stage 2 for a cell by cell basis
            AGB_map = ifthenelse(scalar(AGB_map) > scalar(projection_potential_maximum_undisturbed_AGB_map),
                                 scalar(projection_potential_maximum_undisturbed_AGB_map),
                                 scalar(AGB_map))

            AGB_map = cover(scalar(AGB_map), scalar(null_mask_map))
            # in LULCC.py this map is taken for the time step as input and anthropogenic outtake subtracted

            return AGB_map