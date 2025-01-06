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
def Create_Bioclimate(Directory, File_Psum, File_Tday, File_Tmin, File_Tmax, File_Bio):
    def On_Error(Message):
        print('failed!\n[Error] {:s}'.format(Message))
        saga_api.SG_Get_Data_Manager().Delete_All() # job is done, free memory resources
        saga_api.SG_UI_ProgressAndMsg_Lock(False)
        return False

    #_____________________________________
    saga_api.SG_UI_ProgressAndMsg_Lock(True)

    print('processing [{:s}]...'.format(Directory), end='', flush=True)

    Tool = saga_api.SG_Get_Tool_Library_Manager().Get_Tool('climate_tools', '10')
    if Tool == None:
        return On_Error('requesting tool: Bioclimatic Variables')
    Tool.Reset()

    def Load_Weather(Month):
        print('{:d}'.format(Month), end='', flush=True)
        Psum = saga_api.SG_Get_Data_Manager().Add_Grid(Directory + File_Psum.format(Month))
        Tday = saga_api.SG_Get_Data_Manager().Add_Grid(Directory + File_Tday.format(Month))
        Tmin = saga_api.SG_Get_Data_Manager().Add_Grid(Directory + File_Tmin.format(Month))
        Tmax = saga_api.SG_Get_Data_Manager().Add_Grid(Directory + File_Tmax.format(Month))
        if Psum and Tday and Tmin and Tmax:
            Tday.Set_Scaling(0.1)
            Tmin.Set_Scaling(0.1)
            Tmax.Set_Scaling(0.1)
            Tool.Get_Parameter('P'    ).asList().Add_Item(Psum)
            Tool.Get_Parameter('TMEAN').asList().Add_Item(Tday)
            Tool.Get_Parameter('TMIN' ).asList().Add_Item(Tmin)
            Tool.Get_Parameter('TMAX' ).asList().Add_Item(Tmax)
            return True
        return False

    for Month in range(0, 12):
        if not Load_Weather(Month + 1):
            return On_Error('loading weather for {:d}. month'.format(Month + 1))

    Tool.Set_Parameter('SEASONALITY', 1) # 'Standard Deviation'

    if Tool.Execute() == False:
        return On_Error('executing tool: ' + Tool.Get_Name().c_str())

    #_____________________________________
    def Save_Variable(Variable):
        Grid = Tool.Get_Parameter('BIO_{:02d}'.format(Variable)).asGrid()
        if Grid and Grid.is_Valid():
            if Variable <= 11: # temperatures as 10th degree, scaling factor 10!
                Grid.Set_Scaling(10.)
            print('.', end='', flush=True)
            Grid.Save(Directory + File_Bio.format(Variable))

    for Variable in range(1, 1 + 19):
        Save_Variable(Variable)

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
		Directory = '/mnt/works/_chelsa/chelsa_{:d}'.format(Year) + '/tile_{:02d}/'

		File_Psum = 'CHELSA_pr_mon_MPI-ESM-MR_rcp45_{:02d}'     + '_{:d}.sg-grd-z'.format(Year)
		File_Tday = 'CHELSA_tas_mon_MPI-ESM-MR_rcp45_{:02d}'    + '_{:d}.sg-grd-z'.format(Year)
		File_Tmin = 'CHELSA_tasmin_mon_MPI-ESM-MR_rcp45_{:02d}' + '_{:d}.sg-grd-z'.format(Year)
		File_Tmax = 'CHELSA_tasmax_mon_MPI-ESM-MR_rcp45_{:02d}' + '_{:d}.sg-grd-z'.format(Year)
		File_Bio  = 'CHELSA_bio{:02d}_mon_MPI-ESM-MR_rcp45'     + '_{:d}.sg-grd-z'.format(Year)

		for Tile in range(0, 36):
			Create_Bioclimate(Directory.format(Tile + 1), File_Psum, File_Tday, File_Tmin, File_Tmax, File_Bio)


#_________________________________________
##########################################
