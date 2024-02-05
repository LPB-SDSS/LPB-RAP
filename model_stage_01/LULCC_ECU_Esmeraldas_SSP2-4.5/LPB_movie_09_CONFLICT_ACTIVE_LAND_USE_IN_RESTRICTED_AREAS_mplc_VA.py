"""LAFORET-PLUC-BE-RAP/SFM - LPB mplc forest undisturbed and disturbed net and gross forest
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK),
2021 Q2/Q3
(Re-)written according to PEP 8 and modified original model.
Based on:

Make an MP4 file of the output of the LUC model of Mozambique
Judith Verstegen, 2017-07-04"""
import matplotlib.cm
from matplotlib import animation
from matplotlib import colors as cls
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.font_manager import FontProperties
plt.switch_backend('agg')
import matplotlib as mpl
colormap = mpl.colormaps['viridis'].resampled(10)
import numpy as np
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

# # get the dictionary
dictionary_of_accumulated_land_use_in_restricted_areas = json.loads(sys.argv[1])

##############
### inputs ###
##############

if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
    anthropogenic_impact_simulation = '* simulation conducted WITH additional allocation for depiction of maximum anthropogenic impact'
else:
    anthropogenic_impact_simulation = '* simulation conducted WITHOUT additional allocation for depiction of maximum anthropogenic impact'



## SH: LPB alternation
timesteps = Parameters.get_number_of_time_steps()
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'mplclura'

# classify the values in 7 classes:
# class 1 = 0 %
# class 2 = >0 to 20 %
# class 3 = >20 to 40 %
# class 4 = >40 to 60 %
# class 5 = >60 to 80 %
# class 6 = >80 to <100 %
# class 7 = 100 %
# class 8 is the region
# class 9 is restricted areas

## SH: LPB alternation
# working solution 1 with colormap viridis
list_all_colors = {0:'white',
                   1: colormap(1),
                   2: colormap(3),
                   3: colormap(5),
                   4: colormap(7),
                   5: colormap(10),
                   8: 'black',
                   9: 'grey'}

list_all_names = {1:' = built-up',
                   2:' = cropland - annual',
                   3:' = pastures',
                   4:' = agroforestry',
                   5:' = plantation',
                   8:' = region',
                   9:' = restricted areas'}

## SH: LPB alternation
legend_loc = (0.975,0.175)  # Esmeraldas right bottom

############
### MAIN ###
############

## SH: LPB alternation
# SH: look up the files in the according new output folder
# open the raster and read out the data in a numpy array
if (8 - len(fn)) > 0: nr_zeros = 8 - len(fn)
else:  nr_zeros = 0
in_fn = os.path.join(Filepaths.folder_CONFLICT_mplc_active_land_use,  fn + nr_zeros * '0' + '.001')
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
LUT01 = axarr.text(-0.2, 0.75, '', transform=axarr.transAxes, size=5)
LUT02 = axarr.text(-0.2, 0.72, '', transform=axarr.transAxes, size=5)
LUT03 = axarr.text(-0.2, 0.69, '', transform=axarr.transAxes, size=5)
LUT04 = axarr.text(-0.2, 0.66, '', transform=axarr.transAxes, size=5)
LUT05 = axarr.text(-0.2, 0.63, '', transform=axarr.transAxes, size=5)

anthropogenic_impact = axarr.text(-0.2, -0.1, '', size=6, transform=axarr.transAxes)

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, LUT05, LUT04, LUT03, LUT02, LUT01, year, subtitle, title_annotation, title

## SH: LPB alternation
def animate(i):
    key = i+1
    LUT01_pixels = dictionary_of_accumulated_land_use_in_restricted_areas['1'][str(key)]
    LUT02_pixels = dictionary_of_accumulated_land_use_in_restricted_areas['2'][str(key)]
    LUT03_pixels = dictionary_of_accumulated_land_use_in_restricted_areas['3'][str(key)]
    LUT04_pixels = dictionary_of_accumulated_land_use_in_restricted_areas['4'][str(key)]
    LUT05_pixels = dictionary_of_accumulated_land_use_in_restricted_areas['5'][str(key)]
    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    ##print fn
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')

    anthropogenic_impact.set_text(anthropogenic_impact_simulation)

    LUT05.set_text('plantation: ' + str(LUT05_pixels))
    LUT04.set_text('agroforestry: ' + str(LUT04_pixels))
    LUT03.set_text('pasture: ' + str(LUT03_pixels))
    LUT02.set_text('cropland-annual: ' + str(LUT02_pixels))
    LUT01.set_text('built-up: ' + str(LUT01_pixels))
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - accumulated areas of land use in restricted areas')
    title.set_text('LPB LULCC SIMULATION - most probable landscape configuration')
    return im, leg, LUT05, LUT04, LUT03, LUT02, LUT01, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})

