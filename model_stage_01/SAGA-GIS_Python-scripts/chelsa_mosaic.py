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
def Save_GeoTIFF(Grid, File, Scale = 1., Offset = 0., Options = 'COMPRESS=LZW PREDICTOR=2'):
	if   Scale == 0.: # reset scaling/offset, if any...
		Grid.Set_Scaling(1., 0.)
	elif Scale != 1. or Offset != 0. or Grid.Get_Type() != saga_api.SG_DATATYPE_Short:
		Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('grid_calculus', '1')
		Tool.Reset()
		Tool.Get_Parameter('GRIDS').asList().Add_Item(Grid)
		Tool.Set_Parameter('TYPE'   , 4) # '2 byte signed integer')
		Tool.Set_Parameter('FORMULA', '({:f})+g1*({:f})'.format(Offset, Scale))
		if Tool.Execute() == True:
			Grid = Tool.Get_Parameter('RESULT').asGrid()

    #_____________________________________
	Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('io_gdal', '2')
	if Tool == None:
		print('failed to get tool: Export GeoTIFF')
		return False

	Tool.Reset()
	Tool.Get_Parameter('GRIDS').asList().Add_Item(Grid)
	Tool.Set_Parameter('FILE'   , File)
	Tool.Set_Parameter('OPTIONS', Options)

	return Tool.Execute()


#_________________________________________
##########################################
def Create_Mosaic(Dir_Tiles, Dir_Mosaic, Name, nTiles = 36):
    def On_Error(Message):
        print('failed!\n[Error] {:s}'.format(Message))
        saga_api.SG_Get_Data_Manager().Delete_All() # job is done, free memory resources
        saga_api.SG_UI_ProgressAndMsg_Lock(False)
        return False

    #_____________________________________
    saga_api.SG_UI_ProgressAndMsg_Lock(True)

    print('processing [{:s}]'.format(Name), end='', flush=True)

    Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('grid_tools', '3')
    if not Tool:
        return On_Error('requesting tool: Mosaicking')
    Tool.Reset()

    Tool.Set_Parameter('NAME'             , Name)
    Tool.Set_Parameter('TYPE'             , 4) # '2 byte signed integer'
    Tool.Set_Parameter('RESAMPLING'       , 0) # 'Nearest Neighbour'
    Tool.Set_Parameter('OVERLAP'          , 1) # 'last'
    Tool.Set_Parameter('MATCH'            , 0) # 'none'
    Tool.Set_Parameter('TARGET_DEFINITION', 0) # 'user defined'

    #_____________________________________
    Cellsize = -1.
    Extent   = saga_api.CSG_Rect()

    for Tile in range(0, nTiles):
        print('.', end='', flush=True)
        Grid = saga_api.SG_Get_Data_Manager().Add_Grid(Dir_Tiles.format(Tile + 1) + Name)
        if not Grid or not Grid.is_Valid():
            return On_Error('loading {:d}. tile'.format(Tile + 1))
        Tool.Get_Parameter('GRIDS').asList().Add_Item(Grid)
        if Cellsize < 0:
            Cellsize = Grid.Get_Cellsize()
            Extent   = Grid.Get_Extent  ()
        else:
            Extent.Union(Grid.Get_Extent())

    Tool.Set_Parameter('TARGET_USER_SIZE', 0.0083333333)
    Tool.Set_Parameter('TARGET_USER_XMIN', Extent.Get_XMin())
    Tool.Set_Parameter('TARGET_USER_XMAX', Extent.Get_XMin() + Cellsize * (43200 - 1))
    Tool.Set_Parameter('TARGET_USER_YMIN', Extent.Get_YMin())
    Tool.Set_Parameter('TARGET_USER_YMAX', Extent.Get_YMin() + Cellsize * (20880 - 1))

    #_____________________________________
    print('|...', end='', flush=True)

    if not Tool.Execute():
        return On_Error('executing tool: ' + Tool.Get_Name().c_str())

    #_____________________________________
    Name, Ext = os.path.splitext(Name)

    Grid = Tool.Get_Parameter('TARGET_OUT_GRID').asGrid()

    if not Grid or not Save_GeoTIFF(Grid, Dir_Mosaic + Name + '.tif'):
        return On_Error('saving GeoTIFF')

    #print(saga_api.SG_Get_Data_Manager().Get_Summary().c_str())

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
		Dir_Tiles  = '/mnt/works/_chelsa/chelsa_{:d}'.format(Year) + '/tile_{:02d}/'
		Dir_Mosaic = '/mnt/data/data/_data_by_type/Climate/chelsa/chelsa_v1.2/chelsa_mpi-esm-mr_rcp45_{:d}/'.format(Year)

		if not os.path.exists(Dir_Mosaic):
			os.makedirs(Dir_Mosaic)

		File_Bio  = 'CHELSA_bio{:02d}_mon_MPI-ESM-MR_rcp45' + '_{:d}.sg-grd-z'.format(Year)

		for Variable in range(1, 1 + 19):
			Create_Mosaic(Dir_Tiles, Dir_Mosaic, File_Bio.format(Variable))


#_________________________________________
##########################################
