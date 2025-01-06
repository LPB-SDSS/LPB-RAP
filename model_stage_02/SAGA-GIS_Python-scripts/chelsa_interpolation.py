#! /usr/bin/env python

#################################################################################
# MIT License

# Copyright (c) 2022 Olaf Conrad

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################

#_________________________________________
##########################################
import os, saga_api


#_________________________________________
##########################################
def Save_As_GeoTIFF(Grid, File, Options = 'COMPRESS=LZW PREDICTOR=2'):
	Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('io_gdal', '2')
	if not Tool:
		return False
	Tool.Reset()
	Tool.Get_Parameter('GRIDS').asList().Add_Item(Grid)
	Tool.Set_Parameter('FILE'   , File)
	Tool.Set_Parameter('OPTIONS', Options)
	return Tool.Execute()


#_________________________________________
##########################################
def Interpolate_Grid(X0, File0, X1, File1, X, File, Type = 4):
    def On_Error(Message):
        saga_api.SG_Get_Data_Manager().Delete_All()
        saga_api.SG_UI_ProgressAndMsg_Lock(False)
        print('failed\n[Error] {:s}'.format(Message))
        return False

    Name, Ext = os.path.splitext(os.path.basename(File))
    print('interpolating \'{:s}\'...'.format(Name), end='', flush=True)

    if os.path.exists(File):
        print('already processed')
        return True

    saga_api.SG_UI_ProgressAndMsg_Lock(True)

    Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('grid_calculus', '1')
    if not Tool:
        return On_Error('Failed to request tool: Grid Calculator')

    Grid0 = saga_api.SG_Get_Data_Manager().Add_Grid(File0)
    if not Grid0 or not Grid0.is_Valid():
        return On_Error('load grid: ' + File0)

    Grid1 = saga_api.SG_Get_Data_Manager().Add_Grid(File1)
    if not Grid1 or not Grid1.is_Valid():
        return On_Error('load grid: ' + File1)

    Tool.Reset()
    Tool.Get_Parameter('GRIDS' ).asList().Add_Item(Grid0)
    Tool.Get_Parameter('XGRIDS').asList().Add_Item(Grid1)
    Tool.Set_Parameter('FORMULA'   , 'g1 + (h1 - g1) * {:f}'.format((X - X0) / (X1 - X0)))
    Tool.Set_Parameter('NAME'      , Name)
    Tool.Set_Parameter('TYPE'      , Type) # 4 => '2-byte signed int', 7 => '4-byte float'
    Tool.Set_Parameter('RESAMPLING', 0) # 0 => none; 3 => 'B-Spline Interpolation'

    if not Tool.Execute():
        return On_Error('execute tool ' + Tool.Get_Name().c_str())

    if Ext != '.tif':
        Tool.Get_Parameter('RESULT').asGrid().Save(File)
    elif not Save_As_GeoTIFF(Tool.Get_Parameter('RESULT').asGrid(), File):
        return On_Error('save as GeoTIFF')

    saga_api.SG_Get_Data_Manager().Delete_All() # job is done, free memory resources
    saga_api.SG_UI_ProgressAndMsg_Lock(False)

    print('okay')
    return True


#_________________________________________
##########################################
def Interpolate_Grids(Directory, Filter, Year):
    if not os.path.exists(Directory[2]):
        os.makedirs(Directory[2])

    for Month in range(1, 12 + 1):
        Interpolate_Grid(
            Year[0], Directory[0] + os.sep + Filter[0].format(Month),
            Year[1], Directory[1] + os.sep + Filter[1].format(Month),
            Year[2], Directory[2] + os.sep + Filter[2].format(Month)
        )


#_________________________________________
##########################################
def Run_Processing():
	CHELSA_Root = '/mnt/data/data/_data_by_type/Climate/chelsa/chelsa_v1.2/'

	#_____________________________________
	# 2030 ###############################

	Year = [2000, 2050, 2030]

	Directory = [
		CHELSA_Root + 'climatologies',
		CHELSA_Root + 'chelsa_mpi-esm-mr_rcp45_2041-60',
		CHELSA_Root + 'chelsa_mpi-esm-mr_rcp45_2030'
	]

	#_____________________________________
	# 2030 - precipitation
	Filter = [
		'CHELSA_prec_{:02d}_V1.2_land.tif',
		'CHELSA_pr_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060.tif',
		'CHELSA_pr_mon_MPI-ESM-MR_rcp45_{:02d}_2030.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2030 - temperature, mean
	Filter = [
		'CHELSA_temp10_{:02d}_1979-2013_V1.2_land.tif',
		'CHELSA_tas_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tas_mon_MPI-ESM-MR_rcp45_{:02d}_2030.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2030 - temperature, max
	Filter = [
		'CHELSA_tmax10_{:02d}_1979-2013_V1.2_land.tif',
		'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_{:02d}_2030.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2030 - temperature, min
	Filter = [
		'CHELSA_tmin10_{:02d}_1979-2013_V1.2_land.tif',
		'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_{:02d}_2030.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2090 ###############################

	Year = [2050, 2070, 2090]

	Directory = [
		CHELSA_Root + 'chelsa_mpi-esm-mr_rcp45_2041-60',
		CHELSA_Root + 'chelsa_mpi-esm-mr_rcp45_2061-80',
		CHELSA_Root + 'chelsa_mpi-esm-mr_rcp45_2090'
	]

	#_____________________________________
	# 2090 - precipitation
	Filter = [
		'CHELSA_pr_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060.tif',
		'CHELSA_pr_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2061-2080.tif',
		'CHELSA_pr_mon_MPI-ESM-MR_rcp45_{:02d}_2090.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2090 - temperature, mean
	Filter = [
		'CHELSA_tas_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tas_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2061-2080_V1.2.tif',
		'CHELSA_tas_mon_MPI-ESM-MR_rcp45_{:02d}_2090.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2090 - temperature, max
	Filter = [
		'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2061-2080_V1.2.tif',
		'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_{:02d}_2090.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)

	#_____________________________________
	# 2090 - temperature, min
	Filter = [
		'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2041-2060_V1.2.tif',
		'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_r1i1p1_g025.nc_{:d}_2061-2080_V1.2.tif',
		'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_{:02d}_2090.tif'
	]

	Interpolate_Grids(Directory, Filter, Year)


#_________________________________________
##########################################
