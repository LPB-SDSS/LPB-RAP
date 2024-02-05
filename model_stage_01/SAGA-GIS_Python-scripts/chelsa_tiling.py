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
def Create_Tiles(File_Source, Dir_Target_Root):
    def On_Error(Message):
        print('failed!\n[Error] {:s}'.format(Message))
        saga_api.SG_Get_Data_Manager().Delete_All() # job is done, free memory resources
        saga_api.SG_UI_ProgressAndMsg_Lock(False)
        return False

    #_____________________________________
    saga_api.SG_UI_ProgressAndMsg_Lock(True)

    Name, Ext = os.path.splitext(os.path.basename(File_Source))

    print('processing [{:s}]...'.format(Name), end='', flush=True)

    Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('grid_tools', '27')
    if Tool == None:
        return On_Error('requesting tool: Tiling')

    Grid = saga_api.SG_Get_Data_Manager().Add(File_Source)
    if not Grid or not Grid.is_Valid():
        return On_Error('loading grid: {:s}'.format(File_Source))

    Tool.Reset()
    Tool.Set_Parameter('GRID'      , Grid)
    Tool.Set_Parameter('TILES_SAVE', False)
    Tool.Set_Parameter('OVERLAP'   , 0)
    Tool.Set_Parameter('METHOD'    , 0) # 'number of grid cells per tile'
    Tool.Set_Parameter('NX'        , 5220)
    Tool.Set_Parameter('NY'        , 5220)

    if Tool.Execute() == False:
        return On_Error('executing tool: ' + Tool.Get_Name().c_str())

    #_____________________________________
    Tiles = Tool.Get_Parameter('TILES').asList()
    for i in range(0, Tiles.Get_Data_Count()):
        print('.', end='', flush=True)
        Dir_Target = '{:s}/tile_{:02d}/'.format(Dir_Target_Root, i + 1)
        if not os.path.exists(Dir_Target):
            os.makedirs(Dir_Target)
        Tiles.Get_Data(i).Save('{:s}/{:s}.sg-grd-z'.format(Dir_Target, Name))

    #_____________________________________
    print('okay')
    saga_api.SG_Get_Data_Manager().Delete_All() # job is done, free memory resources
    saga_api.SG_UI_ProgressAndMsg_Lock(False)
    return True


#_________________________________________
##########################################
def Run_Processing():
	Years = [2030, 2090]

	for Year in Years:
		Dir_Source = '/mnt/data/data/_data_by_type/Climate/chelsa/chelsa_v1.2/chelsa_mpi-esm-mr_rcp45_{:d}/'.format(Year)
		Dir_Target = '/mnt/works/_chelsa/chelsa_{:d}/'.format(Year)

		for Month in range(0, 12):
			Create_Tiles(Dir_Source + 'CHELSA_pr_mon_MPI-ESM-MR_rcp45_{:02d}_{:d}.tif'    .format(Month + 1, Year), Dir_Target)
			Create_Tiles(Dir_Source + 'CHELSA_tas_mon_MPI-ESM-MR_rcp45_{:02d}_{:d}.tif'   .format(Month + 1, Year), Dir_Target)
			Create_Tiles(Dir_Source + 'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_{:02d}_{:d}.tif'.format(Month + 1, Year), Dir_Target)
			Create_Tiles(Dir_Source + 'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_{:02d}_{:d}.tif'.format(Month + 1, Year), Dir_Target)


#_________________________________________
##########################################
