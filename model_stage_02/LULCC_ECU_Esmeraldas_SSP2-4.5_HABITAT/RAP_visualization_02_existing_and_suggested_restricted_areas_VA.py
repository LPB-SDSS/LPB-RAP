"""LAFORET-PLUC-BE-RAP/SFM - targeted net forest map
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK), 
2021 Q2/Q3 
(Re-)written according to PEP 8 and modified original model. 
Based on:

Make an MP4 file of the output of the LUC model of Mozambique
Judith Verstegen, 2017-07-04"""

from matplotlib import animation
from matplotlib import colors as cls
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.font_manager import FontProperties
import matplotlib.cm
plt.switch_backend('agg')
import numpy as np
import matplotlib as mpl
colormap = mpl.colormaps['viridis'].resampled(5)
from pcraster import *
import Parameters
import Filepaths
import ast
import json
# get the filename for the output:
import sys
import os
filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
filename = str(filename)

dictionary_of_restricted_areas = json.loads(sys.argv[1])
# get the list with new conflict pixels
list_of_restricted_area_values = dictionary_of_restricted_areas['list_restricted_areas']
print('list_of_restricted_area_values:', list_of_restricted_area_values)

population_peak_year = int(list_of_restricted_area_values[0])
existing_areas = int(list_of_restricted_area_values[1])
existing_areas_percentage_of_landscape = float(list_of_restricted_area_values[2])
suggested_areas = int(list_of_restricted_area_values[3])
potential_total_area_value = existing_areas + suggested_areas
potential_total_percentage_of_landscape = float(list_of_restricted_area_values[4])

# get the list with new conflict pixels
list_of_restricted_area_LUTs = dictionary_of_restricted_areas['list_of_LUTs_for_definition_of_potential_restricted_areas']
print('list_of_restricted_area_LUTs:', list_of_restricted_area_LUTs)

##############
### inputs ###
##############

## SH: LPB alternation
timesteps = 1
init_year = population_peak_year
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'RAP_restricted_areas.map'

## SH: LPB alternation
list_all_colors = {0:'white',
                   1: 'black',
                   2: colormap(2),
                   3: colormap(5),
                   }

list_all_names = {1:'= region',
                   2:'= existing restricted areas',
                   3:'= simulated potential additional restricted areas',
                   }

## SH: LPB alternation
legend_loc = (0.975,0.175)  # Esmeraldas right bottom

############
### MAIN ###
############

## SH: LPB alternation
# SH: look up the files in the according new output folder
wd = os.getcwd()
# open the raster and read out the data in a numpy array
in_fn = os.path.join(wd, Filepaths.folder_RAP_restricted_areas, fn)
setclone(in_fn)
amap = readmap(in_fn)
data = pcr2numpy(amap, 0)

# create custom color map
colorlist = []

valuelist = list(list_all_names.keys())
for i in range(0, len(valuelist)):
    valuelist[i] = int(valuelist[i])
maxvalue = np.max(valuelist)
intmaxvalue = maxvalue.item()
for i in range(0, intmaxvalue + 1):
    if i in list_all_colors:
        colorlist.append(list_all_colors.get(i))     
    else:
        colorlist.append('None')

# create the figure
f, axarr = plt.subplots(1)
plt.axis('off')
# making color map and normalization scheme
cmap_long = cls.ListedColormap(colorlist, name='long')
norm_without_mv = cls.Normalize(vmin=0, \
                    vmax = intmaxvalue)
# create the legend
p = []
s = []

## SH: LPB alternation
# JV: loop over reversed list for ascending order
for nr in list_all_names.keys():#[::-1]:
  p.append(plt.Circle((0, 0), radius=3, lw=0, fc=list_all_colors[nr]))
  s.append(list_all_names[nr])
leg = axarr.legend(p, s, loc='right', bbox_to_anchor=legend_loc,\
                   prop={'size':4}, ncol=1, fancybox=True,\
                   borderpad=0.2, bbox_transform=f.transFigure)
title = axarr.text(-0.2, 1.05, '', weight='semibold', transform=axarr.transAxes)
title_annotation = axarr.text(-0.2, 1, '', fontstyle='italic', transform=axarr.transAxes)
subtitle = axarr.text(-0.2, 0.95, '', transform=axarr.transAxes)
year = axarr.text(-0.2, 0.85, '', transform=axarr.transAxes)

initial_area = axarr.text(-0.2, 0.8, '', transform=axarr.transAxes, size=6)
initial_area_percentage_of_landscape = axarr.text(-0.2, 0.77, '', transform=axarr.transAxes, size=6)
potential_area = axarr.text(-0.2, 0.74, '', transform=axarr.transAxes, size=6)
potential_total_area = axarr.text(-0.2, 0.71, '', transform=axarr.transAxes, size=6)
potential_total_area_percentage_of_landscape = axarr.text(-0.2, 0.68, '', transform=axarr.transAxes, size=6)

disclaimer = axarr.text(-0.25, -0.1, '', size=6, transform=axarr.transAxes)


## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation, title

## SH: LPB alternation
def animate(i):
    t = i + 1
    # if t < 10:
    #     fn = in_fn[:-3] + '00' + str(t)
    # else:
    #     fn = in_fn[:-3] + '0' + str(t)
    ##print fn
    amap = readmap(in_fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    disclaimer.set_text('* based on the land use types: ' + str(list_of_restricted_area_LUTs))
    potential_total_area_percentage_of_landscape.set_text('% of regional landscape: '+ str(potential_total_percentage_of_landscape))
    potential_total_area.set_text('potential total restricted area: ' + str(potential_total_area_value) + ' ' + str(Parameters.get_pixel_size()))
    potential_area.set_text('potential additional restricted area *: ' + str(suggested_areas) + ' ' + str(Parameters.get_pixel_size()))
    initial_area_percentage_of_landscape.set_text('% of regional landscape: ' + str(existing_areas_percentage_of_landscape))
    initial_area.set_text('initial restricted area: ' + str(existing_areas) + ' ' + str(Parameters.get_pixel_size()))
    year.set_text('Population peak year (baseline scenario) = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - based on the simulated maximum land use impact of the population peak')
    title.set_text('RAP LULCC SIMULATION - existing and simulated potential restricted areas')
    return im, leg, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_RAP_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})
# ValueError: unknown file extension: .mp4
#plt.show()

